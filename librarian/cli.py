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

CACHE = Path(__file__).resolve().parent.parent / "cache"


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

    d = sub.add_parser("drift", help="does what is declared still match what exists")
    d.add_argument("--repo", action="append", default=None)
    d.set_defaults(fn=cmd_drift)

    args = ap.parse_args(argv)
    if args.cmd == "drift" and not args.repo:
        args.repo = ["ms"]
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
