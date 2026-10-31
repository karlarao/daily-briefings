#!/usr/bin/env python3
"""Edition 108 ledger corrections, applied BEFORE any section is generated.

The 2026-10-14 build-order rule: a wrong date defeats every date-keyed check
downstream, and editing the assembled HTML leaves rendered tables generated
from the pre-fix ledger. So corrections land on the ledger first.

Every correction below was raised by a research agent against a primary source
today. Two of them correct MY OWN PROMPT rather than the board (the 10-29
lesson) and are marked so -- the board was already right and is left alone.
"""
import json, os, sys, re
SP = os.path.dirname(os.path.abspath(__file__))
led = json.load(open(os.path.join(SP, "parent_ledger.json")))

def row(sec, key):
    for r in led[sec]:
        if r["k"] == key:
            return r
    raise SystemExit("MISSING %s/%s" % (sec, key))

applied, retired = [], []

# 1. DATE MOVED, stated by the vendor on its own page. Two lanes (Databricks and
#    AI App Dev) reached this independently from different docs.
r = row("events", "genie-mcp-beta-endpoint-sunset-oct31")
r["date"] = "2026-11-30"
r["t"] = ("CORRECTED 10-30 <b>The date moved and Databricks says so explicitly.</b> The Beta endpoint "
          "<code>/api/2.0/mcp/genie</code> now reaches end of life <b>2026-11-30</b>, not 10-31 &mdash; the "
          "&ldquo;What&rsquo;s coming&rdquo; page (updated 2026-10-29) states &ldquo;The previous date was "
          "October 31&rdquo;; the 10-31 figure came from the superseded 2026-09-25 release note. Two lanes "
          "reached this independently. <b>A carried urgent therefore retires for 30 days.</b> The migration "
          "substance the board already had is confirmed and is THREE edits, not a URL swap: the URL, the "
          "<code>ai-gateway</code> OAuth scope in place of <code>genie</code>, and an <code>EXECUTE</code> grant "
          "on <code>system.ai.genie_one_mcp</code> &mdash; the Unity Catalog grant is the one that breaks a "
          "service principal silently. Tool names and arguments are unchanged. The per-space "
          "<code>/api/2.0/mcp/genie/{space_id}</code> path is a SEPARATE server and is not covered.")
applied.append("genie-mcp: 2026-10-31 -> 2026-11-30 (vendor-stated move; carried urgent retires)")

# 2. A date this board asserted that the vendor does not publish. The row also
#    carried a Settings-API clause that appears nowhere in the source.
r = row("events", "databricks-partner-ai-settings-api-nov1")
r.pop("date", None)
r["t"] = ("CORRECTED 10-30 <b>The 2026-11-01 date was never published and is withdrawn; this row is now "
          "undated.</b> Databricks&rsquo; &ldquo;What&rsquo;s coming&rdquo; page (updated 2026-10-29) says the "
          "account- and workspace-level partner-powered-AI toggles are removed &ldquo;At a later date&rdquo; "
          "with no date, that <b>each workspace keeps its current value</b> so removal changes no setting, and "
          "that later changes go through your account team. The page does <b>not mention the Settings API at "
          "all</b> &mdash; that clause is withdrawn too. The 2026-09-08 release note likewise gives no date. "
          "Same class as the four fabricated dates in seven editions this board has already corrected.")
applied.append("databricks-partner-ai: 2026-11-01 -> UNDATED, Settings-API clause withdrawn")

# 3. Shipped, and nine days earlier than the board's placeholder.
r = row("events", "duckdb-20-ga-late-oct")
r["date"] = "2026-10-21"
r["t"] = ("DELIVERED 10-30 <b>DuckDB 2.0.0 LTS shipped 2026-10-21</b> &mdash; nine days before the board&rsquo;s "
          "&ldquo;late October (TBD)&rdquo; placeholder, built from ~20,000 commits since 1.5 and supported to "
          "2027-10-22. Full codename is <b>Cinnamon Teal</b> (the GitHub release titles it &ldquo;Cyanoptera&rdquo; "
          "&mdash; same bird). The release calendar is now concrete: 2.0.1 on 2026-11-18, feature freeze 11-04. "
          "The upgrade hazard is <b>one-way storage version 69</b>: a NEW file written by 2.0.0 cannot be read by "
          "pre-2.0 (which reads 64&ndash;68), while an EXISTING file keeps its version when 2.0.0 writes to it &mdash; "
          "so the trap is mixed-version fleets, not single upgrades. Six SILENT result changes ship with it "
          "(<code>~</code>/<code>!~</code> become PARTIAL matching, <code>//</code> and <code>%</code> by zero now "
          "raise, <code>MERGE INTO</code> errors on multiple matching source rows, and three more).")
applied.append("duckdb-20-ga: TBD/late-Oct -> DELIVERED 2026-10-21, storage-69 one-way noted")

# 4. A date no vendor confirms, with the vendor's own pricing contradicting it.
r = row("events", "openai-cursor-cutoff-nov12")
r["t"] = ("DISPUTED 10-30 <b>Kept on the board, but the date is unconfirmed and the vendor&rsquo;s own pricing "
          "cuts against it.</b> Cursor&rsquo;s <code>/docs/models</code> still lists the full OpenAI line today "
          "with <b>no removal notice and no deprecation date anywhere on the page</b>, and <b>GPT-5.6 Sol carries "
          "promotional pricing through 2026-11-21 &mdash; nine days PAST the alleged cutoff</b>, which is not how "
          "you price a model you are about to lose. Press reporting says the final date was never agreed between "
          "the parties. What IS verifiable: no GPT-6 model is listed at all, consistent with OpenAI&rsquo;s stated "
          "position, and <code>status.cursor.com</code> now 301-redirects to <code>status.x.ai</code>, so the "
          "acquisition has landed operationally. Treat 11-12 as unconfirmed and keep an API-key fallback.")
applied.append("openai-cursor-cutoff: date marked DISPUTED with the pricing contradiction recorded")

# 5. Right day in Beijing, wrong day for a UTC reader -- and the gap is 27 hours.
r = row("events", "deepseek-search-fetch-api-billing-nov1")
r["date"] = "2026-10-31"
r["t"] = ("CORRECTED 10-30 <b>Billing starts 2026-10-31 at 16:00 UTC, not 2026-11-01.</b> Both DeepSeek pages "
          "agree on the instant; 11-01 is correct in Beijing time (00:00, UTC+8), so a reader scheduling by UTC "
          "has about <b>27 hours, not two days</b>. Rate is <b>$0.75 per 1,000 calls per endpoint</b> for Search "
          "and Fetch. The free window specifically covered Search/Fetch calls made through server-side tools in "
          "<b>DeepSeek Harness, Claude Code and Codex</b> &mdash; so a retrieval loop wired up on the strength of "
          "it being free starts costing money tomorrow afternoon. A timezone is not a rounding error on a deadline.")
applied.append("deepseek-billing: 2026-11-01 -> 2026-10-31 16:00 UTC (timezone, ~27h not 2d)")

# 6. GitHub moved half of a double cutover. The board carried both on 11-02.
r = row("events", "gha-pull-request-target-off-nov2")
r["date"] = "2026-12-02"
r["t"] = ("CORRECTED 10-30 <b>Moved to 2026-12-02, so 2026-11-02 is a SINGLE cutover, not the double one this "
          "board carried.</b> GitHub&rsquo;s GA changelog carries an <b>editor&rsquo;s note dated 2026-10-21</b> "
          "changing the date. Enforcement blocks <code>pull_request_target</code> runs in <b>public</b> "
          "repositories with no applicable event policy that were on the default before GA &mdash; &ldquo;This "
          "default does not apply to private or internal repositories&rdquo; &mdash; and it starts in <b>evaluate "
          "mode</b>, so Insights shows what would be blocked before anything is. Secondary write-ups published in "
          "September still say November 2 and are stale. What remains on 11-02 is the macOS 14 runner-label "
          "retirement alone.")
applied.append("gha-pull_request_target: 2026-11-02 -> 2026-12-02 (editor's note; 11-02 is now single)")

# 7. Already past, and off by a month. Retire it.
r = row("events", "python-310-full-eol-oct31")
r["date"] = "2026-10-01"
r["t"] = ("CORRECTED 10-30 <b>Python 3.10 reached end of life 2026-10-01, not 2026-10-31 &mdash; it has been dead "
          "for 29 days.</b> python.org states it directly: 3.10.22 is the final release and the series &ldquo;will "
          "receive no further security updates&rdquo;; the devguide table carries a non-italic (actual, not "
          "scheduled) EOL of 2026-10-01. The 10-31 figure is the month-end convention Python uses elsewhere. "
          "The consequence is sharper than the date: the coordinated <b>2026-10-25</b> security release carrying "
          "the eMudhra CA block (CVE-2026-115557) and the <code>tarfile</code> link fix (CVE-2026-114583) went to "
          "3.11&ndash;3.15 and <b>NOT to 3.10</b>, so a 3.10 runtime still trusts the compromised intermediates "
          "with no upstream remedy. 3.10 is now the main generator of unreachable fixes in the AI stack: vLLM "
          "0.32.0, Langfuse 5.0 and httpx2 2.15.0 all require 3.11+.")
applied.append("python-310-eol: 2026-10-31 -> 2026-10-01 (29 days past; retires)")

# 8. Day count only -- but a day count that is quoted in prose has to be right.
r = row("patch", "cve-2026-21962-ohs-weblogic-kev")
r["due"] = ("KEV due 2026-08-27 (<b>64d PAST DUE</b>) &middot; fix exists since the January 2026 CPU")
r["t"] = (str(r.get("t", "")) +
          " <b>RE-MEASURED 10-30:</b> now <b>64 days</b> past its KEV due date, and grepped directly against the "
          "published October 2026 CPU text &mdash; the id appears <b>zero times</b>, a third consecutive quarterly "
          "CPU. The KEV entry carries <b>forensic-triage obligations under BOD 26-04</b>, not merely a patch "
          "requirement. <i>Note for the record: the board&rsquo;s component attribution was already correct "
          "(Oracle HTTP Server / WebLogic Server Proxy Plug-in, not RDBMS) &mdash; a prompt line claiming "
          "otherwise was my error, not the board&rsquo;s.</i>")
applied.append("cve-2026-21962: 63d -> 64d past due; component attribution confirmed already correct")

led["_corrections_108"] = applied
json.dump(led, open(os.path.join(SP, "ledger_108.json"), "w"), ensure_ascii=False)
print("corrections applied to the ledger BEFORE section generation:")
for a in applied:
    print("  -", a)
print("\nrows now past-dated (will retire from Event Horizon):")
for r in led["events"]:
    d = str(r.get("date") or "")
    if d and d < "2026-10-30":
        print("   ", d, r["k"])
