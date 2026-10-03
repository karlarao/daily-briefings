"""Per-run lens helpers. SP and the date constants are session-specific: copy this
file into the run's scratchpad and set SP / TODAY / GEN / ED / PARENT_ED / PARENT_DSLUG
for the edition being built. Landed on main-track 2026-10-03 for `recount_days`, which
is the durable part.

WHY recount_days EXISTS (measured 2026-10-03): three of the six stated KEV day counts in
the published edition-081 ledger were WRONG rather than merely stale, because the 10-02
run recomputed the four rows it remembered. Recompute ALL of them, mechanically, every
run -- and note that `lens_guard.daycounts` then catches what this misses, including, on
the day it was written, a CONTENT error (a row stating a 46-day Aurora lag that had since
closed at 47) rather than an arithmetic one.

GOTCHA worth keeping (cost two cycles on 2026-10-03): `\u0027` inside a single-quoted
Python literal IS an apostrophe and closes the string. When generating HTML, use the
entity the page already uses (&rsquo;) rather than any escape. The 2026-09-17 note covers
`\u` in a re.sub REPLACEMENT string; this is the plain-literal case.
"""

import datetime, json, os, re, sys

SP = "/tmp/claude-0/-home-user-daily-briefings/fc1894f4-c7de-5255-bfeb-3b0e5f953bd0/scratchpad"
sys.path.insert(0, os.path.join(SP, "tools/lens"))
sys.path.insert(0, os.path.join(SP, "tools/ledger"))

import lens_guard as G
import lens_links as L
import ledger_surgery as S

TODAY = "2026-10-03"
GEN = "2026-10-03 09:10 EDT"
ED = "082"
PARENT_ED = "081"
PARENT_DSLUG = "2026-10-02"
MODEL = "claude-opus-5"
PARENT = os.path.join(SP, "lens/index.html")
OUT = os.path.join(SP, "lens/oracle-lens-082.html")
BRIEFS = os.path.join(SP, "tools/ledger/briefs")

T = datetime.date.fromisoformat(TODAY)


def days_out(d):
    """+N for a future date, -N for a past one. Never len()-based (09-27 rule)."""
    return (datetime.date.fromisoformat(d) - T).days


def load_parent():
    h = open(PARENT, encoding="utf-8").read()
    led = G.load_ledger(h)
    return h, led


def recount_days(text):
    """Rewrite every 'YYYY-MM-DD ... Nd' figure from its own anchor.

    Why (measured 2026-10-03): three of the six stated KEV counts in the published
    edition-081 ledger were wrong, not merely stale -- the 10-02 note recomputed
    the four it remembered and left litellm (15 vs 16), the kernel trio (10 vs 11)
    and mlflow (29 vs 30) behind. Recompute ALL of them, never a remembered subset.
    """
    def fix(m):
        anchor, pre, n, suf = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        actual = abs((T - datetime.date.fromisoformat(anchor)).days)
        return anchor + pre + str(actual) + suf
    return re.sub(r"(\d{4}-\d{2}-\d{2})([^.;)]{0,80}?\()(\d+)(d\b)", fix, text)
