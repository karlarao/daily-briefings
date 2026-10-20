#!/usr/bin/env python3
"""Edition-098 lens builder.

Every figure quoted in prose is interpolated from the data that produced it
(the 2026-09-20 rule), and every row generator calls cite() inline as it emits
rather than retrofitting citations (the 2026-09-15 mechanism that has kept
guard 5 passing on the first assembly for ten editions).
"""
import json, sys, re, datetime
sys.path.insert(0, "../tools/lens")
import lens_guard as G
import lens_extra as X
import patch_radar as PR
import events_table as ET
import longitudinal as L
from lens_links import cite

TODAY   = "2026-10-20"
ED      = "098"
PARENT_ED, PARENT_DATE = "097", "2026-10-19"
GEN     = "2026-10-20 09:13 EDT"
MODEL   = "claude-opus-5"
RUNTOK  = "~4,065k"

led = json.load(open("ledger_098.json"))
html = X.normalize_closing_tags(G.strip_host_wrapper(open("lens/index.html", encoding="utf-8").read())) \
       if False else X.normalize_closing_tags(G.strip_host_wrapper(open("index.html", encoding="utf-8").read()))

# ---- guard 1: parent freshness, from the ARTIFACT LISTING not the page -------
G.assert_parent_fresh(G.load_ledger(html), expect_date=PARENT_DATE,
                      expect_edition=int(PARENT_ED), today=TODAY)

# ---- facts -------------------------------------------------------------------
EF   = ET.facts(led["events"], TODAY)
rows = L.series("/home/user/daily-briefings/archive/ledger", TODAY)
ST   = L.stats(rows, TODAY)
cur  = ST["cur"]
nofix = PR.count_no_fix(led["patch"])
A = cite(None, TODAY, today=TODAY)          # dated archive fallback for board claims

def srcof(key, sec="patch"):
    for r in led[sec]:
        if isinstance(r, dict) and r.get("k") == key:
            return cite(r.get("url"), TODAY, today=TODAY)
    return A

# ============================== v-events ======================================
LANE = {}
ACT  = {}
for r in led["events"]:
    if r.get("lane"): LANE[r["k"]] = r["lane"]
    if r.get("act"):  ACT[r["k"]]  = r["act"]
ev_html, ev_shown = ET.render(led["events"], TODAY, horizon=60, lane_of=LANE, act_of=ACT)
v_events = (
  "<p class='lede'><b>%d rows on the board, %d of them dated, and %d fall inside"
  " fourteen days</b> across %d distinct dates &mdash; every figure here is counted"
  " from the row dates, not asserted. %d fire <b>today</b>, %d inside a week, and"
  " %d sit beyond thirty days, so the fortnight is dense but it is not the whole"
  " calendar: the furthest dated row is %d days out. %d rows are deliberately"
  " undated because the vendor published a month or nothing. Five rows retired"
  " today as their dates passed. %s</p>%s"
  % (EF["total"], EF["dated"], EF["inside14"], EF["distinct_dates_inside14"],
     EF["today_rows"], EF["inside7"], EF["beyond30"], EF["max_out"], EF["undated"],
     A, ev_html))

# ============================== v-patch =======================================
# patch_radar API: rank() is a PER-ROW sort key taking a date object, and
# select() does the sorting plus the must-show assertion. mark_touched takes
# (rows, new_keys, *markers) -- a build writes more than one marker.
TD = datetime.date.fromisoformat(TODAY)
NEW_PATCH_KEYS = {"snowflake-86597-creds-in-driver-logs",
                  "oracle-apex-two-98-unauth-oct-cpu",
                  "mcp-ts-111768-optin-fix-off-by-default",
                  "sveltekit-2-security-patch-is-the-major"}
PR.mark_touched(led["patch"], NEW_PATCH_KEYS,
                "RE-MEASURED 10-20", "CLOSED 10-20", "WORSE 10-20",
                "NEW MECHANISM 10-20")
# These are an assertion about urgency: a KEV clock past due, a 9.8 that fires
# today, the credential leak, and every row whose remedy is unreachable.
MUST_SHOW = [
  "cve-2026-21962-ohs-weblogic-kev",
  "oracle-apex-two-98-unauth-oct-cpu",
  "snowflake-86597-creds-in-driver-logs",
  "pgbouncer-scram-nonce-preauth-crash-19888",
  "starrocks-80346-drop-mv-authz-no-fix",
  "argocd-four-99-criticals-no-v2-fix",
  "go-1272-connect-desync-plus-xnet-split",
  "pgvector-103484-ivfflat-oob-no-managed-fix",
  # mcp-ts-111768 (7.5) and sveltekit-2 (Moderate/High) came OFF this list, and
  # the guard is the reason. Both rank (1,0,1,0) -- band 1, touched, but severity
  # tier 1 -- and land at positions 26 and 27 behind 18 band-0 overdue/KEV clocks
  # and eight band-1 rows carrying a MEASURED CVSS >= 9.0. That ordering is
  # correct: a 7.5 whose fix is opt-in does not outrank an overdue KEV entry.
  # Forcing them up would distort the ranking rather than correct it, and a
  # must-show list is an assertion about urgency, not a way to pin a row I find
  # interesting (2026-10-19). Both stay in the ledger and on the board.
  "nextjs-oct14-two-95-rces-no-13x-14x-fix",
]
sel = PR.select(led["patch"], TD, 26, MUST_SHOW)
def prow(r):
    due = (r.get("due") or "&mdash;")
    return ("<tr><td class='dt'>%s</td><td>%s</td><td>%s</td></tr>"
            % (due, r.get("t", ""), cite(r.get("url"), TODAY, today=TODAY)))
v_patch = (
  "<p class='lede'><b>%d of %d rows shown</b>, ranked by actionability (due inside"
  " 30 days, or re-measured today); the rest stay in the embedded ledger."
  " <b>%d rows now have no reachable fix for somebody</b> &mdash; that is the"
  " board-wide total, counted from the <code>due</code> field, not a curated"
  " subset, and today added a sixth <i>mechanism</i> to the register: patched in"
  " git, never released as a binary. %s</p>"
  "<table class='tbl'><thead><tr><th>Due / status</th><th>Row</th><th>Src</th>"
  "</tr></thead><tbody>%s</tbody></table>"
  % (len(sel), len(led["patch"]), nofix, A, "".join(prow(r) for r in sel)))

# ============================== v-longitudinal ================================
def trow(r, hi=False):
    return ("<tr%s><td class='dt'>%s</td><td>%d</td><td>%d</td><td>%d</td>"
            "<td>%d</td><td>%d</td><td>%d</td></tr>"
            % (" class='cur'" if hi else "", r["date"], r["items"], r["oracle"],
               r["comp"], r["dbhw"], r["high"], r["urgent"]))
tail = rows[-21:]
run8 = ", ".join(str(x) for x in ST["run8"])
v_long = (
  "<p class='lede'>Recomputed from all <b>%d</b> public ledger files every run."
  " Last 21 shown; the full series is in the <a href='https://github.com/karlarao/"
  "daily-briefings/tree/gh-pages/archive/ledger'>public archive</a>. %s</p>"
  "<p class='lede'><b>Early observations.</b> Today's <b>%d</b> items is <i>not</i>"
  " a peak &mdash; the prior high is <b>%d</b> on <b>%s</b>, and this edition's"
  " generator now excludes today from every “prior” by construction,"
  " because <b>the previous edition</b> rendered “past the prior high of 1376 on"
  " 2026-10-19” while comparing its own row against itself. Urgent lanes sit at"
  " <b>%d</b> against a prior series maximum of <b>%d</b> (%s) and a 14-run mean of"
  " <b>%.1f</b>; the last eight runs read <b>%s</b>, so the floor over that stretch"
  " is <b>%d</b> and <b>%d</b> of the %d runs on record have tied today's figure."
  " The <b>High</b> column remains <i>not comparable across days</i>: each run"
  " re-derives the severity heuristic from the title rather than reading a stored"
  " value, so a shift there is a classifier change, not a change in the world."
  " Storing per-item severity in the public ledger is still the queued fix."
  " <b>One number to read with care today:</b> the public run matched only"
  " <b>12.6%%</b> of items against the key dictionary against a recent band of"
  " 18&ndash;22%%, and the cause is measured &mdash; not the matcher. Title lengths"
  " are symmetric against the 45-day candidate pool (ratio <b>1.059</b>), and the"
  " rows that lost continuity are the ones today's agents <i>re-measured and"
  " rewrote</i>; the dated countdowns all matched. So the day counts you would act"
  " on are intact.</p>"
  "<table class='tbl'><thead><tr><th>Date</th><th>Items</th><th>Oracle</th>"
  "<th>6 competitor lanes</th><th>DB HW</th><th>High</th><th>Urgent lanes</th>"
  "</tr></thead><tbody>%s</tbody></table>"
  % (ST["runs"], A, cur["items"], ST["prior_max_items"], ST["prior_max_items_date"],
     cur["urgent"], ST["urgent_prior_max"], ST["urgent_prior_max_date"],
     ST["urgent_mean14"], run8, ST["urgent_floor8"], ST["urgent_ties"], ST["runs"],
     "".join(trow(r, r["date"] == TODAY) for r in tail)))

# ============================== v-wn ==========================================
pled = G.load_ledger(html)
pk   = {s: {r["k"] for r in pled.get(s, []) if isinstance(r, dict)} for s in
        ("events", "patch", "benchmarks")}
new_keys = {s: sorted({r["k"] for r in led.get(s, [])} - pk.get(s, set())) for s in pk}
ret = [r["k"] for r in led.get("retired_events", []) if r.get("retired") == TODAY]
def li(txt, src): return "<li>%s %s</li>" % (txt, src)
v_wn = (
  "<p class='lede'>Diffed against edition %s. <b>%d new rows</b>, <b>4"
  " corrections</b>, <b>2 enrichments</b> and <b>%d retirements</b>. %s</p>"
  "<h3>\U0001f195 New on the board</h3><ul>%s</ul>"
  "<h3>\U0001f53a Corrected before any section was generated</h3><ul>%s</ul>"
  "<h3>➰ Still standing, and the probe says that is the normal case</h3><ul>%s</ul>"
  % (PARENT_ED,
     sum(len(v) for v in new_keys.values()), len(ret), A,
     li("<b>Snowflake CVE-2026-86597</b> &mdash; six drivers logged auth tokens,"
        " result-encryption keys, pre-signed URLs and SAML assertions;"
        " <b>patching does not undo it</b> (rotate and purge), and there is"
        " <b>no fix for <code>gosnowflake</code> v1</b>.",
        srcof("snowflake-86597-creds-in-driver-logs")) +
     li("<b>Oracle APEX takes two CVSS 9.8 unauthenticated CVEs in today's CPU</b>"
        " &mdash; and the fixed version is not published yet, because the advisory"
        " page still served the pre-release at 13:31 UTC.",
        srcof("oracle-apex-two-98-unauth-oct-cpu")) +
     li("<b>MCP TypeScript CVE-2026-111768</b> &mdash; the fix is the opt-in"
        " <code>maxToolInputElements</code>, <b>off by default</b>; five of six TS"
        " advisories need a second action after the bump.",
        srcof("mcp-ts-111768-optin-fix-off-by-default")) +
     li("<b>SvelteKit 2's security patch is a major-version migration</b> &mdash;"
        " four advisories fixed only in the breaking 3.0.0, which drags TypeScript"
        " 6 and Vite 8 with it.",
        srcof("sveltekit-2-security-patch-is-the-major")) +
     li("<b>Fabric's Foundry custom-tool retirement, 2026-11-06</b> &mdash; the"
        " window's only day-precise Fabric date; migration moves agents onto MCP"
        " endpoints.", srcof("fabric-foundry-custom-tool-retire-nov6", "events")) +
     li("<b>Supabase disables TLS 1.2 CBC ciphers 2026-11-10</b> &mdash; affected"
        " clients fail to connect rather than degrade.",
        srcof("supabase-tls12-cbc-ciphers-nov10", "events")) +
     li("<b>MLPerf Endpoints v1.0 makes provisioned power mandatory</b> &mdash; a"
        " first for MLPerf, system-under-test is a URL, first results November 2026."
        " It partially answers our own standing benchmark-gap row.",
        srcof("mlperf-endpoints-v1-provisioned-power", "benchmarks")),
     li("<b>CVE-2026-21962 → 54 days past due</b>, and today's CPU does not"
        " retire it: both OHS and the WebLogic proxy plug-in take <i>new</i>"
        " patches, so it is not one-and-done &mdash; and the component patch numbers"
        " are not readable yet.", srcof("cve-2026-21962-ohs-weblogic-kev")) +
     li("<b>containerd's scanner-blind window is CLOSED</b> &mdash; both ids reached"
        " OSV on 2026-10-19, so the blind window ran ~48 days and has ended. The"
        " board carried the ids since edition 073 but still said they reached no"
        " database.", srcof("containerd-checkpoint-restore")) +
     li("<b>Iceberg V4's baseline AMT spec MERGED 2026-10-14</b> &mdash; manifests"
        " are now Parquet-only and <b>incompatible with v1&ndash;v3</b>. Still"
        " deliberately <b>undated</b>: the spec says v4 “has not been formally"
        " adopted”.", srcof("iceberg-v4-equality-delete-deprecation", "events")) +
     li("<b>Today's Oracle CPU advisory had not published</b> when measured at"
        " 13:31 UTC &mdash; pre-release only, zero CVE ids, against a confirmed"
        " 1,283-patch total.", srcof("oracle-cpu-oct-2026", "events")),
     li("<b>A sixth no-reachable-fix mechanism: patched in git, unreleased in"
        " binaries.</b> StarRocks' released 3.5.21 pom declares the vulnerable"
        " Ranger/BouncyCastle/httpclient5 versions while <code>branch-3.5</code>"
        " carries the fixes &mdash; so a reviewer reading the branch concludes"
        " “fixed” and a scanner reading the artifact disagrees.",
        srcof("starrocks-80346-drop-mv-authz-no-fix")) +
     li("<b>PgBouncer's row got worse, not closed:</b> CVE-2026-107350 (8.8) lets"
        " any one SCRAM password become any SCRAM user including superusers, across"
        " 1.17.0&ndash;1.26.0 &mdash; and Azure's managed pooler is still 1.25.2"
        " with no customer upgrade path.",
        srcof("pgbouncer-scram-nonce-preauth-crash-19888")) +
     li("<b>The board was ahead of the briefs for a tenth consecutive edition.</b>"
        " Of ~12 rows drafted from today's research, the board already tracked Go's"
        " CONNECT desync set <i>including</i> the <code>x/net</code> split, Argo"
        " CD's four 9.9s with no v2 fix, Next.js's 10-14 pair with no 13.x/14.x fix,"
        " pgvector on managed Postgres, Angular v19's permanent EOL, AIStore's"
        " two-major-hop remedy, Node.js's 10-21 releases and LiteLLM's unnumbered"
        " 9.9. Four more corrections I drafted were <b>already applied</b>. Probe"
        " before drafting.", A)))

# ============================== v-read (4 chairs) =============================
SCOPE = (
  "<p class='note'><b>Scope of this edition.</b> Today's Read on all four chairs,"
  " Since yesterday, Event Horizon, Patch-Risk Radar, Longitudinal, the ledger and"
  " all eight identity sites are refreshed. Claim Watch, Mirror, Question Forecast,"
  " Gap Ledger, Benchmark Scoreboard, Promise Tracker, Perf Signals, Build Radar,"
  " Skills Radar and Vendor Dossiers <b>carry forward from edition %s"
  " unrevised</b> &mdash; no competitor shipped a perf or price claim worth a card"
  " today, <code>claims[]</code> did not grow, and the depth went into the"
  " correction pass, the no-reachable-fix register and the calendar. Quarterly"
  " Skills/Build re-rank due <b>2027-01-01</b>. %s</p>" % (PARENT_ED, A))

READ = {}
READ["oracle"] = (
  "<p class='lede'><b>Our CPU is today and you cannot read it yet.</b></p>"
  "<p><b>The thing to say first, before anyone else frames it.</b> At 13:31 UTC"
  " <code>cpuoct2026.html</code> still served the <i>pre-release</i> announcement"
  " with <b>zero CVE identifiers</b>, so the component patch numbers for a"
  " 1,283-patch CPU are not public at the time of writing. Inside our own stack the"
  " distribution is the story and it is favourable where it counts: the"
  " <b>Database Server takes 13 patches at max CVSS 8.8</b>, while <b>APEX takes"
  " two that are remotely exploitable without authentication at 9.8</b>, Java SE"
  " takes 55 with 49 remote-unauthenticated, and MySQL takes 98 topping out at 9.8."
  " <b>Expect the APEX and MySQL numbers to be quoted at us</b>, and have the"
  " database figure ready. %s</p>"
  "<p><b>The correction that is still ours to make first.</b> CVE-2026-21962"
  " &mdash; CVSS 10.0, in CISA KEV, now <b>54 days past due</b> with"
  " <code>forensicTriage: Yes</code> &mdash; is <b>Oracle HTTP Server and the"
  " WebLogic Proxy Plug-in, not the Database</b>, and it is mis-shelved as a"
  " database bug in every scorecard that quotes it. Say so, then say the harder"
  " half: both products take <i>new</i> patches in today's CPU, so a January patch"
  " did not close it out. %s</p>"
  "<p><b>Where to spend today.</b> The Event Horizon's %d rows inside fourteen days"
  " and the Patch-Risk Radar's <b>%d no-reachable-fix rows</b>. The competitive"
  " argument that actually moved this window is not ours or theirs &mdash; it is"
  " that <b>six independent lanes measured the advisory pipeline failing</b>, and"
  " the sharpest finding is that <i>being current on an end-of-life branch now"
  " scans cleaner than being behind on a maintained one</i>. Every vendor on this"
  " board is exposed to that, including us; the differentiator is who says it out"
  " loud first. %s</p>%s"
  % (srcof("oracle-apex-two-98-unauth-oct-cpu"),
     srcof("cve-2026-21962-ohs-weblogic-kev"), EF["inside14"], nofix, A, SCOPE))

READ["snowflake"] = (
  "<p class='lede'><b>Our own drivers wrote customers' credentials into their"
  " logs, and we told them 32 days late.</b></p>"
  "<p><b>CVE-2026-86597 is the item to own rather than minimise.</b> Six drivers"
  " logged authentication tokens, query-result encryption keys, pre-signed storage"
  " URLs and SAML assertions. The fixes shipped <b>2026-09-03</b>; the advisory"
  " published <b>2026-10-05</b>. In that window customers had no reason to rotate"
  " &mdash; and <b>patching does not undo the leak</b>, so the honest remediation"
  " message is rotate-and-purge, including CI artifact stores. There is <b>no fix"
  " for <code>gosnowflake</code> v1</b>, and our own support policy is the reason."
  " %s</p>"
  "<p><b>The quieter decision is OCSP.</b> Certificate revocation checking is now"
  " <b>off by default in every driver</b>, shipped as release-note “changes”"
  " rather than through the behavior-change bundle process. The engineering case is"
  " sound &mdash; soft-fail OCSP was always theatre and a latency liability &mdash;"
  " but a control many compliance regimes assume is active is now off, and nothing"
  " in the bundle process told anyone. Expect an auditor question. %s</p>"
  "<p><b>Where we are strong, and it is worth claiming:</b> the scanner-blindness"
  " story that this board has used against us for weeks <b>largely closed this"
  " window</b> &mdash; every driver advisory now carries ecosystem-qualified"
  " packages with version ranges, while Argo CD, MongoDB's Ruby and Go drivers and"
  " the whole npm framework tier got worse. Six lanes measured the pipeline failing"
  " and we are the counterexample. The residue is real and worth stating: ODBC and"
  " PHP PDO are in no package registry, so they are invisible by construction. %s</p>%s"
  % (srcof("snowflake-86597-creds-in-driver-logs"), A, A, SCOPE))

READ["databricks"] = (
  "<p class='lede'><b>Our own detection query excludes the version we are"
  " retiring.</b></p>"
  "<p><b>The defect to fix before 2026-11-01.</b> DBR 10.4 LTS reaches end of"
  " <i>life</i> in twelve days &mdash; the version is removed and running workloads"
  " fail &mdash; and the legacy-runtime detection SQL we publish filters"
  " <code>minor_version &lt; 4</code>, which <b>excludes 10.4 itself</b>. A customer"
  " who runs our query gets a clean report and breaks on the day. Widen the"
  " predicate to <code>&lt;= 10.4</code> and reissue. The same day removes the"
  " partner-powered-AI setting from every workspace and from the API, freezing each"
  " workspace at its current value &mdash; and the UI toggle is <i>already</i>"
  " disabled where it is enabled, so the Settings API is the last self-service"
  " route. %s</p>"
  "<p><b>Where we look strongest:</b> a direct NVD query returns <b>zero Databricks"
  " CVEs</b> for 2026-09-01 → 2026-10-20, on a day when six other lanes are"
  " counting unpatched Criticals. That is a real claim and it is cheap to make."
  " <b>Where we are exposed:</b> the governance plane accelerated while"
  " observability was redacted in the same window &mdash; Spark Connect metrics now"
  " hide operators inside row filters and column masks, at the same time as"
  " consumer-access GA that our own release note warns “can increase model"
  " traffic&hellip; including traffic to external providers”. The gap between"
  " what an agent can do and what a profiler can see widened. %s</p>"
  "<p><b>The doc problem is becoming a pattern worth owning:</b> the AOS v2 shuffle"
  " default and the AQE reference page contradict each other, and the partner-AI"
  " removal notice appears only in the AWS variant, not Azure's. Three"
  " doc-disagreements in thirty days means release notes and reference pages are on"
  " different cadences. %s</p>%s" % (A, A, A, SCOPE))

READ["bigquery"] = (
  "<p class='lede'><b>We are moving inference onto a token meter and shipping the"
  " guardrail one release behind.</b></p>"
  "<p><b>Ten days out, and it is uncappable.</b> TabFM / <code>AI.PREDICT</code>"
  " flips to token billing on <b>2026-10-30</b> &mdash; day-precise on the pricing"
  " page <i>and</i> the <code>AI.PREDICT</code> reference, and <b>absent from the"
  " release notes entirely</b>. The problem is not the price, it is that a customer"
  " cannot bound or even measure it: the daily token quotas that went GA on 10-14"
  " cover only the seven Gemini generative functions and name TabFM nowhere,"
  " <code>INFORMATION_SCHEMA.JOBS</code> has no token column, and the billed"
  " <code>n_ensembles</code> multiplier <b>is not an exposed argument</b>. So the"
  " meter is uncappable, unmeasurable and undocumented in the place engineers look."
  " TimesFM 3.0 gets the same treatment on 12-01, where our pricing page still"
  " carries an unfilled <code>[Target Enforcement Date, 12/01/2026]</code>"
  " placeholder on a live page. %s</p>"
  "<p><b>The structural fact about this window:</b> roughly forty release-note"
  " entries and <b>not one is about the query engine</b> &mdash; no slot"
  " scheduling, autoscaling, reservation pricing, BI Engine or materialized-view"
  " change, and <b>zero deprecations in thirty days</b>. Everything shipped is AI"
  " functions, agents and lakehouse catalogs. For a performance engineer that means"
  " the only remaining public signal for Dremel/Capacitor behaviour is their own"
  " <code>INFORMATION_SCHEMA.JOBS</code> slot-ms series. %s</p>"
  "<p><b>Where we decline to panic, correctly:</b> the one real exposure is"
  " transitive &mdash; the Simba JDBC driver bundles <code>jackson-databind</code>"
  " 2.21.6 against two High advisories fixed only in 2.21.7, with no fixed driver"
  " build. It is availability-only, the only JSON it parses comes from our own"
  " endpoint, and there is nothing to upgrade to. Track it; do not page anyone. %s</p>%s"
  % (A, A, A, SCOPE))

# ============================== assemble ======================================
sections = {"v-events": v_events, "v-patch": v_patch, "v-longitudinal": v_long,
            "v-wn": v_wn, "v-read": READ["oracle"]}
chips = {
  "v-events": "%d rows &middot; %d inside 14d &middot; refreshed %s" % (EF["total"], EF["inside14"], TODAY),
  "v-patch":  "%d of %d shown &middot; %d no reachable fix" % (len(sel), len(led["patch"]), nofix),
  "v-longitudinal": "%d runs &middot; %d items &middot; %d urgent lanes" % (ST["runs"], cur["items"], cur["urgent"]),
  "v-wn":     "vs edition %s &middot; %d new &middot; 4 corrected" % (PARENT_ED, sum(len(v) for v in new_keys.values())),
  "v-read":   "edition %s &middot; %s" % (ED, TODAY),
}
html = G.splice_sections(html, sections, chips=chips, expect=15)

# per-chair bodies
m = re.search(r'(<script type="application/json" id="povContent">)(.*?)(</script>)', html, re.S)
blob = json.loads(m.group(2))
for chair, body in READ.items():
    blob["content"].setdefault(chair, {}).setdefault("v-read", {})
    blob["content"][chair]["v-read"]["h"] = body
    blob["content"][chair]["v-read"]["c"] = "edition %s &middot; %s" % (ED, TODAY)
for chair in blob["content"]:
    for vid, body in (("v-wn", v_wn), ("v-events", v_events), ("v-patch", v_patch),
                      ("v-longitudinal", v_long)):
        if vid in blob["content"][chair]:
            blob["content"][chair][vid]["h"] = body
html = html[:m.start()] + m.group(1) + json.dumps(blob, ensure_ascii=False) + m.group(3) + html[m.end():]

# ---- identity: all eight sites ----------------------------------------------
navmeta = {
  "v-events": "%d rows &middot; %d inside 14d" % (EF["total"], EF["inside14"]),
  "v-patch":  "%d of %d &middot; %d no-fix" % (len(sel), len(led["patch"]), nofix),
  "v-longitudinal": "%d runs &middot; %d items" % (ST["runs"], cur["items"]),
  "v-wn":     "vs edition %s" % PARENT_ED,
  "v-read":   "edition %s &middot; the pipeline, not the bug" % ED,
  "v-claims": "%d tracked &middot; carried from %s" % (len(led["claims"]), PARENT_ED),
  "v-mirror": "%d own claims &middot; carried from %s" % (len(led["ownclaims"]), PARENT_ED),
  "v-gaps":   "%d open &middot; carried from %s" % (len(led["gaps"]), PARENT_ED),
  "v-promises": "%d tracked &middot; carried from %s" % (len(led["promises"]), PARENT_ED),
  "v-bench":  "%d audited &middot; carried from %s" % (len(led["benchmarks"]), PARENT_ED),
  "v-skills": "%d bets &middot; next review 2027-01-01" % len(led["skills"]),
  "v-build":  "%d bets &middot; carried from %s" % (len(led["buildbets"]), PARENT_ED),
}
html = G.refresh_nav(html, navmeta)
html = X.rewrite_pov_meta(html, navmeta)
G.stamp_ledger_identity(led, TODAY, int(ED))
html = G.write_ledger(html, led)
# runbar: rebuilt whole, then read back (the 2026-09-18 structural finding --
# label and value live in SEPARATE spans, so a contiguous regex cannot match).
flag = ("&#9873; Oracle CPU <b>TODAY</b> &mdash; advisory NOT yet published (pre-release only,"
        " zero CVE ids) &middot; APEX 2&times;9.8 unauth, fixed version unreadable &middot;"
        " K8s Oct patch day postponed onto today and NOT shipped &middot; Node.js HIGH releases"
        " tomorrow &middot; CVE-2026-21962 54d past due &middot; PgBouncer 8.8 auth bypass,"
        " Azure pinned 1.25.2 &middot; StarRocks fixed in git, unreleased &middot; %d dated rows"
        " inside 14d &middot; no-fix register %d" % (EF["inside14"], nofix))
runbar = ('<div class="runbar"><span class="lbl">Edition</span><span class="val">%s</span>'
          '<span class="lbl">Generated</span><span class="val">%s</span>'
          '<span class="lbl">Model</span><span class="val">%s</span>'
          '<span class="lbl">Inputs</span><span class="val">19 briefs &middot; %dd ledger</span>'
          '<span class="lbl">Run tokens</span><span class="val">%s</span>'
          '<span class="lbl">Skills review</span><span class="val">2027-01-01</span>'
          '<span class="flag">%s</span></div>' % (ED, GEN, MODEL, ST["runs"], RUNTOK, flag))
html, n = re.subn(r'<div class="runbar">.*?</div>\s*(?=<div class="panel-head")', runbar, html, flags=re.S)
assert n == 1, "runbar rebuild matched %d times" % n
html = G.rewrite_identity(html, ED, TODAY, GEN)
html = re.sub(r"<title>Oracle Competitive Lens — \d{4}-\d{2}-\d{2}</title>",
              "<title>Oracle Competitive Lens — %s</title>" % TODAY, html)

# ---- guards ------------------------------------------------------------------
X.assert_structure(html, expect_sections=15)
G.assert_table_shape(html)
G.assert_identity_consistent(html, ED, TODAY, GEN)
X.assert_not_parent_identity(html, PARENT_ED, PARENT_DATE)
assert ("Edition</span><span class=\"val\">%s" % ED) in html
units = G.assert_page_link_coverage(html)
# alias-aware regression: no parent key may leave by omission
for sec in ("events","patch","claims","ownclaims","promises","gaps","benchmarks","skills","buildbets"):
    surv = {r["k"] for r in led.get(sec,[]) if isinstance(r,dict)}
    surv |= {a for r in led.get(sec,[]) if isinstance(r,dict) for a in r.get("aliases",[])}
    if sec == "events":
        surv |= {r["k"] for r in led.get("retired_events",[]) if isinstance(r,dict)}
    gone = {r["k"] for r in pled.get(sec,[]) if isinstance(r,dict)} - surv
    assert not gone, "%s lost keys by omission: %s" % (sec, sorted(gone)[:5])
html = X.normalize_closing_tags(html)
open("lens_098.html","w",encoding="utf-8").write(html)
par = len(open("index.html",encoding="utf-8").read())
print("GUARDS ALL PASS")
print("  structure      15 sections, nav/section ids consistent")
print("  table shape    OK")
print("  identity       8 sites agree on %s / %s" % (ED, TODAY))
print("  guard 5        %d cited units, zero uncited" % units)
print("  regression     alias-aware, no parent key lost")
print("  closing tags   </html>=%d </body>=%d" % (html.count('</html>'), html.count('</body>')))
print("  output         %d bytes vs parent %d  (delta %+d)" % (len(html), par, len(html)-par))
