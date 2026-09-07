"""Which gate is BLOCKED, and for want of which registry field.

v1's primary product, and the one thing `grep` cannot produce: it needs three
places crossed, and MS already states all three for machines.

  1. what a registry **declares**   the schema comment block in data/*.yaml
  2. what a gate **requires**       the field a gate function actually reads
  3. what an entry **has**          a non-empty value, not merely the key

Nothing is hard-coded, and two precision rules are worth stating because
guessing either one produces confident wrong answers.

**Presence means a non-empty value.** `power_at_sample_mw` is present as a key on
almost every line and its value is `{}` everywhere. `photo/gate.py` says so in
prose -- *"`power_at_sample_mw` is empty for every line of every source"* -- and a
key-existence check reports the opposite.

**Gate attribution comes from the function body, not from the module.** The
`missing.<field>` codes are a flat namespace and they collide: `optics/gate.py`
raises `missing.source` about an illumination source, while `data/particles.yaml`
declares an unrelated `source:` field. Attributing by name would tie a gate to
the wrong registry, so a gate is attached only when its own function reads the
field.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from librarian.doc import Gap

# `#     bleach_photons:   mean photons emitted before bleaching (...)`
_DECLARED = re.compile(r"^#\s{2,}(\w+):", re.MULTILINE)
_MISSING = re.compile(r'"missing\.([a-z_0-9]+)"')
# `-` included: the token after `>` is often an entry name, not a field.
_EXPLICIT = re.compile(r"data/([a-z_]+)\.yaml\s*>\s*([a-z_0-9-]+)")
_GATE_PREFIX = re.compile(r"\A(G\d+[a-z]?):\s*(.+?)(?:\.|\Z)", re.DOTALL)

_GATE_KEY = lambda g: (int(re.sub(r"\D", "", g)), g)


@dataclass(frozen=True, slots=True)
class GateFn:
    gate: str
    module: str
    func: str
    description: str
    reads: frozenset[str]


def _reads(node: ast.AST) -> set[str]:
    """The names a gate function reads **as data**: attributes and string keys.

    Bare identifiers are excluded, and that exclusion is the whole precision of
    this module. A registry field reaches a gate as `setup.<field>` or as a
    string key, never as a local variable -- so counting `ast.Name` attributes a
    gate to any field that happens to share a name with a local. Measured: the
    `product` field of `data/particles.yaml` appeared to be read by `G11`
    (`validity/check_statistical_power`) purely because that function has a local
    called `product`. `lifetime_ns` in `G20` is the real shape -- it appears as
    both an attribute and a string constant.
    """
    out: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
    return out


def gate_functions(root: Path) -> list[GateFn]:
    """Gates as declared by their own docstring, with what they read.

    `optics/checks.py` is the counter-example that makes this worth writing
    carefully: its checks carry questions as docstrings and no gate id at all,
    so it contributes nothing here -- which is a finding, not a parse failure.
    """
    out: list[GateFn] = []
    for path in sorted(root.rglob("checks.py")):
        if ".git" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            doc = ast.get_docstring(node) or ""
            m = _GATE_PREFIX.match(doc.strip())
            if not m:
                continue
            out.append(GateFn(
                gate=m.group(1), module=path.parent.name, func=node.name,
                description=" ".join(m.group(2).split())[:110],
                reads=frozenset(_reads(node)),
            ))
    return out


def field_to_gates(root: Path) -> dict[str, list[str]]:
    """field -> the gates whose own function reads it."""
    out: dict[str, set[str]] = {}
    for gf in gate_functions(root):
        for name in gf.reads:
            out.setdefault(name, set()).add(gf.gate)
    return {k: sorted(v, key=_GATE_KEY) for k, v in out.items()}


def missing_vocabulary(root: Path) -> dict[str, set[str]]:
    """field -> modules that raise `missing.<field>`. Reported, never joined."""
    out: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*.py")):
        if any(p in {".git", "tests"} for p in path.parts):
            continue
        for m in _MISSING.finditer(path.read_text(encoding="utf-8", errors="replace")):
            out.setdefault(m.group(1), set()).add(path.parent.name)
    return out


def registry_fields(root: Path) -> dict[str, set[str]]:
    """registry -> the fields it declares in its own schema comment block."""
    out: dict[str, set[str]] = {}
    for path in sorted((root / "data").glob("*.yaml")):
        rel = path.relative_to(root).as_posix()
        head = path.read_text(encoding="utf-8", errors="replace")
        out[rel] = {m.group(1) for m in _DECLARED.finditer(head)}
    return out


def explicit_refs(root: Path, declared: dict[str, set[str]]) -> set[tuple[str, str]]:
    """(registry, field) pairs a module names outright.

    A token that is not a declared field of that registry is an **entry**
    reference -- `data/particles.yaml > abvigen-red-5um-cooh` -- and is dropped.
    """
    out: set[tuple[str, str]] = set()
    for path in sorted(root.rglob("*.py")):
        if ".git" in path.parts:
            continue
        for m in _EXPLICIT.finditer(path.read_text(encoding="utf-8", errors="replace")):
            reg, tok = f"data/{m.group(1)}.yaml", m.group(2)
            if tok in declared.get(reg, ()):
                out.add((reg, tok))
    return out


def _filled(obj, field: str) -> bool:
    """Does `field` appear anywhere inside with a non-empty value?

    Nesting matters: `power_at_sample_mw` lives under
    `light_sources > <source> > lines > <line>`, so a flat check reports the
    wrong location. Emptiness matters more: its value is `{}` throughout.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k) == field and v not in (None, {}, [], ""):
                return True
            if _filled(v, field):
                return True
    elif isinstance(obj, list):
        return any(_filled(v, field) for v in obj)
    return False


def gaps(root: Path) -> list[Gap]:
    declared = registry_fields(root)
    refs = explicit_refs(root, declared)
    f2g = field_to_gates(root)
    vocab = missing_vocabulary(root)

    out: list[Gap] = []
    for path in sorted((root / "data").glob("*.yaml")):
        rel = path.relative_to(root).as_posix()
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue

        # In scope: a field this registry declares, which some gate reads or
        # some module names for this file. A field nobody consumes is not a gap.
        scope = sorted(f for f in declared.get(rel, ())
                       if f in f2g or f in vocab or (rel, f) in refs)
        if not scope:
            continue

        for group, entries in doc.items():
            if not isinstance(entries, dict):
                continue
            for name, entry in entries.items():
                for f in scope:
                    gates = f2g.get(f, [])
                    out.append(Gap(
                        repo="ms", registry=rel, entry=f"{group}.{name}", field=f,
                        present=_filled(entry, f),
                        gate=gates[0] if gates else None,
                        finding_code=f"missing.{f}" if f in vocab else None,
                    ))
    return out
