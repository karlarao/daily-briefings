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
    r"cvss[^0-9]{0,12}(?:v?[2-4](?:\.[01])?[^0-9]{0,8})?(10(?:\.0)?|[0-9]\.[0-9])"
    r"|\b(10\.0|[0-9]\.[0-9])\s*(?:CRITICAL|HIGH)\b", re.I)


COMPROMISE_RE = re.compile(
    r"malicious release|credential stealer|shipped (?:a |an )?(?:backdoor|stealer|malware)"
    r"|supply-chain compromise|keys? (?:\w+ ){0,2}compromised"
    r"|compromised (?:intermediate |release |signing )?(?:ca|key|pipeline)",
    re.I)


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


# 2026-10-15: extended to "no advisory". assert_must_show rejected the build and
# was right for the third time, and for the same reason as 2026-10-14 -- the ROW
# was right and the PREDICATE was wrong. The day's lead row is Next.js 16.4.1 /
# 15.5.28, two UNAUTHENTICATED RCEs whose `due` reads "no public advisory --
# upgrade by release note": the GHSA ids 404, the affected ranges are unpublished,
# and npm's own endpoint returns 0 advisories for the vulnerable versions. It
# ranked #57, below 26 rows a reader would act on later, because the register's
# predicate could only see a missing FIX.
#
# An advisory that does not exist is the same reader action as a fix that does not
# exist: you cannot scope your exposure, you cannot verify you are done, and no
# gate will tell you. It belongs in the same band. And it generalises rather than
# patching one row -- this window's whole finding is advisories that have not been
# published, so a run will reach for this phrasing again.
#
# Deliberately NOT matched: "advisory" on its own, or "advisory drop", so an
# ordinary disclosure record cannot wander into the no-fix register. The negation
# has to be adjacent to the noun.
# 2026-10-16: FOURTH predicate gap caught by assert_must_show, and for the
# fourth time the ROW was right and the PREDICATE was wrong. The AMD TLBI
# erratum row states that five kernel branches "are all EOL and will never
# receive it" -- which is a no-fix row by any reading a human would give it,
# and is the natural phrasing when the unreachable thing is a BACKPORT rather
# than a patch that does not exist. "never patched" was already matched;
# "will never receive it" was not. Anchored to an explicit object (it / the
# fix / a backport / ...) so that prose merely containing "never" cannot drift
# into the register -- the 10-13 measurement of a loose predicate matching 23
# of 160 rows is the reason this stays tight.
# 2026-10-21: FIFTH predicate gap caught by assert_must_show, and for the fifth
# time the ROW was right and the PREDICATE was wrong. StarRocks 3.5's `due` reads
# "merged on branch-3.5, UNRELEASED - reachable only via 4.0.16 / 4.1.6": the
# fixes for a 9.8 unauthenticated Ranger RCE are committed and no release carries
# them. That is mechanism 6 of this board's own no-reachable-fix register
# ("patched in git, never released as a binary", added 2026-10-20), so a row
# stating it belongs in band 1 by the register's own definition -- it ranked #30
# instead. It is also the phrasing a run will reach for again, because the only
# way to SEE mechanism 6 is to diff a tag's pom against its branch, and
# "merged but unreleased" is how you then write it up.
# Deliberately anchored: "unreleased" must sit near merged/committed/branch
# wording, so a row merely mentioning an unreleased version cannot drift in.
NO_FIX_RE = re.compile(
    # NOTE the character class: an earlier try used [^.;] and failed on the very
    # row it was written for, because "branch-3.5," contains a period. Version
    # numbers are full of dots; only ';' and newline are safe separators here.
    r"(?:merged|committed|fixed)[^;\n]{0,60}\bunreleased\b"
    r"|\bunreleased\b[^;\n]{0,40}(?:merge|commit|branch)"
    r"|no (?:\w+ )?fix|no backport\b|unpatchable|no patch\b|never (?:be )?patched"
    r"|never (?:receive|get)s? (?:it|them|this|the fix|a fix|the patch|a patch"
    r"|the backport|a backport|the workaround)"
    r"|no (?:public |published |ecosystem )?advisor(?:y|ies)"
    r"|advisor(?:y|ies) (?:not|never) published",
    re.I)


def _selftest_no_fix() -> str:
    pos = ["no fix", "no reachable fix", "NO fix for 13.x or 14.x", "unpatchable",
           "no patch available", "will never be patched",
           "are all EOL and will never receive it",
           "6.15-6.17 will never get the backport",
           "no public advisory", "advisory not published"]
    neg = ["fixed 16.4.1 / 15.5.28", "fixed 6.3.0 / 6.3.1 / 6.3.4",
           "2026-09-30 advisory drop", "advisory published 2026-10-07",
           "the vendor will never publish numbers",
           "never reproduced on unmodified upstream",
           "2026-10-20", "RESOLVED 2026-10-03 - fixed on every affected series"]
    ok = sum(1 for x in pos if NO_FIX_RE.search(x)) + sum(1 for x in neg if not NO_FIX_RE.search(x))
    bad = [x for x in pos if not NO_FIX_RE.search(x)] + [x for x in neg if NO_FIX_RE.search(x)]
    return "%d/%d%s" % (ok, len(pos) + len(neg), ("  FAILED: " + repr(bad)) if bad else "")


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
    # 2026-10-22: band 0 also takes a CONFIRMED IN-THE-WILD COMPROMISE, with or
    # without a clock. assert_must_show caught the day's single worst item
    # ranking #59: LiteLLM 1.107.0 shipped a credential stealer from PyPI and the
    # Docker `latest` tag for ~1h45m, and it scored CVSS 0.0 because the attacker
    # published malware rather than filing a CVE. sev_tier already refuses to read
    # "unscored" as "low" (2026-10-12), but band 1 is long and every measured
    # Critical outranks an unscored row inside it, so the register buried it.
    # The band-0 KEV clause exists because ACTIVE EXPLOITATION outranks severity;
    # a malicious package that has already executed in your environment is PAST
    # exploitation -- the reader action is not "patch" but "assume breach and
    # rotate", which is the most time-critical action the radar can carry. Kept
    # tight and anchored to explicit compromise language (a shipped backdoor or
    # stealer, a compromised key or release) rather than the generic word
    # "exploit", which appears in ordinary advisory prose all over the board.
    if COMPROMISE_RE.search((row.get("due") or "") + " " + (row.get("t") or "")):
        return (0, -10000, 0)
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
    # 2026-10-17: band 3 has had the `_touched` tie-break since 10-08, but band 3
    # is UNREACHABLE under the cap -- band 0 plus a 33-row band 1 fills the whole
    # window -- so the tie-break ordered rows nobody ever saw. assert_must_show
    # caught the consequence on four rows at once: LMCache's unauthenticated 9.8
    # ZeroMQ-pickle RCE, the Claude Agent SDK's 9.2 argument injection and React's
    # own unauthenticated 9.5, all ADDED today, plus LiteLLM's 9.9 re-measured
    # today -- every one of them a measured Critical, and every one ranked below
    # 180 rows because its `due` names a fix. That is the 10-13 fault one band
    # over: within the visible window the rows that MOVED are the ones a reader
    # has not seen, and "a fix exists" is what makes a row ordinary only when the
    # row is STATIC. A Critical published three days ago is not ordinary patching
    # just because the maintainer shipped a release. Kept deliberately narrow --
    # `_touched` AND a MEASURED CVSS >= 9.0 (tier 0 only, so an unscored or High
    # row still cannot jump) -- and it borrows band 1's front-half key rather
    # than inventing a band, because it is the same reader action: act now.
    if row.get("_touched") and sev_tier(row) == 0 and not NO_FIX_RE.search(due):
        return (1, 0, 0, 0)
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

def _selftest_touched_critical() -> str:
    """The 2026-10-17 promotion, both directions. 10 cases."""
    from datetime import date as _d
    t = _d(2026, 10, 17)
    ok = n = 0

    def chk(label, row, want_promoted):
        nonlocal ok, n
        n += 1
        promoted = rank(row, t)[:2] == (1, 0)
        if promoted == want_promoted:
            ok += 1
        else:
            print("  FAIL %s: promoted=%s want=%s key=%s" % (label, promoted, want_promoted, rank(row, t)))

    # PROMOTED: touched, measured Critical, a fix exists.
    chk("new 9.8 w/ fix", {"k": "a", "_touched": True, "due": "fixed 0.5.6",
                           "t": "CVSS 9.8 unauthenticated RCE"}, True)
    chk("new 9.5 w/ fix", {"k": "b", "_touched": True, "due": "fixed 19.3.1",
                           "t": "unauthenticated CVSS 9.5 RCE, no CVE id"}, True)
    chk("re-measured 9.9", {"k": "c", "_touched": True, "due": "patched 1.103.1",
                            "t": "CVSS 9.9 privilege escalation"}, True)
    # NOT promoted: untouched, or not Critical, or already band 0/1/4.
    chk("untouched 9.8", {"k": "d", "_touched": False, "due": "fixed 0.5.6",
                          "t": "CVSS 9.8 unauthenticated RCE"}, False)
    chk("touched 8.8 (High)", {"k": "e", "_touched": True, "due": "fixed 1.2.3",
                               "t": "CVSS 8.8 authentication bypass"}, False)
    chk("touched unscored", {"k": "f", "_touched": True, "due": "fixed 2.0",
                             "t": "silent data loss, no CVE and no score"}, False)
    chk("touched 5.3 (Medium)", {"k": "g", "_touched": True, "due": "fixed 9.9.9",
                                 "t": "CVSS 5.3 info leak"}, False)
    chk("touched 9.8 RESOLVED", {"k": "h", "_touched": True, "due": "RESOLVED 2026-10-01",
                                 "t": "CVSS 9.8 was fixed"}, False)
    # A no-fix Critical still goes through band 1 proper (same key, but via the
    # register) -- asserted so the promotion cannot be mistaken for the register.
    nf = {"k": "i", "_touched": True, "due": "no fix on 2.x", "t": "CVSS 9.9 bypass"}
    n += 1
    ok += 1 if rank(nf, t) == (1, 0, 0, 0) else 0
    # An overdue KEV row must still win band 0 outright.
    kev = {"k": "j", "_touched": True, "due": "2026-10-01 (16d PAST DUE)",
           "t": "CISA KEV, CVSS 9.8, actively exploited"}
    n += 1
    ok += 1 if rank(kev, t)[0] == 0 else 0
    return "%d/%d" % (ok, n)

def _selftest_cvss() -> str:
    """The 2026-10-17 scoring-version gap, both directions. 14 cases.

    Found by assert_must_show rejecting the build for the FIFTH time on a row
    that was right and a predicate that was wrong. The optional scoring-version
    group required a MINOR -- it matched "CVSS v3.1 8.6" and "CVSS v4.0 9.5" but
    not "CVSS v4 9.2", which is how a run naturally writes a CVSS 4.0 score. The
    consequence was silent and board-wide, not local to today: three rows scored
    0.0 and therefore sorted as UNMEASURED (tier 1) while asserting a Critical,
    among them one of today's must-show rows and a 9.5 Next.js RCE that only
    ranked at all because its `due` put it in the no-fix register. A severity
    key that reads a Critical as unscored is worse than no severity key, because
    it fails in the direction of silence.
    """
    cases = [
        ("CVSS v4 9.2 argument injection", 9.2),      # the row that caught it
        ("CVSS v4 9.5 unauthenticated RCE", 9.5),
        ("CVSS 4 9.2", 9.2),
        ("CVSS v4 10.0 in CISA KEV", 10.0),
        ("CVSS v3.1 8.6 HIGH", 8.6),                  # unchanged
        ("CVSS v4.0 9.5 / v3.1 8.9", 9.5),            # unchanged, takes the worst
        ("CVSS 9.2 Critical", 9.2),                   # unchanged
        ("CVSS 4.0 = 9.2 CRITICAL", 9.2),             # unchanged
        ("CVSS v2 7.5", 7.5),
        ("9.8 CRITICAL per NVD", 9.8),                # second alternative
        # negative controls: nothing here is a CVSS score
        ("Spring Boot 4.2 shipped today", 0.0),
        ("CVSS v4 with no score published", 0.0),
        ("fixed in 9.0.12 / 8.1.13", 0.0),
        ("Kubernetes 1.34 reaches EOL", 0.0),
    ]
    ok = 0
    for text, want in cases:
        got = max_cvss({"t": text})
        if abs(got - want) < 1e-9:
            ok += 1
        else:
            print("  FAIL %-38r got=%s want=%s" % (text, got, want))
    return "%d/%d" % (ok, len(cases))
