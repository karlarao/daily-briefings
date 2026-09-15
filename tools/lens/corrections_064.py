#!/usr/bin/env python3
"""Edition 064 ledger pass: corrections FIRST, then folds, then retirements.

Order matters (2026-09-14 rule): corrections are applied to the LEDGER before
any section is generated, never to the assembled HTML afterwards -- otherwise
the rendered tables are built from the pre-fix ledger and silently disagree.
"""
import sys, json, copy
sys.path.insert(0, "tools/lens")
import lens_guard as G

TODAY = "2026-09-15"
html = open("lens/parent_stripped.html", encoding="utf-8").read()
parent = G.load_ledger(html)
led = copy.deepcopy(parent)
led["date"], led["edition"] = TODAY, 64

report = []


def find(lst, key):
    for r in lst:
        if r["k"] == key:
            return r
    raise KeyError(key)


# ---------------------------------------------------------------- corrections
# 1. FIPS: 2026-09-21 is a NIST calendar event, NOT an Oracle deadline. Oracle's
#    26ai security guide desupports FIPS_140_2 "sometime after" with no date.
#    The real trap is the silent behaviour flip on FIPS_140=TRUE.
r = find(led["events"], "nist-moves-fips-140-2-to-the-historical-list-oracle-desuppor")
r["t"] = ("NIST moves FIPS 140-2 to the historical list. <b>CORRECTION (ed. 064): this is a NIST "
          "calendar event, not an Oracle deadline</b> — edition 063 carried it as though Oracle "
          "desupported on this date. Oracle's 26ai security guide says only that FIPS_140_2 is "
          "desupported \"sometime after\" FIPS 140-2 moves to the historical list; <b>no Oracle date "
          "is published</b>. The real trap is a silent behaviour flip: FIPS_140=TRUE resolves to "
          "FIPS_140_2 today and will resolve to FIPS_140_3 once FIPS_140_2 goes, same value, "
          "different cipher policy, no error.")
r["act"] = "Set FIPS_140 explicitly to FIPS_140_2 or FIPS_140_3 rather than inheriting TRUE."
r["url"] = ("https://docs.oracle.com/en/database/oracle/oracle-database/26/dbseg/"
            "oracle-database-fips-140-settings.html")
r["corrected"] = "ed064"
report.append("CORRECTED fips: 09-21 is NIST-only; Oracle desupport undated; FIPS_140=TRUE flip noted")

# 2. Play Contacts Permissions: 063 carried 2026-10-28 with a recorded conflict.
#    Today both Google surfaces agree on 2027-01-27; the conflict is resolved.
r = find(led["events"], "play-permission-clampdown-2027")
r["date"] = "2027-01-27"
r["t"] = ("Google Play Contacts Permissions policy binds apps targeting API 37+: broad READ_CONTACTS "
          "needs a declared core-functionality justification or the Contact Picker. <b>CORRECTION "
          "(ed. 064): the date conflict is resolved to 2027-01-27.</b> Editions 062–063 carried "
          "2026-10-28 because Google's Policy Deadlines table and its policy pages disagreed; both "
          "now read 2027-01-27, and the policy preview page states the effective date in prose. "
          "Location, SMS/Call Log and Foreground Services (geofencing) share the date. The earlier "
          "2026-10-28 now survives only in third-party trackers.")
r.pop("conflict", None)
r["corrected"] = "ed064"
r["url"] = "https://support.google.com/googleplay/android-developer/answer/16909972"
report.append("CORRECTED play-contacts: 2026-10-28 -> 2027-01-27, conflict resolved")

# 3. Fabric Runtime 1.3: 062 invented 2026-09-30 as a cliff; 063 said the page
#    carried no retirement sentence at all. Both were wrong -- the lifecycle page
#    dates it 2026-09-30 as a GA->LTS transition with support through March 2027.
r = find(led["events"], "microsoft-fabric-runtime-1-3-spark-3-5-end-of-support-soften")
r["date"] = "2026-09-30"
r["t"] = ("Microsoft Fabric Runtime 1.3 (Spark 3.5) reaches its listed End of Support date — but "
          "<b>enters six-month Long Term Support on 2026-10-01, extending support through March "
          "2027</b>. <b>CORRECTION (ed. 064): this settles two earlier errors.</b> Edition 062 called "
          "2026-09-30 \"a real, day-precise deadline\" (overstated — it is not a cliff); edition 063 "
          "said learn.microsoft.com carried no retirement sentence at all (wrong — the "
          "data-engineering/lifecycle page, updated 2026-08-18, carries the date and the LTS "
          "footnote). The genuine removal risk is March 2027.")
r["act"] = "Plan the Runtime 2.0 move against March 2027, not September."
r["url"] = "https://learn.microsoft.com/en-us/fabric/data-engineering/lifecycle"
r["corrected"] = "ed064"
report.append("CORRECTED fabric-runtime-1.3: undated -> 2026-09-30 GA->LTS, real risk March 2027")

# 4. Snowflake 2026_07: the bundle page says only "a subsequent October release";
#    BCR-2378's rollout timeline names 2026-10-13. Record both rather than
#    silently promoting the day-precise one.
r = find(led["events"], "snowflake-2026-07-enable-oct")
r["date"] = "2026-10-13"
r["t"] = ("Snowflake bundle 2026_07 flips to Enabled-by-default. <b>Two Snowflake pages disagree on "
          "precision:</b> the bundle status page says only \"a subsequent October 2026 release\" "
          "(month, no day) while BCR-2378's rollout timeline names <b>2026-10-13</b>. Carrying the "
          "day-precise one with the disagreement recorded. 23 changes, including three that change "
          "results rather than metadata: BOOLEAN→NUMBER casts now honour the target type (and "
          "overflow where they used to silently downgrade), ARRAY→VECTOR overflow is an error "
          "instead of ±Inf, and semantic views reject FACTS+DIMENSIONS together because the old "
          "behaviour returned arbitrary facts per dimension group.")
r["act"] = "Run the break-test suite as a non-ACCOUNTADMIN role before October."
r["url"] = "https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_07_bundle"
r["corrected"] = "ed064"
report.append("CORRECTED snowflake-2026_07: 2026-10-15 TBD -> 2026-10-13, page disagreement recorded")

# ----------------------------------------------------------- hand-verified fold
# Six patch rows, one story: the parquet-java 1.18.0 silent corruption. They
# accumulated because each edition re-summarised it under a fresh slug. Today
# they are all superseded by one fact (1.18.1 GA'd 2026-09-04 and fixes it), so
# this is the moment to fold. Hand-read, not threshold-matched -- the 09-10/09-11
# measurements show no similarity threshold can separate these safely.
PARQUET_FOLD = [
    "parquet-java-1180-corruption-unfixed",
    "parquet-java-1180-silent-corruption",
    "parquet-java-1181-rc1-voted",
    "parquet-java-1180-corruption",
    "parquet-java-1180-binary-corruption",
    "parquet-java-1181-rc-only",
]
survivor_key = "parquet-java-1180-corruption"
survivor = find(led["patch"], survivor_key)
losers = [k for k in PARQUET_FOLD if k != survivor_key]
aliases = set(survivor.get("aliases", []))
for k in losers:
    row = find(led["patch"], k)
    aliases.add(k)
    aliases.update(row.get("aliases", []))
led["patch"] = [r for r in led["patch"] if r["k"] not in set(losers)]
survivor["aliases"] = sorted(aliases)
survivor["due"] = "2026-09-04"
survivor["t"] = ("<b>RESOLVED — parquet-java 1.18.1 GA'd 2026-09-04 and fixes both corruption paths.</b> "
                 "1.18.0 (2026-08-11) shipped two silent data-corruption regressions, both traceable to "
                 "one broad performance PR that turned defensive copies into shared references: "
                 "<code>ByteBufferBackedBinary.getBytes()</code> clobbering shared page-wide buffers on "
                 "repeated/array columns, and <code>BytesInput.copy()</code> returning a reference "
                 "instead of a copy so a dictionary page could alias its source. <b>Upgrade to 1.18.1 or "
                 "stay on 1.17.1 — 1.18.0 is a corrupting build</b>, and it is the version people moved "
                 "to in order to clear Jackson CVEs. <i>Six ledger rows for this one story folded here "
                 "in edition 064; every losing slug is preserved in aliases[].</i>")
survivor["url"] = "https://github.com/apache/parquet-java/issues/3716"
report.append("FOLDED patch: 6 parquet-java corruption rows -> 1 (%d aliases), marked RESOLVED by 1.18.1"
              % len(survivor["aliases"]))

# ------------------------------------------------------------------ new rows
NEW_PATCH = [
    dict(k="parquet-cve-2026-73334-no-fix", due="2026-09-09",
         t="<b>Apache Parquet CVE-2026-73334 (CVSS 8.1) — NO FIXED VERSION EXISTS.</b> In the Hadoop "
           "<code>crypto.keytools</code> envelope-encryption path the KMS URL can be taken from the "
           "<i>file</i>; a pluggable KmsClient that does not validate the host will send your KMS token "
           "to an attacker's endpoint. Affects 1.12 through <b>1.18.1 inclusive</b> — i.e. including the "
           "release that shipped five days earlier to fix the corruption bugs above. The ASF says the "
           "fix is \"presumably 1.19\", which will turn file-controlled KMS URLs off by default.",
         act="Config-only until 1.19: force application control of the KMS URL in readers. Narrow "
             "population (Parquet modular encryption only), but nothing to patch to.",
         url="https://nvd.nist.gov/vuln/detail/CVE-2026-73334"),
    dict(k="iceberg-18004-cow-update-row-duplication", due="2026-09-07",
         t="<b>Iceberg #18004 — copy-on-write <code>UPDATE … WHERE &lt;subquery&gt;</code> silently "
           "duplicates every row, and there is no newer Iceberg to upgrade to.</b> "
           "<code>SparkCopyOnWriteScan.filter()</code> is not thread-safe; under Spark 4.x AQE prepares "
           "two UPDATE branches concurrently and one sees stale memoized task groups, rescanning the "
           "whole table while the commit deletes only the affected files. Reproduces 3–4 times in 10 on "
           "Spark 4.0/4.1 + Iceberg 1.11.0; a reported 71M-row production table doubled. Iceberg Java "
           "has had no release in four months (1.12.0 is gated on one encryption-key PR).",
         act="Use MERGE INTO instead of subquery UPDATE, or disable AQE for those statements.",
         url="https://github.com/apache/iceberg/issues/18004"),
    dict(k="postgres-mcp-servers-readonly-bypass", due="2026-09-09",
         t="<b>Two independent Postgres MCP servers failed their read-only guarantees, and one has no "
           "release.</b> <code>awslabs.postgres-mcp-server</code> &lt; 1.1.7: CVE-2026-87911 (CVSS 9.6) "
           "— <code>COPY … TO PROGRAM</code> slips past the read-only deny-list for OS command execution "
           "<i>in default read-only mode</i>; plus CVE-2026-85787. <b>Fixed in 1.1.7.</b> "
           "<code>crystaldba/postgres-mcp</code>: CVE-2026-85620 (CVSS 9.2) — "
           "<code>SELECT pg_read_file(...)</code> is blocked but "
           "<code>SELECT * FROM pg_read_file(...)</code> is not, because a function in a FROM clause "
           "parses as a RangeFunction the validator never checks. <b>v0.3.0 is still the latest release; "
           "the fix is an open PR.</b>",
         act="Upgrade the AWS one to 1.1.7. For the other, the remedy is operational: run it as a role "
             "with neither superuser nor pg_read_server_files.",
         url="https://www.vulncheck.com/advisories/postgres-mcp-pro-0.3.0-restricted-mode-bypass-via-from-clause-function"),
    dict(k="percona-psmdb-unpatched-auth-off", due="2026-09-08",
         t="<b>MongoDB CVE-2026-82067 (CVSS 9.2) can leave the authorization subsystem in its default "
           "DISABLED state at startup — and Percona Server for MongoDB has no fixed build.</b> Improper "
           "case-sensitivity handling in config validation; anyone with network reach then has full "
           "admin. MongoDB fixed it 2026-09-08 in 8.0.30 / 8.3.9 / 7.0.41 (now 8.0.32 / 8.3.11 / 7.0.43 "
           "after a second memory-corruption fix three days later). PSMDB's newest builds are 8.0.29-13, "
           "8.3.8-2 and 7.0.40-22 — all below the fix — and its advisory thread has not moved since May.",
         act="Empirical check beats a version check: point an unauthenticated client at every node and "
             "confirm it is rejected.",
         url="https://www.mongodb.com/alerts"),
]
existing_patch = {r["k"] for r in led["patch"]}
for row in NEW_PATCH:
    if row["k"] not in existing_patch:
        led["patch"].append(row)
        report.append("NEW patch row: %s" % row["k"])

NEW_EVENTS = [
    dict(k="istio-gcp-retirement-schedule-oct-dec", date="2026-10-13", lane="DevOps",
         t="Istio's second GCP-artifact \"scream test\" — 15:00–18:00 UTC, three hours (the first ran "
           "one hour on 2026-09-15). Then <b>17 Nov 15:00–21:00 UTC (6h)</b> and <b>8–9 Dec, a full 24 "
           "hours</b>, before permanent retirement in December. <code>gcr.io/istio-release</code>, "
           "<code>registry.istio.io</code> and <code>istio-release.storage.googleapis.com</code> all go "
           "dark; images move to Docker Hub, charts to <code>blob.istio.io</code> / "
           "<code>ghcr.io/istio/release/charts</code>.",
         act="Treat each test as a free CI failure-drill. The December one is not survivable by waiting.",
         url="https://istio.io/latest/blog/2026/retirement-of-gcp/"),
    dict(k="istio-129-eol-oct12", date="2026-10-12", lane="DevOps",
         t="Istio 1.29 end of support. Upgrade path is 1.31, which supports Kubernetes 1.32–1.36 and "
           "carries the fix for ISTIO-SECURITY-2026-006 (13 Envoy CVEs, aggregate CVSS 7.7) — two of "
           "which are policy-bypass shaped: Envoy and the backend disagreeing on dot-segment paths, and "
           "a <code>safe_regex</code> non-UTF-8 fail-open that makes a negative RBAC rule silently pass.",
         act="If you do path-based authz on the mesh, read the two bypass CVEs before upgrading.",
         url="https://istio.io/latest/news/support/announcing-1.29-eol/"),
    dict(k="k8s-137-selinux-default-action-required", date="2026-10-01", lane="DevOps", tbd=True,
         t="Kubernetes v1.37 \"Garhwal\" (released 2026-08-26) carries a genuine <b>ACTION REQUIRED</b>: "
           "<code>SELinuxMount</code> graduates to GA <b>enabled by default</b>, which can break running "
           "workloads on SELinux-enforcing clusters, particularly volumes shared between privileged and "
           "unprivileged pods. Two more upgrade blockers: <code>scheduling.k8s.io/v1alpha2</code> is "
           "removed outright, and kubeadm drops the v1beta3 config API (migrate with a <b>1.35</b> binary "
           "— the 1.37 one cannot read your old config). EKS is still on 1.36 and GKE has 1.37 only in "
           "alpha preview, so this is planning work with no fixed date of its own.",
         act="Audit on a v1.36 cluster and set seLinuxChangePolicy before you upgrade.",
         url="https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.37.md"),
    dict(k="windows11-arm-vs2026-image-migration", date="2026-09-30", lane="DevOps",
         t="GitHub migrates the <code>windows-11-arm</code> hosted runner image to Visual Studio 2026, "
           "gradually between 2026-09-21 and 2026-09-30. <b>Breaking for workflows that depend on "
           "VS2022.</b> Test ahead with <code>runs-on: windows-11-vs2026-arm</code>.",
         act="A one-line runs-on change tells you now instead of during the rollout.",
         url="https://github.blog/changelog/2026-08-20-windows-11-arm64-vs2026-image-generally-available"),
    # NOTE: python-oracledb's year-based versioning (4.0.2 -> 26.0.0, which kills
    # every `oracledb<5` pin) deliberately does NOT go here. Event Horizon is a
    # forward timeline; a thing that already happened with no future date would be
    # added and retired in the same pass. It belongs in Perf Signals instead.
]
existing_ev = {r["k"] for r in led["events"]}
for row in NEW_EVENTS:
    if row["k"] not in existing_ev:
        led["events"].append(row)
        report.append("NEW event row: %s (%s)" % (row["k"], row["date"]))

# ----------------------------------------------------------------- retirement
# Spec: drop event rows once the date passes; Since-yesterday notes them passing.
retired = [r for r in led["events"] if (r.get("date") or "") and r["date"] < TODAY]
led["events"] = [r for r in led["events"] if not ((r.get("date") or "") and r["date"] < TODAY)]
led["retired_events"] = [{"k": r["k"], "date": r["date"], "t": r["t"][:200]} for r in retired]
report.append("RETIRED %d event rows whose date has passed" % len(retired))

json.dump(led, open("lens/ledger_064.json", "w"), ensure_ascii=False, indent=1)
print("\n".join("  " + x for x in report))
print("\nledger 064: events=%d patch=%d claims=%d ownclaims=%d promises=%d gaps=%d benchmarks=%d"
      % (len(led["events"]), len(led["patch"]), len(led["claims"]), len(led["ownclaims"]),
         len(led["promises"]), len(led["gaps"]), len(led["benchmarks"])))
