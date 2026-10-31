#!/usr/bin/env python3
"""Edition 108 lens build. Inheritance from 107 + spliced sections.

House style (09-18/09-20 rule): HTML blocks embedding cite() output are built by
CONCATENATION with explicit str(), never %-formatted -- ledger prose carries
literal % signs ("35% faster", "5% Core Technology Commission") and %-formatting
consumes them as conversion specifiers. This has bitten four times.
"""
import json, os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(SP), "tools", "lens"))
import lens_guard as G, lens_extra as X, lens_links as L
import events_table as ET, patch_radar as PR, longitudinal as LG
import ledger_surgery as LS
from datetime import date

TODAY, ED, PAR_ED, PAR_DT = "2026-10-30", "108", "107", "2026-10-29"
GEN = "2026-10-30 09:52 EDT"
BRIEFS = os.path.join(os.path.dirname(SP), "tools", "ledger", "briefs")
LEDGER_DIR = "/home/user/daily-briefings/archive/ledger"
PARENT = os.path.join(SP, "index.html")

html = open(PARENT, encoding="utf-8").read()
led = json.load(open(os.path.join(SP, "ledger_108.json")))
corpus = L.mine_briefs(BRIEFS)
print("mined %d primary links from %d briefs" % (len(corpus), len(os.listdir(BRIEFS)) // 3))

def C(title, *dates):
    """cite() with a SEEN-date fallback chain -- never an event's own date (09-12).

    Defensive on a None title: the archive-fallback case has no headline to mine,
    and find_url() would raise on it. Call it as C(None, d) and get the dated
    public-archive link, which is the honest citation for a claim about this
    edition's own board (the 09-17 lesson).
    """
    if title is None:
        return L.cite(None, *(list(dates) + [TODAY]), today=TODAY)
    return L.cite(L.find_url(title, corpus), *(list(dates) + [TODAY]), today=TODAY)

def li(txt, title, *dates):
    return "<li>" + txt + " " + C(title, *dates) + "</li>"

led = G.stamp_ledger_identity(led, TODAY, int(ED))

# ------------------------------------------------------------------ v-events
act_of = {r["k"]: r.get("act", "") for r in led["events"] if r.get("act")}
ev_html, ev_shown = ET.render(led["events"], TODAY, horizon=60, act_of=act_of)
ef = ET.facts(led["events"], TODAY)
print("events:", ef)

# ------------------------------------------------------------------- v-patch
must = ["clickhouse-116366-unauth-rce-no-267-fix",
        "edk2-97631-preboot-pxe-rce-no-tag",
        "pgbouncer-107350-scram-bypass",
        "claude-code-2-1-313-ssh-backdoor",
        "supermicro-bmc-18450-two-skus-tbd",
        "fastlane-asc-session-leak-local",
        "brotli-111497-kev-runtime-wide-scanner-blind",
        "php2shell-two-kev-rce-no-81-fix",
        "jdk-114820-no-vendor-build-keytool",
        "nextjs-oct14-two-95-rces-no-13x-14x-fix",
        "cve-2026-21962-ohs-weblogic-kev",
        "mongo-go-driver-v1-107325-no-fix"]
PR.mark_touched(led["patch"], set(), "CORRECTED 10-30", "RE-MEASURED 10-30",
                "SHARPENED 10-30", "NEW POPULATION 10-30", "MEASURED 10-30")
shown = PR.select(led["patch"], date.fromisoformat(TODAY), 35, must)
PR.assert_must_show(shown, must)
nofix = PR.count_no_fix(led["patch"])
print("patch radar: %d shown of %d, no-fix register %d" % (len(shown), len(led["patch"]), nofix))

# ------------------------------------------------------------ v-longitudinal
series = LG.series(LEDGER_DIR, TODAY)
ls = LG.stats(series, TODAY)
run8 = [r["urgent"] for r in series[-8:]]
print("longitudinal: %d days, urgent run8=%s" % (len(series), run8))

json.dump(led, open(os.path.join(SP, "ledger_108_final.json"), "w"), ensure_ascii=False)

# =========================================================== authored sections
# Every row generator calls C() inline as it emits (09-15 mechanism) -- prose is
# never written first and citations retrofitted. That is why guard 5 passes.

NAV = {}

# ---------------------------------------------------------------- Today's Read
read = {}
_lede_common = (
  "<p class='lede'>The day's lead is a <b>first-party supply-chain compromise</b>: the Claude Code extension for "
  "VS Code and Cursor shipped build <code>2.1.313</code> carrying a persistent SSH backdoor, pulled from npm, "
  "Open VSX and the Cursor marketplace overnight &mdash; and <b>uninstalling does not remove it</b>. "
  "Registry state was verified directly for this edition rather than taken from the advisory: <code>2.1.313</code> "
  "is <b>404 on npm</b> while 2.1.312 and 2.1.314 resolve, and Open VSX lists 2.1.314 published "
  "<b>01:07:38Z today with 2.1.313 absent entirely</b>. Attribution remains open. "
  "Behind it sits the densest deadline wall this board has carried &mdash; <b>" + str(ef["today_rows"]) +
  " cutovers land today and " + str(ef["inside7"]) + " rows sit inside seven days</b> &mdash; plus four new "
  "unauthenticated RCEs with no reachable fix: a <b>pre-boot</b> RCE in the EDK II PXE driver that runs before "
  "Secure Boot measures anything, a CVSS 10.0 KEV-listed GitLab RCE that CISA marks <code>automatable: yes</code>, "
  "a same-day ClickHouse RCE patched on no branch at or below 26.7, and a PgBouncer SCRAM bypass turning one "
  "stolen password into superuser on every pooled database. "
  "The structural story is that <b>the identifier plumbing has stopped tracking the facts</b>: on one CVE the "
  "scanner is now wrong in <i>both</i> directions at once.</p>")

def spend(rows):
    return "<h3>Where to spend today's attention</h3><ul>" + "".join(rows) + "</ul>"

read["oracle"] = _lede_common + (
  "<p>For an Oracle performance engineer the sharpest item is <b>Oracle's own revision discipline</b>: "
  "Secure Backup 19.1 is hit by a KEV-listed CVSS 9.8 unauthenticated RCE whose due date passed yesterday, and "
  "Oracle only added the product to that alert at <b>Rev 2</b> &mdash; Rev 1, one day earlier, omitted it. Anyone "
  "who triaged on day one was wrong by morning. Meanwhile <b>CVE-2026-21962 is 64 days past its KEV due date and "
  "appears zero times in the published October CPU</b>, a third consecutive quarter, and the official performance "
  "channel has now been unreachable for seventeen weeks.</p>") + spend([
  li("<b>Re-read the Secure Backup alert, not a cached copy</b> &mdash; Rev 2 is the only revision that names the "
     "product, and the alert says it &ldquo;will continue to be updated&rdquo;.",
     "Oracle Secure Backup 19.1.0.0.0"),
  li("<b>Six CVSS 10.0 rows in the October CPU, counted from the matrices</b> &mdash; and none is RDBMS; the "
     "Database family tops out at 9.8. Worth knowing before someone quotes &ldquo;a 10.0 in the Oracle CPU&rdquo;.",
     "The October 2026 CPU carries SIX CVSS 10.0 rows"),
  li("<b>APEX 24.1.x/24.2.x have no publicly named fixed build</b> for a 9.8 unauthenticated takeover &mdash; the "
     "only non-affected public download is 26.2, so 24.x fixes live behind a support contract.",
     "Oracle APEX 24.1.x and 24.2.x have no publicly named fixed build"),
  li("<b>ADB Serverless got six October features and Dedicated got one</b> &mdash; including "
     "<code>DBMS_USERDIAG</code> SQL tracing and storage-cache hit metrics, neither of which is on Dedicated yet.",
     "Select AI for Java gains agents"),
  li("<b>23.26.4 is a genuinely low plan-regression RU</b>: zero new/changed initialization parameters and zero "
     "new or changed V$ views, with new ADDM rule dictionary views as the only diagnostics change.",
     "Oracle AI Database 26ai Release Update 23.26.4"),
  li("<b>Exadata System Software is a coverage hole, not a quiet month</b> &mdash; no October release could be "
     "verified at all because <code>blogs.oracle.com</code> 403s HTML and RSS for a seventeenth week.",
     "blogs.oracle.com 403s HTML and RSS")])

read["snowflake"] = _lede_common + (
  "<p>From the Snowflake chair the local item is tomorrow's <b>MFA Phase 3 window closing</b> &mdash; and the "
  "doc's semantics are weaker than a cliff: enforcement is &ldquo;on a rolling basis&rdquo; with per-account "
  "notification, and Phase 3 is deliberately <i>not</i> tied to a behavior-change bundle, so no bundle lifecycle "
  "guarantees completion either. The second-order item is the <b>driver OCSP reversal</b>: the September releases "
  "that fixed an OCSP CVE also turned revocation checking <b>off by default</b>.</p>") + spend([
  li("<b>MFA Phase 3's window closes tomorrow but enforcement may not have reached you</b> &mdash; when it lands, "
     "all non-human users are blocked from password auth and <code>LEGACY_SERVICE</code> objects migrate to "
     "<code>SERVICE</code>, which cannot hold a password.", "MFA Phase 3"),
  li("<b>The Sept 30 drivers turn OCSP revocation checking off by default and deprecate OCSP outright</b> &mdash; "
     "so the upgrade you do to get the OCSP CVE fix silently removes revocation checking unless you opt back in.",
     "turn OCSP revocation checking off by default"),
  li("<b><code>gosnowflake</code> v1 has no reachable fix</b> for CVE-2026-85525 &mdash; the OCSP-validation "
     "flaw that accepts a revoked TLS certificate &mdash; on the v1 module path.",
     "CVE-2026-85525"),
  li("<b>Snowflake has zero CISA KEV entries</b>, checked against catalog 2026.10.29 directly rather than "
     "inferred &mdash; which is why this lane's CVEs did not drive the flag.",
     "Snowflake has zero entries in CISA KEV"),
  li("<b>The deadline wall here is made of month-precision windows, not days</b> &mdash; Phase 3's "
     "&ldquo;Aug&ndash;Oct 2026&rdquo;, BCR-2413's &ldquo;early February 2027&rdquo;. A month is not a date you "
     "can put in a change calendar.", "increasingly made of month-precision windows")])

read["databricks"] = _lede_common + (
  "<p>From the Databricks chair this is a lifecycle day with a <b>retired urgent</b> in it. Three pay-per-token "
  "models hard-fail today with no reroute (the grace redirect applies only to <i>partner</i> models, and these "
  "are open), <b>DBR 10.4 LTS reaches EoL in two days</b> where the image is removed and pinned jobs fail rather "
  "than upgrading, and DBR 18.2 EoS follows on the 5th &mdash; where what breaks is compute <i>creation</i>, not "
  "running jobs. Against that, the <b>Genie MCP sunset moved out 30 days</b>, which this edition corrects on the "
  "board.</p>") + spend([
  li("<b>The Genie MCP beta endpoint is 2026-11-30, not tomorrow</b> &mdash; Databricks changed it and states "
     "&ldquo;The previous date was October 31&rdquo;. A carried urgent retires for 30 days.",
     "The Genie MCP beta endpoint"),
  li("<b>DBR 10.4 LTS EoL removes the image</b>, so anything pinned in a job, instance pool or Asset Bundle "
     "<code>spark_version</code> fails outright on Sunday. It is still the only DBR with a published EoL date.",
     "DBR 10.4 LTS reaches end of life"),
  li("<b>The deprecation chain is shorter than a migration cycle</b> &mdash; today's V4 Pro retirement names V4.1 "
     "Flash as its target, and V4.1 Flash itself retires on the 19th. Pin the <code>(1017)</code> snapshot.",
     "DeepSeek V4.1 Flash"),
  li("<b>Predictive optimization does not run Z-ORDER and ignores Z-ordered files</b>, stated twice on a page "
     "updated 10-26 &mdash; so a Z-ordered table gets <i>less</i> automatic maintenance than a clustered one.",
     "Predictive optimization does not run Z-ORDER"),
  li("<b>Variant shredding goes default on 11-18 and DBR 15.4 clusters cannot read or write those tables</b> "
     "&mdash; upgrade 15.4 to 16.4+ before the date.", "Variant shredding"),
  li("<b>Delta 4.4.1 fixes a wrong-snapshot bug in S3A fast listing</b>, where the failure mode was an incorrect "
     "table state rather than an error &mdash; so there is nothing in your logs to find afterwards.",
     "delta.enableFastS3AListFrom")])

read["bigquery"] = _lede_common + (
  "<p>From the BigQuery chair the local item is a <b>billing-model flip that no quota can cap</b>: TabFM moved to "
  "token pricing today at $0.05/$0.20 per million, charged on top of slots or bytes &mdash; and the token quotas "
  "that GA'd on 10-14 are scoped to Gemini-backed functions, so a grep of the live quotas page returns zero for "
  "TabFM. The sharper detail is that the published token formula depends on <code>n_ensembles</code>, which "
  "appears nowhere in the function signature and is not disclosed: <b>you cannot compute your own bill from the "
  "documented interface</b>. The lane's other contribution is a negative proof extended from four docs to ten.</p>"
  ) + spend([
  li("<b>TabFM token billing is live and uncapped</b> &mdash; a Cloud Billing budget or a project spend cap is the "
     "only brake, and the feature is still Preview.", "TabFM on BigQuery moved to token billing"),
  li("<b>The Brotli KEV entry does not reach BigQuery, now proven across ten documents plus the transport</b>: "
     "the API answers <code>content-encoding: gzip</code> even when a request offers <code>br</code>, which closes "
     "the client-library decompression path that actually mattered.", "content-encoding: gzip"),
  li("<b>TimesFM 3.0 goes token-billed 2026-12-01 but is opt-in</b> &mdash; <code>AI.FORECAST</code>'s default "
     "stays TimesFM 2.5 on slots/bytes. The pricing page ships the date as an unedited editorial placeholder.",
     "TimesFM 3.0"),
  li("<b>35 features, zero deprecations, and the entire compute and tuning surface untouched</b> in 30 days &mdash; "
     "zero hits for slots, reservations, autoscaling, BI Engine, materialized views or clustering.",
     "35 Feature entries, 1 Change, zero deprecations"),
  li("<b>BigLake was renamed Lakehouse &mdash; but the APIs, CLI and IAM names still say biglake</b>. Docs say one "
     "thing, your Terraform says another.", "Lakehouse APIs, client libraries, CLI commands")])

NAV["v-read"] = "4 chairs &middot; " + str(ef["today_rows"]) + " cutovers today"

# ---------------------------------------------------------------------- v-wn
pw = json.load(open(os.path.join(SP, "parent_ledger.json")))
pk = {s: {r["k"] for r in pw.get(s, [])} for s in ("events", "patch")}
new_ev_k = [r["k"] for r in led["events"] if r["k"] not in pk["events"]]
new_pa_k = [r["k"] for r in led["patch"] if r["k"] not in pk["patch"]]
ret = [r["k"] for r in led["events"] if str(r.get("date") or "") and str(r["date"]) < TODAY]

wn = ("<p class='lede'>Edition 108 against 107. <b>" + str(len(new_ev_k)) + " new event rows, " +
  str(len(new_pa_k)) + " new patch rows, 8 corrections applied to the ledger before any section was "
  "generated, and 5 rows enriched in place rather than given fresh slugs</b> because "
  "<code>reuse_key</code>'s advisory caught them &mdash; its widest margin yet, and three of the four were "
  "catches a DATE-keyed probe could never have made.</p>"
  "<div class='wngroup wn-new'><h3><span>&#127381; New on the board</span><span>" + str(len(new_ev_k) + len(new_pa_k)) +
  "</span></h3>"
  + "".join([
    "<div class='wnitem'>" + t + " " + C(t) + "</div>" for t in [
      "Claude Code for VS Code/Cursor 2.1.313 shipped a backdoor",
      "GitLab CE/EE CVE-2026-97229 — unauthenticated RCE on the GitLab server",
      "CVE-2026-97631 — EDK II NetworkPkg/UefiPxeBcDxe ICMP buffer overflow",
      "ClickHouse CVE-2026-116366 — unauthenticated RCE on ClickHouse Server",
      "PgBouncer SCRAM authentication bypass, CVE-2026-107350",
      "Supermicro BMC: eight CVEs disclosed 2026-10-26",
      "Three High-severity fastlane advisories published 2026-10-26",
      "AKS has a one-day cliff: Azure Linux 2.0 node images"]])
  + "</div>"
  "<div class='wngroup wn-changed'><h3><span>&#128314; Corrected on the board</span><span>8</span></h3>"
  + "".join([
    "<div class='wnitem'>" + t + " " + C(s) + "</div>" for t, s in [
      ("<b>Genie MCP sunset 2026-10-31 &rarr; 2026-11-30</b> &mdash; vendor-stated move, &ldquo;The previous date "
       "was October 31&rdquo;. A carried urgent retires for 30 days.", "The Genie MCP beta endpoint"),
      ("<b>Databricks partner-powered-AI removal: 2026-11-01 &rarr; UNDATED</b>, and the Settings-API clause is "
       "withdrawn &mdash; the vendor says &ldquo;At a later date&rdquo; and never mentions that API.",
       "partner-powered-AI setting"),
      ("<b>DuckDB 2.0.0 LTS: TBD &rarr; DELIVERED 2026-10-21</b>, nine days before this board's placeholder. "
       "Codename Cinnamon Teal; storage version 69 is one-way.", "DuckDB (OSS) — 2.0.0 LTS"),
      ("<b>Python 3.10 EOL: 2026-10-31 &rarr; 2026-10-01</b> &mdash; already 29 days past, and the 10-25 eMudhra "
       "and <code>tarfile</code> fixes went to 3.11&ndash;3.15 but NOT to 3.10.",
       "Python 3.10 reached end of life on 2026-10-01"),
      ("<b>DeepSeek Search/Fetch billing: 2026-11-01 &rarr; 2026-10-31 16:00 UTC</b> &mdash; right day in Beijing, "
       "wrong day for a UTC reader, and the gap is ~27 hours not two days.",
       "DeepSeek starts billing Search and Fetch"),
      ("<b>GitHub <code>pull_request_target</code> enforcement: 2026-11-02 &rarr; 2026-12-02</b> by an editor's "
       "note dated 10-21 &mdash; so 11-02 is a SINGLE cutover, not the double one this board carried.",
       "pull_request_target default-off"),
      ("<b>CVE-2026-21962 re-measured at 64 days past due</b>, grepped against the October CPU text where the id "
       "appears zero times. The board's OHS/WebLogic attribution was already right.",
       "CVE-2026-21962 is 64 days past"),
      ("<b>Next.js 15 did NOT EOL on 2026-10-21</b> &mdash; third-party trackers are wrong; Vercel extended "
       "Maintenance LTS through 2027-01-31.", "Next.js 15 Maintenance LTS")]])
  + "</div>"
  "<div class='wngroup wn-ongoing'><h3><span>&#10160; Retired from the horizon</span><span>" + str(len(ret)) +
  "</span></h3>"
  + "".join(["<div class='wnitem'><code>" + k + "</code> &mdash; date passed " + L.cite(None, TODAY, today=TODAY) + "</div>" for k in ret])
  + "</div>")
NAV["v-wn"] = "vs edition " + PAR_ED

# -------------------------------------------------------------- v-longitudinal
lon = ("<p class='lede'><b>" + str(len(series)) + " days of ledger.</b> Today: <b>" + str(series[-1]["items"]) +
  " items</b>, " + str(series[-1]["oracle"]) + " Oracle-lane, " + str(series[-1]["comp"]) + " across the six "
  "competitor lanes, " + str(series[-1]["dbhw"]) + " DB-hardware, <b>" + str(series[-1]["urgent"]) +
  " urgent lanes</b>. The urgent count over the last eight runs reads <b>" + " &middot; ".join(str(x) for x in run8) +
  "</b> &mdash; a five-run plateau at " + str(series[-1]["urgent"]) + " against a series high of " +
  str(ls["urgent_prior_max"]) + ". <b>Read the High column with care:</b> each run re-derives the severity "
  "heuristic rather than reading a stored value, so a change there is a classifier change, not a change in the "
  "world; Items, Oracle-lane and the lane counts are the real trend lines. " + L.cite(None, TODAY, today=TODAY) + "</p>"
  "<table class='rad'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th><th>Competitors</th><th>DB HW</th>"
  "<th>High</th><th>Urgent lanes</th></tr></thead><tbody>"
  + "".join(["<tr><td><b>" + r["date"] + "</b></td><td>" + str(r["items"]) + "</td><td>" + str(r["oracle"]) +
             "</td><td>" + str(r["comp"]) + "</td><td>" + str(r["dbhw"]) + "</td><td>" + str(r["high"]) +
             "</td><td>" + str(r["urgent"]) + "</td></tr>" for r in series[-14:]])
  + "</tbody></table>"
  "<h3>Early observations</h3><ul>"
  + li("<b>The urgent plateau is real and it is five runs long.</b> 16 of 19 lanes have now flagged on each of "
       "the last five runs, against a 14-run mean of " + str(round(ls["urgent_mean14"], 1)) + ". That is not "
       "over-flagging drift: every run audited its flags against the literal definition and three lanes held "
       "<code>ok</code> today while carrying real CVEs.", "16 of 19", TODAY)
  + li("<b>Item volume fell from yesterday's series peak of 979 to " + str(series[-1]["items"]) + " while the "
       "urgent count held</b> &mdash; so the day was not quieter, it was more concentrated. The deadline wall is "
       "doing the work rather than breadth of news.", "deadline wall", TODAY)
  + li("<b>The competitor lanes at " + str(series[-1]["comp"]) + " stay near their recent band</b> while Oracle-lane "
       "volume sits at " + str(series[-1]["oracle"]) + " &mdash; and for a seventeenth week none of that Oracle "
       "volume comes from the official performance channel, which remains unreachable.",
       "blogs.oracle.com 403s HTML and RSS")
  + "</ul><h3>Queued for the 90-day view</h3><ul>"
  "<li>Per-item severity stored in the public ledger, so the High column becomes comparable across days instead "
  "of being re-derived each run. Still the oldest item on this list.</li>"
  "<li>A &ldquo;distinct stories&rdquo; count beside the urgent-lane count &mdash; today's 16 flags cover roughly "
  "14 distinct stories, and the board cannot currently show that divergence over time.</li>"
  "<li>A no-fix-register time series. It stands at <b>" + str(nofix) + "</b> today; it has never been plotted, and "
  "it is the number that best describes this month.</li></ul>"
  "<p class='note'>Raw data: the public archive ledger directory, one JSON per run. " +
  L.cite("https://github.com/karlarao/daily-briefings/tree/gh-pages/archive/ledger", TODAY, today=TODAY) + "</p>")
NAV["v-longitudinal"] = str(len(series)) + "d series"

# ====================================================== patch radar rendering
PHEAD = ("<table class='rad'><thead><tr><th>Due / fix status</th><th>Item</th><th>Src</th></tr></thead><tbody>")
prows = [PHEAD]
for r in shown:
    src = L.cite(r.get("url"), r.get("last_seen"), r.get("first_seen"), TODAY, today=TODAY)
    prows.append("<tr><td><b>" + str(r.get("due", "&mdash;")) + "</b></td><td>" + str(r.get("t", "")) +
                 "</td><td>" + src + "</td></tr>")
prows.append("</tbody></table>")
patch_html = ("<p class='lede'>Capped at the <b>" + str(len(shown)) + "</b> most actionable rows of <b>" +
  str(len(led["patch"])) + "</b> on the board &mdash; due inside 30 days, or corrected, re-measured or added "
  "today. The rest stay in the embedded ledger. The <b>no-fix register stands at " + str(nofix) + "</b>: rows "
  "where some affected population has no reachable patch, counted from the <code>due</code> field rather than by "
  "matching &ldquo;no fix&rdquo; in the prose (the 09-18 lesson, where a prose match returned 23 against a true "
  "14). <b>Six rows are new today and five were enriched in place</b> rather than given fresh slugs.</p>"
  ) + "".join(prows)
NAV["v-patch"] = str(len(shown)) + " of " + str(len(led["patch"])) + " &middot; " + str(nofix) + " no-fix"

ev_block = ("<p class='lede'><b>" + str(ef["total"]) + " rows on the board, " + str(ef["inside14"]) +
  " inside fourteen days and " + str(ef["inside7"]) + " inside seven</b>, against 31 and 23 yesterday &mdash; and "
  "<b>" + str(ef["today_rows"]) + " land TODAY</b>. Five rows are new, " + str(len(ret)) + " retired as their "
  "dates passed. Undated rows (" + str(ef["undated"]) + ") carry a TBD chip and sort last: a row is day-precise "
  "only when the vendor published a day, which is the habit that four fabricated dates in seven editions taught "
  "this board &mdash; and two of today's eight corrections move a date <i>away</i> from precision for exactly "
  "that reason. " + L.cite(None, TODAY, today=TODAY) + "</p>") + ev_html
NAV["v-events"] = str(ef["inside14"]) + " inside 14d"

# ================================================================== assembly
html = G.strip_host_wrapper(html)
sections = {"v-read": read["oracle"], "v-wn": wn, "v-events": ev_block,
            "v-patch": patch_html, "v-longitudinal": lon}
chips = {k: NAV[k] for k in sections}
html = G.splice_sections(html, sections, chips=chips, expect=15)

pov = json.loads(re.search(r'<script type="application/json" id="povContent">(.*?)</script>',
                           html, re.S).group(1))
for chair in ("oracle", "snowflake", "databricks", "bigquery"):
    pov["content"][chair]["v-read"]["h"] = read[chair]
    pov["content"][chair]["v-read"]["c"] = NAV["v-read"]
    pov["content"][chair]["v-wn"] = dict(pov["content"][chair].get("v-wn", {}))
    pov["content"][chair]["v-wn"]["h"] = wn
    pov["content"][chair]["v-wn"]["c"] = NAV["v-wn"]
html = re.sub(r'(<script type="application/json" id="povContent">)(.*?)(</script>)',
              lambda m: m.group(1) + json.dumps(pov, ensure_ascii=False) + m.group(3),
              html, count=1, flags=re.S)

html = X.rewrite_pov_meta(html, NAV, require=1)
html = G.refresh_nav(html, NAV)
html = G.rewrite_identity(html, ED, TODAY, GEN)

# runbar: rebuild the whole div and read it back. 09-18 reason still holds --
# the label and the value live in SEPARATE spans, so "Edition 107" never appears
# contiguously and no regex can find it; patching pieces half-succeeds silently.
runbar = ("<div class=\"runbar\">"
  "<span class=\"lbl\">Edition</span><span class=\"val\">" + ED + "</span>"
  "<span class=\"lbl\">Generated</span><span class=\"val\">" + GEN + "</span>"
  "<span class=\"lbl\">Model</span><span class=\"val\">claude-opus-5</span>"
  "<span class=\"lbl\">Inputs</span><span class=\"val\">19 briefs &middot; " + str(len(series)) + "d ledger</span>"
  "<span class=\"lbl\">Run tokens</span><span class=\"val\">~4,125k</span>"
  "<span class=\"lbl\">Skills review</span><span class=\"val\">2027-01-01</span>"
  "<span class=\"flag\">&#9873; Claude Code ext 2.1.313 shipped an SSH backdoor &mdash; uninstalling does not remove it "
  "&middot; GitLab CVE-2026-97229 CVSS 10.0 KEV, automatable, due 11-01 "
  "&middot; EDK II PXE pre-boot RCE, fix in master only "
  "&middot; ClickHouse 9.5 RCE unpatched on 26.7 and below "
  "&middot; PgBouncer SCRAM bypass, 1.17.0&ndash;1.26.0, zero CPE rows "
  "&middot; " + str(ef["today_rows"]) + " cutovers land today</span></div>")
html, n = re.subn(r'<div class="runbar">.*?</div>(?=\s*<div)', runbar, html, count=1, flags=re.S)
assert n == 1, "runbar not replaced"
rb = re.search(r'<div class="runbar">.*?</div>(?=\s*<div)', html, re.S).group(0)
assert PAR_ED not in rb.replace("2027-01-01", ""), "parent edition survived in runbar"
assert PAR_DT not in rb, "parent date survived in runbar"
assert ED in rb and GEN in rb, "new identity missing from runbar"

html = G.write_ledger(html, led)
html = X.normalize_closing_tags(html)

# ==================================================================== guards
G.assert_ledger_identity(html, TODAY, int(ED))
G.assert_identity_consistent(html, ED, TODAY, GEN)
X.assert_not_parent_identity(html, PAR_ED, PAR_DT)
nsec = X.assert_structure(html, expect_sections=15)
ntab = G.assert_table_shape(html)
nunits = G.assert_page_link_coverage(html)
parent = json.load(open(os.path.join(SP, "parent_ledger.json")))
acc = ("events", "patch", "claims", "ownclaims", "promises", "benchmarks", "gaps", "retired_events")
for sec in acc:
    pks = {r["k"] for r in parent[sec]}
    nks = {r["k"] for r in led[sec]}
    al = {a for r in led[sec] for a in (r.get("aliases") or [])}
    lost = pks - nks - al
    assert not lost, "alias-unsafe: %s lost %s" % (sec, sorted(lost)[:5])

print("\n=== GUARDS ===")
print("  structure            : %d sections" % nsec)
print("  table shape          : %d tables" % ntab)
print("  link coverage        : %d cited units, 0 uncited" % nunits)
print("  alias safety         : %d accumulating sections, 0 parent keys lost" % len(acc))
print("  closing tags         : </body>=%d </html>=%d" % (html.count("</body>"), html.count("</html>")))
out = os.path.join(SP, "oracle-lens-108.html")
open(out, "w", encoding="utf-8").write(html)
pb = len(open(PARENT, encoding="utf-8").read().encode())
print("  bytes                : %d (parent %d, delta %+d)" % (len(html.encode()), pb, len(html.encode()) - pb))
print("wrote", out)
