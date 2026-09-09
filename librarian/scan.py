"""Run the adapters, and account for every candidate file.

An adapter asserting its own non-zero count is not enough: it would still pass
while silently dropping a folder. So coverage is checked **from outside** --
candidate files are enumerated independently of the adapter, and any candidate
that produced no document is reported.

The reason is on record. BD `tools/kb.py` pointed at a renamed path and *"simply
reported 'run-less knowledge 0' for 126 existing entries. A silently empty read
is the same failure mode as an unwired checker."*
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from adapters import ADAPTERS
from librarian.doc import Doc, Finding

# Candidate files per source, enumerated independently of the adapter.
CANDIDATES = {
    "ms_kb": lambda r: [p for p in sorted((r / "kb").rglob("*"))
                        if p.is_file() and p.suffix in {".md", ".yaml", ".yml"}],
    "ms_data": lambda r: sorted((r / "data").glob("*.yaml")),
    "ms_docs": lambda r: sorted((r / "docs").rglob("*.md")),
    "ms_agents": lambda r: sorted((r / ".claude" / "agents").glob("*.md")),
    # BD's wiki holds one YAML ledger beside the markdown -- `benchmarks.yaml`
    # is what pytest reads, and it lists more benchmarks than the folder holds
    # pages, so it is a candidate rather than an aside.
    "bd_wiki": lambda r: [p for p in sorted((r / "knowledge" / "wiki").rglob("*"))
                          if p.is_file()
                          and (p.suffix == ".md" or p.name == "benchmarks.yaml")],
    "bd_source": lambda r: sorted((r / "knowledge" / "source").rglob("*.md")),
    "bd_entries": lambda r: sorted((r / "knowledge" / "entries").glob("*.json")),
}


def sources_for(root: Path) -> list[str]:
    """The adapters that apply to this checkout, selected by directory name.

    `librarian.cli` puts every clone at `cache/<repo>` and each source name is
    prefixed with the repo it parses, so the directory name is the selector.

    The alternative -- running every adapter against every checkout -- makes
    `source_empty` fire at error severity for the sources that do not apply,
    which inverts that check: it exists to catch a store that should have
    answered and did not.
    """
    return [n for n in ADAPTERS if n.startswith(f"{root.name}_")]


def commit_sha(root: Path) -> str:
    out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"{root} is not a git checkout: {out.stderr.strip()}")
    return out.stdout.strip()


@dataclass
class ScanReport:
    sha: str = ""
    docs: list[Doc] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    per_source: dict[str, int] = field(default_factory=dict)
    files_seen: dict[str, int] = field(default_factory=dict)
    #: Every repo-relative path that exists. This is what separates a reference
    #: to an unindexed file from a reference to a missing one -- without it, a
    #: link checker reports the whole graph as broken.
    repo_files: set[str] = field(default_factory=set)
    #: Raw text of the candidate files, for frontmatter relations that belong to
    #: the file rather than to any one of its sections.
    source_text: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)


def scan(root: Path, sources: list[str] | None = None) -> ScanReport:
    sha = commit_sha(root)
    rep = ScanReport(sha=sha)
    rep.repo_files = {p.relative_to(root).as_posix()
                      for p in root.rglob("*")
                      if p.is_file() and ".git" not in p.parts}
    names = sources or sources_for(root)
    if not names:
        rep.findings.append(Finding(
            "no_adapter", root.name,
            f"no source is registered for a checkout named {root.name!r}; "
            "an unparsed repository reads as an empty one", "error"))
        return rep

    for name in names:
        adapter = ADAPTERS[name]
        try:
            docs = adapter(root, sha)
        except Exception as e:                       # a parse failure is an error
            rep.findings.append(Finding("adapter_failed", name, f"{type(e).__name__}: {e}", "error"))
            rep.per_source[name] = 0
            continue

        rep.per_source[name] = len(docs)
        rep.docs.extend(docs)

        # 1. non-zero, per source
        if not docs:
            rep.findings.append(Finding(
                "source_empty", name,
                "the adapter returned no documents; a silently empty read is "
                "indistinguishable from an absent store", "error"))
            continue

        # 2. coverage, checked from outside the adapter
        cand_paths = CANDIDATES[name](root)
        cands = {p.relative_to(root).as_posix() for p in cand_paths}
        rep.files_seen[name] = len(cands)
        for p in cand_paths:
            if p.suffix == ".md":
                rep.source_text[p.relative_to(root).as_posix()] = p.read_text(
                    encoding="utf-8", errors="replace")
        covered = {d.path for d in docs}
        for miss in sorted(cands - covered):
            rep.findings.append(Finding(
                "file_produced_nothing", f"{name}:{miss}",
                "a candidate file yielded no document", "warn"))

    # 3. coordinates are mandatory and unique
    seen: dict[str, str] = {}
    for d in rep.docs:
        if d.uid in seen:
            rep.findings.append(Finding(
                "uid_collision", d.uid,
                "two documents claim the same coordinate", "error"))
        seen[d.uid] = d.path

    # 4. `advances` may only be true where evidence is a measurement.
    #    Derived from `evidence`, so this can only fire if the type changed.
    for d in rep.docs:
        if d.advances and d.evidence != "measured":
            rep.findings.append(Finding(
                "advances_without_measurement", d.uid,
                f"evidence={d.evidence!r} but advances is true", "error"))

    return rep
