"""Edition 100 lens assembler. HTML blocks are built by CONCATENATION, never
%-formatting: ledger prose carries literal % signs (the 09-17/09-20 rule)."""
import json, re, sys, datetime
sys.path.insert(0, 'tools/lens')
import lens_guard as G, lens_extra as X, lens_links as LL
import patch_radar as PR, events_table as ET, longitudinal as LG, ledger_surgery as LS

TODAY = "2026-10-22"; GEN = "2026-10-22 09:13 EDT"; ED = "100"
T0 = datetime.date.fromisoformat(TODAY)
PARENT_ED, PARENT_DATE = "099", "2026-10-21"

L = json.load(open('lens/ledger_100.json'))
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
    """Citation for a ledger row: its own url, else SEEN dates, never the event date."""
    return LL.cite(url or row.get('url'), row.get('last_seen'), row.get('first_seen'), TODAY, today=TODAY)
def CB(title, *dates):
    """Citation mined from today's briefs by title."""
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
    k = (r.get('k') or '').lower(); t = (r.get('t') or '').lower()
    for key, lab in LANE.items():
        if key in k or key in t[:160]: return lab
    return r.get('lane') or '&mdash;'
# render() takes DICTS keyed by row key, not callables, and returns (html, count).
lane_of = {r['k']: _lane(r) for r in L['events']}
act_of  = {r['k']: (r.get('act') or '&mdash;') for r in L['events']}
ev_tbl, ev_shown = ET.render(L['events'], TODAY, horizon=60, lane_of=lane_of, act_of=act_of)
ev_body = (
 "<p class='lede'>" + str(ef['total']) + " dated and undated items on the board: <b>" + str(ef['inside14'])
 + " fall inside fourteen days</b>, " + str(ef['inside7']) + " inside seven, " + str(ef['undated'])
 + " are deliberately undated because the vendor published no day, and " + str(ef['beyond30'])
 + " sit beyond thirty. Two past-dated rows retired into the ledger this edition. "
 + "The 26 Oct &ndash; 1 Nov stretch is the densest cutover window this board has carried. " + CB("deadline wall") + "</p>"
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
 + "the embedded ledger. <b>The cap moved 26 &rarr; 30 this edition, deliberately.</b> The standing rule is "
 + "to fix the ranking rather than raise the cap, and that is right when a row sorts below rows a reader "
 + "would act on later &mdash; measured today it is not: <b>band 0 alone holds 21 rows</b> (overdue CISA KEV "
 + "clocks, two CONFIRMED in-the-wild compromises, live KEV inside fourteen days) and the next eight are the "
 + "re-measured Critical no-fix rows. Every row above the line is genuinely act-now, so 26 &mdash; a number "
 + "sized against a twelve-row band 0 &mdash; became the wrong figure, not the sort. " + CB("patch radar") + "</p>"
 + "<p><b>Two ranking defects were fixed at source and both were caught by <code>assert_must_show</code>, "
 + "for the sixth consecutive edition.</b> (1) <b>The day's single worst item ranked #59.</b> LiteLLM 1.107.0 "
 + "shipped a credential stealer and scored <b>CVSS 0.0</b> &mdash; because the attacker published malware "
 + "rather than filing a CVE. <code>sev_tier</code> already refuses to read &ldquo;unscored&rdquo; as "
 + "&ldquo;low&rdquo;, but band 1 is long and every measured Critical outranks an unscored row inside it. "
 + "Band 0 now also takes a <b>confirmed in-the-wild compromise</b>, with or without a clock, on the same "
 + "reasoning the KEV clause already uses: a package that has already executed in your environment is "
 + "<i>past</i> exploitation, and the action is not &ldquo;patch&rdquo; but &ldquo;assume breach and "
 + "rotate&rdquo;. (2) <code>NO_FIX_RE</code> now matches <b>&ldquo;no backport&rdquo;</b> &mdash; the "
 + "natural phrase for a stable-only fix, and the reason the THP row fell to band 3. Two rows came OFF the "
 + "must-show list instead of being forced on: React RSC and Lakekeeper both have a <b>reachable</b> fix, so "
 + "band 3 was correct and the guard was right to refuse them. " + CB("must-show") + "</p>"
 + "".join(rows_html))

# ---------------------------------------------------------------- v-longitudinal
prior = [r for r in ser if r['date'] < TODAY]
cur = ser[-1]
hi_items = max(prior, key=lambda r: r['items'])
urg = [r['urgent'] for r in ser[-8:]]
run8 = ", ".join(str(u) for u in urg)
mean14 = sum(r['urgent'] for r in ser[-14:]) / min(14, len(ser))
lt = ["<table class='tbl'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th><th>Competitors</th>"
      "<th>DB HW</th><th>High</th><th>Urgent lanes</th></tr></thead><tbody>"]
for r in ser[-16:]:
    lt.append("<tr><td>" + r['date'] + "</td><td>" + str(r['items']) + "</td><td>" + str(r.get('oracle',0))
              + "</td><td>" + str(r.get('competitors',0)) + "</td><td>" + str(r.get('dbhw',0)) + "</td><td>"
              + str(r.get('high',0)) + "</td><td>" + str(r['urgent']) + "</td></tr>")
lt.append("</tbody></table>")
longi_body = (
 "<p class='lede'>" + str(len(ser)) + " days of public ledger. Today: <b>" + str(cur['items'])
 + " items</b> across 19 lanes and <b>" + str(cur['urgent']) + " urgent lanes</b>. The last eight runs read "
 + run8 + ", mean " + ("%.1f" % mean14) + " over fourteen days; the series high for items excluding today is "
 + str(hi_items['items']) + " on " + hi_items['date'] + ". " + CB("longitudinal") + "</p>"
 + "<p><b>Read the Items column as research volume, not news volume.</b> Yesterday's 607 was the lowest in "
 + "weeks for a reason that was ours and not the world's &mdash; the research agents ran on a smaller model "
 + "and produced 7&ndash;16k-character briefs. Today's run used no model override and the briefs came back "
 + "<b>21.6k&ndash;48.7k characters</b>, which is why the count returns to " + str(cur['items']) + ". "
 + "<b>The matcher tells the same story from the other side:</b> the cross-day match rate recovered from "
 + "<b>7.6% to 21.8%</b> (189 of 869), and the cause was measured rather than guessed &mdash; "
 + "verdict-shaped headlines (&ldquo;CONFIRMED: date unchanged&rdquo;), which share almost no vocabulary with "
 + "the fact they describe, fell from <b>5.9% of titles to 0.1%</b> after the run told every agent to "
 + "headline the fact first and the verdict in a trailing clause. " + CB("ledger health") + "</p>"
 + "<p>The High column is still <b>not comparable across days</b>: each run re-derives the severity "
 + "heuristic from the title rather than reading a stored value, so a shift there is a classifier change, not "
 + "a change in the world. Storing per-item severity in the public ledger remains the queued fix. "
 + G.archive_link(TODAY) + "</p>"
 + "".join(lt))

# ---------------------------------------------------------------- v-wn (shared)
def li(txt, src): return "<li>" + txt + " " + src + "</li>"
wn_body = (
 "<p class='lede'>Edition " + ED + " against edition " + PARENT_ED + ". <b>Five rows enter the board, eight "
 + "are enriched, two events retire, and no dated row needed correcting</b> &mdash; which is itself the "
 + "finding: every date this board carries survived contact with today's primary sources. " + CB("since yesterday") + "</p>"
 + "<h3>&#127381; New on the board</h3><ul>"
 + li("<b>LiteLLM 1.107.0 was a malicious release</b> &mdash; a credential stealer plus an hourly remote-code "
     "loader, served from PyPI and the Docker <code>latest</code> tag for ~1h45m on 2026-10-21. It executed at "
     "<i>every</i> Python interpreter startup and took the proxy database, where a fleet's upstream provider "
     "keys are concentrated. <b>No patch undoes exposure.</b>", CB("LiteLLM 1.107.0 malicious release"))
 + li("<b>eMudhra/emSign CA keys declared compromised</b> &mdash; no single CVE, six runtimes, six different "
     "remediations, and Go's denylist is compiled into the binary so a static service needs a rebuild.", CB("eMudhra CA compromised"))
 + li("<b>sentence-transformers CVE-2026-68770, CVSS 9.8</b> &mdash; loading a model from a local path bypassed "
     "<code>trust_remote_code</code> and executed custom Python.", CB("sentence-transformers CVE-2026-68770"))
 + li("<b>mem0 CVE-2026-115324, CVSS 9.2</b> &mdash; agent memory is now a path from untrusted content into a "
     "production Databricks warehouse, and OSV had no record on publication day.", CB("mem0 CVE-2026-115324 SQL injection"))
 + li("<b>Lakekeeper signed S3 requests for objects outside the table location</b> &mdash; fixed 0.13.7/0.14.1 "
     "with <b>no CVE, no GHSA and an empty advisories page</b>.", CB("Lakekeeper S3 remote signing"))
 + "</ul><h3>&#128314; Movement on rows already carried</h3><ul>"
 + li("<b>Oracle APEX 9.8:</b> NVD now carries the record and <i>also</i> names no fixed version &mdash; a second "
     "primary source confirming the gap. APEX 26.2 (2026-10-06) is outside every affected range, so <b>26.1.x has "
     "a remedy and 24.1.x/24.2.x have none</b>.", CB("Oracle APEX CVE-2026-101521"))
 + li("<b>CVE-2026-21962 is 56 days past its KEV due date</b>, and the KEV product is Oracle HTTP Server / "
     "WebLogic Proxy Plug-in &mdash; the tier in front of the database, which a DBA does not own.", CB("CVE-2026-21962 KEV"))
 + li("<b>The October CPU has SIX rows at CVSS 10.0, not one</b> &mdash; a correction to yesterday's count. None "
     "is the database; Database Server's own maximum is 9.8.", CB("October 2026 CPU six 10.0"))
 + li("<b>The THP data-loss bug will never trickle down, because the code was deleted rather than patched</b> "
     "&mdash; fixed only in stable 7.1.4, mainline carrier removed, no backport to any longterm series.", CB("CVE-2026-68086 khugepaged"))
 + li("<b>Iceberg's equality-delete ban is now merged spec text</b> (PR #17783, 2026-09-29) and V4 still has no "
     "date &mdash; while the Flink migration task that makes it survivable shipped in 1.12.0.", CB("Iceberg PR 17783 equality deletes"))
 + li("<b>Fabric Runtime 2.0 is 22 days past its own published default-flip window</b> with no flip and no new "
     "date.", CB("Fabric Runtime 2.0 default"))
 + li("<b>Redshift's TLS floor now has a published pre-flight query per flavour</b> &mdash; and the driver "
     "upgrade that satisfies it silently adds a <code>verify-full</code> hostname check.", CB("Redshift TLS 1.2 minimum"))
 + li("<b>parquet-java's NVD record still contradicts itself</b>, and there is no OSV or GHSA record at all, so "
     "a human and a scanner reading it reach opposite conclusions.", CB("parquet CVE-2026-73334"))
 + "</ul><h3>&#10160; Still standing</h3><ul>"
 + li("<b>" + str(nofix) + " rows carry no reachable fix</b> (was 35) &mdash; Kubernetes still ships no binary "
     "with the Go CONNECT-desync fixes 14 days on, Argo CD's four 9.9s will never be patched for 2.x/3.0&ndash;3.2, "
     "pgvector 0.8.7 reaches no managed provider, Doris 2.x/3.x gets no backport.", CB("no reachable fix"))
 + li("<b>" + str(ef['inside14']) + " dated rows fall inside fourteen days</b>, clustered on 26 Oct &ndash; 1 Nov.", CB("dated cutovers"))
 + "</ul>")

# ---------------------------------------------------------------- v-read, per chair
READ = {}
common_tail = (
 "<p><b>Where to spend today's attention.</b></p><ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; band 0 is 21 rows deep, including two confirmed compromises and four "
     "overdue KEV clocks.", G.archive_link(TODAY))
 + li("<b>Event Horizon</b> &mdash; " + str(ef['inside14']) + " rows inside fourteen days, most of them between "
     "26 Oct and 1 Nov.", G.archive_link(TODAY))
 + li("<b>Since yesterday</b> &mdash; five new rows, eight enriched, and no date needing correction.", G.archive_link(TODAY))
 + "</ul>")
READ['oracle'] = (
 "<p class='lede'><b>Edition 100.</b> The competitive picture today is not a product claim, it is a question "
 "every vendor on this board now has to answer: <b>can you tell your customers what you shipped them?</b> "
 "LiteLLM's 1.107.0 release carried a credential stealer out of a lookalike build org while the upstream "
 "GitHub source stayed clean &mdash; so reading the repository told you nothing and <b>pinning the version "
 "gave you the malware</b>. On the same two days the eMudhra/emSign intermediate CA keys were declared "
 "compromised with no single CVE to scan for, and two Critical 9.5 unauthenticated RCEs in Next.js and React "
 "Server Components turned out never to have been published to the global advisory database at all. "
 "<b>Our own worst row is the mirror image of that and we should say so first</b>: Oracle's October CPU names "
 "APEX <b>CVE-2026-101521</b>, CVSS 9.8, remote and unauthenticated, and neither the risk matrix nor NVD names "
 "a fixed build for 24.1.x or 24.2.x. A 9.8 a customer can name and cannot patch is a worse conversation than "
 "one they have not heard of. " + CB("Oracle APEX CVE-2026-101521") + "</p>"
 "<p>The structural counter-story is ours to make carefully. <b>Oracle publishes affected ranges and not fixed "
 "versions by convention</b>, with patch availability behind My Oracle Support &mdash; which is exactly why "
 "the APEX question is unanswerable from public sources, and it is the same convention that makes "
 "&ldquo;is there a 19.33?&rdquo; unanswerable too. Against that, the competitor failures today are of a "
 "different kind: not &ldquo;the fix is behind a support contract&rdquo; but <b>&ldquo;the fix does not exist "
 "and no feed will tell you&rdquo;</b> &mdash; Argo CD stating plainly that four CVSS 9.9 repo-server bugs "
 "will never be patched for 2.x, Kubernetes shipping no binary with the Go desync fixes fourteen days on while "
 "its own branches carry them, pgvector 0.8.7 reaching not one managed Postgres provider in 21 days. "
 "<b>Do not trade one for the other in a room.</b> The honest line is that a published fixed version is table "
 "stakes and we should be first to it. " + CB("Argo CD no v2 fix") + "</p>"
 "<p><b>The quarterly Skills and Build re-rank is due 2027-01-01.</b> Claim Watch, Mirror, Question Forecast, "
 "Gap Ledger, Benchmark Scoreboard, Promise Tracker, Perf Signals, Build Radar, Skills Radar and Vendor "
 "Dossiers <b>carry forward from edition " + PARENT_ED + " unrevised</b>: no competitor shipped a perf or price "
 "claim worth a card today and <code>claims[]</code> did not grow, so the depth went into the security and "
 "deadline movement where the day actually was. " + G.archive_link(TODAY) + "</p>" + common_tail)
READ['snowflake'] = (
 "<p class='lede'><b>Edition 100 &mdash; Snowflake chair (SIMULATED).</b> Our own worst item today is not a CVE, "
 "it is an access change that already fired: <b>BCR-2413 moved Snowsight sign-in to a per-account host on "
 "2026-10-16 with no opt-out</b>, and our own page still reads &ldquo;(Pending)&rdquo; six days later. Any "
 "customer behind a proxy, firewall or ZTNA has users who simply cannot sign in until they allow the new "
 "<code>ACCOUNT_PUBLIC</code> host. <b>That is a self-inflicted availability incident wearing a behaviour-change "
 "label</b>, and the second instance this quarter &mdash; BCR-2451 does the same to Streamlit and SPCS "
 "endpoints. The competitive read: our bundle mechanism is excellent at describing SQL semantics and bad at "
 "flagging a change that is really a network chore. " + CB("BCR-2413 Snowsight") + "</p>"
 "<p>Where we are genuinely exposed to scrutiny: <b>CVE-2026-86597</b> wrote auth tokens, result-encryption "
 "keys, pre-signed URLs and SAML assertions into driver diagnostic logs, and the <b>Go v1 driver has no fixed "
 "release at all</b> &mdash; the fix exists only on the <code>/v2</code> module path while our own support "
 "policy still lists Go 1.11.2 as supported. Deleting old logs is half the remediation and nobody does it. "
 "Against Oracle we can still point at a published fixed version for every other driver, which is more than "
 "their APEX 9.8 has. " + CB("Snowflake CVE-2026-86597 driver logs") + "</p>"
 "<p>And the thing to stop selling as a pure win: <b>we are trading determinism for cost and convenience</b> "
 "&mdash; cached <code>AI_COMPLETE</code> responses, swapped evaluation judge models we ourselves say are "
 "&ldquo;not directly comparable&rdquo;, approximate aggregates inside incremental refresh. A customer running "
 "a CI assertion on a number will find it moves. " + CB("Cortex response caching") + "</p>" + common_tail)
READ['databricks'] = (
 "<p class='lede'><b>Edition 100 &mdash; Databricks chair (SIMULATED).</b> Three cutovers inside fourteen days "
 "and every one makes a customer repoint something: the <b>Genie MCP endpoint sunsets 2026-10-31</b>, three "
 "pay-per-token models retire 2026-10-30, and DeepSeek V4 Flash goes 2026-11-05. The trap is ours: the "
 "replacement we recommended in September for V4 Pro was <i>V4.1 Flash</i>, and V4.1 Flash now retires "
 "2026-11-19 &mdash; so a customer who took our advice literally re-migrates in four weeks. <b>A 30-day "
 "retirement runway on a pinned model id is a support burden we are choosing.</b> " + CB("Genie MCP endpoint sunset") + "</p>"
 "<p>Today's genuine exposure arrived through the agent surface rather than the platform: <b>mem0's "
 "CVE-2026-115324 injects SQL into a Databricks SQL warehouse through stored agent memory</b> &mdash; "
 "attacker-influenced content an agent <i>writes</i>, which no request-inspecting control sees. We shipped "
 "jailbreak screening for MCP tool <i>results</i> in the same window, which is the right half of the problem "
 "and arrived after the capability. Unity Gateway's Skills API is Beta while Genie One already executes code "
 "with the caller's permissions. " + CB("mem0 CVE-2026-115324") + "</p>"
 "<p>The quiet one to get ahead of: <b>deleting a Unity Catalog pipeline now RETAINS its tables by default</b>, "
 "a behaviour reversal that leaves teardown automation paying for orphaned, unmaintainable tables. "
 + CB("Unity Catalog pipeline retains tables") + "</p>" + common_tail)
READ['bigquery'] = (
 "<p class='lede'><b>Edition 100 &mdash; BigQuery chair (SIMULATED).</b> Our release notes this window are an "
 "AI-function changelog: <b>33 of 34 entries are features, and zero touch slots, editions, BI Engine, "
 "materialized views or partitioning</b>. Read generously that is a mature engine; read honestly it means the "
 "surface that determines a customer's bill got no attention while token-priced surfaces multiplied. "
 "<b>TabFM moves to token billing on 2026-10-30</b> and TimesFM 3.0 on 2026-12-01 &mdash; and our own pricing "
 "page still ships that second date as a bracketed placeholder. " + CB("TabFM token pricing") + "</p>"
 "<p>The gap a customer will find before we do: <b>daily AI token quotas went GA and do not cover the two "
 "things moving to token billing.</b> Embeddings, TabFM's <code>AI.PREDICT</code> and TimesFM's "
 "<code>AI.FORECAST</code> are all outside the quota surface, so from 30 Oct there is token-metered spend with "
 "no token guardrail in front of it &mdash; only Cloud Billing caps, which our own post says are not instant. "
 "Defaults are ~$25k/day of input before anything blocks. " + CB("daily AI token quotas") + "</p>"
 "<p>And the reliability datapoint to answer honestly: a <b>single-zone power loss in europe-west2 degraded "
 "BigQuery region-wide for 6h10m</b> &mdash; capacity exhaustion and control-plane timeouts <i>outside</i> the "
 "failed zone. If a customer's DR plan assumes serverless is immune to zonal events, this is their "
 "counterexample. " + CB("europe-west2 zonal power loss") + "</p>" + common_tail)

# ---- splice shared sections; seed oracle body into the chair-flipped shell
SEC = {'v-events': ev_body, 'v-patch': patch_body, 'v-longitudinal': longi_body,
       'v-wn': wn_body, 'v-read': READ['oracle']}
chips = {'v-read': "edition " + ED + " &middot; " + TODAY,
         'v-wn': "vs edition " + PARENT_ED,
         'v-events': str(ef['total']) + " rows &middot; " + str(ef['inside14']) + " inside 14d",
         'v-patch': str(len(shown)) + " of " + str(len(L['patch'])) + " &middot; " + str(nofix) + " no fix",
         'v-longitudinal': str(len(ser)) + " days"}
html = G.splice_sections(html, SEC, chips=chips, expect=15)
print("spliced %d sections (of 15 visited)" % len(SEC))

# ---- povContent: per-chair v-read bodies + meta
m = re.search(r'(<script type="application/json" id="povContent">)(.*?)(</script>)', html, re.S)
P = json.loads(m.group(2))
for ch in ('oracle', 'snowflake', 'databricks', 'bigquery'):
    P['content'][ch]['v-read'] = {'t': "Today's Read", 'e': 'PINNED',
                                  'c': "edition " + ED + " &middot; " + TODAY, 'h': READ[ch]}
html = html[:m.start(2)] + json.dumps(P) + html[m.end(2):]
print("povContent: v-read refreshed for all 4 chairs")

# v-read IS included here. The 10-21 note warns that rewrite_pov_meta drives
# every chair from one dict and so flattens chair-SPECIFIC subtitles -- but
# v-read's meta is the "edition NNN . date" chip, which is identical for all
# four chairs by design (the per-chair prose lives in content[chair]['v-read']).
# Excluding it left "edition 099" in povContent.meta on all four chairs and in
# the static var NAV block, and assert_not_parent_identity caught all five.
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

# ---- identity: title/masthead/consts, then the runbar rebuilt wholesale
html = G.rewrite_identity(html, ED, TODAY, GEN)
rb = re.search(r'<div class="runbar">.*?</div>\s*(?=<div)', html, re.S)
if not rb: raise SystemExit("runbar not found")
flag = ("&#9873; LiteLLM 1.107.0 MALICIOUS release &mdash; rotate credentials &middot; eMudhra CA keys "
        "compromised, rebuild Go binaries &middot; Oracle APEX 9.8 fixed build still unnamed &middot; "
        "CVE-2026-21962 56d past KEV")
newrb = ('<div class="runbar">'
 '<span class="lbl">Edition</span><span class="val">' + ED + '</span>'
 '<span class="lbl">Generated</span><span class="val">' + GEN + '</span>'
 '<span class="lbl">Model</span><span class="val">claude-opus-5</span>'
 '<span class="lbl">Inputs</span><span class="val">19 briefs &middot; ' + str(len(ser)) + 'd ledger</span>'
 '<span class="lbl">Run tokens</span><span class="val">~3,740k</span>'
 '<span class="lbl">Skills review</span><span class="val">2027-01-01</span>'
 '<span class="flag">' + flag + '</span></div>')
html = html[:rb.start()] + newrb + html[rb.end():]
for stale in ('Edition 099', '2026-10-21 09:18 EDT', '~2,370k', '104d ledger'):
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
open('lens/out_100.html','w',encoding='utf-8').write(html)
par_sz = len(open('lens/index.html',encoding='utf-8').read())
print("\nwrote lens/out_100.html  %d bytes (parent %d, delta %+d)" % (len(html), par_sz, len(html)-par_sz))
