"""Edition 104 lens assembler. HTML blocks are built by CONCATENATION, never
%-formatting: ledger prose carries literal % signs (the 09-17/09-20 rule)."""
import json, re, sys, datetime
sys.path.insert(0, 'tools/lens')
import lens_guard as G, lens_extra as X, lens_links as LL
import patch_radar as PR, events_table as ET, longitudinal as LG, ledger_surgery as LS

TODAY = "2026-10-26"; GEN = "2026-10-26 09:53 EDT"; ED = "104"
T0 = datetime.date.fromisoformat(TODAY)
PARENT_ED, PARENT_DATE = "103", "2026-10-25"

L = json.load(open('lens/ledger_104.json'))
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
 + "<p><b>Two of the twenty rows inside seven days land tomorrow, and one of them never shipped a binary.</b> "
 + "Chrome removes <code>emSign ECC Root CA - G3</code> from the Chrome Root Store on the 27th &mdash; delivered "
 + "out-of-band by CRLSet rather than as a Chrome version, which is why there is no release note to point a "
 + "change-management process at, and explicitly <b>not covering Chrome on iOS</b>, where Apple policy forbids the "
 + "Chrome Certificate Verifier and every browser falls back to a trust change Apple has published nothing about. "
 + "The same day Kubernetes 1.34 reaches upstream EOL with <b>1.34.13 never cut</b>. " + CB("Chrome Root Store") + "</p>"
 + "<p><b>The 31st is the densest single day, and all three items are client-side credential or protocol changes "
 + "rather than version bumps.</b> Redshift enforces a TLS 1.2 minimum on provisioned clusters and Serverless "
 + "workgroups &mdash; service-side, so sitting on the TRAILING maintenance track does <i>not</i> defer it, which is "
 + "a nuance a patch-deferral plan gets wrong. Databricks sunsets the bare Genie MCP endpoint, and that one is a "
 + "credential change disguised as a URL change: the replacement is <code>system.ai.genie_one_mcp</code> <i>and</i> "
 + "the OAuth scope moves from <code>genie</code> to <code>ai-gateway</code>, so a <code>genie</code>-scoped token "
 + "cannot call it. MongoDB Atlas stops accepting new Push-Based Log Export configurations &mdash; and the "
 + "replacement changes the log <i>format</i>, JSON-encoding the <code>log</code> field so it needs a second parse "
 + "and dropping the time-order guarantee. " + CB("TLS 1.2 enforced") + "</p>"
 + "<p><b>What is NOT on this table is worth as much as what is.</b> The eleven undated rows are undated because the "
 + "vendor published no day, and the board has now been wrong in that direction four times in seven editions "
 + "&mdash; Iceberg V4, Fabric Runtime 1.3, Snowflake 2026_07 and the Fabric ODBC removal. Today's Iceberg re-read "
 + "holds the line: the <b>V4 Adaptive Metadata Tree baseline spec merged on 2026-10-14</b> with the vote passing "
 + "18 +1 and zero dissent &mdash; and the vote text says in italics that it is <i>not</i> a vote for adoption. "
 + "<b>No V4 release date exists anywhere</b>, so the equality-delete prohibition row stays deliberately undated. "
 + CB("Iceberg V4 adaptive metadata tree") + "</p>"
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
 + "embedded ledger. <b>Seven consecutive weeks of &ldquo;patched upstream, unreachable for you&rdquo; as the "
 + "dominant shape, and this week it acquired two new mechanisms rather than more instances.</b> "
 + CB("no reachable fix") + "</p>"
 + "<p><b>Mechanism one: patched for paying customers only.</b> Oracle shipped JDK 17.0.21.0.3 and 21.0.13.0.3 "
 + "through the Patch Availability Document &mdash; a support-contract gate &mdash; for a CVSS 9.1 affecting every "
 + "supported line from 8 to 27, while <code>openjdk/jdk21u</code> and <code>openjdk/jdk25u</code> still carry all "
 + "four compromised cert files in-tree. That is not inferred from release notes, which actively disagree with each "
 + "other here; it is a direct probe: the four files return <b>HTTP 200</b> on the update repos and <b>404</b> on "
 + "mainline, with a control cert still 200. So Temurin, Corretto and Microsoft all sit at or below the affected "
 + "boundary and the only remedy for the free distributions is four manual <code>keytool -delete</code> calls. "
 + CB("no vendor build carries the fix") + "</p>"
 + "<p><b>Mechanism two: the fix is merged, and tagged in nothing &mdash; and it showed up twice this week in two "
 + "unrelated projects, which is what makes it a category rather than an accident.</b> "
 + "<code>.go-version</code> on Kubernetes <code>release-1.34</code> through <code>-1.37</code> all read "
 + "<code>1.26.10</code> today while every shipped tag carries 1.26.5 or 1.26.8; MariaDB's MDEV-33966 is "
 + "Critical/Fixed against 11.8.10 / 12.3.4 / 13.1.2, none of which exists, for a measured <b>3.5&times;</b> "
 + "throughput regression. <b>This is strictly harder to see than an EOL branch.</b> An EOL branch at least shows "
 + "up as an unsupported version; here git looks patched, every released artifact is not, and an SBOM-and-CVE "
 + "pipeline reports the identical posture before and after the fix was written, because every scanner reads "
 + "versions. The detection that works &mdash; compare the shipped artifact's embedded toolchain against branch "
 + "HEAD &mdash; is one almost nobody runs. " + G.archive_link(TODAY) + "</p>"
 + "<p><b>A third variant is worth naming because it defeats a scanner in the opposite direction: patched, "
 + "reachable, and still off.</b> StarRocks fixed cross-user query-profile disclosure in 4.1.6/4.0.16 behind an FE "
 + "config that ships <b>disabled by default</b> &mdash; the PR says so outright, that an upgrade changes nothing "
 + "until an operator opts in. A scanner sees a patched version while the exposure is unchanged. And arrow-rs "
 + "inverted the shape entirely: 57.3.2, 58.4.1 and 59.3.2 all shipped today, while <b>60.0.0 &mdash; the current "
 + "major, and the version a new project picks &mdash; has no patch at all</b>, so the remedy is to pin backwards. "
 + CB("disabled by default") + "</p>"
 + "<p><b>The cap stays at 35, and the reasoning corrected in ed. 103 held on re-measurement.</b> "
 + "<code>sev_tier</code>'s band 0 is &ldquo;asserts CVSS &ge; 9.0 anywhere in the row&rdquo;, not the CISA KEV "
 + "set: it is <b>" + str(CAPINFO['band0']) + " of " + str(len(L['patch'])) + "</b> rows today, so "
 + "<code>|band0 &cup; must-show|</code> is " + str(CAPINFO['union']) + " and rendering that many would produce a "
 + "list rather than a radar. <code>select()</code>'s force-include is what makes the tight cap safe: all "
 + str(CAPINFO['must']) + " must-show rows are guaranteed present and the remainder fills by rank. "
 + "<b>Before acting on a prior note's number, read the function that produced it.</b> "
 + G.archive_link(TODAY) + "</p>"
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
 + "high of " + str(prior_urg) + " set on " + prior_urg_date + ", and tied with " + str(ties) + " prior days, so "
 + "<b>not a record</b>. The last eight runs read " + run8 + ", mean " + ("%.2f" % mean14)
 + " over fourteen days. The series high for items excluding today is " + str(hi_items['items']) + " on "
 + hi_items['date'] + ". " + CB("longitudinal") + "</p>"
 + "<p><b>" + str(cur['urgent']) + " of 19 lanes flagged, audited one at a time, and all sixteen survive the "
 + "definition applied literally &mdash; but the honest framing is that sixteen flags cover roughly eleven "
 + "distinct stories, and the summary should say so rather than trim to a number.</b> <b>One root cause accounts "
 + "for five of them</b>: the eMudhra CA key compromise reaches App Dev, DevOps, Mobile, Frontend and Oracle as "
 + "five different remediations of one disclosure, and litellm is shared by AI Daily and AI App Dev. Four KEV "
 + "clocks are past due &mdash; Oracle's CVE-2026-21962 at <b>60 days</b> with <code>forensicTriage: Yes</code> and "
 + "a fix that has existed since the January CPU, <b>Ray at 67</b> with a fix released 339 days ago, Apple's "
 + "exploited CoreGraphics bug at 13 with nothing for the iOS 18.7.x train, and Struts at 15 on a 2016 CVE newly "
 + "exploited. " + str(ef['inside14']) + " dated rows fall inside fourteen days. <b>Counting lanes is not counting "
 + "problems.</b> " + CB("flag calibration") + "</p>"
 + "<p><b>The three <code>ok</code> lanes are the discrimination evidence, and each declined in writing.</b> "
 + "Database Hardware reported a month with <b>no CVE at all</b> rather than padding, for a second consecutive "
 + "run, while finding the day's biggest infrastructure story in server DDR5 at $29&ndash;41/GB. BigQuery held at "
 + "<code>ok</code> on its standing ground &mdash; two Criticals that name BigQuery were both fixed server-side "
 + "with the vendor stating no customer action &mdash; and corrected the board on the way, establishing that a "
 + "carried &ldquo;8.1 High&rdquo; figure <b>has no traceable source anywhere</b>: the CNA publishes no metric, "
 + "NVD's is empty, Red Hat says 6.8, Google says Medium, and Oracle serves a 404 for that CVE. Open Formats "
 + "declined the arrow-rs use-after-free with the reasoning spelled out: no CVE, no GHSA, no RUSTSEC entry, an "
 + "OOM-handling trigger rather than attacker-reachable input, and a fix one minor back on a line still "
 + "receiving patches &mdash; so <b>&ldquo;a fix exists but is not reachable&rdquo; does not hold</b>. "
 + CB("ok lanes") + "</p>"
 + "<p>The High column is still <b>not comparable across days</b>: each run re-derives the severity heuristic from "
 + "the title rather than reading a stored value, so a shift there is a classifier change and not a change in the "
 + "world. Storing per-item severity in the public ledger remains the queued fix. The same limitation produced the "
 + "dashboard's <code>changed</code> noise for a <b>fourth consecutive run</b>: <b>8 of 12 rows were classifier "
 + "artifacts</b>, reading as a severity move because the stateless research agents reworded a carried headline "
 + "while the fact sat still. Four real movements survived, and all four are corrections to the board's own prior "
 + "reading rather than movement in the world &mdash; which is itself the week's pattern. "
 + G.archive_link(TODAY) + "</p>"
 + "".join(lt))

# ---------------------------------------------------------------- v-wn (shared)
def li(txt, src): return "<li>" + txt + " " + src + "</li>"
wn_body = (
 "<p class='lede'>Diffed against edition " + PARENT_ED + ". <b>Four new patch rows, seven corrections, no "
 + "retirements</b> &mdash; and the notable thing about the corrections is that <b>seven more were drafted and "
 + "dropped because the board was already right</b>. " + G.archive_link(TODAY) + "</p>"
 + "<p><b>&#128309; New on the board (4)</b></p><ul>"
 + li("<b>CVE-2026-91403, the JDK near-twin</b> &mdash; also 9.1, also <code>javax.net.ssl</code>, advisory 10-21, "
      "three days and one BPR before 114820. The reading: the first removal was incomplete and a second shipped. "
      "A customer who followed the 21 Oct alert exactly is exposed again.", CB("CVE-2026-91403"))
 + li("<b>arrow-rs 60.0.0 is the unpatched line</b> &mdash; 57/58/59 all patched today, no 60.0.x exists, so the "
      "remedy is to pin backwards. The inverse of every &ldquo;upgrade to latest&rdquo; instinct.", CB("arrow-rs"))
 + li("<b>MariaDB MDEV-33966</b> &mdash; a 3.5&times; throughput regression Fixed against three versions that do "
      "not exist, with 11.4 LTS in the affects list and absent from fixVersions.", CB("MDEV-33966"))
 + li("<b>MySQL Server 8.0 absent from all 80 Server rows of the October CPU</b> &mdash; 98 patches, 29 "
      "unauthenticated, including an 8.8 on the Group Replication interconnect, and none of it exists in an 8.0 "
      "community build.", CB("October 2026 CPU"))
 + "</ul>"
 + "<p><b>&#128314; Corrected (7), and the headline one changes what a reader does</b></p><ul>"
 + li("<b>The JDK row moved from &ldquo;no vendor build exists&rdquo; to &ldquo;patched for paying customers "
      "only&rdquo;</b>, which is a different and worse shape. Oracle shipped through a support gate; jdk21u and "
      "jdk25u still carry all four certs in-tree, proven by direct probe rather than by a release note &mdash; "
      "and the release notes actively contradict each other here.", CB("Oracle Security Alert"))
 + li("<b>Kubernetes: the real slip is 6 days, not the 13 the board was reading.</b> The round was deliberately "
      "postponed to 10-20 and <code>schedule.yaml</code> was never updated, so tooling and humans read different "
      "numbers. The sharper half: Go 1.26.10 is merged on all four branches and tagged in none.",
      G.archive_link(TODAY))
 + li("<b>PgBouncer has a second and larger stranded population</b> &mdash; Debian 12 and 13 list all six CVEs "
      "<code>open</code> with no fixed version, alongside Azure's pinned 1.25.2. One binary, three answers to "
      "&ldquo;are we patched?&rdquo;, and the variable is the supply chain.", CB("PgBouncer"))
 + li("<b>MongoDB's advisory is now the thing hiding the exposure</b> &mdash; 8.2 appears neither as affected nor "
      "as fixed, while the 8.2 release notes still call the EOL branch supported. An EOL branch looks <i>clean</i> "
      "in an advisory-driven inventory.", CB("CVE-2026-82067"))
 + li("<b>postgres-mcp's lookalike upgrade is also unfixed</b> &mdash; <code>postgres-mcp-pro</code> 0.4.2 is a "
      "third-party fork carrying the same un-recursed validator, verified by reading it.", CB("postgres-mcp"))
 + li("<b>Ray and Doris re-read</b> &mdash; Ray's KEV clock at 67 days against a fix released 339 days ago, and "
      "Doris now states its own failure mode verbatim: a vulnerability in an archived branch &ldquo;stays unfixed "
      "there, permanently.&rdquo;", CB("Doris download"))
 + "</ul>"
 + "<p><b>&#10134; Drafted and dropped &mdash; the board was already right (7)</b></p><ul>"
 + li("<b>Aurora's 28-CVE gap</b> was already marked RESOLVED with the 2026-09-29 close date; <b>StarRocks' "
      "disabled-by-default knob</b>, <b>Doris 3.1's archive</b>, <b>the React RSC fix list</b>, <b>MongoDB 8.2's "
      "EOL</b>, <b>the eMudhra CVSS spread</b> and <b>the unsourceable 8.1</b> were all already recorded "
      "correctly &mdash; the last of those corrected on 10-25. <b>Seventh consecutive run where probing the board "
      "before drafting paid for itself</b>, and the failure it prevents is worse than wasted work: rewriting a "
      "correct row can reintroduce an error an earlier edition fixed.", G.archive_link(TODAY))
 + "</ul>"
 + "<p><b>&#10150; Still standing</b> &mdash; claims " + str(len(L['claims'])) + ", own claims "
 + str(len(L['ownclaims'])) + ", gaps " + str(len(L['gaps'])) + ", promises " + str(len(L['promises']))
 + ", benchmarks " + str(len(L['benchmarks'])) + ", all carried from ed. " + PARENT_ED + " unrevised. No "
 + "competitor shipped a perf or price claim worth a card today; the day was security and deadline movement, "
 + "and the depth went into the correction pass. " + G.archive_link(TODAY) + "</p>")

# ---------------------------------------------------------------- v-read, four chairs
READ = {}
common_tail = (
 "<p><b>Where to spend today's attention.</b></p><ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; " + str(nofix) + " no-reachable-fix rows, four KEV clocks past due, and "
     "two new mechanisms for the same shape: patched-behind-a-paywall and fix-merged-no-tag.", G.archive_link(TODAY))
 + li("<b>Event Horizon</b> &mdash; " + str(ef['inside14']) + " rows inside fourteen days, " + str(ef['inside7'])
     + " inside seven, two of them tomorrow, nothing retired.", G.archive_link(TODAY))
 + li("<b>Since yesterday</b> &mdash; four new rows, seven corrections, and seven more drafted then dropped "
     "because the board already had them right.", G.archive_link(TODAY))
 + "</ul>")

READ['oracle'] = (
 "<p class='lede'><b>Edition 104.</b> One certificate-authority key compromise has now produced <b>six separate "
 + "runtime remediations on six separate clocks</b>, and the one that failed is ours. Oracle shipped the JDK fix "
 + "&mdash; 17.0.21.0.3 and 21.0.13.0.3 &mdash; through the Patch Availability Document, a support-contract gate, "
 + "while <code>openjdk/jdk21u</code> and <code>openjdk/jdk25u</code> still carry all four compromised cert files "
 + "in-tree. <b>So the sentence a competitor can say about us today is that we patched our paying customers and "
 + "left the free distributions with manual <code>keytool</code> surgery.</b> " + CB("eMudhra CA compromise") + "</p>"
 + "<p><b>And our own publication record makes it harder to act on, not easier.</b> We shipped two 9.1 alerts "
 + "three days apart in the same component &mdash; CVE-2026-91403 on the 21st and CVE-2026-114820 on the 24th "
 + "&mdash; where the second one's affected builds are the first one's fix builds, so a customer who followed the "
 + "first alert to the letter is exposed again and only learns it by reading a second alert. Set that beside "
 + "<b>CVE-2026-21962 at 60 days past its KEV due date</b> with <code>forensicTriage: Yes</code>, absent from the "
 + "October CPU because the fix has existed since <i>January</i> &mdash; today's lane grepped both the advisory "
 + "and its verbose risk matrices and found the id zero times. <b>The pattern a customer can name is that our "
 + "publication is harder to act on than a competitor's silence.</b> " + CB("CVE-2026-21962") + "</p>"
 + "<p><b>Where we are genuinely well placed, and it is a narrow win worth taking accurately.</b> The October RU "
 + "is <b>23.26.4</b> and it shipped <b>31 features</b> into a quarterly patch &mdash; Iceberg UPDATE and DELETE, "
 + "ezTLS, a Witness Replica role, XA promotion of sessionless transactions, four new vector index types. Nobody "
 + "else is delivering that cadence on-prem. <b>The cost is that &ldquo;we're on 19c&rdquo; and &ldquo;we're on "
 + "26ai&rdquo; no longer describe a feature set</b>, and our own retrospective per-RU list exists for 26ai and "
 + "not for 19c. A regression suite now has to be RU-aware rather than release-aware, and that is a real "
 + "operational tax we are passing to customers. " + CB("Release Update 23.26.4") + "</p>"
 + "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question Forecast, "
 + "Gap Ledger, Benchmark Scoreboard, Promise Tracker, Perf Signals, Build Radar, Skills Radar and Vendor "
 + "Dossiers <b>carry forward from ed. " + PARENT_ED + " unrevised</b>: no competitor shipped a perf or price "
 + "claim worth a card, <code>claims[]</code> did not grow, and the depth went into the correction pass and the "
 + "deadline wall, which is where the day was. " + G.archive_link(TODAY) + "</p>"
 + common_tail)

READ['snowflake'] = (
 "<p class='lede'><b>Edition 104 &mdash; Snowflake chair (SIMULATED).</b> Our exposure today is not a CVE, it is "
 + "a default we have already flipped: <b>bundle 2026_07 became Enabled by Default on 2026-10-16</b>, so 23 "
 + "behavior changes are live in every account that did not explicitly opt out. Two of them change results "
 + "silently rather than erroring &mdash; <code>BITCOUNT</code> on a negative NUMBER now returns 128 where it "
 + "returned 8, and BOOLEAN&rarr;NUMBER casts follow the target type &mdash; and one hard-fails any SQL "
 + "referencing two undocumented <code>METADATA$</code> columns that nonetheless worked, which breaks stored "
 + "procedures and tasks at 3am rather than in a dev session. " + CB("bundle 2026_07") + "</p>"
 + "<p><b>The sharper governance item is that our own allowlist stopped being a control.</b> BCR-2378 means "
 + "<code>CORTEX_MODELS_ALLOWLIST</code> no longer gates model access at all &mdash; RBAC is the only mechanism, "
 + "and it now covers embedding models that were previously unenforced. So a role whose access came only from the "
 + "allowlist <b>loses it</b> and <code>AI_EMBED</code> starts failing; in the other direction, "
 + "<code>CORTEX-MODEL-ROLE-ALL</code> granted to PUBLIC now grants every model <i>including ones we ship "
 + "later</i>. And the migration trap is ours: testing as ACCOUNTADMIN proves nothing, because ACCOUNTADMIN "
 + "always has model access. " + CB("CORTEX_MODELS_ALLOWLIST") + "</p>"
 + "<p><b>Where we look worst under symmetric scrutiny is driver revocation, and it is our own sequencing.</b> We "
 + "fixed an OCSP <i>validation</i> bypass on 3 September and then turned OCSP revocation checking off by default "
 + "across six drivers within 24 days, with the old hardening settings now <b>accepted but ignored</b>. A "
 + "customer running fail-close drops silently to no revocation checking on upgrade, with a log warning as the "
 + "only signal. Across the industry the same CVE produced three incompatible answers &mdash; Go fixed it, we "
 + "disabled it, Python deleted it &mdash; so &ldquo;revocation checking is enabled&rdquo; now means three "
 + "different things. <b>Two of the three reduce the security property.</b> " + CB("JDBC 4.4.0") + "</p>"
 + "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question Forecast, "
 + "Gap Ledger and the rest <b>carry forward from ed. " + PARENT_ED + " unrevised</b>. "
 + G.archive_link(TODAY) + "</p>" + common_tail)

READ['databricks'] = (
 "<p class='lede'><b>Edition 104 &mdash; Databricks chair (SIMULATED).</b> Our worst item lands in five days and "
 + "it is a credential change wearing a URL change: <b>the bare Genie MCP endpoint is sunset 2026-10-31</b>, and "
 + "migrating means moving to <code>system.ai.genie_one_mcp</code> <i>and</i> changing the OAuth scope from "
 + "<code>genie</code> to <code>ai-gateway</code>. A <code>genie</code>-scoped token cannot call the replacement, "
 + "so every integration needs a re-authorization pass. <b>The asymmetry is the finding</b>: of five legacy "
 + "<code>/api/2.0/mcp/*</code> routes, only the bare multi-space Genie path is dated &mdash; the per-space form "
 + "and the SQL, AI Search and UC-functions endpoints carry no date, and our managed-MCP doc explicitly blesses "
 + "them. Read the silence as scheduling, not commitment. " + CB("Genie MCP") + "</p>"
 + "<p><b>What a customer will quote at us first is MLflow, and the honest answer is that the worst one has no "
 + "CVE.</b> Five advisories in the window: an unauthenticated <b>CVSS 9.8</b> RCE through a scorer-invoke "
 + "endpoint that imports a request-named module &mdash; its own advisory line is the lesson, <i>&ldquo;a "
 + "package-name prefix is not a provenance boundary&rdquo;</i> &mdash; plus CVE-2026-53995, an unauthenticated "
 + "arbitrary file write affecting <b>every MLflow up to 3.17.1 including all of 2.x</b>, where FileStore is the "
 + "default backend before 3.7.0 and <b>no 2.x fix exists</b>. Three of the five carry no CVE and are absent from "
 + "OSV, so an OSV-backed gate reports MLflow clean while a Dependabot gate does not. "
 + CB("CVE-2026-53995") + "</p>"
 + "<p><b>And one of our own GA claims deserves the Mirror standard applied to it.</b> Multi-statement "
 + "transactions went GA on 10-14 gated on <code>catalog commits</code> &mdash; a feature whose own status reads "
 + "<b>Beta</b> on three doc surfaces and Public/Private Preview on others, which needs DBR 18.0+ to enable on an "
 + "existing table, which <code>CREATE OR REPLACE TABLE</code> cannot toggle, and which materialized views cannot "
 + "use at all. <b>&ldquo;GA&rdquo; is increasingly a statement about the API rather than about the customer's "
 + "tables</b>, and a GA badge does not inherit downward. " + CB("catalog commits") + "</p>"
 + "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question Forecast, "
 + "Gap Ledger and the rest <b>carry forward from ed. " + PARENT_ED + " unrevised</b>. "
 + G.archive_link(TODAY) + "</p>" + common_tail)

READ['bigquery'] = (
 "<p class='lede'><b>Edition 104 &mdash; BigQuery chair (SIMULATED).</b> Our quietest week in months is also our "
 + "strongest competitive position, and the reason is worth stating precisely: <b>we published nothing between "
 + "10-22 and today</b>, and the two Criticals that name BigQuery were both fixed server-side with no customer "
 + "action. Against a board carrying " + str(nofix) + " no-reachable-fix rows, &ldquo;there is nothing for you to "
 + "patch&rdquo; is the claim nobody else can make this week. " + CB("GCP security bulletins") + "</p>"
 + "<p><b>Where we are exposed is a figure attributed to a competitor that nobody can source &mdash; and we "
 + "should be careful, because the same discipline cuts at us.</b> The carried &ldquo;Oracle 8.1 High&rdquo; on "
 + "CVE-2026-111943 has <b>no traceable origin</b>: the CNA publishes <code>metrics: null</code>, NVD's object is "
 + "empty four days after its last modification, Red Hat says 6.8/Important, we say Medium with no score, and "
 + "Oracle serves a 404 for that CVE page. <b>One id, four advisory ecosystems, not one authoritative score.</b> "
 + "A policy gated on &ldquo;no High CVEs&rdquo; gets a different answer per feed &mdash; and our own "
 + "&ldquo;Medium with no score&rdquo; is part of that problem rather than outside it. "
 + CB("CVE-2026-111943") + "</p>"
 + "<p><b>The thing we should fix before anyone asks is that our release notes have quietly stopped being "
 + "authoritative for what customers install.</b> The <code>Libraries</code> sections vanished after 2025-12-22 "
 + "&mdash; <b>308 days</b> &mdash; while the Python client went 3.41 to 3.46.2, bigquery-storage to 2.43.0, "
 + "bigframes to 2.51.0 and a whole Rust SDK went Preview to GA. Two of three main clients also changed GitHub "
 + "homes in that stretch. One of those releases carries a correctness fix &mdash; dropping "
 + "<code>startIndex</code> when a page token is sent &mdash; that silently returns the wrong slice of a result "
 + "set. <b>A customer tracking our release notes for client awareness has been reading a blind feed for ten "
 + "months.</b> " + CB("google-cloud-bigquery") + "</p>"
 + "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question Forecast, "
 + "Gap Ledger and the rest <b>carry forward from ed. " + PARENT_ED + " unrevised</b>. "
 + G.archive_link(TODAY) + "</p>" + common_tail)
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
flag = ("&#9873; JDK 9.1 now patched for ORACLE CUSTOMERS ONLY &mdash; jdk21u/jdk25u still carry all four certs &middot; K8s 1.34 EOLs 27 Oct with 1.34.13 uncut and Go 1.26.10 merged-but-untagged on all four branches &middot; Chrome drops emSign root 27 Oct &middot; Ray KEV 67d overdue &middot; CVE-2026-21962 60d past KEV &middot; 23 dated rows inside 14 days")
newrb = ('<div class="runbar">'
 '<span class="lbl">Edition</span><span class="val">' + ED + '</span>'
 '<span class="lbl">Generated</span><span class="val">' + GEN + '</span>'
 '<span class="lbl">Model</span><span class="val">claude-opus-5</span>'
 '<span class="lbl">Inputs</span><span class="val">19 briefs &middot; ' + str(len(ser)) + 'd ledger</span>'
 '<span class="lbl">Run tokens</span><span class="val">~3,900k</span>'
 '<span class="lbl">Skills review</span><span class="val">2027-01-01</span>'
 '<span class="flag">' + flag + '</span></div>')
html = html[:rb.start()] + newrb + html[rb.end():]
for stale in ('Edition 103', '2026-10-25 09:10 EDT', '~3,950k', '108d ledger'):
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
open('lens/out_104.html','w',encoding='utf-8').write(html)
par_sz = len(open('lens/index.html',encoding='utf-8').read())
print("\nwrote lens/out_104.html  %d bytes (parent %d, delta %+d)" % (len(html), par_sz, len(html)-par_sz))
