#!/usr/bin/env python3
"""Override extractor-computed tokens with the harness-reported figures.

extract_briefs.py sums usage from the LAST assistant record of each agent
transcript; the harness reports the agent's full total in its completion
notification. Measured 2026-09-14: extractor ran 3.8% low overall, per-agent
-3.5% to +11%. The spec says use what the harness reported, so we do.
"""
import json, sys
SP = "/tmp/claude-0/-home-user-daily-briefings/0201b255-e799-57de-ade5-fd7554fff54a/scratchpad"
h = json.load(open(SP + "/harness_tokens.json"))
p = SP + "/tools/ledger/sections.json"
secs = json.load(open(p))
patched = 0
for s in secs:
    if s["id"] in h:
        s["tokens"] = h[s["id"]]
        patched += 1
json.dump(secs, open(p, "w"), indent=1)
tot = sum(s.get("tokens", 0) or 0 for s in secs)
print("patched %d/%d sections with harness tokens; total=%d (~%dk)"
      % (patched, len(secs), tot, round(tot / 5000.0) * 5))
