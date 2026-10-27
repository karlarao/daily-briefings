#!/usr/bin/env python3
"""Edition 099 assembly: Read x4 chairs, Since-yesterday, identity, guards."""
import json, os, sys, re
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import lens_guard as G, lens_extra as X, lens_links as LK

TODAY, EDS, ED = "2026-10-21", "099", 99
GEN = "2026-10-21 09:18 EDT"
PARENT_ED, PARENT_DATE = "098", "2026-10-20"

html = open(os.path.join(SP, "../../lens/parent_stripped.html"), encoding="utf-8").read()
parent = json.load(open(os.path.join(SP, "parent_ledger.json")))
ledger = json.load(open(os.path.join(SP, "ledger_099.json")))
parts = json.load(open(os.path.join(SP, "parts_099.json")))
C = lambda u, *d: LK.cite(u, *d, today=TODAY)
A = C(None, TODAY)                                   # dated archive fallback

NOFIX, EVN = parts["nofix"], parts["ev_shown"]

# ------------------------------------------------------- SINCE YESTERDAY ---
pk = {s: {r["k"] for r in parent.get(s, []) if isinstance(r, dict)} for s in parent
      if isinstance(parent[s], list)}
newp = [r for r in ledger["patch"] if r["k"] not in pk.get("patch", set())]
corrected = [r for r in ledger["patch"] + ledger["events"]
             if re.search(r"(CORRECTED|UPDATED|RE-MEASURED|October actuals|PUBLISHED|SHIPPED today)", r.get("t") or "")]
retired = [r for r in ledger["retired_events"] if r.get("retired") == TODAY]
wn = ("<p class='lede'>Diffed against edition " + PARENT_ED + " (" + PARENT_DATE + "). The movement today is "
      "almost entirely <b>corrections and confirmations</b>, not new stories: probing the key list before "
      "drafting turned up an existing row for every candidate but one. " + A + "</p>"
      "<div class='wngroup'><h3>\U0001f195 New on the board (1)</h3>"
      "<div class='wnitem'><b>A certificate-authority compromise reached two language runtimes in two "
      "days, and only one of them names it.</b> Go 1.27.3 / 1.26.10 add a <code>crypto/x509</code> denylist "
      "on the URGENT track without naming a CA; Node's release the next day names an eMudhra intermediate "
      "CA compromise outright. Statically linked Go services need a rebuild, not a restart. "
      + C("https://groups.google.com/g/golang-announce/c/66pojueaQek") + "</div></div>"
      "<div class='wngroup'><h3>\U0001f53a Corrected or re-measured (" + str(len(corrected)) + ")</h3>"
      "<div class='wnitem'><b>A date we invented is withdrawn.</b> The Cortex-models RBAC retirement "
      "carried a day-precise <b>2026-11-18</b> since edition 094. It appears on no Snowflake page: BCR-2378 "
      "is dated Aug 5 2026 with &ldquo;rollout completes January 2027&rdquo;, month precision only. The row is now "
      "undated, and it is already live for opt-out accounts via bundle 2026_07. " + A + "</div>"
      "<div class='wnitem'><b>Oracle's CPU published ~24h late, and the APEX 9.8 is still unpatchable.</b> "
      "1,295 patches; Database Server took 14 at max 9.8, not the 13 at 8.8 the pre-release page implied. "
      "CVE-2026-101521 is now readable; its fixed version is not. " + A + "</div>"
      "<div class='wnitem'><b>Node.js shipped on time; Kubernetes still has not.</b> Node tagged at 10:38Z "
      "with a Brotli out-of-bounds write permitting RCE. Every Kubernetes <code>stable-1.3x</code> pointer "
      "still serves the 2026-09-23 batch, a second consecutive day measuring empty. " + A + "</div>"
      "<div class='wnitem'><b>pgvector is the register's cleanest instance yet.</b> 0.8.7 fixed the IVFFlat "
      "out-of-bounds write on 2026-10-01; RDS, Aurora and Azure ship 0.8.2, Cloud SQL 0.8.5, AlloyDB "
      "0.8.2.google-1, Neon 0.8.0. Nobody ships the fix. " + A + "</div>"
      "<div class='wnitem'><b>CVE-2026-21962 is 55 days past due, now confirmed rather than assumed</b> &mdash; "
      "a grep of the published October CPU finds zero mentions of it. " + A + "</div></div>"
      "<div class='wngroup'><h3>➰ Retired (" + str(len(retired)) + ")</h3><div class='wnitem'>"
      + ", ".join("<code>" + r["k"] + "</code>" for r in retired)
      + " &mdash; dates passed; moved into <code>retired_events[]</code> rather than deleted. " + A + "</div></div>")

# ------------------------------------------------- TODAY'S READ, 4 CHAIRS ---
def read(lede, spend):
    return ("<p class='lede'>" + lede + "</p><h3>Where to spend today's attention</h3><ul>"
            + "".join("<li>" + b + "</li>" for b in spend) + "</ul>")

ORACLE = read(
 "Two of the three patch days this board was watching resolved today, in opposite directions, and the "
 "gap between them is the competitive story. <b>Oracle's October CPU published</b> about a day late with "
 "<b>1,295 patches</b> &mdash; and the sharpest fact in it is ours to own: <b>Oracle APEX takes a CVSS 9.8 "
 "remotely exploitable without authentication (CVE-2026-101521) whose fixed version cannot be read</b>, "
 "because apex.oracle.com returns 403 and the risk matrix lists affected ranges only. A customer will "
 "quote that back, so say it first: the identifier is public, the remediation is not. <b>Node.js shipped "
 "on schedule at 10:38Z; Kubernetes' postponed October patch day has still shipped nothing</b>, a second "
 "consecutive day of measuring every <code>stable-1.3x</code> pointer on the September batch. The top of "
 "our own CPU is bundled third-party code &mdash; the 9.8 in Database Server is OpenSSL, both MySQL 9.8s are "
 "curl and OpenSSL &mdash; which cuts both ways: it is not our code, and it is our patch to ship. Meanwhile "
 "the day's cleanest competitor wound is managed-service pinning: <b>pgvector 0.8.7 fixed an index-build "
 "out-of-bounds write three weeks ago and not one managed Postgres ships it</b>.",
 ["<b>Patch-Risk Radar</b> &mdash; the APEX row now carries the CVE id and still carries no fixed version. "
  "Of " + str(len(ledger["patch"])) + " rows, <b>" + str(NOFIX) + "</b> have no reachable fix. " + A,
  "<b>Event Horizon</b> &mdash; " + str(EVN) + " dated items inside 60 days, led by the 30/31 October wall: "
  "Redshift's TLS 1.2 floor, Databricks' Genie MCP sunset and two model retirements. " + A,
  "<b>Claim Watch carries forward unrevised</b>, and that is the honest read of the day: no competitor "
  "shipped a performance or price claim worth a card, and <code>claims[]</code> did not grow at all. " + A,
  "<b>Ask in the room:</b> &ldquo;When your advisory names a CVSS 9.8 but not the fixed version, what is your "
  "customer supposed to do for the next 24 hours?&rdquo; &mdash; then be ready for it pointed back at APEX. " + A])

SNOW = read(
 "From this chair the day is a governance-plumbing day, and the risk is that two changes in force break "
 "customers who never read a release note. <b>The Snowsight account-specific host took effect 2026-10-16 "
 "with no opt-out</b>, so anyone reaching Snowflake over a public connection through a filtering firewall, "
 "proxy or SASE path simply stops connecting until the new host is allowlisted &mdash; and bundle 2026_08 "
 "queues the same shape for Streamlit and SPCS endpoints. <b>Bundle 2026_07 went Enabled-by-Default the "
 "same day</b>. The item to test before it is enabled is BCR-2433: <code>CREATE OR REPLACE</code> will "
 "copy grants by default, so a rebuild stops revoking access &mdash; a privilege-model change with no error "
 "message. One correction is owed in the other direction: this board carried a day-precise 2026-11-18 for "
 "the Cortex-models RBAC retirement, and Snowflake publishes no such day.",
 ["<b>Patch-Risk Radar</b> &mdash; the driver-log CVE (CVE-2026-86597) is fixed across Python, JDBC, Go v2, "
  "Node and ODBC, but <b>Go v1 <code>gosnowflake</code> has no fixed version</b>: v1 is marked "
  "last_affected 1.19.1 and the fix is v2-only. " + A,
  "<b>Credit to them where it is due:</b> Snowflake largely FIXED its OSV mapping this window &mdash; driver "
  "advisories now carry ecosystem-qualified packages with ranges, reversing a note this board held against "
  "them for weeks. ODBC and PHP remain registry-less and so invisible by construction. " + A,
  "<b>Event Horizon</b> &mdash; CoWork enables dashboard data access for agents on 26 Oct, five days out. " + A])

DBX = read(
 "Two hard cutovers land inside eleven days and both are narrow, which is the right way to read them: "
 "<b>the Beta Genie MCP endpoint <code>/api/2.0/mcp/genie</code> sunsets 2026-10-31</b> (move to the GA "
 "<code>system.ai.genie_one_mcp</code> service) and <b>DeepSeek V4 Pro and Thinking Machines Inkling "
 "retire 2026-10-30</b>. Neither touches a customer who is not calling those endpoints. The structural "
 "story is that governance keeps moving into the engine &mdash; ABAC now reaches views, time travel and "
 "external engines, and multi-statement transactions went GA across managed Delta <i>and</i> managed "
 "Iceberg &mdash; with catalog commits plus DBR 19 or serverless as the shared dependency, so a pinned runtime "
 "quietly cannot enforce what the docs describe. The agent surface is churning faster than the data "
 "surface: Supervisor Agent and Knowledge Assistant went <i>legacy</i> within weeks of their replacements "
 "shipping.",
 ["<b>A correction in our own favour:</b> this board recorded the Agent Bricks Supervisor API as retired "
  "on 2026-09-30. The schedule page said so; the release notes say only that it went <i>legacy</i> on "
  "10-12. Scheduled is not executed, and the row should say which it is. " + A,
  "<b>No new runtime shipped in the window</b> &mdash; DBR 19 (15 Jun) is still newest, and 10.4 LTS is past "
  "end of support with the detection SQL on the lifecycle page. " + A,
  "<b>Event Horizon</b> &mdash; variant shredding becomes automatic on 2026-11-18 for new VARIANT tables on "
  "DBR 17.3+, and clusters on 15.4 cannot read them. Upgrade readers first. " + A])

BQ = read(
 "A quiet-but-busy GA month with the weakest dated item of the four chairs, and the honest thing to say "
 "is that the one date on the board is <b>press-reported and absent from every Google page</b>: TabFM "
 "token billing on 2026-10-30, which InfoWorld reports and for which no per-token rate is published "
 "anywhere. Everything else was additive &mdash; <code>AI.AGG</code>, <code>gemini-4-argon</code> and "
 "<code>gemini-embedding-2</code> GA, TimesFM 3.0 in preview, reusable column aliases opt-in, cross-region "
 "table copy GA &mdash; with <b>no deprecations and no day-precise breaking change in the window</b>. The "
 "cost-governance direction is the thing to watch: token quotas, token-based TabFM billing and a "
 "per-project daily cap mean AI spend will need watching in tokens alongside slot-hours and bytes scanned.",
 ["<b>Declined to flag, correctly:</b> the carried CVSS 9.4 RCE was patched server-side in May with no "
  "customer action, and the September bulletins name Application Integration and Istio, not BigQuery. " + A,
  "<b>Before 10-30:</b> pull the Cloud Billing SKU for TabFM and price a representative job against your "
  "cached-model path, because the rate is not published and the date is not either. " + A,
  "<b>The agent surface widened again</b> &mdash; the DTS MCP server went GA, and <code>run_bq_command</code> "
  "still exposes the <code>bq</code> CLI including reservation management with IAM as the only control. " + A])

povc = json.loads(re.search(r'<script type="application/json" id="povContent">(.*?)</script>', html, re.S).group(1))
READS = {"oracle": ORACLE, "snowflake": SNOW, "databricks": DBX, "bigquery": BQ}
SUBS = {"oracle": "two patch days resolved, one did not",
        "snowflake": "two changes already in force",
        "databricks": "two cutovers, both narrow",
        "bigquery": "the one date is press-only"}
for chair, body in READS.items():
    povc["content"][chair]["v-read"]["h"] = body
    povc["content"][chair]["v-read"]["c"] = "edition " + EDS + " &middot; " + TODAY
    for vid in povc["meta"][chair]:
        povc["meta"][chair][vid] = re.sub(r"edition \d+", "edition " + EDS,
                                          povc["meta"][chair][vid])
    povc["meta"][chair]["v-read"] = "edition " + EDS + " &middot; " + SUBS[chair]
    povc["meta"][chair]["v-wn"] = "vs edition " + PARENT_ED
html = re.sub(r'(<script type="application/json" id="povContent">).*?(</script>)',
              lambda m: m.group(1) + json.dumps(povc, ensure_ascii=False) + m.group(2),
              html, count=1, flags=re.S)
print("povContent: rewrote v-read for 4 chairs + every meta label")

# ------------------------------------------------------------- SPLICE ------
sections = {"v-read": ORACLE, "v-wn": wn, "v-events": parts["ev"],
            "v-patch": parts["patch"], "v-longitudinal": parts["long"]}
chips = {"v-read": "edition " + EDS + " &middot; " + TODAY,
         "v-wn": "vs edition " + PARENT_ED,
         "v-events": str(EVN) + " dated items &middot; next 60 days",
         "v-patch": "26 of " + str(len(ledger["patch"])) + " &middot; " + str(NOFIX) + " no reachable fix",
         "v-longitudinal": str(parts["days"]) + " ledger days"}
html = G.splice_sections(html, sections, chips=chips, expect=15)
print("spliced 5 of 15 sections (expect counts sections VISITED, not replaced)")

# ----------------------------------------------------------- IDENTITY ------
html = G.rewrite_identity(html, EDS, TODAY, GEN)
nav_meta = {"v-events": str(EVN) + " dated &middot; next 60d",
            "v-patch": "26 of " + str(len(ledger["patch"])) + " &middot; " + str(NOFIX) + " no fix",
            "v-longitudinal": str(parts["days"]) + " ledger days",
            "v-claims": str(len(ledger["claims"])) + " tracked &middot; carried from " + PARENT_ED,
            "v-mirror": str(len(ledger["ownclaims"])) + " own claims &middot; carried from " + PARENT_ED,
            "v-gaps": str(len(ledger["gaps"])) + " open &middot; carried from " + PARENT_ED,
            "v-promises": str(len(ledger["promises"])) + " rows &middot; carried from " + PARENT_ED,
            "v-bench": str(len(ledger["benchmarks"])) + " audited &middot; carried from " + PARENT_ED,
            "v-read": "edition " + EDS + " &middot; " + TODAY,
            "v-wn": "vs edition " + PARENT_ED}
html = G.refresh_nav(html, nav_meta)
# rewrite_pov_meta drives EVERY chair's meta from one dict, so passing v-read
# here would flatten the four chair-specific subtitles set above. Give it only
# the count-bearing views; the per-chair v-read/v-wn labels are already written.
pov_meta = {k: v for k, v in nav_meta.items() if k not in ("v-read", "v-wn")}
html = X.rewrite_pov_meta(html, pov_meta, require=1)
html = G.write_ledger(html, G.stamp_ledger_identity(ledger, TODAY, ED))
html = X.normalize_closing_tags(html)

# -------------------------------------------------------------- GUARDS -----
G.assert_identity_consistent(html, EDS, TODAY, GEN)
G.assert_ledger_identity(html, TODAY, ED)
X.assert_not_parent_identity(html, PARENT_ED, PARENT_DATE)
n_sec = X.assert_structure(html, expect_sections=15)
n_tbl = G.assert_table_shape(html)
n_cit = G.assert_page_link_coverage(html)
assert html.count("</html>") == 1 and html.count("</body>") == 1, "closing tags"
print("guards: structure=%d sections  tables=%d  cited units=%d, zero uncited" % (n_sec, n_tbl, n_cit))
out = os.path.join(SP, "../../lens/oracle-lens-099.html")
open(out, "w", encoding="utf-8").write(html)
raw = open(os.path.join(SP, "../../lens/index.html"), encoding="utf-8").read()
print("WROTE %s  %d bytes (parent %d, delta %+d)" % (out, len(html), len(raw), len(html) - len(raw)))
