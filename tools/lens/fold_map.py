#!/usr/bin/env python3
"""Hand-verified duplicate groups in the inherited events[] board (edition 059).

WHY THIS IS A MAP AND NOT A THRESHOLD. Measured on the real board, the true
duplicates score LOWER on token Jaccard than same-date pairs that must never
merge: the five JDK 27 rows score j=0.05–0.25 against each other, while
"Fabric Runtime 2.0 becomes default" vs "Fabric Runtime 1.3 end of support"
(genuinely different deadlines, same date) scores j=0.15, and two distinct
Oracle October rows score j=0.25. There is no cut that keeps the first group
and rejects the others, because each duplicate is an independent re-summary
that happens to share almost no vocabulary with its twin. So the 09-10 note's
conclusion holds in a stronger form than it was written: a post-hoc matcher is
not merely a treadmill here, it cannot be made safe. Identity has to be
asserted at authoring time — which is what ledger_surgery.reuse_key now does
for every new row, so this backlog is a one-off.

Each group below was read individually before being listed. Survivor first.
"""

# survivor_key: [keys folded into it]
EVENT_FOLDS = {
    # 2026-09-14 — one Databricks entitlement enforcement, written three ways
    "databricks-workspace-entitlement-enforcement": [
        "databricks-enforces-explicit-workspace-entitlements-on-every",
        "databricks-entitlement-enforcement",
    ],
    # 2026-09-15 — JDK 27 GA, five rows (one of which was mis-dated 09-14 and
    # one of which called a non-LTS release "LTS"); both corrected before folding
    "jdk27-ga": [
        "jdk-27-ga-g1-becomes-the-default-collector-in-every-environm",
        "jdk-27-ga-2026-09-15",
        "jdk-27-ga-compact-object-headers-default-jep-534-and-g1-the",
        "jdk-27-lts-ga",
    ],
    # 2026-09-15 — the September CSPU, twice
    "oracle-cspu-september-2026": ["oracle-cspu-sep"],
    # 2026-09-30 — the 2026_06 enablement, twice (both now superseded: the
    # bundle went Enabled-by-Default in 10.32; the survivor is retitled below)
    "snowflake-2026-06-generally-enabled-tbd": ["snowflake-2026-06-enable-slipped-tbd"],
    # 2026-09-30 — Redshift TLS + ODBC land the same day; the survivor's title
    # already names both, the loser names only ODBC
    "redshift-rejects-tls-1-0-1-1-provisioned-and-serverless-and": ["redshift-odbc-1x-eos"],
    # 2026-09-30 — Play registration / developer verification, three rows
    "google-play-every-package-must-be-registered-in-play-console": [
        "play-developer-verification",
        "android-dev-verification",
    ],
    # 2026-10-01 — Python 3.15 GA, twice
    "python-315-ga": ["python-315-ga-2026-10-01"],
    # 2026-10-02 — Copilot model deprecations, twice
    "copilot-model-deprecations-oct2": ["copilot-model-removals-2026-10-02"],
    # 2026-10-20 — the October CPU, three rows
    "oracle-cpu-oct-2026": [
        "oracle-critical-patch-update-expect-23-26-4-26ai-and-19-33-p",
        "oracle-cpu-october",
    ],
    # 2026-10-27 — Kubernetes 1.34 EOL, twice
    "k8s-134-eol": ["kubernetes-v1-34-eol-patch-releases"],
    # 2026-10-30 — BigQuery TabFM token pricing, twice
    "bq-tabfm-token-pricing-oct30": ["bigquery-tabfm-switches-to-token-based-pricing-billed-on-top"],
    # 2026-11-12 — PostgreSQL 14 EOL, four rows
    "postgres-14-eol-nov12": [
        "pg14-last-minor-nov",
        "postgres-14-eol",
        "postgresql-14-eol-2026-11-12",
    ],
}

# Corrections applied BEFORE the fold (a date-keyed fold cannot merge rows that
# disagree about the date, which is exactly why the JDK group survived 09-10).
EVENT_FIXES = {
    "jdk27-ga": {
        "date": "2026-09-15",
        "t": "JDK 27 GA (non-LTS). JEP 534 makes compact object headers the "
             "default on 64-bit (~22% less heap, ~8% less CPU on SPECjbb2015) "
             "and JEP 523 makes G1 the universal default collector, including "
             "on the small/constrained machines that previously got Serial.",
        "url": "https://openjdk.org/jeps/534",
    },
    # The 2026_06 enablement is no longer pending — it landed in 10.32 (Sep 5–9).
    # What remains dated is the toggle disappearing.
    "snowflake-2026-06-generally-enabled-tbd": {
        "t": "Snowflake bundle 2026_06 goes Generally Enabled (opt-out toggle "
             "removed) in a subsequent release — the Enabled-by-Default flip "
             "already landed in 10.32, so this is the last date to have "
             "finished regression testing.",
        "url": "https://docs.snowflake.com/en/release-notes/behavior-changes",
    },
}


def apply(events: list) -> tuple[list, int, int]:
    """Correct, then fold by the verified map. Returns (rows, fixed, folded)."""
    by_key = {e["k"]: e for e in events}
    fixed = 0
    for k, patch in EVENT_FIXES.items():
        if k in by_key:
            by_key[k].update(patch)
            fixed += 1

    drop, folded = set(), 0
    for survivor, losers in EVENT_FOLDS.items():
        s = by_key.get(survivor)
        if s is None:
            continue
        al = s.setdefault("aliases", [])
        for lk in losers:
            l = by_key.get(lk)
            if l is None:
                continue
            for a in [lk] + list(l.get("aliases") or []):
                if a not in al and a != survivor:
                    al.append(a)
            if not s.get("url") and l.get("url"):
                s["url"] = l["url"]
            drop.add(lk)
            folded += 1
    out = [e for e in events if e["k"] not in drop]
    out.sort(key=lambda r: (r.get("date") or "zzzz", r["k"]))
    return out, fixed, folded
