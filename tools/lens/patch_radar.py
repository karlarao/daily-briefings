#!/usr/bin/env python3
"""Patch-Risk Radar row selection and ranking.

Extracted to version control on 2026-10-06 after the radar shipped THREE wrong
orderings in one build, each caught only by reading the rendered rows:

  1. Past-due rows sorted by days ASCENDING put the most overdue first, so the
     radar filled with July rows (mean 491 bytes/row against the parent's 1,240)
     and pushed that day's unauthenticated vLLM RCE off a 24-row cap entirely.
     A radar ranks by what needs doing now: among overdue rows, most RECENT first.

  2. Ranking the no-fix register above past-due clocks then filled all 24 slots
     with no-fix rows and dropped every expired KEV date, including our own
     40-day-overdue CVE-2026-21962. A no-fix row has no deadline to miss; an
     expired KEV date is already late. Past-due outranks it.

  3. THE ROOT ERROR: treating every past date in `due` as "overdue". A bare
     "2026-09-14" in that field overwhelmingly means *fixed then*, not *due
     then*, so twenty historical disclosure records outranked live ones. The
     discriminator is the explicit marker, not the date's position vs today.

The durable part is `assert_must_show`, not the ranking. A cap plus a sort is a
silent filter; a cap plus a sort plus a named must-show list is a filter you can
trust. It fired on attempt 3 and named the row that had fallen off.
"""
from __future__ import annotations
import re
from datetime import date

OVERDUE_RE = re.compile(r"past due|passed|overdue", re.I)
# A live KEV / actively-exploited clock, for the band-0 promotion below.
KEV_RE = re.compile(r"\bKEV\b|actively[- ]exploited|under .{0,24}exploitation", re.I)
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class RadarError(RuntimeError):
    pass


def days_until(due: str, today: date):
    m = DATE_RE.search(due or "")
    return (date(*map(int, m.groups())) - today).days if m else None


def rank(row: dict, today: date):
    """Sort key: (band, within-band key). Lower sorts first.

    band 0  explicitly past-due  -- newest overdue first
    band 1  the no-fix register  -- rows touched this edition first
    band 2  dated, inside 30 days
    band 3  everything else (bare past dates = disclosure records)
    band 4  explicitly RESOLVED
    """
    due = (row.get("due") or "").lower()
    n = days_until(due, today)
    if "resolved" in due:
        return (4, 0, 0)
    if OVERDUE_RE.search(due):
        return (0, -(n if n is not None else 0), 0)
    # 2026-10-09: band 0 also takes a LIVE KEV/exploited clock inside 14 days.
    # assert_must_show caught an actively-exploited CISA KEV entry due in 4 days
    # (apple-coregraphics-86950) ranking #39, behind all 28 rows of the no-fix
    # register, because band 2 sorts after band 1. That is a ranking gap, not a
    # cap problem: the no-fix register is a long, slow-moving list, while a dated
    # KEV clock inside the bar is the most time-critical thing on the board and
    # is the SAME urgency class and the same reader action as the overdue KEV
    # rows already in band 0. Ordering inside band 0 is unchanged (soonest or
    # least-overdue first), so a 4-days-out clock sits adjacent to an 8-days-
    # overdue one, which is how a reader wants to read them.
    if (n is not None and 0 <= n <= 14
            and KEV_RE.search((row.get("due") or "") + " " + (row.get("t") or ""))):
        return (0, n, 0)
    if "no fix" in due:
        return (1, 0 if row.get("_touched") else 1, 0)
    if n is not None and 0 <= n <= 30:
        return (2, n, 0)
    # 2026-10-08: band 3 gained the same touched tie-break band 1 already had.
    # The ranking had no slot for "new this edition, a fix exists, action still
    # outstanding" -- the MCP TypeScript SDK credential-exfil row (fix in 1.31.0,
    # but pre-upgrade credentials stay exposed) landed here and fell off a 24-row
    # cap, and assert_must_show caught it. Band 1's own rationale applies verbatim:
    # within a long band, the rows that MOVED are the ones a reader has not seen.
    return (3, (0 if row.get("_touched") else 1), -(n if n is not None else -999))


def mark_touched(rows: list, new_keys: set, corrected_marker: str) -> None:
    """Flag rows added or corrected this edition.

    Within the long, static no-fix band this is the right recency signal: the
    rows that moved are the ones a reader has not already seen.
    """
    for r in rows:
        r["_touched"] = (r["k"] in new_keys) or (corrected_marker in (r.get("t") or ""))


def select(rows: list, today: date, cap: int, must_show: list) -> list:
    shown = sorted(rows, key=lambda r: rank(r, today))[:cap]
    assert_must_show(shown, must_show)
    for r in rows:
        r.pop("_touched", None)
    return shown


def assert_must_show(shown: list, must_show: list) -> None:
    keys = {r["k"] for r in shown}
    missing = [k for k in must_show if k not in keys]
    if missing:
        raise RadarError(
            "radar dropped must-show rows: %s -- a cap plus a sort is a silent "
            "filter; fix the ranking, do not raise the cap" % missing)


def count_no_fix(rows: list) -> int:
    """Board-wide no-fix count, derived from `due` and nothing else.

    The 2026-10-05 note measured edition 083 rendering "26 no-fix rows" against
    a ledger holding 22, because the figure was prose. Always derive it.
    """
    return sum(1 for r in rows if "no fix" in (r.get("due") or "").lower())
