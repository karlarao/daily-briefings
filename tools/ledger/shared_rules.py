#!/usr/bin/env python3
r"""Computed countdowns for SHARED_RULES.md — never type a relative-time claim.

WHY THIS EXISTS (2026-11-08, edition 117)
-----------------------------------------
SHARED_RULES.md is the one input all 19 research agents read. On 2026-11-08 a
hand-typed line in it said the 2026-11-10 .. 11-12 wall of obligations "has now
PASSED".  The run date was 2026-11-08: every one of those dates was 2-4 days
AHEAD.  Four lanes independently caught it from primary sources (frontend:
"any note saying otherwise is off by two days"; appdev: "only half right";
devops recorded the contradiction "for the record"; oltp led its flag with
"the carry-forward premise was wrong").  Nothing downstream broke, because
SHARED_RULES also tells the agents to verify every date against the vendor --
but a wrong premise in the shared rules costs 19 lanes a correction each.

The durable fix is arithmetic, not proofreading: COMPUTE the "has it passed"
clause from TODAY.  Using this module on 2026-11-09 immediately caught a second
stale derived date -- the 14-day flag bar still read 2026-11-22 (= 11-08 + 14)
where it should have been 2026-11-23.  A derived date rots exactly as silently
as a relative-time phrase.

RULE: any date arithmetic that appears in SHARED_RULES.md comes from here.
Authored prose stays authored; numbers are generated.
"""
import argparse
import datetime
import json
import sys


def out(datestr, today):
    """(days, phrase) for `datestr` relative to `today`. Both ISO strings or dates.

    Negative days mean the date has passed.  The phrase is what goes in front of
    an agent: it says TODAY / TOMORROW / N days out / N days PAST in words, and
    always carries the ISO date so a lane can verify it against the vendor.
    """
    d = _d(datestr)
    t = _d(today)
    n = (d - t).days
    if n < 0:
        return n, "%d day%s PAST (was %s)" % (-n, "" if -n == 1 else "s", d.isoformat())
    if n == 0:
        return n, "TODAY (%s)" % d.isoformat()
    if n == 1:
        return n, "TOMORROW (%s)" % d.isoformat()
    return n, "%d days out (%s)" % (n, d.isoformat())


def bar(today, days=14):
    """The far edge of the flag window: ISO date of today+days.

    The urgent rule is "a hard deadline inside ~14 days".  Spelling that edge as
    a literal date in the rules is a kindness to the lanes and a trap for the
    orchestrator, because it is wrong the next morning.  Generate it.
    """
    return (_d(today) + datetime.timedelta(days=days)).isoformat()


def window(today, days=30):
    """(start, end) ISO strings for a research window ending today."""
    t = _d(today)
    return (t - datetime.timedelta(days=days)).isoformat(), t.isoformat()


def render_block(obligations, today, flag_bar=14):
    """Markdown bullet list of dated obligations, soonest first, countdowns computed.

    `obligations` is an iterable of (iso_date, text).  Anything inside the flag
    bar is marked with a lantern so a lane cannot miss it; anything already past
    says so, with the date it was, because a passed obligation often converts
    into a triage obligation rather than disappearing (see the retired-KEV
    finding of 2026-11-05).
    """
    rows = sorted(((_d(dt), txt) for dt, txt in obligations), key=lambda r: r[0])
    lines = ["**Dated obligations, countdowns computed from %s:**" % _d(today).isoformat(), ""]
    for d, txt in rows:
        n, phrase = out(d, today)
        mark = "**⚑ %s**" % phrase if n <= 1 else phrase
        lines.append("- %s — %s" % (mark, txt))
    lines += ["", "Flag bar for this run: a hard deadline on or before **%s** (today + %d days)."
              % (bar(today, flag_bar), flag_bar)]
    return "\n".join(lines)


def _d(v):
    if isinstance(v, datetime.date):
        return v
    return datetime.date.fromisoformat(str(v)[:10])


# --------------------------------------------------------------------- tests --
def _selftest():
    T = "2026-11-09"
    ok = 0

    def chk(got, want, label):
        nonlocal ok
        assert got == want, "%s: %r != %r" % (label, got, want)
        ok += 1

    chk(out("2026-11-09", T), (0, "TODAY (2026-11-09)"), "today")
    chk(out("2026-11-10", T), (1, "TOMORROW (2026-11-10)"), "tomorrow")
    chk(out("2026-11-12", T), (3, "3 days out (2026-11-12)"), "future")
    chk(out("2026-11-08", T), (-1, "1 day PAST (was 2026-11-08)"), "yesterday singular")
    chk(out("2026-11-01", T), (-8, "8 days PAST (was 2026-11-01)"), "past plural")
    # the 2026-11-08 defect: a 11-10 obligation must NOT read as passed on 11-08
    chk(out("2026-11-10", "2026-11-08")[0] > 0, True, "11-10 is future on 11-08")
    # the 2026-11-09 defect: the bar is today+14, not yesterday+14
    chk(bar("2026-11-09"), "2026-11-23", "bar 14")
    chk(bar("2026-11-08"), "2026-11-22", "bar 14 prior day")
    chk(window("2026-11-09", 30), ("2026-10-10", "2026-11-09"), "window 30")
    # dates accept datetime.date as well as strings
    chk(out(datetime.date(2026, 11, 10), datetime.date(2026, 11, 9))[0], 1, "date objects")
    blk = render_block([("2026-11-12", "PostgreSQL 14 final release"),
                        ("2026-11-10", "Brotli KEV due"),
                        ("2026-11-09", "GHA brownout, runs FAIL"),
                        ("2026-11-01", "Play target API 36")], T)
    # soonest first, past rows still present, lanterns only inside <=1 day
    lines = [l for l in blk.splitlines() if l.startswith("- ")]
    chk(len(lines), 4, "all rows rendered")
    chk(lines[0].startswith("- **⚑ 8 days PAST"), True, "past row sorted first and marked")
    chk("⚑ TODAY" in lines[1], True, "today marked")
    chk("⚑ TOMORROW" in lines[2], True, "tomorrow marked")
    chk(lines[3].startswith("- 3 days out"), True, "future row unmarked")
    chk("2026-11-23" in blk, True, "bar rendered into block")
    print("shared_rules selftest: %d/%d PASS" % (ok, ok))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--today", help="ISO date to treat as today")
    ap.add_argument("--obligations", help="JSON file: [[iso_date, text], ...]")
    ap.add_argument("--flag-bar", type=int, default=14)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.today:
        _selftest()
        sys.exit(0)
    obl = json.load(open(a.obligations)) if a.obligations else []
    print(render_block(obl, a.today, a.flag_bar))
