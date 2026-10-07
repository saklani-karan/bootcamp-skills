#!/usr/bin/env python3
"""net_payloads.py <build_page.py> : each payload in net-payloads.json goes into a day's
sub_html (a raw-HTML field) of min.json and live.json, and is built both --no-net and
--live-photos. A payload with "refused_for" must exit 2 printing that reason in BOTH modes;
one with null must build in both. Prints one PASS/FAIL line per payload."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
B = sys.argv[1]
cases = json.load(open(os.path.join(HERE, "net-payloads.json"), encoding="utf-8"))
with tempfile.TemporaryDirectory() as d:
    for c in cases:
        bad = []
        for base, mode in (("min.json", "--no-net"), ("live.json", "--live-photos")):
            t = json.load(open(os.path.join(HERE, base), encoding="utf-8"))
            t["days"][0]["sub_html"] = "then lunch " + c["html"]
            f = os.path.join(d, "f.json")
            json.dump(t, open(f, "w", encoding="utf-8"), ensure_ascii=False)
            r = subprocess.run([sys.executable, B, f, "--out", os.path.join(d, "o.html"), mode],
                               capture_output=True, text=True)
            if c["refused_for"]:
                if r.returncode != 2 or "the page would reach the network: " not in r.stderr \
                        or c["refused_for"] not in r.stderr:
                    bad.append(f"{mode}: rc={r.returncode} {r.stderr.strip()[:120]!r}")
            elif r.returncode != 0:
                bad.append(f"{mode}: should build, rc={r.returncode} {r.stderr.strip()[:120]!r}")
        want = ("refused: " + c["refused_for"]) if c["refused_for"] else "builds"
        print(("  PASS  " if not bad else "  FAIL  ") + f"net: {c['name']:<48} {want}")
        for b in bad:
            print("          " + b)
