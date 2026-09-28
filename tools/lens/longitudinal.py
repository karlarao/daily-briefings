#!/usr/bin/env python3
"""Recompute the Longitudinal series from ALL archive/ledger/<date>.json.

Per day: total items, oracle-lane items, the six competitor lanes summed,
dbhw items, high-sev count, urgent LANES (not urgent items -- the 09-13
correction: lanes is the comparable figure the flag rule produces).

NOTE (09-11, restated 09-20): the `high` column is NOT comparable across days
-- each run re-derives the severity heuristic rather than reading a stored
value, so a classifier change looks like a change in the world. Items / Oracle
/ lanes are the real trend lines.
"""
import json, glob, os, sys

COMP = ["snowflake", "databricks", "bigquery", "redshift", "fabric", "challengers"]
d = sys.argv[1] if len(sys.argv) > 1 else "archive/ledger"
rows = []
for p in sorted(glob.glob(os.path.join(d, "*.json"))):
    if p.endswith("keys.json"):
        continue
    L = json.load(open(p))
    T = L.get("topics", {})
    tot = sum(len(t.get("items", [])) for t in T.values())
    orc = len(T.get("oracle", {}).get("items", []))
    comp = sum(len(T.get(k, {}).get("items", [])) for k in COMP)
    dbhw = len(T.get("dbhw", {}).get("items", []))
    high = sum(1 for t in T.values() for i in t.get("items", [])
               if i.get("sev") in ("high", "urgent"))
    urg_lanes = sum(1 for t in T.values() if t.get("status") == "urgent")
    rows.append(dict(date=L.get("date", os.path.basename(p)[:10]), items=tot,
                     oracle=orc, comp=comp, dbhw=dbhw, high=high, urgent=urg_lanes))
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "longitudinal.json"), "w"), indent=0)
print("days:", len(rows))
for r in rows[-16:]:
    print("  %(date)s items=%(items)4d oracle=%(oracle)3d comp=%(comp)4d "
          "dbhw=%(dbhw)3d high=%(high)4d urgentLanes=%(urgent)2d" % r)
