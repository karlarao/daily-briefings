#!/usr/bin/env python3
"""Edition 109 lens build. Inheritance from 108 + spliced sections.

House style (09-18/09-20): HTML blocks embedding cite() output are built by
CONCATENATION with explicit str(), never %-formatted -- ledger prose carries
literal % signs and %-formatting consumes them. This has bitten four times.

Numbers that appear in prose next to the table they describe are interpolated
from that table, never typed (the 09-20 lesson, learned the embarrassing way).
"""
import json, os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import lens_guard as G, lens_extra as X, lens_links as L
import events_table as ET, patch_radar as PR, longitudinal as LG
from datetime import date

TODAY, ED, PAR_ED, PAR_DT = "2026-10-31", "109", "108", "2026-10-30"
GEN = "2026-10-31 09:12 EDT"
RUN_TOKENS = "~3,890k"
BRIEFS = os.path.join(os.path.dirname(SP), "ledger", "briefs")
LEDGER_DIR = "/home/user/daily-briefings/archive/ledger"
PARENT = os.path.join(SP, "index.html")

html = open(PARENT, encoding="utf-8").read()
led = json.load(open(os.path.join(SP, "ledger_109.json")))
corpus = L.mine_briefs(BRIEFS)
print("mined %d primary links from %d briefs" % (len(corpus), len(os.listdir(BRIEFS)) // 3))

def C(title, *dates):
    """cite() with a SEEN-date fallback chain -- never an event's own date (09-12).
    None-safe: C(None, d) gives the dated public-archive link, the honest
    citation for a claim about this edition's own board (09-17)."""
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
MUST = ["edk2-97631-preboot-pxe-rce-no-tag",
        "clickhouse-116366-unauth-rce-no-267-fix",
        "pgbouncer-107350-scram-bypass",
        "brotli-111497-kev-runtime-wide-scanner-blind",
        "cve-2026-21962-ohs-weblogic-kev",
        "supermicro-bmc-18450-two-skus-tbd",
        "pinot-73322-lookup-acl-bypass-no-152",
        "parquet-java-1190-rc9-no-ga-bloom-fix",
        "n8n-databricks-node-119557-unpatched",
        "mongo-node-driver-timeoutms-crossuser-no-6x",
        "percona-mysql-84-no-oct-cpu-build",
        "kernel-98432-mptcp-uaf-go-default-on",
        "mongodb-server-131805-sharded-rename-dataloss",
        "k8s-oct-patch-overdue-all-four-branches"]
NEWP = {"pinot-73322-lookup-acl-bypass-no-152", "parquet-java-1190-rc9-no-ga-bloom-fix",
        "n8n-databricks-node-119557-unpatched", "mongo-node-driver-timeoutms-crossuser-no-6x",
        "percona-mysql-84-no-oct-cpu-build", "kernel-98432-mptcp-uaf-go-default-on",
        "kafka-110952-oauthbearer-iss-aud-unset", "valkey-cluster-pubsub-heap-overflow-5-branches"}
PR.mark_touched(led["patch"], NEWP, "CORRECTED 10-31", "RE-MEASURED 10-31",
                "SHARPENED 10-31", "NEW POPULATION 10-31", "VERIFIED 10-31", "IN FORCE 10-31")
shown = PR.select(led["patch"], date.fromisoformat(TODAY), 35, MUST)
PR.assert_must_show(shown, MUST)
nofix = PR.count_no_fix(led["patch"])
print("patch radar: %d shown of %d, no-fix register %d" % (len(shown), len(led["patch"]), nofix))

# ------------------------------------------------------------ v-longitudinal
series = LG.series(LEDGER_DIR, TODAY)
ls = LG.stats(series, TODAY)
run8 = [r["urgent"] for r in series[-8:]]
print("longitudinal: %d days, urgent run8=%s stats=%s" % (len(series), run8, ls))

# ------------------------------------------------------------------ parent diff
pw = json.load(open(os.path.join(SP, "parent_ledger.json")))
pk = {s: {r["k"] for r in pw.get(s, [])} for s in ("events", "patch")}
new_ev_k = [r["k"] for r in led["events"] if r["k"] not in pk["events"]]
new_pa_k = [r["k"] for r in led["patch"] if r["k"] not in pk["patch"]]
ret = [r["k"] for r in led["events"] if str(r.get("date") or "") and str(r["date"]) < TODAY]
print("vs parent: +%d events, +%d patch, %d past-dated event rows" % (len(new_ev_k), len(new_pa_k), len(ret)))

# =========================================================== authored sections
import build_109_body as B
ctx = dict(G=G, X=X, L=L, ET=ET, PR=PR, LG=LG, C=C, li=li,
           TODAY=TODAY, ED=ED, PAR_ED=PAR_ED, ef=ef, shown=shown, nofix=nofix,
           led=led, series=series, ls=ls, run8=run8,
           new_ev_k=new_ev_k, new_pa_k=new_pa_k, ret=ret, ev_html=ev_html)
read, wn, lon, patch_html, ev_block, NAV = B.build(ctx)

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

# runbar: rebuild the whole div and read it back (09-18 -- label and value live
# in SEPARATE spans, so "Edition 108" never appears contiguously and no regex
# can find it; patching pieces half-succeeds silently).
runbar = ("<div class=\"runbar\">"
  "<span class=\"lbl\">Edition</span><span class=\"val\">" + ED + "</span>"
  "<span class=\"lbl\">Generated</span><span class=\"val\">" + GEN + "</span>"
  "<span class=\"lbl\">Model</span><span class=\"val\">claude-opus-5</span>"
  "<span class=\"lbl\">Inputs</span><span class=\"val\">19 briefs &middot; " + str(len(series)) + "d ledger</span>"
  "<span class=\"lbl\">Run tokens</span><span class=\"val\">" + RUN_TOKENS + "</span>"
  "<span class=\"lbl\">Skills review</span><span class=\"val\">2027-01-01</span>"
  "<span class=\"flag\">&#9873; Linux kernel CVE-2026-46300 KEV due TODAY "
  "&middot; GitLab CVE-2026-97229 CVSS 10.0 KEV due TOMORROW, Metasploit PR open "
  "&middot; EDK II PXE pre-boot RCE &mdash; no tagged release, Debian unfixed incl. OVMF "
  "&middot; ClickHouse 9.5 unauth RCE unpatched on 26.7 and below "
  "&middot; Azure's managed PgBouncer pinned at 1.25.2 &mdash; no customer fix for the SCRAM bypass "
  "&middot; Redshift TLS 1.2 minimum in force today "
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
acc = ("events", "patch", "claims", "ownclaims", "promises", "benchmarks", "gaps", "retired_events")
for sec in acc:
    pks = {r["k"] for r in pw[sec]}
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
out = os.path.join(SP, "oracle-lens-109.html")
open(out, "w", encoding="utf-8").write(html)
pb = len(open(PARENT, encoding="utf-8").read().encode())
print("  bytes                : %d (parent %d, delta %+d)" % (len(html.encode()), pb, len(html.encode()) - pb))
print("wrote", out)
