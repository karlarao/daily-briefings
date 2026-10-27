#!/usr/bin/env python3
"""Edition-104 new rows. Identity is DECLARED (the 09-11 rule); reuse_key runs as
an ADVISORY only and prints every same-date parent row so a duplicate is visible
before it ships."""
import json, sys
sys.path.insert(0, 'tools/lens')
import ledger_surgery as LS

TODAY = "2026-10-26"
L = json.load(open('lens/ledger_104.json'))
existing = {r['k'] for ln in L if isinstance(L[ln], list)
            for r in L[ln] if isinstance(r, dict) and 'k' in r}

NEW_PATCH = [
 dict(k="jdk-91403-near-twin-respin-oct21",
   due="<b>the 21 Oct respin did not finish the job</b> &middot; separate Oracle alert, same component",
   t=("<b>CVE-2026-114820 has a near-twin the board was not carrying: CVE-2026-91403, also CVSS 9.1, also "
      "security-libs/<code>javax.net.ssl</code>, advisory 2026-10-21 &mdash; three days and one BPR apart.</b> "
      "91403's affected list is 27.0.1 / 25.0.5 / 21.0.13 / 17.0.21 / 11.0.32.1 / 8u504; 114820's is the same set at "
      "<code>&hellip;0.2</code>. The reading that follows is that the 21 October removal was incomplete and a second one "
      "shipped three days later &mdash; <b>so a customer who followed the first alert to the letter is exposed again, and "
      "the only way they learn that is by reading a second alert</b>. Oracle published a separate Security Alert for each, "
      "and <code>openjdk.org/emudhra</code> names only 114820 (JDK-8395690) as the id to look for in a release note. "
      "<b>If your scanner shows one of the two, it is reading a stale feed.</b> Corroborating the incompleteness from "
      "the other side: Corretto 21's CHANGELOG claims 91403 is addressed in 21.0.13.0.10 while the 21 Oct advisory lists "
      "21.0.13 as affected and the changelog's own issue table contains no cacerts change."),
   url="https://www.oracle.com/security-alerts/alert-CVE-2026-91403.html"),
 dict(k="arrow-rs-60-newest-major-is-the-unpatched-one",
   due="<b>fixed on 57/58/59, no 60.0.x patch exists</b> &middot; remedy is to pin BACK one minor",
   t=("<b>The no-reachable-fix shape inverted this week: arrow-rs and parquet-rs backported a use-after-free and a "
      "correctness set to three maintenance lines on the same day &mdash; 57.3.2, 58.4.1 and 59.3.2, all 2026-10-26 "
      "&mdash; and there is no 60.0.x patch at all, so 60.0.0 (2026-09-15), the current major and the version a new "
      "project picks, is the one line without the fixes.</b> Verified against the full crates.io version list: nothing "
      "exists between 60.0.0 and today. The bug is a use-after-free in <code>Buffer::shrink_to_fit</code> when "
      "<code>MemoryReservation::resize</code> panics, alongside offset handling in <code>RunArray</code>/"
      "<code>MutableArrayData</code>, <code>UnionFields</code> validation, sliced sparse unions and null checks in view "
      "equality. <b>No CVE, no GHSA, no RUSTSEC entry</b> &mdash; it ships in a maintenance release with no security "
      "section, so nothing will tell you. Deliberately <i>not</i> rated act-now: the trigger is an OOM-handling path "
      "rather than attacker-reachable input, and a fixed release is one minor back on a line still receiving patches. "
      "<b>The transferable point is that &ldquo;pin to the newest major&rdquo; is the default advice everywhere and it is "
      "wrong here.</b>"),
   url="https://github.com/apache/arrow-rs/releases"),
 dict(k="mariadb-mdev-33966-fix-merged-no-released-build",
   due="<b>Fixed in Jira against 11.8.10 / 12.3.4 / 13.1.2 &mdash; none of which exists</b>",
   t=("<b>A 3.5&times; MariaDB throughput regression is fixed in git and in no released build, which makes it the second "
      "independent instance of the &ldquo;fix merged, no tag&rdquo; shape this week.</b> MDEV-33966 is marked "
      "Critical/Fixed with fixVersions <b>11.8.10, 12.3.4 and 13.1.2</b>, while the newest <i>released</i> builds are "
      "11.8.9, 12.3.3 and 13.1.1. The Foundation reproduced it with TAF on a memory-resident POINTS-COVERED-PK workload "
      "(10M rows &times; 8 tables, 40 threads, 90G buffer pool, EPYC 9454): parent commits gave 17,925 / 18,739 / 18,737 "
      "TPS against 66,653 / 68,646 / 66,145 patched. <b>The JIRA &ldquo;affects&rdquo; list includes 11.4 and 10.11, both "
      "still LTS, and neither appears in fixVersions</b> &mdash; so on today's data 11.4 LTS has no fix targeted at all. "
      "No MariaDB release landed inside the window. Set this beside Kubernetes carrying Go 1.26.10 on four release "
      "branches with nothing tagged: two projects, one week, and a shape that every version-reading scanner is blind to "
      "by construction."),
   url="https://jira.mariadb.org/browse/MDEV-33966"),
 dict(k="mysql-80-server-absent-from-oct-2026-cpu",
   due="<b>absent from all 80 Server rows of the October CPU</b> &middot; fixes are 9.7.4 / 8.4.13 / 26.10.0",
   t=("<b>Oracle's October 2026 CPU carries 98 new MySQL security patches, 29 remotely exploitable without "
      "authentication &mdash; and MySQL Server 8.0 appears in none of the 80 Server rows.</b> Parsed from the risk "
      "matrix: top scores are CVE-2026-9547 and CVE-2025-15467 at 9.8 (bundled curl/OpenSSL), then <b>CVE-2026-101781 at "
      "8.8 &mdash; Server: Group Replication GCS, remotely exploitable without auth over Adjacent Network with "
      "C:H/I:H/A:H</b>, i.e. the GR interconnect. The &ldquo;Supported Versions Affected&rdquo; column lists Server as "
      "8.4.0&ndash;8.4.12 / 9.7.0&ndash;9.7.3 / 26.7.0&ndash;26.7.1 in 67 of 80 rows; 8.0.x shows up only under MySQL "
      "Cluster and Enterprise Backup. For the 8.0 Server population the quarter's fixes do not exist in a community "
      "build. <b>And the patched population has its own gap: Percona Server's newest 8.4 is 8.4.11-11 (2026-08-20), two "
      "upstream patch levels behind</b>, so the 8.8 GR flaw is not reachable there either."),
   url="https://www.oracle.com/security-alerts/cpuoct2026.html"),
]

print("--- reuse_key advisory on %d drafted patch rows ---" % len(NEW_PATCH))
for row in NEW_PATCH:
    if row['k'] in existing:
        raise SystemExit("key already on board: " + row['k'])
    LS.reuse_key(row, L['patch'], 'due', 'patch')

for row in NEW_PATCH:
    row.setdefault('first_seen', TODAY)
    row['last_seen'] = TODAY
    row['days'] = 1
    L['patch'].append(row)

json.dump(L, open('lens/ledger_104.json','w'), indent=1)
print("\npatch %d -> %d  (+%d new)" % (len(L['patch'])-len(NEW_PATCH), len(L['patch']), len(NEW_PATCH)))
print("sizes:", {k: len(v) for k, v in L.items() if isinstance(v, list)})
