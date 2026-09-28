#!/usr/bin/env python3
"""Edition 077 ledger corrections + new rows.

Applied to the LEDGER, before any section is generated (the 2026-09-14 rule:
correcting the assembled HTML afterwards leaves the rendered table generated
from the pre-fix ledger). Every correction touches the prose, the date/due
field AND the aliases together (the 2026-09-27 rule).
"""
import json, re, sys

def apply(L, TODAY):
    idx = {}
    for bucket, rows in L.items():
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict) and r.get("k"):
                    idx[(bucket, r["k"])] = r
    log = []

    def edit(bucket, key, **kw):
        r = idx.get((bucket, key))
        if r is None:
            raise SystemExit("correction target missing: %s/%s" % (bucket, key))
        for k, v in kw.items():
            r[k] = v
        log.append("%s/%s" % (bucket, key))
        return r

    # 1. NVIDIA PSIRT 2026-10-01 is NOT a cutover and requires no action.
    #    The repo README says PSIRT "will only publish security bulletins on
    #    GitHub", which reads as a channel shutdown. NVIDIA's own Product
    #    Security page carries that sentence PLUS the clause the README omits:
    #    "all bulletins will continue to be available on the Product Security
    #    website... Both this Product Security website and the GitHub repository
    #    will run in parallel." Where the two disagree the fuller vendor page is
    #    authoritative. This RETIRES a tracked deadline rather than moving it.
    edit("events", "nvidia-psirt-stops-publishing-security-bulletins-anywhere-bu",
         t=("<b>CORRECTED (ed. 077) &mdash; this is NOT a cutover and needs no action.</b> "
            "NVIDIA PSIRT begins publishing security bulletins on GitHub (Markdown, CSAF and "
            "CVE Record formats) from this date, but <b>the Product Security website and the "
            "GitHub repository run IN PARALLEL</b> &mdash; NVIDIA's own security page says so "
            "explicitly, and only the repo README's narrower &ldquo;will only publish&rdquo; "
            "wording suggested a shutdown. If you scrape <code>nvidia.custhelp.com</code> or "
            "subscribe by email, nothing breaks on 1 Oct. The GitHub route is still the better "
            "one for automation (CSAF + CVE Record JSON + SHA256 per file) &mdash; that is a "
            "preference, not a deadline. Retire any calendar entry saying the old channel dies."),
         url="https://www.nvidia.com/en-us/security/")

    # 2. CVE-2026-21962: the row disagreed with ITSELF -- `due` said 31d PAST DUE
    #    while the prose said 29. Both are now 32, and the reason no patch
    #    cadence will ever deliver it is stated.
    edit("patch", "cve-2026-21962-ohs-weblogic-kev",
         due="2026-08-27 (32d PAST DUE)",
         t=("CVE-2026-21962 &mdash; Oracle HTTP Server 12.2.1.4.0 / WebLogic Server Proxy "
            "Plug-in 14.1.1.0.0 &amp; 14.1.2.0.0, CVSS 10.0, unauthenticated, scope-changing, "
            "CISA KEV with <code>forensicTriage: Yes</code> under BOD 26-04 &mdash; a "
            "compromise assessment, not just a patch. <b>Deadline 2026-08-27 is now 32 days "
            "past.</b> Re-confirmed 09-28: the fix has existed since the <b>January 2026 CPU</b> "
            "and <b>no CSPU will ever carry it</b>, because CSPUs contain no Fusion Middleware "
            "web-tier content &mdash; anyone waiting on the patch cadence is waiting "
            "indefinitely. Not a Database CVE; it matters to a database audience because "
            "OHS plus the WebLogic proxy plug-in is the canonical front end for APEX and ORDS. "
            "(ed. 077 fixed an internal disagreement: <code>due</code> read 31d while the prose "
            "read 29d.)"),
         url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog")

    # 3. JFrog: correct the ACTION. "Rotate the Access token-signing key" is not
    #    in any of JFrog's four advisories -- today's App Dev lane read all of
    #    them. What IS documented is substantively equivalent and is what the
    #    row should say: an upgrade does not revoke admin tokens already minted.
    edit("patch", "jfrog-42018-42016-kev-due-sep25",
         due="2026-09-25 (3d PAST DUE)",
         t=("CVE-2026-42018 chained with CVE-2026-42016 &mdash; <b>KEV due 2026-09-25, now 3 "
            "days past</b>, and all four JFrog Artifactory KEV entries are now expired "
            "(82329 due 09-05, 66384 due 09-10, 42016 and 42018 due 09-25), every one carrying "
            "BOD 26-04 forensic-triage obligations. Wiz observed the chain in the wild between "
            "15 Aug and 8 Sep: <code>POST /access/api/v1/aws/token/</code> <b>with a trailing "
            "slash</b> returns an anonymous JWT even when anonymous access is off, then "
            "<code>POST /access/api/v1/tokens</code> escalates it to an admin-scoped token; "
            "follow-on activity included persistent admin accounts, malicious Groovy plugins "
            "and Rust backdoors. <b>CORRECTED (ed. 077):</b> the board previously said the "
            "Access <i>token-signing key</i> must be rotated. That wording is in none of "
            "JFrog's four advisories. The documented and substantively equivalent point is "
            "that <b>an upgrade does not revoke admin tokens minted beforehand</b> &mdash; they "
            "keep working until they expire or you revoke them. Revoke tokens and hunt for "
            "persistence; patching alone leaves the attacker resident."),
         url="https://www.wiz.io/blog/artifactory-under-attack-in-the-wild-exploitation-of-cve-2026-42016-cve-2026-4201")

    # 4. Doris: ed. 076 recorded the 4.1.x fix as "superseded by hotfix 4.1.4.1,
    #    not withdrawn". Today's measurement is sharper and worse.
    edit("patch", "doris-cve-2026-72524-no-fix-on-2x-3x",
         due="no fix on 2.x/3.x · download page still serves vulnerable 4.1.3 as “Latest”",
         t=("<b>Apache Doris: the download page still serves the VULNERABLE build as "
            "&ldquo;Latest&rdquo;, verified 2026-09-28, with no advisory banner.</b> It offers "
            "4.1.3 (Latest) and 4.0.8 (Stable); 4.1.3 is affected by all four September CVEs, "
            "including <b>CVE-2026-31377</b> (CVSS 7.5, <code>AV:N/AC:L/PR:N</code> &mdash; "
            "<b>unauthenticated</b> access to FE meta-service endpoints that trusted "
            "client-supplied node information) and <b>CVE-2026-96443</b> (FE remote code "
            "execution via an unvalidated JDBC driver URL), plus CVE-2026-68570 and "
            "CVE-2026-72524 (authz bypasses, the latter allowing drop). <b>4.1.4 &mdash; the "
            "only build the project's own CVE records show clean of all four &mdash; is absent "
            "from that page</b> and exists on <code>downloads.apache.org</code> as source only. "
            "The PMC-recommended replacement <b>4.1.4.1 has NOT released</b>: its vote opened "
            "2026-09-26 06:37 UTC with three binding +1s and cannot close before 2026-09-29 "
            "06:37 UTC. <b>Sharpest finding:</b> CVE-2026-96443's structured record declares a "
            "single affected range <code>2.0.5 ≤ v ≤ 4.1.3</code> with <b>no unaffected "
            "entries and no remediation sentence</b> &mdash; read literally that places 4.0.8, "
            "the page's own &ldquo;Stable&rdquo;, inside the affected range for an FE RCE with "
            "no fixed release named anywhere. The intent is almost certainly &ldquo;fixed in "
            "4.0.8 and 4.1.4&rdquo; by analogy with the other three; the project has not said "
            "so. 3.1/3.0/2.x are unmaintained and CVE-2026-72524 will never be fixed there."),
         url="https://doris.apache.org/download")

    # 5. MongoDB 82067: the Percona half was resolved in ed. 074 but THIS row
    #    still said "no build carrying the fix" -- prose and data corrected
    #    separately, the 09-16 trap.
    edit("patch", "mongodb-cve-82067-auth-disabled",
         due="2026-09-17 · Percona RESOLVED 09-22/23/28",
         t=("CVE-2026-82067 (CVSS 4.0 <b>9.2</b> / 3.1 8.1) &mdash; improper handling of case "
            "sensitivity in configuration validation can leave <b>the authorization subsystem "
            "in a default DISABLED state at server startup</b>, i.e. unauthenticated full admin "
            "access. Fixed upstream 2026-09-08 in 8.3.9 / 8.0.30 / 7.0.41. <b>UPDATED (ed. "
            "077): Percona has now caught up on every line</b> &mdash; Percona Server for "
            "MongoDB 7.0.43-23 (22 Sep), 8.0.32-14 (23 Sep) and <b>8.3.11-3 (28 Sep, today)</b> "
            "each ship this as their sole Critical, closing measured exposure windows of 14, 15 "
            "and 20 days. Note 8.3.11-3 is still labelled <i>technical preview</i> by Percona "
            "while being the only 8.3-line build carrying the fix. <b>MongoDB 8.2 remains "
            "stranded</b>: EOL 31 July 2026, last build 8.2.12, and it received none of the "
            "September batch. Distinct from CVE-2026-18691 (the 11 Aug intra-cluster SASL "
            "downgrade) &mdash; different bug, different date, different fix versions; the "
            "board tracks them as separate rows and that separation is correct."),
         url="https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-82067")

    # 6. Aurora PostgreSQL: the lag is now measured against three peers.
    edit("patch", "pg-28-cves-aug13",
         due="2026-08-13 · Aurora 46d behind, 1 of 28 backported",
         t=("PostgreSQL's 2026-08-13 release is the project's largest security drop: 28 CVEs "
            "across 18.6 / 17.11 / 16.15 / 15.19 / 14.24, seventeen of them CVSS ≥ 8.0. "
            "<b>UPDATED (ed. 077) &mdash; the managed-engine spread is the story and it is now "
            "measured: Neon shipped it in 8 days, RDS in 12, Azure within the month, Supabase "
            "in 43 &mdash; and Aurora PostgreSQL has shipped NO engine containing the batch at "
            "46 days, having backported exactly ONE of the 28</b> (CVE-2026-14671, refint "
            "plan-cache type confusion, 8.8). Aurora's newest engines are 18.4.2 / 17.10.2 / "
            "16.14.2 / 15.18.2 (2026-09-14) and their community bases are still the MAY minors. "
            "Not backported: the <code>pg_dump</code> heap overflow (CVE-2026-19385, 8.8), SQL "
            "injection via <code>EXTRACT</code> deparse (CVE-2026-15741, 8.8), and logical "
            "decoding <code>dlopen</code> of an arbitrary file. Same upstream tarball, five "
            "very different exposure windows. Compensating controls, not a minor-version wait."),
         url="https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Updates.html")

    # 7. postgres-mcp: still unfixed, and the clock is now quantified.
    edit("patch", "postgres-mcp-85620-unpatched-9-2",
         due="no fix · PR open 6 weeks",
         t=("CVE-2026-85620, CVSS 4.0 <b>9.2</b>, <code>PR:N</code>, <b>NO FIXED RELEASE</b>. "
            "<code>crystaldba/postgres-mcp</code>'s restricted-mode allowlist validates function "
            "names on <code>FuncCall</code> AST nodes but not <code>RangeFunction</code> nodes, "
            "so <code>SELECT pg_read_file('/etc/passwd')</code> is blocked while "
            "<code>SELECT * FROM pg_read_file('/etc/passwd')</code> executes. <b>UPDATED (ed. "
            "077): still unfixed six weeks on.</b> The CVE published 2026-09-04; <b>PR #200 has "
            "been open since 2026-08-16</b>, last activity 09-23, and the newest release remains "
            "v0.3.0 from May 2025. A commenter confirmed on 09-23 that both <code>main</code> "
            "and the current PyPI build are still exploitable, and that the bypass reaches DoS "
            "functions and, where extensions permit, arbitrary DDL/DML &mdash; not only file "
            "reads. Stop running it against production. Worth stating plainly: this window's "
            "single worst unfixed vulnerability in the data layer is itself in a Postgres MCP "
            "server."),
         url="https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-85620")


    # 8-10. Enrich the three 09-30/10-01 rows reuse_key's advisory showed were
    #       already on the board -- the 09-11 mechanism working as designed:
    #       make the duplicate visible at build time, then enrich in place.
    edit("events", "snowflake-bcr-2437-native-app-approle-oct1",
         t=("<b>Snowflake BCR-2437 &mdash; every installed Native App inherits "
            "<code>SNOWFLAKE.APP_PUBLIC</code>, and the consumer cannot revoke it.</b> "
            "Re-confirmed 09-28 with the counts: <b>5 account privileges</b> (BIND SERVICE "
            "ENDPOINT, EXECUTE AGENT TASK, MANAGE ARTIFACT PUBLICATION, USE AI FUNCTIONS, VIEW "
            "LINEAGE), <b>13 database roles</b> (including CORTEX_USER, ML_USER, "
            "DATA_METRIC_USER, PYPI_REPOSITORY_USER) and <b>9 application roles</b> (including "
            "APP_DEVELOPER, CORTEX-MODEL-ROLE-ALL) &mdash; &ldquo;with no request in the "
            "manifest and no grant from the consumer&rdquo;. Snowflake's own wording: "
            "&ldquo;consumers can't revoke it or the capabilities granted through it.&rdquo; "
            "Rollout may vary by account. This is the sharpest instance of the window's "
            "dominant pattern &mdash; defaults moving to <i>on, billable and not revocable</i>."),
         act=("Run <code>SHOW APPLICATIONS</code> and <code>SHOW GRANTS TO APPLICATION ROLE "
              "SNOWFLAKE.APP_PUBLIC</code>, read the three capability tables in BCR-2437, and "
              "uninstall any app whose expanded access is unacceptable &mdash; uninstall is the "
              "only control, and it stops working once the change lands."),
         url="https://docs.snowflake.com/en/release-notes/bcr-bundles/un-bundled/bcr-2437")

    edit("events", "gha-90day-retention-oct1",
         t=("<b>GitHub Actions retention begins governing checks, workflow runs and statuses "
            "&mdash; default 90 days, down from 400+, and explicitly NOT retroactive.</b> "
            "Re-confirmed 09-28 with GitHub's own sentence: &ldquo;Adjusting your retention "
            "setting will not restore data that was previously evicted.&rdquo; There is no "
            "export button and no undo, so this is silent permanent loss of CI history for "
            "anyone relying on it for SOC 2 or change-management evidence, release provenance "
            "or flaky-test archaeology. Distinct from the separate 2026-09-24 change, which "
            "only stops <i>expired</i> artifacts appearing in the UI and API and affects "
            "neither retention nor billing &mdash; the two are easy to conflate."),
         act=("Raise the repo/org/enterprise retention setting before Wednesday, or export "
              "first: <code>gh api</code> over <code>/repos/{o}/{r}/actions/runs</code> and "
              "<code>/commits/{sha}/check-runs</code> is the practical route."),
         url="https://github.blog/changelog/2026-08-27-actions-retention-will-cover-checks-workflow-runs-and-statuses/")

    edit("events", "aks-begins-auto-migrating-vmas-clusters-to-vms-pick-your-own",
         t=("<b>AKS begins auto-migrating Availability-Set (VMAS) clusters to Virtual Machines "
            "node pools.</b> Re-confirmed 09-28 with the mechanism, which is the part that "
            "surprises people: it is delivered <i>through the auto-upgrader</i>, so it fires "
            "inside your <code>aksManagedAutoUpgradeSchedule</code> maintenance window whether "
            "or not you opted in. Node pools are recreated either way. (Also corrected: the "
            "board previously carried a separate &ldquo;AKS automatic upgrade window "
            "selection&rdquo; thread; no such change exists &mdash; this VMAS migration, "
            "delivered via the auto-upgrader, is what that description was reaching for.)"),
         act=("Run <code>az aks update --migrate-vmas-to-vms</code> yourself first if you want "
              "to choose the moment rather than have one chosen."),
         url="https://github.com/Azure/AKS/releases/tag/2026-09-04")

    return log
