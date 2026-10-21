#!/usr/bin/env python3
"""Edition 099 ledger pass: corrections FIRST, then new rows, then merge.

Build order is the 2026-09-14 rule: a correction must reach the LEDGER before
any section is generated, or the rendered table is produced from the pre-fix
data and the page contradicts its own embedded ledger.
"""
import json, os, sys, re

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import lens_guard as G
import ledger_surgery as S

TODAY, ED = "2026-10-21", 99
parent = json.load(open(os.path.join(SP, "parent_ledger.json")))
pk = {sec: {r["k"]: r for r in parent.get(sec, []) if isinstance(r, dict)}
      for sec in parent if isinstance(parent[sec], list)}

ledger = {"date": TODAY, "edition": ED}
touched = []


def correct(sec, key, **fields):
    """Copy a parent row forward with fields replaced. Fails loudly on a typo."""
    if key not in pk.get(sec, {}):
        raise SystemExit("correct(): %s/%s is not a parent row" % (sec, key))
    row = dict(pk[sec][key])
    row.update(fields)
    ledger.setdefault(sec, []).append(row)
    touched.append("%s/%s" % (sec, key))
    return row


# ---------------------------------------------------------------------------
# CORRECTIONS (8). Each one was probed against the board first.
# ---------------------------------------------------------------------------

# 1. THE DATE CORRECTION. The board carried a day-precise 2026-11-18 for the
#    Cortex-models RBAC retirement. Today's Snowflake lane read BCR-2378 and the
#    unbundled table: NEITHER carries 2026-11-18. The published rollout is
#    month-only -- "Aug 5, 2026 ... rollout completes January 2027". Same class
#    as the Iceberg V4 (09-12) and Fabric Runtime 2.0 (10-21 below) fabrications:
#    a day we invented defeats every date-keyed check downstream.
correct("events", "snowflake-cortex-models-allowlist-rbac-nov18",
        date=None,   # board convention for undated (7 of 8 parent undated rows use None)
        t=("CORRECTED 10-21 &mdash; the day-precise 2026-11-18 this board carried since edition 094 "
           "appears on NO Snowflake page and is withdrawn. BCR-2378 (CORTEX_MODELS_ALLOWLIST "
           "deprecation + embedding-model RBAC) is dated <b>Aug 5, 2026</b> on the unbundled table "
           "with &ldquo;rollout completes January 2027&rdquo; &mdash; month precision only, so this row is now "
           "UNDATED. It is one story, not two: the allowlist change and the &ldquo;RBAC retirement&rdquo; are the "
           "same BCR. It is also a member of bundle 2026_07, which went Enabled-by-Default on "
           "2026-10-16, so for opt-out-capable accounts the behaviour is ALREADY live. Operator path: "
           "<code>SHOW PARAMETERS LIKE 'CORTEX_MODELS_ALLOWLIST' IN ACCOUNT</code>; if not None, grant "
           "per-model application roles, then set it to 'None'. A raw REVOKE does not remove "
           "CORTEX-MODEL-ROLE-ALL from PUBLIC &mdash; only "
           "<code>SNOWFLAKE.LOCAL.REVOKE_FROM_PUBLIC_APPLICATION_ROLE</code> does."))

# 2. Oracle's October CPU published ~24h after it was due, so yesterday's
#    "advisory does not exist publicly yet" row gets its numbers.
correct("events", "oracle-cpu-oct-2026",
        t=("PUBLISHED &mdash; Rev 1, 2026-10-20, read at 13:25 UTC today (617 KB, 1,739 CVE-id mentions). "
           "<b>1,295 new security patches</b>; 70 rows score 9.8 or higher; the single highest is CVSS "
           "<b>10.0</b> in Oracle Workflow Notification Mailer (E-Business Suite, CVE-2026-101809, remote "
           "+ unauthenticated) &mdash; <i>not</i> a database component. Yesterday's reading of the pre-release "
           "page said Database Server would take 13 patches at max 8.8; the published advisory says "
           "<b>14 patches, max 9.8</b>. Next Oracle security dates: 17 Nov 2026 (CSPU), 15 Dec (CSPU), "
           "19 Jan 2027 (CPU), 16 Feb (CSPU) &mdash; and in CPU months the quarterly CPU is the sole vehicle."))

# 3. Node.js shipped on schedule -- the only one of the three patch events that did.
correct("events", "nodejs-security-releases-oct21",
        t=("SHIPPED today at <b>10:38Z</b> (tags v26.12.1, v24.22.1 'Krypton' LTS, v22.23.4 'Jod' LTS). "
           "<b>10 CVEs, 4 High.</b> The one that matters: <b>CVE-2026-111497</b>, an out-of-bounds write in "
           "the Brotli decoder that Node describes as <i>permitting remote code execution</i> &mdash; reachable "
           "by anything that decompresses <code>Content-Encoding: br</code>. Two more High are TLS hostname "
           "bypasses (fullwidth-digit IPs; hosts that loosely resolve to an IP), so clients that verified "
           "correctly may now fail and clients that should have failed were passing. Also ships the "
           "eMudhra CA distrust (NSS 3.131.1 roots; TLS now rejects chains with blocked public keys). "
           "<b>Node 20 and earlier are EOL and get no fix.</b>"))

# 4. The APEX row's own prediction came true in the worst way: the advisory
#    published, the CVE ids are readable, and the FIXED VERSION still is not.
correct("patch", "oracle-apex-two-98-unauth-oct-cpu",
        due="2026-10-20 &middot; CVE ids now readable &middot; FIXED VERSION STILL NOT PUBLISHED",
        t=("UPDATED 10-21 &mdash; the advisory published and the ids are now readable: <b>CVE-2026-101521</b>, "
           "CVSS <b>9.8</b>, remote and unauthenticated over HTTPS, C/I/A all High, affecting APEX "
           "<b>24.1.0&ndash;24.1.21, 24.2.0&ndash;24.2.20 and 26.1.0&ndash;26.1.4</b>; plus CVE-2026-66010 (DOMPurify, "
           "6.1, unauthenticated, user interaction required). <b>The remediation is still unreadable.</b> "
           "Oracle's risk matrix lists affected ranges only and names no fixed version, and "
           "apex.oracle.com returned 403 to every attempt, so the patch-set note cannot be read. The "
           "implied fixed builds are 24.1.22 / 24.2.21 / 26.1.5 &mdash; that is inference, NOT confirmed. "
           "A 9.8 you can identify and cannot patch is worse than one you have not heard of."))

# 5. The forward-looking CPU row was carrying JULY's figures as its expectation.
correct("patch", "oracle-cpu-oct-20-next",
        due="2026-10-20 &mdash; LANDED",
        t=("October actuals, replacing the carried July expectation (which read 1,449 patches / 15 for "
           "Database Server / max 9.9). <b>Database Server: 14 patches</b>, 4 remote-unauthenticated, 2 "
           "reaching client-only installs; max is <b>CVSS 9.8 CVE-2026-75803</b>, a bundled <b>OpenSSL</b> "
           "flaw in 19.3&ndash;19.32 and 23.4.0&ndash;23.26.3. Then CVE-2026-91563 (OLAP DBMS_AW, 8.8, 19c/21c/26ai) "
           "and CVE-2026-91499 (<b>DBMS_VECTOR</b>, 8.8, 23ai/26ai only &mdash; the vector surface is now its own "
           "attack surface). <b>MySQL: 98 patches</b>, 29 remote-unauthenticated, fixed in 8.4.13 / 9.7.4; "
           "both 9.8s are third-party too (curl CVE-2026-9547, OpenSSL CVE-2025-15467). ORDS takes 35, "
           "GoldenGate 11. <b>The pattern worth acting on: the top of this CPU is bundled third-party "
           "code, so a scanner that reports only Oracle first-party CVEs misses the worst rows.</b>"))

# 6. 54 -> 55 days, and the one new fact: the published CPU does not mention it.
correct("patch", "cve-2026-21962-ohs-weblogic-kev",
        due="KEV due 2026-08-27 (<b>55d PAST DUE</b>) &middot; fix exists since the January 2026 CPU",
        t=("RE-MEASURED 10-21. <b>55 days past its KEV due date</b>, and now confirmed rather than "
           "assumed: a grep of the <i>published</i> October CPU finds <b>zero</b> mentions of "
           "CVE-2026-21962. The October CPU does not retire it. CISA KEV (fetched today) attributes it "
           "to <b>Oracle HTTP Server and the WebLogic Server Proxy Plug-in</b> (12.2.1.4.0, 14.1.1.0.0, "
           "14.1.2.0.0) &mdash; not the database, which is how it keeps getting mis-shelved by teams who "
           "check their DB patch level and move on. Added 2026-08-24, due 08-27, ransomware use "
           "&ldquo;Unknown&rdquo;. The fix has existed since January. This is unpatched by <i>omission</i>, which is "
           "worse rhetorically than unpatched by absence, not better."))

# 7. pgvector: the row existed; today it gets the measured provider matrix.
correct("patch", "pgvector-103484-ivfflat-oob-no-managed-fix",
        due="<b>no reachable fix</b> on any managed Postgres &mdash; 0.8.7 shipped 2026-10-01, nobody ships it",
        t=("RE-MEASURED 10-21 and the gap is now exact. <b>pgvector 0.8.7 shipped 2026-10-01</b> and fixes "
           "CVE-2026-103484 / GHSA-pw7q-9788-x566, an out-of-bounds write during IVFFlat index build that "
           "can lead to code execution (any user who can <code>CREATE INDEX</code> on a table they own). "
           "Measured versions today: <b>RDS, Aurora and Azure Flexible Server 0.8.2; Cloud SQL 0.8.5; "
           "AlloyDB 0.8.2.google-1; Neon 0.8.0 on PG14&ndash;17, 0.8.6 on PG18</b>. <b>Nobody is on 0.8.7.</b> "
           "0.8.2 is doubly stale &mdash; it also predates the 0.8.3 HNSW vacuum-corruption fix. Self-managed: "
           "install 0.8.7 then <code>ALTER EXTENSION vector UPDATE</code> (the extension does not move with "
           "the engine). Managed: restrict who may CREATE INDEX and ask for a date. Not in KEV, no "
           "exploitation reported &mdash; this is mechanism 3 of the no-reachable-fix register "
           "(managed-extension pinning), measured rather than asserted."))

# 8. postgres-mcp: still open, and the clock is worth stating.
correct("patch", "postgres-mcp-85620-unpatched-9-2",
        due="no fix &middot; PR #200 open <b>9 weeks</b>",
        t=("RE-MEASURED 10-21: still no published advisory on the repo (&ldquo;There aren't any published "
           "security advisories&rdquo;) and <b>PR #200 &mdash; &lsquo;Block dangerous functions in FROM clause "
           "(RangeFunction allowlist bypass)&rsquo; &mdash; has been open since 2026-08-16</b>, now nine weeks. PR "
           "#193 (default to RESTRICTED) has been open since 07-30. No release carries a fix, so merged-"
           "in-git would not help even if it merged. Worth stating plainly: this window's single worst "
           "unfixed vulnerability sits in a <i>Postgres MCP server</i> &mdash; the agent surface, not the engine."))

json.dump({"ledger": ledger, "touched": touched}, open(os.path.join(SP, "corrections_099.json"), "w"))
print("corrections applied: %d" % len(touched))
for t in touched:
    print("   " + t)


# ---------------------------------------------------------------------------
# ENRICHMENTS (6) -- rows the board already had, re-measured today. Probing the
# key list first turned up an existing key for EVERY candidate except one, which
# is the 2026-09-09 finding holding for a twelfth consecutive edition.
# ---------------------------------------------------------------------------
correct("patch", "react-rsc-95-unauth-rce-no-cve",
        due="fixed 19.0.9 / 19.1.10 / 19.2.9 / 19.3.1 &middot; <b>no workaround</b>",
        t=("RE-MEASURED 10-21, now 7 days old and still absent from OSV. GHSA-xqc2-xf4c-x3h3, Critical "
           "<b>9.5 (CVSS 4.0)</b>, <b>no CVE id</b> &mdash; which is the reason it is invisible: a scanner keyed on "
           "CVE ids has nothing to key on. Affects react-server-dom-parcel / -turbopack / -webpack at "
           "19.0.0&ndash;19.0.8, 19.1.0&ndash;19.1.9, 19.2.0&ndash;19.2.8 and 19.3.0. <b>The advisory states there is no "
           "workaround.</b> Apps with no server or no RSC-capable bundler are unaffected. "
           "<code>react-server-dom-webpack@19.1.0</code> returns 7 OSV vulns, newest published 2026-07-24 &mdash; "
           "so this RCE is simply not in the answer."))

correct("patch", "nextjs-oct14-two-95-rces-no-13x-14x-fix",
        due="fixed 15.5.28 / 16.4.1 &middot; <b>no fix listed for 13.x or 14.x</b>",
        t=("RE-MEASURED 10-21 from the advisory itself. <b>CVE-2026-96889</b> / GHSA-2464-fhr4-w9xw, "
           "Critical <b>9.5</b>: RCE through the Image Optimization API with SVG, affecting 10.0.0 through "
           "<b>15.5.27</b> and 16.0.1 through 16.4.0, fixed in <b>15.5.28 and 16.4.1</b>. The sibling "
           "GHSA-673q-mjm6-r5xr is a second Critical RCE via <code>use cache</code> returning typed arrays. "
           "The advisory lists no patch for 13.x or 14.x and says nothing about one coming; the only "
           "mitigation is <code>sharp</code> &ge; 0.35.5. <b>And the inversion is exact: "
           "<code>next@15.5.27</code> &mdash; the last version this CVE affects &mdash; returns ZERO vulns from OSV, "
           "while <code>next@14.2.35</code> returns 23.</b>"))

correct("patch", "storybook-94-dev-server-story-rewrite",
        due="patched 10.6.2 / 9.1.21 / 8.6.19 (2026-10-12) &middot; newest OSV entry is Feb 2026",
        t=("RE-MEASURED 10-21: two advisories published 10-12 &mdash; GHSA-f2ph-cmg5-wxc8, <b>Critical</b>, code "
           "injection into a running dev server reachable <b>from any website the developer visits</b>, and "
           "GHSA-px85-f4q5-jh77, High, from the local network. Fixed in 10.6.2, 9.1.21 and 8.6.19. "
           "<b>Neither is in OSV</b> &mdash; Storybook's newest OSV entry is from February 2026. The practical "
           "rule this produces: keep dev servers off shared networks, because the attack needs only a "
           "browser tab and your scanner will not mention it."))

correct("patch", "pgbouncer-scram-nonce-preauth-crash-19888",
        due="fixed 1.26.1 (2026-10-14) &middot; six CVEs in three weeks",
        t=("RE-MEASURED 10-21 and the row is now a pattern, not an incident. <b>1.26.1 (2026-10-14)</b> fixes "
           "<b>CVE-2026-107350</b>: a second StartupMessage sent during SCRAM authentication to a "
           "non-existent database lets someone who knows <i>one</i> auth_file user's password log in as "
           "<b>other SCRAM users, including admins and backend superusers</b>. Also CVE-2026-107349 (CPU spin) "
           "and CVE-2026-107348 (hang at max_packet_size &ge; 2147483649), plus the restored "
           "<code>search_path</code> in ignore_startup_parameters that 1.26.0 regressed. With 1.26.0's "
           "CVE-2026-19888 / -6668 / -6669 that is <b>six CVEs across two releases three weeks apart, three "
           "of them in SCRAM handling</b>. 1.26.0 also REMOVED online restart (<code>-R</code>, SHOW FDS, "
           "SUSPEND) &mdash; use rolling restarts with so_reuseport. <b>Patch the pooler on the same schedule as "
           "the database: it is an auth boundary.</b>"))

correct("patch", "argocd-four-99-criticals-no-v2-fix",
        due="no v2 fix, ever &middot; fixed v3 3.3.15 / 3.4.10 / 3.5.4 / 3.6.0-rc2",
        t=("RE-MEASURED 10-21: unchanged, and the v2 wall is confirmed from the advisories. "
           "<b>CVE-2026-113709</b> (GHSA-fw5c-w8rc-j7fx, <b>9.9</b>) runs commands in repo-server via the "
           "Kustomize Helm config home; the v2 module is affected from 2.1.0 with <b>no patched v2 "
           "release</b>. CVE-2026-77459 (AppProject restrictions bypassed by PreDelete/PostDelete hooks) "
           "and CVE-2026-55797 (High, repo-server command injection via a crafted SSH SOCKS5 proxy URL) "
           "are likewise v2-unfixed. Removing <code>--enable-helm</code> from kustomize.buildOptions is "
           "complete but breaks Helm-through-Kustomize; blocking the upload API closes only one path, "
           "because a committed kustomization still runs on the next sync. Newer points exist "
           "(3.5.6, 3.4.12, 3.3.17) &mdash; take the newest in your minor. <b>For v2 the remedy is a major "
           "migration, not a patch.</b>"))

correct("patch", "starrocks-cve-trio-4014",
        due="merged on branch-3.5, <b>UNRELEASED</b> &middot; reachable only via 4.0.16 / 4.1.6",
        t=("RE-MEASURED 10-21 by diffing poms, which is the only check that sees this. Released tag "
           "<b>3.5.21</b> (2026-08-28, newest on the branch) declares Apache Ranger <b>2.8.0</b>, Bouncy "
           "Castle <b>1.84</b> and httpclient5 <b>5.4.3</b>; <code>branch-3.5</code> HEAD already declares "
           "<b>2.9.0 / 1.86 / 5.6.4</b>. So the fixes for CVE-2026-42537 (Ranger RCE via JDBC URL "
           "injection, 9.8, unauthenticated) and CVE-2026-71290 (httpclient5 TLS hostname verification "
           "silently disabled in the default config, 9.1) are <b>merged and unreleased</b>, with no 3.5.22 "
           "in the feed. <b>4.0.16 and 4.1.6 (both 2026-09-30) DO carry them</b> &mdash; a major-line move. This "
           "is mechanism 6 of the register, and it defeats both halves of a normal process: a reviewer "
           "reading the branch concludes &ldquo;fixed&rdquo;, a scanner reading the released artifact's pom finds "
           "the vulnerable versions, and <b>no advisory names StarRocks at all</b>."))


# ---------------------------------------------------------------------------
# GENUINELY NEW (1). Probing the key list for ca-/x509/emudhra/111943 returned
# nothing, so this is the one story today that the board did not already carry.
# ---------------------------------------------------------------------------
new_patch = [{
    "k": "ca-distrust-go-node-emudhra-oct19-21",
    "due": "Go URGENT track &middot; rebuild required, redeploy is not enough",
    "t": ("A certificate-authority compromise landed in <b>two language runtimes within two days</b>, and "
          "the two disagree about naming it. <b>Go 1.27.3 / 1.26.10</b> (announced 2026-10-20, go.dev dates "
          "them 10-19) carry a single security fix, <b>CVE-2026-111943</b> / GO-2026-6809: a "
          "<code>crypto/x509</code> denylist makes <code>Verify</code> error or filter out chains "
          "containing known-compromised intermediates, for platforms whose system trust store is not "
          "updated. Go ran it on the <b>URGENT</b> track and says &ldquo;highly recommend immediately "
          "upgrading&rdquo;, but <b>names no CA</b>. <b>Node's 2026-10-21 release names it outright</b> &mdash; an "
          "&ldquo;eMudhra Intermediate CA compromise&rdquo; &mdash; and ships NSS 3.131.1 roots plus TLS rejection of "
          "chains with blocked public keys. The attribution is only available by reading both vendors. "
          "<b>Two operational consequences:</b> statically linked Go services need a <i>rebuild</i>, not a "
          "restart, and verification that previously succeeded will now fail, so private-CA and "
          "pinned-chain integration tests are where this surfaces. Expect Python, Java and OS trust "
          "stores next."),
    "url": "https://groups.google.com/g/golang-announce/c/66pojueaQek",
}]
for r in new_patch:
    S.reuse_key(r, parent.get("patch", []), "due", "similarity")
    ledger.setdefault("patch", []).append(r)

print("\nenrichments + new rows: ledger now holds %s"
      % {k: len(v) for k, v in ledger.items() if isinstance(v, list)})
json.dump(ledger, open(os.path.join(SP, "ledger_099_pre_merge.json"), "w"), indent=0)
