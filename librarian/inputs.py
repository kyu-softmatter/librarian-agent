"""What a computation needs, and which of it exists.

The question an agent actually asks is not "what do we know about trap
stiffness" -- `kb_search` answers that -- but **"give me the inputs to compute
trap stiffness on this instrument."** Those are different queries, and the
second one has an answer the corpus cannot rank its way to: it is a closure over
a function's signature.

    radial_stiffness_n_per_m(power_w, bead: Bead, medium: Medium, beam: ObjectiveBeam)

    power_w                float          <- data/light_sources.yaml
    bead.radius_m          float          <- data/particles.yaml
    bead.n                 float
    medium.n               float          <- kb/expertise/sample-medium-refractive-index
    medium.viscosity_pa_s  float | None
    beam.na                float          <- data/objectives.yaml, 6 objectives
    beam.wavelength_m      float

**Derived from the signature, not hand-authored.** A hand-written input list is
the `implemented_in` problem again: it goes stale the first time an argument is
added, and nothing notices. Walking the signature and the dataclasses it names
cannot drift from the code, because it *is* the code.

**Where a name cannot bridge, it says so.** `bead.radius_m` and the registry's
`diameter_um` are the same quantity under different names and units, and no
string comparison should be allowed to claim otherwise. Those links live in
`profiles/field-aliases.yaml`, are **verified against the registries on every
build**, and an alias whose target has disappeared becomes a finding rather than
a silent miss. Anything left over is reported as `unresolved` with search
candidates attached, which is a weaker answer than the question asked and an
honest one.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from librarian.doc import Finding

#: Type names that are values rather than structures to expand.
_SCALARS = {"float", "int", "str", "bool", "bytes", "complex"}
_OPTIONAL = re.compile(r"\bOptional\[|\|\s*None\b")


@dataclass
class Leaf:
    """One scalar a computation needs."""
    path: str                       # beam.na
    name: str                       # na
    type: str                       # float
    optional: bool = False
    #: The docstring of the class that declares this field. Used to search for
    #: candidates when the field name itself is too short to be a query: `n` on
    #: `Medium` is one character, and FTS5 cannot form a token from it, so the
    #: leaf came back with no candidates at all. What declares it can be
    #: searched -- "the immersion medium the bead sits in" -- and that is
    #: derived from the code rather than guessed at.
    declared_by: str = ""
    supplied_by: list[dict[str, Any]] = field(default_factory=list)
    via_alias: Optional[str] = None
    candidates: list[str] = field(default_factory=list)
    candidate_query: str = ""

    @property
    def status(self) -> str:
        if not self.supplied_by:
            return "unresolved"
        if any(s["filled"] for s in self.supplied_by):
            return "ready"
        return "blocked"


@dataclass
class Recipe:
    computation: str
    location: str
    signature: str
    summary: str
    leaves: list[Leaf] = field(default_factory=list)

    @property
    def status(self) -> str:
        """`blocked` outranks `unresolved`: a named missing input beats a guess.

        A caller can act on "no entry supplies `power_at_sample_mw`". It cannot
        act on "this repository does not say where `radius_m` comes from", so
        the first is the more useful headline when both are true.
        """
        s = {l.status for l in self.leaves if not l.optional}
        if "blocked" in s:
            return "blocked"
        if "unresolved" in s:
            return "unresolved"
        return "ready" if s else "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "computation": self.computation,
            "location": self.location,
            "signature": self.signature,
            "summary": self.summary,
            "status": self.status,
            "inputs": [
                {"path": l.path, "type": l.type, "optional": l.optional,
                 "status": l.status, "supplied_by": l.supplied_by,
                 "via_alias": l.via_alias, "candidates": l.candidates,
                 "candidate_query": l.candidate_query}
                for l in self.leaves
            ],
        }


# --------------------------------------------------------------------------
# walking the code
# --------------------------------------------------------------------------

def _classes(root: Path) -> dict[str, tuple[str, list[tuple[str, str]], str]]:
    """Every annotated class in the repository, by name.

    Name collisions keep the first by sorted path, and that is a limitation
    worth stating rather than hiding: two `Medium` classes in different modules
    would resolve to one here.
    """
    out: dict[str, tuple[str, list[tuple[str, str]]]] = {}
    for p in sorted(root.rglob("*.py")):
        if any(x in {".git", "tests", "__pycache__"} for x in p.parts):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in tree.body:
            if isinstance(n, ast.ClassDef) and n.name not in out:
                fields = [(x.target.id, ast.unparse(x.annotation))
                          for x in n.body
                          if isinstance(x, ast.AnnAssign) and isinstance(x.target, ast.Name)]
                if fields:
                    doc = " ".join((ast.get_docstring(n) or "").split())
                    out[n.name] = (p.relative_to(root).as_posix(), fields, doc)
    return out


def find_function(root: Path, name: str) -> Optional[tuple[Path, ast.FunctionDef]]:
    for p in sorted(root.rglob("*.py")):
        if any(x in {".git", "__pycache__"} for x in p.parts):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
                return p, n
    return None


def _base_type(annotation: str) -> str:
    a = annotation.replace("Optional[", "").rstrip("]")
    a = a.split("|")[0].strip()
    return a


def walk_inputs(root: Path, func: ast.FunctionDef,
                classes: dict[str, tuple[str, list[tuple[str, str]], str]],
                depth: int = 3) -> list[Leaf]:
    """The scalar closure of a signature, expanding annotated classes.

    Keyword-only parameters with defaults are skipped: `probe_fraction=0.02` and
    `n_points=96` are how the computation is run, not what it needs to know.
    """
    leaves: list[Leaf] = []

    def expand(prefix: str, annotation: str, level: int, declared_by: str = "") -> None:
        base = _base_type(annotation)
        optional = bool(_OPTIONAL.search(annotation))
        if base in _SCALARS or level <= 0 or base not in classes:
            leaves.append(Leaf(path=prefix, name=prefix.split(".")[-1],
                               type=annotation, optional=optional,
                               declared_by=declared_by))
            return
        for fname, fann in classes[base][1]:
            expand(f"{prefix}.{fname}", fann, level - 1, classes[base][2])

    args = func.args
    positional = args.posonlyargs + args.args
    n_defaults = len(args.defaults)
    required = positional[: len(positional) - n_defaults] if n_defaults else positional
    for a in required:
        if a.arg in {"self", "cls"} or a.annotation is None:
            continue
        expand(a.arg, ast.unparse(a.annotation), depth)
    return leaves


# --------------------------------------------------------------------------
# resolving a leaf to a registry
# --------------------------------------------------------------------------

def registry_keys(root: Path) -> dict[str, set[str]]:
    """Field names each registry actually carries, from its entries.

    Read from the entries rather than only from the schema comment, because
    `data/objectives.yaml` has no comment block -- so a declaration-only lookup
    could not find `na`, which is the field the whole trap calculation turns on.
    """
    out: dict[str, set[str]] = {}
    for p in sorted((root / "data").glob("*.yaml")):
        rel = p.relative_to(root).as_posix()
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError:
            continue
        keys: set[str] = set()
        if isinstance(doc, dict):
            for group, entries in doc.items():
                if isinstance(entries, dict):
                    for entry in entries.values():
                        if isinstance(entry, dict):
                            keys |= {str(k) for k in entry}
        out[rel] = keys
    return out


def load_aliases(path: Path) -> dict[str, dict[str, str]]:
    """`leaf name -> {registry, field, note}`. Verified, never trusted."""
    if not path.exists():
        return {}
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(k): dict(v) for k, v in (d.get("aliases") or {}).items()}


def verify_aliases(aliases: dict[str, dict[str, str]],
                   keys: dict[str, set[str]]) -> list[Finding]:
    """An alias pointing at a field that is gone is a finding, not a miss."""
    out = []
    for leaf, a in sorted(aliases.items()):
        reg, fld = a.get("registry", ""), a.get("field", "")
        if reg not in keys:
            out.append(Finding("alias_registry_missing", f"{leaf} -> {reg}",
                               f"no registry {reg!r} in data/", "error"))
        elif fld not in keys[reg]:
            out.append(Finding("alias_field_missing", f"{leaf} -> {reg} > {fld}",
                               f"{reg} carries no field {fld!r}; the alias is stale",
                               "error"))
    return out


def recipe(root: Path, name: str, index=None,
           aliases_path: Optional[Path] = None) -> Optional[Recipe]:
    hit = find_function(root, name)
    if hit is None:
        return None
    path, func = hit
    classes = _classes(root)
    leaves = walk_inputs(root, func, classes)

    keys = registry_keys(root)
    aliases = load_aliases(aliases_path) if aliases_path else {}

    for leaf in leaves:
        for reg, ks in sorted(keys.items()):
            if leaf.name in ks:
                leaf.supplied_by.append({"registry": reg, "field": leaf.name,
                                         **_coverage(index, reg, leaf.name)})
        if not leaf.supplied_by and leaf.name in aliases:
            a = aliases[leaf.name]
            reg, fld = a.get("registry", ""), a.get("field", "")
            if reg in keys and fld in keys[reg]:
                leaf.via_alias = a.get("note") or f"{reg} > {fld}"
                leaf.supplied_by.append({"registry": reg, "field": fld,
                                         **_coverage(index, reg, fld)})
        if not leaf.supplied_by and index is not None:
            from librarian.index import MIN_MATCH_CHARS, NEUTRAL
            q = leaf.name.replace("_", " ")
            if len(leaf.name) < MIN_MATCH_CHARS and leaf.declared_by:
                q = f"{leaf.path.split('.')[0]} {leaf.declared_by}"
            res = index.search(q, NEUTRAL, limit=3)
            leaf.candidates = [h.uid for h in res.hits]
            leaf.candidate_query = q

    sig = f"{name}({ast.unparse(func.args)})"
    return Recipe(computation=name,
                  location=f"ms:{path.relative_to(root).as_posix()}#{name}",
                  signature=sig,
                  summary=" ".join((ast.get_docstring(func) or "").split())[:200],
                  leaves=leaves)


def _coverage(index, registry: str, field_name: str) -> dict[str, Any]:
    """filled/total from the gap table, where the index knows; else unknown."""
    if index is None:
        return {"filled": None, "total": None}
    rows = [r for r in index.gaps(field=field_name) if r["registry"] == registry]
    if rows:
        return {"filled": rows[0]["filled"], "total": rows[0]["total"]}
    # Not a gate-consumed field, so it has no gap row. Count it directly.
    n = index.db.execute(
        "SELECT count(*) FROM doc WHERE path = ? AND kind = 'registry' "
        "AND body GLOB ?", (registry, f"*{field_name}:*")).fetchone()[0]
    tot = index.db.execute(
        "SELECT count(*) FROM doc WHERE path = ? AND kind = 'registry'",
        (registry,)).fetchone()[0]
    return {"filled": n, "total": tot}
