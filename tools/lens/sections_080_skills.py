# -*- coding: utf-8 -*-
"""Edition 080 Skills Radar + Build Radar bodies -- THE QUARTERLY RE-RANK.

Sticky rule: bets and their "do this quarter" text reproduce verbatim from the
prior edition EXCEPT at a quarterly review, which is what today is. Only the
evidence lines refresh daily. Every factual unit carries a citation inline as it
is emitted (the 09-15 mechanism), never retrofitted.
"""
import os as _os
# Resolve sibling modules relative to THIS file so a future run can import these
# from tools/lens/ instead of from one session's dead scratchpad. The original
# build ran with absolute scratchpad paths; that is what made edition 079's
# sections_079.py unusable as anything but a transcript.
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_SP = _os.environ.get("LENS_SCRATCH", _HERE)
import sys
sys.path.insert(0, _os.path.join(_HERE))
from lens_links import cite

TODAY = "2026-10-01"
A = lambda: cite(None, TODAY)          # dated public-archive fallback

def _bet(title, chip, why, do, ev):
    return ('<div class="card"><div class="cardh"><b>%s</b> <span class="chip %s">%s</span></div>'
            '<p class="why"><b>Why now.</b> %s</p>'
            '<div class="dothis"><b>Do this quarter.</b> %s</div>'
            '<p class="ev"><b>Evidence this run.</b> %s</p></div>') % (
            title, chip.split()[0], chip, why, do, ev)

RERANK_NOTE = (
 '<div class="rerank"><b>QUARTERLY RE-RANK &mdash; executed 2026-10-01, the review date this radar '
 'has carried since edition 001.</b> It had been flagged as approaching for eight consecutive '
 'editions and is done. Derived from <b>84 ledgers</b> (2026-07-08 &rarr; 2026-09-30), normalised '
 'per ledger-day because July is a partial month (23 ledgers against 31 and 30) &mdash; raw '
 'July&rarr;September ratios are inflated about 1.30&times; uniformly and must not be compared '
 'across themes without that correction. %s'
 '<table class="tbl"><thead><tr><th>Theme</th><th>Jul/day</th><th>Aug/day</th><th>Sep/day</th>'
 '<th>Growth</th></tr></thead><tbody>'
 '<tr><td>ai-workload-perf</td><td>7.0</td><td>20.7</td><td>37.3</td><td>5.37&times;</td></tr>'
 '<tr><td>claim-forensics</td><td>6.3</td><td>12.7</td><td>25.8</td><td>4.07&times;</td></tr>'
 '<tr><td>linux-io-observability</td><td>2.2</td><td>3.7</td><td>8.2</td><td>3.70&times;</td></tr>'
 '<tr><td>agent-operable-mcp</td><td>11.9</td><td>21.9</td><td><b>41.8</b></td><td>3.52&times;</td></tr>'
 '<tr><td>open-format-internals</td><td>18.7</td><td>37.5</td><td><b>63.8</b></td><td>3.40&times;</td></tr>'
 '<tr><td>memory-economics</td><td>5.0</td><td>9.0</td><td>13.0</td><td><b>2.60&times;</b></td></tr>'
 '</tbody></table>'
 '<p><b>One correction to our own prep, stated because it changed the outcome.</b> The 09-30 note '
 'annotated <code>agent-operable-mcp</code> as &ldquo;steepest climb&rdquo;. On its own table '
 '<code>ai-workload-perf</code> (6.31&times;) and <code>claim-forensics</code> (5.59&times;) were '
 'both steeper &mdash; the marker sat on the row with the second-highest TOTAL, not the steepest '
 'climb. Both steeper bets were already compounding, so the promotion survives; the stated reason '
 'did not. %s</p>'
 '<p><b>Outcome: zero retired, one added, one promoted, one held against the prep note\'s '
 'recommendation.</b> Seven bets, the top of the documented 5&ndash;7 range, split 4 compounding / '
 '2 emerging / 1 hedge. <b>Next review 2027-01-01.</b></p></div>') % (A(), A())

ORACLE_SKILLS = RERANK_NOTE + "".join([
 _bet("1. AI-workload performance engineering", "compounding compounding",
   "Steepest normalised curve on the board at 5.37&times; and 37.3 items/ledger-day in September.",
   "Unchanged. Own the inference-serving cost model end to end: tokens/sec per dollar, KV-cache "
   "residency, batching and P/D disaggregation, and be the person who can say which of those a "
   "given workload is actually bound by.",
   "MLPerf Inference v6.1 landed with a record 30 submitters and added an <b>end-to-end RAG</b> "
   "benchmark plus permitted speculative decoding in interactive scenarios &mdash; the first "
   "comparable public harness for the pipeline most people actually serve, rather than one model "
   "forward pass. " + A()),
 _bet("2. Claim forensics / reproducible benchmarking", "compounding compounding",
   "4.07&times; and 25.8/day, and it earned its keep three separate times this run.",
   "Unchanged. For every vendor number, reconstruct the workload, the hardware, the scale factor "
   "and who ran it, before arguing about the result.",
   "Three in one day: StarTree's 125k-QPS headline is <b>one TPC-H query on a 200&nbsp;MB table "
   "across 150 servers</b>, with the ClickHouse comparison <i>estimated by StarTree</i> from "
   "published charts; Fabric's GPU-acceleration &ldquo;up to 7&times;&rdquo; is a <b>100&nbsp;GB, "
   "22-query</b> workload against unnamed competitors; and a Tencent TPC-DS 100&nbsp;TB result is "
   "still marked <b>&ldquo;Result In Review&rdquo;</b> with a Report Date and a System Availability "
   "Date two months apart. Meanwhile <b>nothing at all</b> was submitted to TPC-H, TPC-C, TPC-E or "
   "any TPCx suite in the window. " + A()),
 _bet("3. Open-format internals as a tuning surface", "compounding compounding",
   "Highest absolute volume on the board, 63.8 items/ledger-day in September.",
   "Unchanged. Read the specs, not the vendor summaries: manifest scaling, deletion vectors, "
   "VARIANT shredding, and which engine writes what.",
   "Iceberg <b>1.12.0 shipped 2026-09-30</b> carrying the first real V4 machinery (V4 manifest "
   "reader and writer, relative paths, content stats) and <b>removing Spark 3.4</b> &mdash; while "
   "<code>iceberg.apache.org/releases/</code> still advertises 1.11.0. The equality-delete question "
   "settled too: the spec now says <b>prohibited</b> in V4, PR #17783 merged 09-29, and V4 itself "
   "still has no adoption date. " + A()),
 _bet("4. Agent-operable tooling &mdash; MCP over your own diagnostic method",
   "compounding compounding &mdash; PROMOTED from emerging",
   "<b>Promoted at this review.</b> Second-highest absolute volume on the whole board (41.8 "
   "items/ledger-day in September, 3.52&times;), and unlike memory economics the evidence is "
   "continuous and structural rather than episodic. A bet with the largest footprint on the board "
   "bar one is not &ldquo;emerging&rdquo; any more.",
   "Unchanged in substance, sharpened in urgency: encode your diagnostic method as MCP tools, and "
   "be the person in the room who can say what an agent is allowed to do to production and prove it.",
   "The strongest single day of evidence this bet has had. Every warehouse shipped a write-capable "
   "surface: BigQuery's MCP server is on <b>whenever the BigQuery API is</b>, with an unrestricted "
   "<code>execute_sql</code>; Dataform's can <code>push_git_commits</code> to your remote; DTS went "
   "GA with five mutating tools and a <code>service_account_name</code> parameter; Fabric's Core and "
   "IQ servers went GA beside a SQL DW operations skill; and <b>SQLcl 26.3's <code>skills sync</code> "
   "writes definitions into Claude, Codex AND Copilot directories in one command</b>. The only "
   "purpose-built lever is an IAM deny policy on <code>tool.isReadOnly</code> &mdash; and the "
   "previous lever, the <code>gcp.managed.allowedMCPServices</code> org policy, stopped working in "
   "March. " + A()),
 _bet("5. Memory economics / capacity planning 2.0",
   "emerging emerging &mdash; HELD, against our own prep note",
   "<b>Held at emerging deliberately.</b> Its normalised trend is the <b>weakest of all six</b> "
   "(2.60&times;, 13.0/day) and its evidence is episodic by nature &mdash; DRAM contract prices move "
   "quarterly, not daily. The decisive point is sharper than the trend: the two figures the 09-30 "
   "prep note cited to argue for promotion were <b>both withdrawn today</b>.",
   "Unchanged. Price memory per workload, not per server: DIMM count, CXL tiering, and what a "
   "capacity plan looks like when the memory line moves faster than the compute line.",
   "The lane corrected our own carried context twice. <b>&ldquo;$8,260 for a 64&nbsp;GB RDIMM&rdquo; "
   "does not reproduce</b> &mdash; the most recent dated quote is <b>$1,630</b> (2026-09-08), and the "
   "plausible explanation offered as hypothesis is a CNY quote read as USD. And "
   "<b>&ldquo;memory ~35% of server BOM&rdquo; is too LOW, not too high</b>: HPE's CEO puts DRAM and "
   "NAND together above <b>50%</b>. The underlying story is real and arguably stronger than we "
   "claimed &mdash; 4Q26 DRAM +10&ndash;15% QoQ, NAND +15&ndash;20%, enterprise SSD the only "
   "accelerating category, HPE cutting quote validity to <b>14 days</b> while reserving repricing "
   "rights &mdash; but a status change resting on two unverified numbers is not a status change. " + A()),
 _bet("6. Unpatchable-remediation triage", "emerging emerging &mdash; NEW at this review",
   "<b>Added at this review</b>, derived from the same 84 ledgers. Three facets of one skill: "
   "no-fix triage (1,010 items, 21.5/day in September, 4.67&times;), KEV delinquency (402 items, "
   "11.7/day, 10.38&times;) and scanner-blind advisories (285 items, 8.3/day, <b>38&times;</b> from "
   "a near-zero July base). The no-fix facet <i>alone</i> outranks two existing bets on volume, and "
   "nothing on the radar covered it.",
   "Build the decision procedure for when there is no patch: classify by mechanism (EOL branch, "
   "paywalled fix, abandoned project, pending-upstream, no identifier at all), then price the "
   "options &mdash; major upgrade, commercial support, network isolation, or removal. Learn to read "
   "a KEV entry's forensic-triage obligation as work rather than as a patch. And be able to say "
   "which of your gates reads advisory publication versus fix availability.",
   "This is the day the category stopped being a curiosity. <b>A fourth mechanism appeared:</b> "
   "Vercel cut one critical and one high from its September release as &ldquo;pending upstream "
   "coordination&rdquo;, so <b>no fix exists for anyone</b> including fully-patched users &mdash; and "
   "with no CVE id, no scanner and no SBOM query can find them. Alongside: Angular &le;19.2.25 went "
   "from two to <b>six</b> never-to-be-patched Highs, Spring's fix is verifiably absent from Maven "
   "Central below 7.0.9 while 7.0.9 is free, Apache Doris 2.x/3.x get no backport, and the "
   "<b>fifteen</b> containerd/BuildKit/Docker advisories carry CVE ids that return 404 from NVD, OSV "
   "<i>and</i> GitHub's own global database. " + A()),
 _bet("7. Modern Linux I/O &amp; observability", "hedge hedge",
   "Stays a hedge: thinnest by volume at 8.2 items/ledger-day, though growing at 3.70&times;, "
   "faster than three bets above it.",
   "Unchanged. Keep eBPF, io_uring and RDMA in working order as a diagnostic reach, not as a "
   "specialism.",
   "<b>The hedge is paying option value, for the second run running.</b> It produced the window's "
   "single most consequential finding again: <b>CVE-2026-97945</b>, x86 THP/MADV_FREE silently "
   "discarding dirty data under reclaim pressure, with <b>no fix on the 6.6.y LTS series</b> and "
   "Polars users already reporting lost production data. That is data loss, not exposure, and it is "
   "invisible to every layer above the kernel. " + A()),
]) + ('<p class="meta-move"><b>The standing meta-move.</b> One public post a month from this '
  'lens\'s own trend lines, public sources only. This month writes itself: the gap between a fix '
  'existing and you being able to get it or even see it, with the three measured scanner-blindness '
  'mechanisms as the spine. ' + A() + '</p>')

# ---------------- persona chairs: same re-rank DISCIPLINE, different board ----------------
SIM = ('<div class="simbanner"><b>SIMULATED CHAIR.</b> What a performance engineer sitting in this '
       'seat would plausibly bet on, derived from public sources only. Not this vendor\'s roadmap, '
       'not insider knowledge. The re-rank arithmetic below is the same 84-ledger derivation used '
       'for the Oracle chair. ' + A() + '</div>')

def _chair(bets, extra=""):
    return SIM + RERANK_NOTE + extra + "".join(_bet(*b) for b in bets)

SNOWFLAKE_SKILLS = _chair([
 ("1. Behavior-change-bundle forensics", "compounding compounding",
  "The single highest-leverage skill in this seat, and this month proves why: every warehouse "
  "behaviour change arrived through a <b>bundle</b>, not a feature announcement.",
  "Unchanged. Read every BCR before it enables, write the detection query, and keep a standing "
  "inventory of which bundle is Disabled / Enabled-by-Default / Generally Enabled in your account.",
  "A reader watching only the feature feed saw <b>no warehouse news at all</b> this month while "
  "their QAS defaults changed underneath them: bundle 2026_06 went Enabled-by-Default in 10.32 and "
  "turns Query Acceleration on for every new standard warehouse at <b>scale factor 8, up from "
  "2</b>, spending separately-metered serverless credits. In the same bundle "
  "<code>INTERVAL '3' days</code> stopped silently meaning three <i>seconds</i>. " + A()),
 ("2. Credit-cost attribution", "compounding compounding",
  "Defaults are now the cost surface, and three of them moved in one bundle.",
  "Unchanged. Own the per-query credit model: warehouse generation, QAS scale factor, serverless "
  "versus provisioned, and which of those your workload is actually paying for.",
  "QAS auto-on at SF8; <code>CORTEX_ENABLED_CROSS_REGION</code> defaulted on in weekly batches for "
  "accounts that never set it; Trust Center auto-enabling a <b>billable</b> AI scanner on Business "
  "Critical when it detects AI usage. None is a price change; each changes consumption if you do "
  "nothing. " + A()),
 ("3. Open-format internals", "compounding compounding",
  "Iceberg is now the storage contract, not an export format.",
  "Unchanged. Know what Snowflake-managed versus externally-managed Iceberg actually costs you in "
  "replication, and read the partition-evolution semantics before relying on them.",
  "Partition evolution for managed Iceberg went GA 09-18 with no data rewrite; Snowpipe Streaming "
  "into <b>partitioned</b> managed Iceberg went GA 09-24; and bundle 2026_05 made managed Iceberg "
  "tables <b>replicate by default</b> in failover groups &mdash; a storage-and-transfer cost you "
  "can no longer opt out of. " + A()),
 ("4. Agent-operable tooling", "compounding compounding &mdash; PROMOTED from emerging",
  "<b>Promoted at this review</b>, on the same board-wide evidence as the Oracle chair: 41.8 "
  "items/ledger-day in September, second-highest absolute volume.",
  "Encode the diagnostic method as tools, and own the question of what an agent may do to a "
  "warehouse holding production data.",
  "Cortex Agents gained temporary and <b>secure</b> agents plus <code>COPY GRANTS</code>; "
  "Restricted Session Scope went GA as a privilege <i>ceiling</i> that can never grant what the "
  "user lacks &mdash; which is the right shape, and rare. Against that, "
  "<code>CORTEX_MODELS_ALLOWLIST</code> stops controlling model access entirely and RBAC becomes "
  "the only mechanism. " + A()),
 ("5. Memory economics / capacity planning 2.0", "emerging emerging &mdash; HELD",
  "Held for the same measured reason as the Oracle chair: weakest normalised trend of the six at "
  "2.60&times;, and the two figures our own prep cited for promotion were withdrawn today.",
  "Price memory per workload. In this seat it lands as warehouse sizing and cache residency rather "
  "than DIMM counts.",
  "Indirect but real: 4Q26 server DRAM is undersupplied with contract prices up 10&ndash;15% QoQ, "
  "which is the input cost behind every credit you buy. " + A()),
 ("6. Unpatchable-remediation triage", "emerging emerging &mdash; NEW at this review",
  "<b>Added at this review.</b> In this seat the dominant facet is not EOL branches but "
  "<b>scanner blindness</b>, and this lane supplied the month's cleanest measurement of it.",
  "Track driver CVEs from the vendor's release notes, not from your scanner, and know which of your "
  "gates reads advisory publication versus fix availability.",
  "Measured, not asserted: all five Snowflake-CNA driver CVEs sit in OSV with <code>package: "
  "null</code>, GIT ranges only and no GHSA alias, so a package query for "
  "<code>snowflake-connector-python</code> returns 14 vulns and <b>not one of the September "
  "five</b>. The mechanism is proven rather than guessed &mdash; the OLDER Snowflake advisories do "
  "carry proper ecosystem ranges and were all re-stamped <code>modified: 2026-09-10</code>, i.e. "
  "enrichment arrives months late. Your scanner number will move with no change in your exposure. " + A()),
 ("7. Modern Linux I/O &amp; observability", "hedge hedge",
  "Stays a hedge; thinnest by volume and furthest from a managed-warehouse seat.",
  "Keep it as diagnostic reach, not a specialism.",
  "No direct signal in this seat this run; the kernel THP data-loss bug lands on self-managed hosts, "
  "not on Snowflake compute. Saying so rather than inventing an echo. " + A()),
])

DATABRICKS_SKILLS = _chair([
 ("1. AI-workload performance engineering", "compounding compounding",
  "Steepest normalised curve on the board (5.37&times;) and the closest fit to this seat of any bet.",
  "Unchanged. Own serving cost end to end across Model Serving and the agent stack.",
  "The lane's two cutovers are both agent-platform lifecycle: the Agent Bricks <b>Supervisor API</b> "
  "reached EOL 09-30 and migration is a <b>rewrite</b> &mdash; you now write the agent loop "
  "yourself in <code>agent.py</code> on Databricks Apps, losing managed tool execution, background "
  "mode and MCP approval gating. " + A()),
 ("2. Claim forensics / reproducible benchmarking", "compounding compounding",
  "4.07&times;, and this seat's own benchmarks are the ones most often quoted without methodology.",
  "Unchanged. Never cite a Photon or DBR number without naming the cluster, the data and who ran it.",
  "A quiet month for this lane's own claims, which is itself worth recording rather than padding. "
  "The transferable finding came from elsewhere: nothing was submitted to any audited TPC suite in "
  "the window, so there is no neutral price-normalised reference for a 2026 engine comparison. " + A()),
 ("3. Open-format internals", "compounding compounding",
  "Highest absolute volume on the board at 63.8/day.",
  "Unchanged. Delta protocol and Iceberg interop are the same job now; read both specs.",
  "Delta accepted the <b>Materialize Partition Columns</b> RFC on 09-30, letting partition columns "
  "live in the data files rather than only in the path &mdash; directly relevant to engines that "
  "choke on Hive-style virtual partition columns. Delta Lake 4.4.1 shipped 09-29. " + A()),
 ("4. Agent-operable tooling", "compounding compounding &mdash; PROMOTED from emerging",
  "<b>Promoted at this review</b> on the board-wide measurement; in this seat the governance half "
  "is further along than most, which makes the gap elsewhere more visible.",
  "Own what an agent may do to a lakehouse, and make the securable boundary explicit.",
  "UC Skills as a securable governed by VOLUME privileges is the better-shaped answer on the "
  "board &mdash; compare it with BigQuery's <code>execute_sql</code> being on whenever the API is. "
  "The Supervisor API retirement also moves the agent loop into your code, which moves the audit "
  "surface with it. " + A()),
 ("5. Memory economics / capacity planning 2.0", "emerging emerging &mdash; HELD",
  "Held on the measured trend, same as every chair.",
  "Price memory per workload; in this seat that is executor sizing and cache residency.",
  "Indirect: the DRAM and NAND step feeds DBU pricing from underneath. The direct evidence this "
  "quarter was withdrawn, as the Oracle chair records. " + A()),
 ("6. Unpatchable-remediation triage", "emerging emerging &mdash; NEW at this review",
  "<b>Added at this review.</b> In this seat the facet that bites is the <b>EOL-branch</b> one, "
  "because a lakehouse estate carries a long tail of pinned runtimes.",
  "Classify by mechanism before pricing the fix, and treat a major-version upgrade as a project.",
  "The lane returned a measured negative on its own CVEs &mdash; OSV empty for the Databricks and "
  "Delta packages, no Azure Databricks entry in the September MSRC document &mdash; which is the "
  "right result to report rather than pad. The category's evidence came from its neighbours: "
  "Angular, Spring, Doris, Starlette and the fifteen unindexed container advisories. " + A()),
 ("7. Modern Linux I/O &amp; observability", "hedge hedge",
  "Stays a hedge.",
  "Diagnostic reach only.",
  "No direct signal in this seat this run. " + A()),
])

BIGQUERY_SKILLS = _chair([
 ("1. Slot economics and the cost model", "compounding compounding",
  "The defining skill in this seat &mdash; and this month it had nothing to chew on, which is the "
  "finding.",
  "Unchanged. Own the slot model: reservations, autoscaling, on-demand versus capacity, and "
  "bytes-scanned versus slot-hours.",
  "<b>Measured negative, quantified.</b> Across 22 release-note entries in the window, keyword "
  "counts of <b>zero</b> for slot, autoscal, quota, pricing, BI&nbsp;Engine, materialized, vector, "
  "TreeAH, partition, cluster and Omni. A whole month with no engine or cost-model change, while "
  "the surface that <i>writes</i> to the warehouse grew four MCP servers. " + A()),
 ("2. Claim forensics / reproducible benchmarking", "compounding compounding",
  "4.07&times; board-wide.",
  "Unchanged. Reconstruct the workload before arguing about the number.",
  "Cross-cloud caching's claim is the one to test in this seat: 94.8% cache hit rate on follow-on "
  "queries, transfer under 5% of logical bytes. The right measurement is the <b>second</b> query "
  "and bytes transferred &mdash; a cold-cache single shot shows nothing, and the cache storage cost "
  "is not stated on the page. " + A()),
 ("3. Open-format internals", "compounding compounding",
  "Highest absolute volume on the board.",
  "Unchanged. BigLake managed tables and Iceberg read/write are the storage contract.",
  "Continuous queries can now write straight into <b>Iceberg managed tables</b> (GA 09-28) with no "
  "intermediate native hop, and <code>OBJ.LIST</code> went GA without needing a persistent object "
  "table. " + A()),
 ("4. Agent-operable tooling", "compounding compounding &mdash; PROMOTED from emerging",
  "<b>Promoted at this review</b>, and this seat supplies the starkest evidence on the board.",
  "Write the deny policy before anyone asks for an agent, then grant read-write back per tool to "
  "named principals.",
  "Four reachable MCP servers now expose, between them, arbitrary SQL including DDL, transfer "
  "configs that can name a service account, <b>Git pushes to your own repositories</b>, and the "
  "full <code>bq</code> CLI including reservation management. All execute as the calling principal "
  "&mdash; which is the right design &mdash; but the only purpose-built lever is an IAM deny policy "
  "on <code>tool.isReadOnly</code>, and the previous lever "
  "(<code>gcp.managed.allowedMCPServices</code>) <b>stopped working in March, before the servers "
  "shipped</b>. <code>tools/list</code> needs no authentication at all. " + A()),
 ("5. Memory economics / capacity planning 2.0", "emerging emerging &mdash; HELD",
  "Held on the measured trend.",
  "Price memory per workload; here that is slot-memory pressure and shuffle spill.",
  "No direct in-seat signal; the DdRAM step is an input cost one layer down. " + A()),
 ("6. Unpatchable-remediation triage", "emerging emerging &mdash; NEW at this review",
  "<b>Added at this review.</b> This seat's facet is the mirror image of everyone else's: fixes "
  "arrive <b>server-side with no customer action</b>, so the skill is knowing when NOT to act.",
  "Learn to read a vendor bulletin's customer-action field as authoritative, and to decline a "
  "Critical with a straight face when the remedy has already been applied for you.",
  "The lane's only Critical (GCP-2026-056 / CVE-2026-12717) was <b>patched server-side on "
  "2026-05-01</b> with &ldquo;no customer action is required&rdquo; &mdash; 153 days before today "
  "&mdash; and it is absent from KEV. Correctly declined for the fourth consecutive edition. " + A()),
 ("7. Modern Linux I/O &amp; observability", "hedge hedge",
  "Stays a hedge, and is furthest from this seat of any chair.",
  "Diagnostic reach only.",
  "No direct signal. " + A()),
])
