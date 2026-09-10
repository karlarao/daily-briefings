#!/usr/bin/env python3
"""Fold duplicate ledger rows that describe the same dated item.

Why this exists (again): the 2026-09-06 build deduped events[] 162 -> 86, but
nothing in the build *prevents* the next edition inventing a fresh slug for a
story already on the board, and merge_parent faithfully carries every slug
forward. Four editions later events[] was back to 109 with five separate keys
for "JDK 27 GA" on 2026-09-15 and five for the Databricks entitlement
enforcement on 2026-09-14. benchmarks[] has the same disease: five keys for one
Alibaba TPC-DS submission.

Fold rule (deliberately conservative, same shape as the 09-06 pass):
  - rows must share the SAME date field value (events: date, benchmarks: date,
    patch: due) -- a fold can never merge two different deadlines;
  - AND title similarity >= SIM;
  - AND >= 2 shared ANCHOR tokens (version numbers, CVE ids, bundle ids,
    product nouns) so generic wording alone can never merge two rows.
The survivor is the row with the richest payload (longest title, prefers one
carrying a url); losing keys are preserved in the survivor's aliases[] so
prior-edition diffs still resolve. No dated item is ever dropped.
"""
import re
from difflib import SequenceMatcher

SIM = 0.62
MIN_ANCHORS = 2

STOP = set("""the a an and or of for to in on at by with from as is are was were be
this that these those it its new now not no than then there their they you your our we
also very about into over under after before more most less least such same own just
per via vs versus if when while which who whom will would can could should may might
must has have had does do did but so up out off down all any each other another""".split())

# a "strong anchor" is a hard identifier, not merely a long word
_ANCHOR_PATS = [
    re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I),
    re.compile(r"\bGHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}\b", re.I),
    re.compile(r"\b\d{4}_\d{2}\b"),                 # behavior-change bundle ids
    re.compile(r"\b\d+\.\d+(?:\.\d+)*\b"),          # dotted versions
    re.compile(r"\b[a-z]+\d+[a-z]*\b", re.I),       # rg.large, v1.37, p204, 19c...
]


def anchors(text):
    out = set()
    for p in _ANCHOR_PATS:
        out |= {m.group(0).lower() for m in p.finditer(text)}
    # product nouns: capitalised words that are not sentence-initial noise
    for w in re.findall(r"\b[A-Z][A-Za-z0-9]{2,}\b", text):
        lw = w.lower()
        if lw not in STOP:
            out.add(lw)
    return out


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in STOP and len(w) > 2]


_QTY_RE = re.compile(r"\b(\d+(?:\.\d+)*)\s?([a-z]{1,4})\b", re.I)


def quantities(text):
    """{unit: {values}} for tokens like 100TB, 3TB, 19c, v3, 8.3 -- the tokens that
    distinguish two otherwise identically-worded rows (TPC-H 1TB vs 3TB)."""
    out = {}
    for val, unit in _QTY_RE.findall(text):
        out.setdefault(unit.lower(), set()).add(val)
    return out


def conflicting(a, b):
    """True when a and b carry the same measurement unit with different values.

    This is the guard that stopped the first dry run merging the Dell TPC-H 1TB
    and 3TB submissions into one row: same vendor, same month, near-identical
    wording, genuinely different results.
    """
    # Hard identifiers first. Two rows that each name a vulnerability, and name
    # *different* ones, are never the same row -- the first run of this pass
    # folded a JFrog Artifactory KEV entry into a Kestra one because both said
    # "CVE" and "KEV" on the same due date.
    for pat in (_ANCHOR_PATS[0], _ANCHOR_PATS[1], _ANCHOR_PATS[2]):
        ia = {m.group(0).lower() for m in pat.finditer(a)}
        ib = {m.group(0).lower() for m in pat.finditer(b)}
        if ia and ib and not (ia & ib):
            return True
    qa, qb = quantities(a), quantities(b)
    for unit in set(qa) & set(qb):
        if not (qa[unit] & qb[unit]):
            return True
    return False


def _score(a, b):
    ra = SequenceMatcher(None, a, b).ratio()
    # partial ratio: best window of the longer string against the shorter
    s, l = (a, b) if len(a) <= len(b) else (b, a)
    best = ra
    if s and len(l) > len(s):
        step = max(1, len(s) // 4)
        for i in range(0, len(l) - len(s) + 1, step):
            best = max(best, SequenceMatcher(None, s, l[i:i + len(s)]).ratio())
    return max(ra, best)


def dedupe(rows, datefield, max_passes=4):
    """Fold to a fixed point: chained duplicates (A~B, B~C, A!~C) need >1 pass."""
    all_folds = []
    for _ in range(max_passes):
        rows, folds = _dedupe_once(rows, datefield)
        all_folds.extend(folds)
        if not folds:
            break
    return rows, all_folds


def _dedupe_once(rows, datefield):
    """Return (kept_rows, folds) where folds is [(survivor_k, absorbed_k)]."""
    buckets = {}
    for r in rows:
        buckets.setdefault(r.get(datefield) or "", []).append(r)

    kept, folds = [], []
    for _, group in buckets.items():
        if len(group) == 1:
            kept.extend(group)
            continue
        # richest first so the survivor keeps the best payload
        group = sorted(group, key=lambda r: (bool(r.get("url")), len(r.get("t", ""))),
                       reverse=True)
        survivors = []
        for r in group:
            rt, ra = r.get("t", ""), anchors(r.get("t", "") + " " + r.get("k", ""))
            hit = None
            for s in survivors:
                st, sa = s.get("t", ""), anchors(s.get("t", "") + " " + s.get("k", ""))
                if len(ra & sa) < MIN_ANCHORS:
                    continue
                if conflicting(rt + " " + r.get("k", ""), st + " " + s.get("k", "")):
                    continue
                jac = len(ra & sa) / max(1, len(ra | sa))
                # Two independent routes to a fold. The similarity route catches
                # rewordings of a thinly-anchored row; the anchor route catches
                # rows written from completely different angles that nonetheless
                # name the same product, version and mechanism. Requiring the
                # anchor route to clear a Jaccard bar is what keeps a row that
                # merely *mentions* Google out of the Play-registration row.
                if (_score(rt.lower(), st.lower()) >= SIM
                        or (len(ra & sa) >= 3 and jac >= 0.35)):
                    hit = s
                    break
            if hit is None:
                survivors.append(r)
            else:
                al = hit.setdefault("aliases", [])
                for k in [r["k"]] + list(r.get("aliases") or []):
                    if k not in al and k != hit["k"]:
                        al.append(k)
                # never lose a url we had
                if not hit.get("url") and r.get("url"):
                    hit["url"] = r["url"]
                folds.append((hit["k"], r["k"]))
        kept.extend(survivors)
    return kept, folds


if __name__ == "__main__":
    import json, sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lens_guard as G
    src = open(sys.argv[1], encoding="utf-8").read()
    led = G.load_ledger(src)
    for sec, df in (("events", "date"), ("benchmarks", "date"), ("patch", "due")):
        before = len(led.get(sec, []))
        kept, folds = dedupe(led.get(sec, []), df)
        led[sec] = kept
        print("%-11s %3d -> %3d  (%d folded)" % (sec, before, len(kept), len(folds)))
        for s, a in folds[:8]:
            print("      %s  <-  %s" % (s[:52], a[:52]))
    if len(sys.argv) > 2:
        json.dump(led, open(sys.argv[2], "w"), ensure_ascii=False)
