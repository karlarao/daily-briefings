#!/usr/bin/env python3
"""Refresh "N days" countdowns that sit next to a row's OWN date.

Why this exists
---------------
`lens_extra.daycounts_rows` finds rows whose stated day count disagrees with
|today - row date|. It is a detector, and three runs in a row have shown that
acting on its output needs more care than a blanket substitution:

  2026-10-08  "drive the fix from the tool's output and recompute from the
              date -- do not retype."
  2026-10-09  "most of the 42 patch hits are FALSE POSITIVES -- historical
              prose ('fixed 8 days after disclosure', '47 days behind
              community'), not countdowns. Read them, never count them."
  2026-10-11  a blanket rewrite would have corrupted a row: the regex matched
              `cve-2026-21962`'s prose "12 days out", which refers to the
              20 October CPU and NOT to that row's own 2026-08-27 due date.
              The 10-11 run therefore restricted the mechanical pass to the
              `due` parenthetical and hand-reviewed the prose -- leaving the
              Event Horizon's prose countdowns to drift up to 13 days stale.

So the detector is right and the blanket fix is wrong. What makes a count safely
rewritable is not the count, it is the ADJACENCY: a count is a countdown to this
row's own date only when that exact date string appears immediately before it,
inside one clause. "on 2026-10-19 -- 13 days" is rewritable; "12 days out" with
no date beside it is not, and neither is "47 days behind community", because no
date precedes them. Adjacency is what distinguishes them, and it is mechanical.

This module therefore rewrites ONLY counts whose own ISO date is within
`window` characters to their left, with no other ISO date in between, and
returns a report of every rewrite and every count it declined to touch -- so a
build prints what it changed and what a human still has to read.

Past intervals are never touched: a date in the past is reported as "N days
past due"/"N days past"/"N days ago" and a date in the future as "N days"/
"N days out"/"in N days", and both are rewritten only in that correct sense.
"""
from __future__ import annotations
import re
from datetime import date

ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

# "-- 13 days", "(2 days out)", "now 19 days past due", "in 4 days".
# Group 1 is the number; everything else is preserved verbatim.
COUNT = re.compile(
    r"(?:\bin\s+)?(\d{1,4})\s*(?:&nbsp;|\s)*"
    r"(day|days)\b(\s*(?:out|past\s+due|past|ago|left|away))?",
    re.I)

# The compact form the ledger's own `due` field uses: "2026-09-16 (25d PAST DUE)",
# "(4d out)". Found on 2026-10-12: the verbose COUNT pattern above left every one
# of these stale because "25d" carries no "day" word, so ten `due` parentheticals
# the 10-11 run had hand-fixed were silently drifting again a day later. A BARE
# "25d" is deliberately NOT matched -- it could be anything -- so the trailing
# direction marker is required, which is also what makes the sense check below
# meaningful.
COMPACT = re.compile(r"(\d{1,4})\s*d\b(\s*(?:out|past\s+due|past|ago|left|away))",
                     re.I)


def _d(m) -> date:
    return date(*map(int, m.groups()))


def _plain(s: str) -> str:
    """Tag/entity-blind view, same length as the input.

    Patch against the RAW source (the 2026-10-11 rule: three `amend()` misses
    came from reading a tag-stripped view), but *decide* on a view where
    `<b>2026-10-13</b> &mdash; 4 days` reads as one clause. Replacing markup
    with spaces of equal length keeps every offset valid in the raw string.
    """
    out = re.sub(r"<[^>]*>", lambda m: " " * len(m.group(0)), s)
    return re.sub(r"&[a-zA-Z]{2,9};|&#\d{2,5};",
                  lambda m: " " * len(m.group(0)), out)


def refresh(text: str, own: str, today: str, *, window: int = 60):
    """Rewrite countdowns to `own` inside `text`. Returns (text, fixed, left).

    `fixed` and `left` are lists of (stated, actual, snippet) / (stated,
    snippet) so a caller can print both halves.
    """
    m_own = ISO.search(own or "")
    if not m_own:
        return text, [], []
    target, now = _d(m_own), date(*map(int, ISO.match(today).groups()))
    delta = (target - now).days
    iso = m_own.group(0)
    view = _plain(text)
    fixed: list = []
    left: list = []
    edits: list = []

    spans = sorted(list(COUNT.finditer(view)) + list(COMPACT.finditer(view)),
                   key=lambda m: m.start())
    for c in spans:
        lo = max(0, c.start() - window)
        before = view[lo:c.start()]
        at = before.rfind(iso)
        adjacent = at >= 0 and not ISO.search(before[at + len(iso):])
        stated = int(c.group(1))
        snip = re.sub(r"\s+", " ", view[lo:c.end() + 24]).strip()
        if not adjacent:
            if stated != abs(delta):
                left.append((stated, snip))
            continue
        ng = len(c.groups())
        tail = (c.group(3) if ng >= 3 else c.group(2)) or ""
        past = bool(re.search(r"past|ago", tail, re.I))
        # A count written in the past sense belongs to a past date and vice
        # versa; a mismatch means the clause is not this row's countdown.
        if past != (delta < 0):
            left.append((stated, snip))
            continue
        actual = abs(delta)
        if stated == actual:
            continue
        edits.append((c.start(1), c.end(1), str(actual)))
        fixed.append((stated, actual, snip))

    for a, b, rep in reversed(edits):          # right-to-left keeps offsets
        text = text[:a] + rep + text[b:]
    return text, fixed, left


def refresh_rows(rows: list, today: str, *, datefield: str = "date",
                 fields=("t", "due"), window: int = 60):
    """Apply `refresh` across a ledger section. Returns a printable report."""
    report = []
    for r in rows:
        for f in fields:
            if not r.get(f):
                continue
            new, fixed, left = refresh(r[f], r.get(datefield) or "", today,
                                       window=window)
            if fixed:
                r[f] = new
            if fixed or left:
                report.append({"k": r.get("k"), "field": f,
                               "fixed": fixed, "left": left})
    return report
