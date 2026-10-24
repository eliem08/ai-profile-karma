import argparse
import sys
from collections import defaultdict

from .core import LAWS, exposure_score, request_letter, scan_path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ai-profile-karma", description="See what an AI could know about you.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("path")
    s.add_argument("--evidence", type=int, default=2, help="snippets shown per category")
    l = sub.add_parser("letter")
    l.add_argument("--vendor", required=True)
    l.add_argument("--law", choices=sorted(LAWS), default="gdpr")
    l.add_argument("--action", choices=["access", "correct", "delete"], default="delete")
    l.add_argument("--name", required=True)
    l.add_argument("--email", required=True)
    l.add_argument("--categories", nargs="*")
    a = ap.parse_args(argv)

    if a.cmd == "letter":
        print(request_letter(a.vendor, a.law, a.action, a.name, a.email, a.categories))
        return 0
    findings = scan_path(a.path)
    rep = exposure_score(findings)
    print(f"Exposure score: {rep['score']}/100 ({rep['level']}) - {rep['distinct_facts']} distinct facts")
    grouped = defaultdict(list)
    for f in findings:
        grouped[f.category].append(f)
    for cat, items in sorted(grouped.items(), key=lambda kv: -max(i.weight for i in kv[1])):
        print(f"\n[{cat}] {len(items)} mention(s)")
        for f in items[: a.evidence]:
            print(f"  - {f.kind}: {f.snippet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
