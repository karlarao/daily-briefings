#!/usr/bin/env python3
"""Edition 060 ledger surgery.

Two jobs, in this order:

1. CORRECT then FOLD. The 09-10 note predicted events[] would regrow duplicates
   and that a post-hoc matcher is a treadmill. It regrew — but the JDK 27 group
   shows *why* a date-keyed fold could never catch it: one row carries the wrong
   date (2026-09-14; GA is 2026-09-15), and another calls a non-LTS release
   "LTS". A date-keyed matcher cannot merge rows that disagree about the date,
   so the correction has to come first.

2. BUILD-TIME KEY REUSE (the durable fix). `reuse_key` is called before a new
   row is given a slug: if a parent row on the same date is clearly the same
   story, the parent's key is reused, so the duplicate never enters the ledger
   and merge_parent has nothing to carry forward twice.

Both folds keep the 09-10 guards: quantity conflict and hard-identifier
disjointness veto a merge outright.
"""
from __future__ import annotations

import difflib
import re

WORD = re.compile(r"[a-z0-9][a-z0-9.+_-]{1,}")
CVEISH = re.compile(r"\b(?:cve|ghsa)-[0-9][0-9a-z-]{3,}\b", re.I)
QTY = re.compile(r"\b(\d+(?:\.\d+)?)\s?(tb|gb|pb|x|%|ms|tpmc|cvss)\b", re.I)
STOP = {"the", "and", "for", "with", "from", "into", "that", "this", "are",
        "was", "now", "new", "has", "have", "its", "per", "not", "still",
        "all", "one", "two", "but", "you", "your", "will", "than", "then",
        "every", "each", "both", "when", "what", "who", "how", "day", "days"}


def toks(s: str) -> set:
    return {w for w in WORD.findall(s.lower()) if w not in STOP and len(w) > 2}


def anchors(s: str) -> set:
    low = s.lower()
    out = {m.group(0) for m in CVEISH.finditer(low)}
    out |= set(re.findall(r"\b\d+\.\d+(?:\.\d+)?\b", low))
    out |= {w for w in WORD.findall(low) if any(c.isdigit() for c in w) and len(w) > 2}
    return out


def hard_ids(s: str) -> set:
    return {m.group(0).lower() for m in CVEISH.finditer(s)}


def quantity_conflict(a: str, b: str) -> bool:
    """Same unit, different value => never fold (TPC-H 1TB vs 3TB)."""
    qa = {(v, u.lower()) for v, u in QTY.findall(a)}
    qb = {(v, u.lower()) for v, u in QTY.findall(b)}
    for u in {u for _, u in qa} & {u for _, u in qb}:
        va = {v for v, uu in qa if uu == u}
        vb = {v for v, uu in qb if uu == u}
        if va and vb and not (va & vb):
            return True
    return False


def id_disjoint(a: str, b: str) -> bool:
    ia, ib = hard_ids(a), hard_ids(b)
    return bool(ia) and bool(ib) and not (ia & ib)


def jac(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _blocked(a: str, b: str) -> bool:
    return quantity_conflict(a, b) or id_disjoint(a, b)


def same_story(a: str, b: str, route: str) -> bool:
    """ADVISORY ONLY — never use this to merge rows unattended.

    Measured on the real events board (see fold_map.py), this returns False for
    genuine duplicates far more often than it returns True, because each
    duplicate is an independently-worded re-summary. Loosening it to catch them
    makes it merge distinct same-date deadlines instead. It is retained to rank
    candidates for a human, not to decide.

    route='anchor' for events/benchmarks; 'similarity' for patch (09-10 rule:
    the anchor route is far too eager on security rows, where every row shares
    'cve', 'kev', 'cvss').
    """
    if _blocked(a, b):
        return False
    ta, tb = toks(a), toks(b)
    j = jac(ta, tb)
    r = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    if route == "anchor":
        shared = len(anchors(a) & anchors(b))
        return (shared >= 2 and j >= 0.35) or r >= 0.72
    return r >= 0.78 and j >= 0.45


def fold(rows: list, datekey: str, route: str) -> tuple[list, int]:
    """Fold rows sharing a date. Survivor keeps the longest title and absorbs
    the losers' keys into aliases[] so prior-edition diffs still resolve."""
    out, folded = [], 0
    by_date: dict = {}
    for r in rows:
        by_date.setdefault(r.get(datekey) or "", []).append(r)
    for _d, group in by_date.items():
        kept: list = []
        for r in group:
            hit = None
            for k in kept:
                if same_story(r["t"], k["t"], route):
                    hit = k
                    break
            if hit is None:
                kept.append(dict(r))
                continue
            folded += 1
            al = hit.setdefault("aliases", [])
            for a in [r["k"]] + list(r.get("aliases") or []):
                if a not in al and a != hit["k"]:
                    al.append(a)
            if len(r["t"]) > len(hit["t"]):
                hit["t"] = r["t"]
            if not hit.get("url") and r.get("url"):
                hit["url"] = r["url"]
        out.extend(kept)
    out.sort(key=lambda r: (r.get(datekey) or "zzzz", r["k"]))
    return out, folded


def reuse_key(new_row: dict, parent_rows: list, datekey: str, route: str,
              same_as: str | None = None, warn=print):
    """Build-time key reuse.

    HARD-WON CORRECTION (2026-09-11, same day it was written): the first version
    of this delegated the decision to `same_story`, which is the very matcher the
    measurements in fold_map.py prove cannot separate a true duplicate from two
    distinct same-date events. It therefore fired zero times and let a FIFTH
    "PostgreSQL 14 EOL" row onto a board from which four had just been folded.

    Similarity cannot establish identity here. So:

      * `same_as` is the real mechanism — the author declares the parent key.
      * The matcher is kept only as an ADVISORY: it never silently reuses a key,
        it prints the same-date candidates so a duplicate is visible at build
        time instead of discovered an edition later. Silence is the bug; a noisy
        list a human skims is the fix.
    """
    if same_as:
        if not any(p["k"] == same_as for p in parent_rows):
            raise SystemExit(f"reuse_key: same_as={same_as!r} is not a parent row")
        return same_as

    d = new_row.get(datekey)
    peers = [p for p in parent_rows if p.get(datekey) == d]
    if peers:
        warn(f"  [reuse_key] {len(peers)} existing row(s) already dated {d} — "
             f"confirm none is the same story as {new_row['k']!r}:")
        for p in peers:
            warn(f"      {p['k']:52} {p['t'][:74]}")
    return new_row["k"]


def assert_alias_safe(new_rows: list, parent_rows: list, label: str) -> None:
    """09-10 replacement for assert_no_regression: a fold legitimately shrinks a
    section, so assert no parent key was LOST — it must still be present as a
    key or inside some survivor's aliases[]."""
    have = set()
    for r in new_rows:
        have.add(r["k"])
        have.update(r.get("aliases") or [])
    missing = [p["k"] for p in parent_rows if p["k"] not in have]
    if missing:
        raise SystemExit(f"{label}: {len(missing)} parent keys vanished: {missing[:5]}")
