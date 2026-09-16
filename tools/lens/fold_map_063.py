#!/usr/bin/env python3
"""Edition 063 hand-verified fold map for claims[], ownclaims[] and patch[].

Why a hand map and not a matcher: measured on this board 2026-09-11, true
duplicates score LOWER on token Jaccard than same-date pairs that must never
merge. There is no safe threshold. Identity is asserted by a human reading the
rows. Same reasoning as lens/fold_map.py (events, edition 060).

Each entry is {survivor_key: [keys folded into it]}. The survivor keeps its own
prose; every folded key is appended to the survivor's aliases[] so prior-edition
diffs still resolve and no row leaves by omission (guard 2, alias-aware form).

Verified by reading all 8 MI455X rows, all 3 CBTREE rows and all 11 CSPU rows
in full on 2026-09-14. Cluster notes are in the comments so the next editor can
check the reasoning rather than trust it.
"""

# ---- claims[] -------------------------------------------------------------
# The 8 MI455X rows are NOT 8 claims. They are 3 distinct competitive claims
# plus 5 restatements of the same two spec sheets:
#   * the PART   (432 GB HBM4, 23.3 TB/s, ~40 PFLOPS MXFP4)
#   * the RACK   (Helios: 72 GPUs, 31 TB HBM4, 1.7 PB/s, vs Rubin NVL72)
# and three claims that each say something the others do not:
#   * measured 20 TB/s MLA decode in FP8 (a MEASURED number, not a peak - the
#     honest form, and the one worth citing back at them)
#   * Helios at 4x efficiency
#   * Helios at +30% tokens/dollar vs Rubin NVL72
CLAIMS_FOLD = {
    "amd-mi455x-432gb-memory-lead": [
        "amd-mi455x-432gb-hbm4",            # same spec sheet, adds "2.9x MI355X"
        "amd-mi455x-bandwidth-per-flop-up",  # same spec sheet, adds 12x36GB + 245kW
    ],
    "amd-mi455x-bandwidth-contradiction": [
        "amd-helios-31tb-hbm4-rack",         # same rack figures, adds UALoE detail
    ],
    # kept distinct, do NOT fold: amd-mi455x-measured-decode,
    # amd-helios-4x-efficiency, amd-helios-30pct-tokens-dollar
}

# ---- ownclaims[] ----------------------------------------------------------
# Two rows describe the identical published result (4.5s -> 0.7s on 35M rows of
# Citibike data via a spatiotemporal CBTREE composite index). The third row that
# mentions CBO is a different claim about blog cadence and stays.
OWNCLAIMS_FOLD = {
    "oracle-cbtree-spatiotemporal-6-4x": [
        "cbtree-spatiotemporal-4-10x",
    ],
}

# ---- patch[] --------------------------------------------------------------
# September CSPU: three rows on 2026-09-15 for one event. One is accurate
# (714 patches / 11 Database Server, confirmed against the pre-release advisory
# again today); one is WRONG - it is dated 2026-09-15 but its prose describes
# the AUGUST CSPU (943 patches); one is a bare stub.
# August CSPU: five rows on 2026-08-18 for one advisory, of which exactly two
# carry distinct facts - the volume, and the Clusterware 9.6 pair.
PATCH_FOLD = {
    "oracle-cspu-sep-15-next": [
        "oracle-cspu-sep15",                 # prose describes AUGUST, misdated
        "oracle-monthly-cspu-third-tuesday",  # bare stub, no content
    ],
    "oracle-cspu-aug-2026-clusterware": [
        "oracle-cspu-aug-supersedes-1932",
        "oracle-monthly-cspu-aug",
        "august-2026-cspu-volume-943-patches-925-cves-across-23-produ",
    ],
    # kept distinct: cspu-aug-2026-clusterware-96 carries the two CVSS 9.6
    # Clusterware CVEs and is the row the 2026-09-04 rename correction updates.
}

# Rows whose `due` field is not a date and breaks every date-keyed check.
# "standing" is legitimate and documented (the plan-regression chatter row);
# "shipped 18 Aug" is a malformed date that should have been 2026-08-18 and is
# folded away above anyway.
DUE_FIXES = {
    "august-2026-cspu-volume-943-patches-925-cves-across-23-produ": "2026-08-18",
}
