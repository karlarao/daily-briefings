# -*- coding: utf-8 -*-
"""Edition 080 Build Radar bodies, all four chairs. Quarterly re-rank applied:
zero retired, zero added, ONE sharpened. Statuses unchanged -- a re-rank that
changes nothing is a legitimate outcome and is stated as one."""
import os as _os
# Resolve sibling modules relative to THIS file so a future run can import these
# from tools/lens/ instead of from one session's dead scratchpad. The original
# build ran with absolute scratchpad paths; that is what made edition 079's
# sections_079.py unusable as anything but a transcript.
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_SP = _os.environ.get("LENS_SCRATCH", _HERE)
import sys
sys.path.insert(0, _HERE)
sys.path.insert(0, _os.path.join(_HERE))
from lens_links import cite
TODAY = "2026-10-01"
A = lambda: cite(None, TODAY)

BOUNDARY = ('<div class="boundary"><b>HARD BOUNDARY.</b> This is an outside-in thesis built from '
 'public signals only, for internal conversations. Actual roadmap knowledge must never be written '
 'into it &mdash; that boundary is what keeps this artifact clean. ' + A() + '</div>')

RR = ('<div class="rerank"><b>QUARTERLY RE-RANK &mdash; 2026-10-01.</b> Re-derived from the same 84 '
 'ledgers as the Skills Radar. Outcome: <b>zero bets retired, zero added, statuses unchanged, one '
 'sharpened.</b> A re-rank that changes little is a real outcome and worth saying plainly rather '
 'than manufacturing churn to look diligent &mdash; the rule permits replacing up to two bets, it '
 'does not require it. The one change: <code>ru-manifests-audited-tpc</code> gains a second leg '
 'from the measured scanner-blindness trend (285 ledger items, 38&times; growth from a near-zero '
 'July base). <b>Next review 2027-01-01.</b> ' + A() + '</div>')

def bet(t, chip, why, what, ev):
    return ('<div class="card"><div class="cardh"><b>%s</b> <span class="chip %s">%s</span></div>'
            '<p class="why"><b>Why us / why now.</b> %s</p>'
            '<div class="dothis"><b>What to build.</b> %s</div>'
            '<p class="ev"><b>Evidence this run.</b> %s</p></div>') % (t, chip.split()[0], chip, why, what, ev)

SIM = ('<div class="simbanner"><b>SIMULATED CHAIR.</b> Outside-in product theses a strategist in '
       'this seat could defend from public sources. Not this vendor\'s roadmap. ' + A() + '</div>')

ORACLE_BUILD = BOUNDARY + RR + "".join([
 bet("1. Self-explaining closed-loop performance automation", "white-space white-space",
  "Still nobody's. The whole industry shipped observability this month and none of it explains itself.",
  "Unchanged. Automation that states what it changed, why, and what it expects to happen &mdash; "
  "and that can be argued with.",
  "Fabric shipped Dynamic Tables Insights and an &ldquo;Analyze with CoCo&rdquo; button emitting "
  "ready-to-apply DDL; Redshift shipped auto-vacuum fixes; OCI gained SQL-profile lifecycle control. "
  "All of them tell you <i>what</i>; none tells you <i>why</i> in a form you can dispute. " + A()),
 bet("2. Memory-tiering economics as a product line", "white-space white-space",
  "The cost curve finally makes the argument for us: DRAM+NAND now exceed <b>50%</b> of a "
  "traditional server's BOM and 4Q26 contract prices are up 10&ndash;20% QoQ.",
  "Unchanged. Sell the tier, not the DIMM: measured placement with a published cost model.",
  "Two vendors shipped the <i>hardware</i> half of this thesis as an explicitly <b>cost</b> pitch "
  "rather than a capacity one &mdash; Astera's Leo 2 reclaims retired <b>DDR4</b> behind CXL 3.2 at "
  "768&nbsp;GB per expander, and Kioxia showed a 512&nbsp;GB CXL <b>flash</b> device at 755&nbsp;ns "
  "for cold pages. Nobody is selling the placement decision. " + A()),
 bet("3. Agent-native, security-hardened MCP surface", "white-space white-space",
  "<b>Highest-conviction bet on this board after this quarter</b>, and still white-space precisely "
  "because every vendor shipped the capability and none shipped the hardening.",
  "Unchanged. A write-capable agent surface with per-tool privilege, per-statement audit, and a "
  "read-only mode that is the default rather than a second tool name.",
  "The evidence is now overwhelming and it cuts our way. BigQuery's <code>execute_sql</code> is on "
  "whenever the API is; Dataform's agent can push Git commits; the <code>bq</code> CLI including "
  "reservation management is reachable; <code>tools/list</code> needs no auth. Of <b>104 MCP CVEs "
  "published in September, three are CVSS 10.0</b>, and the dominant class is a server bound to "
  "0.0.0.0 with no auth and no Host/Origin check. The sharpest datapoint of all: <b>the window's "
  "worst unfixed data-layer vulnerability is itself in a Postgres MCP server</b> "
  "(CVE-2026-85620, CVSS 9.2, fix only an open PR). " + A()),
 bet("4. Open catalog + external-engine writes", "parity-play parity-play",
  "Rivals are competing on each other's catalog endpoints as first-class connection types now.",
  "Unchanged. Credential-vended, policy-enforced external writes against our tables.",
  "SageMaker Unified Studio added generic Iceberg REST connections naming <b>Snowflake Open Catalog "
  "and Databricks Unity Catalog</b> as supported types; ClickHouse now writes Iceberg into OneLake "
  "at GA; Fabric federated its catalog to AWS Glue. The REST spec's own centre of gravity moved "
  "this month from credential vending to <b>authorization</b> &mdash; finer-grained read "
  "restrictions, file-level delegation, encryption key metadata. " + A()),
 bet("5. Per-GB serverless streaming ingest", "parity-play parity-play",
  "Every competitor now bills streaming ingest by volume with no cluster to size.",
  "Unchanged. Per-GB ingest with no provisioned pipeline.",
  "Snowpipe Streaming Elastic Channels went GA with one implicit server-scaled path per pipe; "
  "Fabric previewed on-demand billing per category with <b>no smoothing</b> and a zero-provisioned "
  "F0 SKU. The direction is unambiguous. " + A()),
 bet("6. RU change manifests + a current audited TPC &mdash; and now fix-availability manifests",
  "trust-play trust-play &mdash; SHARPENED at this review",
  "<b>Sharpened.</b> The original thesis was credibility through published change manifests and a "
  "current audited benchmark. This quarter handed it a second, stronger leg: the industry's "
  "vulnerability metadata is measurably broken in <b>both</b> directions, and a vendor that "
  "published machine-readable fix-availability would be solving a problem its customers can now "
  "name.",
  "Unchanged on the original two. <b>Added:</b> a per-RU machine-readable manifest of which CVEs a "
  "patch actually carries, so a customer's scanner can distinguish &ldquo;fixed&rdquo; from "
  "&ldquo;advisory published&rdquo;. The gap is documented, not hypothetical.",
  "Three measurements, one direction. <b>Fifteen</b> September advisories across containerd, "
  "BuildKit and Docker Engine carry CVE ids in the vendors' own notes and return <b>404 from NVD, "
  "OSV and GitHub's global Advisory Database</b> &mdash; proven to be the promotion step, because "
  "promoted siblings from the same projects resolve normally. Five Snowflake driver CVEs are filed "
  "with <code>package: null</code> so no lockfile query finds them. And some fixes carry no id at "
  "all: Redis fixed an ACL bypass and an unauthenticated cluster bus with zero CVEs. "
  "<b>Our own side is the proof the thesis is needed:</b> this run's Oracle lane had to grep five "
  "advisories by hand to establish that CVE-2026-21962's fix ships only in cpujan2026 and is absent "
  "from the June, July, August and September drops &mdash; so an estate current on monthly CSPUs is "
  "still exposed, and nothing published says so. " + A()),
]) + ('<p class="meta-move"><b>Retirement rule.</b> A bet retires when Oracle publicly ships it '
      '(noted in Since-yesterday, gap closes in the Gap Ledger) or the market invalidates it. '
      'Nothing retired at this review. ' + A() + '</p>')

def _persona(seat, bets):
    return SIM + RR + "".join(bet(*b) for b in bets)

SNOWFLAKE_BUILD = _persona("snowflake", [
 bet.__self__ if False else ("1. Bundle-impact simulation as a product", "white-space white-space",
  "The bundle mechanism is this vendor's biggest operational liability and nobody sells the fix.",
  "A dry-run that replays your own query history against a pending bundle and reports which "
  "statements change results, not just which features changed.",
  "BCR-2287 ships a <code>QUERY_HISTORY</code> detection query by hand, which is the manual version "
  "of exactly this. And the need is proven: semantic-view FACTS+DIMENSIONS queries had been "
  "returning <i>arbitrarily chosen</i> fact values per dimension group, so customers were "
  "&ldquo;making decisions based on unreliable data without realizing it&rdquo;. " + A()),
 ("2. Credit-cost pre-flight", "white-space white-space",
  "Defaults became the cost surface this month and there is no estimator.",
  "A per-query credit estimate before execution, including serverless QAS spend.",
  "QAS auto-on at SF8 across every new standard warehouse, cross-region inference defaulted on in "
  "weekly batches, and a billable AI scanner auto-enabling on AI usage. CloudWatch shipped the "
  "analogous control for Logs Insights (estimate bytes scanned <i>before</i> you run) &mdash; proof "
  "the primitive is buildable. " + A()),
 ("3. Governed agent surface", "white-space white-space",
  "Same board-wide gap as every chair, and this seat is further along than most.",
  "Per-tool privilege with a default-deny read-only mode.",
  "Restricted Session Scope as a privilege <b>ceiling</b> that intersects RBAC and can never grant "
  "what the user lacks is the best-shaped primitive on the board this month. " + A()),
 ("4. Neutral REST catalog", "parity-play parity-play",
  "Open Catalog has published nothing for a year while Horizon takes the Iceberg governance work.",
  "Either invest in the neutral catalog or say plainly that Horizon is the answer.",
  "Open Catalog's release-notes page is still topped by 2025-09-29, while Horizon gained the "
  "<b>Iceberg Scan Plan API</b> in preview so external engines hit data-protection policies rather "
  "than bypassing them, and Catalog Explorer became the default Snowsight browser. " + A()),
 ("5. Per-GB streaming ingest", "parity-play parity-play",
  "Already largely delivered in this seat.",
  "Keep Elastic Channels honest about the ordered/exactly-once tradeoff.",
  "Elastic Channels GA, at-least-once with per-append durable acks &mdash; and <b>Named Channels "
  "remain the only route for ordered exactly-once</b>, which the docs say plainly. That is the "
  "right disclosure. " + A()),
 ("6. Driver CVE manifests", "trust-play trust-play &mdash; SHARPENED",
  "<b>Sharpened on this seat's own worst finding.</b>",
  "Publish machine-readable affected/fixed ranges in a form OSV can ingest, with a GHSA alias.",
  "Five CVEs filed with <code>package: null</code> and GIT ranges only means pip-audit, Dependabot "
  "and osv-scanner report <b>clean against a vulnerable fleet</b> &mdash; and the minimum supported "
  "Python connector (3.12.3) sits <i>below</i> the version that fixes a CVSS 9.2 "
  "hostname-verification bypass. The support floor is beneath the security floor. " + A()),
])

DATABRICKS_BUILD = _persona("databricks", [
 ("1. Self-explaining optimization", "white-space white-space",
  "Predictive Optimization decides; it does not explain.",
  "Emit the reasoning and the expected delta, and let an engineer dispute it.",
  "A quiet month in this seat for optimizer work, stated rather than padded. " + A()),
 ("2. Lifecycle contracts for agent platforms", "white-space white-space",
  "<b>This seat just demonstrated the gap itself.</b>",
  "A deprecation path for a managed agent loop that is a migration, not a rewrite.",
  "The Agent Bricks <b>Supervisor API</b> reached EOL 09-30 and the migration is a rewrite: you "
  "re-implement the loop, background mode and MCP approval gating yourself. The naming trap is the "
  "tell &mdash; the declarative Supervisor <i>Agent</i> is NOT retiring, only the <i>API</i>, and a "
  "reader who misses that panics about the wrong product. " + A()),
 ("3. Governed agent surface", "white-space white-space",
  "Board-wide gap; this seat has the best primitive and should press it.",
  "Per-tool privilege on a securable boundary.",
  "UC Skills as a securable governed by VOLUME privileges is the right shape, and stands out against "
  "BigQuery's always-on <code>execute_sql</code>. " + A()),
 ("4. Open catalog + external writes", "parity-play parity-play",
  "Unity Catalog is now a connection type in a competitor's product.",
  "Credential-vended external writes with policy enforcement.",
  "SageMaker Unified Studio names Unity Catalog as a supported IRC type; Fabric supports Azure "
  "Databricks native storage in OneLake in production. " + A()),
 ("5. Per-GB streaming ingest", "parity-play parity-play",
  "Lakeflow is close; the billing story is not per-GB.",
  "Per-GB ingest with no provisioned pipeline.",
  "No in-window movement on the billing model. " + A()),
 ("6. Runtime change manifests", "trust-play trust-play &mdash; SHARPENED",
  "<b>Sharpened on the board-wide metadata failure.</b>",
  "Machine-readable per-DBR manifests of what changed and which CVEs are carried.",
  "This lane returned a clean measured negative on its own CVEs &mdash; OSV empty, no MSRC entry. "
  "The need is demonstrated next door: <b>auto-optimized shuffle v2 is on by default in DBR 19 with "
  "no supporting documentation anywhere</b>, which is precisely the class a manifest would surface. " + A()),
])

BIGQUERY_BUILD = _persona("bigquery", [
 ("1. Self-explaining slot allocation", "white-space white-space",
  "Autoscaling decides and reports nothing you can argue with.",
  "Explain the slot decision per query with the counterfactual.",
  "<b>MERGE, UPDATE, DELETE and EXPORT execution steps became visible in query plans on 09-30</b> "
  "&mdash; genuinely the most useful change in the month for anyone tuning DML, because upsert "
  "plans were previously opaque. That is a step toward this bet, from the right direction. " + A()),
 ("2. Cost pre-flight", "white-space white-space",
  "Bytes-scanned billing with no estimate is the oldest complaint in this seat.",
  "A pre-execution cost estimate that is binding.",
  "<b>The sibling service just shipped it:</b> CloudWatch Logs Insights can now estimate bytes "
  "scanned before you run a query. The primitive exists one product away. " + A()),
 ("3. Governed agent surface", "white-space white-space",
  "<b>This seat has the widest gap on the entire board and should be most uncomfortable about it.</b>",
  "Default-deny, per-tool privilege, a real read-only mode, and an approval prompt for mutations.",
  "Four MCP servers exposing arbitrary SQL including DDL, service-account-naming transfer configs, "
  "Git pushes and the full <code>bq</code> CLI with reservation management. The server is enabled "
  "<b>whenever the BigQuery API is</b>. The one org-policy control "
  "(<code>gcp.managed.allowedMCPServices</code>) <b>stopped working in March, before the servers "
  "shipped</b>, leaving IAM deny policies as the only lever &mdash; and <code>tools/list</code> "
  "requires no authentication at all. " + A()),
 ("4. Open catalog + external writes", "parity-play parity-play",
  "BigLake is the asset; the catalog war is being fought on endpoints.",
  "Full external-engine writes against BigLake managed tables.",
  "Continuous queries now write into Iceberg managed tables at GA; cross-cloud caching reads "
  "Iceberg behind Unity Catalog, Glue and Snowflake Horizon. " + A()),
 ("5. Per-GB streaming ingest", "parity-play parity-play",
  "Storage Write API is strong; continuous queries are not per-GB.",
  "Per-GB continuous ingest without a reservation.",
  "Stateful continuous queries need an Enterprise reservation with a <code>CONTINUOUS</code> "
  "assignment and clear a <b>10-slot admission threshold per job</b> &mdash; the opposite of "
  "serverless per-GB. " + A()),
 ("6. Fix-availability manifests", "trust-play trust-play &mdash; SHARPENED",
  "<b>Sharpened.</b> This seat is the one vendor that can credibly claim the server-side-fix model, "
  "and it should publish the evidence rather than ask for trust.",
  "Machine-readable &ldquo;no customer action required, patched on DATE&rdquo; attestations per "
  "service, consumable by a scanner.",
  "Its only Critical was patched server-side on 2026-05-01 with no customer action &mdash; a genuinely "
  "better outcome than every other chair's, and one no scanner can see. That asymmetry is the "
  "product opportunity. " + A()),
])
