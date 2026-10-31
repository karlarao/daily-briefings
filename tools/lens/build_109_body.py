# -*- coding: utf-8 -*-
"""Edition 109 authored sections. Imported by build_109.py after facts exist."""

def build(ctx):
    G, X, L, ET, PR, LG = ctx["G"], ctx["X"], ctx["L"], ctx["ET"], ctx["PR"], ctx["LG"]
    C, li = ctx["C"], ctx["li"]
    TODAY, ED, PAR_ED = ctx["TODAY"], ctx["ED"], ctx["PAR_ED"]
    ef, shown, nofix, led = ctx["ef"], ctx["shown"], ctx["nofix"], ctx["led"]
    series, ls, run8 = ctx["series"], ctx["ls"], ctx["run8"]
    new_ev_k, new_pa_k, ret = ctx["new_ev_k"], ctx["new_pa_k"], ctx["ret"]
    ev_html = ctx["ev_html"]
    NAV = {}
    cur = series[-1]

    # ------------------------------------------------------------ Today's Read
    lede = (
      "<p class='lede'>Today's board has one organising fact: <b>a single certificate authority failed, and the "
      "remediation arrived as a separate release in every runtime you own.</b> Eight eMudhra/emSign intermediate "
      "CA private keys turned out to be <i>guessable</i> rather than stolen &mdash; all eight with "
      "<code>d &lt; 256</code>, one elliptic-curve key with <b><code>d = 4</code></b> &mdash; and because each "
      "runtime compiles or vendors its own trust store, the fix landed independently in Go, Python, Node, pip, "
      "uv, certifi, Flutter, Firebase, Oracle's database and the gcloud CLI. Two of those are worse than an "
      "upgrade: <b><code>pip</code> always merges its vendored certifi with the system store, so distrusting the "
      "root at OS level does not protect a Python app</b> &mdash; you must upgrade pip <i>inside every "
      "virtualenv</i> &mdash; and on mobile the CA bundle is compiled into the binary, so shipped Flutter and "
      "Firebase apps stay exposed until you rebuild and reship. "
      "Around that sits the densest end-of-support fortnight this board has carried: <b>" + str(ef["inside14"]) +
      " dated rows inside fourteen days, " + str(ef["inside7"]) + " inside seven, and " + str(ef["today_rows"]) +
      " landing today</b>. Four KEV clocks are live &mdash; the Linux kernel <b>today</b>, GitLab at CVSS 10.0 "
      "<b>tomorrow</b> with a Metasploit PR open, Brotli on <b>10 Nov</b> &mdash; and the two most serious new "
      "flaws are both patched in a branch nobody has tagged: a <b>pre-boot</b> RCE in the EDK II PXE driver that "
      "executes before Secure Boot measures anything, and an unauthenticated ClickHouse RCE that exists on no "
      "branch at or below 26.7. <b>The no-fix register stands at " + str(nofix) + ".</b></p>")

    def spend(rows):
        return "<h3>Where to spend today's attention</h3><ul>" + "".join(rows) + "</ul>"

    read = {}
    read["oracle"] = lede + (
      "<p>For an Oracle performance engineer the sharpest item is not in the database: it is <b>Oracle's patch "
      "cadence failing its own quarterly model, twice in eleven days.</b> Three out-of-band Security Alerts "
      "landed after the 20 Oct CPU and <b>a direct grep confirms none of their CVEs appears in it</b> &mdash; "
      "including a CVSS 9.8 unauthenticated RCE that <b>Rev 2 added Oracle Secure Backup 19.1 to on 26 Oct</b>, "
      "and the eMudhra root-CA distrust that <b>Rev 2 added Database Server 19.3&ndash;19.32, 21.3&ndash;21.23 "
      "and 23.4.0&ndash;23.26.3 to on 30 Oct</b> &mdash; effectively every supported release, through the "
      "embedded JDK. Anyone who triaged from Rev 1 was wrong within days. Meanwhile "
      "<b>CVE-2026-21962 is 65 days past its KEV due date</b> with a fix available since the January 2026 CPU and "
      "not re-shipped in October, a third consecutive quarter of unpatched-by-omission, and the official "
      "performance channel has now been unreachable for <b>nineteen</b> weeks.</p>") + spend([
      li("<b>Patch from the alerts, not the CPU.</b> The quarterly window is provably no longer Oracle's security "
         "cadence: a parallel eight-times-a-year CSPU track exists (next <b>17 Nov</b>) and the October alerts sit "
         "outside both.", "Three out-of-band Security Alerts"),
      li("<b>The newest release carries the newest holes, and they are in the AI surface.</b> Four of the 14 "
         "DB Server CVEs this quarter exist only in 23.4.0&ndash;23.26.3, topped by <b>CVE-2026-91499 at 8.8 in "
         "<code>DBMS_VECTOR</code></b> over Oracle Net. Adopting vector search is a net increase in patch "
         "obligation.", "CVE-2026-91499"),
      li("<b>ORDS 26.3 is now the front door to MCP and the most-patched component in the tools stack</b> &mdash; "
         "35 patches this CPU, 11 unauthenticated, top score 8.8, fixed build 26.3.0 &mdash; and 26.3 MCP now "
         "<i>requires</i> the <code>ORDS_MCP_SERVER</code> role, so existing clients break until it is granted.",
         "Oracle REST Data Services took 35 patches"),
      li("<b>Exadata 26.2 is RoCE-only and pre-X8M racks have no path</b>, Live Update cannot cross the OL8&rarr;OL9 "
         "boundary, and OL9 flips NSS order to <code>sss files</code> &mdash; an LDAP UID colliding with "
         "<code>dbmsvc</code> stops management services starting. Check for collisions <i>before</i> you upgrade.",
         "Exadata System Software 26.2 desupports InfiniBand"),
      li("<b>23.26.4 shipped 31 features and not one is named for the optimizer</b>, statistics, Automatic "
         "Indexing, SPM or In-Memory. That is the documented list, not an inference from the unreachable blog &mdash; "
         "the quarter's engineering went to Iceberg writes, vectors, HA plumbing and SQL syntax.",
         "RU 23.26.4's 31 features include nothing named for the optimizer")])

    read["snowflake"] = lede + (
      "<p><span class='sim'>SIMULATED CHAIR</span> From the Snowflake seat the day is about <b>dates that soften "
      "rather than harden, and defaults that arrive before their controls.</b> Release 10.37 moved the whole "
      "bundle ladder &mdash; 2026_07 is now enabled by default and 2026_06 generally enabled, so the opt-out "
      "lever on <code>CORTEX_MODELS_ALLOWLIST</code> is the only one left &mdash; and this board had to "
      "<b>withdraw a day-precise date it was carrying</b>: the final retirement reads &ldquo;January 2027&rdquo;, "
      "a month with no day. The catch is instructive, because a search summary asserted the board's own figure "
      "and the primary page overruled it. On the agent side, <b>CoWork's "
      "<code>dashboard_data_access</code> defaults to TRUE, grants whole underlying tables for the conversation, "
      "and does not appear in <code>DESCRIBE AGENT</code> unless it was explicitly set</b> &mdash; so you cannot "
      "enumerate your exposure with the obvious command.</p>") + spend([
      li("<b>Two unbundled dates sit just outside the fortnight and both bite IaC first:</b> interactive-warehouse "
         "<code>AUTO_SUSPEND</code> drops 24h&rarr;1h on <b>17 Nov</b> (a <code>CREATE OR REPLACE</code> without an "
         "explicit value inherits the new default, and an interactive resume resets cache and restarts the minimum "
         "billable period), and Azure allowlists need Network Identifiers on <b>18 Nov</b>, with Key Vault requiring "
         "NSP migration.", "interactive warehouses"),
      li("<b>Set <code>INCLUDE_PROTECTED_USER_DATA = FALSE</code> now if account membership is sensitive.</b> "
         "Bundle 2026_08 adds <code>ALL_USER_DETAILS</code>, callable by <i>any</i> session because it resolves no "
         "object &mdash; and the docs say disabling the bundle only postpones the change.", "ALL_USER_DETAILS"),
      li("<b>Secondary indexes went GA on <i>standard</i> tables</b> &mdash; not hybrid, not Iceberg &mdash; with "
         "maintenance billed through the search-optimization service. That is the month's real perf lever for "
         "selective lookups, and the cost lands in a bucket you may already have budgeted elsewhere.",
         "Secondary indexes went GA"),
      li("<b>Iceberg v3 upgrades are GA and permanent</b>: rollback is Time Travel only, inside retention. And "
         "non-constant expression defaults are evaluated <i>only</i> for Snowflake writes, so another engine "
         "writing the same table will not apply them.", "Iceberg v3 table upgrades"),
      li("<b>One driver CVE finally became scanner-visible &mdash; a month after the fix.</b> CVE-2026-86597's "
         "fixes shipped 2026-09-03; the GHSA with package ranges landed 2026-10-05, which is when builds that "
         "passed yesterday started failing. ODBC and PHP PDO have no OSV ecosystem at all.", "CVE-2026-86597")])

    read["databricks"] = lede + (
      "<p><span class='sim'>SIMULATED CHAIR</span> From the Databricks seat this is a <b>deadline week with a "
      "third-party-credential problem attached.</b> Two hard cutovers land on <b>5 Nov</b> &mdash; Runtime 18.2 "
      "end-of-support, where the consequence is sharper than &ldquo;no support&rdquo; because 18.2 stops being "
      "selectable when you <i>edit</i> a cluster, and DeepSeek V4 Flash (0731) retiring with workloads simply "
      "stopping &mdash; and the model named as its replacement, V4.1 Flash, is itself gone on <b>19 Nov</b>. "
      "Both of this month's Databricks CVEs are in <b>third-party tools holding a Databricks credential, not in "
      "Databricks</b>: mem0's vector store injects SQL into your warehouse, and n8n's node reads your secrets "
      "with <b>no patched release in existence</b>. A policy that tracks only &ldquo;Databricks CVEs&rdquo; sees "
      "neither.</p>") + spend([
      li("<b>Find the callers before the models go.</b> Databricks publishes the query: join "
         "<code>system.serving.endpoint_usage</code> to <code>system.serving.served_entities</code> and filter "
         "<code>entity_name LIKE '%&lt;model&gt;%'</code> grouped by <code>requester</code>. Run it for both "
         "DeepSeek snapshots.", "find workloads using retired models"),
      li("<b>Go 1.20.x straight to CLI 1.23.0 and skip 1.21/1.22.</b> 1.20.0 removed the Terraform engine outright "
         "(<code>bundle.engine: terraform</code> now errors), 1.21.0 broke SQL-notebook uploads, and 1.23.0 rolled "
         "that back.", "Databricks CLI v1.20.0"),
      li("<b>DataFrame caching on serverless is a preview that is already on</b> &mdash; &ldquo;enabled by default "
         "for most workspaces&rdquo; &mdash; so if you want deterministic cost accounting, disable it from the "
         "Previews page rather than discovering it in a bill.", "DataFrame caching"),
      li("<b>Serverless metrics now hide row-filter and column-mask internals</b>, so anything that parses Spark "
         "Connect metrics to attribute cost or find skew is blind inside a protected subplan.",
         "DataFrame execution metrics now hide internal operators"),
      li("<b>Delta 4.4.1 makes destructive maintenance a no-op rather than an error on catalog-managed tables</b> "
         "&mdash; log cleanup, auto-compaction and manifest generation are <i>skipped</i>, not refused. A vacuum "
         "job you still schedule now does nothing silently.", "Catalog-managed tables require the catalog")])

    read["bigquery"] = lede + (
      "<p><span class='sim'>SIMULATED CHAIR</span> From the BigQuery seat October was the <b>quietest engine month "
      "in a long while and the loudest agent month</b>: of 34 release-note entries, 20 are conversational "
      "analytics or <code>AI.*</code> features and <b>zero</b> touch slots, reservations, editions, autoscaling, "
      "pricing, BI Engine, materialized views, partitioning, clustering or vector search. The two items that do "
      "change operations are both sharp. <b>Reusable column aliases went GA as an org- or project-scoped DDL "
      "flag with no query-level override</b>, and enabling it changes name resolution for queries that already "
      "work &mdash; an alias now shadows outer-query columns, UDF arguments and script variables inside its "
      "scope. And the <b>MCP <code>execute_sql</code> tool runs DDL and DML at a global endpoint while MCP Data "
      "Access audit logging is off by default.</b></p>") + spend([
      li("<b>Check <code>EFFECTIVE_PROJECT_OPTIONS</code> before assuming which alias mode you are in.</b> "
         "Google's own mitigation advice is &ldquo;do not name aliases after script variables, function arguments "
         "or outer query columns&rdquo; &mdash; which is advice about queries you have already written.",
         "Reusable column aliases went GA"),
      li("<b>&ldquo;IAM is the only control&rdquo; is now wrong in both directions.</b> Deny policies can filter on "
         "<code>tool.isReadOnly</code> and <code>request.auth.oauth.client_id</code>, so &ldquo;block every "
         "non-read-only MCP tool&rdquo; is expressible while &ldquo;allow only read-only&rdquo; is not &mdash; and "
         "Model Armor does not scan <code>resource/read</code> calls.", "Control MCP use with IAM"),
      li("<b>Turn on Data Access logging for the MCP service and confirm you get a line</b> &mdash; the docs do not "
         "promise that tool names or arguments are recorded, so verify rather than assume.", "MCP audit logging"),
      li("<b>Arrow query results are the first real alternative to the key-value row encoding</b>, and the client "
         "side landed with it: <code>google-cloud-bigquery</code> 3.47.0 skips job creation for Arrow "
         "<code>query_and_wait</code>, but needs <code>bigquery-storage</code> 2.43.0 &mdash; a two-package bump, "
         "and no job row to inspect afterwards.", "Apache Arrow query results"),
      li("<b>Python UDF volume mounts have no version pinning</b> &mdash; &ldquo;changes in Cloud Storage can affect "
         "the UDF automatically, even during a running query&rdquo;. Treat the mounted prefix as immutable by "
         "convention and scope the connection's service account with a prefix condition.",
         "Python UDF volume mounts")])

    NAV["v-read"] = "4 chairs &middot; " + str(ef["today_rows"]) + " cutovers today"

    # -------------------------------------------------------------------- v-wn
    wn = ("<p class='lede'>Edition " + ED + " against " + PAR_ED + ". <b>" + str(len(new_ev_k)) +
      " new event rows, " + str(len(new_pa_k)) + " new patch rows, " + str(len(led.get("_corrections_109", []))) +
      " corrections applied to the ledger before any section was generated, and 8 rows enriched in place</b> "
      "rather than given fresh slugs. The shape of the day is the 10-30 finding repeating: <b>almost the entire "
      "November deadline wall was already on this board with correct dates</b>, so probing came first and the "
      "depth went into corrections and enrichment. " + C(None, TODAY) + "</p>"
      "<div class='wngroup wn-new'><h3><span>&#127381; New on the board</span><span>" +
      str(len(new_ev_k) + len(new_pa_k)) + "</span></h3>"
      + "".join(["<div class='wnitem'>" + t + " " + C(s) + "</div>" for t, s in [
        ("<b>Apache Pinot CVE-2026-73322</b> &mdash; <code>lookup()</code> bypasses broker ACLs and skips "
         "row-level security on the dimension table; <b>no 1.5.2, and 1.6.0 needs Java 25</b>.",
         "CVE-2026-73322: lookup() bypasses broker access control"),
        ("<b>Parquet-Java has no GA build</b> carrying the bloom-filter-wrong-column-path or dictionary-collision "
         "fixes &mdash; 1.19.0 stuck after nine RCs with no October vote, 1.18.2 only at DISCUSS.",
         "Apache Parquet Java 1.18.2 release"),
        ("<b>n8n Databricks node CVE-2026-119557</b> &mdash; unencoded <code>spaceId</code> lets a webhook reach "
         "<code>/api/2.0/secrets/get</code> with your stored credential. <b>No patched release exists.</b>",
         "n8n's Databricks node has an unpatched path traversal"),
        ("<b>MongoDB Node driver: cross-user data exposure via <code>timeoutMS</code></b>, plus unverified SRV "
         "hostnames since v3.3.3. <b>No CVE, no GHSA, and no 6.x backport.</b>",
         "cross-user data exposure via timeoutMS"),
        ("<b>Percona Server for MySQL 8.4 has no build carrying the October CPU</b> &mdash; newest tag 8.4.11-11 "
         "(2026-08-20), inside the affected range for a pre-auth 8.8.",
         "Percona Server for MySQL 8.4 users have no release"),
        ("<b>Kernel CVE-2026-98432 reaches Go programs</b> because Go has enabled MPTCP by default on listen "
         "sockets since 1.24 &mdash; and upgrading Go is explicitly <i>not</i> the remedy.",
         "CVE-2026-98432"),
        ("<b>Kafka CVE-2026-110952</b> &mdash; OAUTHBEARER checks <code>iss</code>/<code>aud</code> only if "
         "configured, and both are unset by default. Fixable by config; 4.4.0 refuses to start without it.",
         "CVE-2026-110952"),
        ("<b>Valkey cluster Pub/Sub heap overflow</b> patched across five branches at once &mdash; the breadth is "
         "the signal.", "heap buffer overflow when constructing cluster Pub/Sub"),
        ("<b>Snowflake interactive <code>AUTO_SUSPEND</code> 24h&rarr;1h on 2026-11-17</b>, and <b>Azure Network "
         "Identifier allowlists on 2026-11-18</b> &mdash; both unbundled, both bite IaC first.",
         "interactive warehouses")]])
      + "</div>"
      "<div class='wngroup wn-changed'><h3><span>&#128314; Corrected on the board</span><span>" +
      str(len(led.get("_corrections_109", []))) + "</span></h3>"
      + "".join(["<div class='wnitem'>" + t + " " + C(s) + "</div>" for t, s in [
        ("<b>Snowflake <code>CORTEX_MODELS_ALLOWLIST</code> retirement: 2026-11-18 &rarr; UNDATED.</b> The vendor "
         "publishes &ldquo;January 2027&rdquo;, a month with no day. Recorded for the method as much as the date: "
         "a search summary asserted this board's own figure and the primary page overruled it &mdash; <b>a "
         "secondary source agreeing with your board is not corroboration when both may share one bad origin.</b>",
         "CORTEX_MODELS_ALLOWLIST"),
        ("<b>MongoDB SERVER-131805: &ldquo;no fix on ANY Percona build&rdquo; &rarr; Percona now carries it.</b> "
         "8.0.34-15 (22 Oct) and 7.0.45-24 (21 Oct) track upstream at an <b>8&ndash;9 day</b> lag, closing a "
         "no-fix this board has carried since September. 5.0, 6.0 and EOL 8.2 are still unpatched.",
         "Percona is current for the first time"),
        ("<b>CVE-2026-21962 re-measured at 65 days past due</b>, and the fix-by-omission re-confirmed against "
         "Oracle's own CVE-to-advisory map: available since the January 2026 CPU, absent from October's.",
         "CVE-2026-21962 is 65 days past its due date"),
        ("<b>Kubernetes row: a relative &ldquo;TODAY&rdquo; replaced with 2026-10-30.</b> 1.34 reached EOL "
         "yesterday; the word was true when written and false by morning. <b>A relative date inside carried prose "
         "is a claim that rots silently.</b>", None),
        ("<b><code>edk2-stable202610</code> does not exist.</b> Secondary write-ups place the PXE fix in that tag; "
         "the tag list jumps 202605&rarr;202608 and a raw fetch 404s, so the newest tag still predates the "
         "2026-10-15 merge and the GHSA still reads &ldquo;Not patched currently&rdquo;.",
         "no tagged EDK II stable release carries the fix")]])
      + "</div>"
      "<div class='wngroup wn-ongoing'><h3><span>&#10160; Past their date on the horizon</span><span>" +
      str(len(ret)) + "</span></h3>"
      + "".join(["<div class='wnitem'><code>" + k + "</code> &mdash; date passed " + C(None, TODAY) +
                 "</div>" for k in ret])
      + "</div>")
    NAV["v-wn"] = "vs edition " + PAR_ED

    # ---------------------------------------------------------- v-longitudinal
    lon = ("<p class='lede'><b>" + str(len(series)) + " days of ledger.</b> Today: <b>" + str(cur["items"]) +
      " items</b>, " + str(cur["oracle"]) + " Oracle-lane, " + str(cur["comp"]) + " across the six competitor "
      "lanes, " + str(cur["dbhw"]) + " DB-hardware, <b>" + str(cur["urgent"]) + " urgent lanes</b>. The urgent "
      "count over the last eight runs reads <b>" + " &middot; ".join(str(x) for x in run8) + "</b> &mdash; so "
      "<b>the six-run plateau at " + str(max(run8[:-1])) + " broke today</b>, down to " + str(cur["urgent"]) +
      " against a series high of " + str(ls["urgent_prior_max"]) + " and a 14-run mean of " +
      str(round(ls["urgent_mean14"], 1)) + ". That is the agents' arithmetic, not a trim: seven lanes returned "
      "<code>ok</code> while holding real CVEs and each wrote out why. <b>Read the High column with care:</b> "
      "every run re-derives the severity heuristic rather than reading a stored value, so a change there is a "
      "classifier change, not a change in the world; Items, Oracle-lane and the lane counts are the real trend "
      "lines. " + C(None, TODAY) + "</p>"
      "<table class='rad'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th><th>Competitors</th><th>DB HW</th>"
      "<th>High</th><th>Urgent lanes</th></tr></thead><tbody>"
      + "".join(["<tr><td><b>" + r["date"] + "</b></td><td>" + str(r["items"]) + "</td><td>" + str(r["oracle"]) +
                 "</td><td>" + str(r["comp"]) + "</td><td>" + str(r["dbhw"]) + "</td><td>" + str(r["high"]) +
                 "</td><td>" + str(r["urgent"]) + "</td></tr>" for r in series[-14:]])
      + "</tbody></table>"
      "<h3>Early observations</h3><ul>"
      + li("<b>The plateau broke downward, and the reason is visible in the lanes rather than in the heuristic.</b> "
           "Six consecutive runs flagged " + str(max(run8[:-1])) + " of 19; today flags " + str(cur["urgent"]) +
           ". Seven lanes held <code>ok</code> while carrying real CVEs &mdash; AI Hardware on the grounds that "
           "<b>zero NVIDIA entries exist in the entire CISA KEV catalog</b>, Open Formats declining a CVSS 8.1 "
           "because the fix predates disclosure, Frontend declining two Criticals with a 17-day-old reachable fix. "
           "Calibration applied literally, not trimmed to a number.", "zero NVIDIA entries", TODAY)
      + li("<b>Item volume rose to " + str(cur["items"]) + " while urgent fell</b> &mdash; so the day was broader "
           "and less acute. The deadline wall carries the weight instead: <b>" + str(ef["inside14"]) +
           " dated rows inside fourteen days across " + str(ef["distinct_dates_inside14"]) +
           " distinct dates</b>, which is a schedule problem rather than an incident.", None, TODAY)
      + li("<b>The no-fix register is the number that best describes this month, and it stands at " + str(nofix) +
           ".</b> Today it gained a Pinot ACL bypass whose only fix is a breaking major with a JDK rollout on its "
           "critical path, and lost one &mdash; Percona's MongoDB builds closed to an 8&ndash;9 day lag. <b>A "
           "resolved no-fix is worth recording as loudly as a new one.</b>", None, TODAY)
      + li("<b>Oracle-lane volume sits at " + str(cur["oracle"]) + " and for a nineteenth week none of it comes "
           "from the official performance channel</b>, which 403s HTML and RSS alike. That is a structural "
           "coverage gap, not a quiet quarter, and the brief says so on its face.",
           "blogs.oracle.com 403s HTML and RSS")
      + "</ul><h3>Queued for the 90-day view</h3><ul>"
      "<li>Per-item severity stored in the public ledger, so the High column becomes comparable across days "
      "instead of being re-derived each run. Still the oldest item on this list.</li>"
      "<li>A &ldquo;distinct stories&rdquo; count beside the urgent-lane count &mdash; today's " +
      str(cur["urgent"]) + " flags cover roughly 11 distinct stories, and the board cannot show that divergence "
      "over time.</li>"
      "<li>A no-fix-register time series. It stands at <b>" + str(nofix) + "</b> today, has never been plotted, "
      "and it moved in both directions this run.</li></ul>"
      "<p class='note'>Raw data: the public archive ledger directory, one JSON per run. " +
      L.cite("https://github.com/karlarao/daily-briefings/tree/gh-pages/archive/ledger", TODAY, today=TODAY) +
      "</p>")
    NAV["v-longitudinal"] = str(len(series)) + "d series"

    # ----------------------------------------------------------------- v-patch
    PHEAD = "<table class='rad'><thead><tr><th>Due / fix status</th><th>Item</th><th>Src</th></tr></thead><tbody>"
    prows = [PHEAD]
    for r in shown:
        src = L.cite(r.get("url"), r.get("last_seen"), r.get("first_seen"), TODAY, today=TODAY)
        prows.append("<tr><td><b>" + str(r.get("due", "&mdash;")) + "</b></td><td>" + str(r.get("t", "")) +
                     "</td><td>" + src + "</td></tr>")
    prows.append("</tbody></table>")
    patch_html = ("<p class='lede'>Capped at the <b>" + str(len(shown)) + "</b> most actionable rows of <b>" +
      str(len(led["patch"])) + "</b> on the board &mdash; due inside 30 days, or corrected, re-measured or added "
      "today. The rest stay in the embedded ledger. The <b>no-fix register stands at " + str(nofix) + "</b>: rows "
      "where some affected population has no reachable patch, counted from the <code>due</code> field rather than "
      "by matching &ldquo;no fix&rdquo; in the prose (the 09-18 lesson, where a prose match returned 23 against a "
      "true 14). <b>" + str(len(new_pa_k)) + " rows are new today and 8 were enriched in place</b> rather than "
      "given fresh slugs, because <code>probe_identifiers</code> made every near-match visible first. " +
      C(None, TODAY) + "</p>") + "".join(prows)
    NAV["v-patch"] = str(len(shown)) + " of " + str(len(led["patch"])) + " &middot; " + str(nofix) + " no-fix"

    # ---------------------------------------------------------------- v-events
    ev_block = ("<p class='lede'><b>" + str(ef["total"]) + " rows on the board, " + str(ef["inside14"]) +
      " inside fourteen days and " + str(ef["inside7"]) + " inside seven</b> &mdash; against 29 and 23 yesterday "
      "&mdash; and <b>" + str(ef["today_rows"]) + " land TODAY</b>. Two rows are new, both Snowflake unbundled "
      "changes, and " + str(len(ret)) + " sit past their date. Undated rows (" + str(ef["undated"]) + ") carry a "
      "TBD chip and sort last: <b>a row is day-precise only when the vendor published a day</b>, which is the "
      "habit five fabricated dates taught this board &mdash; and today's corrections move one more date "
      "<i>away</i> from precision for exactly that reason. " + C(None, TODAY) + "</p>") + ev_html
    NAV["v-events"] = str(ef["inside14"]) + " inside 14d"

    return read, wn, lon, patch_html, ev_block, NAV
