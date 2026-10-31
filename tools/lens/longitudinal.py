#!/usr/bin/env python3
"""Recompute the Longitudinal series from ALL public ledger files.

Every number in the prose is interpolated from the series this computes -- the
2026-09-20 rule ("any figure in prose next to the table it describes must be
read out of that data"). Two defects in the edition-097 generator are fixed
here:

 1. PRIOR HIGH INCLUDED TODAY. 097 rendered "Today's 1376 items is the series
    peak, past the prior high of 1376 on 2026-10-19" -- comparing today's row
    against itself, because the max was taken over the whole series including
    the current date. `prior` now excludes TODAY by construction.
 2. "series maximum of N (date)" for urgent lanes had the same exposure.

The High column is deliberately NOT presented as comparable across days: each
run re-derives the severity heuristic from the title rather than reading a
stored value, so a shift there is a classifier change, not a change in
the world. Storing per-item severity in the public ledger is the queued fix.
"""
import json, glob, os, sys

COMPETITOR = ["snowflake", "databricks", "bigquery", "redshift", "fabric", "challengers"]


def series(ledger_dir, today=None):
    out = []
    for p in sorted(glob.glob(os.path.join(ledger_dir, "*.json"))):
        if os.path.basename(p) == "keys.json":
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        date = d.get("date") or os.path.basename(p)[:-5]
        topics = d.get("topics", {})
        items = sum(len(v.get("items", [])) for v in topics.values())
        orc = len(topics.get("oracle", {}).get("items", []))
        comp = sum(len(topics.get(t, {}).get("items", [])) for t in COMPETITOR)
        dbhw = len(topics.get("dbhw", {}).get("items", []))
        high = sum(1 for v in topics.values() for i in v.get("items", [])
                   if i.get("sev") in ("high", "urgent"))
        urg = sum(1 for v in topics.values() if v.get("status") == "urgent")
        out.append(dict(date=date, items=items, oracle=orc, comp=comp,
                        dbhw=dbhw, high=high, urgent=urg))
    return out


def stats(rows, today):
    """Return the facts the prose needs, with TODAY excluded from every 'prior'."""
    cur = next((r for r in rows if r["date"] == today), None)
    if cur is None:
        raise SystemExit("no row for today (%s) -- stamp the ledger first" % today)
    prior = [r for r in rows if r["date"] != today]
    if not prior:
        raise SystemExit("no prior rows")
    pmax_items = max(prior, key=lambda r: r["items"])
    umax = max(prior, key=lambda r: r["urgent"])
    last8 = rows[-8:]
    last14 = rows[-14:]
    ties = sum(1 for r in prior if r["urgent"] == cur["urgent"])
    return dict(
        runs=len(rows), cur=cur,
        prior_max_items=pmax_items["items"], prior_max_items_date=pmax_items["date"],
        is_peak=cur["items"] > pmax_items["items"],
        urgent_prior_max=umax["urgent"], urgent_prior_max_date=umax["date"],
        urgent_ties=ties,
        urgent_floor8=min(r["urgent"] for r in last8),
        urgent_mean14=sum(r["urgent"] for r in last14) / len(last14),
        run8=[r["urgent"] for r in last8],
    )


if __name__ == "__main__":
    # NOTE: the series json is written where the CALLER asks, never beside this
    # file. tools/lens/ lives in the repo, and the repo root is a public web
    # root served by GitHub Pages -- a run's scratch output must stay in the
    # session scratchpad. (Landed 2026-10-20 after the first cut defaulted to
    # os.path.dirname(__file__), i.e. straight into the repo.)
    if len(sys.argv) < 4:
        sys.exit("usage: longitudinal.py <ledger-dir> <today YYYY-MM-DD> "
                 "<out-series.json>   # out path must be OUTSIDE the repo")
    led_dir, today, out = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = series(led_dir, today)
    json.dump(rows, open(out, "w"), indent=1)
    if any(r["date"] == today for r in rows):
        s = stats(rows, today)
        print(json.dumps({k: v for k, v in s.items() if k != "cur"}, indent=1))
        print("today:", json.dumps(s["cur"]))
    else:
        print("runs:", len(rows), "- today not yet stamped")
        print("last 3:", json.dumps(rows[-3:]))
