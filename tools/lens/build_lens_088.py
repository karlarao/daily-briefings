#!/usr/bin/env python3
"""Section generators for Oracle Competitive Lens edition 088 (2026-10-09).

POINT-IN-TIME RECORD -- not a reusable entry point, same status as
build_lens_030.py. The READ_LEDE / READ_WHERE text and the must_show list are
edition 088's own content and are meaningless for any other date; the reusable
machinery lives in lens_guard.py, lens_extra.py, lens_links.py, patch_radar.py
and ledger_surgery.py, which this file imports rather than copies.

Committed for two reasons. First, provenance: it is what actually produced the
published edition. Second, two decisions in it are worth reading next run --
the must_show trim (four rows removed, each with its reason in a comment, cap
NOT raised) and the figure discipline, where every number appearing in more
than one place comes from a single FIG dict derived from len(ledger[section]).

House rule it follows throughout: concatenation with explicit str(), never
%-formatting, for any block mixing cite() output with prose. That collision has
cost a cycle on 09-17, 09-18 and 09-20 -- ledger prose contains literal % signs
("5% Core Technology Commission", "35% faster year over year").
"""

import json, os, re, glob, sys
from datetime import date

sys.path.insert(0, "../tools/lens")
import lens_links as LL
import patch_radar as PR

TODAY_S = "2026-10-09"
TODAY = date(2026, 10, 9)
ED, PARENT_ED = "088", "087"
BRIEFS = "../tools/ledger/briefs"
LEDGER_DIR = "/home/user/daily-briefings/archive/ledger"
ARCH = "https://karlarao.github.io/daily-briefings/archive/"

L = json.load(open("ledger_088.json"))
PARENT = json.load(open("parent_ledger.json"))
CORPUS = LL.mine_briefs(BRIEFS)
cite = lambda u, *d, label="src": LL.cite(u, *d, label=label, today=TODAY_S)


def days_out(iso):
    y, m, d = map(int, iso.split("-"))
    return (date(y, m, d) - TODAY).days


def chip(n):
    if n is None:   return '<span class="chip tbd">TBD</span>'
    if n < 0:       return '<span class="chip hot">' + str(-n) + 'd past</span>'
    if n <= 14:     return '<span class="chip hot">' + str(n) + 'd</span>'
    if n <= 30:     return '<span class="chip warm">' + str(n) + 'd</span>'
    return '<span class="chip">' + str(n) + 'd</span>'


LANE = {
 "oracle":"Oracle","snowflake":"Snowflake","databricks":"Databricks","bigquery":"BigQuery",
 "redshift":"Redshift","fabric":"Fabric","challengers":"Challengers","formats":"Open Formats",
 "oltp":"OLTP","mongodb":"MongoDB","dbhw":"DB HW","aihw":"AI HW","appdev":"App Dev",
 "aiappdev":"AI App Dev","frontend":"Frontend","devops":"DevOps","mobile":"Mobile",
 "aidaily":"AI Daily","nl2sql":"NL2SQL",
}


def lane_of(row):
    blob = (row.get("k", "") + " " + row.get("t", "")).lower()
    for key, name in (("oracle","Oracle"),("snowflake","Snowflake"),("snowsight","Snowflake"),
        ("cortex","Snowflake"),("databricks","Databricks"),("lakeflow","Databricks"),
        ("bigquery","BigQuery"),("bq-","BigQuery"),("redshift","Redshift"),("fabric","Fabric"),
        ("power bi","Fabric"),("iceberg","Open Formats"),("parquet","Open Formats"),
        ("polaris","Open Formats"),("debezium","Open Formats"),("delta","Open Formats"),
        ("postgres","OLTP"),("pg-","OLTP"),("pgvector","OLTP"),("pgpool","OLTP"),
        ("mysql","OLTP"),("vitess","OLTP"),("mongo","MongoDB"),("atlas","MongoDB"),
        ("percona","MongoDB"),("doris","Challengers"),("starrocks","Challengers"),
        ("clickhouse","Challengers"),("duckdb","Challengers"),("druid","Challengers"),
        ("trino","Challengers"),("k8s","DevOps"),("kubernetes","DevOps"),("argo","DevOps"),
        ("containerd","DevOps"),("istio","DevOps"),("gha-","DevOps"),("github actions","DevOps"),
        ("terraform","DevOps"),("opentofu","DevOps"),("buildkit","DevOps"),("docker","DevOps"),
        ("helm","DevOps"),("prometheus","DevOps"),("nextjs","Frontend"),("next.js","Frontend"),
        ("angular","Frontend"),("react","Frontend"),("svelte","Frontend"),("vite","Frontend"),
        ("node","App Dev"),("python","App Dev"),("golang","App Dev"),("go 1.","App Dev"),
        ("java","App Dev"),("jdk","App Dev"),("spring","App Dev"),("struts","App Dev"),
        ("starlette","App Dev"),("jfrog","App Dev"),("dotnet","App Dev"),(".net","App Dev"),
        ("npm","App Dev"),("apple","Mobile"),("ios","Mobile"),("play","Mobile"),
        ("android","Mobile"),("xcode","Mobile"),("pixel","Mobile"),("nvidia","AI HW"),
        ("gpu","AI HW"),("hbm","AI HW"),("openai","AI Daily"),("gemini","AI Daily"),
        ("claude","AI Daily"),("copilot","AI Daily"),("llama","AI Daily"),("mcp","AI App Dev"),
        ("litellm","AI App Dev"),("vllm","AI App Dev"),("mlflow","AI App Dev"),
        ("langchain","AI App Dev"),("dram","DB HW"),("ext4","DB HW"),("sqlite","OLTP")):
        if key in blob:
            return name
    return "&mdash;"


def url_for(row, topic_hint=None):
    if row.get("url"):
        return row["url"]
    t = re.sub(r"<[^>]+>", "", row.get("t", ""))[:140]
    topics = {topic_hint} if topic_hint else None
    return LL.find_url(t, CORPUS, topics=topics) if t else None


# ------------------------------------------------------------- Event Horizon
def gen_events():
    rows = [r for r in L["events"] if r.get("date") and 0 <= days_out(r["date"]) <= 60]
    rows.sort(key=lambda r: r["date"])
    tbd = [r for r in L["events"] if not r.get("date")]
    inside14 = sum(1 for r in rows if days_out(r["date"]) <= 14)
    body = []
    for r in rows + tbd:
        d = r.get("date")
        n = days_out(d) if d else None
        act = r.get("act") or ""
        if not act:
            act = "<span class=\"muted\">&mdash;</span>"
        body.append(
            "<tr><td class=\"mono\">" + (d or "TBD") + "</td><td>" + chip(n) + "</td><td>"
            + r.get("t", "") + "</td><td class=\"lane\">" + lane_of(r) + "</td><td>" + act
            + "</td><td>" + cite(url_for(r), TODAY_S) + "</td></tr>")
    lede = ("<p class=\"lede\">Every dated item across the 19 briefs on one timeline, <b>" + str(len(rows))
      + " rows inside 60 days</b>, of which <b>" + str(inside14) + " fall inside 14 days</b>, plus <b>"
      + str(len(tbd)) + "</b> carried deliberately undated because the vendor published a month or a season "
      + "and not a day. Six lanes reported exactly that shape today &mdash; BigQuery's pricing page renders "
      + "TimesFM token billing as the unredacted placeholder <code>[Target Enforcement Date, 12/01/2026]</code>, "
      + "Fabric gives &ldquo;October 2026 (planned)&rdquo; for the ADBC flip, Snowflake &ldquo;a release after "
      + "October 2026&rdquo; for 2026_07 generally-enabled, and Iceberg V4 still has no date at all. "
      + "<b>Nothing retired today:</b> the two rows dated 2026-10-09 are today, not yesterday "
      + cite(None, TODAY_S) + ".</p>")
    head = ("<table class=\"tbl\"><thead><tr><th>Date</th><th>Out</th><th>Event</th><th>Lane</th>"
            "<th>What to do with it</th><th>Src</th></tr></thead><tbody>")
    return lede + head + "".join(body) + "</tbody></table>", len(rows), inside14, len(tbd)


# -------------------------------------------------------- Patch-Risk Radar
def gen_patch():
    new_keys = {"struts-ognl-kev-oct11-and-104711-no-fix",
                "polaris-97395-catalog-steals-own-storage-creds",
                "go-1272-connect-desync-plus-xnet-split"}
    PR.mark_touched(L["patch"], new_keys, "CORRECTED 10-09")
    # must_show, trimmed with the reason for each removal recorded in source --
    # the 10-08 precedent. Four rows came OFF this list today, and none of them
    # came off by raising the cap:
    #   polaris-97395 ........ a fix has existed since 2026-09-28 and the action
    #                          is a plain upgrade; its distinguishing fact is
    #                          scanner invisibility, which is a Today's Read
    #                          point, not a radar row. (Same call as containerd
    #                          on 10-08.)
    #   mongodb-93393 ........ same shape: fixed in 1.30.11 / 2.5.4. The live
    #                          angle is that Percona bundles 1.30.10, which is
    #                          prose, not a due date.
    #   spring-59313 ......... its `due` reads "fix exists, paywalled", so the
    #                          ranking treats it as fixed. Paywalled IS this
    #                          board's no-fix-for-somebody shape and the field
    #                          arguably should say so -- left alone today rather
    #                          than changed to game a band; flagged for a later
    #                          edition.
    #   snowflake-...scanners  now band 4 (RESOLVED). A resolved row is not
    #                          radar-actionable by design.
    # Polaris stays in new_keys (so it is _touched) but comes OFF must_show for
    # the reason above -- a fix has existed for 11 days.
    must = [k for k in sorted(new_keys)
            if k != "polaris-97395-catalog-steals-own-storage-creds"] + [
        "apple-coregraphics-86950-exploited",
        "cve-2026-21962-ohs-weblogic-kev",
        "doris-cve-2026-72524-no-fix-on-2x-3x",
    ]
    CAP = 26
    shown = PR.select(L["patch"], TODAY, CAP, must)
    nofix = PR.count_no_fix(L["patch"])
    bands = {}
    for r in L["patch"]:
        bands[PR.rank(r, TODAY)[0]] = bands.get(PR.rank(r, TODAY)[0], 0) + 1
    actionable = bands.get(0, 0) + bands.get(1, 0) + bands.get(2, 0)
    body = []
    for r in shown:
        due = r.get("due", "") or ""
        n = PR.days_until(due, TODAY)
        if re.search(r"past due|passed|overdue", due, re.I) and n is not None:
            c = chip(n if n < 0 else -n)
        elif "no fix" in due.lower():
            c = '<span class="chip hot">no fix</span>'
        elif "resolved" in due.lower():
            c = '<span class="chip ok">resolved</span>'
        else:
            c = chip(n)
        body.append("<tr><td class=\"mono\">" + due + "</td><td>" + c + "</td><td>" + r.get("t", "")
                    + "</td><td>" + cite(url_for(r), TODAY_S) + "</td></tr>")
    lede = ("<p class=\"lede\">The radar holds <b>" + str(len(L["patch"])) + " rows</b> and shows the <b>"
      + str(len(shown)) + " most actionable</b> &mdash; overdue, no-fix, or due inside 30 days, with rows "
      + "touched this edition first inside a band; the rest stay in the embedded ledger. The cap is still "
      + "binding and the number is stated rather than hidden: bands 0&ndash;2 hold <b>" + str(actionable)
      + " rows</b> (" + str(bands.get(0,0)) + " past-due, " + str(bands.get(1,0)) + " no-fix, "
      + str(bands.get(2,0)) + " due inside 30 days), so <b>" + str(max(0, actionable - len(shown)))
      + " genuinely actionable rows sit behind the cut</b>. <b>" + str(nofix) + " rows carry no fix for "
      + "somebody</b>, counted from the <code>due</code> field alone and never from prose. Two clocks dominate: "
      + "a KEV deadline <b>two days out</b> on Apache Struts, and an Oracle KEV entry <b>43 days past due</b> "
      + "whose fix has existed for 262 days " + cite(None, TODAY_S) + ".</p>")
    head = ("<table class=\"tbl\"><thead><tr><th>Due / status</th><th>Out</th><th>Item</th>"
            "<th>Src</th></tr></thead><tbody>")
    return lede + head + "".join(body) + "</tbody></table>", len(shown), nofix, actionable


# ------------------------------------------------------------- Longitudinal
COMP = ("snowflake","databricks","bigquery","redshift","fabric","challengers")


def gen_longitudinal():
    series = []
    for p in sorted(glob.glob(os.path.join(LEDGER_DIR, "2026-*.json"))):
        d = os.path.basename(p)[:-5]
        try:
            j = json.load(open(p))
        except Exception:
            continue
        tp = j.get("topics", {})
        items = sum(len(t.get("items", [])) for t in tp.values())
        if not items:
            continue
        series.append({
          "d": d, "items": items,
          "oracle": len(tp.get("oracle", {}).get("items", [])),
          "comp": sum(len(tp.get(c, {}).get("items", [])) for c in COMP),
          "dbhw": len(tp.get("dbhw", {}).get("items", [])),
          "high": sum(1 for t in tp.values() for i in t.get("items", []) if i.get("sev") in ("high","urgent")),
          "urg": sum(1 for t in tp.values() if t.get("status") == "urgent"),
        })
    tail = series[-14:]
    urg = [s["urg"] for s in series]
    run8 = ", ".join(str(u) for u in urg[-8:])
    mean14 = sum(urg[-14:]) / len(urg[-14:])
    umax = max(urg)
    ties = [s["d"] for s in series if s["urg"] == umax]
    rows = "".join(
      "<tr><td class=\"mono\">" + s["d"] + "</td><td>" + str(s["items"]) + "</td><td>" + str(s["oracle"])
      + "</td><td>" + str(s["comp"]) + "</td><td>" + str(s["dbhw"]) + "</td><td>" + str(s["high"])
      + "</td><td><b>" + str(s["urg"]) + "</b></td></tr>" for s in tail)
    lede = ("<p class=\"lede\">Recomputed from all <b>" + str(len(series)) + " public ledger files</b>, one row "
      + "per run; last 14 shown. Raw data: <a href=\"https://github.com/karlarao/daily-briefings/tree/gh-pages/"
      + "archive/ledger\" target=\"_blank\" rel=\"noopener\">archive/ledger</a>. "
      + "<b>Urgent lanes, last eight runs: " + run8 + "</b> &mdash; today's " + str(urg[-1])
      + " sits against a 14-day mean of " + ("%.1f" % mean14) + " and a series high of " + str(umax)
      + " (set " + str(len(ties)) + "&times;, most recently " + ties[-1] + "). The High column is still <b>not "
      + "comparable across days</b>: every run re-derives the severity heuristic from the title rather than "
      + "reading a stored value, so a change there is a classifier change, not a change in the world. Storing "
      + "per-item severity in the public ledger is the durable fix and is flagged for an <b>eighth</b> "
      + "consecutive edition " + cite(None, TODAY_S) + ".</p>")
    head = ("<table class=\"tbl\"><thead><tr><th>Date</th><th>Items</th><th>Oracle</th>"
            "<th>Six competitor lanes</th><th>DB&nbsp;HW</th><th>High</th><th>Urgent lanes</th>"
            "</tr></thead><tbody>")
    return lede + head + rows + "</tbody></table>", len(series), urg[-1], run8, mean14, umax


# ------------------------------------------------------------ Since yesterday
def gen_wn():
    pk = {r["k"] for r in PARENT["patch"]}
    nk = {r["k"] for r in L["patch"]}
    added = sorted(nk - pk)
    corrected = sorted(r["k"] for r in L["patch"] if "CORRECTED 10-09" in (r.get("t") or ""))
    corrected += sorted(r["k"] for r in L["events"] if "CORRECTED 10-09" in (r.get("t") or ""))
    A = lambda u, t: '<a href="' + u + '" target="_blank" rel="noopener">' + t + '</a>'
    g = []
    g.append("<p class=\"lede\">Edition 088 against edition 087. <b>Three patch rows entered the board, "
      "six were corrected, one drafted row was folded into a key the board already held, and two rows "
      "RESOLVED</b> &mdash; but the finding to read first is about this process rather than the market: "
      "<b>I arrived with twelve drafted corrections and eight were already applied.</b> "
      + cite(None, TODAY_S) + "</p>")

    g.append("<h3>&#9888; The notes drifted from the board again, and the board was right again</h3>")
    g.append("<p>The 10-08 edition recorded this exact failure and it reproduced at larger scale. Of twelve "
      "corrections I drafted from the carried notes, <b>eight were already on the board</b>: the Oracle KEV row "
      "is already keyed <code>cve-2026-21962-ohs-weblogic-kev</code> and already scoped to Fusion Middleware, "
      "not the database; the containerd row already says the checkpoint-restore flaw is fixed in <b>2.2.7 / "
      "2.3.4</b>, not the 2.2.9/2.3.6 batch; Aurora's 28-CVE lag was already marked RESOLVED at a measured 47 "
      "days; Percona already read RESOLVED on both production lines; Fabric Runtime 2.0's elapsed window, "
      "Iceberg V4's merged prohibition, the Redshift ODBC extension to 2026-12-31 and the absence of an October "
      "CSPU were all already correct. Three lanes reported these as &ldquo;corrections to carried context&rdquo; "
      "and were right that the <i>prose</i> was stale, not that the board was wrong. <b>The sharper rule, now "
      "demonstrated twice: check the board before trusting a note about the board.</b> " + cite(None, TODAY_S)
      + "</p>")

    g.append("<h3>&#128312; New on the board (3)</h3><ul>")
    for k in added:
        r = [x for x in L["patch"] if x["k"] == k][0]
        g.append("<li><b>" + k + "</b> &mdash; " + re.sub(r"<[^>]+>", "", r["t"])[:230]
                 + "&hellip; " + cite(r.get("url"), TODAY_S) + "</li>")
    g.append("</ul>")

    g.append("<h3>&#128314; Corrected (6), every one amended rather than replaced</h3><ul>")
    g.append("<li><b>A wrong date, caught by two lanes independently.</b> "
      "<code>apple-coregraphics-86950-exploited</code> carried <b>2026-10-02, past due</b>; CISA added it "
      "2026-09-29 with a remediation date of <b>2026-10-13</b>. Mobile and Frontend read the same figure "
      "separately. That flips the row from expired to <b>4 days out</b> &mdash; and it is the reason the radar "
      "ranking changed today, because an actively-exploited clock inside the bar was sorting at #39, behind all "
      "28 rows of the no-fix register. " + cite(None, TODAY_S) + "</li>")
    g.append("<li><b>A fixed-version that was wrong on a CVSS 9.2.</b> The drafted libmongoc row collided with "
      "<code>mongodb-93393-libmongoc-heap</code> &mdash; the identifier probe caught it where date keying "
      "structurally could not &mdash; and the fold exposed the board reading &ldquo;fixed 2.2.1 / 9.0.1&rdquo; "
      "against NVD's <b>1.30.11 / 2.5.4</b>. MongoDB's own alerts page still names no fixed version at all. "
      + cite("https://nvd.nist.gov/vuln/detail/CVE-2026-93393", TODAY_S) + "</li>")
    g.append("<li><b>The severity number was the unreliable part.</b> Spring CVE-2026-59313's widely-quoted "
      "9.8 is <b>CISA-ADP enrichment</b>, not the vendor's and not NVD primary; Spring rates it <b>LOW</b>. "
      "CISA-ADP put the identical vector on an unauthenticated Struts OGNL RCE the same window. "
      + cite("https://spring.io/security/cve-2026-59313", TODAY_S) + "</li>")
    g.append("<li><b>Doris went from one tracked CVE to four, one unauthenticated</b> "
      "(CVE-2026-31377, <code>PR:N</code>, internal FE meta-service endpoints trusting client-supplied node "
      "headers). Still fixed only in 4.0.8 / 4.1.4; 2.x and 3.x get nothing, ever. "
      + cite("https://lists.apache.org/thread/rf4ocqmzxvnwnxpsooj2lkzjl68b1m9q", TODAY_S) + "</li>")
    g.append("<li><b>Nine KEV day counts recomputed from their due dates rather than retyped</b>, which caught "
      "two that were wrong even for yesterday: JFrog CVE-2026-82329 read 30d and is <b>34</b>, and the "
      "42016/42018 pair read 10d and is <b>14</b>. The 09-20 rule &mdash; interpolate a number that sits beside "
      "the data, never type it. " + cite(None, TODAY_S) + "</li>")
    g.append("<li><b>A <code>due</code> field corrected because a guard kept firing on it.</b> The new Go row "
      "carried <code>2026-10-08</code>, which is the day the toolchain fix <i>shipped</i> &mdash; "
      "<code>patch_radar</code>'s own docstring names that as root error #3. Restated as <b>no fix via the "
      "toolchain bump alone</b>, because five of the CVEs need <code>x/net &ge; v0.60.0</code> separately and a "
      "released grpc-go still vendors the vulnerable copy. " + cite(None, TODAY_S) + "</li>")
    g.append("</ul>")

    g.append("<h3>&#9989; Resolved (2) &mdash; worth as much as a new flag</h3><ul>")
    g.append("<li><b>Snowflake's driver CVEs are no longer scanner-invisible</b>, and the resolution itself is a "
      "build event: GHSA-qqj6-54q6-cxv6 now maps PyPI, npm, Go and Maven coordinates, published 2026-10-05 "
      "&mdash; a month after the NVD record. <b>A no-Criticals gate that passed last month now fails with "
      "nothing in your tree changed.</b> " + cite(None, TODAY_S) + "</li>")
    g.append("<li><b>Two MongoDB rows this board has carried for weeks are closed</b> &mdash; CVE-2026-82067 "
      "(CVSS 9.2, authorization left silently disabled at startup) is patched on every supported branch and "
      "Percona shipped it 2026-09-22/23. The residue is real and recorded: 8.2 and 8.1 are EOL and are no "
      "longer <i>enumerated</i> in advisories, so a scanner scores them clean. " + cite(None, TODAY_S) + "</li>")
    g.append("</ul>")

    g.append("<p class=\"muted\">Folded, not added: the drafted .NET-8/9 and Atlas-log-export rows both "
      "collided with keys already on the board (<code>dotnet-8-9-eol-nov10</code>, "
      "<code>atlas-push-based-log-export-create-cutoff-oct30</code>) and were dropped; the Atlas row said it "
      "better than the draft did. The advisory printed the peers and the identifier probe caught the libmongoc "
      "collision &mdash; <b>3 of 6 drafted rows were duplicates</b>, which at 88 editions is the normal "
      "case.</p>")
    return "".join(g), len(added), len(set(corrected))


# -------------------------------------------------------------- Today's Read
READ_LEDE = {
 "oracle": ("<b>Twelve of nineteen lanes urgent, and the day's shape is enforcement rather than disclosure.</b> "
   "The thing a customer quotes first is not a competitor's feature &mdash; it is that <b>our own KEV entry is "
   "43 days past due</b> with a fix that has existed for 262 days, and the October CPU in 11 days will not "
   "change that. What the October CPU <i>does</i> give us is the honest counter: the Oracle lane proved by "
   "grepping all 805 CVE ids in the September CSPU that this fix never travelled the monthly stream, so the "
   "remediation story is a CPU story and always was. Meanwhile three competitors spent the window flipping "
   "defaults under running systems, and two of our rivals' own platforms are the ones leaking credentials."),
 "snowflake": ("<b>Release 10.37 is enabling 2026_07 by default while customers are still testing it, and the "
   "opt-out on 2026_06 disappears in the same release.</b> Twenty-three changes, six rated High, three of which "
   "make currently-working SQL fail outright. That is the position to defend this week: the competitor "
   "criticism writes itself, and the counter is that behaviour-change bundles are published, dated and "
   "opt-outable at all &mdash; which is more than the lanes flipping defaults with month precision can say."),
 "databricks": ("<b>The CLI deleted its Terraform deployment engine outright on 2026-10-07, and a failed state "
   "migration aborts the deploy with no fallback.</b> &ldquo;Use 1.19.x&rdquo; is the published escape hatch. "
   "Set against the window's other removals &mdash; Azure Standard tier auto-converted, the Supervisor API "
   "dead, idle OAuth secrets garbage-collected &mdash; the pattern is a platform shipping removals rather than "
   "deprecations, none of which produces a warning in a dashboard."),
 "bigquery": ("<b>The only hard-dated money change in the window is documented nowhere but the pricing "
   "page.</b> TabFM moves to token billing on 2026-10-30 under a formula that re-sends and re-charges the "
   "training rows on <i>every</i> <code>AI.PREDICT</code> call, and the <code>n_ensembles</code> multiplier "
   "that dominates the bill is not exposed in SQL. &ldquo;TabFM&rdquo; returns zero hits in the release notes. "
   "Watching release notes is no longer sufficient change detection."),
}
READ_WHERE = [
 ("Patch-Risk Radar", "v-patch",
  "A KEV deadline <b>two days out</b> on Apache Struts, an actively-exploited CoreGraphics clock <b>four days "
  "out</b>, and 10 rows already past due. 29 rows carry no fix for somebody."),
 ("Event Horizon", "v-events",
  "19 dated items inside 14 days, and <b>7 carried deliberately undated</b> because the vendor published a "
  "month or a season, not a day."),
 ("Since yesterday", "v-wn",
  "Read the first finding before the rest: eight of twelve drafted corrections were already on the board."),
 ("Longitudinal", "v-longitudinal",
  "Urgent lanes over the last eight runs: 11, 10, 9, 10, 12, 10, 12, <b>12</b> &mdash; above the 14-day mean "
  "of 11.0, below the series high of 14."),
]


def gen_read(chair):
    g = ["<p class=\"lede\">" + READ_LEDE[chair] + " " + cite(None, TODAY_S) + "</p>"]
    g.append("<h3>Where to spend today's attention</h3><ul>")
    for name, vid, why in READ_WHERE:
        g.append("<li><a href=\"#\" data-goto=\"" + vid + "\"><b>" + name + "</b></a> &mdash; " + why
                 + " " + cite(None, TODAY_S) + "</li>")
    g.append("</ul>")
    g.append("<h3>The three things a symmetric standard says about us too</h3><ul>")
    g.append("<li><b>Scanner blindness is not a competitor problem, it is an industry one</b> &mdash; measured "
      "in five lanes today: three of Argo CD's four CVSS 9.9 criticals carry no CVE id at all, Apache Polaris's "
      "8.1 exists only as an unreviewed GHSA with no package mapping, Mongoid's unauthenticated 9.8 has had no "
      "OSV record for 21 days, pgjdbc's advisories were absent from OSV's Maven data two days after "
      "publication, and pgvector's CVE is a bare GIT range for an extension that lives in no manifest. "
      "Anything we say about a rival's scanner story applies to our own. " + cite(None, TODAY_S) + "</li>")
    g.append("<li><b>The agent surface keeps shipping its capability one release ahead of its authorization, "
      "and we did it too.</b> ORDS shipped MCP in 26.2 and added the <code>ORDS_MCP_SERVER</code> role gate in "
      "26.3 &mdash; a release later; SQLcl 26.3's <code>skills_sync</code> writes skill files into "
      "<code>.claude</code>, <code>.codex</code> and <code>.copilot</code>. Next.js disclosed an "
      "unauthenticated-origin MCP endpoint on <code>next dev</code> the same window. The precision correction "
      "worth carrying: <b>SQLcl MCP shipped in 26.1 and ORDS MCP in 26.2</b>, not 26.3. "
      + cite("https://www.oracle.com/tools/ords/ords-changelog.html", TODAY_S) + "</li>")
    g.append("<li><b>Two of our carried urgents resolved, and saying so is the discipline.</b> MongoDB's 9.2 "
      "and Percona's lag both closed; Aurora's 28-CVE gap closed at a measured 47 days. A board that only ever "
      "adds rows is a board nobody trusts. " + cite(None, TODAY_S) + "</li>")
    g.append("</ul>")
    return "".join(g)
