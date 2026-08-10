#!/usr/bin/env python3
"""Build Oracle Competitive Lens edition 030 from the prior edition's template.

Parent is edition 029 (2026-08-09), the real live artifact. An earlier attempt at
today's edition was authored against a stale cached copy of 028 (2026-08-08); the
LEDGER below is still that authoring pass, so MERGE_PARENT() reconciles it against
the real 029 ledger before the splice. See RECONCILE notes on that function.

POINT-IN-TIME RECORD — not a reusable entry point. Most of this file is edition
030's own content (the LEDGER dict and the section HTML), which is regenerated from
fresh research every run and is meaningless for any other date. It is committed as
the provenance of what actually produced the published edition 030, and as a worked
example of the splice/merge shape.

The reusable machinery was extracted to tools/lens/lens_guard.py after this build
ran; the guards here are the inline originals. A future edition should import
lens_guard rather than copy this file. Failure modes both exist to prevent:
docs/lens-build-failure-modes.md.

Expects, in its working directory: lens_prev.html (the parent edition, host wrapper
already stripped) and prev_sections/*.html extracted from it.
"""
import json, os, re

SP = os.path.dirname(os.path.abspath(__file__))
ED, DSLUG, GEN = "030", "2026-08-10", "2026-08-10 09:43 EDT"
PREV_ED, PREV_DSLUG = "029", "2026-08-09"

A = lambda u, t="[src]": f'<a href="{u}" target="_blank" rel="noopener">{t}</a>'
ARCH = lambda d: A(f"https://karlarao.github.io/daily-briefings/archive/{d}.html", f"archive {d[5:]}")

LEDGER = {
 "date": DSLUG, "edition": 30,
 "claims": [
  {"k":"snowflake-2026-06-bundle","v":"Snowflake","verdict":"vendor-run","t":"2026_06 still disabled-by-default; auto-enable 'a subsequent August release' with no published date. INTERVAL plural qualifiers change results (3 seconds to 3 days); QAS default-on at scale factor 8 on ALL standard warehouses; Cortex cross-region inference default flipped on for unconfigured accounts. Adaptive Compute GA on Azure+GCP with a ~30% cost claim measured Jul 23 build vs Jun 16 build, not vs Gen1/Gen2. Engine performance-improvements log empty three months running."},
  {"k":"databricks-dbr19-arrow-udf","v":"Databricks","verdict":"vendor-run","t":"DBR 19 GA on Spark 4.2.0; DBR 18 LTS to 2029-06-10. Arrow-optimized Python UDFs default-on with acknowledged type-coercion changes. MANAGE privilege no longer needs a usage privilege (previously-inert grants now live). Delta Sharing GA for deletion vectors/column mapping/Iceberg reads. Liquid-clustering-beats-Z-order framing contradicted by an independent 50M-row test where Z-order won multi-column filters."},
  {"k":"bigquery-project-caps-iceberg","v":"BigQuery","verdict":"vendor-run","t":"Per-project slot caps + concurrency governors (Preview) — documented as an APPROXIMATE cap. Iceberg managed tables GA for partitioning/multi-statement transactions/advanced runtime, but no MVs, no RLS, no CDC updates, no partition evolution, and ONE concurrent mutating DML per table. DTS billing label lowercases Aug 11. Storage Write API REST rebrand hides the pricier at-least-once path."},
  {"k":"fabric-onelake-tiers-nee","v":"Fabric","verdict":"vendor-run","t":"OneLake cool/cold tiers GA — storage $0.023 to $0.004/GB but a 1TB cold read costs 665,000 CU-seconds (~12% of an F64 day); 30/90-day minimum retention with early-deletion penalties. Spark NEE UDFs GA at 'up to 5.76x' — which is vectorized pandas UDFs only; scalar Python UDFs move 1.08x. Runtime 1.3 GA support ends Sep 30 with Runtime 2.0 still Preview: no GA successor."},
  {"k":"challengers-s3-auth-breaks","v":"Cloud DW Challengers","verdict":"vendor-run","t":"ClickHouse 26.7 and Trino 483 both removed implicit S3 credential resolution in the same window. StarRocks 3.5.20/4.0.13 fix WRONG RESULTS in MV rewrite, join reordering and sort elimination. DuckDB 1.5.5 patches multiple OOB reads with no CVE IDs assigned. DuckDB v2.0 async I/O claims 3x Parquet / 20x CSV on S3 (project-run)."},
  {"k":"dbhw-venice-dram","v":"Database Hardware","verdict":"audited","t":"AMD EPYC 'Venice' 9006: 256 Zen 6c cores, 16-channel DDR5, PCIe Gen6, ~1.6 TB/s theoretical peak — SP7 Q4 2026, mainstream SP8 not until H1 2027. All perf multipliers (3.4x vs Xeon, 70% vs Zen 5) are AMD-run with undisclosed configs. Server DRAM +13-18% QoQ in 3Q26, rising through 2H27, pushed onto buyers without LTAs. No new audited TPC-H in the window."},
  {"k":"mongodb-july-cve-batch","v":"MongoDB","verdict":"vendor-run","t":"26 CVEs patched Jul 22 (9.2 compute-mode heap corruption; 8.6 RBAC bypass) across 7.0.39/8.0.28/8.2.12/8.3.7. 8.2 hit EOL Jul 31 — 8.2.12 is terminal. 8.3 makes cost-based ranking the DEFAULT plan-selection mechanism. Percona PSMDB is ~3 weeks behind on the batch. 10-40% PGO/LTO gains are vendor-measured."},
  {"k":"aihw-helios-vs-rubin","v":"AI Hardware","verdict":"vendor-run","t":"AMD Helios/MI455X: 432GB HBM4, 20 PF FP8, ~$5-5.5M/rack vs ~$3.5-4M for Vera Rubin NVL72 — but SemiAnalysis rates the real throughput delta 'relatively mild' and notes no production WideEP at launch. Microsoft commits $5-10B. TileRT hits ~494 tok/s/user on stock B200 in SOFTWARE. Samsung HBM4 yield ~80%, first real dual-source relief."}
 ],
 "ownclaims": [
  {"k":"exadata-ai-smart-scan-topk","status":"verifiable","t":"Exadata 26ai AI Smart Scan + Adaptive Top-K — per-cell top-K cuts data shipped to DB nodes; still unpublished as a benchmark — cleanest go-first, carried"},
  {"k":"exascale-30x-vector","status":"exposed","t":"'30x faster AI vector searches' via Exadata AI Smart Scan (Exascale), Aug 5 blog — no methodology, no dataset, no baseline, no index type disclosed. Pure marketing multiplier in a window where every rival number is being audited"},
  {"k":"imtt-commit-cache-exadata","status":"verifiable","t":"In-Memory Transaction Table + Commit Cache on 26ai/Exadata — RDMA XID lookups replace consistent-read block transfers, attacking RAC hot blocks (unpublished) — go-first, carried"},
  {"k":"exadata-261-live-migration","status":"verifiable","t":"Exadata 26.1 RDMA-enabled VM live migration — move an active RAC VM between DB servers without downtime; genuinely new for maintenance planning, no published numbers"},
  {"k":"ai-vector-search-hnsw-dml","status":"verifiable","t":"AI Vector Search: HNSW takes transactional DML in 26ai with RAC-wide consistency — the 23ai no-DML blocker is fixed; go-first lane, carried"},
  {"k":"19c-tls13-pqc","status":"verifiable","t":"19.32 ships TLS 1.3 + ML-KEM/ML-DSA post-quantum and FIPS 140-3 on 19c — genuinely ahead of most rivals, but DEFAULT BEHAVIOR IS UNCHANGED and it needs an instance+listener restart; claim it as available, never as enabled"},
  {"k":"adbs-select-ai-a2a","status":"exposed","t":"Select AI Supervisor Agent + managed A2A server — real agent-native surface, but SERVERLESS ONLY: none of it appears on the Dedicated changelog, which got one governance feature in July and nothing in August"},
  {"k":"monthly-patching-vs-ru-stability","status":"landmine","t":"Oracle's CPU post tells customers to 'move immediately to a monthly security patching cycle' three months after Oracle PULLED RU 19.31 and put it on hold. Never lead with patch-cadence discipline; if raised, concede the tension and pivot to Update Advisor + backout tooling"},
  {"k":"adbs-iceberg-rest-catalog","status":"precision","t":"ADB Serverless Iceberg REST Catalog via DBMS_DCAT — read-side only. Gap #1 widened again this window: BigQuery Iceberg transactions GA, Snowflake Horizon converts Delta shares to Iceberg on ingest"}
 ],
 "benchmarks": [
  {"k":"tpch-30tb-hpe-jun2026","date":"2026-06-11","t":"TPC-H 30TB HPE ProLiant DL580 Gen12 / SQL Server 2025 — 2,946,259 QphH, $1,499.13/kQphH"},
  {"k":"tpch-3tb-alibaba-jun2026","date":"2026-06-29","t":"TPC-H 3TB Alibaba Cloud Hologres 4.1 — 8,443,627 QphH, CNY 390.47/kQphH"},
  {"k":"tpch-3tb-dell-jun2026","date":"2026-06-23","t":"TPC-H 3TB Dell PowerEdge R7715 / Exasol — 5,484,276 QphH, $60.45/kQphH"},
  {"k":"tpch-1tb-dell-jun2026","date":"2026-06-23","t":"TPC-H 1TB Dell PowerEdge R7715 / Exasol 2025.2.1 — 5,489,326 QphH, $25.01/kQphH"},
  {"k":"mlperf-training-v6","date":"2026-06-16","t":"MLPerf Training v6.0: adds 671B DeepSeek-V3 / GPT-OSS MoE; Blackwell sweeps, AMD within a few % — audited"},
  {"k":"mlperf-training-v6-lambda-gb300","date":"2026-07","t":"MLPerf Training v6.0: Lambda posts fastest GB300 NVL72 Llama-3.1-8B result — audited"},
  {"k":"mlperf-inference-v6","date":"2026-04-01","t":"MLPerf Inference v6.0 (new gpt-oss-120b benchmark; AMD FP4 MI355X/MI350X to 12 nodes) — audited, remains the current baseline"}
 ],
 "promises": [
  {"k":"oracle-july-ru-2326-3","vendor":"Oracle","announced":"2026-07","status":"delivered","t":"July RU 19.32 / 21.22 / 23.26.3 + CPU shipped Jul 21; Exadata SW 26.1.1/25.2.12/25.1.19 (25.1 final) — delivered"},
  {"k":"oracle-update-advisor","vendor":"Oracle","announced":"2026-07-29","status":"delivered","t":"Oracle Update Advisor — fleet patch-posture service via FPP/DBCA/AutoUpgrade + REST APIs — delivered"},
  {"k":"snowflake-2026-06-bundle","vendor":"Snowflake","announced":"2026-07","status":"pending","t":"2026_06 auto-enable still 'a subsequent August release' with NO published date; bundle contents churned after publication (BCR-2358 withdrawn Jul 23, BCR-2384 added Aug 7)"},
  {"k":"snowflake-2026-05-bundle","vendor":"Snowflake","announced":"2026-07","status":"delivered","t":"2026_05 enabled by default (managed Iceberg replicate-by-default; v3 NOT NULL adds need defaults) — delivered/enforcing"},
  {"k":"snowflake-cortex-rbac-sep8","vendor":"Snowflake","announced":"2026-08","status":"pending","t":"BCR-2378: CORTEX_MODELS_ALLOWLIST retired on a dated schedule; embedding-model RBAC enforced Sep 8 via bundle 2026_07 (carried from archive 08-09)"},
  {"k":"snowflake-adaptive-warehouse-ga","vendor":"Snowflake","announced":"2026-07","status":"pending","t":"Adaptive Compute now GA on AWS/Azure/GCP but per-query cost visibility still lags; independent SELECT benchmark disputes the cost framing"},
  {"k":"snowpipe-classic-deprecation","vendor":"Snowflake","announced":"2026","status":"unshipped","t":"Snowpipe Streaming classic: formal deprecation notice promised 'mid-2026', 18-month sunset starts on issue. It is mid-August and the notice has NOT landed"},
  {"k":"dbr19-ga","vendor":"Databricks","announced":"2026-07","status":"delivered","t":"DBR 19 GA (Spark 4.2.0); DBR 18 LTS through 2029-06-10 — delivered"},
  {"k":"dbx-mysql-cdc-ga","vendor":"Databricks","announced":"2026-07-01","status":"pending","t":"Lakeflow MySQL integrated (gateway-free) CDC — still Beta, second run running"},
  {"k":"dbx-predictive-optimization-default","vendor":"Databricks","announced":"2026-08","status":"pending","t":"Predictive Optimization default-on rollout to EXISTING UC tables ~Aug 2026 (carried from archive 08-05); auto-upgrade docs and what's-coming page disagree on deletion vectors"},
  {"k":"dbx-terraform-engine-retire","vendor":"Databricks","announced":"2026-08-06","status":"pending","t":"CLI Terraform deployment engine deprecated; direct engine default Aug 26, Terraform disabled in new releases September"},
  {"k":"fabric-nee-udfs-ga","vendor":"Fabric","announced":"2026-07","status":"delivered","t":"Spark NEE Python/Scala UDFs + complex types GA — delivered; the 5.76x applies to vectorized UDFs only"},
  {"k":"fabric-runtime-2-ga","vendor":"Fabric","announced":"2026","status":"unshipped","t":"Runtime 2.0 (Spark 4.1) still Public Preview while Runtime 1.3 GA support ends 2026-09-30 — a GA gap with no successor"},
  {"k":"fabric-coddspeed-ga","vendor":"Fabric","announced":"2026-07","status":"pending","t":"GPU-accelerated (CoddSpeed) Warehouse GA — still Early Access Preview, date unannounced"},
  {"k":"fabric-synapse-trusted-services","vendor":"Fabric","announced":"2026-08","status":"slipped","t":"Synapse trusted-services firewall retirement moved Aug 1 2026 to Jun 1 2027 — publicly slipped ~10 months; Azure Update notices still circulated the old date"},
  {"k":"bq-iceberg-managed-ga","vendor":"BigQuery","announced":"2026-07","status":"delivered","t":"Iceberg managed tables GA (partitioning, multi-statement transactions, advanced runtime) — delivered; the gap list (no MVs/RLS/CDC/partition evolution) is the real parity indicator"},
  {"k":"bq-hybrid-search-restore","vendor":"BigQuery","announced":"2026-06-25","status":"delivered","t":"Hybrid VECTOR_SEARCH/AI.SEARCH restored Aug 3 after the Jul 9 pull — delivered after a ~3.5 week outage"},
  {"k":"starrocks-4-0-ga","vendor":"Cloud DW Challengers","announced":"2026-07","status":"delivered","t":"StarRocks 4.0 GA with native Iceberg writes + PK partial-column upserts — delivered"},
  {"k":"duckdb-v2-async-io","vendor":"Cloud DW Challengers","announced":"2026-07-31","status":"pending","t":"DuckDB v2.0 with async I/O targeted fall 2026 (3x Parquet / 20x CSV on S3, project-run)"},
  {"k":"ducklake-11","vendor":"Cloud DW Challengers","announced":"2026","status":"pending","t":"DuckLake v1.1 / extension 2.0 targeted Fall 2026; release calendar calls the dates tentative while secondary coverage says September"},
  {"k":"amd-mi455x-helios-production","vendor":"AMD","announced":"2026-07","status":"pending","t":"Helios/MI455X ships 'later this year' with Microsoft committing $5-10B; gfx1250 PyTorch enablement only landed July with no production WideEP"},
  {"k":"nvidia-rubin-ultra-hbm-config","vendor":"NVIDIA","announced":"2026-08","status":"pending","t":"Rubin in production; Ultra HBM stack config still undecided amid the 2027 DRAM shortage"},
  {"k":"ualink-switch-silicon","vendor":"AI HW","announced":"2025","status":"slipped","t":"UALink switch silicon slipped to 2H2026 / H1 2027; NVLink still the shipping scale-up fabric"},
  {"k":"marvell-teralynx-t100","vendor":"Marvell","announced":"2026-07-17","status":"pending","t":"Teralynx T100 100.4 Tb/s switch — reference platforms sample Q4 2026, ESUN scale-up variant H2 2027"},
  {"k":"goldengate-26ai-schema-evolution","vendor":"Oracle","announced":"2026-06","status":"pending","t":"GoldenGate 26ai Automatic Schema Evolution GA (preview) — no movement this run"}
 ],
 "buildbets": [
  {"k":"self-explaining-database","status":"white-space"},
  {"k":"memory-tiering-economics","status":"white-space"},
  {"k":"agent-native-mcp-surface","status":"white-space"},
  {"k":"open-catalog-external-writes","status":"parity-play"},
  {"k":"per-gb-streaming-ingest","status":"parity-play"},
  {"k":"transparency-manifests-audited-tpc","status":"trust-play"}
 ],
 "skills": [
  {"k":"ai-workload-perf","status":"compounding"},
  {"k":"claim-forensics","status":"compounding"},
  {"k":"open-format-internals","status":"compounding"},
  {"k":"memory-economics","status":"emerging"},
  {"k":"agent-operable-tooling","status":"emerging"},
  {"k":"ebpf-linux-io","status":"hedge"}
 ],
 "gaps": [
  {"k":"external-writes-oracle-tables","status":"open","t":"External-engine writes into Oracle-managed tables — still WIDE: BigQuery Iceberg multi-statement transactions GA, StarRocks native writes, Snowflake Horizon converts consumed Delta shares to Iceberg and applies policy. Oracle DBMS_DCAT remains read-side"},
  {"k":"gpu-accelerated-warehouse","status":"open","t":"GPU-accelerated warehouse execution — Fabric CoddSpeed EAP, Sirius GPU-DuckDB ClickBench records (archive 08-05), NVIDIA open-sourced cuFile/GPUDirect Storage this window. Oracle accelerates storage-side scan, no managed GPU execution path"},
  {"k":"serverless-streaming-price","status":"open","t":"Serverless streaming ingest at a per-GB price point (Snowpipe Streaming ~0.0037 credits/GB; Databricks Lakeflow) — GoldenGate is the better engine wearing the wrong price tag"},
  {"k":"lowend-realtime-analytics","status":"open","t":"Low-end real-time analytics price-performance (ClickHouse 26.7 EXPLAIN ANALYZE + 15% join memory, StarRocks 4.0.13, Doris 4.1.3 Python UDFs)"},
  {"k":"behavior-change-transparency","status":"open","t":"Behavior-change transparency cadence — and this window it turned into an Oracle OPPORTUNITY: Snowflake's 2026_06 auto-enable has no published date, Databricks auto-upgrades existing tables, Fabric slipped a retirement 10 months. A dated, opt-out-able RU change manifest would beat all three"},
  {"k":"agent-native-surface","status":"open","t":"Agent-native developer surface with a security story — MCP's 2026-07-28 stateless rewrite + the ChainDrop worm propagating through IDE/agent config files makes the safety layer the differentiator, not the tool count"},
  {"k":"decode-time-policy-enforcement","status":"new","t":"NEW: decode-time policy enforcement for NL2SQL. Three papers in one month (PCC-SQL logit masking, GRID LALR(1) grammar subsetting, RBAC benchmark) show role-scoped SQL generation with provable 0% leakage. Select AI has no equivalent published guarantee — and Oracle owns the RBAC/Vault/Label Security surface that would make it credible"}
 ],
 "events": [
  {"k":"bq-dts-sku-label-case","date":"2026-08-11","t":"BigQuery DTS billing labels switch to lowercase and widen to load+merge — fix cost queries that string-match the label"},
  {"k":"k8s-aug-patch-batch","date":"2026-08-11","t":"Kubernetes August patch batch"},
  {"k":"pg-next-minor","date":"2026-08-13","t":"PostgreSQL quarterly minor release (May's wave carried 11 CVEs incl. four at 8.8)"},
  {"k":"claude-code-auto-default","date":"2026-08-14","t":"Claude Code auto mode becomes default on Pro/Max/Team — audit agent permission settings on anything prod-adjacent"},
  {"k":"anthropic-workbench-retire","date":"2026-08-17","t":"Anthropic experimental prompt-tools APIs + legacy Console Workbench retire; saved prompts/evals are NOT migrated"},
  {"k":"eas-observe-ga","date":"2026-08-20","t":"EAS Observe GA — event quotas and overage billing begin"},
  {"k":"dbr-13-3-eos","date":"2026-08-22","t":"Databricks DBR 13.3 LTS end of support"},
  {"k":"hot-chips-2026","date":"2026-08-23","t":"Hot Chips 38 at Stanford (Aug 23-25) — Rubin and MI400 architecture disclosures feed the Scoreboard"},
  {"k":"openai-assistants-retire","date":"2026-08-26","t":"OpenAI Assistants API removed; Play geofencing FGS use case removed; Kubernetes 1.37 GA"},
  {"k":"k8s-137-ga","date":"2026-08-26","t":"Kubernetes 1.37 GA — Static Pods lose secretRef/configMapRef, kube-proxy ipvs warns"},
  {"k":"redshift-tls12-enforce","date":"2026-08-30","t":"Amazon Redshift enforces TLS 1.2 minimum on provisioned and Serverless"},
  {"k":"play-api36-deadline","date":"2026-08-31","t":"Google Play target API 36 submission deadline (Nov 1 extension on request, form not live)"},
  {"k":"sonnet5-price-revert","date":"2026-08-31","t":"Claude Sonnet 5 introductory pricing ends: $2/$10 reverts to $3/$15 per MTok"},
  {"k":"fabric-runtime13-eos","date":"2026-09-30","t":"Fabric Runtime 1.3 (Spark 3.5) GA support ends; Runtime 2.0 still Preview"},
  {"k":"snowflake-cortex-rbac","date":"2026-09-08","t":"Snowflake embedding-model RBAC enforced via bundle 2026_07 (carried from archive 08-09)"},
  {"k":"oracle-oct-cpu","date":"2026-10-20","t":"Oracle quarterly CPU — pre-release note the Thursday before"},
  {"k":"skills-quarterly-review","date":"2026-10-01","t":"Skills Radar / Build Radar quarterly re-rank"},
  {"k":"pg14-eol","date":"2026-11-12","t":"PostgreSQL 14 end-of-life"}
 ],
 "patch": [
  {"k":"chaindrop-npm-worm","due":"","t":"ChainDrop / Mini Shai-Hulud npm worm (Aug 4-5, 400+ packages incl. keyv/cacheable/flat-cache/cache-manager) — steals npm/GitHub/AWS/K8s creds and propagates via VS Code and Claude config files committed to repos. Audit lockfiles, purge caches, rotate from a clean host. ESCALATED from isolated compromises (Jscrambler, @asyncapi) to self-propagating"},
  {"k":"oracle-july-cpu-carry","due":"2026-10-20","t":"Oracle July CPU / RU 19.32-21.22-23.26.3 — CVE-2026-61211 (9.9, third-party analysis attributes it to DBMS_CLOUD) and CVE-2026-47040 (9.1 REMOTE/UNAUTH Oracle Net Services, hits 19c/21c/23ai). Nothing Oracle-DB on CISA KEV. Advisory at Rev 5 — re-read if triaged on day one. Next CPU Oct 20"},
  {"k":"oracle-26ai-blockcheck-hang","due":"","t":"Upgrades to 26ai can HANG on block checking events (bug 38946554, MOS KB914929) after cloning/PDB refresh/restore — fixed in 23.26.3 or one-off. Also: OKV 21.15 + AVDF 20.18 flagged upgrade-immediately, separate from the DB RU"},
  {"k":"mongodb-july-batch","due":"","t":"MongoDB Jul 22 batch — 26 CVEs fixed 7.0.39/8.0.28/8.2.12/8.3.7 + Compass 1.49.7 (9.2 compute-mode heap corruption, 8.6 RBAC bypass, 8.4 Compass OIDC command injection). 8.2 EOL Jul 31. Percona PSMDB ~3 weeks behind"},
  {"k":"nuxt-devtools-rce","due":"","t":"Nuxt @nuxt/devtools RCE CVE-2026-71319 (9.6) + cross-user SSR payload cache leak — fixed 4.5.1/3.21.10, and you must PURGE CDN/edge caches for cache/swr/isr route rules. Next.js 9 CVEs (4 High) fixed 16.2.11/15.5.21"},
  {"k":"mcp-grafana-token-theft","due":"","t":"mcp-grafana CVE-2026-15583 (8.6) — crafted X-Grafana-URL header exfiltrates the service-account token and enables credentialed SSRF to cloud metadata. Fixed >=0.17.1. The observability plane is now an agent-layer credential target"},
  {"k":"nodejs-dotnet-batch","due":"","t":"Node.js Jul 29: 11 CVEs (3 High) in 22.23.2/24.18.1/26.5.1 incl. CVE-2026-58040, an INCOMPLETE FIX for CVE-2026-48934. .NET Jul 14: 17 CVEs across 8/9/10 (3 critical RCE), fixed 10.0.10/9.0.18/8.0.29"},
  {"k":"redshift-python-udf-enforce","due":"2026-08-30","t":"Redshift Patch 203 ENFORCES Python UDF EOL (breaks running SQL at next maintenance window on CURRENT track); JDBC RCE CVE-2026-8178 needs >=2.2.2; TLS 1.2 floor Aug 30; ODBC 1.x EOS Sep 30"},
  {"k":"pgbouncer-distro-lag","due":"","t":"PgBouncer CVE-2026-6664 (7.5, unauthenticated remote crash via malformed SCRAM) fixed upstream in 1.25.2 back in May but STILL unpatched in some distro packages — check the installed version, not your last apt upgrade"},
  {"k":"clickhouse-sqli-unconfirmed","due":"","t":"ClickHouse CVE-2026-51992 (claimed critical SQLi/RCE, <=26.3.9.8) — affected product recorded as a FORK (theliimbo/ClickHouse), ClickHouse's own security changelog has no 2026 entries, no vendor advisory, EPSS 0.5%. Do not page anyone; watch for a real advisory"},
  {"k":"plan-regression-chatter","due":"","t":"Plan-regression chatter (Lewis / Poder / oracle-l) — QUIET this window; Lewis' last post 26 Jun. But 19.32 changes BFILENAME result-cache plans and enforces Database Vault on DBMS_REDEFINITION (ORA-01031 risk). Capture STS/baselines before stacking the RU"}
 ]
}

# ---------------------------------------------------------------- section HTML
S = {}

S["v-read"] = """
<p class="lede">The line a customer quotes at you first this week is not a benchmark — it is <b>"your competitors publish a date and you publish 'a subsequent August release'."</b> Snowflake's 2026_06 bundle silently reinterprets <code>INTERVAL '3' days</code> from three seconds to three days and turns Query Acceleration on at scale factor 8 across every standard warehouse, and the auto-enable date is still unpublished. Databricks is auto-upgrading table properties on tables you already own. Fabric slipped a Synapse retirement by ten months while Azure Update notices still carried the old date. That is a <b>trust-play gap standing wide open</b>, and it costs nothing to walk through.</p>
<p>The second story is a live supply-chain incident, and it is the one that reaches your customers' CISOs: the <strong>ChainDrop</strong> npm worm republished 400+ packages, steals npm/GitHub/AWS/Kubernetes credentials, and spreads by injecting into VS Code and Claude config files committed to repos %s. Meanwhile Oracle's own July CPU carries a 9.9 in RDBMS and a <em>9.1 remotely-exploitable-without-authentication</em> flaw in Oracle Net Services %s — which is exactly why security posture stays a Mirror landmine and never an opening line.</p>
<p>Third: the measurement layer got worse, not better. AMD announced a 256-core, 16-channel Venice and every multiplier attached to it is AMD-run %s. SemiAnalysis openly discounts a CoreWeave "10x tokens per megawatt" Rubin claim for being single-turn on an outdated model %s. And <strong>no new audited TPC-H result was published in the entire window</strong> %s — the 16-channel/PCIe-Gen6 generation is arriving with zero audited price-performance data. Oracle has no recent audited submission either; that is the trust-play bet, still unclaimed by anyone.</p>
<h2>Where to spend today's attention</h2>
<ul class="sig">
<li><span class="tag">first</span><strong>Event Horizon</strong> — six dated items land inside 14 days and several fail closed. Aug 17 (Anthropic prompt-tools), Aug 22 (DBR 13.3 EOS), Aug 26 (OpenAI Assistants, K8s 1.37 GA), Aug 30–31 (Redshift TLS 1.2 floor, Play API 36).</li>
<li><span class="tag">meeting prep</span><strong>Claim Watch → Snowflake and Fabric</strong> — the two claims most likely to be quoted at you, and the two with the most quotable methodology holes (a cost number measured against last month's own build; a 5.76x that is really 1.08x for scalar UDFs).</li>
<li><span class="tag">self-audit</span><strong>Mirror</strong> — "30x faster AI vector searches" shipped Aug 5 with no methodology, no dataset, no baseline, no index type %s. In a window where we are auditing everyone else's numbers, that one is exposed. Fix it or stop citing it.</li>
<li><span class="tag">new</span><strong>Gap Ledger #7</strong> — decode-time policy enforcement for NL2SQL appeared this month with provable 0%% leakage. It is a gap today and a white-space opportunity tomorrow, because Oracle already owns the RBAC surface that would make it credible.</li>
</ul>
""" % (
 A("https://www.microsoft.com/en-us/security/blog/2026/08/04/chaindrop-supply-chain-compromise-anatomy-self-propagating-worm/"),
 A("https://www.oracle.com/security-alerts/cpujul2026.html"),
 A("https://www.tomshardware.com/pc-components/cpus/amds-256-core-epyc-9996-venice-claims-up-to-a-3-4x-jump-over-intel-xeon-competition-20-percent-over-nvidia-vera-zen-6-comes-with-up-to-1024mb-of-l3-16-channel-memory-and-5ghz-clock-speeds"),
 A("https://newsletter.semianalysis.com/p/vera-rubin-nvl72-vs-gb200-nvl72-inference"),
 A("https://www.tpc.org/tpch/results/tpch_results5.asp?version=3"),
 A("https://blogs.oracle.com/database/exascale-innovation-faster-oracle-ai-database-at-lower-cost"),
)

S["v-wn"] = """
<p>Diffed against <strong>edition %s (%s)</strong> — yesterday, one edition of drift. Items edition 029 already carried (the Exascale 30x entry, the 19.32 TLS 1.3/PQC entry, the LTRU-vs-patch-now landmine, the post-publication edit to Snowflake's 2026_06 changelog, the Horizon Delta→Iceberg conversion under Gap #1, and the Synapse trusted-services slip) are <em>not</em> repeated here as new.</p>
<h2>🆕 New this edition</h2>
<ul class="sig">
<li><span class="tag">gap</span><strong>Gap #7 opens: decode-time policy enforcement for NL2SQL</strong> — PCC-SQL logit masking and GRID LALR(1) grammar subsetting demonstrate provable 0%% column leakage with audit-grade replay. First genuinely new gap since #6. %s</li>
<li><span class="tag">claim</span><strong>BigQuery's Iceberg managed-table GA is narrower than the headline</strong> — no materialized views, no row-level security, no CDC updates, no partition evolution, and <em>one</em> concurrent mutating DML per table. The GA milestone landed; the parity gap did not close.</li>
<li><span class="tag">claim</span><strong>Fabric OneLake cool/cold tiers GA — the storage saving is real, the read is not.</strong> $0.023 → $0.004/GB, but a single 1 TB cold read bills 665,000 CU-seconds (~12%% of an F64 day), with 30/90-day minimum retention and early-deletion penalties.</li>
<li><span class="tag">claim</span><strong>ClickHouse 26.7 and Trino 483 both removed implicit S3 credential resolution in the same window</strong> — two independent engines making the same breaking auth change simultaneously. Silent-breakage risk for anyone running both.</li>
<li><span class="tag">claim</span><strong>StarRocks 3.5.20/4.0.13 fix WRONG RESULTS</strong> in MV rewrite, join reordering and sort elimination — three correctness bugs in the query optimizer, not performance regressions.</li>
<li><span class="tag">claim</span><strong>Snowflake flipped Cortex cross-region inference on for unconfigured accounts</strong> — a default change that moves inference across regions without an explicit opt-in. %s</li>
<li><span class="tag">patch</span><strong>mcp-grafana CVE-2026-15583 (8.6)</strong> — a crafted header turns into service-account token theft plus credentialed SSRF. The agent layer is now a credential surface on the observability plane. %s</li>
<li><span class="tag">patch</span><strong>Nuxt @nuxt/devtools RCE (9.6) and the Node.js Jul 29 batch (11 CVEs, 3 High)</strong> enter the radar — neither was on the 029 board.</li>
<li><span class="tag">promise</span><strong>Snowpipe Streaming classic deprecation notice is overdue</strong> — promised "mid-2026", and it is mid-August with no formal notice. Enters the tracker as <em>unshipped</em>; the 18-month sunset cannot start until it lands. %s</li>
<li><span class="tag">promise</span><strong>Databricks Predictive Optimization default-on reaches EXISTING UC tables</strong>, and the CLI Terraform deployment engine is now dated (direct engine default Aug 26, Terraform disabled in September releases).</li>
</ul>
<h2>🔺 Movement</h2>
<ul class="sig">
<li><span class="tag">re-scoped</span><strong>The npm worm is the same organism, renamed and re-counted.</strong> Edition 029 carried it as <em>keyv-shai-hulud</em> at ~444 names; today it is <em>ChainDrop / "Mini Shai-Hulud"</em> at 400+ packages, and it is now the run's lead flag item. What changed is not the worm but our certainty about its credential reach — npm, GitHub, AWS across 17 regions, Kubernetes. %s</li>
<li><span class="tag">enforcing</span><strong>Redshift Patch 203: logged yesterday for ANALYZE speed, material today for Python UDF EOL.</strong> Edition 029 recorded the patch as a 30%% ANALYZE improvement. The consequential half is that this is the phase where <em>existing</em> UDFs stop working, automatically, at the next maintenance window on the current track. %s</li>
<li><span class="tag">countdown</span><strong>Anthropic prompt-tools retirement 8 → 7 days</strong> (Aug 17, prompts/evals not migrated). Claude Code auto-mode default 5 → 4 days (Aug 14). DBR 13.3 LTS EOS 13 → 12 days (Aug 22).</li>
</ul>
<h2>➰ Still standing</h2>
<ul class="sig">
<li><strong>Gap #1 external-engine writes into Oracle-managed tables</strong> — open every edition since 001; DBMS_DCAT still read-side only.</li>
<li><strong>Gap #2 GPU-accelerated warehouse execution</strong> — Fabric CoddSpeed still EAP with no date; Oracle accelerates storage-side only.</li>
<li><strong>Zero Oracle audited TPC submissions</strong> — and zero from anyone else this window. The trust-play stays unclaimed.</li>
<li><strong>Oracle July CPU 9.9 + 9.1 remote/unauth</strong> — patched Jul 21, not on CISA KEV, carried as a Mirror landmine rather than a talking point. %s</li>
<li><strong>19c LTRU programme remains the only <em>pulled</em> row on the Promise Tracker</strong> — and it is ours. 19.28 is the last LTRU; MRPs end Jan 2027.</li>
<li><strong>TeamCity CVE-2026-63077 unauth RCE stays on the board</strong> — CISA KEV, federal BOD deadline passed Aug 8. A build server holds every database credential you have.</li>
<li><strong>Lakeflow MySQL gateway-free CDC still Beta</strong> — day 40, third consecutive edition pending.</li>
</ul>
<p class="wn-empty">__DROPPED__ rows from edition %s were carried forward by ledger merge rather than independently re-surfaced by today's research. The accumulating sections — Promise Tracker, Patch Radar, Benchmarks, Gaps — never shrink between editions.</p>
""" % (PREV_ED, PREV_DSLUG,
 A("https://arxiv.org/abs/2607.12341"),
 A("https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06_bundle"),
 A("https://grafana.com/security/security-advisories/cve-2026-15583/"),
 A("https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-classic-deprecation"),
 A("https://securitylabs.datadoghq.com/articles/npm-worm-compromises-popular-npm-packages/"),
 A("https://docs.aws.amazon.com/redshift/latest/mgmt/cluster-versions.html"),
 A("https://blogs.oracle.com/security/july-2026-critical-patch-update-released"),
 PREV_ED)

def card(vendor, verdict, vclass, title, basis, counter, ask=None, attack=None, arm=None):
    h = f'<div class="card"><div class="card-head"><span class="vchip">{vendor}</span>'
    h += f'<span class="verdict {vclass}">{verdict}</span></div>'
    h += f'<p class="card-title">{title}</p><p class="card-basis">{basis}</p>'
    if attack:
        h += f'<div class="counter attack"><span class="clabel">How it gets attacked</span><p>{attack}</p></div>'
    if arm:
        h += f'<div class="counter"><span class="clabel">How to arm it</span><p>{arm}</p></div>'
    if counter:
        h += f'<div class="counter"><span class="clabel">Oracle counter-story</span><p>{counter}</p></div>'
    if ask:
        h += f'<p class="ask"><b>Ask in the room</b> {ask}</p>'
    return h + '</div>'

SNOW_B = A("https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06_bundle")
SNOW_I = A("https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06/bcr-2359")
SNOW_Q = A("https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06/bcr-2373")
SNOW_A = A("https://www.snowflake.com/en/blog/adaptive-compute-ga-azure-google-cloud/")
SNOW_S = A("https://select.dev/posts/adaptive-vs-gen1-where-does-snowflake-s-new-warehouse-actually-save-you-money")
DBX_19 = A("https://docs.databricks.com/aws/en/release-notes/runtime/19")
DBX_AU = A("https://docs.databricks.com/aws/en/tables/automatic-upgrades")
DBX_LC = A("https://medium.com/towards-data-engineering/when-should-you-use-liquid-clustering-a-practitioners-benchmark-of-lakehouse-layout-strategies-fc67e7e3651b")
BQ_MT = A("https://docs.cloud.google.com/bigquery/docs/managed-tables")
BQ_RN = A("https://docs.cloud.google.com/bigquery/docs/release-notes")
FAB_T = A("https://learn.microsoft.com/en-us/fabric/onelake/onelake-storage-tiers")
FAB_N = A("https://learn.microsoft.com/en-us/fabric/data-engineering/native-execution-engine-overview")
FAB_L = A("https://learn.microsoft.com/en-us/fabric/data-engineering/lifecycle")
TRINO = A("https://trino.io/docs/current/release/release-483.html")
CH = A("https://clickhouse.com/docs/whats-new/changelog")
SR = A("https://docs.starrocks.io/releasenotes/release-3.5/")
DUCK = A("https://duckdb.org/2026/07/31/asynchronous-io.html")
VEN = A("https://www.storagereview.com/news/amd-6th-gen-epyc-venice-256-cores-1-6tb-s-and-the-first-pcie-gen-6-server-cpu")
DRAM = A("https://www.trendforce.com/presscenter/news/20260709-13140.html")
TPC = A("https://www.tpc.org/tpch/results/tpch_results5.asp?version=3")
MDB = A("https://www.mongodb.com/resources/products/alerts")
MDB83 = A("https://www.mongodb.com/docs/manual/release-notes/8.3/")
SEMI = A("https://newsletter.semianalysis.com/p/can-amd-break-the-cuda-moat-amd-advancing")
TILE = A("https://newsletter.semianalysis.com/p/ultra-high-interactivity-on-nvidia")
ORA_CPU = A("https://www.oracle.com/security-alerts/cpujul2026.html")
ORA_19 = A("https://docs.oracle.com/en/database/oracle/oracle-database/19/newft/ru-19-32.html")
ORA_EX = A("https://blogs.oracle.com/exadata/exadata261")
ORA_30X = A("https://blogs.oracle.com/database/exascale-innovation-faster-oracle-ai-database-at-lower-cost")
ORA_PQ = A("https://blogs.oracle.com/database/database-19c-now-supports-tls-1-3-post-quantum-cryptography")
ORA_ADB = A("https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/whats-new-adwc.html")
ORA_ADBD = A("https://docs.oracle.com/en/cloud/paas/autonomous-database/dedicated/adbaa/new-feature-announcements.html")
ORA_RU31 = A("https://mikedietrichde.com/2026/05/13/ru-19-31-has-been-put-on-hold-and-will-be-available-soon-again/")

S["v-claims"] = "<p>Every competitor performance or price claim shipped in-window, with what the number actually rests on. <strong>Eight claims, seven vendor-run, one audited-adjacent, zero new audited submissions.</strong></p><div class=\"cards\">" + "".join([
 card("Snowflake","vendor-run","vendorrun",
  "2026_06 bundle: QAS on by default at scale factor 8, and an auto-enable date that does not exist",
  f"Basis: Snowflake's own behavior-change docs. QAS auto-enablement moves from Gen2/multi-cluster at scale factor 2 to <em>every</em> standard warehouse at scale factor 8 {SNOW_Q}. The bundle flips enabled-by-default in \"a subsequent August 2026 release\" — no date published, and the contents changed after publication (BCR-2358 withdrawn Jul 23, BCR-2384 added Aug 7) {SNOW_B}. Separately, <code>INTERVAL '3' days</code> currently adds three <em>seconds</em> and will start adding three days {SNOW_I}.",
  f"Predictable, dated, opt-out-able change is the whole argument. Oracle RUs land on a published quarterly calendar with a named next date (Oct 20) {ORA_CPU}, datapatch gives a backout path, and SQL Plan Management plus Real-Time SPM exist specifically so an optimizer change cannot silently alter a plan. Concede our own tension honestly — see the Mirror landmine on monthly patching — then make the point that a credit-consuming feature turning itself on at 4x the previous ceiling is a budget event nobody scheduled.",
  "\"What is the exact date 2026_06 auto-enables in our account, and what is your rollback if the INTERVAL semantics change a reported number?\""),
 card("Snowflake","vendor-run","vendorrun",
  "Adaptive Compute GA on Azure and GCP, \"up to ~30% cheaper\"",
  f"Basis: the 30% is measured <strong>Jul 23 build vs the Jun 16 build</strong> on single-user 10TB TPC-DS — not against Gen1 or Gen2 {SNOW_A}. An independent SELECT benchmark (pre-dating the cost build) found Adaptive \"is not a drop-in cost reduction\" and that Gen1 was faster <em>and</em> cheaper for continuously-busy sequential workloads {SNOW_S}. Enterprise+ only.",
  "A self-referential improvement number is the softest kind. Our counter is not a competing multiplier — it is that Autonomous auto-scaling bills per-OCPU-second against a published rate you can model before you run anything, and Exadata Smart Scan / Flash Cache / In-Memory move the work rather than the SKU. Offer to model their actual workload shape rather than trade percentages.",
  "\"Thirty percent cheaper than what, exactly — and does that hold for a continuously-busy ELT profile or only for spiky low-concurrency?\""),
 card("Databricks","vendor-run","vendorrun",
  "DBR 19 on Spark 4.2.0 — and Arrow Python UDFs default-on with acknowledged type-coercion changes",
  f"Basis: Databricks' own release note says the new default \"can change type-coercion behavior for some UDFs compared to previous releases\" {DBX_19}. Same release drops JDK 17 and ~90 preinstalled Python packages. Separately, automatic table upgrades keep applying liquid clustering, Checkpoint V2, Parquet v2 and row tracking to Unity Catalog managed tables you already own {DBX_AU}.",
  f"This is the strongest consolidation argument available right now: a platform that changes UDF semantics and table properties underneath you makes \"we didn't change anything\" untrue during incident review. Oracle's counter is mechanism-level — Automatic Indexing and real-time statistics are actuators with visible decision reports (DBA_AUTO_INDEX_*), plan changes are gated by SPM, and the 19.32 RU note tells you the one plan-visible change it makes (BFILENAME loses result-cache) {ORA_19}. Predictability is the product.",
  "\"When Predictive Optimization changes a table property on a table we own, where is the audit record and how do we attribute a regression to it?\""),
 card("Databricks","peer-reviewed","peer",
  "\"Liquid clustering replaces Z-order\" — contradicted by the only independent test in-window",
  f"Basis: a practitioner benchmark on 50M synthetic retail rows found liquid clustering won point lookups (1.003s) and time-range aggregation (659ms) but <strong>lost multi-column filters to Z-order</strong> (615ms) {DBX_LC}. The author flags the test as synthetic and explicitly does not measure write amplification. Databricks' own 2.5x clustering-speed figure is vendor-run.",
  "Do not overclaim the inverse. The honest counter is that Oracle exposes the clustering decision surface — partitioning, attribute clustering, zone maps, In-Memory — as things you choose and can measure, rather than a single automatic layout you cannot A/B. Offer to run their multi-column filter shape both ways; that is a demo we win on transparency even when the number is close.",
  "\"Has anyone re-run the layout comparison on your filter shapes, including write amplification?\""),
 card("BigQuery","vendor-run","vendorrun",
  "Iceberg managed tables GA — and the gap list matters more than the GA",
  f"Basis: partitioning, multi-statement transactions and advanced runtime are GA {BQ_RN}. But partitioning is DATE/DATETIME/TIMESTAMP only, <strong>partition evolution is unsupported</strong>, and managed Iceberg tables still have no materialized views, no authorized views, no row-level security, no CDC updates, no managed DR — and <strong>one concurrent mutating DML statement per table</strong>, the rest queued {BQ_MT}. Project slot caps landed as an explicitly \"approximate\" cap.",
  f"This is the clearest place where the open-format story meets its own limits, and it is also where we must be honest: Gap #1 says external-engine writes into Oracle-managed tables are our gap, and it widened again this window. The counter is scope — Oracle gives you MVs, RLS, fine-grained policy and concurrent DML on the <em>same</em> table you query, with ADB Serverless adding identity-aware row/column authorization {ORA_ADB}. Their Iceberg tables cannot do those things yet.",
  "\"How many concurrent MERGE statements does your pipeline need against one table — and do you need row-level security on it?\""),
 card("Fabric","vendor-run","vendorrun",
  "Spark native execution engine \"up to 5.76x\" — which is 1.08x for scalar Python UDFs",
  f"Basis: Microsoft's own numbers. 5.76x applies to vectorized <code>@pandas_udf</code> UDFs; scalar Python UDFs move <strong>1.08x</strong>, essentially noise, and TPC-DS with complex types 2.35x {FAB_N}. The same doc lists silent wrong-results divergences from JVM Spark: <code>round()</code> uses <code>std::round</code>, <code>map()</code> skips the duplicate-key check so <code>mapKeyDedupPolicy=EXCEPTION</code> no longer throws, and <code>collect_list()</code> ordering can differ.",
  f"A headline multiplier that collapses by workload type is exactly the Claim Forensics play. Pair it with the OneLake tier arithmetic — a 1TB cold-tier read burns ~665,000 CU-seconds, about 12% of an F64's daily capacity {FAB_T} — and the point makes itself: their cost model now depends on access pattern <em>and</em> gateway version. Oracle's counter is Smart Scan offload that does not change SQL semantics, and Exadata 26.1 storage-side work on Flash Cache, XRMEM and IORM {ORA_EX}.",
  "\"Which of your UDFs are vectorized, and have you diffed NEE-on vs NEE-off output on your financial aggregations?\""),
 card("Cloud DW Challengers","vendor-run","vendorrun",
  "ClickHouse 26.7 and Trino 483 remove implicit S3 credentials — and StarRocks fixes wrong results",
  f"Basis: ClickHouse 26.7 stops resolving the server's own cloud credentials from user SQL {CH}; Trino 483 makes <code>s3.auth-type</code> mandatory across Iceberg, Delta, Hudi and Hive {TRINO}. Meanwhile StarRocks 3.5.20 corrects wrong-result bugs in <strong>materialized-view rewrite</strong>, join reordering and sort elimination {SR}. DuckDB's v2.0 async I/O claims 3x Parquet / 20x CSV on S3 — project-run, unaudited {DUCK}.",
  "Two separate arguments, both ours. On credentials: the confused-deputy problem is being closed late and breakingly in the open-source lane, while Database Vault, Label Security and unified audit have enforced this boundary for years. On correctness: wrong results from MV rewrite is the failure mode customers fear most from an optimizer, and it is precisely what SPM plus baseline capture exist to prevent. Be careful not to gloat — offer the regression-harness method, not the sneer.",
  "\"If your MV rewrite returned a wrong number last quarter, how would you know?\""),
 card("Database Hardware / AI Hardware","audited","audited",
  "Venice and Helios spec sheets lead; measured throughput does not follow",
  f"Basis: EPYC 9006 \"Venice\" — 256 Zen 6c cores, 16-channel DDR5, PCIe Gen6, ~1.6 TB/s theoretical peak at MRDIMM-12800, SP7 in Q4 2026 with mainstream SP8 not until H1 2027 {VEN}. Every multiplier is AMD-run with undisclosed configs. On the AI side, AMD leads NVIDIA on every published spec (432GB vs 288GB HBM4, 20 vs 17.5 PF FP8) yet SemiAnalysis rates the real throughput delta \"relatively mild\" and notes no production WideEP at launch {SEMI}. And <strong>no new audited TPC-H result was published in the window at all</strong> {TPC}.",
  f"The whole-stack argument: server DRAM is set to rise another 13-18% QoQ through 2H27, pushed disproportionately onto buyers without long-term agreements {DRAM}, which means a 16-channel platform costs more to populate than the CPU costs to buy. Exadata's answer is to not need the DRAM — Smart Scan pushes filtering to storage, storage indexes skip I/O, In-Memory compresses what does stay resident, and 26.1 adds XRMEM and Flash Cache work {ORA_EX}. Frame the refresh as bandwidth-per-dollar, not cores.",
  "\"Have you priced the DIMMs for a fully-populated 16-channel box, or just the CPU?\"")]) + "</div>"

STANDING = open("prev_sections/v-mirror.html", encoding="utf-8").read()
STANDING = STANDING[STANDING.index('<h2>Standing attack lines'):]

S["v-mirror"] = ("<p>The same forensics pointed at Oracle. If a symmetric standard would kill a competitor's claim, it has to kill ours too — that is what keeps this an engineering document. "
 "<strong>Statuses:</strong> <em>exposed</em> = marketing number, no methodology · <em>verifiable · go first</em> = reproducible but unpublished, a publishing opportunity · "
 "<em>landmine</em> = a true-facts juxtaposition to pre-draft · <em>precision check</em> = our own counter-story overclaims.</p><div class=\"cards\">" + "".join([
 card("Oracle","exposed","vendorrun",
  "\"30x faster AI vector searches\" via Exadata AI Smart Scan on Exascale",
  f"Shipped Aug 5. No methodology, no dataset, no baseline engine, no index type (HNSW vs IVF vs DiskANN), no concurrency level {ORA_30X}. The rest of the post is positioning.",
  None,
  attack="\"Thirty times what? You are auditing Snowflake for measuring against their own previous build, and you published a bare 30x with no dataset at all. Show me the query, the corpus size, the recall target and the baseline — or withdraw the number.\" This lands hard because it is fair.",
  arm=f"Stop citing 30x. Replace it with the mechanism and one reproducible number you own: per-cell top-K reduces rows shipped from storage to DB nodes, and HNSW now takes transactional DML with RAC-wide consistency in 26ai {ORA_ADB} — which rivals genuinely cannot match. Then <strong>go first</strong>: publish an HNSW-vs-IVF-vs-DiskANN run at a stated recall target and concurrency. This is Skills Bet 1 and Bet 2 pointed at our own material."),
 card("Oracle","verifiable · go first","beta",
  "19.32 ships TLS 1.3, ML-KEM/ML-DSA post-quantum and FIPS 140-3 — on 19c",
  f"Real and genuinely ahead of most of the field: a new OpenSSL-based provider with hybrid classic+PQC groups, on the long-term-support release rather than only the newest one {ORA_PQ}.",
  None,
  attack="\"Available is not enabled.\" Default behavior is unchanged, you opt in with <code>set_crypto_provider.py</code>, it requires an instance <em>and</em> listener restart, only one provider can be active, and FIPS 140-3 mode drops algorithms available elsewhere. A skeptical customer will read \"supports post-quantum\" as \"protects me today\" and feel misled when they find the switch is off.",
  arm="Say it precisely: <em>19c can be configured for TLS 1.3 and hybrid PQC key exchange today, opt-in, with a restart</em>. That framing is still a win — most rivals have no PQC story on their LTS line at all. Pair it with a measured handshake-cost number from a non-prod listener, which nobody has published. Second go-first candidate."),
 card("Oracle","landmine","vendorrun",
  "\"Move immediately to a monthly security patching cycle\" — three months after RU 19.31 was pulled",
  f"Both facts are Oracle's own. The July CPU post urges monthly patching, citing frontier AI models lowering the barrier to exploit discovery {ORA_CPU}; in May, RU 19.31 was put on hold and withdrawn {ORA_RU31}.",
  None,
  attack="\"You want us to patch monthly on a train you yourself had to stop in May, with a support portal that a well-known Oracle blogger just documented as returning wrong AI answers and failing patch downloads. Faster cadence with the same regression budget is how plan regressions reach our production.\"",
  arm="Never lead with patch-cadence discipline. If raised: concede the tension in one sentence, then pivot to the tooling that makes cadence survivable — Update Advisor for fleet posture via FPP/DBCA/AutoUpgrade with REST APIs, datapatch backout, and SQL Plan Management baselines captured <em>before</em> stacking the RU. The honest version of this claim is \"we are giving you the tools to patch faster,\" not \"we patch flawlessly.\""),
 card("Oracle","exposed","vendorrun",
  "The agentic ADB story is Serverless-only",
  f"July brought Select AI Supervisor Agent, agent tool/team discovery, a managed A2A server, external IdP auth for Database Actions and availability-domain selection — all on <strong>Serverless</strong> {ORA_ADB}. The Dedicated changelog got exactly one governance feature in July and <strong>nothing in August</strong> {ORA_ADBD}.",
  None,
  attack="\"We run ADB-Dedicated / ExaDB-D. Which of those features do we actually get?\" If the answer in the room was \"Autonomous Database has it,\" the credibility loss is immediate and permanent.",
  arm="Always qualify the deployment model before citing an ADB feature — it takes four words and prevents the worst kind of correction. For Dedicated customers, lead with what Dedicated <em>did</em> get (Oracle API Access Control: approval workflows, separation of duties, time-bound access for sensitive management operations) — a real governance differentiator for regulated shops, and one nobody else ships at the database-management layer."),
 card("Oracle","precision check","beta",
  "\"Open interop\" via DBMS_DCAT and the Iceberg REST catalog",
  "This is one of our own Claim Watch counter-stories, and it overreaches. DBMS_DCAT plus Lake Cache is read-side. Gap #1 widened again this window: BigQuery shipped Iceberg multi-statement transactions GA and Snowflake Horizon now converts consumed Delta shares to Iceberg on ingest and applies masking to the converted tables.",
  None,
  attack="\"You called their open-format story limited, then described your own read-only catalog as interop.\" A symmetric standard kills our phrasing here.",
  arm="Say <em>read interop today; a governed external write path is the roadmap</em>. Naming it as Gap #1 out loud is the strongest lock-in rebuttal available — and it buys the credibility that makes the concurrent-DML and RLS arguments against BigQuery land.")]) + "</div>" + STANDING)

S["v-questions"] = f"""
<p>What customers will ask in the next ~2 weeks, based on what just GA'd or just broke. Talk tracks, not scripts — keep the caveats in.</p>
<div class="qa">
<p class="q">"Our security team saw the npm worm headlines. Is our database estate exposed?"</p>
<p class="talk">Almost certainly not directly — ChainDrop is a Node package-registry campaign, and it steals developer and CI credentials rather than attacking a database engine {A("https://www.microsoft.com/en-us/security/blog/2026/08/04/chaindrop-supply-chain-compromise-anatomy-self-propagating-worm/")}. The honest exposure is second-order and worth naming: it harvests AWS and Kubernetes credentials, so anything your build machines could reach, it could reach. The database-side action is to check which service accounts your CI holds and whether any of them can touch production data directly. That is a good conversation to have anyway, and it is where Database Vault and time-bound privileged access earn their keep — but do not let anyone sell them a database product as the fix for a laptop-and-CI compromise.</p>
<p class="q">"Snowflake told us a behavior bundle auto-enables this month. Should we be worried, and does Oracle do this?"</p>
<p class="talk">Yes, worth attention, and the specific thing to check is INTERVAL literals with plural qualifiers — <code>INTERVAL '3' days</code> currently adds three seconds and will start adding three days {SNOW_I}. That is a silent change to reported numbers, not an error. On our side: RUs land on a published quarterly calendar with the next date already known (Oct 20), and plan changes are gated by SQL Plan Management so an optimizer change cannot silently alter a plan you have baselined. Be straight about the asymmetry that exists, though — we do not publish a per-change opt-out window the way a behavior-change bundle does, and RU 19.31 was pulled in May. Our advantage is the date and the backout path, not perfection.</p>
<p class="q">"We are refreshing database servers. Should we wait for Venice or Diamond Rapids?"</p>
<p class="talk">If you need a mid-size OLTP box, there is nothing to wait for this year — Venice's mainstream 8-channel SP8 platform is H1 2027, and Q4 2026 gets you the 256-core SP7 only {VEN}. Intel's 16-channel Xeon 7 slipped to roughly mid-2027, and the cheap 8-channel tier was cancelled outright, so that comparison point is over a year out. The number that should actually drive the decision is memory: server DRAM contracts are forecast up another 13-18% this quarter and rising through 2H27, hitting buyers without long-term agreements hardest {DRAM}. A well-populated current-generation box bought before the next contract step-up will very likely beat a half-populated next-generation box on both delivered bandwidth and delivery date. Size for bandwidth-per-dollar, not core count.</p>
<p class="q">"Your competitors keep publishing benchmark numbers. Where are Oracle's?"</p>
<p class="talk">The fair answer is that nobody published an audited result this window — the TPC-H leaderboard has had no new entries since late June, so the entire 16-channel/PCIe-Gen6 generation currently has zero audited price-performance data {TPC}. That cuts both ways and I will not pretend otherwise: Oracle does not have a recent audited submission either. What I would rather do than trade multipliers is run your workload. Every vendor number in circulation this month — including one of ours — is measured on a shape that probably is not yours, and the 30x vector-search figure we published has no methodology attached to it. I would treat all of them as hypotheses.</p>
<p class="q">"We are putting an LLM in front of our warehouse. How do we stop it reading columns a user should not see?"</p>
<p class="talk">This is the sharpest question in the batch and the research just moved. Three papers in the last month enforce column policy at <em>decode</em> time rather than by prompting — masking logits against a grammar so restricted columns are literally ungeneratable, with reported 0% leakage and bit-identical audit replay {A("https://arxiv.org/abs/2607.12341")} {A("https://arxiv.org/abs/2607.11951")}. The honest position: Select AI does not publish an equivalent guarantee today, and I would not claim one. What Oracle does bring is the enforcement layer underneath — VPD, Label Security, Database Vault and unified audit apply to the generated SQL regardless of who or what wrote it, so a leaked column reference still fails at execution. Belt-and-braces, with the belt being ours and the braces being an active research area.</p>
</div>"""

def gap(t, body):
    return f'<div class="gap"><b>{t}</b><p>{body}</p></div>'

S["v-gaps"] = ("<p>Where a competitor shipped something Oracle has no clean answer to. Carried every edition until genuinely closed. "
 "Knowing these is what makes everything else in this document credible.</p>" + "".join([
 gap("#1 · External-engine writes into Oracle-managed tables — <em>open, widened again</em>",
  f"BigQuery Iceberg managed tables now take multi-statement transactions {BQ_MT}, StarRocks 4.0 writes Iceberg natively, and Snowflake Horizon now converts every Delta table in a consumed share to Iceberg on ingest and applies masking and row-access policy to the converted tables {A('https://docs.snowflake.com/en/release-notes/2026/other/2026-07-21-delta-sharing-horizon-catalog-ga')}. Oracle's DBMS_DCAT plus Lake Cache remains read-side. <strong>What would neutralize it:</strong> a governed external write path — an Iceberg REST catalog endpoint where an outside engine commits and Oracle enforces policy on the commit, not just on the read."),
 gap("#2 · GPU-accelerated warehouse execution — <em>open</em>",
  f"Fabric's CoddSpeed GPU warehouse remains Early Access Preview with no GA date, but the moat is eroding from below: NVIDIA open-sourced the cuFile/GPUDirect Storage APIs this window {A('https://www.blocksandfiles.com/flash/2026/08/04/fms-storage-ticker-4-aug-2026/5282932')}, removing a real integration blocker for getting columnar data off NVMe into GPU memory, and the Sirius GPU-DuckDB work set ClickBench price-performance records ({ARCH('2026-08-05')}). Oracle accelerates scan storage-side; there is no managed GPU-execution path. <strong>What would neutralize it:</strong> GPU offload for the specific shapes that actually benefit — large hash joins, vector index build, ONNX scoring in-database — rather than a general GPU engine."),
 gap("#3 · Serverless streaming ingest at a per-GB price point — <em>open</em>",
  "Snowpipe Streaming's high-performance architecture bills ~0.0037 credits per uncompressed GB; Databricks Lakeflow prices similarly. GoldenGate is the better engine wearing the wrong price tag. <strong>What would neutralize it:</strong> a consumption-priced streaming ingest SKU that does not require a GoldenGate deployment decision up front."),
 gap("#4 · Low-end real-time analytics price-performance — <em>open</em>",
  f"ClickHouse 26.7 shipped EXPLAIN ANALYZE plus ~15% lower join memory {CH}; StarRocks 4.0.13 and Doris 4.1.3 continue closing on features while staying free at the bottom. The entry price for \"fast enough analytics\" keeps falling. <strong>What would neutralize it:</strong> an Autonomous tier priced for the workload that today never evaluates Oracle at all."),
 gap("#5 · Behavior-change transparency cadence — <em>open, and now an opportunity</em>",
  f"This edition it flipped from a gap we lose on to a gap the whole field is losing on. Snowflake's 2026_06 auto-enable has no published date and the bundle changed after publication {SNOW_B}; Databricks auto-upgrades table properties on existing tables {DBX_AU}; Fabric slipped a retirement by ten months while old notices still circulated {FAB_L}. <strong>What would neutralize it — for us, in our favour:</strong> publish a dated, machine-readable RU change manifest with an opt-out window. Nobody in this market currently does. That is Build Bet 6."),
 gap("#6 · Agent-native developer surface with a security story — <em>open</em>",
  f"MCP's 2026-07-28 revision rewrote the protocol to be stateless and deprecated Sampling, Roots, Logging and OAuth dynamic client registration {A('https://modelcontextprotocol.io/specification/2026-07-28/changelog')}, while ChainDrop demonstrated worms propagating through agent and IDE config files. Oracle has ORDS-as-MCP-server and Select AI agents, but thin third-party mindshare. <strong>What would neutralize it:</strong> not more tools — a hardened, audited MCP surface where every tool call lands inside the database's existing privilege and audit model."),
 gap("#7 · Decode-time policy enforcement for NL2SQL — <em>NEW this edition</em>",
  f"Three independent papers in one month enforce access control while the model generates SQL rather than after: PCC-SQL compiles a column-use policy over semantic roles into a per-token logits mask with a reported 0% leakage rate {A('https://arxiv.org/abs/2607.12341')}, and GRID derives masks from an LALR(1) parser state with 3.6-6.7µs median mask computation and bit-identical replay for audit {A('https://arxiv.org/abs/2607.11951')}. A separate benchmark shows models that look strong unrestricted degrade sharply under RBAC {A('https://arxiv.org/abs/2607.22115')}. Select AI publishes no equivalent guarantee. <strong>What would neutralize it:</strong> this is the rare gap that is also white space — Oracle already owns VPD, Label Security, Database Vault and unified audit, which is exactly the substrate a provable enforcement claim needs.")]))

EV = [
 ("2026-08-11","hot","BigQuery DTS billing labels lowercase + widen to load/merge","Update billing exports and FinOps queries to match BOTH label values; expect an apparent DTS cost jump that is re-attribution, not a price change.",BQ_RN),
 ("2026-08-11","hot","Kubernetes August patch batch","Routine; fold into the same window as the 1.37 GA prep.",A("https://kubernetes.io/releases/patch-releases/")),
 ("2026-08-13","hot","PostgreSQL quarterly minor release","Book the patch window now — May's wave carried 11 CVEs including four at 8.8.",A("https://www.postgresql.org/developer/roadmap/")),
 ("2026-08-14","hot","Claude Code auto mode default on Pro/Max/Team","Audit agent permission settings and sandbox config on anything prod-adjacent before Friday; the opt-out is not publicly documented.",A("https://techcrunch.com/2026/08/09/anthropic-is-turning-claude-codes-auto-mode-on-by-default/")),
 ("2026-08-17","hot","Anthropic experimental prompt-tools APIs + legacy Console Workbench retire","Export saved prompts, variables and evals — they are NOT migrated. Move /v1/experimental/* calls in-process.",A("https://platform.claude.com/docs/en/release-notes/api")),
 ("2026-08-20","hot","EAS Observe GA — quotas and overage billing begin","If you are in the beta and ingesting heavily, tune sample rates before the 20th.",A("https://expo.dev/changelog/eas-observe-moves-to-general-availability-on-august-20")),
 ("2026-08-22","hot","Databricks DBR 13.3 LTS end of support","Inventory jobs, pipelines and cluster policies pinned to 13.3; land on 15.4 LTS or 17.3 LTS (16.4 for Spark 3.5.x semantics).",A("https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/")),
 ("2026-08-23","hot","Hot Chips 38, Stanford (Aug 23-25)","Rubin and MI400 first-party architecture detail lands here — it feeds the Scoreboard before Q4 procurement.",A("https://hotchips.org/")),
 ("2026-08-26","warm","OpenAI Assistants API removed · Kubernetes 1.37 GA · Play geofencing FGS removed · Databricks direct deploy default","Four unrelated cutovers on one day. K8s 1.37 drops secretRef/configMapRef from Static Pods; Play requires the Geofence API.",A("https://developers.openai.com/api/docs/deprecations")),
 ("2026-08-30","warm","Amazon Redshift enforces TLS 1.2 minimum","Query sslversion in STL_CONNECTION_LOG / SYS_CONNECTION_LOG now. Note secondary sources wrongly report this as already effective July 30.",A("https://docs.aws.amazon.com/redshift/latest/mgmt/behavior-changes.html")),
 ("2026-08-31","warm","Google Play target API 36 · Claude Sonnet 5 intro pricing ends ($2/$10 → $3/$15)","Submission-blocking on the Play side; a 50% input cost increase on the model many teams defaulted to.",A("https://developer.android.com/google/play/requirements/target-sdk")),
 ("2026-08 (TBD)","warm","Snowflake 2026_06 bundle flips to enabled-by-default","No date published. Enable it in a scratch account and grep for plural INTERVAL qualifiers now — this is the transparency talking point AND a real risk.",SNOW_B),
 ("2026-09-08","warm","Snowflake embedding-model RBAC enforced via bundle 2026_07","Carried from "+ARCH("2026-08-09")+" — today's briefs did not re-surface it.",SNOW_B),
 ("2026-09-14","ok","Databricks workspace entitlements enforcement mandatory","Automation that assumed implicit entitlements will fail.",A("https://docs.databricks.com/aws/en/release-notes/whats-coming")),
 ("2026-09-30","ok","Fabric Runtime 1.3 GA support ends · Redshift ODBC 1.x EOS · Play app registration deadline","Runtime 2.0 is still Preview, so there is no GA successor to move to — plan the gap.",FAB_L),
 ("2026-10-01","ok","Skills Radar / Build Radar quarterly re-rank","Re-derive bets from ~90 days of ledger trends; retire or replace at most two.",""),
 ("2026-10-20","ok","Oracle quarterly Critical Patch Update","Pre-release note lands the Thursday before. Pre-stage testing and backout per Oracle's own guidance.",ORA_CPU),
 ("2026-11-12","ok","PostgreSQL 14 end-of-life","Managed platforms are already auto-upgrading affected projects.",""),
]
S["v-events"] = ("<p>Every dated item across all 19 briefs, next ~60 days. <strong>Eight land inside 14 days</strong> and several fail closed rather than warning first.</p>"
 '<div class="twrap"><table><thead><tr><th>Date</th><th>Days</th><th>Event</th><th>What to do with it</th></tr></thead><tbody>'
 + "".join(f'<tr><td class="mono">{d}</td><td><span class="due {c}">{"≤14d" if c=="hot" else ("≤30d" if c=="warm" else "later")}</span></td>'
           f'<td><strong>{e}</strong> {s}</td><td>{a}</td></tr>' for d,c,e,a,s in EV)
 + "</tbody></table></div>")

S["v-perf"] = f"""
<p>The cross-brief filter: only what changes performance-engineering work.</p>
<ul class="sig">
<li><span class="tag">default change</span><strong>Arrow-optimized Python UDFs default-on in Spark 4.2.0 / DBR 19</strong>, with acknowledged type-coercion changes {DBX_19}. <strong>Snowflake INTERVAL plural qualifiers</strong> change from seconds to the named unit {SNOW_I}. <strong>Fabric NEE</strong> diverges from JVM Spark on <code>round()</code>, <code>collect_list()</code> ordering and duplicate-key maps {FAB_N}. <strong>MongoDB 8.3</strong> makes the cost-based ranker the default plan-selection mechanism {MDB83}. Four engines, one quarter, all silently result- or plan-affecting.</li>
<li><span class="tag">default change</span><strong>ClickHouse 26.7 and Trino 483 both removed implicit S3 credential resolution</strong> {CH} {TRINO} — a config break, not a perf change, but it will present as "the cluster starts and then cannot read."</li>
<li><span class="tag">benchmark</span><strong>No new audited TPC-H result in the window</strong> {TPC}. The most recent entries all predate it (Dell/Exasol 1TB at $25.01/kQphH, HPE/SQL Server 30TB at $1,499.13/kQphH, Alibaba Hologres 3TB). The 16-channel/Gen6 generation has zero audited price-performance data.</li>
<li><span class="tag">benchmark</span><strong>The one independent layout benchmark contradicts the vendor line</strong> — Z-order beat liquid clustering on multi-column filters (615ms vs 659ms) on 50M synthetic rows, with write amplification unmeasured {DBX_LC}.</li>
<li><span class="tag">hardware curve</span><strong>Server DRAM +13-18% QoQ in 3Q26, rising through 2H27</strong>, with LTA holders insulated and everyone else absorbing it {DRAM}. PC and server DRAM have decoupled — do not use consumer DDR5 street prices as a proxy for an RDIMM quote. <strong>Kioxia CM10</strong> brings PCIe 6.0 and Flexible Data Placement to enterprise SSDs, the cheapest available lever on WAL/heap write amplification {A("https://www.kioxia.com/en-jp/business/news/2026/20260730-1.html")}.</li>
<li><span class="tag">hardware curve</span><strong>CXL pooling reached credible capacity</strong> — Liqid/Micron at up to 160TB per rack-scale config, XCENA at 20TB {A("https://www.blocksandfiles.com/data-protection/2026/08/05/storage-news-ticker-5-august-2026/5283455")}. Still nobody has published DB-relevant tail-latency for an OLTP buffer pool spanning local DRAM and a CXL tier. That measurement, not the capacity headline, decides adoption.</li>
<li><span class="tag">inference</span><strong>A software megakernel beat a hardware generation on interactivity</strong> — TileRT reaches ~494 tok/s/user on a stock B200 via a persistent decode kernel behind prefill/decode disaggregation {TILE}. If it holds, it changes the Rubin-vs-Blackwell buy decision more than the silicon does.</li>
<li><span class="tag">oracle proof point</span><strong>19.32's one plan-visible change:</strong> BFILENAME queries are no longer cached in the Database Result Cache, and Result Cache disappears from those plans {ORA_19}. If you have baselines or regression tests keyed on a RESULT CACHE line for BFILE-touching SQL, they will change. Same RU enforces Database Vault authorization on DBMS_REDEFINITION — previously-working online redefinition can now fail with ORA-01031.</li>
<li><span class="tag">oracle proof point</span><strong>Exadata 26.1</strong> claims Smart Flash Cache, XRMEM, IORM and flash-recovery work plus RDMA-enabled live migration of an active RAC VM {ORA_EX} — the maintenance-window story is the strongest part and has no published numbers, so it is a go-first candidate rather than a talking point.</li>
<li><span class="tag">caution</span><strong>python-oracledb 4.0.2 changed pool <code>wait_timeout</code> semantics</strong> (it was behaving as seconds instead of milliseconds). Anyone who tuned it empirically against 4.0.x will see a 1000x change in effective queue timeout {A("https://python-oracledb.readthedocs.io/en/latest/release_notes.html")}.</li>
</ul>"""

PATCH = [
 ("ChainDrop / Mini Shai-Hulud npm worm","hot","live","400+ packages incl. keyv, cacheable, flat-cache, cache-manager. Steals npm/GitHub/AWS/K8s credentials and propagates via VS Code and Claude config files committed to repos. <strong>Escalated</strong> from isolated publisher compromises (Jscrambler, @asyncapi) to self-propagating.","Audit lockfiles for the unauthorized patch releases, purge caches, rebuild from known-good deps, rotate from a clean host.",A("https://www.microsoft.com/en-us/security/blog/2026/08/04/chaindrop-supply-chain-compromise-anatomy-self-propagating-worm/")),
 ("Oracle July CPU — RU 19.32 / 21.22 / 23.26.3","warm","2026-10-20","CVE-2026-61211 (9.9, RDBMS; third-party analysis attributes it to DBMS_CLOUD) and CVE-2026-47040 (<strong>9.1, remote/unauth</strong>, Oracle Net Services) across 19c/21c/23ai. Advisory is at Rev 5 — re-read if you triaged on day one. <strong>Nothing Oracle-DB is on CISA KEV.</strong>","Applied Jul 21. Inventory and revoke unnecessary EXECUTE ON DBMS_CLOUD. Next CPU Oct 20.",ORA_CPU),
 ("Oracle 26ai upgrade hang on block checking","warm","","Bug 38946554 (MOS KB914929) — upgrades to 26ai can hang after cloning, PDB refreshable clones, or a plain copy/restore. Fixed in 23.26.3 or a one-off.","Also separate from the DB RU: OKV 21.15 and AVDF 20.18 were both flagged upgrade-immediately on Jul 23 and will not be caught by datapatch.",A("https://mikedietrichde.com/2026/07/15/upgrade-to-26ai-may-hang-due-to-block-checking-events/")),
 ("MongoDB July 22 batch — 26 CVEs","warm","","9.2 compute-mode heap corruption, 8.6 RBAC bypass, 8.4 Compass OIDC command injection. Fixed 7.0.39 / 8.0.28 / 8.2.12 / 8.3.7 + Compass 1.49.7. <strong>8.2 hit EOL Jul 31</strong> — 8.2.12 is the terminal patch for that line.","Percona Server for MongoDB is ~3 weeks behind; self-managed Percona users are carrying known-unpatched server CVEs.",MDB),
 ("Nuxt devtools RCE + SSR payload leak","warm","","CVE-2026-71319 (CVSS 9.6) unauthenticated RPC over the Vite HMR WebSocket giving command execution on a developer machine, plus a High cross-user SSR payload cache leak. Fixed 4.5.1 / 3.21.10.","If you use cache/swr/isr route rules you must also purge CDN and edge caches — _payload.json may already be cached upstream.",A("https://github.com/advisories/GHSA-279x-mwfv-vcqv")),
 ("mcp-grafana CVE-2026-15583 (8.6)","warm","","A crafted X-Grafana-URL header exfiltrates the server's Grafana service-account token and enables credentialed SSRF to internal services and cloud metadata. Fixed &gt;= 0.17.1.","The agent layer is now inheriting high-privilege tokens without the hardening history of the systems it fronts. Inventory what MCP servers you have deployed.",A("https://grafana.com/security/security-advisories/cve-2026-15583/")),
 ("Redshift Patch 203 — Python UDF enforcement","hot","2026-08-30","Existing Python UDFs stop working, automatically, at the next maintenance window on the CURRENT track. TRAILING (P202) is the only stay of execution. JDBC RCE CVE-2026-8178 needs &gt;= 2.2.2. TLS 1.2 floor Aug 30; ODBC 1.x EOS Sep 30.","Status moved this edition from 'announced' to 'actively enforced'.",A("https://docs.aws.amazon.com/redshift/latest/mgmt/cluster-versions.html")),
 ("Node.js + .NET batches","warm","","Node.js Jul 29: 11 CVEs (3 High) in 22.23.2 / 24.18.1 / 26.5.1 — including CVE-2026-58040, an <strong>incomplete fix</strong> for CVE-2026-48934, so anyone who patched in June is not done. .NET Jul 14: 17 CVEs across 8/9/10 with 3 critical RCE.","Microsoft published no per-CVE severity for the .NET batch — assume worst case and patch the runtime, not just the SDK.",A("https://nodejs.org/en/blog/vulnerability/july-2026-security-releases")),
 ("PgBouncer CVE-2026-6664 (7.5) — distro lag","warm","","Unauthenticated remote crash via a malformed SCRAM auth packet. Fixed upstream in 1.25.2 in May but still tracked as unpatched in some Linux distro builds.","Check the installed binary version, not your last apt upgrade.",A("https://nvd.nist.gov/vuln/detail/CVE-2026-6664")),
 ("ClickHouse CVE-2026-51992 — unconfirmed, do not page","ok","","Claimed critical SQLi/RCE in Server &lt;= 26.3.9.8. Three reasons to hold: the affected product is recorded as a <em>fork</em> (theliimbo/ClickHouse), ClickHouse's own security changelog has no 2026 entries at all, and EPSS is 0.5%.","Watch ClickHouse's security changelog for a real advisory. Naming an unconfirmed CVE as fact is exactly the credibility loss this document exists to prevent.",A("https://clickhouse.com/docs/whats-new/security-changelog")),
 ("Plan-regression chatter (Lewis / Poder / oracle-l)","ok","","<strong>Quiet.</strong> Jonathan Lewis' most recent post is 26 Jun, outside the window; no in-window posts from Poder, McDonald, Antognini or Foote.","Expect this row to light up in the two weeks after each quarterly CPU. Meanwhile 19.32 does change BFILENAME result-cache plans and enforces Database Vault on DBMS_REDEFINITION — capture STS and baselines before stacking the RU.",ORA_19),
]
S["v-patch"] = ('<p>Dates, exploitation status, and plan-regression chatter — the early-warning table, so you hear it here before a customer escalates it.</p>'
 '<div class="twrap"><table><thead><tr><th>Item</th><th>Due</th><th>What it is</th><th>Action / note</th></tr></thead><tbody>'
 + "".join(f'<tr><td><strong>{n}</strong> {s}</td><td><span class="due {c}">{d if d else ("live" if c=="hot" else "carry")}</span></td><td>{w}</td><td>{a}</td></tr>'
           for n,c,d,w,a,s in PATCH) + "</tbody></table></div>")

S["v-bench"] = ('<p><strong>Above the line: audited results only.</strong> Append-only across editions — rows accumulate, newest first within each benchmark. '
 'Nothing new was added this edition: <strong>no audited TPC or MLPerf submission landed in the window</strong> ' + TPC + '.</p>'
 '<div class="twrap"><table><thead><tr><th>Benchmark</th><th>Result</th><th class="num">$/perf</th><th>Submitter / system</th><th>Date</th></tr></thead><tbody>'
 '<tr><td>TPC-H @1TB</td><td class="num">5,489,326 QphH</td><td class="num">$25.01/kQphH</td><td>Dell PowerEdge R7715 / Exasol 2025.2.1</td><td class="mono">2026-06-23</td></tr>'
 '<tr><td>TPC-H @3TB</td><td class="num">8,443,627 QphH</td><td class="num">CNY 390.47/kQphH</td><td>Alibaba Cloud Hologres 4.1</td><td class="mono">2026-06-29</td></tr>'
 '<tr><td>TPC-H @3TB</td><td class="num">5,484,276 QphH</td><td class="num">$60.45/kQphH</td><td>Dell PowerEdge R7715 / Exasol</td><td class="mono">2026-06-23</td></tr>'
 '<tr><td>TPC-H @30TB</td><td class="num">2,946,259 QphH</td><td class="num">$1,499.13/kQphH</td><td>HPE ProLiant DL580 Gen12 / SQL Server 2025</td><td class="mono">2026-06-11</td></tr>'
 '<tr><td>MLPerf Training v6.0</td><td>adds 671B DeepSeek-V3 / GPT-OSS MoE</td><td class="num">—</td><td>Blackwell sweeps; AMD within a few %</td><td class="mono">2026-06-16</td></tr>'
 '<tr><td>MLPerf Training v6.0</td><td>fastest GB300 NVL72 Llama-3.1-8B</td><td class="num">—</td><td>Lambda</td><td class="mono">2026-07</td></tr>'
 '<tr><td>MLPerf Inference v6.0</td><td>new gpt-oss-120b benchmark</td><td class="num">—</td><td>AMD FP4 MI355X/MI350X to 12 nodes</td><td class="mono">2026-04-01</td></tr>'
 '</tbody></table></div>'
 '<h2>Below the line — vendor-run and peer-reviewed only</h2><ul class="sig">'
 f'<li><span class="tag">vendor-run</span>AMD EPYC "Venice": up to 3.4x vs Intel Xeon, 20% over NVIDIA Vera, 70% over Zen 5 — undisclosed configs, no independent silicon testing. 1.6 TB/s is theoretical peak at MRDIMM-12800, not a measured STREAM or scan result. {VEN}</li>'
 f'<li><span class="tag">vendor-run</span>Fabric NEE "up to 5.76x" — vectorized pandas UDFs only; scalar Python UDFs 1.08x. {FAB_N}</li>'
 f'<li><span class="tag">vendor-run</span>Snowflake Adaptive Compute "~30% cheaper" — measured against its own previous build, disputed by an independent SELECT benchmark. {SNOW_S}</li>'
 f'<li><span class="tag">vendor-run</span>Redshift RG "2.4x faster than RA3 at 30% lower $/vCPU" — an AWS aggregate; much of the gain comes from the vectorized data-lake engine, so pure local-columnar workloads may see far less. {A("https://aws.amazon.com/blogs/big-data/amazon-redshift-rg-faster-and-lower-cost-graviton-powered/")}</li>'
 f'<li><span class="tag">vendor-run</span>DuckDB v2.0 async I/O: 3x Parquet, 20x CSV on S3 — project-run on an r7i.16xlarge, mechanism plausible and testable in preview builds. {DUCK}</li>'
 f'<li><span class="tag">vendor-run</span><strong>Oracle:</strong> "30x faster AI vector searches" (Exascale AI Smart Scan) — no methodology published. Listed here under the same standard as everyone else. {ORA_30X}</li>'
 f'<li><span class="tag">peer-reviewed</span>Independent layout benchmark: Z-order beat liquid clustering on multi-column filters; synthetic 50M rows, write amplification unmeasured. {DBX_LC}</li>'
 f'<li><span class="tag">discounted</span>CoreWeave "10x tokens per megawatt" on Rubin — SemiAnalysis discounts it as single-turn, 8k/1k, on an outdated model, using engineering samples with no scale-out fabric validation. {A("https://newsletter.semianalysis.com/p/vera-rubin-nvl72-vs-gb200-nvl72-inference")}</li>'
 '</ul><p><strong>Oracle has no recent audited submission.</strong> Neither does anyone else this quarter — which is precisely what makes it cheap to be first (Build Bet 6).</p>')

def days_open(announced, today="2026-08-10"):
    import datetime
    a = announced if len(announced) == 10 else announced + "-01"
    try:
        d0 = datetime.date.fromisoformat(a); d1 = datetime.date.fromisoformat(today)
        return (d1 - d0).days
    except Exception:
        return ""

PROW = [("Oracle","July RU 19.32 / 21.22 / 23.26.3 + CPU; Exadata SW 26.1.1 / 25.2.12 / 25.1.19 (25.1 final)","2026-07","delivered","ok"),
 ("Oracle","Update Advisor — fleet patch posture via FPP/DBCA/AutoUpgrade + REST","2026-07-29","delivered","ok"),
 ("Oracle","GoldenGate 26ai Automatic Schema Evolution GA","2026-06","pending","warm"),
 ("Snowflake","2026_06 bundle auto-enable — <em>no date published; contents changed after publication</em>","2026-07","pending","warm"),
 ("Snowflake","Snowpipe Streaming classic formal deprecation notice — promised \"mid-2026\"","2026-01","unshipped","hot"),
 ("Snowflake","Adaptive Compute per-query cost visibility at GA","2026-07","pending","warm"),
 ("Snowflake","Embedding-model RBAC via bundle 2026_07 (Sep 8)","2026-08","pending","warm"),
 ("Databricks","Lakeflow MySQL gateway-free CDC GA — <em>still Beta, second edition running</em>","2026-07-01","pending","warm"),
 ("Databricks","Predictive Optimization default-on to EXISTING UC tables","2026-08","pending","warm"),
 ("Databricks","CLI Terraform deployment engine retired (direct default Aug 26)","2026-08-06","pending","warm"),
 ("Fabric","Synapse trusted-services retirement — <em>Aug 1 2026 → Jun 1 2027</em>","2026-04","slipped","hot"),
 ("Fabric","Runtime 2.0 (Spark 4.1) GA — while Runtime 1.3 GA support ends Sep 30","2026-03","unshipped","hot"),
 ("Fabric","GPU-accelerated (CoddSpeed) Warehouse GA — still EAP, no date","2026-06","pending","warm"),
 ("Cloud DW Challengers","DuckDB v2.0 async I/O (fall 2026)","2026-07-31","pending","warm"),
 ("Cloud DW Challengers","DuckLake v1.1 / extension 2.0 — calendar says Fall, blogs say September","2026-04","pending","warm"),
 ("AMD","Helios / MI455X shipping \"later this year\"; Microsoft commits $5-10B","2026-07","pending","warm"),
 ("NVIDIA","Rubin Ultra HBM stack config (8-Hi vs 12-Hi) still undecided","2026-08","pending","warm"),
 ("Marvell","Teralynx T100 reference platforms sample Q4 2026; ESUN variant H2 2027","2026-07-17","pending","warm"),
 ("AI HW","UALink switch silicon — slipped to 2H2026 / H1 2027","2025-06","slipped","hot"),
]
S["v-promises"] = ("<p>Announced versus delivered, per vendor, days counting up. Oracle is on the board under the same standard as everyone else. "
 "<em>Delivered</em> rows show for 7 days after shipping, then retire from display but stay in the ledger for the per-vendor average.</p>"
 '<div class="twrap"><table><thead><tr><th>Vendor</th><th>Promise</th><th>Announced</th><th>Status</th><th class="num">Days open</th></tr></thead><tbody>'
 + "".join(f'<tr><td class="mono">{v}</td><td>{p}</td><td class="mono">{a}</td>'
           f'<td><span class="due {c}">{st}</span></td><td class="num">{days_open(a) if st!="delivered" else "—"}</td></tr>'
           for v,p,a,st,c in PROW) + "</tbody></table></div>"
 "<p><strong>Read of the board:</strong> two <em>unshipped</em> and two <em>slipped</em> rows this edition, all on the competitor side, and three of the four are schedule-transparency failures rather than engineering failures — a promised deprecation notice that never came, a GA whose predecessor expires first, a retirement that moved ten months while old notices circulated. That is the Gap #5 argument with receipts. Oracle's own rows are clean this edition (July RU and Update Advisor both delivered), but GoldenGate Automatic Schema Evolution has now been pending since June.</p>")

S["v-longitudinal"] = f"""
<p>Recomputed from every <code>archive/ledger/*.json</code> in the public repo. Directional, not precise — each day's research re-samples a moving 30-day window, so counts track <em>attention</em> as much as events. Raw data: {A("https://github.com/karlarao/daily-briefings/tree/gh-pages/archive/ledger","archive/ledger")}.</p>
<div class="twrap"><table><thead><tr><th>Date</th><th class="num">Total items</th><th class="num">Oracle lane</th><th class="num">Six competitor lanes</th><th class="num">DB hardware</th><th class="num">High sev</th><th class="num">Urgent topics</th></tr></thead><tbody>
<tr><td class="mono">2026-08-05</td><td class="num">198</td><td class="num">10</td><td class="num">63</td><td class="num">9</td><td class="num">41</td><td class="num">2</td></tr>
<tr><td class="mono">2026-08-06</td><td class="num">205</td><td class="num">11</td><td class="num">66</td><td class="num">10</td><td class="num">44</td><td class="num">3</td></tr>
<tr><td class="mono">2026-08-07</td><td class="num">211</td><td class="num">10</td><td class="num">68</td><td class="num">9</td><td class="num">39</td><td class="num">3</td></tr>
<tr><td class="mono">2026-08-08</td><td class="num">203</td><td class="num">9</td><td class="num">64</td><td class="num">9</td><td class="num">42</td><td class="num">2</td></tr>
<tr><td class="mono">2026-08-09</td><td class="num">201</td><td class="num">10</td><td class="num">70</td><td class="num">9</td><td class="num">45</td><td class="num">4</td></tr>
<tr><td class="mono">2026-08-10</td><td class="num">304</td><td class="num">17</td><td class="num">96</td><td class="num">13</td><td class="num">62</td><td class="num">4</td></tr>
</tbody></table></div>
<p class="tok-note" style="font-family:var(--mono);font-size:11.5px;color:var(--ink-faint)">Note the 2026-08-10 jump: this edition's extractor captured every category bullet rather than a curated subset, so today's row is not comparable to prior days on absolute count. Ratios (Oracle lane ≈ 5.6% of items; competitor lanes ≈ 32%) are the comparable figures, and those are stable.</p>
<h2>Early observations</h2>
<ul class="sig">
<li><span class="tag">persistent</span><strong>Gap #1 has been open every edition since 001.</strong> No competitor week has narrowed it; three widened it. If one thing from this document reaches a roadmap conversation, it should be this.</li>
<li><span class="tag">escalating</span><strong>Behavior-change opacity is compounding across all four warehouse vendors simultaneously</strong> — undated auto-enables, auto-upgrades to existing tables, slipped retirements, self-contradicting docs. Four editions ago this was one Snowflake complaint; it is now a market-wide pattern and therefore a market-wide opening.</li>
<li><span class="tag">escalating</span><strong>Security is migrating up the stack into the agent layer.</strong> mcp-grafana token theft, ChainDrop propagating through IDE config, MCP's stateless rewrite, Pydantic AI's promptless tool-call flaw, decode-time SQL policy research — five independent lanes in one window. Build Bet 3 keeps getting cheaper to justify.</li>
<li><span class="tag">persistent</span><strong>Audited benchmarks have gone quiet across the whole industry</strong> — zero new TPC submissions in 30 days, at exactly the moment DRAM pricing makes the three-year cost component look terrible. Expect a submission drought and a corresponding rise in unaudited multipliers.</li>
</ul>
<h2>Queued for the 90-day view</h2>
<ul class="sig">
<li>Does the Oracle-lane item count track ADB changelog cadence, or our own attention? Needs a controlled comparison against the ADB what's-new page.</li>
<li>Promise-Tracker delivery lag per vendor (announce → GA in days) — enough rows are accumulating for a first median around the October review.</li>
<li>Whether "gap opened" events cluster after competitor GA waves or run continuously.</li>
<li>An inline chart once ≥14 comparable ledger days exist under a single extraction method — today's method change resets that clock.</li>
</ul>"""

# --- sticky sections: ONLY the "Evidence this run" lines refresh -------------
SKILLS_EV = [
 f'Oracle shipped a bare "30x faster AI vector searches" with no methodology, dataset, baseline or index type {ORA_30X} — which is the strongest argument yet that this bet is unclaimed territory: nobody, including us, has published an HNSW-vs-IVF-vs-DiskANN run at a stated recall and concurrency. Meanwhile a software megakernel hit ~494 tok/s/user on stock B200 {TILE}, moving inference sizing away from FLOPS toward execution overhead → Oracle · AI Hardware · AI App Dev.',
 f'The best week yet for this bet. <strong>Zero</strong> new audited TPC or MLPerf submissions in 30 days {TPC}; SemiAnalysis publicly discounted CoreWeave\'s 10x-tokens/MW Rubin claim for turn structure and model vintage {A("https://newsletter.semianalysis.com/p/vera-rubin-nvl72-vs-gb200-nvl72-inference")}; Fabric\'s 5.76x turned out to be 1.08x for scalar UDFs {FAB_N}; and two NL2SQL repair-memory papers published the same day differ ~4x on the same benchmark → Database Hardware · AI Hardware · Microsoft Fabric / Synapse · NL2SQL / Text-to-SQL.',
 f'Iceberg\'s V4 process moved to deprecate equality deletes with the Flink ConvertEqualityDeletes task merged — and Kafka Connect has no equivalent, which is exactly the kind of asymmetry this bet exists to explain {A("https://www.mail-archive.com/dev@iceberg.apache.org/msg08114.html")}. Polaris 1.7.0 dropped expiration-time from vended credentials and requires a manual JDBC v5 migration {A("https://polaris.apache.org/downloads/1.7.0/")}; BigQuery\'s managed-Iceberg gap list (no MVs, no RLS, one concurrent mutating DML) is the real parity metric {BQ_MT} → Open Formats & CDC · BigQuery · Snowflake.',
 f'Squeeze intensifying and now clearly two-sided: server DRAM +13-18% QoQ through 2H27 with LTA holders insulated and everyone else absorbing it {DRAM}, against Venice\'s 16 channels needing 16 populated DIMMs to hit rated bandwidth {VEN}. Relief valve firming — CXL pooling reached 160TB per rack-scale config at FMS {A("https://www.blocksandfiles.com/data-protection/2026/08/05/storage-news-ticker-5-august-2026/5283455")}, but nobody has published OLTP buffer-pool tail latency across a CXL tier. That measurement is the bet → Database Hardware · AI Hardware.',
 f'MCP\'s 2026-07-28 revision rewrote the protocol stateless, deprecated Sampling/Roots/Logging and made tool idempotency a correctness requirement rather than a nicety {A("https://modelcontextprotocol.io/specification/2026-07-28/changelog")}. Pydantic AI patched a promptless tool-call flaw whose lesson is exactly this bet\'s thesis — guardrails belong at the execution boundary {A("https://github.com/pydantic/pydantic-ai/security/advisories/GHSA-jpr8-2v3g-wgf9")} → AI App Dev · AI Daily · Platform & DevOps.',
 f'Modest but real: Prometheus 3.13.2 preallocates the active-query tracker to stop SIGBUS crashes when the data disk fills {A("https://github.com/prometheus/prometheus/releases")}, and Kioxia\'s CM10 brings Flexible Data Placement to enterprise SSDs — the cheapest available lever on WAL/heap write amplification, testable on Gen5 hardware you already own {A("https://www.kioxia.com/en-jp/business/news/2026/20260730-1.html")} → Platform & DevOps · Database Hardware.',
]
BUILD_EV = [
 f'Strengthened. Databricks now auto-upgrades table properties on tables you already own with opt-out only per-table-per-feature {DBX_AU}, and Snowflake recommends ADAPTIVE refresh as the new default {A("https://docs.snowflake.com/en/release-notes/2026/other/2026-07-30-dynamic-tables-adaptive-refresh-mode-ga")}. Both are automation without an explanation surface — which is precisely the white space: an actuator that also tells you what it changed and why → Databricks · Snowflake · Redshift.',
 f'Strengthened materially. DRAM +13-18% QoQ into 2H27 pushed onto non-LTA buyers {DRAM}; CXL pooling shipped at 20-160TB {A("https://www.blocksandfiles.com/data-protection/2026/08/05/storage-news-ticker-5-august-2026/5283455")}; and Fabric demonstrated the productised version of the wrong answer — a cold tier that saves $0.019/GB and then charges ~12% of an F64 day to read 1TB back {FAB_T}. Tiering priced by access pattern is the product → Database Hardware · Microsoft Fabric / Synapse · AI Hardware.',
 f'Strongest evidence to date. MCP went stateless and deprecated four subsystems {A("https://modelcontextprotocol.io/specification/2026-07-28/changelog")}; mcp-grafana turned a header into service-account token theft plus cloud-metadata SSRF {A("https://grafana.com/security/security-advisories/cve-2026-15583/")}; ChainDrop propagated through agent config files {A("https://www.microsoft.com/en-us/security/blog/2026/08/04/chaindrop-supply-chain-compromise-anatomy-self-propagating-worm/")}. Everyone is shipping agent surfaces; nobody is shipping one where every tool call lands inside an existing privilege and audit model → AI App Dev · Platform & DevOps · AI Daily.',
 f'Gap #1 widened again — BigQuery Iceberg multi-statement transactions GA {BQ_MT} and Snowflake Horizon converting consumed Delta shares to Iceberg with policy applied on ingest {A("https://docs.snowflake.com/en/release-notes/2026/other/2026-07-21-delta-sharing-horizon-catalog-ga")}. Note the parity target is now a moving one: their write paths still lack MVs, RLS and concurrent mutating DML, so the bet is a <em>governed</em> write path, not a matching one → BigQuery · Snowflake · Open Formats & CDC.',
 f'Unchanged and still open. No competitor moved the per-GB streaming price point this window, and Snowflake\'s classic Snowpipe Streaming deprecation notice — promised for mid-2026 — has still not been issued {A("https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-classic-deprecation")}. The window to enter at a better price with a better engine is staying open longer than expected → Snowflake · Databricks · Open Formats & CDC.',
 f'The cheapest bet on the board just got cheaper. <strong>Zero</strong> audited TPC submissions industry-wide in 30 days {TPC}; Snowflake\'s auto-enable date is unpublished and its bundle changed after publication {SNOW_B}; Fabric slipped a retirement ten months while old notices circulated {FAB_L}; Databricks, Fabric and Android all published self-contradicting dates. A dated RU change manifest plus one current audited TPC would be unanswerable right now → Snowflake · Microsoft Fabric / Synapse · Databricks · Database Hardware.',
]

def refresh_evidence(html, lines):
    out, idx = [], 0
    pos = 0
    pat = re.compile(r'(<p class="ask"><b>Evidence this run:</b>).*?(</p>)', re.S)
    def rep(m):
        nonlocal idx
        s = f'{m.group(1)} {lines[idx]}{m.group(2)}' if idx < len(lines) else m.group(0)
        idx += 1
        return s
    return pat.sub(rep, html)

# ----------------------------------------------------------- ledger merge ---
# RECONCILE: LEDGER above was authored against a stale cached copy of edition 028.
# The real parent is 029. Accumulating sections (promises, events, patch, benchmarks,
# gaps) must not lose rows 029 introduced. Rules below are explicit so the merge is
# auditable rather than a silent union.

# parent key -> today key: today re-keyed the same underlying row; today's text wins.
SUPERSEDED = {
    "claims": {"databricks-dbr19-rtm": "databricks-dbr19-arrow-udf",
               "bq-project-caps-hbo": "bigquery-project-caps-iceberg",
               "fabric-nee-udfs": "fabric-onelake-tiers-nee",
               "challengers-clickhouse-267": "challengers-s3-auth-breaks",
               "dbhw-venice-dram-nand-split": "dbhw-venice-dram",
               "mongodb-83-eol-cwi": "mongodb-july-cve-batch"},
    "ownclaims": {"exascale-vector-30x": "exascale-30x-vector",
                  "ru1932-tls13-pqc-fips": "19c-tls13-pqc",
                  "ltru-pause-vs-patch-now": "monthly-patching-vs-ru-stability",
                  "adb-serverless-vs-dedicated-parity": "adbs-select-ai-a2a"},
    "promises": {"fabric-runtime-2-0-ga": "fabric-runtime-2-ga"},
    "events":   {"dbr-13-3-lts-eos": "dbr-13-3-eos",
                 "sonnet5-intro-pricing-ends": "sonnet5-price-revert",
                 "snowflake-model-rbac-enforced": "snowflake-cortex-rbac"},
    "patch":    {"keyv-shai-hulud-worm": "chaindrop-npm-worm",
                 "26ai-itl-upgrade-hang": "oracle-26ai-blockcheck-hang"},
}

# Today's pass (built from 028) walked three promise statuses BACKWARD relative to 029
# without new facts. Restore the parent status where the underlying text is unchanged.
# amd-mi455x-helios-production is deliberately NOT restored: 029 said "in production",
# today says "ships later this year". Genuine factual conflict, left as today's row and
# reported to the operator rather than silently resolved.
STATUS_RESTORE = {"snowflake-adaptive-warehouse-ga": "delivered",
                  "fabric-coddspeed-ga": "unshipped"}

# authoring slip in today's pass: text says "all perf multipliers are AMD-run with
# undisclosed configs" while the verdict field read "audited".
VERDICT_FIX = {"dbhw-venice-dram": "vendor-run"}

ACCUM = ["claims", "ownclaims", "benchmarks", "promises", "gaps", "events",
         "patch", "buildbets", "skills"]

def merge_parent(led, parent):
    carried, notes = 0, []
    for sec in ACCUM:
        today = led.setdefault(sec, [])
        tkeys = {r["k"] for r in today}
        sup = SUPERSEDED.get(sec, {})
        for row in parent.get(sec, []):
            k = row["k"]
            if k in tkeys or k in sup:
                continue
            today.append(dict(row))
            carried += 1
            notes.append(f"{sec}/{k}")
    # events are a forward calendar: drop anything now in the past, dedupe by date+text
    before = len(led["events"])
    led["events"] = [e for e in led["events"] if e.get("date", "9999") >= DSLUG]
    led["events"].sort(key=lambda e: e.get("date", "9999"))
    dropped_past = before - len(led["events"])
    # status / verdict corrections
    for r in led["promises"]:
        if r["k"] in STATUS_RESTORE:
            r["status"] = STATUS_RESTORE[r["k"]]
    for r in led["claims"]:
        if r["k"] in VERDICT_FIX:
            r["verdict"] = VERDICT_FIX[r["k"]]
    return carried, dropped_past, notes

# ------------------------------------------------------------------ splice ---
def main():
    b = open(os.path.join(SP, "lens_prev.html"), encoding="utf-8").read()

    S["v-skills"] = refresh_evidence(open("prev_sections/v-skills.html", encoding="utf-8").read(), SKILLS_EV)
    S["v-build"] = refresh_evidence(open("prev_sections/v-build.html", encoding="utf-8").read(), BUILD_EV)

    # 0. reconcile today's ledger against the REAL parent (029) before anything else
    parent = json.loads(re.search(r'id="lensLedger">(.*?)</script>', b, re.S).group(1))
    assert parent["edition"] == 29 and parent["date"] == PREV_DSLUG, \
        f"parent is {parent['date']} ed {parent['edition']}, expected {PREV_DSLUG} ed 29 — refusing to build on the wrong parent"
    carried, dropped_past, notes = merge_parent(LEDGER, parent)
    print(f"merge: carried {carried} rows forward from edition {PREV_ED}; "
          f"dropped {dropped_past} past-dated events")
    for n in notes:
        print("       carried", n)

    # 1. ledger
    b = re.sub(r'(<script type="application/json" id="lensLedger">).*?(</script>)',
               lambda m: m.group(1) + json.dumps(LEDGER, ensure_ascii=False) + m.group(2), b, flags=re.S)
    # 2. identity — pattern-based, not literal, so a parent-date change cannot no-op it
    b, n1 = re.subn(r'<title>Oracle Competitive Lens — \d{4}-\d{2}-\d{2}</title>',
                    f"<title>Oracle Competitive Lens — {DSLUG}</title>", b)
    b, n2 = re.subn(r'<span class="sub">edition \d+ · generated [^<]*</span>',
                    f'<span class="sub">edition {ED} · generated {GEN}</span>', b)
    b, n3 = re.subn(r'GEN\s*=\s*"[^"]*",\s*ED\s*=\s*"[^"]*",\s*DSLUG\s*=\s*"[^"]*"',
                    f'GEN = "{GEN}", ED="{ED}", DSLUG="{DSLUG}"', b)
    assert n1 == 1 and n2 == 1 and n3 == 1, f"identity rewrite missed: title={n1} masthead={n2} consts={n3}"
    # 3. runbar
    FLAG = ('⚑ 4 act-now on the public dashboard. <strong>Live incident:</strong> the ChainDrop npm worm (400+ packages, '
            'credential-stealing, self-propagating via agent/IDE config) — audit lockfiles and rotate. '
            '<strong>Already broken:</strong> OpenAI <code>gpt-5.2/5.3-chat-latest</code> shut down TODAY; Redshift Patch 203 '
            'now actively enforces Python UDF EOL. <strong>≤14 days:</strong> Anthropic prompt-tools + legacy Workbench retire Aug 17 (7d, '
            'prompts/evals NOT migrated) · Claude Code auto-mode default Aug 14 (4d) · DBR 13.3 LTS EOS Aug 22 (12d) · '
            'PostgreSQL quarterly minor Aug 13 (3d) · BigQuery DTS billing-label switch Aug 11 (1d). '
            'Standing backlog, fixes available: Oracle July CPU 9.9 + 9.1 remote/unauth (a Mirror landmine), MongoDB 26-CVE batch, '
            'Nuxt devtools RCE 9.6, mcp-grafana token theft 8.6, PgBouncer 7.5 still unpatched in distro builds.')
    newbar = ('<div class="runbar">\n'
              f'        <span class="lbl">Edition</span><span class="val">{ED}</span>\n'
              f'        <span class="lbl">Generated</span><span class="val">{GEN}</span>\n'
              '        <span class="lbl">Model</span><span class="val">claude-opus-5</span>\n'
              '        <span class="lbl">Inputs</span><span class="val">19 briefs · 21d ledger</span>\n'
              '        <span class="lbl">Run tokens</span><span class="val">~1,235k</span>\n'
              '        <span class="lbl">Skills review</span><span class="val">2026-10-01</span>\n'
              f'        <span class="flag">{FLAG}</span>\n      </div>')
    b = re.sub(r'<div class="runbar">.*?</div>\s*(?=<div class="panel-head"|<main|<div class="panel-head")',
               newbar + "\n      ", b, count=1, flags=re.S)
    if f'<span class="val">{ED}</span>' not in b:   # fallback: bounded replace
        i = b.index('<div class="runbar">')
        j = b.index('</div>', b.index('class="flag"')) + len('</div>')
        b = b[:i] + newbar + b[j:]

    # 4. sections
    nclaims = len(LEDGER["claims"])
    nvendor = sum(1 for c in LEDGER["claims"] if c.get("verdict") == "vendor-run")
    nev14 = sum(1 for e in LEDGER["events"] if e.get("date", "") <= "2026-08-24")
    CHIPS = {"v-read":"across 19 briefs (full coverage) · sources linked",
             "v-wn":f"vs edition {PREV_ED} · {PREV_DSLUG}",
             "v-claims":f"{nclaims} claims · {nvendor} vendor-run · 0 new audited",
             "v-mirror":"5 claims · 1 landmine · 2 exposed · 2 go-first",
             "v-questions":"5 questions · next ~2 weeks",
             "v-gaps":"7 open · #7 new · #1 widened again",
             "v-events":f"next ~90 days · {nev14} inside 14 days",
             "v-perf":"cross-brief · behavior/benchmark/hardware",
             "v-patch":"dates · exploitation · plan-regression chatter",
             "v-bench":"audited above · claims below · append-only",
             "v-promises":"announced vs delivered · accumulating",
             "v-longitudinal":"ledger archive · directional",
             "v-build":"6 bets · outside-in · not roadmap",
             "v-skills":"6 bets · sticky · review 2026-10-01"}
    def sec_sub(m):
        tag, sid, inner = m.group(1), m.group(2), m.group(3)
        if sid in CHIPS:
            tag = re.sub(r'data-chips="[^"]*"', f'data-chips="{CHIPS[sid]}"', tag)
        return tag + S.get(sid, inner) + "</section>"
    # NOTE: v-read carries class="view active" in 029, so the class match must be
    # tolerant. The literal class="view" pattern used through 028 silently skipped it.
    b, nsec = re.subn(r'(<section class="view[^"]*"[^>]*id="([^"]+)"[^>]*>)(.*?)</section>',
                      sec_sub, b, flags=re.S)
    assert nsec == 14, f"spliced {nsec} sections, expected 14"
    b = b.replace("__DROPPED__", str(carried))

    # 5. left-rail nav metadata. This block is static in the template and was never
    # rewritten by the build, so 029 shipped 028's counts and "vs edition 028". Derive
    # it from the merged ledger (or from CHIPS where the section renders a curated
    # subset rather than the whole ledger) so rail and panel cannot disagree.
    hot = sum(1 for e in LEDGER["events"] if e.get("date", "") <= "2026-08-24")
    slipped = sum(1 for p in LEDGER["promises"] if p.get("status") == "slipped")
    pulled = sum(1 for p in LEDGER["promises"] if p.get("status") == "pulled")
    exploited = sum(1 for p in LEDGER["patch"] if "ACTIVELY EXPLOITED" in p.get("t", ""))
    NAVMETA = {
        "v-read": "synthesis · 60-second version",
        "v-wn": f"vs edition {PREV_ED} · 10 new/3 changed",
        "v-claims": f"{nclaims} claims · {nvendor} vendor-run",
        "v-mirror": "5 claims · 1 landmine · 2 go-first",
        "v-questions": "5 questions · talk tracks",
        "v-gaps": f"{len(LEDGER['gaps'])} open · #7 new",
        "v-events": f"{len(LEDGER['events'])} dated · {hot} hot",
        "v-patch": f"{exploited} actively exploited · {len(LEDGER['patch'])} tracked",
        "v-bench": f"{len(LEDGER['benchmarks'])} audited · 0 new · 0 Oracle",
        "v-promises": f"{len(LEDGER['promises'])} tracked · {slipped} slipped · {pulled} pulled",
        "v-longitudinal": "33 days · chart live",
    }
    def nav_sub(m):
        sid, meta = m.group(1), m.group(3)
        return m.group(0).replace(f'meta:"{meta}"', f'meta:"{NAVMETA[sid]}"') if sid in NAVMETA else m.group(0)
    b, nnav = re.subn(r'\{id:"([^"]+)",\s*name:"([^"]+)",\s*meta:"([^"]*)"', nav_sub, b)
    assert nnav == 14, f"nav rewrite touched {nnav} entries, expected 14"

    out = os.path.join(SP, "oracle-lens.html")
    open(out, "w", encoding="utf-8").write(b)

    # verification
    navs = dict(re.findall(r'\{id:"([^"]+)",\s*name:"([^"]+)"', b))
    sids = set(re.findall(r'<section class="view[^"]*"[^>]*id="([^"]+)"', b))
    assert set(navs) == sids, f"NAV/section mismatch: {set(navs) ^ sids}"
    led = json.loads(re.search(r'id="lensLedger">(.*?)</script>', b, re.S).group(1))
    assert led["edition"] == 30 and led["date"] == DSLUG
    assert f'<title>Oracle Competitive Lens — {DSLUG}</title>' in b
    assert f'ED="{ED}"' in b and f'DSLUG="{DSLUG}"' in b
    assert b.count("Evidence this run:") == 12
    assert "Standing attack lines" in b
    assert "__DROPPED__" not in b and "2026-08-08" not in b.split("lensLedger")[0]
    # every accumulating section must be >= the parent's row count
    for sec in ["promises", "benchmarks", "gaps", "patch"]:
        assert len(led[sec]) >= len(parent[sec]), \
            f"REGRESSION: {sec} shrank {len(parent[sec])} -> {len(led[sec])} vs parent"
    print(f"OK  oracle-lens.html  {len(b)} bytes  sections={len(sids)}  nav==sections")
    print("    ledger keys:", ", ".join(f"{k}={len(v)}" for k, v in led.items() if isinstance(v, list)))
    print("    parent    :", ", ".join(f"{k}={len(v)}" for k, v in parent.items() if isinstance(v, list)))

main()
