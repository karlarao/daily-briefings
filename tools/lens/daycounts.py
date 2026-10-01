#!/usr/bin/env python3
"""Recompute every "Nd PAST DUE" / "N days past" figure from the row's own date.

WHY THIS IS A BUILD STEP AND NOT A HAND CORRECTION
--------------------------------------------------
A past-due day count is the only field on the board that is WRONG BY DEFAULT
tomorrow: it decays one unit per day with nobody touching it. Editions 069, 077,
078 and 079 each hand-corrected some of these, and each time a different subset
was missed -- because the figure is written in TWO places per row (the `due`
field and the prose) and a correction that touches one leaves the other. The
09-28 note names that exact trap ("a row that disagreed with ITSELF"), and the
09-27 note names its parent ("corrected the prose and left the data").

Measured on the edition-078 parent at 2026-09-30: SEVEN of eight rows carrying a
day count were stale, drifts of +1 to +10 days, and the JFrog row disagreed with
itself in the same edition (prose "3d", due field "4d PAST DUE").

So: derive the number, never store it twice by hand. This rewrites both sites
from the ISO date and then ASSERTS they agree, which is the property the hand
process kept failing to hold.
"""
from __future__ import annotations
import datetime as _dt
import re

# "(33d PAST DUE)", "now 8 days past", "due 2026-09-16, 8d past due"
_FIG = re.compile(r"(?P<n>\d+)\s*(?P<unit>d|days?)\s*(?P<tail>PAST\s*DUE|past\s*due|past)", re.I)
_ISO = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _past(iso: str, today: str) -> int:
    return (_dt.date.fromisoformat(today) - _dt.date.fromisoformat(iso)).days


def anchor_date(row: dict) -> str | None:
    """The date the count is measured FROM: the KEV/patch due date.

    Taken from the `due` field's own ISO date -- not from `first_seen`/`last_seen`,
    which are when WE saw it, and not from the prose, which is what we are fixing.
    """
    m = _ISO.search(str(row.get("due") or ""))
    return m.group(1) if m else None


def refresh_row(row: dict, today: str, warn=None) -> tuple[dict, list]:
    """Rewrite every day-count figure in `due` and `t` from `anchor_date(row)`.

    Returns (row, changes). A row with no anchor date or no figure is untouched.
    """
    iso = anchor_date(row)
    if not iso:
        return row, []
    n = _past(iso, today)
    if n < 0:                      # not past due yet; leave the row alone
        return row, []
    changes = []

    def sub(field: str, text: str) -> str:
        def rep(m):
            old = int(m.group("n"))
            if old == n:
                return m.group(0)
            changes.append((field, old, n))
            # "33d" keeps the tight form; "8 days" keeps the spaced word form,
            # so the rewrite reads like the prose it replaces.
            if m.group("unit").lower() == "d":
                unit = "d"
            else:
                unit = " day" if n == 1 else " days"
            return str(n) + unit + " " + m.group("tail")
        return _FIG.sub(rep, text)

    row = dict(row)
    row["due"] = sub("due", str(row.get("due") or ""))
    row["t"] = sub("t", str(row.get("t") or ""))
    if changes and warn:
        warn("  [daycounts] %s: anchor %s -> %dd past; %s"
             % (row.get("k", "?")[:44], iso, n,
                ", ".join("%s %d->%d" % c for c in changes)))
    return row, changes


def assert_consistent(row: dict, today: str) -> None:
    """Both sites must now state the same number, and it must be the true one."""
    iso = anchor_date(row)
    if not iso:
        return
    n = _past(iso, today)
    if n < 0:
        return
    found = {int(m.group("n")) for m in _FIG.finditer(
        str(row.get("due") or "") + " " + str(row.get("t") or ""))}
    bad = found - {n}
    if bad:
        raise SystemExit(
            "daycounts: row %r still states %s days past due; anchor %s => %d"
            % (row.get("k"), sorted(bad), iso, n))


def refresh_all(rows: list, today: str, warn=print) -> tuple[list, int]:
    out, touched = [], 0
    for r in rows:
        r2, ch = refresh_row(r, today, warn=warn)
        if ch:
            touched += 1
        assert_consistent(r2, today)
        out.append(r2)
    return out, touched


if __name__ == "__main__":
    T = "2026-09-30"
    # the real stale rows measured on the 078 parent
    rows = [
        {"k": "litellm-kev", "due": "2026-09-16 (8d PAST DUE)",
         "t": "LiteLLM CVE-2026-59822 — CISA KEV, due 2026-09-16, now 8 days past"},
        {"k": "oracle-21962", "due": "2026-08-27 (33d PAST DUE)",
         "t": "CVE-2026-21962 — 33d PAST DUE, forensic triage required"},
        # the row that disagreed with ITSELF (prose 3d vs due 4d)
        {"k": "jfrog-quad", "due": "2026-09-25 (4d PAST DUE) · 4 KEV entries",
         "t": "CVE-2026-42018 chained with CVE-2026-42016 — 3d PAST DUE"},
        # not past due yet -> untouched
        {"k": "future", "due": "2026-10-14", "t": "something due 2026-10-14"},
        # no anchor -> untouched
        {"k": "nofix", "due": "no fix exists", "t": "unpatched, no fixed release"},
    ]
    out, n = refresh_all(rows, T)
    print("\ntouched %d/%d rows" % (n, len(rows)))
    assert "14d PAST DUE" in out[0]["due"] and "14 days past" in out[0]["t"]
    assert "34d PAST DUE" in out[1]["due"] and "34d PAST DUE" in out[1]["t"]
    # the self-disagreeing row must now agree in BOTH places
    assert "5d PAST DUE" in out[2]["due"] and "5d PAST DUE" in out[2]["t"], out[2]
    assert out[3]["t"] == "something due 2026-10-14"
    assert out[4]["due"] == "no fix exists"
    # and the assertion must FIRE on a row left inconsistent by hand
    try:
        assert_consistent({"k": "x", "due": "2026-08-27 (33d PAST DUE)", "t": ""}, T)
        raise AssertionError("assert_consistent failed to fire")
    except SystemExit:
        pass
    print("daycounts self-test OK — including the self-disagreeing row and the guard firing")
