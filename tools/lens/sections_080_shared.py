# -*- coding: utf-8 -*-
"""Edition 080 shared (chair-independent) sections, generated FROM the ledger.
cite() is called inline by each row generator as it emits -- never retrofitted.
That is the mechanism that has kept guard 5 passing on first assembly since 09-15.
"""
import os as _os
# Resolve sibling modules relative to THIS file so a future run can import these
# from tools/lens/ instead of from one session's dead scratchpad. The original
# build ran with absolute scratchpad paths; that is what made edition 079's
# sections_079.py unusable as anything but a transcript.
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_SP = _os.environ.get("LENS_SCRATCH", _HERE)
import sys, json, re
from datetime import date
SP = _SP
sys.path.insert(0, SP + "/tools/lens")
from lens_links import cite, ARCHIVE_START
import daycounts

TODAY = "2026-10-01"
T = date(2026, 10, 1)
L = json.load(open(SP + "/lens/ledger_wip.json"))

def seen_cite(r):
    """Pass a SEEN date, never an event date -- the 09-12 cite() rule."""
    return cite(r.get("url"), r.get("last_seen"), r.get("first_seen"), TODAY)

def iso(v):
    m = re.search(r"(20\d\d)-(\d\d)-(\d\d)", str(v or ""))
    return date(*map(int, m.groups())) if m else None

def chip(n):
    if n is None: return '<span class="chip tbd">TBD</span>'
    if n < 0:  return '<span class="chip past">%dd past</span>' % -n
    if n == 0: return '<span class="chip hot">TODAY</span>'
    if n <= 14: return '<span class="chip hot">%dd</span>' % n
    if n <= 30: return '<span class="chip warm">%dd</span>' % n
    return '<span class="chip cool">%dd</span>' % n

# ---------------- EVENT HORIZON: next ~60 days + past-due, 5 columns ----------------
def build_events():
    rows, retired = [], []
    for r in L["events"]:
        d = iso(r.get("date"))
        n = (d - T).days if d else None
        if n is not None and (n < -14 or n > 60):
            retired.append(r); continue
        rows.append((n if n is not None else 9999, r, n))
    rows.sort(key=lambda x: (x[0] >= 0, abs(x[0]) if x[0] != 9999 else 10**6, x[0]))
    out = ['<p class="lede">Every dated item across the 19 briefs on one timeline. '
           'Past-due rows stay visible until they are 14 days old, because a deadline that '
           'slipped past is more actionable than one still approaching. '
           + cite(None, TODAY) + '</p>']
    out.append('<table class="tbl"><thead><tr><th>Date</th><th>Days</th><th>Event</th>'
               '<th>What to do with it</th><th>Src</th></tr></thead><tbody>')
    for _, r, n in rows:
        act = r.get("act") or "Read the row and decide; no action recorded yet."
        out.append('<tr><td class="mono">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                   % (r.get("date") or "TBD", chip(n), r.get("t") or r["k"], act, seen_cite(r)))
    out.append('</tbody></table>')
    out.append('<p class="foot">%d rows shown; %d past-dated rows outside the -14..+60 window this edition '
               'and kept in the embedded ledger. %s</p>' % (len(rows), len(retired), cite(None, TODAY)))
    return "".join(out), len(rows), len(retired)

# ---------------- PATCH-RISK RADAR: hand-pinned head + ranked tail ----------------
# The 09-29 defect: sorting dated rows by days_out ASCENDING puts the MOST NEGATIVE
# first, which filled the radar with July rows and silently dropped the board's
# headline. No ranking function knows that a 35-day-delinquent CVSS 10.0 KEV entry
# outranks a 4-day-old one, because |days| is a countdown and delinquency is not.
PIN_HEAD = [
 "cve-2026-21962-ohs-weblogic-kev",
 "jfrog-artifactory-82329-kev",
 "jfrog-42018-42016-kev-due-sep25",
 "litellm-59822-mcp-auth-bypass-kev",
 "mlflow-64849-ssrf-kev-overdue",
 "linux-kernel-kev-trio-sep21",
 "wso2-cve-2026-5430-kev-past-due",
 "starlette-badhost-48710-kev",
 "angular-v19-permanent-eol-unpatched",
 "postgres-mcp-85620-unpatched-9-2",
 "mongodb-82-no-fixed-version",
]
def build_patch(cap=26):
    idx = {r["k"]: r for r in L["patch"]}
    head, missing = [], []
    for k in PIN_HEAD:
        if k not in idx:
            raise SystemExit("ERROR: pinned patch head not on the board: %s" % k)
        head.append(idx[k])
    seen = {r["k"] for r in head}
    def rank(r):
        d = iso(r.get("due"))
        n = (d - T).days if d else None
        nofix = 1 if re.search(r"no fix|unpatched|no fixed|paywall|enterprise", str(r.get("due") or ""), re.I) else 0
        return (-nofix, abs(n) if n is not None else 9999)
    tail = sorted((r for r in L["patch"] if r["k"] not in seen), key=rank)[:max(0, cap - len(head))]
    rows = head + tail
    out = ['<p class="lede">Capped at the %d most actionable rows and it says so on its face &mdash; '
           'the board carries %d. The head of this table is <b>hand-pinned and asserted present</b>, '
           'not ranked: no sort function knows that a 35-day-delinquent CVSS 10.0 KEV entry outranks '
           'a 4-day-old one, because |days| is a countdown and delinquency is not. %s</p>'
           % (len(rows), len(L["patch"]), cite(None, TODAY))]
    out.append('<table class="tbl"><thead><tr><th>Due</th><th>Days</th><th>Item</th><th>Src</th></tr>'
               '</thead><tbody>')
    for r in rows:
        d = iso(r.get("due"))
        n = (d - T).days if d else None
        out.append('<tr><td class="mono">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                   % (r.get("due") or "&mdash;", chip(n), r.get("t") or r["k"], seen_cite(r)))
    out.append('</tbody></table>')
    def is_nofix(r):
        d = str(r.get("due") or "").strip().lower()
        if d.startswith("no fix path"):      # scanner blindness, not a missing fix
            return False
        return d.startswith("no fix") or d in ("fix exists, paywalled", "unmaintained")
    nofix = [r for r in L["patch"] if is_nofix(r)]
    out.append('<p class="foot"><b>No-fix register: %d rows board-wide.</b> That is the '
               'authoritative count, taken from the <code>due</code> field rather than from prose '
               '&mdash; a predicate matching "no fix" anywhere in a row\'s text returns far more, '
               'because plenty of rows <i>discuss</i> an unpatched thing without being one (the '
               '09-18 rule: state the board-wide total and today\'s additions as two numbers from '
               'one source). %s</p>' % (len(nofix), cite(None, TODAY)))
    return "".join(out), len(rows), missing, len(nofix)

EVENTS_H, EV_N, EV_RET = build_events()
PATCH_H, PA_N, PA_MISS, NOFIX_N = build_patch()
