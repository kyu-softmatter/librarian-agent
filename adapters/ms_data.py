"""MS `data/*.yaml` -- the registries a gate actually consumes.

These are not knowledge: they are the inputs a gate reads at runtime
(`optics/components.py` loads `fluorophores.yaml`, `filters.yaml`,
`pixel_size.yaml`). They are indexed because **what a registry does not contain
is the reason a gate returns BLOCKED**, and that absence is v1's primary
product. Field-level presence is computed in `librarian/gaps.py`; this adapter
supplies the entries themselves so a gap has something to point at.

A vendor datasheet spec belongs here rather than in `kb/literature/` --
MS `kb/literature/README.md`: *"A datasheet is the manufacturer describing the
part in hand, not a third party describing a different one."* So a registry
entry is `confirmed_default`, not `assumed`, unless it says `verified: false`.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from librarian.doc import Doc


def _flatten_note(entry: dict) -> str:
    return yaml.safe_dump(entry, allow_unicode=True, sort_keys=True)


def ms_data(root: Path, sha: str) -> list[Doc]:
    data = root / "data"
    if not data.is_dir():
        raise FileNotFoundError(f"{data} does not exist")

    out: list[Doc] = []
    for path in sorted(data.glob("*.yaml")):
        rel = path.relative_to(root).as_posix()
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError as e:
            raise ValueError(f"{rel}: {e}") from e
        if not isinstance(doc, dict):
            continue

        for group, entries in doc.items():
            if not isinstance(entries, dict):
                continue
            for name, entry in entries.items():
                if not isinstance(entry, dict):
                    entry = {"value": entry}
                # `verified: false` is stated across most registries, and the
                # headers say why: the values are catalog nominals whose wings
                # are wrong, and crosstalk verdicts are decided by the wings.
                verified = entry.get("verified")
                evidence = "confirmed_default" if verified else None
                out.append(Doc(
                    repo="ms", path=rel, locator=f"{group}.{name}",
                    commit_sha=sha, kind="registry",
                    origin=group,
                    evidence=evidence,
                    tier=2 if evidence else None,
                    reproduced=("yes" if verified is True
                                else "no" if verified is False else None),
                    title=f"{path.stem} > {name}",
                    body=_flatten_note(entry),
                ))
    return out
