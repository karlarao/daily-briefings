#!/usr/bin/env python3
"""Probe the PARENT ledger for a noun / CVE id across every section.

The 2026-10-08 and 2026-10-09 runs each drafted corrections for rows that were
ALREADY right on the board (4 of 6, then 8 of 12). In both cases the stale thing
was the prose in CLAUDE.md, not the board. The rule that came out of it:

    check the board BEFORE writing a correction, not after.

Usage:  python3 probe_board.py <term> [<term> ...]
Prints every matching row with its section, key, dated field and full text, so a
draft can be compared against what is actually stored. Read the hits, never
count them (10-09: the id probe returned 4 and 6 peers for two rows and most
were noun-collision noise; one of the ten was the real duplicate).
"""
import json, sys, re, os

LED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parent_ledger.json")
SECTIONS = ("events", "patch", "claims", "ownclaims", "promises",
            "benchmarks", "gaps", "buildbets", "skills", "retired_events")


def rows(led, name):
    v = led.get(name)
    return v if isinstance(v, list) else []


def main(terms):
    led = json.load(open(LED))
    pats = [re.compile(re.escape(t), re.I) for t in terms]
    total = 0
    for sec in SECTIONS:
        for r in rows(led, sec):
            if not isinstance(r, dict):
                continue
            blob = " ".join(str(r.get(f, "")) for f in
                            ("k", "t", "v", "due", "date", "announced", "status", "verdict"))
            if any(p.search(blob) for p in pats):
                total += 1
                dated = r.get("due") or r.get("date") or r.get("announced") or ""
                print("[%s] %s" % (sec, r.get("k")))
                if dated:
                    print("    dated: %s" % dated)
                for f in ("status", "verdict", "days", "first_seen", "last_seen"):
                    if r.get(f) not in (None, ""):
                        print("    %s: %s" % (f, r[f]))
                txt = re.sub(r"<[^>]+>", "", str(r.get("t") or r.get("v") or ""))
                print("    %s" % txt[:400].replace("\n", " "))
                if r.get("aliases"):
                    print("    aliases: %s" % r["aliases"])
                print()
    print("== %d row(s) matched %s ==" % (total, terms))
    if total == 0:
        print("NOTE: zero hits is NOT proof the story is new -- try a different "
              "noun, a CVE id, and the vendor name separately (10-06/10-09).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
