"""Edition 101 lens assembler. HTML blocks are built by CONCATENATION, never
%-formatting: ledger prose carries literal % signs (the 09-17/09-20 rule)."""
import json, re, sys, datetime
sys.path.insert(0, 'tools/lens')
import lens_guard as G, lens_extra as X, lens_links as LL
import patch_radar as PR, events_table as ET, longitudinal as LG, ledger_surgery as LS

TODAY = "2026-10-23"; GEN = "2026-10-23 09:51 EDT"; ED = "101"
T0 = datetime.date.fromisoformat(TODAY)
PARENT_ED, PARENT_DATE = "100", "2026-10-22"

L = json.load(open('lens/ledger_101.json'))
PAR = json.load(open('lens/parent_ledger.json'))
LONG = json.load(open('lens/longi.json'))
ser, stats = LONG['series'], LONG['stats']
shown_keys = json.load(open('lens/shown_keys.json'))
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
 + " sit beyond thirty. <b>The 26 Oct &ndash; 6 Nov stretch is the densest cutover window this board "
 + "has ever carried</b> &mdash; and every row in it requires a client-side change rather than a "
 + "vendor-side one. Three rows enter dated today and two past-dated rows retired. " + CB("deadline wall") + "</p>"
 + "<p><b>One row moved in the direction nobody plans for: it un-retired.</b> This board had already "
 + "retired the Snowsight account-specific sign-in host as a passed 2026-10-16 date. Snowflake's "
 + "BCR-2413 now reads <b>&ldquo;early February 2027 (exact date to be determined)&rdquo;</b>, so the "
 + "date did not fire &mdash; it relocated, for the third time. That is the clearest argument this "
 + "board has for recording a vendor's precision rather than its number. " + CB("BCR-2413 Snowsight") + "</p>"
 + ev_tbl)

# ---------------------------------------------------------------- v-patch
rows_html = ["<table class='tbl'><thead><tr><th>Due / fix status</th><th>Item</th><th>Src</th></tr></thead><tbody>"]
for r in shown:
    rows_html.append("<tr><td>" + (r.get('due') or '&mdash;') + "</td><td>" + (r.get('t') or '')
                     + "</td><td>" + C(r) + "</td></tr>")
rows_html.append("</tbody></table>")
patch_body = (
 "<p class='lede'>The register holds <b>" + str(nofix) + " rows with no reachable fix</b> out of "
 + str(len(L['patch'])) + " tracked; <b>" + str(len(shown)) + "</b> are rendered here and the rest stay "
 + "in the embedded ledger. Five rows enter the register today, and the shape they share is the "
 + "window's signature: <b>the fix exists and the affected population cannot reach it, cannot see it, "
 + "or both</b>. " + CB("patch radar") + "</p>"
 + "<p><b><code>assert_must_show</code> earned its keep for the seventh consecutive edition, and the "
 + "ranking defect it caught was a vocabulary gap rather than a sort bug.</b> Two must-show rows sank "
 + "to band 3 &mdash; the pgvector managed-provider row and the new Hudi wrong-rows row &mdash; because "
 + "<code>NO_FIX_RE</code> had no pattern for either phrasing. Neither row ever says &ldquo;no "
 + "fix&rdquo;: one says <i>&ldquo;zero of seven managed providers ship 0.8.7&rdquo;</i> and the other "
 + "<i>&ldquo;carried by NO release&rdquo;</i>. Both are now matched, with a lookahead so <b>&ldquo;no "
 + "release <i>notes</i> were published&rdquo; stays a negative</b> &mdash; a false positive my own "
 + "regression case caught before it shipped. The standing instruction held: the cap stayed at 30 and "
 + "the ranking was fixed. " + CB("must-show") + "</p>"
 + "<p><b>A deliberate widening of what this register admits, stated rather than smuggled.</b> The "
 + "Hudi row is not a CVE &mdash; it is a correctness defect that silently returns wrong rows, with the "
 + "fix merged to a branch that no release carries and the triggering config on by default. The urgent "
 + "rule's clause is &ldquo;a fix exists but is not reachable for an affected population&rdquo;, and a "
 + "query quietly returning the wrong answer is at least as actionable as a patched CVE. It is carried "
 + "here on that reading, and the reading is on the row's face. " + CB("Hudi VARIANT wrong rows") + "</p>"
 + "".join(rows_html))

# ---------------------------------------------------------------- v-longitudinal
prior = [r for r in ser if r['date'] < TODAY]
cur = ser[-1]
hi_items = max(prior, key=lambda r: r['items'])
urg = [r['urgent'] for r in ser[-8:]]
run8 = ", ".join(str(u) for u in urg)
urg_max = max(r['urgent'] for r in ser)
ties = [r['date'] for r in ser if r['urgent'] == urg_max]
mean14 = sum(r['urgent'] for r in ser[-14:]) / min(14, len(ser))
assert cur['urgent'] == 16 and urg_max == 16, (cur['urgent'], urg_max)
lt = ["<table class='tbl'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th><th>Competitors</th>"
      "<th>DB HW</th><th>High</th><th>Urgent lanes</th></tr></thead><tbody>"]
for r in ser[-16:]:
    lt.append("<tr><td>" + r['date'] + "</td><td>" + str(r['items']) + "</td><td>" + str(r.get('oracle',0))
              + "</td><td>" + str(r.get('competitors',0)) + "</td><td>" + str(r.get('dbhw',0)) + "</td><td>"
              + str(r.get('high',0)) + "</td><td>" + str(r['urgent']) + "</td></tr>")
lt.append("</tbody></table>")
longi_body = (
 "<p class='lede'>" + str(len(ser)) + " days of public ledger. Today: <b>" + str(cur['items'])
 + " items</b> across 19 lanes and <b>" + str(cur['urgent']) + " urgent lanes &mdash; a series high</b>, "
 + "against a previous ceiling of 14. The last eight runs read " + run8 + ", mean "
 + ("%.1f" % mean14) + " over fourteen days. The series high for items excluding today is "
 + str(hi_items['items']) + " on " + hi_items['date'] + ". " + CB("longitudinal") + "</p>"
 + "<p><b>16 urgent lanes was audited rather than trimmed, and the honest reading is that the day was "
 + "genuinely heavy.</b> Every one of the sixteen survives the definition applied literally: four CISA "
 + "KEV clocks already expired (Oracle at 57 days, Apple at 10, LiteLLM at 37, Atlassian at 5), nine "
 + "lanes carrying a fix their population cannot reach, and a cutover wall of " + str(ef['inside14'])
 + " dated rows inside fourteen days. <b>16 flags cover ~14 distinct stories</b> &mdash; LiteLLM is "
 + "shared by AI Daily and AI App Dev, and the eMudhra CA compromise reaches App Dev, DevOps and Oracle "
 + "as three different consequences of one key ceremony. <b>The three <code>ok</code> lanes are the "
 + "evidence the agents discriminated</b>: AI Hardware pulled the KEV catalog and found zero of 33 "
 + "additions touching GPU or AI infrastructure, then declined to flag a CVSS 10.0 AIStore RCE because "
 + "its fix is genuinely reachable; Database Hardware reported a month with no CVE at all rather than "
 + "padding; NL2SQL reported no dated item in the lane. " + CB("flag calibration") + "</p>"
 + "<p>The High column is still <b>not comparable across days</b>: each run re-derives the severity "
 + "heuristic from the title rather than reading a stored value, so a shift there is a classifier "
 + "change and not a change in the world. Today gave that limitation a second, sharper demonstration "
 + "&mdash; <b>three of seven rows on the dashboard's own &ldquo;changed&rdquo; card were pure "
 + "classifier artifacts</b>, reading &ldquo;urgent &rarr; normal&rdquo; because the research agents "
 + "reworded a carried headline while the underlying fact sat still. They were excluded by hand and the "
 + "exclusion was landed in the tooling. Storing per-item severity in the public ledger remains the "
 + "durable fix. " + G.archive_link(TODAY) + "</p>"
 + "".join(lt))

# ---------------------------------------------------------------- v-wn (shared)
def li(txt, src): return "<li>" + txt + " " + src + "</li>"
wn_body = (
 "<p class='lede'>Edition " + ED + " against edition " + PARENT_ED + ". <b>Eight rows enter the board, "
 + "twelve are enriched, five dated rows needed correcting and one row came back from the dead</b> "
 + "&mdash; the heaviest correction pass in a dozen editions, and four of the five corrections moved a "
 + "claim this board had been carrying confidently. " + CB("since yesterday") + "</p>"
 + "<h3>&#127381; New on the board</h3><ul>"
 + li("<b>Chrome removes <code>emSign ECC Root CA - G3</code> on 2026-10-27</b> &mdash; eight eMudhra "
     "intermediate CA private keys were recoverable from their public certificates, and this gives the "
     "carried eMudhra row a date where it had none.", CB("emSign ECC Root CA removal"))
 + li("<b>CVE-2026-21589 is in CISA KEV five days past due and it is CI/CD infrastructure</b> &mdash; "
     "Bitbucket and Bamboo Data Center, with forensic-triage obligations, scored 9.3 by Atlassian and "
     "7.5 by NVD.", CB("CVE-2026-21589 Atlassian KEV"))
 + li("<b>Apache Hudi silently returns wrong rows</b> for nullable VARIANT columns on MoR reads under "
     "Spark 4.1, with the fix merged to the branch, <b>no release carrying it</b>, and the triggering "
     "config on by default.", CB("Hudi VARIANT wrong rows"))
 + li("<b>A CVSS 9.5 React Server Components RCE that no scanner can see</b> &mdash; repository-only "
     "advisory, no CVE, 404 in both OSV and GitHub's database nine days after the fix, and "
     "<code>npm audit</code> returns zero for an affected version.", CB("React Server Components RCE"))
 + li("<b>Snowflake publishes its Go v1 driver's patched version as the literal string "
     "&ldquo;None&rdquo;</b> while its own client policy still accepts that driver &mdash; auth tokens "
     "and query-result master keys written to logs.", CB("Snowflake CVE-2026-86597 Go driver"))
 + li("<b>RDS for PostgreSQL force-upgrades eight minor versions on 2026-10-31</b>, with downtime, "
     "regardless of the auto-minor-upgrade setting.", CB("RDS PostgreSQL end of standard support"))
 + li("<b>Google Play's Billing Library 7 cliff on 2026-11-01</b> &mdash; a publishing gate, kept as a "
     "row distinct from the target-API-36 cliff that shares the date.", CB("Play Billing Library 7"))
 + li("<b>mongo-go-driver v1 has no fix for an unauthenticated panic-DoS</b>; v2.9.2 is a module-path "
     "migration.", CB("mongo-go-driver CVE-2026-107325"))
 + "</ul><h3>&#128314; Corrections &mdash; four of them to claims this board was confident about</h3><ul>"
 + li("<b>Fabric Runtime 2.0 IS now the default</b>, closing three editions of &ldquo;promised late "
     "September, no flip&rdquo; &mdash; and the board also had its Spark version wrong: it is Spark "
     "<b>4.1</b> with Delta Lake 4.2, not 4.0. The vendor still published no day, so the row stays "
     "undated rather than being backfilled.", CB("Fabric Runtime 2.0 default"))
 + li("<b>The Iceberg equality-delete ban is merged spec text, not a proposal</b> (PR #17783, "
     "2026-09-29) &mdash; and V4 still has no date <i>by the design of the process</i>: the baseline "
     "AMT vote stated in terms that it was &ldquo;not a vote for adoption&rdquo;. This board's "
     "deliberate undating was right.", CB("Iceberg equality deletes forbidden v4"))
 + li("<b>Doris CVE-2026-72524's affected population is narrower than carried</b> &mdash; 3.1.x only, "
     "not 2.0&ndash;2.1.x or 3.0.x, per NVD's <code>defaultStatus: unaffected</code>. What replaced the "
     "overstatement is harsher for those affected: 3.1.4 is now in &ldquo;Archived Releases&rdquo;, "
     "which receive nothing, &ldquo;security patches included&rdquo;.", CB("Doris archived releases"))
 + li("<b>Percona Server for MongoDB is NOT the stranded population</b> &mdash; it crossed the "
     "CVE-2026-82067 fix in September. <b>MongoDB 8.2 is</b>: its own tracker names 8.2.13 as the fix "
     "and that release was never published.", CB("CVE-2026-82067 MongoDB"))
 + li("<b>The Next.js/sharp framing overstated it, and the truth is narrower and worse</b> &mdash; a "
     "fresh install does resolve sharp to 0.35.5, but a lockfile already pinned to 0.34.x satisfies the "
     "declared range, is not moved by the upgrade, and 0.34 has had no release since 2025-11-06.", CB("next sharp 0.34"))
 + li("<b>Un-retired: the Snowsight account-host date did not fire, it moved</b> &mdash; out to "
     "&ldquo;early February 2027 (exact date to be determined)&rdquo;, its third relocation.", CB("BCR-2413"))
 + "</ul><h3>&#10160; Still standing</h3><ul>"
 + li("<b>" + str(nofix) + " rows carry no reachable fix</b> &mdash; pgvector 0.8.7 on zero of seven "
     "managed providers at 22 days, Argo CD 2.x's four CVSS 9.9s never to be patched, StarRocks 3.5's "
     "trio merged-but-untagged for 56 days, Kubernetes shipping nothing in 30 days.", CB("no reachable fix"))
 + li("<b>" + str(ef['inside14']) + " dated rows fall inside fourteen days</b>, " + str(ef['inside7'])
     + " of them inside seven.", CB("dated cutovers"))
 + "</ul>")

# ---------------------------------------------------------------- v-read, per chair
READ = {}
common_tail = (
 "<p><b>Where to spend today's attention.</b></p><ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; " + str(nofix) + " no-reachable-fix rows, five of them new, and "
     "four KEV clocks already expired.", G.archive_link(TODAY))
 + li("<b>Event Horizon</b> &mdash; " + str(ef['inside14']) + " rows inside fourteen days, clustered on "
     "26 Oct to 6 Nov, every one needing a client-side change.", G.archive_link(TODAY))
 + li("<b>Since yesterday</b> &mdash; eight new rows and five date corrections, four of them to claims "
     "this board was confident about.", G.archive_link(TODAY))
 + "</ul>")
READ['oracle'] = (
 "<p class='lede'><b>Edition 101.</b> The competitive question today is not whose engine is faster, it "
 "is <b>whether a customer can find out that they are exposed</b> &mdash; and on that measure the whole "
 "industry failed this week. A CVSS 9.9 LiteLLM privilege escalation got a CVE id on 10-22 and is still "
 "a 404 in GitHub's global advisory database while a <i>Moderate</i> from the same day was syndicated. A "
 "CVSS 9.5 React Server Components RCE returns <b>zero</b> from <code>npm audit</code> nine days after "
 "its fix. OSV holds none of MongoDB's Go, .NET or Ruby advisories. Three of containerd's four October "
 "advisories have no CVE at all. <b>Our own worst row is the mirror image and we should say it "
 "first</b>: Oracle's October CPU names APEX <b>CVE-2026-101521</b>, CVSS 9.8, remote and "
 "unauthenticated, and neither the risk matrix nor NVD names a fixed build for 24.1.x or 24.2.x &mdash; "
 "the public path is a two-release jump to APEX 26.2. A 9.8 a customer <i>can</i> name and cannot patch "
 "is a worse conversation than one nobody has heard of. " + CB("Oracle APEX CVE-2026-101521") + "</p>"
 "<p><b>And the row we have now carried for fifty-seven days is the one to lead with internally.</b> "
 "CVE-2026-21962 is 57 days past its CISA KEV due date with <code>forensicTriage: Yes</code>, the fix "
 "has existed since the January 2026 CPU, and a grep of the published October advisory finds the id "
 "<b>zero times</b>. That is unpatched by omission, which is the one failure mode we cannot blame on a "
 "database. Against it, the competitor failures today are of a different kind &mdash; not &ldquo;the fix "
 "is behind a support contract&rdquo; but <b>&ldquo;the fix does not exist and no feed will tell "
 "you&rdquo;</b>: Argo CD stating plainly that four CVSS 9.9s will never be patched for 2.x, Kubernetes "
 "shipping no release in thirty days after postponing its batch <i>specifically</i> for the Go CVE "
 "fixes, pgvector 0.8.7 reaching not one of seven managed providers in 22 days, MongoDB 8.2 never "
 "receiving the 8.2.13 its own tracker names. <b>Do not trade one for the other in a room.</b> The "
 "honest line is that a published fixed version is table stakes and we are not currently clearing it. "
 + CB("CVE-2026-21962 KEV") + "</p>"
 "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question "
 "Forecast, Gap Ledger, Benchmark Scoreboard, Promise Tracker, Perf Signals, Build Radar, Skills Radar "
 "and Vendor Dossiers <b>carry forward from edition " + PARENT_ED + " unrevised</b>: no competitor "
 "shipped a perf or price claim worth a card today and <code>claims[]</code> did not grow, so the depth "
 "went into the correction pass and the security movement, which is where the day actually was. "
 + G.archive_link(TODAY) + "</p>" + common_tail)
READ['snowflake'] = (
 "<p class='lede'><b>Edition 101 &mdash; Snowflake chair (SIMULATED).</b> Our own worst item today is "
 "an access default we are about to flip <i>for everyone</i>: on <b>2026-10-26, three days out, agents "
 "begin defaulting to <code>dashboard_data_access: TRUE</code></b>, which lets an agent answering a "
 "question about a dashboard query the <b>full underlying tables</b> rather than the columns the tiles "
 "show, bounded only by the asking user's role. The opt-out is a specification replace, so omitted "
 "fields are lost. <b>And it is not in a bundle</b>, so "
 "<code>SYSTEM$SHOW_ACTIVE_BEHAVIOR_CHANGE_BUNDLES</code> will not show it and a bundle-based change "
 "process misses it entirely &mdash; along with the November Legacy Notebook execution cutoff, the "
 "10-13 Cortex evaluation default flip, and the 10-19 Feature Store billing change. Four of this "
 "window's biggest behaviour changes bypassed the mechanism customers actually monitor. " + CB("dashboard_data_access") + "</p>"
 "<p>Where we are genuinely exposed to scrutiny: <b>we now publish a patched version of "
 "&ldquo;None&rdquo;</b>. CVE-2026-86597 wrote auth tokens, query-result master keys, pre-signed URLs "
 "and SAML assertions into driver diagnostic logs, and the Go v1 driver has no fix at all &mdash; four "
 "sources agree, including our own advisory table &mdash; while our client-version policy still lists "
 "Go 1.11.2 as supported. So our platform will keep accepting a driver we ourselves document as "
 "unpatchable. Against Oracle we can still point at a published fixed version for every other driver, "
 "which is more than their APEX 9.8 has. " + CB("Snowflake CVE-2026-86597 Go driver") + "</p>"
 "<p>And the quiet one that already fired: <b>bundle 2026_07 went enabled-by-default in release "
 "10.37</b>, so <code>ACCESS_HISTORY.invoker_identity</code> is <i>gone from customer accounts "
 "today</i> and replaced by an <code>agents_info</code> ARRAY &mdash; the rewrite is a "
 "<code>LATERAL FLATTEN</code>, not a rename, and any audit query or BI tile reading the old column is "
 "failing right now. " + CB("invoker_identity agents_info BCR-2420") + "</p>" + common_tail)
READ['databricks'] = (
 "<p class='lede'><b>Edition 101 &mdash; Databricks chair (SIMULATED).</b> Two cutovers inside eight "
 "days and both make a customer repoint something: the <b>Beta Genie MCP endpoint sunsets "
 "2026-10-31</b>, and three pay-per-token models retire 2026-10-30 with a fourth on 11-05. The Genie "
 "one carries a trap worth owning: <b>it is two changes, not one</b> &mdash; the URL moves to "
 "<code>system.ai.genie_one_mcp</code> <i>and</i> the on-behalf-of-user OAuth scope changes from "
 "<code>genie</code> to <code>ai-gateway</code>, so a URL-only migration fails auth and a smoke test "
 "reusing a cached token will not catch it. " + CB("Genie MCP endpoint sunset") + "</p>"
 "<p>The model-retirement runway is a support burden we are choosing. DeepSeek V4 Flash retires 11-05 "
 "and the replacement we name, V4.1 Flash, <b>itself retires 2026-11-19</b> &mdash; so a customer who "
 "follows our guidance literally re-migrates in four weeks. Point them at the <b>1017 checkpoint</b> "
 "directly. " + CB("Databricks retired models policy") + "</p>"
 "<p>And the governance claim to stop making until the asymmetry closes: <b>our write-capable agent "
 "surface is GA while the control for it is Beta.</b> Jailbreak screening of MCP tool <i>results</i> "
 "&mdash; the only place a server that rewrites its own tool metadata at runtime is visible &mdash; "
 "entered Beta on 10-21, after the capability shipped. Worse, the entitlement enforcement we announced "
 "for 09-14 <b>does not do what our own doc says</b>: the console path now forces an explicit choice, "
 "but a principal added through the API or Terraform still <i>silently inherits</i> the workspace "
 "<code>users</code> group's entitlements for backward compatibility. Specify entitlements explicitly "
 "or the enforcement buys nothing. " + CB("Databricks entitlement migration") + "</p>" + common_tail)
READ['bigquery'] = (
 "<p class='lede'><b>Edition 101 &mdash; BigQuery chair (SIMULATED).</b> On <b>2026-10-30, seven days "
 "out, TabFM moves to per-token billing</b> &mdash; and the finding that should worry us is not the "
 "price, it is that <b>nothing we ship can cap it</b>. The daily AI token quotas we GA'd on 10-14 are "
 "scoped to Gemini-backed generative functions; TabFM, TimesFM, <code>AI.PREDICT</code> and "
 "<code>AI.FORECAST</code> return zero hits in our own cost-control doc. "
 "<code>maximum_bytes_billed</code> caps the wrong metric and a reservation covers the wrong half. So "
 "from Friday an Enterprise customer with <code>AI.PREDICT</code> in a scheduled query goes from zero "
 "marginal cost to metered, silently, with only a Cloud Billing budget &mdash; which our own post calls "
 "a broad backstop that is not instant. " + CB("TabFM token pricing") + "</p>"
 "<p>The detail a customer will find before we do: <b>a TabFM token is a table cell</b>, so the bill "
 "scales with rows &times; columns &times; ensembles rather than bytes scanned &mdash; roughly "
 "<b>$27 per 10M-row run at one ensemble and $218 at eight</b> &mdash; and <code>n_ensembles</code> is "
 "service-controlled with no parameter on <code>AI.PREDICT</code> to set it. <b>They cannot compute "
 "their own charge from our documented API.</b> " + CB("TabFM token formula") + "</p>"
 "<p>And the thing to fix in our own copy before anyone screenshots it: the pricing page ships the "
 "literal placeholder <b>&ldquo;[Target Enforcement Date, 12/01/2026]&rdquo;</b> for TimesFM 3.0 token "
 "billing. An unredacted editorial bracket on a live pricing page is the kind of detail that makes a "
 "procurement team doubt every other date on it. " + CB("TimesFM token pricing") + "</p>" + common_tail)

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
flag = ("&#9873; emSign root removed from Chrome 27 Oct &mdash; reissue + rebuild trust stores &middot; "
        "LiteLLM 1.107.0 payload survives pip uninstall &middot; K8s 1.34 EOL 27 Oct with no final patch "
        "&middot; CVE-2026-21962 57d past KEV")
newrb = ('<div class="runbar">'
 '<span class="lbl">Edition</span><span class="val">' + ED + '</span>'
 '<span class="lbl">Generated</span><span class="val">' + GEN + '</span>'
 '<span class="lbl">Model</span><span class="val">claude-opus-5</span>'
 '<span class="lbl">Inputs</span><span class="val">19 briefs &middot; ' + str(len(ser)) + 'd ledger</span>'
 '<span class="lbl">Run tokens</span><span class="val">~3,830k</span>'
 '<span class="lbl">Skills review</span><span class="val">2027-01-01</span>'
 '<span class="flag">' + flag + '</span></div>')
html = html[:rb.start()] + newrb + html[rb.end():]
for stale in ('Edition 100', '2026-10-22 09:13 EDT', '~3,740k', '105d ledger'):
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
open('lens/out_101.html','w',encoding='utf-8').write(html)
par_sz = len(open('lens/index.html',encoding='utf-8').read())
print("\nwrote lens/out_101.html  %d bytes (parent %d, delta %+d)" % (len(html), par_sz, len(html)-par_sz))
