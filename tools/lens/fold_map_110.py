#!/usr/bin/env python3
"""Edition 110 hand-verified fold map.

METHOD NOTE (this is the finding, not just the fix). Three fold criteria were
measured against the edition-109 board before choosing one:

  1. SAME DUE DATE  -- 6 clusters of >=3 rows in patch[]. Every one inspected was
     genuinely DIFFERENT CVEs sharing a publication date (2026-08-20 held a
     BigQuery JDBC RCE, a pgjdbc SCRAM downgrade, a Chainlit MCP RCE, a crates.io
     maintainer compromise and the Spring 91-CVE drop). Date-keyed folding of
     patch[] would destroy distinct stories. Confirms the 2026-09-10 note.

  2. SHARED HARD IDENTIFIER (same CVE id on two rows) -- 32 ids appear on >1 row,
     five on four rows. This looked like the clean signal and is NOT: the rows
     CROSS-REFERENCE each other's CVE ids in analytical prose. The four rows
     carrying CVE-2026-114820 are a CA-distrust row, an Oracle out-of-band-alert
     row, a "patched for paying customers only" JDK row and a "near-twin respin"
     row -- four distinct stories that each cite the same id. Folding on shared
     id would have destroyed all four. This EXTENDS the 2026-09-11 conclusion:
     once ledger prose becomes cross-referential, even hard identifiers stop
     being identity evidence.

  3. NEAR-IDENTICAL PROSE (SequenceMatcher on the de-tagged `t` field, >=0.80,
     length-ratio gated) -- across all 564 rows of patch/claims/ownclaims/
     events/promises this found exactly ONE pair, at ratio 1.000. That is the
     criterion that works, because it tests what a duplicate actually is: the
     same row written twice.

The headline result is therefore that the duplication backlog the 09-10 .. 09-21
notes kept deferring is PAID DOWN AND NOT REGROWING. patch[] growing 160 -> 227
since late September is real new content. Build-time identity assertion
(ledger_surgery.reuse_key's advisory + drafting discipline) is what did it.
"""

# Verified by eye: identical de-tagged prose, identical `due` field, same story
# (Percona PSMDB shipping the CVE-2026-82067 fix on 2026-09-22/23). The
# mongodb-* key is the survivor because it is the older, broader key that also
# carries the September batch context; the percona-* key becomes an alias.
FOLD_PATCH = [
    ("mongodb-sep8-batch-percona-unpatched", ["percona-psmdb-unpatched-auth-off"]),
]

FOLD_CLAIMS = []      # measured: zero near-identical pairs
FOLD_OWNCLAIMS = []   # measured: zero
FOLD_EVENTS = []      # measured: zero
FOLD_PROMISES = []    # measured: zero


def apply_fold(rows, fold):
    """Fold losers into survivors, preserving every loser key in aliases[].

    Carries first_seen back to the oldest and days forward to the largest, so a
    fold never resets a day count. Returns (rows, n_folded).
    """
    by = {r["k"]: r for r in rows}
    dropped = set()
    n = 0
    for keep, losers in fold:
        if keep not in by:
            raise SystemExit("fold survivor missing: %s" % keep)
        s = by[keep]
        al = list(s.get("aliases") or [])
        for lk in losers:
            if lk not in by:
                raise SystemExit("fold loser missing: %s" % lk)
            l = by[lk]
            al += [lk] + list(l.get("aliases") or [])
            fs = [d for d in (s.get("first_seen"), l.get("first_seen")) if d]
            if fs:
                s["first_seen"] = min(fs)
            ds = [d for d in (s.get("days"), l.get("days")) if isinstance(d, int)]
            if ds:
                s["days"] = max(ds)
            dropped.add(lk)
            n += 1
        s["aliases"] = sorted(set(al))
    return [r for r in rows if r["k"] not in dropped], n
