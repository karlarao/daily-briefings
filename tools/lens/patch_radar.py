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
# A CVSS score as the briefs actually write it: "CVSS 9.9", "CVSS 3.1 9.8",
# "CVSS 4.0 9.4", "(9.8 CRITICAL)", "cvss:3.1/...  9.8". Deliberately loose on
# the prefix and strict on the number so a version string ("Doris 3.1.x") and a
# day count ("47 days") cannot be read as a severity.
_CVSS_RE = re.compile(
    r"cvss[^0-9]{0,12}(?:[2-4]\.[01][^0-9]{0,8})?(10(?:\.0)?|[0-9]\.[0-9])"
    r"|\b(10\.0|[0-9]\.[0-9])\s*(?:CRITICAL|HIGH)\b", re.I)


def max_cvss(row: dict) -> float:
    """Highest CVSS asserted anywhere in the row, or 0.0 when none is.

    A row may name several scores (a vendor score and a CISA-ADP score that
    disagree by seven points -- see the 2026-10-11 note). The radar ranks on the
    WORST claim in the row, because that is the one that decides whether a reader
    stops reading email; which authority is right is the row's prose to argue.
    """
    hay = " ".join(str(row.get(k) or "") for k in ("t", "due"))
    best = 0.0
    for m in _CVSS_RE.finditer(hay):
        val = m.group(1) or m.group(2)
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        if 0.0 <= v <= 10.0:
            best = max(best, v)
    return best


def sev_tier(row: dict) -> int:
    """Coarse severity tier, LOWER sorts first (0 = most severe).

    Coarse on purpose. A 9.9 and a 9.8 are the same reader action, so bucketing
    keeps the band's recency signal meaningful inside a severity class instead of
    letting a 0.1 difference reorder the whole band.

    CORRECTION, 2026-10-12, within hours of shipping the first version:
    `assert_must_show` rejected the build and was right. The first cut returned
    the BOTTOM tier for a row with no CVSS at all, which reads "unscored" as
    "low" -- and on the real board 10 of 32 no-fix rows carry no score of any
    kind, among them a silent Prometheus TSDB data-loss bug, an unauthenticated
    pre-credential PgBouncer crash, and a kernel THP bug that discards dirty
    folios. Two of those were must-show rows and the cap dropped them.

    Absence of a score is not evidence of low severity; it is an unmeasured
    item. This window's own strongest finding is that the most consequential
    things frequently carry no CVSS -- AMD's TLBI erratum has no CVE at all,
    and three of Argo CD's four 9.9s were never assigned one. So an unscored row
    sorts in the MIDDLE tier: never above a measured Critical, never below a
    measured Low.
    """
    v = max_cvss(row)
    if v >= 9.0:
        return 0
    if v == 0.0 or v >= 7.0:        # unmeasured ranks with High, not with Low
        return 1
    return 2


NO_FIX_RE = re.compile(r"no (?:\w+ )?fix|unpatchable|no patch\b|never (?:be )?patched", re.I)


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
    # 2026-10-14: this clause required 0 <= n <= 14, so a KEV clock fell OUT of
    # band 0 the day after its deadline passed -- apple-coregraphics-86950, an
    # actively-exploited entry whose due date was 2026-10-13, dropped from band 0
    # to band 3 overnight and assert_must_show caught it. A KEV entry is MORE
    # urgent the day after its deadline, not less: the obligation is now breached
    # and (for forensicTriage entries) it has grown a triage requirement. Accept
    # any n <= 14, so an overdue KEV clock sorts with the other overdue rows and
    # a just-expired one sits next to the 8-days-overdue entries where a reader
    # wants it. Ordering inside band 0 is unchanged.
    if (n is not None and n <= 14
            and KEV_RE.search((row.get("due") or "") + " " + (row.get("t") or ""))):
        return (0, n, 0)
    # 2026-10-14: this was a bare `"no fix" in due` substring test, and it missed
    # "no reachable fix" -- which is STRICTLY BETTER prose and the wording a run
    # reaches for when the fix exists but cannot be applied (AIStore 4.x with a
    # collapsed host_net cannot boot into the 5.0 that carries the fix). That row
    # fell out of band 1 entirely. This is the fourth consecutive edition where
    # assert_must_show caught a band-1 wording mismatch, but the first where the
    # ROW was right and the PREDICATE was wrong, so the fix belongs here rather
    # than in the row: a future run will write "no reachable fix" again, because
    # it is the more accurate phrase. Kept tight and anchored to `due` only --
    # the 10-13 note measured a loose prose-wide predicate matching 23 of 160
    # rows because rows legitimately DISCUSS unpatched things.
    if NO_FIX_RE.search(due):
        # 2026-10-12: band 1 gained a severity key. Until today it sorted ONLY on
        # `_touched`, so the no-fix register's internal order was arbitrary within
        # each half -- and `assert_must_show` caught the consequence on 2026-10-11:
        # a row carrying four CVSS 9.9s (Argo CD, no CVE ids, absent from OSV and
        # NVD) ranked #36 inside a 32-row no-fix band and fell off a 26-row cap.
        # The 10-11 note named the fix as "a severity key inside band 1, not a
        # bigger cap"; this is it. Severity outranks recency here because the
        # register is long and slow-moving: a 9.9 a reader has seen before still
        # matters more than a 5.3 they have not. Tiers are coarse (see sev_tier)
        # so `_touched` still orders rows of comparable severity.
        # 2026-10-13: band 1 outgrew its own ordering. The register is now 35
        # rows against a 26-row cap with 12 rows ahead of it in band 0, so the
        # visible window ends INSIDE band 1 -- and because severity was the
        # primary key, roughly fifteen untouched tier-0 rows sat ahead of every
        # row that MOVED today. assert_must_show caught the consequence twice in
        # one build: a CVSS 10.0 unauthenticated-remote row added today and an
        # 8.8 enriched today both fell off. That is the ranking fault the 10-08
        # note already named for band 3 -- "within a long band, the rows that
        # MOVED are the ones a reader has not seen" -- and band 1 had the
        # tie-break but ranked it BELOW severity. Fixed by promoting touched
        # rows of Critical/High/unscored severity (tier <= 1) to the front of
        # band 1; everything else keeps the 10-12 order exactly. Severity still
        # governs within each half, so a touched 5.3 cannot outrank an untouched
        # 9.9 -- only a touched 9.9/8.8/unscored can.
        tier = sev_tier(row)
        moved_and_serious = 0 if (row.get("_touched") and tier <= 1) else 1
        return (1, moved_and_serious, tier, 0 if row.get("_touched") else 1)
    if n is not None and 0 <= n <= 30:
        return (2, n, 0)
    # 2026-10-08: band 3 gained the same touched tie-break band 1 already had.
    # The ranking had no slot for "new this edition, a fix exists, action still
    # outstanding" -- the MCP TypeScript SDK credential-exfil row (fix in 1.31.0,
    # but pre-upgrade credentials stay exposed) landed here and fell off a 24-row
    # cap, and assert_must_show caught it. Band 1's own rationale applies verbatim:
    # within a long band, the rows that MOVED are the ones a reader has not seen.
    return (3, (0 if row.get("_touched") else 1), -(n if n is not None else -999))


def mark_touched(rows: list, new_keys: set, *markers: str) -> None:
    """Flag rows added, corrected or re-measured this edition.

    Within the long, static no-fix band this is the right recency signal: the
    rows that moved are the ones a reader has not already seen.

    2026-10-14: this took a SINGLE `corrected_marker`, but a build writes more
    than one. Today's edition prefixes corrections with "CORRECTED 10-14" and
    re-measurements with "RE-CONFIRMED 10-14", and the Mongoid row -- an
    unauthenticated 9.8 whose scanner-blindness was newly measured WITH a
    positive control -- carried the second marker, so it was never flagged
    touched and fell off a 26-row cap. assert_must_show caught it. A row whose
    claim was re-measured this edition has moved just as much as one whose text
    was corrected: both are things the reader has not seen. Accepts any number
    of markers; a single string still works positionally.
    """
    for r in rows:
        t = r.get("t") or ""
        r["_touched"] = (r["k"] in new_keys) or any(m in t for m in markers)


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
