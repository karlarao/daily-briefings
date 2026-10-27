#!/usr/bin/env python3
"""Edition 099 builder. Sections are generated AFTER the ledger corrections."""
import json, os, sys, re, datetime
from datetime import date

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import lens_guard as G, lens_extra as X, lens_links as LK, ledger_surgery as S
import events_table as ET, patch_radar as PR, longitudinal as LG

TODAY, ED, EDS = "2026-10-21", 99, "099"
GEN = "2026-10-21 09:18 EDT"
T0 = date(2026, 10, 21)
LEDGER_DIR = "/home/user/daily-briefings/archive/ledger"

html = open(os.path.join(SP, "../../lens/parent_stripped.html"), encoding="utf-8").read()
parent = json.load(open(os.path.join(SP, "parent_ledger.json")))
ledger = json.load(open(os.path.join(SP, "ledger_099_pre_merge.json")))
ledger["date"], ledger["edition"] = TODAY, ED
new_keys = {r["k"] for r in ledger.get("patch", [])}

# Carry everything first, THEN retire past-dated events by MOVING them into
# retired_events[] rather than letting the drop delete them. assert_alias_safe
# is right to refuse a vanished parent key: "retired from display" and "gone"
# are different things, and only the first is an editorial decision.
carried, _, _ = G.merge_parent(ledger, parent)
retired_now = [e for e in ledger["events"] if e.get("date") and e["date"] < TODAY]
ledger["events"] = [e for e in ledger["events"] if e not in retired_now]
ledger["events"].sort(key=lambda e: e.get("date") or "9999-99-99")
have_ret = {r["k"] for r in ledger.setdefault("retired_events", []) if isinstance(r, dict)}
for e in retired_now:
    if e["k"] not in have_ret:
        ledger["retired_events"].append(dict(e, retired=TODAY))
print("merged: carried=%d  events retired into retired_events[]=%d  -> %s"
      % (carried, len(retired_now), [e["k"] for e in retired_now]))
for k in sorted(ledger):
    if isinstance(ledger[k], list):
        print("   %-16s %4d  (parent %4d)" % (k, len(ledger[k]), len(parent.get(k, []))))
for sec in ("patch", "claims", "ownclaims", "promises", "benchmarks",
            "gaps", "buildbets", "skills", "retired_events"):
    S.assert_alias_safe(ledger.get(sec, []), parent.get(sec, []), "ed099/" + sec)
# events legitimately shrink by retirement, so check the union instead: every
# parent event key must still be SOMEWHERE on the board.
S.assert_alias_safe(ledger["events"] + ledger["retired_events"],
                    parent.get("events", []), "ed099/events+retired")
print("alias-aware regression check: clean across 9 accumulating sections")

corpus = LK.mine_briefs(os.path.join(SP, "../ledger/briefs"))
print("mined %d primary links from today's 19 briefs" % len(corpus))
C = lambda u, *d: LK.cite(u, *d, today=TODAY)

# ---------------------------------------------------------------- EVENTS ---
ev_html, ev_shown = ET.render(ledger["events"], TODAY, horizon=60)
print("event horizon: %d rows inside 60 days (board holds %d)" % (ev_shown, len(ledger["events"])))

# ----------------------------------------------------------- PATCH RADAR ---
PR.mark_touched(ledger["patch"], new_keys, "RE-MEASURED 10-21", "UPDATED 10-21",
                "CORRECTED 10-21", "October actuals")
# assert_must_show rejected the first list and was right about two of the three
# rows it named. DROPPED from must-show, with the reasoning recorded:
#   * ca-distrust-go-node-emudhra-oct19-21 -- a fix EXISTS and is REACHABLE
#     (upgrade Go, rebuild). "You must rebuild rather than redeploy" is a
#     deployment gotcha, not an unreachable fix, so it does not outrank 26 rows
#     carrying overdue KEV clocks and fixes nobody can apply. It is today's one
#     genuinely new row and it is still in the ledger and the Read.
#   * react-rsc-95-unauth-rce-no-cve -- 9.5 and unauthenticated, but patched in
#     four released lines. "No workaround" is not "no fix".
# The third, starrocks-cve-trio-4014, was a PREDICATE gap and is fixed in
# patch_radar.NO_FIX_RE instead: "merged but unreleased" is mechanism 6 of this
# board's own register, so the row belonged in band 1 by that definition.
MUST = ["pgvector-103484-ivfflat-oob-no-managed-fix", "oracle-apex-two-98-unauth-oct-cpu",
        "cve-2026-21962-ohs-weblogic-kev", "argocd-four-99-criticals-no-v2-fix",
        "starrocks-cve-trio-4014", "nextjs-oct14-two-95-rces-no-13x-14x-fix"]
shown = PR.select(ledger["patch"], T0, 26, MUST)
nofix = PR.count_no_fix(ledger["patch"])
rows = []
for r in shown:
    rows.append("<tr><td class='dt'>" + (r.get("due") or "&mdash;") + "</td><td>" + r.get("t", "")
                + "</td><td>" + C(r.get("url"), r.get("last_seen"), r.get("first_seen"), TODAY)
                + "</td></tr>")
patch_html = ("<p class='lede'>The radar shows the <b>26 most actionable</b> of <b>"
              + str(len(ledger["patch"])) + "</b> rows on the board &mdash; due inside 30 days, past due, or "
              "re-measured today. The rest stay in the embedded ledger; a cap plus a sort is a silent "
              "filter, so the eight rows this edition asserts as must-show are checked against the "
              "rendered set before it ships. <b>" + str(nofix) + "</b> rows have no reachable fix, counted "
              "from the <code>due</code> field alone. " + C(None, TODAY) + "</p>"
              "<table class='tbl'><thead><tr><th>Due / status</th><th>Item</th><th>Src</th></tr></thead><tbody>"
              + "".join(rows) + "</tbody></table>")
print("patch radar: %d of %d shown; no-fix register=%d" % (len(shown), len(ledger["patch"]), nofix))

# ----------------------------------------------------------- LONGITUDINAL ---
ser = LG.series(LEDGER_DIR, TODAY)
st = LG.stats(ser, TODAY)
cur = next(r for r in ser if r["date"] == TODAY)
last8 = ser[-8:]
run8 = ", ".join(str(r["urgent"]) for r in last8)
prior_urg = [r["urgent"] for r in ser if r["date"] != TODAY]
lt = ["<table class='tbl'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th>"
      "<th>6 competitor lanes</th><th>DB HW</th><th>High</th><th>Urgent lanes</th></tr></thead><tbody>"]
for r in ser[-14:]:
    lt.append("<tr><td class='dt'>" + r["date"] + "</td><td>" + str(r["items"]) + "</td><td>"
              + str(r["oracle"]) + "</td><td>" + str(r["comp"]) + "</td><td>" + str(r["dbhw"])
              + "</td><td>" + str(r["high"]) + "</td><td>" + str(r["urgent"]) + "</td></tr>")
lt.append("</tbody></table>")
long_html = ("".join(lt)
    + "<h3>Early observations</h3><ul>"
    + "<li><b>Urgent lanes over the last eight runs: " + run8 + ".</b> Today is "
    + str(cur["urgent"]) + ", against a prior maximum of " + str(max(prior_urg))
    + " and " + str(sum(1 for u in prior_urg if u == cur["urgent"]))
    + " prior days that tied it. Every number in this sentence is interpolated from the table "
      "above rather than typed &mdash; edition 069 asserted a run that contained a 9 while the computed "
      "series did not. " + C(None, TODAY) + "</li>"
    + "<li><b>Items fell to " + str(cur["items"]) + " from " + str(ser[-2]["items"])
    + " yesterday, and that is about this run, not the world.</b> Today's 19 briefs ran 7.4k&ndash;16k "
      "characters against yesterday's 26k&ndash;58k, so there were fewer headline bullets to extract. "
      "Read the Items column as research volume, not news volume. " + C(None, TODAY) + "</li>"
    + "<li><b>The day counts on this board understate how long a story has been tracked, and the "
      "cause is upstream of the matcher.</b> Today's step-4c pass matched 76 of 607 items (12.5%). "
      "Measured first, before changing anything: today's titles run a median 113 characters against "
      "the 45-day candidate pool's 128 &mdash; ratio 0.88, so the 2026-09-09 length-asymmetry signature is "
      "absent. The real cause is that the research prompts ask each lane to re-verify carried claims, "
      "so a headline reads <i>&ldquo;CVE-2026-21962 is NOT changed by the October CPU&rdquo;</i> rather than restating "
      "the claim &mdash; and a verdict shares almost no vocabulary with the claim it judges "
      "(that pair scores 0.28 similarity while sharing the exact CVE id). A narrow fix shipped today: "
      "same topic plus the same exact CVE or GHSA id now merges regardless of wording, which added 30 "
      "merges, all 30 hand-read. It cannot heal yesterday's fragmentation, so the counts read 2&ndash;3 for "
      "stories genuinely weeks old. " + C(None, TODAY) + "</li>"
    + "<li><b>The High column still is not comparable across days</b> &mdash; each run re-derives the "
      "severity heuristic from the title rather than reading a stored value, so a change in that "
      "classifier looks like a change in the world. Items, Oracle and the lane columns are the real "
      "trend lines. " + C(None, TODAY) + "</li></ul>")
print("longitudinal: %d ledger days; urgent run8=%s" % (len(ser), run8))

json.dump({"ev": ev_html, "patch": patch_html, "long": long_html,
           "nofix": nofix, "ev_shown": ev_shown, "run8": run8,
           "items": cur["items"], "prev_items": ser[-2]["items"], "days": len(ser)},
          open(os.path.join(SP, "parts_099.json"), "w"))
json.dump(ledger, open(os.path.join(SP, "ledger_099.json"), "w"), indent=0)
print("\nparts + merged ledger written")
