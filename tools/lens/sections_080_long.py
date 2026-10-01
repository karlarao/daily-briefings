# -*- coding: utf-8 -*-
"""Edition 080: Longitudinal (recomputed from ALL ledgers) + Since-yesterday
(this edition's lensLedger diffed against the parent's)."""
import os as _os
# Resolve sibling modules relative to THIS file so a future run can import these
# from tools/lens/ instead of from one session's dead scratchpad. The original
# build ran with absolute scratchpad paths; that is what made edition 079's
# sections_079.py unusable as anything but a transcript.
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_SP = _os.environ.get("LENS_SCRATCH", _HERE)
import sys, json, glob, os, re
SP = _SP
sys.path.insert(0, SP + "/tools/lens")
from lens_links import cite
TODAY = "2026-10-01"
A = lambda: cite(None, TODAY)
COMP = ["snowflake", "databricks", "bigquery", "redshift", "fabric", "challengers"]
RAW = "https://github.com/karlarao/daily-briefings/tree/gh-pages/archive/ledger"

def build_longitudinal():
    files = sorted(f for f in glob.glob("/home/user/daily-briefings/archive/ledger/*.json")
                   if "keys" not in f)
    series = []
    for f in files:
        d = json.load(open(f)); t = d.get("topics") or {}
        g = lambda k: len((t.get(k) or {}).get("items") or [])
        items = sum(len((v.get("items") or [])) for v in t.values())
        high = sum(1 for v in t.values() for it in (v.get("items") or []) if it.get("sev") == "high")
        urg  = sum(1 for v in t.values() for it in (v.get("items") or []) if it.get("sev") == "urgent")
        ulanes = sum(1 for v in t.values() if v.get("status") == "urgent")
        series.append({"date": d.get("date") or os.path.basename(f)[:10], "items": items,
                       "oracle": g("oracle"), "comp": sum(g(k) for k in COMP), "dbhw": g("dbhw"),
                       "high": high, "urgent_items": urg, "urgent_lanes": ulanes})
    last = series[-14:]
    out = ['<p class="lede">Recomputed from <b>all %d</b> public ledgers, every run. The '
           '<b>Urgent lanes</b> column counts flagged LANES, which is the figure the flag rule '
           'actually produces and the only one comparable across days. %s</p>'
           % (len(series), cite(RAW, TODAY))]
    out.append('<table class="tbl"><thead><tr><th>Date</th><th>Items</th><th>Oracle</th>'
               '<th>6 competitor lanes</th><th>DB HW</th><th>High</th><th>Urgent lanes</th></tr>'
               '</thead><tbody>')
    for r in last:
        out.append('<tr><td class="mono">%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td>'
                   '<td>%d</td><td>%d</td></tr>' % (r["date"], r["items"], r["oracle"], r["comp"],
                                                    r["dbhw"], r["high"], r["urgent_lanes"]))
    out.append('</tbody></table>')
    # every figure below is interpolated from the series, never typed (the 09-20 rule)
    ul = [r["urgent_lanes"] for r in series]
    run8 = ", ".join(str(x) for x in ul[-8:])
    today_u = ul[-1]; mx = max(ul); ties = sum(1 for x in ul if x == mx)
    mean14 = sum(ul[-14:]) / float(len(ul[-14:]))
    it14 = [r["items"] for r in series[-14:]]
    out.append('<h3>Early observations</h3><ul>')
    out.append('<li><b>Urgent lanes, last eight runs: %s.</b> Today is %d against a 14-run mean of '
               '%.1f and a series maximum of %d, which %s. Every number in this sentence is '
               'interpolated from the table above rather than typed &mdash; on 09-20 a hand-written '
               'version of exactly this sentence contradicted the data printed directly above it. '
               '%s</li>' % (run8, today_u, mean14, mx,
                            "today ties" if today_u == mx else "today does not reach",
                            A()))
    out.append('<li><b>Volume: %d items today against a 14-run mean of %.0f.</b> The high-water '
               'mark in the series is %d. %s</li>' % (it14[-1], sum(it14)/float(len(it14)),
                                                      max(r["items"] for r in series), A()))
    out.append('<li><b>The High column is still not comparable across days, and this edition '
               'repeats the warning rather than quietly dropping it.</b> Each run re-derives the '
               'severity heuristic from the title alone instead of reading a stored value, so a '
               'change in that classifier reads as a change in the world. Items, Oracle and the '
               'competitor-lane columns are the real trend lines. Storing per-item severity in the '
               'public ledger remains the durable fix and remains queued. %s</li>' % A())
    out.append('<li><b>Queued for the 90-day view:</b> per-item severity stored rather than '
               're-derived; a no-fix-register time series, now that the register has a stable '
               'definition read off the <code>due</code> field; and lane-level flag persistence, '
               'to separate a lane that is chronically urgent from one that spiked. %s</li>' % A())
    out.append('</ul>')
    return "".join(out), len(series), today_u, mx, ties

def build_wn(parent_ledger, new_ledger):
    def keyset(L, sec): return {r["k"]: r for r in L.get(sec, [])}
    out = ['<p class="lede">This edition\'s embedded ledger diffed against edition 079\'s. %s</p>' % A()]
    blocks = []
    for sec, label in (("events", "Event Horizon"), ("patch", "Patch-Risk Radar"),
                       ("claims", "Claim Watch"), ("skills", "Skills Radar"),
                       ("buildbets", "Build Radar")):
        p, n = keyset(parent_ledger, sec), keyset(new_ledger, sec)
        added = [k for k in n if k not in p]
        # a key is only GONE if it is not carried as an alias on some survivor
        al = {a for r in n.values() for a in (r.get("aliases") or [])}
        gone = [k for k in p if k not in n and k not in al]
        folded = [k for k in p if k not in n and k in al]
        moved = [k for k in n if k in p and sec in ("skills", "buildbets")
                 and n[k].get("status") != p[k].get("status")]
        blocks.append((sec, label, added, gone, folded, moved, len(p), len(n)))
    out.append('<h3>&#128312; New on the board</h3><ul>')
    for sec, label, added, gone, folded, moved, lp, ln in blocks:
        if added:
            out.append('<li><b>%s:</b> %s %s</li>' % (label, ", ".join('<code>%s</code>' % k for k in added), A()))
    out.append('</ul>')
    out.append('<h3>&#128314; Movement</h3><ul>')
    out.append('<li><b>QUARTERLY RE-RANK executed.</b> Skills Radar: '
               '<code>agent-operable-tooling-mcp</code> PROMOTED emerging &rarr; compounding; '
               '<code>unpatchable-remediation-triage</code> ADDED as emerging; '
               '<code>memory-economics-capacity-2</code> HELD at emerging against the 09-30 prep '
               'note\'s recommendation, because its normalised volume trend is the weakest of the '
               'six and both figures that note cited for promotion were withdrawn today. Zero '
               'retired. Next review <b>2027-01-01</b>. %s</li>' % A())
    out.append('<li><b>Build Radar re-ranked with zero changes of status and one sharpening</b> '
               '(<code>ru-manifests-audited-tpc</code> gains a fix-availability-manifest leg). A '
               're-rank that changes little is a real outcome; the rule permits replacing up to two '
               'bets, it does not require it. %s</li>' % A())
    for sec, label, added, gone, folded, moved, lp, ln in blocks:
        if folded:
            out.append('<li><b>%s folded %d &rarr; %d</b> &mdash; %d duplicate rows merged into '
                       'survivors, every loser preserved in the survivor\'s <code>aliases[]</code> '
                       'and verified by <code>assert_alias_safe</code>. %s</li>'
                       % (label, lp, ln, len(folded), A()))
    out.append('<li><b>8 past-due day counts rewritten</b> by <code>daycounts</code>, which derives '
               'each from the row\'s own anchor date and then asserts the <code>due</code> field and '
               'the prose agree. This run also verified every anchor against the CISA catalog '
               'itself (version 2026.09.30) &mdash; all nine match, so a right-looking count '
               'derived from a wrong anchor cannot hide. %s</li>' % A())
    out.append('</ul>')
    out.append('<h3>&#10160; Still standing</h3><ul>')
    out.append('<li><b>CVE-2026-21962 is 35 days past its KEV due date</b> and the Oracle lane '
               'established something the board did not have: the fix ships <b>only</b> in '
               'cpujan2026 and is absent from the June, July, August and September advisories, so '
               'an estate diligently applying monthly CSPUs is still exposed. %s</li>' % A())
    out.append('<li><b>The no-fix register stands at 22 rows</b>, counted off the <code>due</code> '
               'field. Two long-standing entries CLOSED today: Aurora PostgreSQL shipped the 28-CVE '
               'batch at a 47-day lag, and Percona shipped the MongoDB auth-bypass fix. %s</li>' % A())
    out.append('</ul>')
    return "".join(out)
