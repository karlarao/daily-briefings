#!/usr/bin/env python3
"""Field-aware ledger row patcher with an exactly-once anchor assertion.

WHY (2026-11-21, carried into 11-22 and 11-23): corrections are applied to the
LEDGER before any section is generated (the 09-14 build-order rule), and the
11-22 run proved the other half of it -- patching a section's rendered OUTPUT
after the ledger changed leaves the guard failing on a string you just fixed.
So: edit rows here, then re-run every generator.

Every patch names the row key, the field, and an anchor substring that must occur
EXACTLY ONCE in that field. A miss or a double match raises. That is what makes a
silent no-op impossible -- the same discipline rewrite_identity applies to
identity sites.
"""
import json
import re
import sys

SECTIONS = ("events", "patch", "claims", "ownclaims", "promises",
            "benchmarks", "gaps", "buildbets", "skills", "retired_events")


def find(led, key):
    """Return (section, row) for `key`, raising if absent or ambiguous."""
    hits = [(s, r) for s in SECTIONS for r in led.get(s, [])
            if isinstance(r, dict) and r.get("k") == key]
    if not hits:
        raise SystemExit("patch_rows: no row with key %r" % key)
    if len(hits) > 1:
        raise SystemExit("patch_rows: key %r appears in %d rows (%s)"
                         % (key, len(hits), [s for s, _ in hits]))
    return hits[0]


def patch(led, key, field, old, new, *, allow_new_field=False):
    """Replace `old` with `new` inside led[...][key][field]. Anchor must be unique."""
    sec, row = find(led, key)
    if field not in row:
        if not allow_new_field:
            raise SystemExit("patch_rows: %s has no field %r (pass allow_new_field)"
                             % (key, field))
        row[field] = ""
    cur = str(row[field] or "")
    n = cur.count(old)
    if n != 1:
        raise SystemExit("patch_rows: anchor %r matched %d times in %s.%s (need 1)\n"
                         "  field now: %s" % (old[:80], n, key, field, cur[:300]))
    row[field] = cur.replace(old, new)
    return sec, row


def setfield(led, key, field, value):
    """Set a field outright (for dates, due, status). Prints the old value."""
    sec, row = find(led, key)
    before = row.get(field, "<absent>")
    row[field] = value
    print("  [%s] %s.%s: %r -> %r" % (sec, key, field, before, value))
    return sec, row


def append(led, key, field, text):
    """Append to a prose field, asserting the text is not already present."""
    sec, row = find(led, key)
    cur = str(row.get(field) or "")
    if text.strip() and text.strip() in cur:
        raise SystemExit("patch_rows: %s.%s already contains that text" % (key, field))
    row[field] = cur + text
    return sec, row


def _selftest():
    led = {"events": [{"k": "a", "date": "2026-01-01", "t": "one TWO three"},
                      {"k": "b", "date": None, "t": "dup dup"}]}
    ok = 0
    patch(led, "a", "t", "TWO", "2"); assert led["events"][0]["t"] == "one 2 three"; ok += 1
    try:
        patch(led, "b", "t", "dup", "x"); raise AssertionError("double match passed")
    except SystemExit: ok += 1
    try:
        patch(led, "a", "t", "nope", "x"); raise AssertionError("zero match passed")
    except SystemExit: ok += 1
    try:
        find(led, "zzz"); raise AssertionError("missing key passed")
    except SystemExit: ok += 1
    setfield(led, "b", "date", "2026-11-23"); assert led["events"][1]["date"] == "2026-11-23"; ok += 1
    try:
        patch(led, "a", "nofield", "x", "y"); raise AssertionError("missing field passed")
    except SystemExit: ok += 1
    append(led, "a", "t", " more")
    try:
        append(led, "a", "t", "more"); raise AssertionError("duplicate append passed")
    except SystemExit: ok += 1
    return "%d/7" % ok


if __name__ == "__main__":
    print("patch_rows selftest:", _selftest())
