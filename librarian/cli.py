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
    from librarian.gaps import gaps, gate_functions, missing_vocabulary
    root = _root(args.repo)
    gfs = gate_functions(root)
    rows = gaps(root)

    mods = sorted({g.module for g in gfs})
    print(f"gates declared in a checks docstring: {len(gfs)}  "
          f"across {len(mods)} modules ({', '.join(mods)})")
    print(f"`missing.<field>` codes in the gate vocabulary: "
          f"{len(missing_vocabulary(root))}\n")
    by_field: dict[tuple[str, str, str | None], list] = {}
    for g in rows:
        by_field.setdefault((g.registry, g.field, g.gate), []).append(g)

    print(f"{'registry':26s} {'field':22s} {'gate':6s} {'code':26s} filled/total")
    print("-" * 96)
    for (reg, fld, gate), gs in sorted(by_field.items(),
                                       key=lambda kv: (sum(x.present for x in kv[1]), kv[0])):
        have = sum(x.present for x in gs)
        # --missing-only filters what is shown; the ratio stays over the whole
        # registry, because "0 of 6" and "0 of 0" say different things.
        if args.missing_only and have:
            continue
        mark = "  <- BLOCKED: nothing supplies it" if have == 0 else ""
        code = gs[0].finding_code or "-"
        print(f"{reg:26s} {fld:22s} {gate or '-':6s} {code:26s} {have:3d}/{len(gs):<3d}{mark}")
    return 0


def cmd_reindex(args) -> int:
    from librarian.index import build, manifest
    from librarian.scan import scan
    docs, shas = [], {}
    for repo in args.repo:
        rep = scan(_root(repo))
        errs = [f for f in rep.findings if f.severity == "error"]
        if errs:
            _print_findings(errs)
            return 1
        docs += rep.docs
        shas[repo] = rep.sha
        print(f"  {repo}@{rep.sha}: {len(rep.docs)} docs")
    n = build(docs, INDEX, shas)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(manifest(shas, n))
    print(f"\nwrote {INDEX.relative_to(ROOT)} -- {n} docs")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")
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


def cmd_drift(args) -> int:
    from librarian.drift import drift
    findings = []
    for repo in args.repo:
        findings += drift(_root(repo), repo)
    _print_findings(findings, always=True)
    return 1 if any(f.severity == "error" for f in findings) else 0


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
    g.add_argument("--repo", default="ms")
    g.add_argument("--missing-only", action="store_true")
    g.set_defaults(fn=cmd_gaps)

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

    d = sub.add_parser("drift", help="does what is declared still match what exists")
    d.add_argument("--repo", action="append", default=None)
    d.set_defaults(fn=cmd_drift)

    args = ap.parse_args(argv)
    if args.cmd in {"drift", "reindex"} and not args.repo:
        args.repo = ["ms"]
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
