#!/usr/bin/env python3
"""Edition 109: ledger corrections FIRST, then additions/enrichments.

Build-order rule (09-14): corrections are applied to the LEDGER before any
section is generated, never to the assembled HTML afterwards.

Today's shape repeats the 10-30 finding: almost the entire November deadline
wall was ALREADY on the board with correct dates, so the work went into
corrections + enrichment rather than new event rows. Probe before drafting.
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import ledger_surgery as LS
import lens_extra as X

led = json.load(open(os.path.join(SP, "ledger_109.json")))
TODAY = "2026-10-31"

def R(sec, key):
    for r in led[sec]:
        if r["k"] == key:
            return r
    raise SystemExit("MISSING %s/%s" % (sec, key))

corr, enriched, new_ev, new_patch = [], [], [], []

# ======================================================= PHASE 1: CORRECTIONS

# C1 -- a day-precise date the vendor does not publish, and an agent caught a
# search summary asserting exactly the board's date against the primary page.
r = R("events", "snowflake-cortex-models-allowlist-rbac-nov18")
r.pop("date", None)
r["t"] = ("<span class='corr'>CORRECTED 10-31 &mdash; date withdrawn</span> <b>This board carried "
  "2026-11-18. Snowflake's own BCR-2378 page gives <i>&ldquo;January 2027&rdquo;</i> &mdash; a month, no day "
  "&mdash; for bundle 2026_07 becoming generally enabled and <code>CORTEX_MODELS_ALLOWLIST</code> being fully "
  "retired.</b> The staged retirement is real and partly already done: allowlist-based access was removed "
  "2026-09-08, model RBAC is now the only mechanism, and it is now enforced for embedding models too "
  "(<code>AI_EMBED</code>, <code>AI_MULTI_EMBED</code>, <code>AI_SIMILARITY</code>, "
  "<code>EMBED_TEXT_768/1024</code>). What is gone is the day. The catch is worth recording for its own sake: "
  "today's lane found a search summary asserting &ldquo;fully retired 2026-11-18&rdquo; &mdash; the board's "
  "exact figure &mdash; and overruled it from the primary page. <b>A secondary source agreeing with your board "
  "is not corroboration when both may share one bad origin.</b> Operational note that survives the date change: "
  "a plain <code>REVOKE APPLICATION ROLE &hellip; FROM ROLE PUBLIC</code> does <b>not</b> remove the bootstrap "
  "grant; you need <code>CALL SNOWFLAKE.LOCAL.REVOKE_FROM_PUBLIC_APPLICATION_ROLE(&hellip;)</code>.")
corr.append("snowflake-cortex-models-allowlist: 2026-11-18 -> UNDATED (vendor says 'January 2027')")

# C2 -- a no-fix claim that has partly resolved. Percona closed to 8-9 days.
r = R("patch", "mongodb-server-131805-sharded-rename-dataloss")
r["due"] = ("fixed 2026-10-13 in 7.0.45 / 8.0.34 / 8.3.13 / 9.0.4 &middot; <b>Percona now carries it (8&ndash;9d "
            "lag)</b> &middot; still NO fix on 5.0 / 6.0 / 8.2")
r["t"] = (str(r["t"]) + " <span class='corr'>CORRECTED 10-31</span> <b>The &ldquo;no fix on ANY Percona build&rdquo; "
  "half of this row is now wrong.</b> Percona Server for MongoDB <b>8.0.34-15 (22 Oct)</b> and "
  "<b>7.0.45-24 (21 Oct)</b> track the upstream patches that fix SERVER-131805 and the 13 Oct CVE batch &mdash; "
  "an <b>8&ndash;9 day</b> lag rather than the multi-month gap that made Percona this board's standing "
  "&ldquo;patched upstream, unpatched for you&rdquo; example since September. <b>A resolved no-fix is worth as "
  "much as a new one</b>, so it is recorded rather than quietly dropped. What has NOT changed: 5.0, 6.0 and the "
  "EOL 8.2 line still have no patched build, and the failure mode is unchanged &mdash; a cross-database "
  "<code>renameCollection</code> on a sharded cluster can destroy both namespaces and <b>return success</b>, so "
  "the application gets no signal at all.")
corr.append("mongodb-131805: Percona no longer unpatched (8.0.34-15 / 7.0.45-24) -- a RESOLVED no-fix")

# C3 -- day count on a KEV row that is measured, not estimated.
r = R("patch", "cve-2026-21962-ohs-weblogic-kev")
r["due"] = ("KEV due 2026-08-27 (<b>65d PAST DUE</b>) &middot; fix exists since the January 2026 CPU")
r["t"] = (str(r["t"]) + " <span class='corr'>RE-MEASURED 10-31</span> <b>65 days past due</b>, and today's lane "
  "re-confirmed against Oracle's own CVE-to-advisory map that the fix has been available since the "
  "<b>January 2026 CPU</b> and is <b>not re-shipped in the October CPU</b> &mdash; a third consecutive quarter. "
  "This is the board's cleanest example of unpatched <i>by omission</i> rather than by unavailability, which is "
  "the worse of the two.")
corr.append("cve-2026-21962: 64d -> 65d past due, fix-by-omission re-confirmed")

# C4 -- "TODAY" inside carried prose rots overnight (the 10-29/10-30 class).
r = R("patch", "k8s-oct-patch-overdue-all-four-branches")
r["due"] = ("<b>1.34 went EOL 2026-10-30 with 1.34.13 never cut</b> &middot; <b>fix merged on every branch, "
            "tagged in nothing</b>")
r["t"] = (str(r["t"]) + " <span class='corr'>CORRECTED 10-31</span> <b>Date hygiene, not new facts: this row said "
  "&ldquo;1.34 EOL TODAY&rdquo;, which was true when it was written and false by the next morning.</b> 1.34 "
  "reached end of life on <b>2026-10-30</b>. A relative word inside carried prose is a dated claim that rots "
  "silently &mdash; the row now states the date.")
corr.append("k8s row: relative 'TODAY' replaced with 2026-10-30 (carried-prose date rot)")

# C5 -- a phantom tag in secondary coverage, measured against the real tag list.
r = R("patch", "edk2-97631-preboot-pxe-rce-no-tag")
r["t"] = (str(r["t"]) + " <span class='corr'>VERIFIED 10-31</span> <b>Three things measured directly today. "
  "(1) The fix IS in <code>master</code></b> &mdash; PR #13302 merged 2026-10-15 (<code>fa78907</code>), with a "
  "<code>ZeroMem</code> plus a bounded <code>CopiedLen</code> loop in <code>PxeBcSupport.c</code>. "
  "<b>(2) <code>edk2-stable202610</code> does not exist.</b> Secondary write-ups claiming the fix shipped in that "
  "tag are wrong: the tag list jumps 202605 &rarr; 202608 and a raw fetch 404s, so the newest tag "
  "(<code>edk2-stable202608</code>, 2026-08-12) still predates the fix and the GHSA itself continues to read "
  "&ldquo;Not patched currently&rdquo;. <b>(3) Debian ships it unfixed in every suite</b> &mdash; bookworm, "
  "bookworm-security, trixie, forky and sid, with trixie marked <code>&lt;no-dsa&gt;</code> &mdash; and because "
  "OVMF is the firmware QEMU/KVM guests boot, <b>any VM that netboots has the same pre-boot exposure with no "
  "distro update coming</b>. A PoC posted 2026-10-29 argues a flooder can still force the DoS, so treat the "
  "merged fix as possibly incomplete. The vendor-independent remedy is unchanged: take network boot out of the "
  "boot order.")
corr.append("edk2-97631: 'edk2-stable202610' is a phantom tag; Debian unfixed incl. OVMF guests")

# ============================================ PHASE 2: ENRICH (no fresh slugs)

def enrich(sec, key, add, due=None, note=None):
    r = R(sec, key)
    r["t"] = str(r.get("t", "")) + " " + add
    if due:
        r["due"] = due
    r["last_seen"] = TODAY
    enriched.append(note or key)

enrich("patch", "clickhouse-116366-unauth-rce-no-267-fix",
  "<span class='corr'>SHARPENED 10-31</span> <b>Two measured traps, pointing opposite ways.</b> "
  "The tag list is a <i>false positive</i>: <code>v26.7.37.6-stable</code> was tagged 2026-10-22 and "
  "<code>v26.7.36.9-stable</code> on 10-21, while <code>SECURITY.md</code> marks 26.7, 26.6, 26.5, 26.4, 26.2 "
  "and 26.1 all &ldquo;N&rdquo; for security updates &mdash; so a 26.7 operator sees activity nine days ago and "
  "concludes they are maintained. <b>They are not, and there will be no 26.7 build with this fix.</b> "
  "GitHub Releases is a <i>false negative</i>: <code>releases/tag/v26.9.27.3-stable</code> 404s and the tag page "
  "tops out at <code>v26.10.2.103-stable</code>, while <code>packages.clickhouse.com/tgz/stable/</code> serves "
  "all four patched builds with HTTP 200 (bogus versions 404, so it is not a wildcard). <b>The authoritative "
  "pair is the vendor's supported-versions table plus the package repository &mdash; not either feed alone.</b>",
  note="clickhouse-116366 (tag false-positive + GitHub-Releases false-negative, both measured)")

enrich("patch", "pgbouncer-107350-scram-bypass",
  "<span class='corr'>NEW POPULATION 10-31</span> <b>A population with no lever at all: Azure Database for "
  "PostgreSQL's built-in PgBouncer is pinned at <code>1.25.2</code> and Azure manages its updates</b>, so a "
  "flexible server with <code>pgbouncer.enabled = true</code> is exposed to this 8.8 SCRAM bypass with "
  "<b>no customer-side upgrade path</b> &mdash; 1.25.2 predates both the 09-23 and the 10-14 CVE batches. "
  "The workarounds are architectural: disable the built-in pooler and run your own 1.26.1, or move to "
  "PgBouncer/PgCat on VMs (Azure's own doc already recommends PgCat for multithreaded scale). "
  "Azure defaults <code>ignore_startup_parameters</code> to empty, which probably takes the companion DoS "
  "(CVE-2026-107349) off the table there &mdash; but <b>the auth bypass is config-independent</b>. "
  "Scanner status re-measured today: <b>all six 2026 PgBouncer CVEs still have zero CPE rows in NVD</b>, OSV "
  "carries them only as Bitnami and Debian source records, and the Debian record lists the <i>fixed</i> version "
  "<code>1.26.1-1</code> inside its own affected list. <code>SHOW VERSION;</code> remains the only real test.",
  note="pgbouncer-107350 (Azure's managed pooler pinned at 1.25.2 -- no reachable fix)")

enrich("patch", "brotli-111497-kev-runtime-wide-scanner-blind",
  "<span class='corr'>RE-MEASURED 10-31</span> <b>Ten days to the KEV date, and the remediation list grew "
  "rather than shrank.</b> Fixed runtimes: Node <b>22.23.4 / 24.22.1 / 26.12.1</b> (21 Oct), .NET "
  "<b>8.0.33 / 9.0.22 / 10.0.14</b> out-of-band (25 Oct) plus .NET 11 RC3, Bun <b>1.4.4</b>, PyPI "
  "<code>brotli</code> / <code>brotlicffi</code> <b>1.2.1 / 1.2.1.0</b>, and Envoy "
  "<b>1.40.0 / 1.39.3 / 1.38.6 / 1.37.8 / 1.36.12</b>. <b>Patching the OS <code>libbrotli</code> fixes none of "
  "them</b> &mdash; each compiles its own copy &mdash; and <b>.NET self-contained apps and container images must "
  "be rebuilt and republished</b>, because a newer runtime on the host does not touch the runtime bundled into "
  "the app. The scanner picture is now wrong in both directions on one CVE: the record has "
  "<code>package: null</code> with GIT-only ranges so a lockfile query matches nothing, while NVD has attached "
  "unbounded <code>clickhouse</code>, <code>duckdb</code> and <code>apache:arrow</code> CPEs so those match "
  "forever despite neither vendor publishing a word. <b>The ecosystem data lives only on the alias GHSA, and it "
  "covers PyPI and nothing else</b> &mdash; for Node, Bun and .NET the vulnerable artifact is the runtime "
  "binary, which no manifest names.",
  note="brotli-111497 (Envoy + .NET rebuild requirement; CPE wrong in both directions)")

enrich("patch", "supermicro-bmc-18450-two-skus-tbd",
  "<span class='corr'>RE-MEASURED 10-31</span> <b>Nine CVEs across the two 26 Oct advisories, credited to "
  "runZero, and Supermicro says it is &ldquo;still testing and validating affected products&rdquo; &mdash; "
  "several SKUs still read TBD rather than a fixed firmware version</b> (X12DGU, X13SEW-TF-OS1 among them). "
  "The headline <b>CVE-2026-18450 (CVSS 9.8, AV:N/PR:N)</b> is a missing integrity/encryption check on IPMI "
  "commands, so crafted packets execute arbitrary commands on an <i>active RMCP+ session</i>. Behind it: "
  "CVE-2026-65220 (8.8) RAKP+ privilege escalation to administrator, CVE-2026-18449 (7.5) a hardcoded SMCRAKP "
  "key, CVE-2026-65219 (7.4) session establishment via crafted RAKP Message 3 ordering, CVE-2026-65211 (7.2) "
  "authenticated read/write of BMC physical memory, CVE-2026-65213 (6.6) root command execution, CVE-2026-65210 "
  "(4.9) arbitrary BMC file read, CVE-2026-18451 (3.1) a time-seeded KVM launch token, and CVE-2026-16521 (7.2) "
  "OS command injection in the syslog feature. One internal inconsistency worth knowing before you triage from "
  "the page: the CVE-2026-65211 heading says Critical while its own table says High. <b>No workaround is "
  "offered; the vendor-independent one is to get IPMI/Redfish off any routable path.</b>",
  note="supermicro BMC (nine CVEs, SKUs still TBD, 9.8 on an active RMCP+ session)")

enrich("events", "gitlab-97229-kev-due-nov1",
  "<span class='corr'>ENRICHED 10-31</span> <b>Due tomorrow, and a Metasploit module PR is open.</b> CISA marks "
  "it <code>automatable: yes</code>. Affected 19.2&ndash;19.2.7, 19.3&ndash;19.3.4 and 19.4&ndash;19.4.1; fixed "
  "in <b>19.2.8 / 19.3.5 / 19.4.2</b>, released 2026-10-12, so the fix has been sitting there for nineteen days. "
  "Self-managed only. The same patch carries CVE-2026-14814, a permissive regex in repository file access that "
  "can poison cached raw-file responses so targeted pipelines execute attacker content and may leak protected "
  "environment variables. <b>The underlying defect generalises:</b> CISA's own note says other products may be "
  "affected by the same Ruby/Onigmo integer overflow in the regex compiler &mdash; so anything that compiles "
  "user-supplied patterns on an Onigmo engine inherits the question.",
  note="gitlab-97229 (Metasploit PR open, automatable:yes, fix available 19 days)")

enrich("events", "redshift-rejects-tls-1-0-1-1-provisioned-and-serverless-and",
  "<span class='corr'>IN FORCE 10-31</span> <b>This is the day. AWS's behavior-changes page reads "
  "&ldquo;Beginning October 31, 2026&hellip; Incoming connections that use TLS versions 1.0 or 1.1 will be "
  "rejected&rdquo;</b>, provisioned and Serverless alike; warehouses not using TLS at all are unaffected. The "
  "pre-flight queries are published per flavour and are the only way to find a straggler before it pages you: "
  "<code>sslversion</code> in <code>STL_CONNECTION_LOG</code> (provisioned), <code>ssl_version</code> in "
  "<code>SYS_CONNECTION_LOG</code> (Serverless). The companion trap also landed in-window: <b>JDBC 2.3.0 "
  "(12 Oct) and the Python connector 2.2.0 (9 Oct) both flipped default <code>sslmode</code> from "
  "<code>verify-ca</code> to <code>verify-full</code></b>, which today only logs a hostname-mismatch warning and "
  "still connects &mdash; both changelogs state a future release will fail the connection. "
  "<b>That warning in your logs today is the outage in a later release</b>, and CNAMEs, proxies and PrivateLink "
  "aliases are the likely hits.",
  note="redshift TLS 1.2 (in force today; verify-full warn-then-fail is the follow-on)")

enrich("events", "dbr-18-2-eos-nov5",
  "<span class='corr'>ENRICHED 10-31</span> <b>Five days, and the consequence is sharper than &ldquo;no "
  "support&rdquo;: at end-of-support 18.2 &ldquo;is no longer selectable using the UI when you create or update "
  "a compute resource&rdquo;</b> &mdash; so merely <i>editing</i> an existing cluster forces a version change. "
  "Fixes are not backported and running workloads only &ldquo;might continue to run&rdquo; until a best-effort "
  "End of Life six months later, set without prior notice. Only 18.2 is affected: 18 LTS runs to 2029-06-10 and "
  "17.3 LTS to 2028-10-22. <b>One vendor-page contradiction worth not planning around:</b> the lifecycle page "
  "says &ldquo;The end-of-support date is three years after the GA release date&rdquo; while 18.2 shipped "
  "2026-05-05 and ends 2026-11-05 &mdash; six months. The same page explains why (pre-19 runtimes shipped as "
  "minor feature versions), so <b>trust the table, not the sentence</b>.",
  note="dbr-18-2-eos (editing a cluster forces the move; lifecycle page self-contradicts)")

enrich("patch", "mysql-80-server-absent-from-oct-2026-cpu",
  "<span class='corr'>SHARPENED 10-31</span> <b>The asymmetry is the finding: MySQL <i>Server</i> 8.0 has "
  "dropped out of the October CPU risk matrix entirely (EOL), but MySQL <b>Cluster</b> 8.0.0&ndash;8.0.49 is "
  "still listed as affected</b> &mdash; so an NDB 8.0 operator is in scope for this CPU while a Server 8.0 "
  "operator is simply unsupported. The quarter's worst MySQL-native issue is <b>CVE-2026-101781 (CVSS 8.8, "
  "<code>Server: Group Replication GCS</code>, unauthenticated, adjacent-network)</b> &mdash; reachable by "
  "anything on the group-communication network, which is usually &ldquo;the cluster subnet&rdquo;. The LTS fix "
  "is <b>8.4.13</b> (2026-10-20). Note also that the two CVSS 9.8 rows in the MySQL matrix are bundled "
  "third-party libraries (curl CVE-2026-9547, OpenSSL CVE-2025-15467), not server code &mdash; worth knowing "
  "before someone quotes &ldquo;a 9.8 in MySQL&rdquo;.",
  note="mysql-80-cpu (Server 8.0 out of the matrix while Cluster 8.0 stays in)")

# ====================================================== PHASE 3: NEW ROWS
# Every drafted row is probed FIRST -- by date for events, by identifier for
# patch rows (the 09-17 Doris lesson: a story tracked since an earlier date is
# invisible to a date-keyed probe).

NOUNS = {
  "snowflake-auto-suspend-interactive-1h-nov17": ["auto_suspend", "interactive warehouse", "bcr-2473"],
  "snowflake-azure-network-identifiers-nov18": ["network identifier", "bcr-2391", "azure storage"],
  "pinot-73322-lookup-acl-bypass-no-152": ["cve-2026-73322", "pinot", "lookup"],
  "parquet-java-1190-rc9-no-ga-bloom-fix": ["parquet-java", "bloom filter", "1.19.0"],
  "n8n-databricks-node-119557-unpatched": ["cve-2026-119557", "n8n"],
  "mongo-node-driver-timeoutms-crossuser-no-6x": ["timeoutms", "srvallowedhostssuffix", "node driver"],
  "percona-mysql-84-no-oct-cpu-build": ["percona server for mysql", "8.4.11-11"],
  "kernel-98432-mptcp-uaf-go-default-on": ["cve-2026-98432", "mptcp", "multipathtcp"],
  "kafka-110952-oauthbearer-iss-aud-unset": ["cve-2026-110952", "oauthbearer", "jwks"],
  "valkey-cluster-pubsub-heap-overflow-5-branches": ["ghsa-f4q9-j22m-xqq9", "cluster pub/sub", "valkey"],
}

EV = [
 dict(k="snowflake-auto-suspend-interactive-1h-nov17", date="2026-11-17",
      t=("<b>Snowflake interactive warehouses: the default <i>and minimum</i> <code>AUTO_SUSPEND</code> drops from "
         "86,400s (24h) to 3,600s (1h)</b>, planned 2026-11-17 and marked &ldquo;subject to change&rdquo; "
         "(BCR-2473, unbundled). Existing warehouses keep their current value &mdash; but a "
         "<code>CREATE OR REPLACE</code> without an explicit <code>AUTO_SUSPEND</code> picks up the new 1-hour "
         "default, and for an <i>interactive</i> warehouse a suspend/resume <b>resets the cache, incurs warm-up "
         "and starts a new minimum billable period</b>. If you rebuild warehouses from IaC, pin "
         "<code>AUTO_SUSPEND = 86400</code> explicitly before the flip."),
      act="Grep IaC for CREATE OR REPLACE WAREHOUSE without an explicit AUTO_SUSPEND and pin it."),
 dict(k="snowflake-azure-network-identifiers-nov18", date="2026-11-18",
      t=("<b>Snowflake on Azure: allowlists must carry Snowflake Network Identifiers for Azure Storage and Key "
         "Vault from 2026-11-18</b> (BCR-2391, unbundled). Get the prefixes from "
         "<code>SYSTEM$GET_SNOWFLAKE_EGRESS_IP_RANGES</code> and take <i>only</i> those whose <code>usage</code> "
         "includes &ldquo;Network Identifier&rdquo; &mdash; <b>not</b> the &ldquo;Stable Egress IP&rdquo; entries "
         "&mdash; keep your existing subnet-ID rules, and allowlist every prefix. <b>Key Vault requires NSP "
         "migration</b> because of platform restrictions, and Snowflake says to open a ticket for an extension if "
         "you cannot make the date. Validate with <code>SYSTEM$VALIDATE_STORAGE_INTEGRATION</code>, "
         "<code>SYSTEM$VERIFY_EXTERNAL_VOLUME</code> and <code>SYSTEM$VERIFY_CMK_INFO</code> after setting "
         "<code>ENABLE_NETWORK_IDENTIFIER_ALLOWLISTING_VALIDATION</code>. The page does not spell out what breaks "
         "if you miss it, which is its own reason to test early."),
      act="Pull the Network Identifier prefixes, allowlist them, and migrate Key Vault to NSP."),
]

PA = [
 dict(k="pinot-73322-lookup-acl-bypass-no-152",
      due="<b>no fix below the breaking 1.6.0 major</b> &middot; 0.7.0&ndash;1.5.1 affected &middot; no workaround published",
      t=("<b>Apache Pinot's <code>lookup()</code> bypasses broker access control, and the only fix is a breaking "
         "major.</b> With broker ACLs enabled the single-stage engine authorizes <i>only</i> the table in the "
         "<code>FROM</code> clause; <code>lookup()</code> names its dimension table as a <b>string literal</b>, so "
         "that table is never authorized &mdash; and <b>per-principal row-level security filters on it are not "
         "applied either</b>. Any user authorized for one table can read columns from any dimension table in the "
         "cluster and pull arbitrary rows by supplying primary-key values. Affects 0.7.0 through 1.5.1; "
         "<b>there is no 1.5.2</b>, and 1.6.0 (2026-10-29) <b>requires Java 25 to build and run</b>, defaults "
         "Scala to 2.13, removes native text/FST indexes and <code>TEXT_CONTAINS</code>, drops Spark 2 and Presto, "
         "and flips Kafka <code>auto.offset.reset</code> to <code>earliest</code>. So remediation is a migration "
         "project with a JDK rollout on its critical path, not a patch. The multi-stage engine is unaffected; the "
         "advisory offers no interim workaround, so containment is to stop relying on broker ACLs for "
         "dimension-table isolation until you can upgrade.")),
 dict(k="parquet-java-1190-rc9-no-ga-bloom-fix",
      due="<b>no GA release contains the fix</b> &middot; 1.19.0 stuck after nine RCs &middot; 1.18.2 only at DISCUSS",
      t=("<b>Parquet-Java has two pruning-correctness fixes and no released build that carries either.</b> On "
         "<code>parquet-1.18.x</code> but unreleased: <b>#3873 preserves column path components when handling "
         "Bloom filters</b> &mdash; i.e. a bloom filter evaluated against the <i>wrong column</i>, which is wrong "
         "pruning and therefore <b>missing rows</b>, not a crash &mdash; and <b>#3872 fixes dictionary lookup "
         "collisions between dotted field names and nested column paths</b>. Alongside them: #3871 (no flushing "
         "incomplete files after writer failure), #3874 (row-group buffer release) and Jackson 2.22.3 for CVEs. "
         "<b>1.19.0 has had nine release candidates since 2026-09-04 and there was no <code>[VOTE]</code> thread "
         "for it in all of October</b> (its Java 17 minimum is the obvious blocker for downstreams), while 1.18.2 "
         "is still only a <code>[DISCUSS]</code> thread opened 2026-10-26. Current GA on "
         "<code>downloads.apache.org</code> remains <b>1.18.1</b>. This is a silent-correctness exposure with no "
         "patch available and no CVE id, so nothing will tell you about it.")),
 dict(k="n8n-databricks-node-119557-unpatched",
      due="<b>no patched release exists</b> &middot; 2.14.0&ndash;2.46.3 affected &middot; no GHSA, no fix note",
      t=("<b>CVE-2026-119557: n8n's Databricks node concatenates unencoded input into API paths, so a webhook can "
         "read your Databricks secrets using your stored credential.</b> <code>spaceId</code>, "
         "<code>indexName</code> and <code>filePath</code> go straight into paths such as "
         "<code>${host}/api/2.0/genie/spaces/${spaceId}</code>, so <code>../</code> from a webhook, chat or form "
         "input redirects the call to an arbitrary Databricks endpoint while still presenting the stored "
         "credential &mdash; the researcher's PoC lands on <code>/api/2.0/secrets/get</code>. NVD lists "
         "<b>2.14.0 through 2.46.3</b> as affected; 2.46.3 (30 Oct) is the newest 2.x and <b>no release note "
         "mentions the Databricks node or path encoding</b>, there is <b>no GHSA</b>, and the two advisories NVD "
         "cross-references cover the n8n-API and Supabase nodes instead &mdash; so anyone matching by GHSA id will "
         "mis-attribute it. Mitigation is architectural, not a bump: never bind external input to those three "
         "fields, and scope the Databricks credential down. Telling detail: the LangChain "
         "<code>VectorStoreDatabricks</code> node encodes its value correctly &mdash; the "
         "<code>nodes-base</code> Databricks node does not.")),
 dict(k="mongo-node-driver-timeoutms-crossuser-no-6x",
      due="<b>no 6.x backport</b> &middot; both current Mongoose majors pin BELOW the fix &middot; no CVE, no GHSA",
      t=("<b>The MongoDB Node.js driver disclosed cross-user data exposure, and the only fixed version is one no "
         "dependency tree reaches.</b> MongoDB's own wording: versions from v6.11.0 and from v7.0.0 before v7.8.0 "
         "are affected by &ldquo;connection pool desynchronization after operation timeout&rdquo; that <b>can "
         "expose other users' data</b>, with the remediation given as &ldquo;discontinue the use of "
         "<code>timeoutMS</code> as soon as possible&rdquo; &mdash; not merely upgrade. A second issue in the same "
         "release: <b>SRV-returned hostnames were never properly verified from v3.3.3 through 7.8.0</b>, i.e. every "
         "<code>mongodb+srv://</code> connection string for seven years; 7.8.0 adds "
         "<code>srvAllowedHostsSuffix</code> and <code>srvHostValidator</code>. The reachability problem, "
         "measured: the <code>6x</code> dist-tag is still <b>6.21.0, published 2025-11-12</b> &mdash; twelve months "
         "with no security release &mdash; <b>Mongoose 8.24.7 pins <code>mongodb@~6.20.0</code> and even Mongoose "
         "9.11.4 pins <code>~7.7</code></b>, below the fix. Neither current Mongoose line can install 7.8.0 without "
         "an npm <code>overrides</code> entry, and for Mongoose 8.x there is no reachable fix short of a major "
         "migration. <b>No CVE and no GitHub advisory were issued for either issue</b> &mdash; it exists only in "
         "release prose, so every scanner reports clean. One upgrade trap: 7.8.0 makes "
         "<code>timeoutMS</code>/<code>timeoutMode</code> deprecated and <b>inert</b>, so operations that used to "
         "time out silently stop timing out.")),
 dict(k="percona-mysql-84-no-oct-cpu-build",
      due="<b>newest 8.4 build is 8.4.11-11 (2026-08-20)</b> &middot; two upstream minors behind &middot; inside the affected range",
      t=("<b>Percona Server for MySQL 8.4 has no release carrying the October CPU.</b> The newest "
         "<code>Percona-Server-8.4.*</code> tag is <b>8.4.11-11, dated 2026-08-20</b> &mdash; two upstream minors "
         "behind (8.4.12 on 08-18, 8.4.13 on 10-20) and squarely inside the <b>8.4.0&ndash;8.4.12</b> affected "
         "range for <b>CVE-2026-101781</b> (CVSS 8.8, <code>Server: Group Replication GCS</code>, unauthenticated, "
         "adjacent-network). Percona did ship 26.7.0-1 on 2026-10-19 &mdash; <i>the day before</i> the CPU &mdash; "
         "so it is based on 26.7.0, itself inside the affected 26.7.0&ndash;26.7.1 range. Stated honestly: a git "
         "tag is not package GA and Percona may publish within days, so verify against Percona's own release notes "
         "before concluding. But today, on Percona 8.4, <b>there is nothing to upgrade to</b> &mdash; and this is "
         "the inverse of the usual assumption, with the open-source distribution now the slower path for MySQL.")),
 dict(k="kernel-98432-mptcp-uaf-go-default-on",
      due="<b>upgrading Go is NOT the remedy</b> &middot; patched kernel, or GODEBUG=multipathtcp=0",
      t=("<b>A Linux-kernel use-after-free in IPv4 TCP handling reaches Go programs because Go turned MPTCP on by "
         "default.</b> The Go Security Team posted on 2026-10-30 that CVE-2026-98432 matters to Go because <b>Go "
         "has enabled MPTCP by default on listen sockets since Go 1.24</b>, with a publicly described exploit "
         "achieving RCE against MPTCP listeners. <b>The best fix is a patched kernel</b> &mdash; upgrading the "
         "toolchain does not help &mdash; and the Go-side mitigations are <code>GODEBUG=multipathtcp=0</code> at "
         "runtime or <code>godebug multipathtcp=0</code> in the main module's <code>go.mod</code>, both overridden "
         "by a per-socket <code>SetMultipathTCP</code>. The team notes the bug is not MPTCP-specific, so non-MPTCP "
         "systems may be exposed to similar attacks, and calls it premature to change Go's default. "
         "<b>This is the shape to watch: &ldquo;we enabled the better protocol by default&rdquo; moves your blast "
         "radius into code you do not ship.</b>")),
 dict(k="kafka-110952-oauthbearer-iss-aud-unset",
      due="<b>fixable by CONFIG without upgrading</b> &middot; 3.1.0&ndash;4.3.x &middot; and 4.4.0 refuses to start without it",
      t=("<b>Kafka brokers using SASL/OAUTHBEARER with the bundled JWKS validator always verify the JWT signature "
         "but check <code>iss</code> and <code>aud</code> only if you configured them &mdash; and both are unset by "
         "default.</b> CVE-2026-110952, affecting 3.1.0 up to (not including) 4.4.0. Most exposed where one JWKS "
         "endpoint serves multiple issuers &mdash; a multi-tenant IdP, or shared signing keys &mdash; because a "
         "token from another issuer then authenticates, possibly as a higher-privileged principal. <b>The fix is "
         "configuration, not a version:</b> set <code>sasl.oauthbearer.expected.issuer</code> and "
         "<code>sasl.oauthbearer.expected.audience</code> per listener to exact provider values; both options have "
         "existed since 3.1.0, so brokers with both set were never affected and you can remediate without "
         "upgrading. The flip side is an upgrade trap: <b>from 4.4.0 a broker configured with a JWKS endpoint will "
         "not start</b> unless both are set (per-axis opt-outs <code>allow.unverified.issuer</code> / "
         "<code>allow.unverified.audience</code>). Companion in the same disclosure: <b>CVE-2026-111551</b>, where "
         "several Streams and client deserializers read a declared size or count and <b>allocate before checking it "
         "against the bytes present</b> &mdash; <code>max.message.bytes</code> does not help, and because the poison "
         "record stays in the topic <b>the OOM recurs on every restart</b>.")),
 dict(k="valkey-cluster-pubsub-heap-overflow-5-branches",
      due="fixed 2026-10-26 in 9.1.3 / 9.0.7 / 8.1.11 / 8.0.12 / 7.2.15 &middot; authenticated",
      t=("<b>Valkey patched a heap buffer overflow in cluster Pub/Sub message construction across five branches at "
         "once</b> (GHSA-f4q9-j22m-xqq9, 2026-10-26): an <i>authenticated</i> client publishing an oversized "
         "message can crash the server or potentially execute code. Reachable on any clustered deployment where "
         "application credentials can publish &mdash; which is most of them, since Pub/Sub is usually an "
         "application-level capability rather than an admin one. The same releases reject module writes while "
         "writes are paused and fix a <code>RESTORE</code> abort. Five simultaneous back-branch releases is itself "
         "the signal: the maintainers judged every supported line reachable, including 7.2.")),
]

print("=== reuse_key advisory (events, date-keyed) ===")
for row in EV:
    LS.reuse_key(row, led["events"], "date", "events")
print("=== probe_identifiers advisory (patch, identifier-keyed) ===")
probe_rows = EV + PA
rep = X.assert_probed(probe_rows, led["patch"] + led["events"], NOUNS)
print("   probe report:", rep)

for row in EV:
    row.setdefault("first_seen", TODAY); row.setdefault("last_seen", TODAY); row.setdefault("days", 1)
    led["events"].append(row); new_ev.append(row["k"])
for row in PA:
    row.setdefault("first_seen", TODAY); row.setdefault("last_seen", TODAY); row.setdefault("days", 1)
    led["patch"].append(row); new_patch.append(row["k"])

led["_corrections_109"] = corr
json.dump(led, open(os.path.join(SP, "ledger_109.json"), "w"), ensure_ascii=False)

print("\n=== PREP 109 ===")
print("corrections : %d" % len(corr))
for c in corr: print("   -", c)
print("enriched    : %d" % len(enriched))
for e in enriched: print("   -", e)
print("new events  : %d  %s" % (len(new_ev), new_ev))
print("new patch   : %d  %s" % (len(new_patch), new_patch))
print("totals      : events=%d patch=%d" % (len(led["events"]), len(led["patch"])))
