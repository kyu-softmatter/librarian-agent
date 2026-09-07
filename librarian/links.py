"""Cross-references, and the difference between unresolved and broken.

Three link forms exist in the corpus, all of them read off it rather than
assumed:

    [[sample-medium-refractive-index]]      wikilink, used by kb/expertise/
    [text](../../docs/07-roadmap.md#anchor) relative markdown link
    supersedes: <id>                        frontmatter relation

**Unresolved is not broken, and conflating them is how a link checker becomes
noise.** A reference to `../../NOTICE.md` resolves to a file that exists and is
simply not indexed -- there is no adapter for it, and there should not be. Only a
reference whose target is absent from the repository is a defect. So a link
carries a status rather than a boolean:

    indexed   the target is a document in the index      -> a real neighbour
    in_repo   the file exists, nothing indexes it        -> fine, not a neighbour
    missing   the file is not there                      -> the drift finding
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from typing import Iterable, Optional

from librarian.doc import Doc
from librarian.md import frontmatter, strip_fences

# `[[slug]]`. Restricted to slug shape on purpose: the corpus contains
# `[[null, 750]]`, which is a YAML fragment quoted in prose and not a link.
_WIKI = re.compile(r"\[\[([a-z0-9][a-z0-9._-]*)\]\]")
#: An ellipsis marks a placeholder, not a slug: `[[647-exposure-...]]`.
_PLACEHOLDER_SLUG = re.compile(r"\.\.\.")
# `](path)` or `](path#anchor)`, relative only -- http and mailto are skipped.
_MDLINK = re.compile(r"\]\(\s*(?!https?:|mailto:|#)([^)\s]+?)\s*\)")

RELATIONS = ("cites", "supersedes", "superseded_by", "applies_to")


@dataclass(frozen=True)
class Link:
    src_uid: str
    relation: str
    raw: str
    dst_path: Optional[str]
    dst_locator: Optional[str]
    dst_uid: Optional[str]
    status: str            # indexed | in_repo | missing

    def __post_init__(self) -> None:
        if self.relation not in RELATIONS:
            raise ValueError(f"relation {self.relation!r} not in {RELATIONS}")
        if self.status not in {"indexed", "in_repo", "missing"}:
            raise ValueError(f"status {self.status!r}")


def _normalise(src_path: str, target: str) -> str:
    """Resolve a relative reference against the referring file's directory."""
    return posixpath.normpath(posixpath.join(posixpath.dirname(src_path), target))


def extract(docs: Iterable[Doc], repo_files: set[str],
            source_text: dict[str, str] | None = None) -> list[Link]:
    """Every reference in the corpus, resolved as far as the corpus allows.

    `docs` supplies the bodies; `repo_files` is every repo-relative path that
    exists, which is what separates `in_repo` from `missing`. Without it the
    checker reports the whole reference graph as broken.
    """
    docs = list(docs)
    by_path: dict[str, list[Doc]] = {}
    by_stem: dict[str, Doc] = {}
    for d in docs:
        by_path.setdefault(d.path, []).append(d)
    for path, group in by_path.items():
        stem = posixpath.basename(path).rsplit(".", 1)[0]
        by_stem.setdefault(stem, group[0])

    def resolve(src: Doc, relation: str, raw: str,
                path: str, locator: Optional[str]) -> Link:
        # A directory reference points at its README where one is indexed.
        candidates = [path] if not path.endswith("/") else []
        if path.endswith("/"):
            candidates = [path.rstrip("/") + "/README.md"]
        hit = next((c for c in candidates if c in by_path), None)
        if hit:
            target = by_path[hit]
            uid = next((d.uid for d in target if d.locator == locator), target[0].uid)
            return Link(src.uid, relation, raw, hit, locator, uid, "indexed")
        clean = path.rstrip("/")
        if clean in repo_files or any(f.startswith(clean + "/") for f in repo_files):
            return Link(src.uid, relation, raw, clean, locator, None, "in_repo")
        return Link(src.uid, relation, raw, clean, locator, None, "missing")

    out: list[Link] = []
    for d in docs:
        text = strip_fences(d.body)
        for m in _WIKI.finditer(text):
            slug = m.group(1)
            if _PLACEHOLDER_SLUG.search(slug):
                continue
            target = by_stem.get(slug)
            if target is not None:
                out.append(Link(d.uid, "cites", m.group(0), target.path,
                                None, target.uid, "indexed"))
            else:
                # A wikilink names a slug, not a path, so `missing` would be a
                # guess about where it was supposed to live.
                out.append(Link(d.uid, "cites", m.group(0), None, None, None,
                                "in_repo" if slug in repo_files else "missing"))
        for m in _MDLINK.finditer(text):
            raw = m.group(1)
            path, _, anchor = raw.partition("#")
            if not path:
                continue
            out.append(resolve(d, "cites", m.group(0),
                               _normalise(d.path, path), anchor or None))

    # Frontmatter relations, read once per file rather than once per section.
    for path, group in by_path.items():
        text = (source_text or {}).get(path)
        if not text:
            continue
        fm, _ = frontmatter(text)
        head = group[0]
        for key, relation in (("supersedes", "supersedes"),
                              ("superseded_by_measurement", "superseded_by")):
            v = fm.get(key)
            if not v or str(v).strip().lower() in {"null", "none", ""}:
                continue
            out.append(resolve(head, relation, f"{key}: {v}",
                               _normalise(path, str(v)), None))
        for sysid in (fm.get("applies_to_systems") or []):
            target = by_stem.get(str(sysid))
            if target is not None:
                out.append(Link(head.uid, "applies_to", f"applies_to_systems: {sysid}",
                                target.path, None, target.uid, "indexed"))

    # Deterministic order, so the index is byte-reproducible.
    return sorted(set(out), key=lambda l: (l.src_uid, l.relation, l.raw,
                                           l.dst_uid or "", l.dst_path or ""))
