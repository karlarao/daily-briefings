#!/usr/bin/env python3
"""Override extractor-computed token counts with the harness-reported figures.

Why this exists (measured 2026-09-14): extract_briefs.py reads `usage` from the
LAST assistant record of each agent transcript. The harness reports the agent's
FULL total in its completion notification. Across 19 agents the extractor ran
3.8% low overall, and between -3.5% and +11% per agent -- small, but the routine
spec says to use "the token usage your harness reported", and the notification
figure is the one that matches what the run actually cost.

Usage:
    python3 apply_harness_tokens.py <harness_tokens.json> <sections.json>

harness_tokens.json is {"<topic id>": <int>, ...}, transcribed from each agent's
completion notification. Topics absent from it keep the extractor's value.
"""
import json
import sys


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    hpath, spath = sys.argv[1], sys.argv[2]
    harness = json.load(open(hpath))
    secs = json.load(open(spath))

    patched, delta = 0, 0
    for s in secs:
        if s["id"] in harness:
            delta += harness[s["id"]] - int(s.get("tokens") or 0)
            s["tokens"] = harness[s["id"]]
            patched += 1

    json.dump(secs, open(spath, "w"), indent=1)
    total = sum(int(s.get("tokens") or 0) for s in secs)
    print("patched %d/%d sections; net %+d tokens; total=%d (~%dk)"
          % (patched, len(secs), delta, total, round(total / 5000.0) * 5))
    missing = [s["id"] for s in secs if s["id"] not in harness]
    if missing:
        print("no harness figure (kept extractor value): %s" % ", ".join(missing))


if __name__ == "__main__":
    main()
