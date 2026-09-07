"""librarian -- scan | gaps | drift

    python -m librarian.cli scan  --repo ms
    python -m librarian.cli gaps  --repo ms [--missing-only]
    python -m librarian.cli drift --repo ms [--repo bd]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
INDEX = ROOT / "index" / "kb.sqlite"
PROFILES = ROOT / "profiles"
MANIFEST = ROOT / "map" / "manifest.json"


def _root(repo: str) -> Path:
    p = CACHE / repo
    if not p.is_dir():
        sys.exit(f"cache/{repo} is not present. Clone it there first.")
    return p


def cmd_scan(args) -> int:
    from librarian.scan import scan
    rep = scan(_root(args.repo))
    print(f"repo {args.repo} @ {rep.sha}\n")
    for name, n in rep.per_source.items():
        seen = rep.files_seen.get(name, 0)
        print(f"  {name:12s} {n:5d} docs   from {seen:3d} files")
    print(f"  {'total':12s} {len(rep.docs):5d} docs")
    print("\n  by kind:", dict(Counter(d.kind for d in rep.docs)))
    print("  by evidence:", dict(Counter(str(d.evidence) for d in rep.docs)))
    print(f"  advances=True: {sum(d.advances for d in rep.docs)}")
    _print_findings(rep.findings)
    return 0 if rep.ok else 1


def cmd_gaps(args) -> int:
    from librarian.index import Index
    if not INDEX.exists():
        sys.exit("no index. Run: python -m librarian.cli reindex --repo ms")
    idx = Index(INDEX)
    try:
        rows = idx.gaps(missing_only=args.missing_only)
    finally:
        idx.close()
    print(f"{'registry':26s} {'field':22s} {'gate':6s} {'code':26s} filled/total")
    print("-" * 96)
    for r in rows:
        mark = "  <- BLOCKED: nothing supplies it" if r["blocked"] else ""
        print(f"{r['registry']:26s} {r['field']:22s} {r['gate'] or '-':6s} "
              f"{r['finding_code'] or '-':26s} "
              f"{r['filled']:3d}/{r['total']:<3d}{mark}")
    return 0


def cmd_supplies(args) -> int:
    import json

    from librarian.index import Index
    if not INDEX.exists():
        sys.exit("no index. Run: python -m librarian.cli reindex --repo ms")
    idx = Index(INDEX)
    try:
        out = idx.supplies(args.name)
    finally:
        idx.close()
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    print(f"{out['name']}  (asked as a {out['asked_as']})  status={out['status']}\n")
    for r in out["coverage"]:
        print(f"  {r['registry']} > {r['field']}  gate={r['gate'] or '-'}  "
              f"{r['filled']}/{r['total']}"
              + ("   <- BLOCKED" if r["blocked"] else ""))
    unfilled = [e for e in out["entries"] if not e["present"]]
    if unfilled:
        print(f"\n  entries without it ({len(unfilled)}):")
        for e in unfilled[:12]:
            print(f"    {e['registry']} > {e['entry']}")
    if out["mentioned_in"]:
        print(f"\n  mentioned in {len(out['mentioned_in'])} documents:")
        for d in out["mentioned_in"][:8]:
            print(f"    {d['uid']}  ({d['kind']}, evidence={d['evidence']})")
    return 0


def _broken_link_findings(links) -> list:
    """A reference whose target is absent from the repository.

    `in_repo` is excluded: a reference to a file no adapter reads is not a
    defect, and reporting it is how a link checker becomes noise.
    """
    from librarian.doc import Finding
    return [
        Finding("broken_cross_reference", f"{l.src_uid} -> {l.raw}",
                f"{l.relation} target {l.dst_path or l.raw!r} is not in the "
                "repository", "warn")
        for l in links if l.status == "missing"
    ]


def _alias_findings(root: Path) -> list:
    """A recorded field alias whose target has disappeared.

    Aliases bridge the places a name cannot -- `radius_m` against the registry's
    `diameter_um` -- and a hand-maintained mapping is the thing that goes stale
    first. Verified on every build, so a stale one is a finding rather than a
    leaf that quietly stops resolving.
    """
    from librarian.inputs import load_aliases, registry_keys, verify_aliases
    return verify_aliases(load_aliases(PROFILES / "_field-aliases.yaml"),
                          registry_keys(root))


def cmd_reindex(args) -> int:
    from librarian.drift import drift
    from librarian.gaps import gaps as compute_gaps
    from librarian.index import build, manifest
    from librarian.links import extract
    from librarian.scan import scan
    docs, links, gap_rows, findings, shas = [], [], [], [], {}
    for repo in args.repo:
        rep = scan(_root(repo))
        errs = [f for f in rep.findings if f.severity == "error"]
        if errs:
            _print_findings(errs)
            return 1
        ls = extract(rep.docs, rep.repo_files, rep.source_text)
        gs = compute_gaps(_root(repo))
        fs = (drift(_root(repo), repo) + _broken_link_findings(ls)
              + _alias_findings(_root(repo)))
        docs += rep.docs
        links += ls
        gap_rows += gs
        findings += fs
        shas[repo] = rep.sha
        print(f"  {repo}@{rep.sha}: {len(rep.docs)} docs, {len(ls)} links, "
              f"{len(gs)} gap rows, {len(fs)} findings")
    n = build(docs, INDEX, shas, links, gap_rows, findings)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(manifest(shas, n))
    print(f"\nwrote {INDEX.relative_to(ROOT)} -- {n} docs")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")

    from librarian.index import Index
    idx = Index(INDEX)
    try:
        counts = idx.link_counts()
        print(f"\nlinks: {counts}")
        stored = idx.findings()
        if stored:
            print(f"\nfindings stored in the index: {len(stored)}")
            _print_rows(stored)
    finally:
        idx.close()
    return 0


def cmd_search(args) -> int:
    import json

    from librarian.index import Index, load_profiles
    from librarian.scan import commit_sha
    if not INDEX.exists():
        sys.exit("no index. Run: python -m librarian.cli reindex --repo ms")

    profiles = load_profiles(PROFILES)
    if args.profile not in profiles:
        sys.exit(f"unknown profile {args.profile!r}. Known: {', '.join(sorted(profiles))}")

    idx = Index(INDEX)
    current = {r: commit_sha(CACHE / r) for r in idx.repo_shas if (CACHE / r).is_dir()}
    res = idx.search(" ".join(args.query), profiles[args.profile],
                     limit=args.limit, current_shas=current,
                     require={"evidence": args.require_evidence} if args.require_evidence else None)
    if args.json:
        print(json.dumps(res.as_dict(), indent=2, ensure_ascii=False))
        return 0

    stale = "  [index_stale]" if res.index_stale else ""
    print(f"status={res.status}  profile={res.profile}{stale}")
    print(f"terms: match={res.terms_matched} glob={res.terms_globbed}\n")
    if res.status == "searched_empty":
        print("  searched_empty -- the corpus was searched and returned nothing.")
        print("  (Not the same as not_searched, which is the absence of a record.)")
        return 0
    for i, h in enumerate(res.hits, 1):
        tier = f"{h.evidence or '-'}/{h.tier if h.tier is not None else '-'}"
        print(f"{i:2d}. {h.score:8.3f}  {h.uid}")
        print(f"      {h.title[:96]}")
        print(f"      kind={h.kind}  evidence={tier}  advances={h.advances}  "
              f"falsifier={h.has_falsifier}  by={h.matched_by}")
        if h.snippet:
            print(f"      {h.snippet[:110]}")
    return 0


def cmd_get(args) -> int:
    import json

    from librarian.index import Index
    if not INDEX.exists():
        sys.exit("no index. Run: python -m librarian.cli reindex --repo ms")
    idx = Index(INDEX)
    try:
        d = idx.get(args.uid)
    finally:
        idx.close()
    if d is None:
        print(f"not_found: {args.uid}")
        print("  no document, and no other section of that path either.")
        return 1
    if d.get("status") == "not_found":
        print(f"not_found: {args.uid}")
        print("  the path is indexed but not that locator. Sections there:")
        for u in d["near"]:
            print(f"    {u}")
        return 1
    if args.json:
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return 0
    print(f"{d['uid']}\n")
    print(f"  title        {d['title']}")
    print(f"  kind         {d['kind']}   origin={d['origin']}")
    print(f"  evidence     {d['evidence']}  tier={d['tier']}  "
          f"advances={d['advances']}")
    print(f"  falsifier    {d['has_falsifier']}   review_after={d['review_after']}")
    print(f"  provenance   {d['provenance']}   reproduced={d['reproduced']}")
    if d["conditions"]:
        print(f"  conditions   {d['conditions']}")
    print(f"  refs out     {len(d['links_out'])}   refs in {len(d['links_in'])}")
    print("\n" + (d["body"] or "(no body)"))
    return 0


def cmd_neighbors(args) -> int:
    import json

    from librarian.index import Index
    if not INDEX.exists():
        sys.exit("no index. Run: python -m librarian.cli reindex --repo ms")
    idx = Index(INDEX)
    try:
        rows = idx.neighbors(args.uid, relation=args.relation, direction=args.direction)
    finally:
        idx.close()
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    if not rows:
        print(f"no {args.relation} neighbours {args.direction} of {args.uid}")
        return 0
    for r in rows:
        arrow = "->" if r["direction"] == "out" else "<-"
        st = f"  [{r.get('status')}]" if r.get("status") not in (None, "indexed") else ""
        print(f"{arrow} {r['uid'] or '(unresolved)'}{st}")
        if r.get("title"):
            print(f"     {r['title'][:92]}")
    return 0


def cmd_archive_sample(args) -> int:
    import json

    from librarian.archive import sample
    out = Path(args.out) if args.out else None
    try:
        rep = sample(Path(args.path), out)
    except OSError as e:
        sys.exit(str(e))
    print(json.dumps({k: v for k, v in rep.items() if k != "summary_keys"},
                     indent=2, ensure_ascii=False))
    print(f"\nsummary keys found ({len(rep['summary_keys'])}):")
    for k in rep["summary_keys"][:60]:
        print(f"  {k}")
    if len(rep["summary_keys"]) > 60:
        print(f"  ... and {len(rep['summary_keys']) - 60} more")
    if out:
        print(f"\nfragments written verbatim to {out}")
        print("Read them before running archive-dump: the device-tier key names "
              "are unverified, and a sweep would apply a guessed parser to every "
              "file.")
    return 0


def cmd_archive_dump(args) -> int:
    import json

    from librarian.archive import ArchiveError, dump
    try:
        rep = dump(Path(args.root), Path(args.out), CACHE / "ms", limit=args.limit)
    except ArchiveError as e:
        sys.exit(str(e))
    print(json.dumps({k: v for k, v in rep.items() if k != "unresolved"},
                     indent=2, ensure_ascii=False))
    print("\nfields looked for and not found (count of files):")
    for k, n in rep["unresolved"].items():
        print(f"  {n:6d}  {k}")
    print("\nEach line above is a field docs/02 section 6 declares and this "
          "draft could not fill.\nThe sample file turns that list into the diff "
          "to apply.")
    return 0


def cmd_inputs(args) -> int:
    import json

    from librarian.index import Index
    from librarian.inputs import recipe
    idx = Index(INDEX) if INDEX.exists() else None
    try:
        r = recipe(_root(args.repo), args.computation, index=idx,
                   aliases_path=PROFILES / "_field-aliases.yaml")
    finally:
        if idx:
            idx.close()
    if r is None:
        print(f"not_found: no function named {args.computation!r} in cache/{args.repo}")
        return 1
    if args.json:
        print(json.dumps(r.as_dict(), indent=2, ensure_ascii=False))
        return 0

    print(f"{r.computation}   status={r.status}")
    print(f"  {r.location}")
    print(f"  {r.signature}")
    if r.summary:
        print(f"  {r.summary[:150]}")
    print()
    mark = {"ready": "ok      ", "blocked": "BLOCKED ", "unresolved": "unresolved"}
    for l in r.leaves:
        opt = " (optional)" if l.optional else ""
        print(f"  {mark[l.status]:11s} {l.path:24s} {l.type:16s}{opt}")
        for s in l.supplied_by:
            f, tt = s.get("filled"), s.get("total")
            cov = f"  {f}/{tt}" if f is not None else ""
            print(f"              <- {s['registry']} > {s['field']}{cov}"
                  + ("   [via alias]" if l.via_alias else ""))
        if l.via_alias:
            print(f"                 {l.via_alias[:96]}")
        for c in l.candidates:
            print(f"              ?  {c}")
    return 0


def cmd_drift(args) -> int:
    from librarian.drift import drift
    findings = []
    for repo in args.repo:
        findings += drift(_root(repo), repo)
    if INDEX.exists():
        from librarian.index import Index
        idx = Index(INDEX)
        try:
            findings += idx.broken_links()
        finally:
            idx.close()
    _print_findings(findings, always=True)
    return 1 if any(f.severity == "error" for f in findings) else 0


def _print_rows(rows) -> None:
    """Findings as they come out of the index -- dicts, not Finding objects."""
    from collections import Counter as _C
    print(f"  {dict(_C(r['check'] for r in rows))}\n")
    for r in rows:
        tag = "ERROR" if r["severity"] == "error" else "warn "
        print(f"  [{tag}] {r['check']}")
        print(f"          {r['subject']}")
        print(f"          {r['detail']}")


def _print_findings(findings, always: bool = False) -> None:
    if not findings:
        if always:
            print("no findings")
        return
    by_check = Counter(f.check for f in findings)
    print(f"\n{len(findings)} findings: {dict(by_check)}\n")
    for f in sorted(findings, key=lambda x: (x.severity != "error", x.check, x.subject)):
        tag = "ERROR" if f.severity == "error" else "warn "
        print(f"  [{tag}] {f.check}")
        print(f"          {f.subject}")
        print(f"          {f.detail}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="librarian")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="run the adapters and account for every file")
    s.add_argument("--repo", default="ms")
    s.set_defaults(fn=cmd_scan)

    g = sub.add_parser("gaps", help="which gate is BLOCKED for want of which field")
    g.add_argument("--missing-only", action="store_true")
    g.set_defaults(fn=cmd_gaps)

    sp = sub.add_parser("supplies", help="what supplies a field, or what a gate waits for")
    sp.add_argument("name", help="a registry field (bleach_photons) or a gate (G10)")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_supplies)

    r = sub.add_parser("reindex", help="rebuild the index from scratch")
    r.add_argument("--repo", action="append", default=None)
    r.set_defaults(fn=cmd_reindex)

    q = sub.add_parser("search", help="query the index under a caller profile")
    q.add_argument("query", nargs="+")
    q.add_argument("--profile", default="neutral")
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--require-evidence", action="append", default=None,
                   help="hard filter, opt-in only: measured | assumed | confirmed_default")
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_search)

    g2 = sub.add_parser("get", help="one document in full, with its references")
    g2.add_argument("uid")
    g2.add_argument("--json", action="store_true")
    g2.set_defaults(fn=cmd_get)

    nb = sub.add_parser("neighbors", help="documents one hop away in the reference graph")
    nb.add_argument("uid")
    nb.add_argument("--relation", default="cites",
                    choices=["cites", "supersedes", "superseded_by", "applies_to",
                             "same_file"])
    nb.add_argument("--direction", default="out", choices=["out", "in", "both"])
    nb.add_argument("--json", action="store_true")
    nb.set_defaults(fn=cmd_neighbors)

    asa = sub.add_parser("archive-sample",
                         help="one acquisition's header fragments, verbatim -- run this first")
    asa.add_argument("path", help="path to one metadata.txt")
    asa.add_argument("--out", default=None, help="write the fragments to a file")
    asa.set_defaults(fn=cmd_archive_sample)

    ad = sub.add_parser("archive-dump",
                        help="every acquisition header under a root, as JSONL")
    ad.add_argument("root", help=r"the archive root, e.g. D:\data")
    ad.add_argument("--out", default="archive-dump.jsonl")
    ad.add_argument("--limit", type=int, default=None,
                    help="stop after N files -- use it for a first pass")
    ad.set_defaults(fn=cmd_archive_dump)

    inp = sub.add_parser("inputs",
                         help="what a computation needs, and which of it exists")
    inp.add_argument("computation", help="a function name, e.g. radial_stiffness_n_per_m")
    inp.add_argument("--repo", default="ms")
    inp.add_argument("--json", action="store_true")
    inp.set_defaults(fn=cmd_inputs)

    d = sub.add_parser("drift", help="does what is declared still match what exists")
    d.add_argument("--repo", action="append", default=None)
    d.set_defaults(fn=cmd_drift)

    args = ap.parse_args(argv)
    if args.cmd in {"drift", "reindex"} and not args.repo:
        args.repo = ["ms"]
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
