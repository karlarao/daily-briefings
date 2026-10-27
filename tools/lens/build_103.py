"""Edition 103 lens assembler. HTML blocks are built by CONCATENATION, never
%-formatting: ledger prose carries literal % signs (the 09-17/09-20 rule)."""
import json, re, sys, datetime
sys.path.insert(0, 'tools/lens')
import lens_guard as G, lens_extra as X, lens_links as LL
import patch_radar as PR, events_table as ET, longitudinal as LG, ledger_surgery as LS

TODAY = "2026-10-25"; GEN = "2026-10-25 09:10 EDT"; ED = "103"
T0 = datetime.date.fromisoformat(TODAY)
PARENT_ED, PARENT_DATE = "102", "2026-10-24"

L = json.load(open('lens/ledger_103.json'))
PAR = json.load(open('lens/parent_ledger.json'))
LONG = json.load(open('lens/longi.json'))
ser, stats = LONG['series'], LONG['stats']
shown_keys = json.load(open('lens/shown_keys.json'))
CAPINFO = json.load(open('lens/capinfo.json'))
corpus = LL.mine_briefs('tools/ledger/briefs')
print("mined %d primary links from today's briefs" % len(corpus))

html = open('lens/index.html', encoding='utf-8').read()
html = G.strip_host_wrapper(html)
G.assert_parent_fresh(PAR, expect_date=PARENT_DATE)
print("guard 1: parent fresh (edition %s / %s)" % (PAR.get('edition'), PAR.get('date')))

def C(row, url=None):
    return LL.cite(url or row.get('url'), row.get('last_seen'), row.get('first_seen'), TODAY, today=TODAY)
def CB(title, *dates):
    return LL.cite(LL.find_url(title, corpus), *(dates or (TODAY,)), today=TODAY)

ef = ET.facts(L['events'], TODAY)
nofix = PR.count_no_fix(L['patch'])
shown = [r for r in L['patch'] if r['k'] in set(shown_keys)]
shown.sort(key=lambda r: PR.rank(r, T0))

# ---------------------------------------------------------------- v-events
LANE = {'oracle':'Oracle','snowflake':'Snowflake','databricks':'Databricks','bigquery':'BigQuery',
        'redshift':'Redshift','fabric':'Fabric','mongodb':'MongoDB','oltp':'OLTP','formats':'Formats',
        'appdev':'App Dev','devops':'DevOps','frontend':'Frontend','mobile':'Mobile','aidaily':'AI Daily',
        'aiappdev':'AI App Dev','aihw':'AI HW','dbhw':'DB HW','challengers':'Challengers','nl2sql':'NL2SQL'}
def _lane(r):
    k=(r.get('k') or '').lower(); t=(r.get('t') or '').lower()
    for key,lab in LANE.items():
        if key in k or key in t[:160]: return lab
    return r.get('lane') or '&mdash;'
lane_of = {r['k']: _lane(r) for r in L['events']}
act_of  = {r['k']: (r.get('act') or '&mdash;') for r in L['events']}
ev_tbl, ev_shown = ET.render(L['events'], TODAY, horizon=60, lane_of=lane_of, act_of=act_of)
ev_body = (
 "<p class='lede'>" + str(ef['total']) + " dated and undated items on the board: <b>" + str(ef['inside14'])
 + " fall inside fourteen days</b>, " + str(ef['inside7']) + " inside seven, " + str(ef['undated'])
 + " are deliberately undated because the vendor published no day, and " + str(ef['beyond30'])
 + " sit beyond thirty. <b>Nothing retired today</b> &mdash; no dated row fell past. " + CB("deadline wall") + "</p>"
 + "<p><b>The 26 Oct &ndash; 8 Nov wall is the densest this board has carried, and almost none of it is a "
 + "CVE.</b> " + str(ef['inside7']) + " rows land inside seven days alone: Snowflake flips agent "
 + "<code>dashboard_data_access</code> to TRUE <b>tomorrow</b>, Chrome removes the emSign root on the 27th, "
 + "Kubernetes 1.34 EOLs the same day, Node 26 becomes LTS on the 28th, BigQuery meters TabFM and Fabric "
 + "stops accepting legacy pipeline activities on the 30th, and on the 31st Redshift enforces TLS 1.2, "
 + "Databricks sunsets the Beta Genie MCP endpoint and MongoDB Atlas stops accepting new log-export "
 + "configurations. Every one needs a client-side change and they land on different teams. "
 + CB("dated cutovers") + "</p>"
 + "<p><b>One of them is a credential change disguised as a URL change, which is the kind of detail a "
 + "migration plan misses.</b> The Genie MCP sunset moves the endpoint to "
 + "<code>system.ai.genie_one_mcp</code> <i>and</i> changes the OAuth scope from <code>genie</code> to "
 + "<code>ai-gateway</code> &mdash; a <code>genie</code>-scoped token cannot call the replacement, so every "
 + "integration needs a re-authorization pass, not a config edit. Seven days later Databricks removes the "
 + "account- and workspace-level toggle for partner-powered AI features: whatever your workspace is set to "
 + "on 1 Nov is what it keeps, and changing it afterwards requires an account-team request. "
 + CB("Genie MCP endpoint sunset") + "</p>"
 + ev_tbl)

# ---------------------------------------------------------------- v-patch
rows_html = ["<table class='tbl'><thead><tr><th>Due / fix status</th><th>Item</th><th>Src</th></tr></thead><tbody>"]
for r in shown:
    rows_html.append("<tr><td>" + (r.get('due') or '&mdash;') + "</td><td>" + (r.get('t') or '')
                     + "</td><td>" + C(r) + "</td></tr>")
rows_html.append("</tbody></table>")
patch_body = (
 "<p class='lede'>The register holds <b>" + str(nofix) + " rows with no reachable fix</b> out of "
 + str(len(L['patch'])) + " tracked; <b>" + str(len(shown)) + "</b> are rendered here and the rest stay in "
 + "the embedded ledger. Today's shape is the sharpest version of that the board has seen: "
 + "<b>MongoDB merged 48 fixes onto a branch and never cut the release</b>, <b>no JDK vendor has shipped a "
 + "build for a CVSS 9.1 published yesterday</b>, and <b>Apache Doris archived a branch with a live "
 + "authorization bypass on it</b>. " + CB("no reachable fix") + "</p>"
 + "<p><b>A correction to this section's own reasoning, which matters more than any single row.</b> The cap "
 + "move in ed. 102 went from 30 to 35 on the stated ground that &ldquo;band 0 &mdash; CISA KEV &mdash; alone "
 + "holds 21 rows&rdquo;. <b>Band 0 is not the KEV set.</b> <code>sev_tier</code> returns 0 for any row "
 + "asserting a CVSS of 9.0 or above anywhere in its text, and measured against the parent ledger that is "
 + "<b>65 of 201 rows</b> &mdash; today <b>" + str(CAPINFO['band0_today']) + " of "
 + str(len(L['patch'])) + "</b>, the single addition being the new JDK row, which legitimately asserts 9.1. "
 + "So <code>|band0 &cup; must-show|</code> is <b>85</b> and was always about 84; applying the 10-24 rule "
 + "literally would render 85 of " + str(len(L['patch'])) + " rows, which is a list, not a radar. <b>The cap "
 + "therefore stays at 35 and the rule's own escape clause applies &mdash; raise it to exactly that union, "
 + "or not at all.</b> The force-include added on 10-24 is what makes this safe: "
 + "<code>select()</code> guarantees all " + str(CAPINFO['must']) + " must-show rows and fills the remainder "
 + "by rank, and it satisfies the assertion even at a cap of 30. " + G.archive_link(TODAY) + "</p>"
 + "<p><b>Two carried rows were corrected in ways that change what a reader does.</b> The Snowflake OCSP "
 + "row said scanner blindness on those driver CVEs had closed &mdash; it closed for CVE-2026-86597 only, "
 + "and <b>the half still open is the higher-scoring bug</b>: CVE-2026-85525 (7.4, "
 + "<code>technicalImpact: total</code>) has no GHSA, no <code>GO-</code> and no <code>PYSEC</code> record in "
 + "OSV at all. And the Vitess row said six advisories; <b>October carried 17, of which 16 return 404 from "
 + "OSV</b> &mdash; the one that is indexed is the lowest-impact item in the set. "
 + CB("Vitess GHSA advisories") + "</p>"
 + "".join(rows_html))

# ---------------------------------------------------------------- v-longitudinal
prior = [r for r in ser if r['date'] < TODAY]
cur = ser[-1]
hi_items = max(prior, key=lambda r: r['items'])
urg = [r['urgent'] for r in ser[-8:]]
run8 = ", ".join(str(u) for u in urg)
urg_max = max(r['urgent'] for r in ser)
prior_urg = max(r['urgent'] for r in prior)
mean14 = sum(r['urgent'] for r in ser[-14:]) / min(14, len(ser))
assert cur['urgent'] == 16 and prior_urg == 17, (cur['urgent'], prior_urg)
lt = ["<table class='tbl'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th><th>Competitors</th>"
      "<th>DB HW</th><th>High</th><th>Urgent lanes</th></tr></thead><tbody>"]
for r in ser[-16:]:
    lt.append("<tr><td>" + r['date'] + "</td><td>" + str(r['items']) + "</td><td>" + str(r.get('oracle',0))
              + "</td><td>" + str(r.get('comp',0)) + "</td><td>" + str(r.get('dbhw',0)) + "</td><td>"
              + str(r.get('high',0)) + "</td><td>" + str(r['urgent']) + "</td></tr>")
lt.append("</tbody></table>")
longi_body = (
 "<p class='lede'>" + str(len(ser)) + " days of public ledger. Today: <b>" + str(cur['items'])
 + " items</b> across 19 lanes and <b>" + str(cur['urgent']) + " urgent lanes</b> &mdash; one below "
 + "yesterday's series high of " + str(prior_urg) + ", <b>not a new record</b>. The last eight runs read "
 + run8 + ", mean " + ("%.1f" % mean14) + " over fourteen days. The series high for items excluding today "
 + "is " + str(hi_items['items']) + " on " + hi_items['date'] + ". " + CB("longitudinal") + "</p>"
 + "<p><b>" + str(cur['urgent']) + " of 19 lanes flagged, audited one at a time, and all sixteen survive "
 + "the definition applied literally &mdash; but the count overstates the day's breadth and the summary "
 + "should say so.</b> Four KEV clocks are past due (Oracle at 59 days with "
 + "<code>forensicTriage: Yes</code>, <b>Ray at 66</b>, LiteLLM at 39, Apple at 12 with no fix for the "
 + "iOS 18.7.x train), eleven lanes carry a fix their population cannot reach, and " + str(ef['inside14'])
 + " dated rows fall inside fourteen days. <b>But one root cause accounts for five of the sixteen</b>: the "
 + "eMudhra CA key compromise reaches Oracle, App Dev, DevOps, Mobile and AI Daily as five different "
 + "remediations of one disclosure, and litellm is shared by AI Daily and AI App Dev. <b>Sixteen flags cover "
 + "roughly eleven distinct stories. Counting lanes is not counting problems.</b> " + CB("flag calibration") + "</p>"
 + "<p><b>The three <code>ok</code> lanes are the discrimination evidence, and each declined in writing.</b> "
 + "Database Hardware reported a month with <b>no CVE at all</b> rather than padding, for a second "
 + "consecutive run. Open Formats declined the Hudi VARIANT corruption on the ground that <b>a mitigation is "
 + "in force by default</b> &mdash; the durable damage needs the non-default Spark record merger, while the "
 + "default Avro merger is correct and Merge-on-Read fails loudly. BigQuery established that "
 + "CVE-2026-111943 <b>is not a BigQuery CVE at all</b>: GCP-2026-071 lists 19 affected products and "
 + "BigQuery, the <code>bq</code> CLI, the drivers and the client libraries appear in none of them. "
 + CB("ok lanes") + "</p>"
 + "<p>The High column is still <b>not comparable across days</b>: each run re-derives the severity "
 + "heuristic from the title rather than reading a stored value, so a shift there is a classifier change and "
 + "not a change in the world. <b>Today gave that limitation a second, sharper demonstration &mdash; this "
 + "time in the Patch Radar's own ranking rather than in this table.</b> The cap move in ed. 102 was justified by "
 + "reporting band 0 at 21 rows; band 0 is <code>CVSS &ge; 9.0</code>, not CISA KEV, and the parent ledger "
 + "already held 65. A mislabelled band is the same failure as an unstored severity: the number is real, the "
 + "thing it names is not what the prose says. Also structural for a third consecutive run: <b>18 of 21 "
 + "<code>changed</code> rows on the dashboard were classifier artifacts</b>, reading &ldquo;urgent &rarr; "
 + "normal&rdquo; because the research agents reworded a carried headline while the fact sat still. Three "
 + "real movements survived. " + G.archive_link(TODAY) + "</p>"
 + "".join(lt))

# ---------------------------------------------------------------- v-wn (shared)
def li(txt, src): return "<li>" + txt + " " + src + "</li>"
wn_body = (
 "<p class='lede'>Edition " + ED + " against edition " + PARENT_ED + ". <b>Four rows enter the board, one "
 + "new event, eleven carried rows corrected or enriched, and nothing retired.</b> Five of today's apparent "
 + "corrections turned out to be corrections to this run's own prompt rather than to the ledger &mdash; "
 + "which is itself the finding. " + CB("since yesterday") + "</p>"
 + "<h3>&#127381; New on the board</h3><ul>"
 + li("<b>A CVSS 9.1 published yesterday affects every supported JDK line and no vendor build carries the "
     "fix</b> &mdash; CVE-2026-114820 (<code>javax.net.ssl</code>) hits JDK 8, 11, 17, 21, 25 and 27, and "
     "Temurin's and Corretto's newest GA builds all predate the advisory. The interim remedy is four "
     "<code>keytool -delete</code> calls, including <code>comodoaaaca</code> &mdash; because the "
     "intermediates were cross-signed by Sectigo into AAA Certificate Services, so removing the emSign roots "
     "alone leaves a valid path. On Debian/Ubuntu <code>apt upgrade</code> is documented not to work.",
     CB("CVE-2026-114820 JDK javax.net.ssl"))
 + li("<b><code>python -m venv</code> still installs a pip whose vendored certifi trusts the compromised "
     "root</b> on every CPython from 3.9 to 3.12, and <b>3.9 has no reachable fix at all</b>. Updating the OS "
     "trust store does not help: pip <i>unions</i> vendored certifi into the truststore context, and pip "
     "23.0.1 vendors no truststore at all. Python 3.15.0, GA 16 days ago, shipped a compromised-root pip.",
     CB("pip ensurepip certifi emSign"))
 + li("<b>Kubernetes merged the CA fix into all four release branches and released none of them</b> &mdash; "
     "the October patch round is 12 days past target on 1.34, 1.35, 1.36 and 1.37 simultaneously, 1.34 EOLs "
     "in two days, and the next window falls fourteen days after that EOL.",
     CB("Kubernetes October patch overdue"))
 + li("<b>A CISA KEV entry on the runtime most GPU clusters run went 66 days past due</b> &mdash; Ray "
     "CVE-2025-62593, DNS-rebinding to RCE on the head node, <code>forensicTriage: Yes</code>, fixed in "
     "<code>ray 2.52.0</code>. Finding it corrected a negative result this board shipped yesterday.",
     CB("Ray CVE-2025-62593 CISA KEV"))
 + "</ul><h3>&#128314; Corrections</h3><ul>"
 + li("<b>The eMudhra &ldquo;seven-point vendor disagreement&rdquo; was two different CVEs in two different "
     "TLS stacks.</b> CVE-2026-111943 is Go's <code>crypto/x509</code> record (Red Hat 6.8, "
     "<code>AC:H/UI:R</code>, rated <b>Important</b> not Medium; <b>NVD carries no score at all</b>); "
     "Oracle's are CVE-2026-91403 and CVE-2026-114820 against JSSE at 9.1 with <code>AC:L/UI:N</code>. The "
     "gap is entirely in the vector. Three lanes tried to reconcile a disagreement that does not exist.",
     CB("CVE-2026-111943 Red Hat"))
 + li("<b>Snowflake's scanner blindness only HALF closed, and the open half is the higher-scoring bug.</b> "
     "GHSA-qqj6-54q6-cxv6 now resolves across four ecosystems, but <b>CVE-2026-85525 has no GHSA, no "
     "<code>GO-</code> and no <code>PYSEC</code> record anywhere in OSV</b> &mdash; so scanners surface the "
     "6.5 log-leak and miss the 7.4 revocation bypass. Worse sequel: 27 days after that fix, Snowflake turned "
     "OCSP checking <b>off by default across six drivers in 24 days</b>, and the old fail-close settings are "
     "now accepted-but-ignored.", CB("Snowflake CVE-2026-85525 OCSP"))
 + li("<b>Vitess disclosed 17 advisories in October, not six, and 16 of them are invisible.</b> Queried one "
     "id at a time, sixteen return 404 from OSV; the only indexed one is the lowest-impact item. Ten of the "
     "sixteen are High-severity SQL injection in the query path, including comment-splitting that hides SQL "
     "from <i>ACL checks</i>.", CB("Vitess GHSA advisories OSV"))
 + li("<b>Angular's two SSR packages have different ceilings, so a single &ldquo;&le;19.2.25&rdquo; rule "
     "under-reports.</b> Three advisories cap <code>@angular/platform-server</code> at 19.2.25; "
     "CVE-2026-104871 caps <b><code>@angular/ssr</code> at 19.2.27</b>. Four in-window advisories, zero 19.x "
     "releases in the repo.", CB("Angular platform-server ssr advisories"))
 + li("<b>Fabric's CVE-2026-63509 score gap is the Scope metric, not an aggregator error.</b> MSRC publishes "
     "9.9 with <code>S:C</code>; NVD publishes 8.8 with <code>S:U</code> and <b>re-analyzed the record on "
     "2026-10-18</b>, so it is a deliberate judgement. Microsoft is authoritative on scope. A policy reading "
     "NVD rates this High, not Critical.", CB("CVE-2026-63509 MSRC NVD"))
 + "</ul><h3>&#10160; Still standing</h3><ul>"
 + li("<b>" + str(nofix) + " rows carry no reachable fix</b> &mdash; MongoDB's unreleased 8.2.13 with 48 "
     "fixes tagged to it, Doris 3.1 archived with the CVE live, Azure's PgBouncer pinned at 1.25.2, pgvector "
     "0.8.7 on zero of seven managed providers at 24 days, Angular &le;19 and Nuxt 3 permanently unfixed, "
     "Argo CD 2.x&ndash;3.2 never to be patched, and gosnowflake v1 fixable only by changing import path.",
     CB("no reachable fix"))
 + li("<b>" + str(ef['inside14']) + " dated rows fall inside fourteen days</b>, " + str(ef['inside7'])
     + " of them inside seven, and the 26 Oct &ndash; 8 Nov cluster is almost entirely data platforms and "
     "runtime lifecycle rather than CVEs.", CB("dated cutovers"))
 + li("<b>Severity has migrated out of advisory databases into release notes and mailing lists.</b> A CVSS "
     "9.5 React RCE is still unindexed after 11 days with no CVE; CockroachDB's 8.8 and 7.8 have no CVE ids; "
     "three containerd advisories have none and 404 from OSV; Mongoose patched four lines with no advisory; "
     "litellm's only machine-readable record is an <i>amended</i> March <code>MAL-</code> entry. A "
     "no-Criticals gate passed through all of it.", CB("scanner blindness"))
 + "</ul>")

# ---------------------------------------------------------------- v-read, per chair
READ = {}
common_tail = (
 "<p><b>Where to spend today's attention.</b></p><ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; " + str(nofix) + " no-reachable-fix rows, four KEV clocks past due, "
     "and a correction to the cap reasoning shipped in ed. 102.", G.archive_link(TODAY))
 + li("<b>Event Horizon</b> &mdash; " + str(ef['inside14']) + " rows inside fourteen days, "
     + str(ef['inside7']) + " inside seven, nothing retired.", G.archive_link(TODAY))
 + li("<b>Since yesterday</b> &mdash; four new rows, one new event, eleven corrections, and five "
     "&ldquo;corrections&rdquo; that turned out to be against our own prompt.", G.archive_link(TODAY))
 + "</ul>")

READ['oracle'] = (
 "<p class='lede'><b>Edition 103.</b> One certificate-authority key compromise is still reorganising every "
 "group, and the mechanism is now known precisely enough to take into a room: the eight eMudhra "
 "intermediates are <b>P-384 keys whose private scalars are all below 256</b> &mdash; trivially recoverable "
 "from the certificates &mdash; all minted in a single 2025-04-30 ceremony. <b>No Certificate Transparency "
 "entries exist for them</b>, so a CT-enforcing browser could never have been attacked and this is "
 "disproportionately a <i>backend</i> problem: service-to-service TLS, curl and language-runtime HTTP "
 "clients carry the whole risk. " + CB("eMudhra CA compromise") + "</p>"
 "<p><b>Our own position got worse in a specific and avoidable way: we shipped two out-of-band alerts four "
 "days apart, and the second one's affected builds are the first one's fix builds.</b> CVE-2026-91403 "
 "(21 Oct, 9.1) distrusts the compromised intermediates; CVE-2026-114820 (24 Oct, 9.1, same component, same "
 "vector) removes the roots and affects exactly the <code>-b32</code> / <code>.0.2</code> builds that "
 "remediate the first. Three Java patch events in five days. A customer who followed our 21 October alert "
 "to the letter is exposed again, and the only way they learn that is by reading a second alert. "
 + CB("Oracle Security Alert CVE-2026-114820") + "</p>"
 "<p><b>And we are the outlier on scoring, in a way that is now documented rather than suspected.</b> "
 "CVE-2026-75803 appears in our own October CPU with <b>four different scores</b> &mdash; 9.8 "
 "(RDBMS/OpenSSL), 9.1 (AHF), 9.1 (BI EE) and 6.2 (RDBMS/Python) &mdash; against NVD's 9.1, and <b>21c "
 "appears only in the 6.2 row</b>, so &ldquo;are we affected?&rdquo; depends which component row a reader "
 "lands on. Our 9.8 adds an <code>A:H</code> nobody else assigns. Set that beside <b>CVE-2026-21962 at 59 "
 "days past its KEV due date with <code>forensicTriage: Yes</code></b>, absent from the October CPU because "
 "the fix has existed since <i>January</i>, and the pattern a customer can name is that our publication is "
 "harder to act on than a competitor's silence. " + CB("CVE-2026-75803") + "</p>"
 "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question "
 "Forecast, Gap Ledger, Benchmark Scoreboard, Promise Tracker, Perf Signals, Build Radar, Skills Radar and "
 "Vendor Dossiers <b>carry forward from edition " + PARENT_ED + " unrevised</b>: no competitor shipped a "
 "perf or price claim worth a card today and <code>claims[]</code> did not grow, so the depth went into the "
 "correction pass and the security movement, which is where the day was. " + G.archive_link(TODAY) + "</p>"
 + common_tail)

READ['snowflake'] = (
 "<p class='lede'><b>Edition 103 &mdash; Snowflake chair (SIMULATED).</b> Our worst item lands "
 "<b>tomorrow</b> and it is an access default, not a bug: on <b>2026-10-26 agents begin defaulting to "
 "<code>dashboard_data_access: TRUE</code></b>, so an agent answering a dashboard question can query the "
 "<b>whole underlying tables</b> rather than the columns the tiles show, bounded only by the asking user's "
 "role. <code>DESCRIBE AGENT</code> will not show the property on an agent that never set it, yet it still "
 "resolves TRUE, and the opt-out is a full specification replace so omitted fields are silently dropped. "
 "<b>It is not in a bundle</b>, so a bundle-based change process misses it entirely. "
 + CB("dashboard_data_access") + "</p>"
 "<p><b>Where we are most exposed to scrutiny today, and it is our own sequencing.</b> We shipped the fix "
 "for an OCSP <i>validation bypass</i> on 3 September &mdash; and then, 27 days later, <b>turned OCSP "
 "revocation checking off by default across six drivers in 24 days</b>: Go 2.3.0, JDBC 4.4.0, Node 3.4.0 and "
 "ODBC 4.0.0 on 09-30, ODBC 3.22.0 on 10-23, with Python 5.1.0 removing <code>OCSP_MODE</code> outright. "
 "The sharp part is that <b>the old hardening settings are now accepted but ignored</b> "
 "(<code>disableOCSPChecks=false</code>, <code>insecureMode=false</code>, "
 "<code>DisableOCSPCheck=false</code>), and ODBC 4.x ships its CRL replacement <code>DISABLED</code> &mdash; "
 "so a customer running fail-close drops silently to no revocation checking on upgrade, with a log warning "
 "as the only signal. " + CB("Snowflake OCSP configuration") + "</p>"
 "<p>And a credit we should claim carefully rather than overclaim: the scanner-blindness story on our driver "
 "CVEs is <b>half</b> closed. GHSA-qqj6-54q6-cxv6 now resolves across PyPI, npm, Maven and both Go module "
 "paths &mdash; real progress &mdash; but <b>CVE-2026-85525, the higher-scoring one, has no GHSA, no "
 "<code>GO-</code> and no <code>PYSEC</code> record at all</b>, so every lockfile scanner still misses it. "
 "Saying &ldquo;it's fixed&rdquo; invites the customer to discover that themselves. "
 + CB("Snowflake CVE-2026-86597 GHSA") + "</p>" + common_tail)

READ['databricks'] = (
 "<p class='lede'><b>Edition 103 &mdash; Databricks chair (SIMULATED).</b> Two dated cutovers inside seven "
 "days and the first one is a <b>credential</b> change we are describing as an endpoint change. The Beta "
 "Genie MCP endpoint sunsets <b>2026-10-31</b>, and migrating is not a URL swap: the OAuth scope moves from "
 "<code>genie</code> to <code>ai-gateway</code>, so a <code>genie</code>-scoped token cannot call the "
 "replacement. Every integration needs a re-issued credential before the 31st. "
 + CB("Genie MCP endpoint sunset") + "</p>"
 "<p><b>Seven days after that we take away a self-service control, which is the one customers will "
 "remember.</b> On <b>2026-11-01</b> the account- and workspace-level toggle for partner-powered AI features "
 "is removed; each workspace keeps whatever it is set to, and changing it afterwards <b>requires contacting "
 "the account team</b>. That is the last self-service window, and we have not framed it that way. "
 + CB("partner-powered AI features toggle") + "</p>"
 "<p><b>The governance asymmetry worth stopping defending: everything with a date is moving inside Unity "
 "Gateway, and everything outside it has no date.</b> Genie MCP has a hard sunset because its replacement "
 "lives in the Gateway; <code>/api/2.0/mcp/sql</code>, AI Search MCP and UC-functions MCP carry <b>no "
 "sunset date at all</b> &mdash; re-verified against the primary doc today, so there is no invented date to "
 "plan against. Add consumer access to Unity Gateway going GA with its own cost warning, jailbreak "
 "screening of MCP tool results entering Beta <i>after</i> the write-capable surface shipped, and managed "
 "MCP Services heading to GA with <b>read and write enabled by default</b>, and the honest description is a "
 "consolidation onto one policy, audit and billing chokepoint whose cost to the customer is a forced "
 "credential re-issue. " + CB("Databricks managed MCP") + "</p>" + common_tail)

READ['bigquery'] = (
 "<p class='lede'><b>Edition 103 &mdash; BigQuery chair (SIMULATED).</b> Our best result today is a "
 "negative one we should state plainly rather than let a customer infer: <b>CVE-2026-111943 is not a "
 "BigQuery CVE.</b> GCP-2026-071 lists 19 affected products and BigQuery, the <code>bq</code> CLI, the "
 "JDBC/ODBC drivers and the client libraries appear in <b>none</b> of them. But the remediation is still the "
 "customer's: the CVE resolves to <b>GO-2026-6809</b> plus three RUSTSEC advisories, so if their BigQuery "
 "access path is a Go or Rust binary &mdash; a client library, a Storage Write API ingester, a Beam Go "
 "pipeline &mdash; the fix arrives only when <i>they</i> rebuild. No managed-fleet rollout reaches a binary "
 "they ship. " + CB("GCP-2026-071") + "</p>"
 "<p><b>The thing that can silently change query results is ours and it is a one-flag, org-wide switch.</b> "
 "Reusable column aliases went GA 2026-10-15, off by default, enabled only by <code>ALTER PROJECT</code> or "
 "the organization equivalent &mdash; and turning it on changes resolution order so an alias <b>shadows an "
 "outer query column, a UDF argument or a script variable</b>. Our own documentation shows a correlated "
 "subquery returning a constant and <b>a UDF returning 15 instead of 110</b>. There is no session-level "
 "<code>SET</code> and no per-dataset opt-in: one admin statement changes name resolution for every existing "
 "query in the project. " + CB("reusable column aliases") + "</p>"
 "<p><b>And on 2026-10-30, five days out, TabFM moves to per-token billing &mdash; with nothing we ship "
 "able to cap it.</b> <code>AI.PREDICT</code> sits under <i>Predictive</i> AI functions, a category separate "
 "from the <i>Generative</i> functions the daily token quotas cover, and custom query quotas meter bytes on "
 "on-demand pricing only, so an Enterprise reservation has no instrument at all. The detail a customer finds "
 "before we do: the billing formula multiplies by <code>n_ensembles</code>, which is <b>not an "
 "<code>AI.PREDICT</code> argument</b> and is documented nowhere. <b>They cannot compute their own charge "
 "from our published API.</b> " + CB("TabFM token pricing") + "</p>" + common_tail)
SEC = {'v-events': ev_body, 'v-patch': patch_body, 'v-longitudinal': longi_body,
       'v-wn': wn_body, 'v-read': READ['oracle']}
chips = {'v-read': "edition " + ED + " &middot; " + TODAY,
         'v-wn': "vs edition " + PARENT_ED,
         'v-events': str(ef['total']) + " rows &middot; " + str(ef['inside14']) + " inside 14d",
         'v-patch': str(len(shown)) + " of " + str(len(L['patch'])) + " &middot; " + str(nofix) + " no fix",
         'v-longitudinal': str(len(ser)) + " days"}
html = G.splice_sections(html, SEC, chips=chips, expect=15)
print("spliced %d sections (of 15 visited)" % len(SEC))

m = re.search(r'(<script type="application/json" id="povContent">)(.*?)(</script>)', html, re.S)
P = json.loads(m.group(2))
for ch in ('oracle','snowflake','databricks','bigquery'):
    P['content'][ch]['v-read'] = {'t': "Today's Read", 'e': 'PINNED',
                                  'c': "edition " + ED + " &middot; " + TODAY, 'h': READ[ch]}
html = html[:m.start(2)] + json.dumps(P) + html[m.end(2):]
print("povContent: v-read refreshed for all 4 chairs")

navmeta = {'v-read': "edition " + ED + " &middot; " + TODAY,
           'v-wn': "vs edition " + PARENT_ED,
           'v-events': str(ef['total']) + " rows &middot; " + str(ef['inside14']) + " inside 14d",
           'v-patch': str(len(shown)) + " shown &middot; " + str(nofix) + " no fix",
           'v-longitudinal': str(len(ser)) + " days",
           'v-claims': str(len(L['claims'])) + " tracked &middot; carried from " + PARENT_ED,
           'v-mirror': str(len(L['ownclaims'])) + " own claims &middot; carried from " + PARENT_ED,
           'v-gaps': str(len(L['gaps'])) + " open &middot; carried from " + PARENT_ED,
           'v-bench': str(len(L['benchmarks'])) + " audited &middot; carried from " + PARENT_ED,
           'v-promises': str(len(L['promises'])) + " rows &middot; carried from " + PARENT_ED,
           'v-build': str(len(L['buildbets'])) + " bets &middot; carried from " + PARENT_ED,
           'v-skills': str(len(L['skills'])) + " bets &middot; re-rank 2027-01-01"}
html = G.refresh_nav(html, navmeta)
html = X.rewrite_pov_meta(html, navmeta)
print("nav + povContent meta driven from len(ledger[section])")

html = G.rewrite_identity(html, ED, TODAY, GEN)
rb = re.search(r'<div class="runbar">.*?</div>\s*(?=<div)', html, re.S)
if not rb: raise SystemExit("runbar not found")
flag = ("&#9873; JDK 9.1 published 10-24 with NO vendor build &mdash; keytool is the only remedy &middot; litellm 1.107.0 images carry a VALID old-key cosign signature &middot; emSign root leaves Chrome 27 Oct &middot; K8s 1.34 EOL 27 Oct, Oct patch 12d late on all 4 branches &middot; Ray KEV 66d overdue &middot; CVE-2026-21962 59d past KEV")
newrb = ('<div class="runbar">'
 '<span class="lbl">Edition</span><span class="val">' + ED + '</span>'
 '<span class="lbl">Generated</span><span class="val">' + GEN + '</span>'
 '<span class="lbl">Model</span><span class="val">claude-opus-5</span>'
 '<span class="lbl">Inputs</span><span class="val">19 briefs &middot; ' + str(len(ser)) + 'd ledger</span>'
 '<span class="lbl">Run tokens</span><span class="val">~3,950k</span>'
 '<span class="lbl">Skills review</span><span class="val">2027-01-01</span>'
 '<span class="flag">' + flag + '</span></div>')
html = html[:rb.start()] + newrb + html[rb.end():]
for stale in ('Edition 102', '2026-10-24 09:36 EDT', '~3,876k', '107d ledger'):
    assert stale not in newrb, stale
print("runbar rebuilt and read back clean")

html = G.write_ledger(html, G.stamp_ledger_identity(L, TODAY, int(ED)))
html = X.normalize_closing_tags(html)

# ---------------------------------------------------------------- GUARDS
G.assert_identity_consistent(html, ED, TODAY, GEN); print("guard: identity consistent across sites")
G.assert_ledger_identity(html, TODAY, int(ED));     print("guard: embedded ledger identity")
X.assert_not_parent_identity(html, PARENT_ED, PARENT_DATE); print("guard: no parent identity asserted")
print("guard: structure    %d sections" % X.assert_structure(html, 15))
print("guard: table shape  %d tables" % G.assert_table_shape(html))
print("guard 5: link coverage %d cited units" % G.assert_page_link_coverage(html))
LS.assert_alias_safe(L['patch'], PAR['patch'], 'patch')
for sec in ('claims','ownclaims','promises','benchmarks','gaps','buildbets','skills'):
    LS.assert_alias_safe(L[sec], PAR[sec], sec)
pk = {r['k'] for r in PAR['events']}
nk = {r['k'] for r in L['events']} | {r['k'] for r in L['retired_events']}
lost = pk - nk
if lost: raise SystemExit("events lost by omission: %s" % sorted(lost))
print("guard: alias-safe across 8 accumulating sections; 0 event keys lost")
print("closing pairs: </body>=%d </html>=%d" % (html.count('</body>'), html.count('</html>')))
open('lens/out_103.html','w',encoding='utf-8').write(html)
par_sz = len(open('lens/index.html',encoding='utf-8').read())
print("\nwrote lens/out_103.html  %d bytes (parent %d, delta %+d)" % (len(html), par_sz, len(html)-par_sz))
