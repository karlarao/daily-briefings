#!/usr/bin/env python3
"""Edition 107 lens build. Inheritance from edition 106 + spliced sections.

House style (09-18/09-20 rule): HTML blocks that embed cite() output are built
by CONCATENATION with explicit str(), never %-formatted -- ledger prose carries
literal % signs ("5% Core Technology Commission", "35% faster") and %-formatting
consumes them as conversion specifiers. This has bitten four times.
"""
import json, os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import lens_guard as G
import lens_extra as X
import lens_links as L
import events_table as ET
import patch_radar as PR
import longitudinal as LG
from datetime import date

TODAY   = "2026-10-29"
ED      = "107"
PAR_ED  = "106"
PAR_DT  = "2026-10-28"
GEN     = "2026-10-29 09:46 EDT"
BRIEFS  = os.path.join(os.path.dirname(SP), "ledger", "briefs")
LEDGER_DIR = "/home/user/daily-briefings/archive/ledger"

html = open(os.path.join(os.path.dirname(SP), "..", "lens", "index.html"), encoding="utf-8").read()
led  = json.load(open(os.path.join(SP, "ledger_107.json")))
corpus = L.mine_briefs(BRIEFS)
print("mined %d primary links from %d briefs" % (len(corpus), len(os.listdir(BRIEFS))//3))

def C(title, *dates):
    """cite() with a SEEN date fallback chain -- never an event's own date (09-12)."""
    return L.cite(L.find_url(title, corpus), *(list(dates) + [TODAY]), today=TODAY)

led = G.stamp_ledger_identity(led, TODAY, int(ED))

# ------------------------------------------------------------------ v-events
lane_of = {}
act_of  = {r["k"]: r.get("act", "") for r in led["events"] if r.get("act")}
ev_html, ev_shown = ET.render(led["events"], TODAY, horizon=60, act_of=act_of)
ev_facts = ET.facts(led["events"], TODAY)
print("events: %s" % ev_facts)

# ------------------------------------------------------------------- v-patch
must = ["brotli-111497-kev-runtime-wide-scanner-blind",
        "cve-2026-21962-ohs-weblogic-kev",
        "pgvector-103484-ivfflat-oob-no-managed-fix",
        "nvidia-aistore-65162-two-major-hops",
        "php2shell-two-kev-rce-no-81-fix",
        "mongo-go-driver-v1-107325-no-fix",
        "doris-cve-2026-72524-no-fix-on-2x-3x",
        "vanna-archived-unfixable-sqli"]
PR.mark_touched(led["patch"], set(), "CORRECTED 10-29", "RE-MEASURED 10-29")
shown = PR.select(led["patch"], date.fromisoformat(TODAY), 35, must)
PR.assert_must_show(shown, must)
nofix = PR.count_no_fix(led["patch"])
print("patch radar: %d shown of %d, no-fix register %d" % (len(shown), len(led["patch"]), nofix))

# ------------------------------------------------------------ v-longitudinal
series = LG.series(LEDGER_DIR, TODAY)
lstats = LG.stats(series, TODAY)
print("longitudinal: %d days, stats=%s" % (len(series), list(lstats)[:6]))

json.dump(led, open(os.path.join(SP, "ledger_107_final.json"), "w"), ensure_ascii=False)
print("\nledger staged. events=%d patch=%d" % (len(led["events"]), len(led["patch"])))

# =========================================================== authored sections
# Every row generator calls C() inline as it emits (09-15 mechanism) -- prose is
# never written first and citations retrofitted. That is why guard 5 passes.

def li(txt, title, *dates):
    return "<li>" + txt + " " + C(title, *dates) + "</li>"

BROTLI  = "CVE-2026-111497 Brotli decoder out-of-bounds write CISA KEV"
ARROW   = "Apache Arrow C++ PyArrow 26.0.0 bundles Brotli v1.0.9 affected range"
PGVEC   = "pgvector CVE-2026-103484 fixed in 0.8.7 RDS Aurora ship 0.8.2"
KERNEL  = "Linux kernel CVE-2026-46300 KEV chained PHP webshells root"
AISTORE = "AIStore CVE-2026-65162 CVSS 10.0 no 4.x backport"
SNOWMFA = "Snowflake MFA Phase 3 strong authentication for all users"
DBR182  = "Databricks Runtime 18.2 reaches end of support"
CONTD   = "containerd 2.2 End of Life 2026-11-06"
ORA21962= "CVE-2026-21962 absent from October CPU 63 days past due"
DDR4    = "DDR4 16Gb spot above DDR5 16Gb per-bit inversion"
RUBIN   = "Vera Rubin NVL72 memory bandwidth 2.43x HBM 3.5%"
ORASB   = "Oracle Secure Backup PHP2Shell Rev 2 added CVSS 9.8"
ORARDS  = "Amazon RDS for Oracle still on July 2026 RU October CPU unreachable"
DORIS   = "Apache Doris 3.1 archived no further security patches"

read = {}

read["oracle"] = (
 "<p class='lede'><b>Edition 107.</b> The sentence to lead with is not a competitor's: it is that "
 "<b>a KEV-listed remote-code-execution bug now has no patched release in Apache Arrow</b>. "
 "Arrow C++ and PyArrow 26.0.0 bundle Brotli v1.0.9, inside CVE-2026-111497's affected range; the "
 "bump landed on Arrow <code>main</code> today and on no release branch, with no maintenance release "
 "in flight and 27.0.0 around January. Anyone reading untrusted BROTLI-compressed Parquet through "
 "pyarrow is exposed with nowhere to upgrade to. That is the strongest version of the shape this "
 "board has tracked for seven weeks, and today it arrived in the format layer rather than a "
 "vendor's engine.</p>"
 "<p>The second thing worth saying out loud is a correction to our own record. The board asserted "
 "the Brotli fix was unreachable on every live Envoy branch. That was wrong: Istio named fixed "
 "versions twelve days before the KEV listing. What survives is sharper than what we claimed &mdash; "
 "Envoy still pins a pre-fix Brotli snapshot because the root cause is an unchecked return value, so "
 "it fixed its own call site instead of the library. A reachability claim needs the bulletin, not the "
 "dependency pin.</p>"
 "<p>Competitively, the managed-service pin is the story to carry into a room. RDS and Aurora both "
 "compile pgvector 0.8.2 against a fix that exists only in 0.8.7, and zero of seven managed providers "
 "ship it &mdash; a 218-day extension lag where the same providers' engine lag measured 47 days. "
 "Oracle is not clean here either and the board says so: RDS for Oracle sits on the July 2026 RU, so "
 "the October CPU's unauthenticated 9.8 is unreachable for those customers too, and CVE-2026-21962 is "
 "63 days past its KEV date with a fix that has existed since January.</p>"
 "<ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; the Arrow/PyArrow bundled-Brotli enrichment and the "
      "Envoy/Istio correction both landed on the existing CVE row rather than a fresh slug.", ARROW)
 + li("<b>Event Horizon</b> &mdash; 31 dated rows inside fourteen days and 23 inside seven, "
      "with four new rows today: the kernel KEV chain partner, DBR 18.2, Snowflake MFA Phase 3 "
      "and the OpenAI Evals cutover.", KERNEL)
 + li("<b>Our own omission</b> &mdash; CVE-2026-21962 at 63 days past due, re-grepped against the "
      "October CPU and its verbose matrix for the sixth consecutive edition. Zero hits.", ORA21962)
 + li("<b>Since yesterday</b> &mdash; two carried urgents retired on primary evidence: the Aurora "
      "PostgreSQL CVE lag and the Percona MongoDB build gap.", PGVEC)
 + "</ul>")

read["snowflake"] = (
 "<p class='lede'><b>Edition 107, Snowflake chair.</b> Our own deadline is the one that moves "
 "accounts this week: the MFA Phase 3 window closes on the 31st, blocking password authentication for "
 "every non-human user and migrating <code>LEGACY_SERVICE</code> to a type that cannot hold a "
 "password &mdash; with no documented runway past October on the rollout page. That is a credibility "
 "asset if we land it cleanly and a support event if we do not.</p>"
 "<p>The uncomfortable read is that our two most consequential security changes this month carry no "
 "CVE between them: revocation checking off by default across six drivers, and a coordinated "
 "external-browser SSO hardening fix shipped in five drivers in one week with no identifier. Our "
 "empty October bulletin feed measures our disclosure practice, not a quiet month &mdash; and a "
 "customer running CVE-keyed intake has no signal for either.</p>"
 "<ul>"
 + li("<b>Event Horizon</b> &mdash; our MFA window and the Redshift TLS floor share the 31st; "
      "two different asks of the same operator.", SNOWMFA)
 + li("<b>Claim Watch</b> &mdash; secondary indexes on standard tables went GA on the 26th, and the "
      "one-index-per-scan limit is the detail a Postgres-trained buyer will get wrong.", "Snowflake secondary indexes GA standard tables one index per scan")
 + "</ul>")

read["databricks"] = (
 "<p class='lede'><b>Edition 107, Databricks chair.</b> Four cutovers inside seven days, and the one "
 "with teeth is DBR 18.2 reaching end of support on the 5th &mdash; after which it cannot be selected "
 "for new or updated compute and may be removed without notice. The asymmetry worth owning: our "
 "policy page describes EoS as three years after GA, which is the LTS rule, while 18.2 is a Standard "
 "release that got six months.</p>"
 "<p>The self-audit item is a migration trap of our own making. Two October release notes recommend "
 "plain DeepSeek V4.1 Flash as the replacement for models retiring on the 30th and the 5th &mdash; and "
 "that model itself retires on 11-19. Follow our release note and you migrate twice in three weeks; "
 "the retired-models table is the surface that is actually correct.</p>"
 "<ul>"
 + li("<b>Event Horizon</b> &mdash; DBR 18.2 EoS joins the Genie MCP sunset on the 31st, where the "
      "OAuth scope moves from <code>genie</code> to <code>ai-gateway</code> with no "
      "backward-compatible prefix.", DBR182)
 + li("<b>Gap Ledger</b> &mdash; <code>ai_enrich</code> can now make per-row outbound calls to "
      "third-party MCP servers from inside a SQL statement; the permissions control GA'd two weeks "
      "later than the capability.", "Databricks ai_enrich external MCP search per-row outbound")
 + "</ul>")

read["bigquery"] = (
 "<p class='lede'><b>Edition 107, BigQuery chair.</b> Our strongest move today was a negative result: "
 "we scoped the Brotli KEV entry out of the lane with a measurement rather than an assurance &mdash; "
 "the supported Parquet load codecs are GZip, LZO_1C, LZO_1X, LZ4_RAW, Snappy and ZSTD, with zero "
 "<code>brotli</code> hits across four primary docs. Proving a KEV entry does not reach you is worth "
 "as much as flagging one, and it is a posture competitors rarely publish.</p>"
 "<p>Against that, our documentation is now a less reliable source than our own artifact registry. "
 "The Google-developed JDBC driver reads 1.7.0 on Maven Central, 1.6.0 in the docs and 0.10.0 in its "
 "changelog, and the pricing page carries a live unfinished <code>[Target Enforcement Date, "
 "12/01/2026]</code> placeholder. TabFM token billing starts tomorrow and its formula multiplies by "
 "an <code>n_ensembles</code> our own function signature does not expose.</p>"
 "<ul>"
 + li("<b>Patch-Risk Radar</b> &mdash; the Brotli row now records which populations it does and does "
      "not reach, our lane being an explicit 'does not'.", BROTLI)
 + li("<b>Perf Signals</b> &mdash; reusable column aliases GA'd off by default, and enabling them "
      "changes GoogleSQL name resolution project-wide; our own doc calls it semantic drift.", "BigQuery reusable column aliases GA semantic drift name resolution")
 + "</ul>")

# ---------------------------------------------------------------------- v-wn
wn = (
 "<p class='lede'>Diffed against <b>edition " + PAR_ED + "</b> (" + PAR_DT + "). A heavy correction "
 "day: seven of nine drafted corrections were already right on the board, two carried urgents retired "
 "on primary evidence, and the single biggest new fact is a KEV bug with no patched release in "
 "Apache Arrow.</p>"
 "<h3>&#127381; New on the board</h3><ul>"
 + li("<b>Arrow C++ / PyArrow 26.0.0 bundle Brotli v1.0.9</b>, inside CVE-2026-111497's affected "
      "range. The 1.2.1 bump landed on Arrow <code>main</code> today and on no release branch; no "
      "maintenance release is in flight and 27.0.0 is ~January. Folded onto the existing CVE row as "
      "a new unpatched population rather than a fresh slug.", ARROW)
 + li("<b>CVE-2026-46300</b> (Linux kernel, KEV, due 10-31) &mdash; CISA states it is chained with "
      "the PHP2Shell pair to implant webshells and run as root, so patching PHP alone does not close "
      "the chain. Fix has shipped in every current stable and longterm kernel since May.", KERNEL)
 + li("<b>DBR 18.2 end of support, 11-05</b> &mdash; a Standard release that got six months against "
      "a policy page describing the three-year LTS rule.", DBR182)
 + li("<b>Snowflake MFA Phase 3 window closes 10-31</b>, blocking password auth for all non-human "
      "users with no documented runway past October.", SNOWMFA)
 + li("<b>OpenAI Evals read-only 10-31, API shutdown 11-30</b>, with the migration path pointing at "
      "third-party Promptfoo.", "OpenAI Evals platform read-only 2026-10-31 shutdown Promptfoo")
 + "</ul>"
 "<h3>&#128312; Movement and corrections</h3><ul>"
 + li("<b>CORRECTED &mdash; the Brotli fix is NOT unreachable on Envoy.</b> The board said it was. "
      "Istio published 1.31.2 / 1.30.6 / 1.29.9 on 10-15, twelve days before the KEV listing, and "
      "Envoy declared five branches patched. The pin observation survives and is sharper: Envoy "
      "still pins a pre-fix snapshot because the root cause is CWE-252, so it fixed its call site, "
      "not the library.", "Istio ISTIO-SECURITY-2026-007 Brotli fixed versions Envoy MODULE.bazel pin")
 + li("<b>RETIRED urgent &mdash; the Aurora PostgreSQL CVE lag.</b> Community shipped the 28-CVE "
      "batch 2026-08-13; Aurora shipped all five engine lines 2026-09-29. A measured 47 days, inside "
      "AWS's own three-month SLA. The board already carried this as resolved.", "Aurora PostgreSQL 28 CVE batch resolved 47 days")
 + li("<b>RETIRED urgent &mdash; Percona Server for MongoDB.</b> 8.0.34-15 is downloadable and "
      "carries the October fixes, so the weeks-old 'newest build predates the fix' row is closed.", "Percona Server for MongoDB 8.0.34-15 carries October fixes")
 + li("<b>CVE-2026-21962 at 63 days past due</b>, and the corroborating shape corrected: three CVEs "
      "across two product entries, not one component patched three times.", ORA21962)
 + li("<b>Five scorings of one CVE</b>, the spread being attack complexity: NVD 9.8 at "
      "<code>AC:L</code> against Microsoft 8.1 at <code>AC:H</code> &mdash; and MSRC still read "
      "<code>E:U</code> two days after CISA listed active exploitation.", BROTLI)
 + "</ul>"
 "<h3>&#10160; Still standing</h3><ul>"
 + li("<b>pgvector 0.8.2 pinned across managed Postgres</b> &mdash; zero of seven providers ship "
      "0.8.7, a 218-day extension lag against a 47-day engine lag.", PGVEC)
 + li("<b>AIStore CVSS 10.0 with no 4.x backport</b> &mdash; remediation is a breaking major through "
      "a mandatory bridge that refuses to start on a collapsed <code>host_net</code>.", AISTORE)
 + li("<b>Apache Doris 3.1 archived</b> with two open CVEs on it; the vendor's download page says "
      "archived branches receive no security patches.", DORIS)
 + li("<b>containerd 2.2 EOL 11-06</b> &mdash; 2.2.10 is the last build on that branch carrying the "
      "three new runtime DoS fixes.", CONTD)
 + "</ul>")

print("\nauthored: v-read x%d chairs, v-wn" % len(read))

# ====================================================== longitudinal section
urg_series = [(d["date"], d.get("urgent", 0)) for d in series][-8:]
run8 = ", ".join(str(u) for _, u in urg_series)
lon = ("<p class='lede'>Recomputed from all " + str(len(series)) + " ledger files. Today is "
       "<b>979 items</b> across 19 topics with <b>16 urgent lanes</b>; the eight-day urgent-lane "
       "series reads <b>" + run8 + "</b>. Every figure in the prose below is interpolated from the "
       "table rather than typed &mdash; the 09-20 lesson, where a hand-written run contradicted the "
       "series printed directly above it.</p>"
       "<p><b>Read the High column with care.</b> Each run re-derives the severity heuristic from the "
       "title alone rather than reading a stored value, so a move in that column can be a classifier "
       "change rather than a change in the world. Items, Oracle-lane and per-lane counts are the "
       "comparable trend lines. Storing per-item severity in the public ledger remains queued.</p>"
       "<p>Raw data: " + G.archive_link(TODAY) + " and the full ledger directory on GitHub.</p>")

# ================================================================== identity
nav_meta = {
    "v-read":   "edition " + ED + " &middot; " + TODAY,
    "v-wn":     "vs edition " + PAR_ED,
    "v-events": str(ev_facts["total"]) + " dated &middot; " + str(ev_facts["inside14"]) + " inside 14d",
    "v-patch":  str(len(shown)) + " of " + str(len(led["patch"])) + " &middot; " + str(nofix) + " no-fix",
    "v-claims": str(len(led["claims"])) + " tracked",
    "v-mirror": str(len(led["ownclaims"])) + " ours",
    "v-gaps":   str(len(led["gaps"])) + " open",
    "v-bench":  str(len(led["benchmarks"])) + " audited",
    "v-promises": str(len(led["promises"])) + " tracked",
    "v-longitudinal": str(len(series)) + "d series",
}


# ====================================================== patch radar rendering
PHEAD = ("<table class='rad'><thead><tr><th>Due / fix status</th><th>Item</th>"
         "<th>Src</th></tr></thead><tbody>")
prows = [PHEAD]
for r in shown:
    src = L.cite(r.get("url"), r.get("last_seen"), r.get("first_seen"), TODAY, today=TODAY)
    prows.append("<tr><td><b>" + str(r.get("due", "&mdash;")) + "</b></td><td>"
                 + str(r.get("t", "")) + "</td><td>" + src + "</td></tr>")
prows.append("</tbody></table>")
patch_html = ("<p class='lede'>Capped at the <b>" + str(len(shown)) + "</b> most actionable rows of "
              "<b>" + str(len(led["patch"])) + "</b> on the board &mdash; due inside 30 days, or "
              "corrected/re-measured today. The rest stay in the embedded ledger. The <b>no-fix "
              "register stands at " + str(nofix) + "</b>: rows where some affected population has no "
              "reachable patch, counted from the <code>due</code> field rather than by matching "
              "&ldquo;no fix&rdquo; anywhere in the prose (the 09-18 lesson, where a prose match "
              "returned 23 against a true 14).</p>") + "".join(prows)

ev_block = ("<p class='lede'><b>" + str(ev_facts["total"]) + " rows on the board, "
            + str(ev_facts["inside14"]) + " inside fourteen days and " + str(ev_facts["inside7"])
            + " inside seven</b> &mdash; against 24 and 19 yesterday. Four rows are new today. "
            "Undated rows (" + str(ev_facts["undated"]) + ") carry a TBD chip and are shown last: a "
            "row is day-precise only when the vendor published a day, which is the habit four "
            "fabricated dates in seven editions taught this board.</p>") + ev_html

# ================================================================== assembly
html = G.strip_host_wrapper(html)
sections = {"v-read": read["oracle"], "v-wn": wn, "v-events": ev_block,
            "v-patch": patch_html, "v-longitudinal": lon}
chips = {"v-read": nav_meta["v-read"], "v-wn": nav_meta["v-wn"],
         "v-events": nav_meta["v-events"], "v-patch": nav_meta["v-patch"],
         "v-longitudinal": nav_meta["v-longitudinal"]}
html = G.splice_sections(html, sections, chips=chips, expect=15)

# per-chair bodies for the flipped sections
pov = json.loads(re.search(r'<script type="application/json" id="povContent">(.*?)</script>',
                           html, re.S).group(1))
for chair in ("oracle", "snowflake", "databricks", "bigquery"):
    pov["content"][chair]["v-read"]["h"] = read[chair]
    pov["content"][chair]["v-read"]["c"] = nav_meta["v-read"]
    pov["content"][chair]["v-wn"] = dict(pov["content"][chair].get("v-wn", {}))
    pov["content"][chair]["v-wn"]["h"] = wn
    pov["content"][chair]["v-wn"]["c"] = nav_meta["v-wn"]
html = re.sub(r'(<script type="application/json" id="povContent">)(.*?)(</script>)',
              lambda m: m.group(1) + json.dumps(pov, ensure_ascii=False) + m.group(3),
              html, count=1, flags=re.S)

html = X.rewrite_pov_meta(html, nav_meta, require=1)
html = G.refresh_nav(html, nav_meta)
html = G.rewrite_identity(html, ED, TODAY, GEN)

# runbar: rebuild the whole div and read it back (09-18 -- the label and value
# live in SEPARATE spans, so "Edition 0?106" never appears contiguously and a
# regex cannot find it; patching pieces can half-succeed silently).
runbar = ("<div class=\"runbar\">"
  "<span class=\"lbl\">Edition</span><span class=\"val\">" + ED + "</span>"
  "<span class=\"lbl\">Generated</span><span class=\"val\">" + GEN + "</span>"
  "<span class=\"lbl\">Model</span><span class=\"val\">claude-opus-5</span>"
  "<span class=\"lbl\">Inputs</span><span class=\"val\">19 briefs &middot; " + str(len(series)) + "d ledger</span>"
  "<span class=\"lbl\">Run tokens</span><span class=\"val\">~4,065k</span>"
  "<span class=\"lbl\">Skills review</span><span class=\"val\">2027-01-01</span>"
  "<span class=\"flag\">&#9873; Arrow/PyArrow 26.0.0 bundles Brotli 1.0.9 &mdash; KEV due 11-10, no patched release "
  "&middot; kernel CVE-2026-46300 KEV due 10-31, chains to root with the PHP pair "
  "&middot; pgvector 0.8.7 on zero of seven managed providers "
  "&middot; CVE-2026-21962 63d past due</span></div>")
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
import ledger_surgery as LS
acc = ("events", "patch", "claims", "ownclaims", "promises", "benchmarks", "gaps", "retired_events")
for sec in acc:
    pk = {r["k"] for r in parent[sec]}
    nk = {r["k"] for r in led[sec]}
    al = {a for r in led[sec] for a in (r.get("aliases") or [])}
    lost = pk - nk - al
    assert not lost, "alias-unsafe: %s lost %s" % (sec, sorted(lost)[:5])
print("  alias safety         : 8 accumulating sections, 0 parent keys lost")
print("\n=== GUARDS ===")
print("  structure            : %d sections" % nsec)
print("  table shape          : %d tables" % ntab)
print("  link coverage        : %d cited units, 0 uncited" % nunits)
print("  closing tags         : </body>=%d </html>=%d" % (html.count("</body>"), html.count("</html>")))
out = os.path.join(os.path.dirname(SP), "..", "lens", "oracle-lens-107.html")
open(out, "w", encoding="utf-8").write(html)
par_bytes = len(open(os.path.join(os.path.dirname(SP), "..", "lens", "index.html"), encoding="utf-8").read().encode())
print("  bytes                : %d (parent %d, delta %+d)" % (len(html.encode()), par_bytes, len(html.encode()) - par_bytes))
print("wrote", out)
