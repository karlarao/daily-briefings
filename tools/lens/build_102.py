"""Edition 102 lens assembler. HTML blocks are built by CONCATENATION, never
%-formatting: ledger prose carries literal % signs (the 09-17/09-20 rule)."""
import json, re, sys, datetime
sys.path.insert(0, 'tools/lens')
import lens_guard as G, lens_extra as X, lens_links as LL
import patch_radar as PR, events_table as ET, longitudinal as LG, ledger_surgery as LS

TODAY = "2026-10-24"; GEN = "2026-10-24 09:36 EDT"; ED = "102"
T0 = datetime.date.fromisoformat(TODAY)
PARENT_ED, PARENT_DATE = "101", "2026-10-23"

L = json.load(open('lens/ledger_102.json'))
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
 + " sit beyond thirty. Two past-dated rows retired today. " + CB("deadline wall") + "</p>"
 + "<p><b>The 26 Oct &ndash; 6 Nov window is now the densest the board has carried, and it is almost "
 + "entirely one vendor category: the data platforms.</b> Snowflake flips agent dashboard access on the "
 + "26th, BigQuery meters TabFM on the 30th, Fabric stops accepting legacy pipeline activities the same "
 + "day, Redshift enforces TLS 1.2 and Databricks sunsets the Beta Genie MCP endpoint on the 31st, and "
 + "Fabric's Foundry custom tool stops working on 6 Nov. <b>Not one of those is a CVE</b>, every one "
 + "needs a client-side change, and they land on five different teams. " + CB("dated cutovers") + "</p>"
 + "<p><b>One of them is not a deadline at all and the board says so deliberately.</b> Fabric's legacy "
 + "Teams and Outlook activities stop being <i>addable</i> on 30 Oct while existing instances keep "
 + "running and stay editable &mdash; a nearer date than the Foundry retirement and a lower consequence. "
 + "Today's Fabric lane flagged that asymmetry itself rather than letting the nearer date read as the "
 + "more urgent one. " + CB("Fabric legacy activities") + "</p>"
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
 + "in the embedded ledger. The shape they share is the window's signature: <b>the fix exists and the "
 + "affected population cannot reach it, cannot see it, or both</b>. " + CB("patch radar") + "</p>"
 + "<p><b>The radar's cap moved from 30 to 35 today, and the reason is a measurement rather than a "
 + "preference &mdash; so it is on the record here.</b> The standing instruction is &ldquo;fix the "
 + "ranking, do not raise the cap&rdquo;, and it is the right instruction whenever a must-show row "
 + "falls because its band is wrong. That is not this edition. <b>Band 0 &mdash; CISA KEV &mdash; alone "
 + "holds 21 rows</b>, the editorial must-show set is 20, and only 6 of those rank into band 0 "
 + "naturally, so <code>band0 &cup; must-show</code> is exactly <b>35</b> and no reordering fits it "
 + "inside 30. 35 is that union, not a round number. " + CB("must-show") + "</p>"
 + "<p><b><code>assert_must_show</code> earned its keep for the eighth consecutive edition and caught "
 + "two genuine defects underneath the cap problem.</b> First, a <code>NO_FIX_RE</code> vocabulary gap: "
 + "the mongo-go-driver row says <i>&ldquo;no v1 backport&rdquo;</i>, and the pattern matched "
 + "<code>no backport</code> but not a qualifier sitting between the two words &mdash; now widened, "
 + "with &ldquo;no backporting policy&rdquo; kept as a negative in the same edit. Second, and more "
 + "interesting: the PgBouncer row sank because its <code>due</code> field described the CVEs and never "
 + "named <b>who is stranded</b>. That is a content defect the ranking correctly surfaced, and today's "
 + "OLTP lane supplied the missing fact &mdash; Azure Database for PostgreSQL ships <b>1.25.2</b>, "
 + "inside the affected range of all six CVEs, with no customer override and no bump since July 2026. "
 + "<b>A row that cannot say who is stranded cannot be ranked as stranded.</b> " + CB("PgBouncer CVE-2026-107350") + "</p>"
 + "<p><b>A correction to a row this board shipped confidently yesterday.</b> The Hudi VARIANT entry "
 + "said &ldquo;silently returns wrong rows &hellip; under Spark 4.1&rdquo;. Today's Open Formats lane "
 + "read the issue rather than the summary and found three errors: it is <b>Spark 4.0.2</b> and the "
 + "issue states <b>4.1+ is not affected</b>; Merge-on-Read reads <b>fail loudly</b> with "
 + "<code>[MALFORMED_VARIANT]</code>; and the durable corruption is Copy-on-Write with the <b>Spark</b> "
 + "record merger persisting <code>metadata</code>/<code>value</code> bytes swapped into the base file, "
 + "while the <b>default Avro merger is correct</b>. That last point is the actionable one and the old "
 + "framing hid it &mdash; there is a mitigation available today. " + CB("Hudi VARIANT corruption") + "</p>"
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
assert cur['urgent'] == 17 and urg_max == 17 and prior_urg == 16, (cur['urgent'], urg_max, prior_urg)
lt = ["<table class='tbl'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th><th>Competitors</th>"
      "<th>DB HW</th><th>High</th><th>Urgent lanes</th></tr></thead><tbody>"]
for r in ser[-16:]:
    lt.append("<tr><td>" + r['date'] + "</td><td>" + str(r['items']) + "</td><td>" + str(r.get('oracle',0))
              + "</td><td>" + str(r.get('comp',0)) + "</td><td>" + str(r.get('dbhw',0)) + "</td><td>"
              + str(r.get('high',0)) + "</td><td>" + str(r['urgent']) + "</td></tr>")
lt.append("</tbody></table>")
longi_body = (
 "<p class='lede'>" + str(len(ser)) + " days of public ledger. Today: <b>" + str(cur['items'])
 + " items</b> across 19 lanes and <b>" + str(cur['urgent']) + " urgent lanes &mdash; a series high</b>, "
 + "against a previous ceiling of " + str(prior_urg) + ". The last eight runs read " + run8 + ", mean "
 + ("%.1f" % mean14) + " over fourteen days. The series high for items excluding today is "
 + str(hi_items['items']) + " on " + hi_items['date'] + ". " + CB("longitudinal") + "</p>"
 + "<p><b>" + str(cur['urgent']) + " urgent lanes out of 19 was audited one row at a time rather than "
 + "trimmed, and the honest reading is that only two lanes could defensibly have returned "
 + "<code>ok</code>.</b> Every one of the " + str(cur['urgent']) + " survives the definition applied "
 + "literally: <b>four CISA KEV clocks already expired</b> (Oracle 58 days with "
 + "<code>forensicTriage: Yes</code>, Apple 11 with no fix for the iOS 18.7.x train, LiteLLM 38, "
 + "Atlassian 6 and that one is Bitbucket and Bamboo), <b>eleven lanes carrying a fix their population "
 + "cannot reach</b>, and a cutover wall of " + str(ef['inside14']) + " dated rows inside fourteen days. "
 + "<b>But the flag count overstates the day's breadth</b>: " + str(cur['urgent']) + " flags cover "
 + "roughly <b>20 distinct stories</b>, and two root causes account for seven of them &mdash; the "
 + "eMudhra CA compromise reaches App Dev, DevOps, Oracle, Mobile and AI Daily as five different "
 + "remediations of one key disclosure, and litellm is shared by AI Daily and AI App Dev. Counting "
 + "lanes is not counting problems. " + CB("flag calibration") + "</p>"
 + "<p><b>The two <code>ok</code> lanes are the discrimination evidence and both wrote out their "
 + "reasoning, one of them in seven numbered points.</b> AI Hardware pulled the KEV catalog itself, "
 + "found zero of 35 additions touching GPU or AI infrastructure, and declined a <b>CVSS 10.0</b> "
 + "AIStore RCE on dates &mdash; the fix shipped four weeks before the bulletin. It also took Isaac Lab "
 + "seriously as an unreachable-fix candidate (its advisory named a <i>beta</i> as the only fix) before "
 + "reasoning it down to &ldquo;expensive, not unreachable&rdquo; once 3.0.0 went GA. Database Hardware "
 + "reported a month with <b>no CVE at all</b> rather than padding, and read two EPYC bulletins' "
 + "revision histories to establish that a 2026-09-24 &ldquo;last updated&rdquo; stamp was editorial "
 + "rather than new exposure &mdash; a false flag avoided by checking. " + CB("ok lanes") + "</p>"
 + "<p>The High column is still <b>not comparable across days</b>: each run re-derives the severity "
 + "heuristic from the title rather than reading a stored value, so a shift there is a classifier change "
 + "and not a change in the world. <b>Today gave that limitation its sharpest demonstration yet &mdash; "
 + "ten of the eleven rows on the dashboard's own &ldquo;changed&rdquo; card were pure classifier "
 + "artifacts</b>, reading &ldquo;urgent &rarr; normal&rdquo; because the research agents reworded a "
 + "carried headline while the underlying fact sat perfectly still. One real movement survived the pass. "
 + "The 10-23 prediction that this is structural rather than a one-off is now confirmed twice over; "
 + "storing per-item severity in the public ledger remains the durable fix. " + G.archive_link(TODAY) + "</p>"
 + "".join(lt))

# ---------------------------------------------------------------- v-wn (shared)
def li(txt, src): return "<li>" + txt + " " + src + "</li>"
wn_body = (
 "<p class='lede'>Edition " + ED + " against edition " + PARENT_ED + ". <b>Four rows enter the board, "
 + "four carried rows were corrected and two past-dated events retired.</b> Three of the four "
 + "corrections moved a claim this board shipped confidently yesterday, and one of them inverted the "
 + "affected version set. " + CB("since yesterday") + "</p>"
 + "<h3>&#127381; New on the board</h3><ul>"
 + li("<b>Oracle shipped an out-of-band Security Alert one day after its own CPU</b> &mdash; "
     "CVE-2026-91403, CVSS 9.1, network, unauthenticated: the eMudhra compromise reaching Oracle as a "
     "Java SE / GraalVM JSSE trust problem, landing on exactly the Java builds the 20 Oct CPU had just "
     "delivered. No fixed build number is publicly identifiable; the only pointer is MOS-gated.",
     CB("Oracle Security Alert CVE-2026-91403"))
 + li("<b><code>python -m venv</code> still hands out a CA bundle trusting the compromised root</b> "
     "&mdash; every CPython from 3.9 to 3.12 ships an <code>ensurepip</code> pip whose vendored certifi "
     "trusts <code>emSign ECC Root CA - G3</code>, and <b>Python 3.9 has no reachable fix at all</b>: "
     "pip 26.2.2 is the only fixed pip and it requires &ge;3.10. Worse, pip 23.0.1 vendors no truststore, "
     "so an OS trust-store update is irrelevant there.", CB("pip ensurepip certifi emSign"))
 + li("<b>Kubernetes missed its October patch on every supported branch simultaneously</b> &mdash; "
     "1.34.13, 1.35.10, 1.36.6 and 1.37.2 are all 11 days overdue, the last tags were cut 2026-09-23, "
     "and the next window falls <i>after</i> 1.34's EOL. A release-process event, not four coincidences.",
     CB("Kubernetes October patch overdue"))
 + li("<b>Next.js 14 and earlier will never be patched for the unauthenticated image RCE</b> &mdash; "
     "fixed only in 15.5.28 and 16.4.1, with 14.x Unsupported since 2023. The reachable remediation is "
     "not a Next.js upgrade but <code>sharp@^0.35.5</code> directly.", CB("Next.js 14 unsupported"))
 + "</ul><h3>&#128314; Corrections</h3><ul>"
 + li("<b>The Hudi VARIANT row was wrong in three ways, and the correction surfaces a mitigation the "
     "old framing hid.</b> It is <b>Spark 4.0.2</b> and the issue states <b>4.1+ is not affected</b> "
     "&mdash; this board had the affected set inverted. MoR reads <b>fail loudly</b>, not silently. And "
     "the durable corruption is Copy-on-Write with the <b>Spark</b> record merger; the <b>default Avro "
     "merger is correct</b>, so there is something to do today.", CB("Hudi VARIANT corruption"))
 + li("<b>Argo CD: two advisories this window, not four, and the stranded population is wider than "
     "carried.</b> CVE-2026-77459 (9.9, delete hooks escape AppProject restrictions) and CVE-2026-55797 "
     "&mdash; and the advisory text covers <b>2.x <i>and</i> 3.0 through 3.2</b>, with no configuration "
     "setting that applies the project check to delete hooks.", CB("Argo CD CVE-2026-77459"))
 + li("<b>Snowflake's Go v1 &ldquo;patched version: None&rdquo; is accurate, and the reason changes the "
     "remediation.</b> The CNA record encodes v1 and <code>/v2</code> as separate packages; the fix "
     "exists only on the <code>/v2</code> module path, and v1's last release predates the advisories by "
     "five months. It is not a pending backport &mdash; it is an import-path migration.",
     CB("Snowflake CVE-2026-86597 Go driver"))
 + li("<b>The PgBouncer row never named who is stranded, which is why the radar could not rank it.</b> "
     "Azure Database for PostgreSQL ships <b>1.25.2</b> with no customer override and no bump since "
     "July 2026, inside the affected range of all six CVEs &mdash; and CVE-2026-107350 (8.8) has no "
     "configuration workaround.", CB("PgBouncer CVE-2026-107350"))
 + "</ul><h3>&#10160; Still standing</h3><ul>"
 + li("<b>" + str(nofix) + " rows carry no reachable fix</b> &mdash; pgvector 0.8.7 on zero of seven "
     "managed providers at 23 days, Argo CD 2.x&ndash;3.2 never to be patched, MongoDB 8.2's 8.2.13 "
     "never published, Doris 3.1 archived with the CVE live, Angular &le;19 and Next.js &le;14 "
     "permanently unfixed.", CB("no reachable fix"))
 + li("<b>" + str(ef['inside14']) + " dated rows fall inside fourteen days</b>, " + str(ef['inside7'])
     + " of them inside seven, and the 26 Oct &ndash; 6 Nov cluster is almost entirely data platforms.",
     CB("dated cutovers"))
 + li("<b>Scanner blindness through six independent mechanisms in one day</b> &mdash; a repo-only React "
     "advisory, Vitess GHSAs absent from OSV, Mongoose patching with no advisory at all, DocumentDB "
     "hardening with no CVE id, Doris with an empty NVD CPE set, and shaded JDBC dependencies. In every "
     "case the fix existed; only the notification was missing.", CB("scanner blindness"))
 + "</ul>")

# ---------------------------------------------------------------- v-read, per chair
READ = {}
common_tail = (
 "<p><b>Where to spend today's attention.</b></p><ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; " + str(nofix) + " no-reachable-fix rows and four KEV clocks "
     "already expired; the cap moved to 35 because band 0 alone is 21 KEV rows.", G.archive_link(TODAY))
 + li("<b>Event Horizon</b> &mdash; " + str(ef['inside14']) + " rows inside fourteen days, clustered on "
     "26 Oct to 6 Nov and almost entirely data platforms.", G.archive_link(TODAY))
 + li("<b>Since yesterday</b> &mdash; four new rows and four corrections, three of them to claims this "
     "board shipped confidently yesterday.", G.archive_link(TODAY))
 + "</ul>")
READ['oracle'] = (
 "<p class='lede'><b>Edition 102.</b> One CA key disclosure reorganised the whole week, and the thing "
 "worth taking into a room is <i>how</i> the industry fixed it: not by removing a root, but by "
 "denylisting eight SPKI hashes inside the Go toolchain. That is strictly stronger &mdash; it catches "
 "Sectigo's cross-signed copies too, which a root removal structurally cannot &mdash; but it converts a "
 "certificate problem into a <b>rebuild</b> problem, and your slowest-moving binary now defines your "
 "exposure. Eight projects rebuilt inside four days. <b>Kubernetes merged the bump into all four "
 "release branches and shipped nothing</b>, because its October patch is 11 days overdue on every "
 "branch at once, three days before 1.34's EOL. " + CB("eMudhra CA compromise") + "</p>"
 "<p><b>Our own worst row is that we are now on both sides of this.</b> Oracle shipped an out-of-band "
 "Security Alert for <b>CVE-2026-91403</b> (CVSS 9.1, network, unauthenticated) on 21 October &mdash; "
 "one day after our own CPU &mdash; distrusting the compromised intermediates in Java SE and GraalVM "
 "JSSE, landing on exactly the builds the CPU had just delivered. And <b>no fixed build number is "
 "publicly identifiable</b>: the only remediation pointer is a MOS-gated advisory. Set beside "
 "<b>CVE-2026-21962 at 58 days past its KEV due date</b> with <code>forensicTriage: Yes</code> and a "
 "fix that has existed since the <i>January</i> CPU, the pattern a customer can name is that our "
 "publication is harder to act on than our competitors' absence. " + CB("Oracle Security Alert CVE-2026-91403") + "</p>"
 "<p><b>The competitor failures today are of a different kind and the distinction is worth keeping "
 "straight.</b> Theirs is mostly &ldquo;the fix does not exist and no feed will tell you&rdquo; &mdash; "
 "Argo CD stating that 2.x through 3.2 will never be patched, pgvector 0.8.7 reaching none of seven "
 "managed providers in 23 days, MongoDB 8.2 never receiving the 8.2.13 its own tracker names, a React "
 "RCE that <code>npm audit</code> cannot see. Ours is <b>unpatched by omission</b>, which is the one "
 "failure mode we cannot attribute to anyone else. Do not trade one for the other in a room: a "
 "published, reachable fixed version is table stakes and on APEX and 21962 we are not clearing it. "
 + CB("CVE-2026-21962 KEV") + "</p>"
 "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question "
 "Forecast, Gap Ledger, Benchmark Scoreboard, Promise Tracker, Perf Signals, Build Radar, Skills Radar "
 "and Vendor Dossiers <b>carry forward from edition " + PARENT_ED + " unrevised</b>: no competitor "
 "shipped a perf or price claim worth a card today and <code>claims[]</code> did not grow, so the depth "
 "went into the correction pass and the security movement, which is where the day was. "
 + G.archive_link(TODAY) + "</p>" + common_tail)
READ['snowflake'] = (
 "<p class='lede'><b>Edition 102 &mdash; Snowflake chair (SIMULATED).</b> Our own worst item is two "
 "days out and it is an access default, not a bug: on <b>2026-10-26 agents begin defaulting to "
 "<code>dashboard_data_access: TRUE</code> for every account</b>, which lets an agent answering a "
 "dashboard question query the <b>whole underlying tables</b> rather than the columns the tiles show, "
 "bounded only by the asking user's role. The opt-out is a full specification replace, so omitted "
 "fields are silently dropped &mdash; and <b>it is not in a bundle</b>, so a bundle-based change process "
 "misses it entirely. " + CB("dashboard_data_access") + "</p>"
 "<p>Where we are exposed to scrutiny, with one piece of credit we should claim: our Go v1 driver's "
 "patched version is the literal string <b>&ldquo;None&rdquo;</b>, and today's reading establishes that "
 "this is <i>accurate</i> rather than a data-quality bug &mdash; the fix lives on the <code>/v2</code> "
 "module path and v1's last release predates the advisories by five months, so remediation is an "
 "import-path migration we should say out loud instead of letting a customer discover it. The credit: "
 "<b>the scanner-blindness problem on these CVEs has closed</b>. GHSA-qqj6-54q6-cxv6 now resolves "
 "across PyPI, npm, Maven and both Go module paths. A September lockfile scan that came back clean "
 "should be re-run. " + CB("Snowflake CVE-2026-86597 Go driver") + "</p>"
 "<p>And the row that keeps teaching the same lesson: <b>BCR-2413 relocated for a third time</b>, now "
 "reading &ldquo;early February 2027, exact date to be determined&rdquo;. It did not fire on 16 Oct; it "
 "moved. Recording a vendor's <i>precision</i> rather than its number is why this board did not have to "
 "retract a date. " + CB("BCR-2413") + "</p>" + common_tail)
READ['databricks'] = (
 "<p class='lede'><b>Edition 102 &mdash; Databricks chair (SIMULATED).</b> Four dated cutovers inside "
 "twelve days and every one makes a customer repoint something. The <b>Beta Genie MCP endpoint sunsets "
 "2026-10-31</b>, and it carries a trap we own: <b>it is two changes, not one</b> &mdash; the URL moves "
 "to <code>system.ai.genie_one_mcp</code> <i>and</i> the OAuth scope changes from <code>genie</code> to "
 "<code>ai-gateway</code>, so a URL-only migration fails auth and a smoke test on a cached token will "
 "not catch it. " + CB("Genie MCP endpoint sunset") + "</p>"
 "<p>The model-retirement runway is a support burden we are choosing. DeepSeek V4 Flash retires 11-05 "
 "and the replacement we name, V4.1 Flash, <b>itself retires 2026-11-19</b> &mdash; a customer who "
 "follows our guidance literally re-migrates in four weeks. Point them at the <b>1017</b> checkpoint "
 "directly. And the 11-18 <code>variantShredding</code> default has a worse problem: <b>our own two "
 "docs disagree on the remediation</b> &mdash; <code>whats-coming</code> says upgrade to DBR 16.4+, the "
 "feature doc requires <b>17.3+</b>, and 16.4 is below 17.3, so a customer following the migration "
 "advice still cannot read the tables. " + CB("Databricks variantShredding") + "</p>"
 "<p>The governance asymmetry to stop defending: <b>our write-capable agent surface is GA while the "
 "control for it is Beta.</b> Jailbreak screening of MCP tool <i>results</i> &mdash; the only place a "
 "server that rewrites its own tool metadata at runtime is visible &mdash; entered Beta on 10-21, after "
 "the capability shipped. Only the Genie endpoint got a hard sunset; <code>/api/2.0/mcp/sql</code>, AI "
 "Search and UC functions got &ldquo;existing integrations can continue&rdquo; with no date, and the "
 "same page notes they <b>bypass Unity Gateway</b> and appear in no tracing table. "
 + CB("Databricks managed MCP") + "</p>" + common_tail)
READ['bigquery'] = (
 "<p class='lede'><b>Edition 102 &mdash; BigQuery chair (SIMULATED).</b> On <b>2026-10-30, six days "
 "out, TabFM moves to per-token billing</b> &mdash; and what should worry us is not the price, it is "
 "that <b>nothing we ship can cap it</b>, and that is now documented rather than inferred. Our own "
 "quotas page puts <code>AI.PREDICT</code> under <i>Predictive</i> AI functions, a category separate "
 "from the <i>Generative</i> functions the daily token quotas cover; the string appears exactly once in "
 "a 134k-character page, in that taxonomy list, with no quota row anywhere. Custom query quotas meter "
 "<b>bytes on on-demand pricing only</b>, so an Enterprise reservation has no instrument at all. "
 + CB("TabFM token pricing") + "</p>"
 "<p>The detail a customer will find before we do: the billing formula multiplies by "
 "<b><code>n_ensembles</code></b>, which is <b>not an <code>AI.PREDICT</code> argument</b> and is "
 "documented nowhere &mdash; a service-side multiplier on both input and output tokens. <b>They cannot "
 "compute their own charge from our published API.</b> And because TabFM is in-context learning, the "
 "training rows are re-billed on <i>every call</i>: there is no trained artifact to amortise, which "
 "inverts the cost curve BQML taught everyone. " + CB("TabFM token formula") + "</p>"
 "<p>Two things to fix in our own copy before anyone screenshots them: the pricing page still ships the "
 "literal placeholder <b>&ldquo;[Target Enforcement Date, 12/01/2026]&rdquo;</b> for TimesFM 3.0, and "
 "our reusable-column-aliases GA is an <b>org- or project-wide DDL flag</b> whose own doc heads the "
 "hazard &ldquo;semantic drift&rdquo; &mdash; one admin statement changes name resolution for every "
 "existing query, with no per-query or per-dataset opt-in. " + CB("reusable column aliases") + "</p>"
 + common_tail)
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
flag = ("&#9873; litellm cosign key rotated TODAY &mdash; repin every verify gate &middot; emSign ECC root leaves Chrome 27 Oct &middot; Atlassian KEV 6d overdue (Bitbucket + Bamboo) &middot; K8s 1.34 EOL 27 Oct, Oct patch cycle 11d late &middot; CVE-2026-21962 58d past KEV")
newrb = ('<div class="runbar">'
 '<span class="lbl">Edition</span><span class="val">' + ED + '</span>'
 '<span class="lbl">Generated</span><span class="val">' + GEN + '</span>'
 '<span class="lbl">Model</span><span class="val">claude-opus-5</span>'
 '<span class="lbl">Inputs</span><span class="val">19 briefs &middot; ' + str(len(ser)) + 'd ledger</span>'
 '<span class="lbl">Run tokens</span><span class="val">~3,875k</span>'
 '<span class="lbl">Skills review</span><span class="val">2027-01-01</span>'
 '<span class="flag">' + flag + '</span></div>')
html = html[:rb.start()] + newrb + html[rb.end():]
for stale in ('Edition 101', '2026-10-23 09:51 EDT', '~3,830k', '106d ledger'):
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
open('lens/out_102.html','w',encoding='utf-8').write(html)
par_sz = len(open('lens/index.html',encoding='utf-8').read())
print("\nwrote lens/out_102.html  %d bytes (parent %d, delta %+d)" % (len(html), par_sz, len(html)-par_sz))
