"""Edition 105 lens assembler. HTML blocks are built by CONCATENATION, never
%-formatting: ledger prose carries literal % signs (the 09-17/09-20 rule)."""
import json, re, sys, datetime
sys.path.insert(0, 'tools/lens')
import lens_guard as G, lens_extra as X, lens_links as LL
import patch_radar as PR, events_table as ET, longitudinal as LG, ledger_surgery as LS

TODAY = "2026-10-27"; GEN = "2026-10-27 09:42 EDT"; ED = "105"
T0 = datetime.date.fromisoformat(TODAY)
PARENT_ED, PARENT_DATE = "104", "2026-10-26"

L = json.load(open('lens/ledger_105.json'))
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
 + " fall inside fourteen days</b> and <b>" + str(ef['inside7']) + " inside seven</b> &mdash; the densest "
 + "seven-day window the board has carried. " + str(ef['undated']) + " are deliberately undated because the "
 + "vendor published no day, and " + str(ef['beyond30']) + " sit beyond thirty. One row retired: Snowflake's "
 + "CoWork dashboard-data default, which passed yesterday. " + CB("deadline wall") + "</p>"
 + "<p><b>The window opens with a KEV clock that has two days on it, and it is the only item on this table that "
 + "carries a federal remediation deadline rather than a vendor one.</b> PHP's php2shell pair "
 + "(<code>CVE-2026-109618</code>, <code>CVE-2026-109619</code>) entered CISA KEV on the 26th with remediation "
 + "due <b>2026-10-29</b> and <code>forensicTriage: Yes</code> &mdash; unauthenticated RCE as the web-worker "
 + "account, fixed only in 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12, with <b>8.1 and earlier never getting a fix</b> and "
 + "CISA's own alert instructing operators to take those systems offline. The reason it belongs on an Oracle "
 + "board: <b>the same CVE-2026-109618 is the subject of an out-of-band Oracle Security Alert</b> against Oracle "
 + "Secure Backup 19.1.0.0.0&ndash;19.1.0.1.0, which bundles PHP, and Oracle revised that alert yesterday telling "
 + "customers to patch &ldquo;without delay&rdquo;. " + CB("php2shell") + "</p>"
 + "<p><b>Today itself carries two items, and neither ships as a version you can pin.</b> Chrome removes "
 + "<code>emSign ECC Root CA - G3</code> from its trust store this morning &mdash; delivered out-of-band, so there "
 + "is no release note for a change-management process to point at &mdash; and <b>Kubernetes 1.34 reaches upstream "
 + "end of life with v1.34.13 never cut</b>. The second is the sharper one: <code>dl.k8s.io</code> still points "
 + "every supported minor at the 23 Sep builds, and the October round is uncut on 1.34, 1.35, 1.36 and 1.37 "
 + "simultaneously, fourteen days past the <code>targetDate: 2026-10-13</code> all four still advertise. "
 + CB("Kubernetes 1.34") + "</p>"
 + "<p><b>The 31st is the densest single day and every item on it is a client-side protocol or credential change, "
 + "not a version bump.</b> Redshift enforces a TLS 1.2 minimum on provisioned clusters <i>and</i> Serverless "
 + "workgroups &mdash; service-side, so a trailing maintenance track does not defer it &mdash; and the drivers you "
 + "would upgrade to in response also flip default <code>sslmode</code> to <code>verify-full</code>, which is "
 + "documented in three GitHub changelogs and <b>nowhere in AWS's behavior-changes page</b>. Databricks sunsets "
 + "the bare Genie MCP endpoint, where the OAuth scope moves from <code>genie</code> to <code>ai-gateway</code> so "
 + "an updated URL alone fails. MongoDB Atlas stops accepting new Push-Based Log Export configurations "
 + "permanently. Then 11-01 (Play target-API), 11-04 (Vitess v23.0 EOL), 11-06 (containerd 2.2, Fabric's Foundry "
 + "tool), 11-10 (.NET 8 and 9 together) and 11-12 (PostgreSQL 14). " + CB("TLS 1.2") + "</p>"
 + "<p><b>What is NOT dated here is still worth as much as what is.</b> The " + str(ef['undated']) + " undated rows "
 + "are undated because the vendor published no day, and the board has been wrong in that direction five times in "
 + "nine editions &mdash; Iceberg V4, Fabric Runtime 1.3, Snowflake 2026_07, the Fabric ODBC removal and the "
 + "Snowsight host cutover, which turned out to have <b>moved to early February 2027</b> rather than passed. "
 + "Today's confirmation holds that line: Snowflake's BCR-2413 now reads &ldquo;early February 2027, exact date to "
 + "be determined&rdquo;, and the board's 10-23 correction un-retiring it was right. " + CB("BCR-2413") + "</p>"
 + ev_tbl)

# ---------------------------------------------------------------- v-patch
rows_html = ["<table class='tbl'><thead><tr><th>Due / fix status</th><th>Item</th><th>Src</th></tr></thead><tbody>"]
for r in shown:
    rows_html.append("<tr><td>" + (r.get('due') or '&mdash;') + "</td><td>" + (r.get('t') or '')
                     + "</td><td>" + C(r) + "</td></tr>")
rows_html.append("</tbody></table>")
patch_body = (
 "<p class='lede'>The register holds <b>" + str(nofix) + " rows with no reachable fix</b> out of "
 + str(len(L['patch'])) + " tracked; <b>" + str(len(shown)) + "</b> are rendered here and the rest stay in the "
 + "embedded ledger. <b>Eight consecutive weeks of &ldquo;patched upstream, unreachable for you&rdquo; as the "
 + "dominant shape &mdash; and today it stopped being one shape. Six distinct mechanisms are live on the board "
 + "simultaneously.</b> " + CB("no reachable fix") + "</p>"
 + "<p><b>One: the fix is merged and tagged in nothing &mdash; now a two-project pattern, which is what makes it a "
 + "category.</b> <code>.go-version</code> on Kubernetes <code>release-1.34</code> through <code>-1.37</code> all "
 + "read <code>1.26.10</code> while every shipped tag carries 1.26.5 or 1.26.8, so the <code>crypto/x509</code> "
 + "fix is reachable from no downloadable artifact. containerd is in the same state and worse: nothing shipped "
 + "since 10-13, the bump is merged only on <code>release/2.4</code> and <b>unmerged on release/2.2 and the 2.3 "
 + "LTS</b> &mdash; while 2.2 EOLs on 11-06, leaving a Kubernetes 1.36 cluster exactly one supported runtime, the "
 + "LTS that has not merged the fix. <b>Strictly harder to detect than an EOL branch:</b> git looks patched, every "
 + "artifact is not, and an SBOM pipeline reports the identical posture before and after. " + CB("go-version") + "</p>"
 + "<p><b>Two: patched for paying customers only, and today the probe closed it.</b> Oracle ships the JDK 9.1 fix "
 + "on the <code>.0.3</code> train through the Patch Availability Document. The removal commit "
 + "<b>JDK-8395690</b> landed on <code>openjdk/jdk</code> mainline on 10-24 (&minus;353 lines, four cert files) and "
 + "<b>jdk21u and jdk25u still carry all four</b>, their <code>cacerts</code> untouched since 08-28. Adoptium's "
 + "newest GA builds &mdash; <code>jdk-21.0.13+9</code>, <code>jdk-25.0.5+8</code>, <code>jdk-17.0.21+9</code> "
 + "&mdash; are the affected base builds. And the two alerts finally resolve: 91403 distrusts the "
 + "<b>intermediates</b> and lists base builds; 114820 removes the <b>roots</b> and lists the <code>.0.2</code> "
 + "builds. Both &ldquo;.0.2 is fixed&rdquo; and &ldquo;.0.2 is not fixed&rdquo; were literally true. "
 + CB("no vendor build carries the fix") + "</p>"
 + "<p><b>Three: the fix exists, is reachable, and is off.</b> StarRocks' query-profile access check ships "
 + "<code>false</code> in <code>Config.java</code>, confirmed at source today, so upgrading applies nothing. "
 + "<b>Four: the fix is on the predecessors of the current major.</b> arrow-rs patched 57.3.2 / 58.4.1 / 59.3.2 "
 + "and left <b>60.0.0 &mdash; <code>max_stable_version</code>, what <code>cargo add arrow</code> gives you &mdash; "
 + "with no patch</b>; 60.1.0 was tagged 10-23 and is still not on crates.io. <b>Five: the branch is archived.</b> "
 + "Apache Doris 3.1, whose download page says archived branches &ldquo;receive no further releases of any kind, "
 + "security patches included&rdquo;. <b>Six: the dependent ecosystem forbids the fixed line.</b> Snowflake's CA "
 + "distrust shipped only in Python connector 5.1.0 and ODBC 4.2.0, while Snowpark, ML, SQLAlchemy and the CLI all "
 + "require <code>&lt; 5.0.0</code> &mdash; and 4.8.1, five days later, carries only a certifi bump. "
 + CB("disabled by default") + "</p>"
 + "<p><b>Beneath all six sits a seventh problem that is not about patching at all: the advisory a scanner reads "
 + "may never have been published.</b> React's unauthenticated RSC RCE (CVSS 4.0 9.5) is <b>still absent from the "
 + "GitHub Advisory Database and OSV thirteen days on</b>, so <code>npm audit</code>, Dependabot and osv-scanner "
 + "all return clean on a vulnerable tree. The mechanism is now measured rather than inferred: "
 + "<code>GHSA-frr6-h895-5pxp</code> resolves as a <b>repo-scoped</b> advisory under <code>dart-lang/sdk</code> "
 + "while the global path 404s, because <b>a repo advisory never published globally exists only under its repo "
 + "path and nothing warns you</b>. Grafana shipped fixes today for three CVE ids that exist in no public database "
 + "at all, OpenTofu's certificate filter has no GHSA, and <code>GHSA-x547-2835-q547</code> sits in "
 + "<code>unreviewed/</code> with <b>zero affected-package ranges</b>. " + CB("React RSC") + "</p>"
 + "<p><b>The cap stays at 35 and the ed. 103 reasoning held on re-measurement.</b> <code>sev_tier</code>'s band 0 "
 + "is &ldquo;asserts CVSS &ge; 9.0 anywhere in the row&rdquo;, not the KEV set: <b>"
 + str(CAPINFO['band0']) + " of " + str(len(L['patch'])) + "</b> rows today, so <code>|band0 &cup; must-show|</code> "
 + "is " + str(CAPINFO['union']) + " and rendering that many is a list, not a radar. <code>select()</code>'s "
 + "force-include keeps the tight cap safe: all " + str(CAPINFO['must']) + " must-show rows are present and the "
 + "remainder fills by rank. " + G.archive_link(TODAY) + "</p>"
 + "".join(rows_html))

# ---------------------------------------------------------------- v-longitudinal
prior = [r for r in ser if r['date'] < TODAY]
cur = ser[-1]
hi_items = max(prior, key=lambda r: r['items'])
urg = [r['urgent'] for r in ser[-8:]]
run8 = ", ".join(str(u) for u in urg)
prior_urg = max(r['urgent'] for r in prior)
prior_urg_date = max(prior, key=lambda r: r['urgent'])['date']
mean14 = sum(r['urgent'] for r in ser[-14:]) / min(14, len(ser))
ties = sum(1 for r in prior if r['urgent'] == cur['urgent'])
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
 + " items</b> across 19 lanes and <b>" + str(cur['urgent']) + " urgent lanes</b> &mdash; one below the series "
 + "high of " + str(prior_urg) + " set on " + prior_urg_date + ", tied with " + str(ties) + " prior days, so "
 + "<b>not a record</b>. The last eight runs read " + run8 + ", mean " + ("%.2f" % mean14)
 + " over fourteen days. Series high for items excluding today is " + str(hi_items['items']) + " on "
 + hi_items['date'] + ". " + CB("longitudinal") + "</p>"
 + "<p><b>" + str(cur['urgent']) + " of 19 lanes flagged, audited one at a time, and all sixteen survive the "
 + "definition applied literally &mdash; and unlike yesterday the flags are not collapsing onto a few root "
 + "causes: sixteen flags cover <b>fourteen distinct stories</b>, against roughly eleven yesterday.</b> Only two "
 + "are shared: <code>postgres-mcp</code>'s CVE-2026-85620 reaches NL2SQL and AI App Dev, and PHP's "
 + "CVE-2026-109618 reaches App Dev and Oracle &mdash; the second of those only because Oracle Secure Backup "
 + "bundles PHP, which is a genuine second remediation rather than a duplicate. Four KEV clocks are past due: "
 + "<b>Ray at 68 days</b> with <code>forensicTriage: Yes</code>, Oracle's CVE-2026-21962 at <b>61</b> with a fix "
 + "that has existed since the January CPU, Apple's exploited CoreGraphics bug at 14 &mdash; which finally got an "
 + "iOS 18.7.11 backport yesterday &mdash; and php2shell with <b>two days left</b>. " + str(ef['inside14'])
 + " dated rows fall inside fourteen days. " + CB("flag calibration") + "</p>"
 + "<p><b>The three <code>ok</code> lanes are the discrimination evidence and each declined in writing.</b> "
 + "Database Hardware reported a month with <b>one Medium firmware CVE</b>, patched on every branch including both "
 + "LTS trains, and spent its budget settling a carried question instead: the 4Q26 DRAM contract figure is "
 + "<b>+10&ndash;15% QoQ</b> from TrendForce's own release, and the &ldquo;~20%&rdquo; the board had been unable to "
 + "resolve traces to an aggregator, not to TrendForce. Open Formats measured <b>zero advisories across seventeen "
 + "packages in five ecosystems</b> while four real credential-plumbing defects shipped with no CVE, GHSA or "
 + "RUSTSEC id between them &mdash; and declined the arrow-rs use-after-free on the ground that its fix is now "
 + "released on three lines. BigQuery held its server-side-fix ground for a third run and corrected the board on "
 + "the way, establishing that <b>CVE-2026-111943 is a Go <code>crypto/x509</code> advisory assigned by "
 + "<code>security@golang.org</code></b> &mdash; Oracle was never its CNA, so the &ldquo;preliminary 8.1&rdquo; the "
 + "board chased for a week was a misattribution rather than an untraceable score. " + CB("ok lanes") + "</p>"
 + "<p>The High column remains <b>not comparable across days</b>: each run re-derives the severity heuristic from "
 + "the title rather than reading a stored value, so a shift is a classifier change, not a change in the world. "
 + "Storing per-item severity in the public ledger is still the queued fix, open since 09-11. The same limitation "
 + "produced the dashboard's <code>changed</code> noise for a <b>fifth consecutive run</b>: <b>9 of 15 rows were "
 + "classifier artifacts</b> &mdash; &ldquo;remain the fix&rdquo;, &ldquo;still the one to read first&rdquo;, "
 + "&ldquo;have not moved&rdquo; &mdash; reading as severity moves because stateless agents reworded a carried "
 + "headline while the fact sat still. Six real movements survived, and one of them is a row that duplicated a "
 + "<code>new</code> pick, excluded for that reason rather than for being an artifact. "
 + G.archive_link(TODAY) + "</p>"
 + "".join(lt))

# ---------------------------------------------------------------- v-wn (shared)
def li(txt, src): return "<li>" + txt + " " + src + "</li>"
wn_body = (
 "<p class='lede'>Diffed against edition " + PARENT_ED + ". <b>One new event, three new patch rows, four "
 + "corrections and seven enrichments &mdash; and the number worth reporting is that <b>seven further rows were "
 + "drafted and redirected</b> because <code>reuse_key</code>'s advisory found them already on the board, two "
 + "under identical keys. " + G.archive_link(TODAY) + "</p>"
 + "<p><b>&#128309; New on the board (4)</b></p><ul>"
 + li("<b>PHP php2shell in CISA KEV, due 2026-10-29</b> &mdash; CVE-2026-109618 and -109619, unauthenticated RCE "
      "as the web-worker account, <code>forensicTriage: Yes</code>, fixed only in 8.2.35/8.3.36/8.4.27/8.5.12, "
      "with <b>8.1 and earlier never fixed</b> and CISA telling operators to take them offline. Three scores for "
      "one patch: the CNA says 9.2 <code>AC:H</code> for both, NVD says 9.8 <code>AC:L</code> and 8.1.",
      CB("php2shell"))
 + li("<b>LiteLLM's own pipeline signed the trojanized artifacts</b> &mdash; so <code>cosign verify</code> passes "
      "on the poisoned image against the key most deployments pin. Every post-March control held; the provenance "
      "of the build <i>input</i> was never checked. The project's own pin advice points at 1.106.2, which "
      "documents the old key.", CB("cosign"))
 + li("<b>Snowflake turned revocation checking off by default across six driver lines</b> &mdash; and the "
      "replacement ships <code>DISABLED</code>. The sequence is the finding: a CVE let a revoked certificate "
      "through, the fix repaired OCSP, the next release stopped checking revocation at all &mdash; in the month a "
      "real CA key compromise made revocation matter.", CB("revocation"))
 + li("<b>The deadline wall itself</b> &mdash; " + str(ef['inside7']) + " dated rows inside seven days, the densest "
      "window the board has carried, with 10-31 holding three independent client-side credential or protocol "
      "changes.", G.archive_link(TODAY))
 + "</ul>"
 + "<p><b>&#128260; Corrected (4)</b></p><ul>"
 + li("<b>The Kubernetes patch row asserted a &ldquo;revised 2026-10-20&rdquo; date that no primary source "
      "carries.</b> Re-measured: <code>schedule.yaml</code> still says 10-13 (14 days stale), LWKD says 11-10 "
      "with <b>no delay recorded</b>. October was folded into November, and 1.34 EOL'd today with 1.34.13 never "
      "cut.", CB("Kubernetes"))
 + li("<b>The eMudhra row was tracking one of two remediations.</b> The Go denylist fixes "
      "<code>Certificate.Verify</code> and does nothing for shelled-out <code>git</code>/<code>helm</code>/"
      "<code>kustomize</code>, which read the image's own CA store &mdash; Argo CD needed a <b>second</b> release "
      "to fix that. Two narrowing facts: the intermediates were <b>never CT-logged</b>, so browsers were "
      "structurally safe and backend clients were the exposed population; and only <b>one</b> trusted root "
      "actually needs removing, so &ldquo;delete the emSign roots&rdquo; is unsafe advice.", CB("eMudhra"))
 + li("<b>MongoDB's reachability story moved for a new reason, and a standing note retired.</b> Percona is "
      "<b>no longer the laggard</b> &mdash; 8.0.34-15 is at parity with the newest publishable upstream. But "
      "9.0.5 / 8.3.14 / 8.0.35 / 7.0.46 all read <code>released: true</code> in Jira while <b>none is "
      "downloadable</b>, which dissolves the board's older &ldquo;shipped on two different days&rdquo; puzzle: "
      "Jira's <code>releaseDate</code> is a build-cut date, proven by a 403-vs-200 probe.", CB("MongoDB"))
 + li("<b>The React row now carries the mechanism behind its own invisibility.</b> A GHSA is globally resolvable "
      "only if someone published it globally &mdash; <code>GHSA-frr6-h895-5pxp</code> resolves repo-scoped under "
      "<code>dart-lang/sdk</code> and 404s everywhere else, which is why an earlier edition read it as resolving "
      "nowhere. Both readings were right about different paths.", CB("advisory database"))
 + "</ul>"
 + "<p><b>&#9875; Enriched in place, not re-slugged (7)</b> &mdash; the advisory redirected every one of these from "
 + "a fresh key: the Redshift TLS row (ODBC 2.3.0 joins the <code>verify-full</code> flip; the change appears in "
 + "zero of four grepped doc variants), Genie MCP (the <i>newer</i> Databricks page still lists the dying endpoint "
 + "as live), Play target-API (Google's own deadline timeline omits it), containerd 2.2 EOL (1.36 is left one "
 + "supported runtime, the LTS that has not merged the fix), .NET 8/9 EOL (NativeAOT needs republishing, not "
 + "updating), the JDK row (JDK-8395690 is mainline-only; Adoptium's newest are the affected builds) and PgBouncer "
 + "(the worst of the six is an <b>authentication bypass</b>, and Azure Linux 3, Ubuntu 24.04 and 26.04 LTS all "
 + "join the stranded list). <b>A fresh slug for a tracked story is what makes <code>days</code> lie.</b> "
 + G.archive_link(TODAY) + "</p>"
 + "<p><b>&#10150; Still standing</b> &mdash; claims " + str(len(L['claims'])) + ", own claims "
 + str(len(L['ownclaims'])) + ", gaps " + str(len(L['gaps'])) + ", promises " + str(len(L['promises']))
 + ", benchmarks " + str(len(L['benchmarks'])) + ", all carried from ed. " + PARENT_ED + " unrevised. No "
 + "competitor shipped a perf or price claim worth a card; the day was security, deadlines and the correction "
 + "pass. " + G.archive_link(TODAY) + "</p>")

# ---------------------------------------------------------------- v-read, four chairs
READ = {}
common_tail = (
 "<p><b>Where to spend today's attention.</b></p><ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; " + str(nofix) + " no-reachable-fix rows, four KEV clocks past due, and "
     "the unreachability shape now running in <b>six distinct mechanisms</b> at once.", G.archive_link(TODAY))
 + li("<b>Event Horizon</b> &mdash; " + str(ef['inside14']) + " rows inside fourteen days and " + str(ef['inside7'])
     + " inside seven, the densest window the board has carried.", G.archive_link(TODAY))
 + li("<b>Since yesterday</b> &mdash; four new rows and four corrections, plus seven drafts the "
     "<code>reuse_key</code> advisory redirected because the board already had them.", G.archive_link(TODAY))
 + "</ul>")

READ['oracle'] = (
 "<p class='lede'><b>Edition 105.</b> The uncomfortable sentence today is not about a competitor's product, it is "
 + "about ours bundling someone else's. <b>PHP's php2shell pair entered CISA KEV on the 26th with remediation due "
 + "on the 29th</b>, and <code>CVE-2026-109618</code> is simultaneously the subject of an <b>out-of-band Oracle "
 + "Security Alert</b> against Oracle Secure Backup, which ships PHP &mdash; so OSB 19.1.0.0.0&ndash;19.1.0.1.0 "
 + "now carries <b>two independent unauthenticated CVSS 9.8 RCE paths eight days apart</b>. An out-of-band alert "
 + "means it could not wait for a CPU. A backup server usually sits on a management network, which is mitigation "
 + "and not a fix. " + CB("Oracle Secure Backup") + "</p>"
 + "<p><b>Our publication record is still the thing that is hardest to defend, and today it got one answer and one "
 + "new problem.</b> The answer: the two JDK 9.1 alerts three days apart are <b>sequential halves of one "
 + "remediation</b> &mdash; 91403 distrusts the intermediates, 114820 removes the roots &mdash; so a customer who "
 + "followed the first alert exactly was genuinely still exposed, and now knows why. The new problem is that the "
 + "fixed <code>.0.3</code> train is gated behind the Patch Availability Document while <b>no free OpenJDK build "
 + "carries either half</b>: JDK-8395690 is mainline-only, jdk21u and jdk25u still ship all four cert files, and "
 + "Adoptium's newest GA builds are the ones our own alert lists as affected. Worse for credibility: "
 + "<code>ops.java/emudhra</code>, cited as authoritative inside <i>both</i> our alerts, returns <b>403</b>. "
 + CB("JDK eMudhra") + "</p>"
 + "<p><b>And CVE-2026-21962 is now 61 days past its KEV due date</b> with <code>forensicTriage: Yes</code> and a "
 + "fix that has existed since the <i>January</i> CPU &mdash; today's lane grepped both the October advisory and "
 + "its verbose risk matrices and found the id <b>zero times</b>, which is correct rather than negligent, and "
 + "exactly the problem: nothing in the October publication tells an operator that the thing they are overdue on "
 + "was fixed nine months ago. Set against that, the one unambiguous win is <b>Deep Data Security shipping in "
 + "three components at once</b> &mdash; ORDS 26.3, node-oracledb 26.0.0, python-oracledb 26.0.0 &mdash; "
 + "propagating a real end-user identity through an MCP call path so VPD, Database Vault and audit see a person "
 + "rather than a pool user. That is the right place to solve agent authorization and nobody else is shipping it. "
 + "<b>The self-audit: the control that gates it, the new <code>ORDS_MCP_SERVER</code> role, shipped under "
 + "&ldquo;Issues Fixed&rdquo;</b> &mdash; a breaking authorization change filed as a bug fix. " + CB("DeepSec") + "</p>"
 + "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question Forecast, "
 + "Gap Ledger, Benchmarks, Promise Tracker, Perf Signals, Build Radar, Skills Radar and Vendor Dossiers "
 + "<b>carry forward from ed. " + PARENT_ED + " unrevised</b> &mdash; no competitor shipped a perf or price claim "
 + "worth a card, so the depth went into the correction pass and the deadline wall. "
 + G.archive_link(TODAY) + "</p>" + common_tail)

READ['snowflake'] = (
 "<p class='lede'><b>Edition 105 &mdash; Snowflake chair (simulated).</b> The exposure today is ours and it is not "
 + "a CVE. <b>We turned certificate revocation checking off by default across every client line</b> &mdash; JDBC "
 + "4.4.0, Go 2.3.0, Python 4.8.0, Node.js 3.4.0, ODBC 3.22.0 &mdash; and the replacement, CRL, ships "
 + "<code>DISABLED</code> in ODBC 4.x and Python 5.x. The sequence is what a skeptical customer will read back to "
 + "us: a CVE let a <i>revoked</i> certificate be accepted, we fixed OCSP validation, and the next release of "
 + "every driver stopped checking revocation at all &mdash; in the same month eight intermediate CA private keys "
 + "became publicly recoverable. " + CB("revocation") + "</p>"
 + "<p><b>And the distrust fix landed on the lines our own ecosystem forbids.</b> RUSTSEC-2026-0382 is addressed "
 + "in Python connector <b>5.1.0</b> and ODBC <b>4.2.0</b> only; Python <b>4.8.1</b> shipped five days later with "
 + "nothing but a certifi floor, and Snowpark, Snowflake ML, SQLAlchemy and the CLI all still require connector "
 + "<code>&lt; 5.0.0</code>. JDBC, Go and Node.js have had <b>no release at all</b> since the disclosure. "
 + "Meanwhile <code>gosnowflake</code> v1 has <b>no <code>fixed</code> event at all</b> for CVE-2026-85525 "
 + "&mdash; remediation is an import-path migration, not a version bump. <b>Our honest position is that we "
 + "maintain two parallel lines and backport selectively, and the reachability gap is a structural consequence of "
 + "that, not an oversight.</b> " + CB("connector fork") + "</p>"
 + "<p><b>Where we are clean, and should say so precisely.</b> Neither driver CVE is in CISA KEV &mdash; verified "
 + "against catalog 2026.10.26, which holds <b>zero Snowflake entries of any kind</b> &mdash; and neither is "
 + "reported exploited. BCR-2413's Snowsight host cutover slipped to <b>early February 2027</b> rather than "
 + "passing, which closes a date that had moved three times. And bundle 2026_07 going Enabled by Default on 10-16 "
 + "went without incident. <b>The counter a competitor will reach for: 2026_08 adds "
 + "<code>ALL_USER_DETAILS</code>, which returns every active user's name and email to <i>any</i> session in the "
 + "account</b>, and disabling the bundle only defers it &mdash; the durable control is "
 + "<code>INCLUDE_PROTECTED_USER_DATA = FALSE</code>. " + CB("2026_08") + "</p>"
 + "<p><b>Carried from ed. " + PARENT_ED + " unrevised:</b> Claim Watch, Mirror, Question Forecast, Gap Ledger and "
 + "the compounding sections. " + G.archive_link(TODAY) + "</p>" + common_tail)

READ['databricks'] = (
 "<p class='lede'><b>Edition 105 &mdash; Databricks chair (simulated).</b> Our sharpest problem today is a "
 + "self-inflicted documentation one with four days on the clock. <b>The legacy Genie MCP endpoint "
 + "<code>/api/2.0/mcp/genie</code> is sunset on the 31st</b>, and our <i>newer</i> built-in-MCP-services page "
 + "&mdash; updated 23 October, a week after the page carrying the notice &mdash; still lists it as a live Public "
 + "Preview endpoint with <b>no deprecation marker and no date</b>. A customer reading the newer page will not "
 + "learn the path dies. The migration is also not a URL swap: the OAuth scope moves from <code>genie</code> to "
 + "<code>ai-gateway</code>. " + CB("Genie MCP") + "</p>"
 + "<p><b>The MLflow picture is the one a security reviewer will press on, and the honest answer is that our "
 + "advisories outrun the databases.</b> Five MLflow advisories published this window; <b>OSV returns two</b> for "
 + "a 3.16.0 install, and the three it cannot see include a <b>CVSS 9.8 unauthenticated RCE</b> on what was the "
 + "default backend before 3.7.0. The path-traversal fix shipped in 3.17.2 whose release notes mention <b>only two "
 + "Optuna bug fixes</b> &mdash; so both halves of the normal detection path failed independently in the same "
 + "project in the same month: the scanner has no record and the changelog has no signal. All five are patched and "
 + "reachable on 3.x, which is why this is <code>ok</code> and not a flag &mdash; but the remedy is "
 + "<code>pip show mlflow</code> by hand, not a clean scan. " + CB("MLflow") + "</p>"
 + "<p><b>Where we are genuinely ahead, and it is worth stating with the caveat attached.</b> We shipped "
 + "<b>jailbreak screening for MCP tool calls <i>and results</i></b> on 10-21 &mdash; a tacit admission that a "
 + "tool's return value is an injection vector, which is the correct threat model and almost nobody else is "
 + "shipping it. Multi-statement transactions went GA, and on-demand state repartitioning removed the "
 + "long-standing rule that a stateful query's shuffle-partition count is frozen at checkpoint creation. "
 + "<b>The self-audit: in the same month, <code>databricks aitools install</code> writes raw skill files into each "
 + "detected agent's <i>global</i> directory by default and fetches them from GitHub on demand</b> &mdash; and CLI "
 + "1.22.1 had to pin skills to 0.2.32 to work around GitHub rate limits, so the delivery path for an agent's "
 + "instructions is the public GitHub API. " + CB("jailbreak screening") + "</p>"
 + "<p><b>Carried from ed. " + PARENT_ED + " unrevised:</b> Claim Watch, Mirror, Question Forecast, Gap Ledger and "
 + "the compounding sections. " + G.archive_link(TODAY) + "</p>" + common_tail)

READ['bigquery'] = (
 "<p class='lede'><b>Edition 105 &mdash; BigQuery chair (simulated).</b> We had the quietest security day of the "
 + "three warehouses and the loudest semantics day, and the second is the one a customer will remember. "
 + "<b>Reusable column aliases went GA on 10-15 as an org- or project-wide DDL switch</b> &mdash; one "
 + "<code>ALTER PROJECT SET OPTIONS</code> statement, and our own documentation states plainly that enabling it "
 + "<b>can change the output of existing queries</b>, with two documented failure modes that raise no error: a "
 + "same-named table column silently wins over an alias, and an alias silently shadows an outer-query column, a "
 + "UDF argument or a script variable. " + CB("reusable column aliases") + "</p>"
 + "<p><b>The design choice is the criticism.</b> The safe shape &mdash; a per-query or per-session flag, the way "
 + "the rest of GoogleSQL's behaviour toggles work &mdash; was available and not chosen. A blast radius of an "
 + "entire organisation, set by one statement, for a change whose documented consequence is silently wrong "
 + "results, makes &ldquo;which dialect am I running?&rdquo; a question you must query "
 + "<code>EFFECTIVE_PROJECT_OPTIONS</code> to answer. Alongside it, <b><code>AI.AGG</code> went GA with "
 + "<code>max_error_ratio</code> defaulting to <code>1.0</code></b>, so an aggregation returns partial results "
 + "rather than failing unless inference fails for <i>every</i> row &mdash; and nothing in "
 + "<code>INFORMATION_SCHEMA</code> surfaces the failure ratio. <b>That is an error model that is the opposite of "
 + "SQL's, shipped as the default.</b> " + CB("AI.AGG") + "</p>"
 + "<p><b>Where we are clean, and we did the work to prove it rather than assert it.</b> No security bulletin in "
 + "the window names BigQuery, BigLake, Dataproc or Dataplex; every Critical is patched server-side with no "
 + "customer action. Our lane also <b>corrected the board</b>: CVE-2026-111943 is a Go <code>crypto/x509</code> "
 + "advisory assigned by <code>security@golang.org</code>, not an Oracle one, so the &ldquo;preliminary 8.1 "
 + "High&rdquo; that had been chased for a week was a <b>misattribution</b>. <b>The one thing to fix on our own "
 + "side:</b> the gcloud CLI's BigQuery component shipped the distrusted root and was fixed in <b>590.0.1</b> "
 + "&mdash; yet BigQuery is <b>absent from GCP-2026-071's product list</b>, so a customer auditing by product name "
 + "clears themselves wrongly while <code>bq</code> still trusts a revoked root. " + CB("gcloud 590.0.1") + "</p>"
 + "<p><b>Carried from ed. " + PARENT_ED + " unrevised:</b> Claim Watch, Mirror, Question Forecast, Gap Ledger and "
 + "the compounding sections. " + G.archive_link(TODAY) + "</p>" + common_tail)
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
flag = ("&#9873; PHP php2shell in CISA KEV &mdash; remediation due 29 Oct, 2 days, forensic triage, and 8.1-and-earlier never fixed &middot; K8s 1.34 EOL TODAY with 1.34.13 never cut and Go 1.26.10 merged-but-untagged on all four branches &middot; Chrome drops emSign root today &middot; Redshift TLS 1.2 + Genie MCP sunset 31 Oct &middot; Ray KEV 68d overdue &middot; CVE-2026-21962 61d past KEV &middot; 26 dated rows inside 14 days")
newrb = ('<div class="runbar">'
 '<span class="lbl">Edition</span><span class="val">' + ED + '</span>'
 '<span class="lbl">Generated</span><span class="val">' + GEN + '</span>'
 '<span class="lbl">Model</span><span class="val">claude-opus-5</span>'
 '<span class="lbl">Inputs</span><span class="val">19 briefs &middot; ' + str(len(ser)) + 'd ledger</span>'
 '<span class="lbl">Run tokens</span><span class="val">~3,715k</span>'
 '<span class="lbl">Skills review</span><span class="val">2027-01-01</span>'
 '<span class="flag">' + flag + '</span></div>')
html = html[:rb.start()] + newrb + html[rb.end():]
for stale in ('Edition 104', '2026-10-26 09:53 EDT', '~3,900k', '109d ledger'):
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
open('lens/out_105.html','w',encoding='utf-8').write(html)
par_sz = len(open('lens/index.html',encoding='utf-8').read())
print("\nwrote lens/out_105.html  %d bytes (parent %d, delta %+d)" % (len(html), par_sz, len(html)-par_sz))
