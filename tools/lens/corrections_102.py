#!/usr/bin/env python3
"""Edition-102 ledger corrections. Applied BEFORE section generation (09-14).

Every entry was checked against the board first (probe_board.py) so a row that
was already right is not "corrected" again -- the 10-08/10-09 lesson.
"""
import json, sys

L = json.load(open('lens/ledger_102.json'))
P = {r['k']: r for r in L['patch']}
applied, skipped = [], []

def fix(key, *, due=None, t=None, note=''):
    r = P.get(key)
    if r is None:
        skipped.append(key + '(absent)'); return
    if due is not None:
        r['due'] = due
    if t is not None:
        r['t'] = t
    applied.append(key + ('/' + note if note else ''))

# 1. Hudi -- THREE corrections. The board said "silently return wrong rows ...
# under Spark 4.1". Today's Open Formats lane read the issue directly: it is
# Spark 4.0.2 and the issue states Spark 4.1+ is NOT affected; MOR reads FAIL
# LOUDLY with [MALFORMED_VARIANT]; and the durable corruption is COW with the
# SPARK record merger persisting metadata/value bytes swapped into the base
# file, while the DEFAULT Avro merger is correct -- so a mitigation exists today.
fix('hudi-variant-wrong-rows-no-release',
    due="<b>fix on master only, carried by NO release</b> &middot; <code>branch-1.2.x</code> dormant 22d, no 1.2.2 proposed",
    t=("<span class='corr'>CORRECTED 10-24</span> <b>Three corrections to this row, all from reading the issue "
       "rather than the summary.</b> (1) It is <b>Spark 4.0.2</b>, and the issue states <b>Spark 4.1+ is not "
       "affected</b> &mdash; this board carried &ldquo;under Spark 4.1&rdquo;, which inverted the affected set. "
       "(2) Merge-on-Read reads of a variant nested in a struct <b>fail loudly</b> with "
       "<code>[MALFORMED_VARIANT]</code> under either record merger; they do not silently return wrong rows. "
       "(3) The durable damage is <b>Copy-on-Write with the SPARK record merger</b>, which rewrites carried-over "
       "rows with the <code>metadata</code> and <code>value</code> bytes <b>swapped and persisted into the base "
       "file</b>, so every later read of those rows fails &mdash; while COW with the <b>default Avro merger is "
       "correct</b>. That last point is the actionable one and the prior framing hid it: there is a mitigation "
       "today (keep the Avro merger, or move to Spark 4.1+). Hudi's own label is "
       "<code>issue:data-corruption</code>. Fix #20161 landed on master 2026-10-01 and was never backported; "
       "<code>branch-1.2.x</code> has been at 1.2.2-SNAPSHOT since 2026-09-24 with its newest commit 2026-10-02, "
       "and the October dev list carries no 1.2.2 vote, RC or call for fixes. So the fix exists and is "
       "unreachable. Also worth knowing for whoever probes this next: <b>Hudi's JIRA is effectively dead</b> "
       "&mdash; the newest issue was created 2025-09-10 and the project moved to GitHub Issues."), note='3x')

# 2. Argo CD -- today's DevOps lane counted TWO advisories this window, not
# four, and only one is 9.9. The unpatched population is also wider than the
# row said: 3.0 through 3.2 are out of support too, not just 2.x.
fix('argocd-four-99-criticals-no-v2-fix',
    due="no fix for <b>2.x AND 3.0&ndash;3.2</b>, ever &middot; fixed 3.3.15 / 3.4.10 / 3.5.4 / 3.6.0-rc2",
    t=("<span class='corr'>CORRECTED 10-24</span> <b>The count was wrong and the stranded population was too "
       "narrow.</b> This window carries <b>two</b> new Argo CD advisories, not four, and only one is CVSS 9.9: "
       "<b>CVE-2026-77459</b> (PreDelete/PostDelete hooks bypass AppProject destination-namespace and resource "
       "restrictions, <code>S:C</code>) and <b>CVE-2026-55797</b> (repo-server command injection via a crafted "
       "SSH repository SOCKS5 proxy URL). Both carry <code>last_affected: 2.14.21</code> with no fixed version, "
       "and the advisory text widens it beyond what this board said: &ldquo;Argo CD 2.x and 3.0 through 3.2 are "
       "out of support and will not receive a patch.&rdquo; The mechanism is the part worth keeping: delete hooks "
       "run with the <b>application-controller's</b> credentials, so a user with push access to the backing Git "
       "repo can commit a hook the project would otherwise reject and have it create cluster-scoped objects on "
       "Application deletion. <b>No configuration setting applies the project check to delete hooks</b> &mdash; "
       "the only levers are Git write access, who may delete Applications, and the controller's own RBAC."), note='2not4')

# 3. gosnowflake v1 -- "patched versions: None" is ACCURATE, not a data-quality
# bug: Snowflake's CNA encodes v1 and /v2 as separate packages and the fix
# exists only on /v2. That changes the remediation from "wait" to "migrate".
fix('snowflake-86597-creds-in-driver-logs',
    due="patched 2026-09-03 &middot; <b>v1 unfixable: the fix is on the <code>/v2</code> module path</b>",
    t=("<span class='corr'>CORRECTED 10-24</span> <b>The v1 &ldquo;patched versions: None&rdquo; field is "
       "accurate, and the reason matters.</b> Snowflake's CNA record encodes the Go driver as two packages: "
       "<code>github.com/snowflakedb/gosnowflake</code> with <code>lessThanOrEqual: 1.19.1</code> and <b>no "
       "fixed event at all</b>, and <code>.../v2</code> fixed at 2.2.0. v1's last release is <b>1.19.1, tagged "
       "2026-04-08</b> &mdash; five months before the 2026-09-08 advisories. So this is not a pending backport "
       "and not an abandoned project: the fix is on a different <b>import path</b>, and remediation is a module "
       "migration that Snowflake's own 2.0.0 notes label a breaking change. Go's <code>/vN</code> convention "
       "guarantees this recurs, because the module path IS the package identity &mdash; a v1 line that stops "
       "receiving releases is indistinguishable in advisory data from a dead one. Three CVEs ride it: "
       "CVE-2026-85525 (7.4, OCSP validation &mdash; the only one needing no feature precondition), "
       "CVE-2026-86600 (8.2) and CVE-2026-86597. Fixed elsewhere: Python 4.7.3, JDBC 4.3.4, Node 3.3.0, "
       "PHP PDO 4.2.0, ODBC 3.20.0."), note='v2path')

# 4. PgBouncer -- the row described the CVEs but never named the stranded
# population, which is why the radar could not rank it. Today's OLTP lane
# measured it: Azure ships 1.25.2 with no customer override.
fix('pgbouncer-scram-nonce-preauth-crash-19888',
    due="fixed 1.26.1 &middot; <b>no fix has reached Azure, pinned at 1.25.2 with no customer override</b>",
    t=("<span class='corr'>ENRICHED 10-24</span> <b>The stranded population is now named, and it is a managed "
       "service.</b> <b>Azure Database for PostgreSQL's built-in PgBouncer is 1.25.2</b> on every supported "
       "major version &mdash; re-verified against Azure's own concept page (<code>ms.date</code> 2026-10-03) "
       "&mdash; which is inside the affected range of all six CVEs fixed in 1.26.0 and 1.26.1. The service "
       "release notes show the last PgBouncer bump was <b>July 2026</b>, the bump cadence runs 6&ndash;12 months "
       "(1.22.1 Apr 2024 &rarr; 1.23.1 Oct 2025 &rarr; 1.25.1 Mar 2026 &rarr; 1.25.2 Jul 2026), and the customer "
       "cannot change the version. The same page claims Azure &ldquo;ensure[s] that PgBouncer stays up to date "
       "with the latest features and security patches&rdquo;, which cannot be true alongside a pinned 1.25.2. "
       "<b>CVE-2026-107350 (CVSS 8.8) has no configuration workaround</b> &mdash; one known <code>auth_file</code> "
       "password logs an attacker in as any other SCRAM user including backend superusers &mdash; so the only "
       "levers are connecting on 5432 or moving to a self-managed pooler. Two scope corrections for Azure "
       "specifically: CVE-2026-107348 almost certainly does not apply (Azure does not expose "
       "<code>max_packet_size</code>), and CVE-2026-107349 applies only where "
       "<code>pgbouncer.ignore_startup_parameters</code> is set without <code>options</code> &mdash; which is a "
       "<b>config-only mitigation available today</b>."), note='azure-stranded')

json.dump(L, open('lens/ledger_102.json','w'), indent=1)
print('corrections applied: %s' % ', '.join(applied))
print('skipped: %s' % (', '.join(skipped) or '-'))
