
cd "$(git rev-parse --show-toplevel)" && git fetch origin && git checkout gh-pages && git pull --ff-only origin gh-pages && touch .nojekyll && git config user.name "briefings-bot" && git config user.email "briefings-bot@users.noreply.github.com"

================================================================================
DAILY BRIEFINGS — SINGLE-ROUTINE PIPELINE (GitHub Pages variant)
Paste this ENTIRE file as the prompt of ONE scheduled routine.
It is self-contained: it carries all 18 briefs AND the dashboard template.
This variant publishes to GitHub Pages via `git push` (repo karlarao/daily-briefings)
instead of a Claude artifact URL. It runs attached to that repo, already cloned &
authenticated by the GitHub App. Pages serves the ROOT of the gh-pages branch, so
this routine commits to gh-pages and writes ONLY claude.html — the static
index.html landing page and the Codex-side codex.html (both at the gh-pages root)
are NOT touched.
================================================================================

================================================================================
HOW THIS WORKS + HOW TO MAINTAIN IT   (read me first)
================================================================================

WORKFLOW (one scheduled run, top to bottom):

                       ┌───────────────────────────────────────────────┐
   COLD START          │ Ephemeral VM — NOTHING persists between runs.  │
   (scheduled)  ─────▶ │ This prompt is the ONLY durable thing. Every   │
                       │ file below is rebuilt from scratch each run.   │
                       └───────────────────────────────────────────────┘
                                        │
   Step 0  BOOTSTRAP ....... cd repo root, git fetch, checkout gh-pages, pull,
                                        │       touch .nojekyll, set git author
   Step 1  NOW ............. run `date` → full "YYYY-MM-DD HH:MM TZ"
                                        │
   Step 2  SECTIONS ........ build the 18 topics, all {status:"pending"}
                                        │
   Step 3/4  THE LOOP  — once per topic, daily/high-churn first:
   ┌────────────────────────────────────────────────────────────────────┐
   │  a. research ....... ordinary web search, last 30d (AI Daily 24–48h)│
   │  b. format ......... markdown in the OUTPUT FORMAT skeleton         │
   │  c. classify ....... status = ok | slow | urgent                   │
   │                      (+ flag_reason ONLY when urgent)              │
   │  d. rebuild ........ claude.html = template + new DATA block   │
   │  e. keep local ..... do NOT push per-topic (single end-of-run push) │
   └────────────────────────────────────────────────────────────────────┘
              │  repeat 18×                            ▲
              └────────────────────────────────────────┘
                                        │  (loop done)
   Step 5  FINALIZE ........ set generated + summary → git add/commit/push ONCE
                                        │
   Step 5b VERIFY .......... confirm the Pages DEPLOYMENT for the pushed commit
                                        │       succeeded; re-trigger (empty commit) if
                                        │       it failed/stalled, up to 3×
   Step 6  NOTIFY .......... ONE push IF push failed OR Pages deploy failed,
                                        │       ELSE IF any status=="urgent" (else: silent)
                                        ▼
                                     ( done )

   Per-topic data model (one object per topic):
     { id, name, group, cadence, freq, updated, status, md, flag_reason }
     the run CHANGES only ──▶  updated · status · md · flag_reason
     id / name / group / cadence / freq  stay identical to the template defaults.

--------------------------------------------------------------------------------
THE "TWO PLACES" RULE  (the one thing to get right when editing)
--------------------------------------------------------------------------------
Every topic lives in TWO places that MUST stay in sync:

  (1) "THE 18 BRIEFS" list below  → the RESEARCH spec
      carries: id · name · group · cadence  +  Scope  +  Priorities
  (2) APPENDIX A template DATA block → the RENDER spec
      carries: id · name · group · cadence · freq  +  default fields

  id + name + group + cadence MUST be byte-identical in both places, or the
  sidebar/label and the brief won't line up. `freq` (1–3 meter dots) and the
  Scope/Priorities text each live in only ONE place — see below.

--------------------------------------------------------------------------------
HOW TO ADD A NEW TOPIC
--------------------------------------------------------------------------------
  1. Choose a unique lowercase `id` (no spaces), e.g. "streaming".
  2. Add a numbered entry to "THE 18 BRIEFS" with:  id · "Name" · group · cadence
     then a Scope: line and a Priorities: line (copy an existing entry's shape).
  3. Add ONE section object to the template DATA block (copy an existing line,
     change id/name/group/cadence/freq). Rules:
       - `group` MUST equal one of the three GROUPS strings exactly
         ("Data layer", "Application layer", "AI, Research & Hardware"), OR add a
         new group (see next section).
       - `freq` = 1 | 2 | 3  → the churn meter, display-only: sets both the bars AND
         the label the dashboard shows (3=▮▮▮ "firehose", 2=▮▮ "steady", 1=▮ "quiet"
         — how newsy the lane typically is). It does NOT affect what runs — all
         topics run every run. The `cadence` field still exists in the data for
         contract stability but is no longer displayed anywhere.
       - keep the defaults: updated:"", status:"pending", md:"", flag_reason:"".
  4. If it overlaps an existing topic's lane, add a line to DEDUP BOUNDARY so they
     don't double-report.
  5. Cosmetic-only: the literal "18" appears in the header, "WHAT THIS ROUTINE
     DOES", the template kicker, and the summary example. The code counts topics
     dynamically (B.sections.length), so nothing breaks if you forget — but update
     them so the copy stays honest.

HOW TO ADD A NEW SIDEBAR GROUP (category):
  - Add the exact new group string to BOTH: the `GROUPS` array in the template
    <script> (order there = order of sidebar sections) AND each topic's `group`.

--------------------------------------------------------------------------------
HOW TO EDIT / REMOVE A TOPIC
--------------------------------------------------------------------------------
  - Change Scope or Priorities only .......... edit ONLY the "THE 18 BRIEFS" entry.
  - Rename / move group / change cadence ..... edit BOTH places (must match).
  - Change freq (churn bars + label) ......... edit ONLY the template DATA object.
  - Remove a topic ........................... delete it from BOTH places.

--------------------------------------------------------------------------------
NOTES FOR A FUTURE LLM RUNNING THIS  (intent > literal instructions)
--------------------------------------------------------------------------------
  - This prompt is model-agnostic. If you are a newer/different model, follow the
    INTENT, not the exact tool names:
      • "publish" = write the self-contained HTML to claude.html and `git push`
        it (ONE push at the end of the run; see PUBLISH TARGET), THEN verify the
        GitHub Pages DEPLOYMENT for that commit actually succeeded (see step 5b) —
        a green `git push` is NOT a green publish. If the push is impossible, or the
        Pages deploy keeps failing after re-triggers (auth/network/Pages outage),
        send the single notification saying so — that failure IS the news.
      • "web search" = ordinary search. Do NOT use deep-research (token budget).
      • Parallelize the 18 briefs if your harness supports subagents / parallel
        tool calls; otherwise run them sequentially. Either way, keep the local
        claude.html current after each topic so a crash still leaves the
        latest built state staged for the single end-of-run push.
  - Keep the APPENDIX A template's <style> and <script> effectively verbatim.
    ONLY the DATA block between the two markers changes each run. If you ever
    improve the template, preserve the DATA contract (same field names) or update
    "BUILDING THE DASHBOARD" to match — the render code reads those exact fields.
  - JSON-encode `md` and `flag_reason` (escape quotes, backslashes, newlines) so
    the file stays valid JS.
  - Hold the calibration: 0–3 "urgent" on a normal day. Urgent = drop-what-you're-
    doing (actively-exploited/unpatched CVE on a stack a reader runs, or a hard
    deadline within ~14 days). "Something happened" is NOT urgent.
  - Verify volatile facts (versions, model IDs, pricing) against primary docs, never
    memory — this matters MORE as your training cutoff ages relative to run date.
  - Don't narrate. The dashboard + the single notification are the whole deliverable.

================================================================================

## WHAT THIS ROUTINE DOES (each scheduled run)

You are an automated engineering-news briefing generator. In one run you:
1. Produce up to 18 short briefings (each is a web-search digest for the past 30 days).
2. Render them into ONE self-contained HTML dashboard.
3. Publish that dashboard to GitHub Pages by committing it as claude.html at the
   root of the gh-pages branch and pushing ONCE at the end of the run (one Pages
   build per run), THEN verifying the Pages deployment actually succeeded.
4. Send ONE push notification at the very end — if the git push failed OR the Pages
   deployment failed, or (if the publish succeeded) only if something urgent (an
   act-now CVE, a breaking/behavior change, or a hard deadline) turned up.

Nobody is watching the run. The dashboard + the single notification ARE the
deliverable. Do not narrate; just produce and publish.

## PUBLISH TARGET — GITHUB PAGES (git push)

This routine runs attached to karlarao/daily-briefings, already cloned &
authenticated (GitHub App). Pages is served from the ROOT of the gh-pages branch.
Publish by committing the built dashboard onto gh-pages and pushing:
  • Branch: gh-pages   (Pages source = gh-pages / root)
  • Build file: claude.html   (at the gh-pages root — do NOT touch index.html or codex.html)
  • Ensure .nojekyll exists at the root   (Pages serves HTML verbatim)
  • Push ONCE at the end of the run (one Pages build per run)
  • Publishing is NOT complete when `git push` succeeds — it is complete only when the
    Pages DEPLOYMENT for that commit succeeds. The GitHub Pages "build and deployment"
    step fails/stalls intermittently and leaves the live site on the PREVIOUS build.
    VERIFY the deployment from the GitHub side (see RUN PROCEDURE step 5b) — do NOT
    verify by fetching the *.github.io URL, because the run VM's egress policy blocks
    *.github.io. If the deploy failed or stalled, re-trigger with an empty commit; a
    persistent deploy failure IS the news → notify.
Public URL (after Pages enabled): https://karlarao.github.io/daily-briefings/claude.html
If git push fails (auth/network), send one notification saying so — that failure IS the news.

## RUN PROCEDURE

0. BOOTSTRAP. The VM boots with the repo cloned & GitHub-App-authenticated. Prepare it:
     cd "$(git rev-parse --show-toplevel)" || exit 1
     git fetch origin && git checkout gh-pages && git pull --ff-only origin gh-pages
     touch .nojekyll
     git config user.name "briefings-bot"
     git config user.email "briefings-bot@users.noreply.github.com"
   (Pages serves the gh-pages root; index.html + codex.html already live there and
    are left untouched. No settings.json / Artifact permission — we publish via git.)

1. Establish the current timestamp in US EASTERN time by running
   `TZ="America/New_York" date '+%Y-%m-%d %H:%M %Z'` — capture date, time, AND
   timezone as NOW in the form "YYYY-MM-DD HH:MM TZ" (e.g. "2026-07-04 14:47 EDT").
   ALWAYS render NOW in Eastern (America/New_York), NOT UTC — the zone abbreviation
   will read EST in winter and EDT during daylight saving; either is correct, just
   keep it Eastern. The run VM's clock is UTC, so you MUST pass TZ="America/New_York"
   (do not use a bare `date`, which would emit UTC).
   There may be MULTIPLE runs per day, so ALWAYS use the full timestamp (never just
   the date) for `generated` and for each section's `updated`, so the dashboard's
   "Last run" indicator shows the Eastern time of day, not only the date.

2. Build an in-memory `sections` array = the 18 topics in "THE 18 BRIEFS" below,
   in that order, each starting {status:"pending", md:"", updated:"", flag_reason:""}.

3. Run ALL 18 topics every run (the cadence gate is OFF by request). Note: the AI
   Daily brief uses a 24–48h window; every other brief uses the past 30 days.

4. FOR EACH topic, in listed order (daily/high-churn first):
   a. Do the brief: follow the topic's Scope + Priorities and the SHARED RULES.
      Use web search. Cover the past 30 days (AI Daily: past 24–48h). No deep-research.
   b. Format the result as markdown in the exact OUTPUT FORMAT (see SHARED RULES).
   c. Set:
        section.md      = the markdown you produced
        section.updated = NOW   (full "YYYY-MM-DD HH:MM TZ" timestamp)
        section.status  = "urgent"  ONLY IF the brief has an ACT-NOW item: an
                                     actively-exploited or unpatched CVE relevant to
                                     a stack a reader actually runs, OR a hard
                                     deadline within ~14 days. Most topics, most
                                     days, are NOT urgent.
                        = "slow"     if it was a genuine slow day (little/nothing);
                        = "ok"       otherwise — notable news, but nothing act-now.
        section.flag_reason = "" by default. When (and ONLY when) you set
                              status="urgent", also set flag_reason to a SHORT
                              markdown string (1–3 sentences) that NAMES the specific
                              act-now item, states the concrete action, and points to
                              the category below where the full detail lives — e.g.
                              "**CopyFail (CVE-2026-31431)** is in CISA KEV with a
                              validated EKS/GKE PoC. **Do now:** patch node kernels +
                              bump runc/containerd. See **Security / CVEs** below."
                              It renders as a red "why this is flagged" banner at the
                              top of the flagged brief so the reader sees WHAT is
                              flagged without hunting through the whole brief.
                              JSON-encode it like `md`. Leave it "" for non-urgent.
      CALIBRATION: expect 0–3 "urgent" across ALL topics on a normal day. If you
      flagged more than ~3, you are over-flagging — re-examine and downgrade the
      borderline ones to "ok". "Something happened" is NOT urgent; "drop what you're
      doing" is. Do not manufacture urgency to fill the flag.
   d. Rebuild claude.html locally (see "BUILDING THE DASHBOARD").
   e. Do NOT push per-topic. Keep the local file current so a crash still leaves the
      latest built state staged for the single end-of-run push.

5. After the loop: set generated=NOW (full "YYYY-MM-DD HH:MM TZ" timestamp) + a
   one-line summary INCLUDING TOKEN SPEND (e.g. "18 topics · 2 flagged · 1 slow ·
   ~830k tokens"). Token accounting: as each research subagent completes, your
   harness reports its token usage in the completion result — keep a running total
   across all 18 and round to the nearest ~5k for the summary. It's a volume gauge
   (subagent tokens only; orchestration overhead not included), not a bill. If your
   harness does not report per-agent usage, OMIT the token segment entirely —
   never estimate it. Then rebuild claude.html once more and publish with a
   SINGLE push (retry on network error, backoff 2/4/8/16s):
     git add claude.html .nojekyll
     git commit -m "briefings ${NOW}" || echo "no changes"
     git push origin gh-pages
     DEPLOY_SHA=$(git rev-parse HEAD)   # remember which commit must go live
   Treat a non-zero `git push` exit (after all retries) as PUSH FAILED for the
   notification step below.

5b. VERIFY THE PAGES DEPLOYMENT (do NOT trust push success alone).
   A push landing on gh-pages does NOT mean the page updated — the GitHub Pages
   "pages build and deployment" step fails/stalls intermittently and leaves the live
   site serving the PREVIOUS build. You also CANNOT verify by fetching the public
   URL: the run VM's egress policy blocks *.github.io (host_not_allowed). Verify from
   the GitHub side:
     - Poll the "pages build and deployment" workflow run whose head_sha == DEPLOY_SHA
       (via the GitHub API/MCP: list workflow runs, event=dynamic, branch=gh-pages;
       match head_sha; read status/conclusion), or the Pages deployment/build-status
       API, until it reaches a terminal state (allow ≈ up to 3 minutes; poll every
       ~20–30s, do not busy-loop).
     - If conclusion == "success" → the page is live; done.
     - If conclusion == "failure", OR it is still "queued"/"in_progress" after ~3 min
       (stuck) → RE-TRIGGER by pushing an empty commit, then re-verify:
         git commit --allow-empty -m "redeploy: re-trigger Pages build (transient deploy failure)"
         git push origin gh-pages
         DEPLOY_SHA=$(git rev-parse HEAD)
       Repeat this re-trigger + verify up to 3 times total.
   If it still fails after 3 re-triggers, treat that as PAGES DEPLOY FAILED for the
   notification step below. If you have NO way to query deploy status this run (e.g.
   GitHub API/MCP unavailable in a headless run), do not assume success — say so in
   the notification.

6. NOTIFICATION (exactly one, at the end):
   - If git push FAILED (after retries) OR the Pages deployment FAILED (after
     re-triggers): send ONE push — "Pages publish failed: <reason>" (name whether it
     was the push or the Pages deploy, and the last DEPLOY_SHA). That failure IS the news.
   - Else if ANY section.status === "urgent": send ONE push. Lead sentence = the single
     most important item across all briefs; then list each urgent topic with its
     headline + why it matters + the deadline/severity. Wrap in <routine_summary>…</routine_summary>.
   - Otherwise: send NOTHING. A quiet, healthy run is not worth a notification.

## BUILDING THE DASHBOARD (claude.html)

Write claude.html as EXACTLY the template in "APPENDIX A — DASHBOARD
TEMPLATE", with ONE change: replace everything between the two markers

    /* ===== DATA — the routine replaces this whole block each run ===== */
    ...
    /* ===== end DATA ===== */

with a single assignment:

    window.BRIEFINGS = {
      generated: "YYYY-MM-DD HH:MM TZ",     // full timestamp — includes time of day
      summary:   "one-line run summary",
      sections: [ /* the 18 section objects, same order & fields as the template */ ]
    };

Each section object = {id, name, group, cadence, freq, updated, status, md, flag_reason}.
`updated` is also a full "YYYY-MM-DD HH:MM TZ" timestamp.
Keep id/name/group/cadence/freq identical to the template's defaults; only
updated/status/md/flag_reason change per run. `md` and `flag_reason` are JavaScript
strings — JSON-encode them (escape quotes, backslashes, and newlines) so the file
stays valid JS. `flag_reason` is "" unless status is "urgent". Do not alter any HTML
or the <script> logic below the DATA block.

================================================================================
SHARED RULES  (apply to EVERY brief)
================================================================================

- Don't use deep-research — it consumes too many tokens. Use ordinary web search.
- Cover the past 30 days (exception: AI Daily uses the past 24–48 hours).
- Lens: a working software/performance engineer. Skip theory without application,
  skip marketing, skip keynote/thought-leadership fluff, skip anything that doesn't
  change how someone designs, operates, tunes, secures, or ships.
- Prefer changelogs, release notes, specs, VLDB/SIGMOD papers, and independent
  engineering blogs/postmortems over press releases and analyst reports.
- Flag every CVE / security finding with severity (CVSS if available) and whether a
  fix/patched version exists.
- Note when two sources contradict each other on a performance/cost claim.
- Slow day? Say so plainly and set status "slow". Never manufacture stories.
- Verify volatile facts (version numbers, model IDs, pricing) against primary docs;
  don't rely on memory.

OUTPUT FORMAT for each brief (markdown, this exact skeleton):

    **TL;DR** — 1–2 sentences: the one thing to know today.

    ## <Category>
    - **Headline** — 1–2 sentences on what it means for your work.
      [source](url) · [changelog/docs](url)
    (repeat categories; skip empty ones — don't pad)

    ## Worth your weekend
    - 1–3 things to test / benchmark / read deeply.

    ## Heads up
    - deprecations, EOL/《deadline》 dates, breaking changes.

    ## Signals worth watching
    - 2–3 trends / benchmark contradictions / architectural shifts.

    ## Filtered out
    - items you skipped, with links (brief).

DEDUP BOUNDARY (so topics don't repeat each other):
- The "Open Formats & CDC" brief OWNS Iceberg/Delta/Hudi/Paimon, catalogs
  (Polaris/Unity/Glue/S3 Tables), and CDC/zero-ETL (Debezium etc.). Every vendor
  brief DEFERS those stories to it and only mentions a format/CDC item when it
  directly changes that engine's own behavior.
- "OLTP & Distributed SQL" owns the transactional/serving side; the warehouse
  briefs own OLAP.
- The DATABASE briefs (the whole "Data layer" group) collectively replace a single
  generic "databases" sweep — do NOT also write a catch-all DB brief.
- "AI Daily" OWNS frontier-model releases/pricing/benchmarks, coding agents & dev
  tools (Cursor/Copilot/Claude Code/Cline/Zed/etc.), AI security incidents, AI
  policy/regulation, and AI industry moves. "AI App Dev" OWNS the builder's view —
  how you USE models (API primitives, MCP, agent frameworks, RAG, eval, serving
  cost). Rule of thumb: a model RELEASE or PRICE change → AI Daily; how to CALL the
  API / build with it → AI App Dev. Each defers the other's lane.
- "Database Hardware" OWNS server CPUs, commodity memory (DDR/LPDDR) & the DRAM/NAND
  market, CXL pooling/tiering, NVMe/storage, storage/replication interconnect, GPU-for-DB
  acceleration (RAPIDS/HeavyDB/Bodo), DPU/SmartNIC offload, Apple Silicon for embedded DB,
  and hardware-driven TPC/TPCx price-performance results. "AI Hardware" OWNS GPUs/
  accelerators, HBM, inference-serving hardware patterns, training interconnect/fabrics,
  cloud GPU availability/pricing, and XPUs. Draw the line by reader-intent: would you act
  by changing HARDWARE-for-a-DB (→ Database Hardware) or by sizing an INFERENCE/TRAINING
  cluster (→ AI Hardware)? Commodity DRAM/DDR/CXL → Database Hardware; HBM → AI Hardware.
- Benchmarks: audited TPC/TPCx results and $/QphH·$/tpmC moves DRIVEN BY a hardware/
  server/storage config belong to "Database Hardware". Engine-attributed benchmark claims
  (ClickBench, vendor TPC-H/DS marketing, "Nx faster") stay in the relevant engine brief.
  Test: hardware-driven → Database Hardware; engine-driven → engine brief.
- Interconnect: "AI Hardware" owns cluster/collective fabrics (NVLink, training-scale
  InfiniBand/Ultra Ethernet/RoCE, GPUDirect, KV-cache transfer). "Database Hardware" owns
  RDMA/low-latency networking as applied to DBs (NVMe-oF, RDMA replication/remote-memory,
  DPU/SmartNIC offload, kernel-bypass NICs). A new raw transport generation → AI Hardware
  carries the spec/gen, Database Hardware carries the DB-latency/disaggregation implication.
  Test: wiring a GPU cluster → AI Hardware; DB replicate/serve/disaggregate → Database Hardware.
- AI Daily and AI App Dev DEFER hardware to "AI Hardware" (mention only if it directly
  changes what you can ship today).
- "NL2SQL / Text-to-SQL" owns Text-to-SQL research/benchmarks/tooling; the other AI
  briefs defer NL2SQL-specific papers to it.

================================================================================
CADENCE GATE  (DISABLED — kept for reference only; default is run all 18)
================================================================================

Not in use: every topic runs every run. (If you ever re-enable mixed cadence, run a
topic only on its days by TODAY's weekday; skipped topics keep their prior state.)

================================================================================
THE 18 BRIEFS  (id · name · scope · priorities)
================================================================================

1. id=oltp · "OLTP & Distributed SQL" · group=Data layer · Daily
   Scope: PostgreSQL (+extensions), MySQL/MariaDB/Percona, distributed SQL
   (CockroachDB, TiDB, YugabyteDB, Spanner, Vitess/PlanetScale), managed
   Postgres/MySQL (Aurora/RDS, AlloyDB, Cloud SQL, Azure DB, Neon, Supabase),
   SQLite/libSQL. Owns the transactional side.
   Priorities: 1) engine releases/lifecycle (core vs managed rollout) 2) planner/
   index/EXPLAIN/vacuum/partitioning changes 3) replication/HA/consensus, failover,
   sharding rebalancing 4) MVCC/isolation/locks/WAL/storage-engine 5) vector in OLTP
   (pgvector/pgvectorscale, HNSW/IVF/DiskANN) 6) online DDL & migration tooling
   (pgroll, gh-ost, Flyway/Liquibase/Atlas/Alembic) 7) CVEs/auth(SCRAM/TLS/IAM)/
   poolers 8) pooling/backup/PITR/observability(pg_stat_statements/auto_explain)
   9) VLDB/SIGMOD w/ shipping impact 10) ORMs/drivers/IDEs/monitoring.

2. id=formats · "Open Formats & CDC" · group=Data layer · Daily · CROSS-CUTTING OWNER
   Scope: table formats (Iceberg, Delta, Hudi, Paimon, DuckLake), catalogs (Polaris/
   Open Catalog, Unity Catalog OSS, Glue/S3 Tables, Gravitino, Lakekeeper, Nessie),
   file formats (Parquet/ORC/Arrow/Lance), CDC/ingestion (Debezium, Kafka Connect,
   Flink CDC, Fivetran, Airbyte, Estuary, GoldenGate, DMS, Datastream, dlt).
   Priorities: 1) format spec/releases (Iceberg v3, Delta protocol; deletion vectors,
   row lineage, VARIANT, geo) 2) catalog releases & REST-catalog spec, credential
   vending, the catalog war 3) cross-engine interop matrix (write-once/read-anywhere,
   UniForm) — highest value 4) CDC/ingestion releases: apply throughput, exactly-once,
   schema-evolution, backfill, WAL/slot gotchas 5) streaming-to-table & compaction,
   MoR vs CoW 6) query perf over formats (manifest scaling, pruning, data-skipping)
   7) governance/security + CVEs 8) format/catalog conversion & migration (XTable)
   9) research w/ shipping impact 10) client libs (pyiceberg, delta-rs, iceberg-rust,
   ADBC), dbt/SQLMesh onto formats.

3. id=oracle · "Oracle" · group=Data layer · Weekly
   Scope: Oracle DB 19c/21c/23ai, Exadata, Autonomous AI Database (Serverless &
   Dedicated), RAC, ASM, Data Guard, GoldenGate, RMAN, ORDS/APEX, Multitenant,
   OCI DB; HeatWave/TimesTen if relevant.
   ALWAYS FETCH these authoritative Autonomous AI Database changelog pages every run
   and surface any feature dated within the past 30 days (link the specific feature;
   note its date). These are the source of truth for ADB feature rollouts:
     - ADB Dedicated — new feature announcements:
       https://docs.oracle.com/en/cloud/paas/autonomous-database/dedicated/adbaa/new-feature-announcements.html
     - ADB Dedicated — earlier announcements (for the tail of the 30-day window):
       https://docs.oracle.com/en/cloud/paas/autonomous-database/dedicated/adbaa/new-feature-announcements-1.html
     - ADB Serverless — what's new:
       https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/whats-new-adwc.html
     - ADB Serverless — previous feature announcements (for the tail of the window):
       https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/previous-feature-announcements.html
   Give ADB rollouts their own bullet group in the Oracle brief, and distinguish
   Serverless vs. Dedicated (a feature in one is not automatically in the other).
   ALSO TRACK the official Oracle Database blog every run — https://blogs.oracle.com/database/
   — with SPECIAL ATTENTION to PERFORMANCE posts (optimizer/CBO, In-Memory, Exadata
   Smart Scan, AWR/ASH/SQL Monitor tuning, real-time stats, parallel query, sharding/
   RAC perf, AI Vector Search performance). Surface any post published within the past
   30 days that has engineer-actionable perf/tuning content, and give performance items
   their own bullet (a "## Performance" category, or a clearly-labeled bullet) linking the
   specific blog post. Skip pure marketing/announcement posts with no tuning takeaway.
   Priorities: 1) RU/RUR, quarterly CPU, interim patches, 23ai increments, Exadata
   system SW (patch #s, MOS notes, anything that changes optimizer/params/breaks SQL)
   2) CBO changes across RUs, hints, optimizer_features_enable, SPM, real-time stats,
   Automatic Indexing, plan regressions after patch, In-Memory 3) RAC/Cache Fusion,
   sharding, App Continuity/TAF, Data Guard FSFO/role transitions 4) GoldenGate,
   logminer/integrated capture, XStream, Data Pump, Debezium Oracle 5) In-Memory,
   Exadata Smart Scan/storage indexes, HeatWave, external-table/Iceberg 6) AI Vector
   Search (VECTOR, HNSW/IVF/DiskANN), Select AI, JSON Duality 7) Multitenant/
   partitioning/flashback/online redef/EBR/blockchain tables, 23ai SQL, SQLcl/Liquibase
   8) CPU/CVE, TDE/wallet/OKV, Database Vault, audit, licensing 9) RMAN/ZDLRA/ASM/
   pooling(UCP/DRCP)/AWR/ASH/SQL Monitor/OCI pricing 10) SQLDev/SQLcl/VS Code,
   python-oracledb/node-oracledb/ODP.NET/JDBC. Prefer Poder/Lewis/McDonald/Bayliss/
   Pachot/oracle-base. Note MOS-only sources by note ID. Distinguish 19c/21c/23ai and
   on-prem/Exadata/Autonomous.

4. id=snowflake · "Snowflake" · group=Data layer · 2–3×/week
   Scope: SQL engine + micro-partitions, warehouses (std/Gen2/adaptive/serverless),
   Snowpark + Container Services, Cortex (LLM/Search/Analyst), Iceberg + Polaris,
   Dynamic Tables, Unistore/Hybrid Tables, Streams & Tasks, Snowpipe, Horizon.
   Priorities: 1) releases & BEHAVIOR-CHANGE BUNDLES (enablement/opt-out dates,
   preview→GA) — anything that changes results/defaults/breaks SQL 2) warehouse
   perf & credit cost (Gen2/adaptive, QAS, search optimization, auto-clustering,
   MVs, caches) 3) Iceberg/Polaris/open-catalog (DEFER deep format news to `formats`)
   4) Snowpipe Streaming, Dynamic Tables refresh/lag, CDC into SF 5) Cortex/VECTOR/
   hybrid search, credit/SQL-semantic changes 6) Unistore/Hybrid Tables 7) Horizon
   governance, cloning/time-travel, migration tooling 8) CVEs, MFA/auth enforcement
   9) credit/pricing, warehouse sizing, ACCOUNT_USAGE 10) drivers/CLI/Snowpark ML/
   Native Apps/dbt-snowflake. Distinguish preview vs GA, edition, per-cloud.

5. id=databricks · "Databricks" · group=Data layer · 2–3×/week
   Scope: DBR/Photon/Spark, Unity Catalog, Delta Lake, Iceberg/UniForm, DBSQL
   serverless, Lakeflow/DLT, Lakebase, Mosaic AI (Model Serving/Vector Search),
   Genie/AI-BI, Liquid Clustering, Predictive Optimization.
   Priorities: 1) DBR (+LTS)/Photon/DBSQL/DLT/UC/Delta OSS releases — deprecations,
   result/default changes 2) Photon coverage, Spark AQE, Liquid Clustering vs
   Z-order, deletion vectors/MoR, Predictive Optimization, caches (flag non-indep
   benchmarks) 3) Delta protocol & Iceberg interop (DEFER deep format news to
   `formats`) 4) Structured Streaming, Lakeflow Connect, CDC (Auto Loader/CDF/DLT)
   5) Unity Catalog governance/federation/Delta Sharing 6) Mosaic AI Vector Search,
   AI functions in SQL 7) Lakebase/online tables 8) CVEs/credential handling 9) DBU
   pricing/SKU, serverless vs classic, autoscaling, system tables 10) connectors/
   dbt-databricks/CLI/SDKs/Asset Bundles. Distinguish OSS vs proprietary, classic vs
   serverless, note cloud (AWS/Azure/GCP).

6. id=bigquery · "BigQuery" · group=Data layer · 2×/week
   Scope: Dremel/Capacitor engine, editions & slots (on-demand vs capacity, autoscaling,
   reservations), BigLake/Iceberg/external tables, BQML + Gemini, MVs, partition/
   clustering, BI Engine, Studio, Dataform, vector search, Omni.
   Priorities: 1) weekly release notes, preview→GA, deprecations, quota/limit changes
   2) slot scheduling/autoscaling, on-demand vs capacity pricing, short-query & history-
   based opt, MV/BI Engine, pruning, bytes-scanned/slot-hours 3) storage & open formats
   (BigLake managed tables, Iceberg r/w) — DEFER deep format news to `formats` 4)
   Storage Write API, Datastream (CDC), continuous queries 5) Gemini-in-BQ, BQML,
   ML.GENERATE_TEXT, VECTOR (IVF/TreeAH) 6) column/row security, Dataplex, cross-region
   7) partition/cluster strategy, STRUCT/ARRAY/JSON, PK/FK metadata, dbt-bigquery 8)
   CVEs/CMEK/VPC-SC 9) pricing/editions, reservations, INFORMATION_SCHEMA, byte-limit
   controls 10) client libs/bigframes/bq CLI/JDBC. Distinguish preview vs GA,
   on-demand vs editions, multi-region vs regional.

7. id=redshift · "Redshift" · group=Data layer · Weekly
   Scope: Serverless (RPU) & provisioned (RA3), engine + columnar storage, Spectrum,
   zero-ETL, Redshift ML, data sharing, MVs, AQUA, concurrency scaling, auto/manual
   WLM, dist/sort keys, S3 Tables/Iceberg, Glue/Lake Formation/Athena adjacency.
   Priorities: 1) cluster/serverless releases, maintenance-track changes, deprecations
   (RPU/pricing, result/default changes) 2) RPU autoscaling/AI-scaling, concurrency
   scaling, auto-WLM, ATO (auto sort/dist), MV auto-refresh/rewrite, AQUA 3) RA3
   managed storage, dist/sort keys, Spectrum, S3 Tables/Iceberg (DEFER deep format
   news to `formats`) 4) zero-ETL (Aurora/RDS/DynamoDB→RS), streaming from Kinesis/MSK
   5) cross-cluster/account/region data sharing 6) Redshift ML/Bedrock, vector where
   avail 7) dist/sort strategy, ANALYZE, late-binding views, RLS, dbt-redshift 8)
   CVEs/KMS/IAM/RBAC 9) Serverless base-RPU & RA3 pricing, Advisor, snapshots, SYS_*
   views 10) drivers/Data API/Query Editor v2/dbt. Distinguish Serverless vs RA3, region.

8. id=fabric · "Microsoft Fabric / Synapse" · group=Data layer · Weekly
   Scope: Fabric (OneLake, Warehouse, Lakehouse/SQL endpoint, Direct Lake, Fabric
   Spark, Fabric SQL DB, RTI/Eventhouse-KQL, Data Factory, mirroring), Synapse
   (legacy SQL/Spark pools), Power BI semantic models, Delta/Iceberg in OneLake,
   F-SKU/CU economics.
   Priorities: 1) Fabric what's-new, preview→GA, Synapse deprecation/migration, SKU
   changes (CU billing, result/default changes) 2) Warehouse/SQL-endpoint engine,
   Direct Lake (+fallback to DirectQuery), Spark Native Execution Engine, V-Order, CU
   consumption/throttling 3) OneLake, Delta, Iceberg interop, shortcuts (DEFER deep
   format news to `formats`) 4) mirroring (Snowflake/Cosmos/Azure SQL/PG→Fabric),
   RTI/Eventstream/Eventhouse, Data Factory 5) Direct Lake vs Import vs DirectQuery
   6) Copilot in Fabric, vector in Eventhouse/SQL DB 7) Warehouse T-SQL surface,
   Fabric SQL DB, DACPAC/dbt-fabric 8) CVEs/Entra/private-link/Purview 9) F-SKU
   pricing, CU smoothing/throttling/bursting, Capacity Metrics 10) drivers/Fabric CLI/
   REST/Spark runtime. Prefer Chris Webb, Sandeep Pawar. Distinguish Fabric vs Synapse,
   preview vs GA, Direct Lake/Import/DirectQuery.

9. id=challengers · "Cloud DW Challengers" · group=Data layer · 2×/week
   Scope: ClickHouse/Cloud, Firebolt, StarRocks/CelerData, Doris/VeloDB, MotherDuck/
   DuckDB/DuckLake, SingleStore, Teradata VantageCloud, Databend, Dremio, Trino/
   Starburst, Pinot/StarTree, Druid/Imply, Yellowbrick.
   Priorities (group by engine, say WHICH engine each item is about): 1) engine/cloud
   releases (versions, deprecations, breaking upgrades) 2) vectorized exec/CBO/runtime-
   filter/MV/index changes — prefer ClickBench & reproducible TPC-H/DS; flag vendor
   benchmarks 3) Iceberg/Delta/Hudi r/w + catalogs + DuckLake (DEFER deep format news
   to `formats`) 4) real-time ingestion (Kafka/Pulsar/Kinesis), CDC, upsert/compaction
   5) HTAP (SingleStore/Doris/StarRocks), Pinot/Druid low-latency serving 6) vector/
   inverted indexes, hybrid search 7) partition/sort/PK-upsert/TTL, dbt adapters 8)
   CVEs 9) pricing-model shifts (separation, serverless, credits), autoscaling 10)
   drivers/dbt/cloud launches. Distinguish OSS core vs managed (ClickHouse OSS vs Cloud,
   StarRocks vs CelerData, Doris vs VeloDB, DuckDB vs MotherDuck).

10. id=appdev · "App Dev (Backend)" · group=Application layer · Daily
    Scope: server-side runtimes (Go, Rust, JVM/Kotlin, Python incl. no-GIL, Node/Deno/
    Bun, .NET), backend frameworks, data-access (ORMs/drivers/pools), APIs (REST/
    GraphQL/gRPC/tRPC/OpenAPI/protobuf), caching/messaging (Redis/Valkey, Kafka/NATS/
    RabbitMQ), observability, build/deploy. Client/driver/app side — DB engine internals
    go to the data-layer briefs.
    Priorities: 1) language/runtime releases (LTS, betas) — GC/default/flag/breaking
    changes 2) perf & concurrency (GC/allocator, async/goroutine/virtual-thread,
    profiling, pools) 3) ORMs/query builders (Prisma, Drizzle, SQLAlchemy, Hibernate,
    Ent, GORM, sqlc, jOOQ) — generated-SQL/pooling/txn changes 4) API/serialization
    (JSON/Protobuf/Avro), versioning, idempotency 5) caching/brokers, outbox, exactly-
    once 6) OpenTelemetry/tracing/profiling 7) architecture (CQRS, sagas/Temporal/
    durable execution, resilience) — battle-tested only 8) CVEs & supply chain (npm/
    PyPI/crates/Maven), auth libs 9) build/pkg mgrs (Cargo/uv/pnpm/Gradle), containers,
    testcontainers 10) framework/stdlib releases, tooling.

11. id=aiappdev · "AI App Dev" · group=Application layer · Daily · FAST-MOVING
    Scope: the BUILDER's view of LLM apps — model APIs/SDKs USAGE (Anthropic Claude,
    OpenAI, Gemini, + Llama/Mistral/DeepSeek/Qwen/open-weights), agent frameworks, MCP,
    RAG/retrieval, LLM eval/observability, inference serving (vLLM/TGI/SGLang/Ollama) +
    gateways, prompt/context engineering. Vector-STORE internals → database briefs.
    DEFER to "AI Daily": frontier-model RELEASE announcements & PRICING, coding-agent/
    dev-tool news, AI security incidents, AI policy, industry moves. DEFER hardware to
    "AI Hardware". This brief = how to USE the models, not what shipped.
    Priorities: 1) API primitives (tool use, structured outputs, caching, batch, reasoning
    modes) — flag breaking tool-call/message-format changes 2) MCP spec + servers/clients
    + transport/auth 3) agent frameworks (LangGraph, LlamaIndex, Pydantic AI, OpenAI/
    Claude Agent SDK, CrewAI, Mastra) + patterns 4) RAG (embeddings, rerankers, chunking,
    hybrid, context packing) 5) eval & observability (LLM-as-judge pitfalls, LangSmith/
    Langfuse/Braintrust/Phoenix, OTel GenAI) 6) inference/serving/cost (quantization,
    KV-cache, spec decoding, gateways: LiteLLM/OpenRouter/Portkey) 7) prompt injection/
    tool-abuse/exfil + CVEs in AI SDKs 8) applied research w/ shipping impact 9) provider
    SDK releases & tooling. VERIFY model IDs & pricing against primary docs — never memory.

12. id=frontend · "Frontend & Web Platform" · group=Application layer · Daily
    Scope: JS/TS frameworks (React/Next, Svelte/SvelteKit, Vue/Nuxt, SolidStart, Angular,
    Astro, Remix/React Router, Qwik), TS + TC39, build tools (Vite, Turbopack, esbuild,
    Rspack, Rolldown, swc), web platform (Baseline, new CSS/HTML/JS APIs, WASM, View
    Transitions), styling (Tailwind/CSS), state/data (TanStack, tRPC, Zod/Valibot),
    testing (Vitest/Playwright), Core Web Vitals.
    Priorities: 1) framework/tooling releases (stable vs RC/canary) — rendering/default/
    routing/breaking changes 2) web platform & Baseline (safe-to-ship vs behind-flag)
    3) perf & CWV (LCP/INP/CLS, bundle size, hydration/streaming/RSC) 4) rendering & data
    (SSR/SSG/ISR, RSC/Server Actions, caching, routing) 5) TypeScript + ECMAScript stage
    moves 6) Tailwind/CSS features (:has, nesting, layers, scoping), a11y 7) TanStack/
    tRPC/validation 8) CVEs & npm supply-chain incidents 9) bundlers/monorepo/pkg mgrs/
    deploy platforms (Vercel/Netlify/Cloudflare) 10) devtools/Storybook. Prefer web.dev/
    MDN/caniuse/TC39. Distinguish stable vs canary and browser-support status.

13. id=devops · "Platform & DevOps" · group=Application layer · Daily
    Scope: Kubernetes + containers (containerd, mesh, gateway), IaC (Terraform/OpenTofu,
    Pulumi, Crossplane, CDK), CI/CD (GH Actions, GitLab CI, Argo, Flux, Dagger), cloud
    compute/networking/serverless (AWS/GCP/Azure), observability infra (Prometheus,
    Grafana, OTel, Cilium/Pixie/eBPF, Loki/Tempo/Mimir), containers/build (Docker/
    BuildKit/Buildpacks), FinOps.
    Priorities: 1) K8s minor releases + KEPs, tool releases — FLAG removed K8s APIs &
    breaking manifest/pipeline/module changes 2) scheduler/autoscaling (HPA/VPA/Karpenter),
    gateway API, CSI, in-place pod resize 3) Terraform/OpenTofu divergence, Pulumi/
    Crossplane, provider/state breaking changes, policy-as-code 4) CI/CD releases, GitOps,
    progressive delivery, SLSA/signing 5) cloud compute/net (Graviton/ARM, serverless,
    EKS/GKE/AKS) — perf/availability/cost 6) OTel semantic-conventions/collector, eBPF,
    SLO tooling — cardinality/cost 7) Docker/BuildKit/distroless/registry 8) CVEs (esp.
    container-escape/K8s), secrets, SBOM/provenance 9) FinOps (pricing/instances, spot/
    commitments, OpenCost/Kubecost) 10) CNCF releases, Backstage/IDP. Distinguish GA vs
    beta/alpha (feature gates), per-cloud/distro.

14. id=mobile · "Mobile Development" · group=Application layer · Weekly
    Scope: iOS (Swift/SwiftUI/UIKit/Xcode), Android (Kotlin/Compose/Studio/AGP), cross-
    platform (React Native+Expo, Flutter/Dart, KMP), APP-STORE POLICY, mobile perf,
    CI/CD (Fastlane/EAS/Codemagic).
    Priorities: 1) iOS/Android SDK, Xcode/Studio/AGP, Swift/Kotlin, SwiftUI/Compose
    releases (beta vs stable) — API/build/breaking changes 2) APP-STORE POLICY &
    requirements — Apple/Google policy, target-SDK/API-level deadlines, privacy-manifest/
    data-safety, review rules; HARD DATES that block submission (highest consequence —
    always surface the date) 3) RN (New Architecture/Fabric/TurboModules)/Expo, Flutter/
    Dart, KMP — breaking/migration 4) SwiftUI/Compose stable APIs, UIKit/View interop
    5) startup/jank/memory/battery/app-size, baseline profiles/R8 6) OS capabilities
    (widgets, live activities, permissions), on-device ML (Core ML/ML Kit/Gemini Nano)
    7) CVEs, permission/privacy model, keychain/keystore, CocoaPods/SPM/Gradle supply
    chain 8) TestFlight/Play testing, staged rollout, OTA/code-push rules, signing 9)
    Fastlane/EAS/Xcode Cloud/Gradle build 10) profilers/testing (XCTest/Espresso/Maestro).
    Treat store-policy deadlines as first-class. Distinguish beta vs stable, iOS/Android/
    cross-platform.

15. id=aidaily · "AI Daily" · group=AI, Research & Hardware · Daily · FAST FEED (24–48h)
    Scope: the AI INDUSTRY/TOOLING view for a working engineer — frontier model releases
    & pricing, coding agents & dev tools (Claude Code, Cursor, Copilot, Cline, Aider,
    Windsurf, Zed, OpenCode), OSS AI infra (vLLM/SGLang/llama.cpp, LangChain/LlamaIndex),
    AI security/safety incidents, AI policy/regulation, notable industry moves.
    WINDOW: past 24–48 HOURS (not 30 days). Label anything older that's just now breaking.
    DEDUP: OWNS model releases/pricing/benchmarks, coding-agent & dev-tool news, AI
    policy, industry moves. DEFER "how to build with the APIs" (primitives, MCP, agents,
    RAG, eval, serving cost) to "AI App Dev". DEFER GPU/accelerator/inference-HARDWARE
    to "AI Hardware". DEFER NL2SQL-specific papers to "NL2SQL".
    Priorities: 1) frontier model releases & updates you can use — new models, capability
    jumps, context/pricing/API changes, deprecations, rate limits, system cards (Anthropic,
    OpenAI, Google DeepMind, Meta, Mistral, xAI, DeepSeek, Qwen). Real-world benchmarks
    only (SWE-bench, Terminal-Bench, Aider, LiveCodeBench, GPQA, artificialanalysis.ai) —
    skip MMLU theater 2) dev tools & coding agents (Claude Code, Cursor, Copilot, Cline,
    Aider, Windsurf, Zed, OpenCode) — features, MCP servers, IDE integrations, CLIs 3)
    infra & libraries (vLLM, SGLang, llama.cpp, LangChain, LlamaIndex, eval frameworks) —
    releases/breaking changes on GitHub 4) research w/ shipping impact (arXiv) — prompting,
    fine-tuning, RAG, agent architectures, interpretability, efficiency 5) platform/
    ecosystem shifts — cloud AI offerings, licensing, major open-weight releases 6)
    security/safety/failure modes — prompt injection, jailbreaks, supply-chain, incidents/
    postmortems, safety evals 7) policy/regulation (engineer-relevant only) — EU AI Act
    enforcement, US executive actions, state laws that change what you can ship 8) industry
    moves (filtered) — funding/M&A/partnerships only if they affect tooling/APIs/models
    9) new dev tools & packages devs are adopting (OpenCode/Pi/Claude Code/Hermes etc.).
    Prefer primary sources (changelogs, GitHub releases, lab blogs, papers); flag rumors/
    leaks as such; note when sources contradict.

16. id=nl2sql · "NL2SQL / Text-to-SQL" · group=AI, Research & Hardware · Daily
    Scope: NL2SQL / Text-to-SQL research & engineering — schema linking, query generation,
    schema annotation, error correction, agentic pipelines, RL/fine-tuning for SQL,
    long-context schemas, multi-dialect SQL, eval benchmarks, production patterns, tools.
    Priorities: 1) new arXiv papers (schema linking, generation, annotation, error
    correction, agentic pipelines, RL/fine-tuning, long-context, multi-dialect, eval) —
    only if a concrete technique an engineer can apply 2) benchmark updates (Spider, BIRD,
    LiveSQLBench, BEAVER, SQLBench, new ones) — call out the benchmark-vs-production gap
    3) production patterns & failure modes — what's actually breaking, semantic layer vs
    raw NL2SQL tradeoffs 4) tools & libraries (Vanna, DAIL-SQL, DIN-SQL, sqlcoder, etc.)
    5) techniques worth trying — prompting, RAG, schema compression, tribal-knowledge
    injection, execution-feedback loops.
    For each key paper give: title + arXiv ID, core technique (2 sentences), why it
    matters for production (not just benchmarks), link. Skip papers that only lift
    Spider/BIRD scores without a transfer story. Flag vendor-blog-only claims.

17. id=aihw · "AI Hardware" · group=AI, Research & Hardware · Daily
    Scope: accelerators & cluster hardware for LLM inference/training — GPUs/accelerators
    (NVIDIA/AMD/Intel/TPU/Trainium-Inferentia/Maia/Apple Neural Engine/Groq/Cerebras/
    Tenstorrent/SambaNova/d-Matrix/Etched), HBM memory, inference-serving hardware patterns,
    cloud GPU availability/pricing, training interconnect/fabrics, power/cooling/density,
    hardware research. Owns the "sizing an inference/training cluster" lens. Skip consumer/
    gaming unless it has a datacenter or local-inference implication (e.g. RTX for local LLM).
    Priorities: 1) GPU & accelerator releases — FLOPS, HBM capacity/BW, interconnect,
    availability (cloud vs on-prem), pricing; what changes for sizing an LLM inference
    cluster 2) HBM (HBM3E/HBM4) supply/pricing/allocation 3) inference-hardware patterns
    (spec-decoding HW, P/D disaggregation, KV-cache offload to CPU/NVMe, continuous batching)
    4) cluster/collective interconnect & scale-up/scale-out fabrics (NVLink/NVSwitch,
    training-scale InfiniBand/Ultra Ethernet/RoCE, 400/800G) — all-reduce, GPUDirect,
    KV-cache transfer 5) cloud GPU/accelerator availability
    & spot/reserved pricing shifts (AWS/GCP/Azure/Lambda/CoreWeave/Together/Fireworks) 6)
    XPUs vs merchant GPUs (Trainium/Ironwood/Maia) 7) power/cooling/density (liquid cooling,
    TOPS/watt) 8) research (Hot Chips, ISCA, MLPerf) actionable within 12 months. Prefer
    independent benchmarks (MLPerf, artificialanalysis.ai, epoch.ai) over vendor FLOPS; flag
    when FLOPS don't translate to real throughput; mark rumors/leaks vs available vs vaporware.
    DEDUP: DEFERS commodity DRAM/DDR/CXL, DB-server CPUs/NVMe, GPU-for-DB, and DB-benchmark
    (TPC) stories to "Database Hardware"; owns HBM and accelerator/cluster hardware.

18. id=dbhw · "Database Hardware" · group=Data layer · 2×/week
    Scope: hardware that changes how you size, tune, and cost a DATABASE server — server
    CPUs (EPYC/Xeon/Neoverse/Graviton/Ampere), commodity memory (DDR5/DDR6, LPDDR, CXL
    pooling/tiering) & the DRAM/NAND market, NVMe/storage (PCIe 5/6, ZNS, computational
    storage, SCM), storage/replication interconnect, GPU-for-DB acceleration (RAPIDS cuDF,
    HeavyDB, Bodo), DPU/SmartNIC offload, Apple Silicon for embedded DB (SQLite/DuckDB), and
    audited DB benchmarks (TPC/TPCx price-performance). Owns the "sizing/tuning/costing a DB
    server" lens.
    Priorities: 1) server CPU releases (cores, memory channels, PCIe lanes, AMX/AVX-512) —
    OLTP throughput, scan/analytics, CPU-side inference 2) commodity memory & the DRAM/NAND
    market — DDR5/DDR6/LPDDR pricing & availability, CXL pooling/disaggregation for in-memory
    DBs & large vector-index sizing; DB-server BOM/TCO impact 3) NVMe & storage (PCIe 6.0,
    ZNS SSD, computational storage, SCM) — DB I/O, WAL, checkpoint, index/weight loading 4)
    TPC/TPCx & price-performance ($/QphH, $/tpmC) leaderboard moves where the driver is a
    hardware/server/storage config — call out audited vs unaudited, reproducibility 5)
    RDMA & low-latency networking for DBs — RoCE/InfiniBand, NVMe-oF storage
    disaggregation, RDMA/CXL remote-memory pooling, kernel-bypass (DPDK/io_uring); DB
    commit/replication/consensus latency 6) GPU-DB acceleration (RAPIDS
    cuDF, HeavyDB, Bodo, FPGA storage engines) & DPU/SmartNIC offload 7) Apple Silicon /
    unified memory for local & embedded DB 8) cloud DB-instance hardware (Graviton/Arm DB
    instances, mem-optimized families) — perf/availability/cost 9) power/cooling where it
    changes DB rack economics 10) research (VLDB, OSDI, ASPLOS, SIGMOD) actionable within 12
    months. Prefer independent/audited benchmarks (TPC, TPC-H/DS repro) over vendor claims;
    flag vendor-run/unaudited numbers; add a "Cost/performance shift" note when a CPU/memory/
    NVMe move is big enough to revisit current DB infra.
    DEDUP: OWNS commodity DRAM/DDR/CXL, DB-server CPUs, NVMe/storage, GPU-for-DB, and
    hardware-driven TPC/TPCx price-performance. DEFERS GPU/accelerator/HBM/inference-cluster
    stories to "AI Hardware". Engine-attributed benchmark claims (ClickBench, vendor TPC-H/DS
    marketing, "Nx faster") stay in the relevant engine brief. Test: hardware-driven →
    Database Hardware; engine-driven → engine brief.

================================================================================
APPENDIX A — DASHBOARD TEMPLATE
Write this to claude.html verbatim, replacing ONLY the DATA block
(between the two markers) with the run's window.BRIEFINGS assignment.
================================================================================

Reproduce the file below verbatim as claude.html, replacing ONLY the
content between the two DATA markers with your run's window.BRIEFINGS assignment.

```html
<title>Daily Briefings — Live Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  *,*::before,*::after{box-sizing:border-box}
  :root{
    --bg:#eef1f5;--surface:#fff;--surface-2:#e7ecf1;--surface-3:#dde3ea;
    --border:#cdd6df;--border-soft:#dde3ea;
    --ink:#161d29;--ink-soft:#48566a;--ink-faint:#7b8798;
    --accent:#0f6f83;--accent-strong:#0b5566;--accent-tint:#e2f0f2;
    --amber:#b06f13;--amber-tint:#f5ebd8;
    --ok:#2f855a;--ok-dot:#16b364;--urgent:#c0392b;--slow:#7b8798;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,Roboto,sans-serif;
    --mono:ui-monospace,"SF Mono","Cascadia Code","JetBrains Mono",Menlo,Consolas,monospace;
    --shadow:0 1px 2px rgba(16,29,41,.06),0 8px 28px rgba(16,29,41,.07);
  }
  @media (prefers-color-scheme:dark){:root{
    --bg:#0c1015;--surface:#121821;--surface-2:#19212c;--surface-3:#212b38;
    --border:#2a3644;--border-soft:#1e2732;--ink:#e7edf4;--ink-soft:#a3b0c0;--ink-faint:#6d7a8b;
    --accent:#3fb6cf;--accent-strong:#63c9de;--accent-tint:#123039;--amber:#e0a94a;--amber-tint:#2c2413;
    --ok:#4cc487;--ok-dot:#4ae88f;--urgent:#f0685b;--slow:#6d7a8b;--shadow:0 1px 2px rgba(0,0,0,.4),0 10px 34px rgba(0,0,0,.45);
  }}
  :root[data-theme="light"]{
    --bg:#eef1f5;--surface:#fff;--surface-2:#e7ecf1;--surface-3:#dde3ea;
    --border:#cdd6df;--border-soft:#dde3ea;--ink:#161d29;--ink-soft:#48566a;--ink-faint:#7b8798;
    --accent:#0f6f83;--accent-strong:#0b5566;--accent-tint:#e2f0f2;--amber:#b06f13;--amber-tint:#f5ebd8;
    --ok:#2f855a;--ok-dot:#16b364;--urgent:#c0392b;--slow:#7b8798;--shadow:0 1px 2px rgba(16,29,41,.06),0 8px 28px rgba(16,29,41,.07);
  }
  :root[data-theme="dark"]{
    --bg:#0c1015;--surface:#121821;--surface-2:#19212c;--surface-3:#212b38;
    --border:#2a3644;--border-soft:#1e2732;--ink:#e7edf4;--ink-soft:#a3b0c0;--ink-faint:#6d7a8b;
    --accent:#3fb6cf;--accent-strong:#63c9de;--accent-tint:#123039;--amber:#e0a94a;--amber-tint:#2c2413;
    --ok:#4cc487;--ok-dot:#4ae88f;--urgent:#f0685b;--slow:#6d7a8b;--shadow:0 1px 2px rgba(0,0,0,.4),0 10px 34px rgba(0,0,0,.45);
  }
  html,body{margin:0;height:100%}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1240px;margin:0 auto;min-height:100%;display:flex;flex-direction:column}
  .masthead{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:20px 22px 15px;border-bottom:1px solid var(--border)}
  .brand{display:flex;flex-direction:column;gap:3px;min-width:0}
  .kicker{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);font-weight:600}
  .title{font-size:25px;font-weight:800;letter-spacing:-.02em;line-height:1;margin:0}
  .sub{font-size:12.5px;color:var(--ink-faint);font-family:var(--mono)}
  .tools{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .tbtn{font-family:var(--mono);font-size:12px;color:var(--ink-soft);background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 11px;cursor:pointer}
  .tbtn:hover{border-color:var(--accent);color:var(--ink)}
  .tbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .app{display:grid;grid-template-columns:290px 1fr;flex:1;min-height:0}
  .rail{border-right:1px solid var(--border);padding:14px 12px 40px;overflow:auto}
  .group{margin-top:14px}.group:first-child{margin-top:2px}
  .group-h{font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-faint);padding:4px 8px;display:flex;justify-content:space-between}
  .nav-item{width:100%;text-align:left;background:transparent;border:0;border-radius:8px;padding:9px 10px;margin:1px 0;cursor:pointer;display:flex;align-items:center;gap:9px;color:var(--ink);border-left:2.5px solid transparent}
  .nav-item:hover{background:var(--surface-2)}
  .nav-item.active{background:var(--surface-2);border-left-color:var(--accent)}
  .nav-item:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
  .sdot{width:8px;height:8px;border-radius:50%;background:var(--slow);flex-shrink:0}
  .sdot.ok{background:var(--ok-dot)}.sdot.urgent{background:var(--urgent)}.sdot.pending{background:var(--surface-3);border:1px solid var(--border)}.sdot.slow{background:var(--slow)}
  .nav-main{display:flex;flex-direction:column;gap:1px;min-width:0;flex:1}
  .nav-name{font-size:13.5px;font-weight:600;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .nav-item.active .nav-name{color:var(--accent)}
  .nav-meta{font-family:var(--mono);font-size:10px;color:var(--ink-faint);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .meter{display:inline-flex;gap:2px;flex-shrink:0}
  .meter i{width:4px;height:11px;border-radius:1px;background:var(--surface-3);display:block}
  .meter i.on{background:var(--ink-faint)}
  .nav-item.active .meter i.on{background:var(--accent)}
  .panel{overflow:auto;padding:22px 26px 60px}
  .runbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:11px 15px;margin-bottom:20px;box-shadow:var(--shadow)}
  .runbar .lbl{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint)}
  .runbar .val{font-family:var(--mono);font-size:12.5px;color:var(--ink);font-variant-numeric:tabular-nums}
  .runbar .flag{margin-left:auto;font-family:var(--mono);font-size:11.5px;color:var(--urgent);font-weight:600}
  .panel-head{display:flex;flex-direction:column;gap:9px;padding-bottom:16px;border-bottom:1px solid var(--border);margin-bottom:18px}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-faint);display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .chip{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;padding:3px 8px;border-radius:999px;border:1px solid var(--border);color:var(--ink-soft)}
  .chip.urgent{color:var(--urgent);border-color:color-mix(in oklab,var(--urgent) 45%,var(--border))}
  .chip.ok{color:var(--ok);border-color:color-mix(in oklab,var(--ok) 40%,var(--border))}
  .panel-title{font-size:27px;font-weight:800;letter-spacing:-.025em;margin:0;text-wrap:balance}
  .content{max-width:74ch}
  .content h2{font-size:15px;letter-spacing:.02em;margin:26px 0 8px;padding-bottom:5px;border-bottom:1px solid var(--border-soft)}
  .content h3{font-size:14px;margin:18px 0 6px;color:var(--ink)}
  .content p{margin:10px 0}
  .content ul{margin:8px 0;padding-left:20px}.content li{margin:5px 0}
  .content a{color:var(--accent);text-decoration:none;border-bottom:1px solid color-mix(in oklab,var(--accent) 35%,transparent)}
  .content a:hover{border-bottom-color:var(--accent)}
  .content code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);padding:1px 5px;border-radius:4px}
  .content strong{font-weight:700}
  .content hr{border:0;border-top:1px solid var(--border);margin:20px 0}
  .content blockquote{margin:12px 0;padding:8px 14px;border-left:3px solid var(--accent);background:var(--surface-2);border-radius:0 6px 6px 0;color:var(--ink-soft)}
  .content .pending{color:var(--ink-faint);font-style:italic;padding:20px 0}
  .flagbanner{margin:0 0 20px;padding:13px 16px;border:1px solid color-mix(in oklab,var(--urgent) 45%,var(--border));border-left:4px solid var(--urgent);border-radius:8px;background:color-mix(in oklab,var(--urgent) 9%,var(--surface));color:var(--ink)}
  .flagbanner .fb-h{display:block;font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--urgent);font-weight:700;margin-bottom:5px}
  .flagbanner p{margin:0}.flagbanner p+p{margin-top:6px}
  .flagbanner a{color:var(--urgent);border-bottom:1px solid color-mix(in oklab,var(--urgent) 40%,transparent)}
  .helppanel{margin:14px 22px 0;background:var(--surface);border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow);padding:14px 18px;font-size:13.5px;line-height:1.55}
  .helppanel[hidden]{display:none}
  .helppanel .hp-head{display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:14px;margin-bottom:6px}
  .helppanel p{margin:8px 0}
  .helppanel ul{margin:6px 0;padding-left:22px}
  .helppanel li{margin:4px 0}
  .helppanel code{font-family:var(--mono);font-size:.9em;background:var(--surface-2);padding:1px 5px;border-radius:4px}
  .helppanel .sdot{display:inline-block;vertical-align:middle;margin-right:2px}
  .strip{display:none}
  @media (max-width:860px){
    .app{grid-template-columns:1fr}.rail{display:none}
    .strip{display:flex;gap:6px;overflow-x:auto;padding:10px 14px;border-bottom:1px solid var(--border)}
    .schip{flex:0 0 auto;font-family:var(--mono);font-size:11.5px;padding:7px 10px;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--ink-soft);cursor:pointer;white-space:nowrap;display:flex;gap:6px;align-items:center}
    .schip.active{border-color:var(--accent);color:var(--accent);background:var(--accent-tint)}
    .panel{padding:16px}.panel-title{font-size:22px}.masthead{padding:15px 16px 11px}
  }
  @media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <header class="masthead">
    <div class="brand">
      <span class="kicker">🗞️ Auto-generated · one routine, 18 briefs</span>
      <h1 class="title">Daily Briefings</h1>
      <span class="sub" id="subline">awaiting first run</span>
    </div>
    <div class="tools">
      <button class="tbtn" id="copyBriefBtn" title="Copy this brief as Markdown to your clipboard">📋 copy brief</button>
      <button class="tbtn" id="copyAllBtn" title="Copy all briefs as Markdown to your clipboard">📋 copy all</button>
      <button class="tbtn" id="htmlBriefBtn" title="Open this brief as a standalone HTML page in a new tab — then Ctrl/Cmd+S to save or share">↗ brief.html</button>
      <button class="tbtn" id="htmlAllBtn" title="Open all briefs as one standalone HTML page in a new tab — then Ctrl/Cmd+S to save or share">↗ all.html</button>
      <button class="tbtn" id="themeBtn"><span id="themeIcon">◐</span> theme</button>
      <button class="tbtn" id="helpBtn" title="How to read this dashboard">? help</button>
    </div>
  </header>
  <div class="helppanel" id="helpPanel" hidden>
    <div class="hp-head"><span>How to read this dashboard</span><button class="tbtn" id="helpClose" title="Close">✕</button></div>
    <p><strong>Refresh.</strong> Every topic is re-researched from scratch on every run — <code>upd &lt;timestamp&gt;</code> is when. Nothing is skipped.</p>
    <p><strong>Bars = how much news the lane typically produces</strong> (not how often it's refreshed):</p>
    <ul>
      <li><code>▮▮▮</code> <strong>firehose</strong> — news practically daily (OLTP, Frontend, DevOps, AI Daily…)</li>
      <li><code>▮▮&nbsp;</code> <strong>steady</strong> — regular but not constant (Snowflake, Databricks, BigQuery…)</li>
      <li><code>▮&nbsp;&nbsp;</code> <strong>quiet</strong> — slow-moving lane (Oracle, Redshift, Fabric, Mobile…)</li>
    </ul>
    <p><strong>Status dots = what today's research found:</strong></p>
    <ul>
      <li><span class="sdot ok"></span> <strong>fresh</strong> — researched, nothing act-now</li>
      <li><span class="sdot urgent"></span> <strong>⚑ flagged</strong> — act-now item (the red banner at the top of the brief names it)</li>
      <li><span class="sdot slow"></span> <strong>slow day</strong> — genuinely little news in this lane today</li>
      <li><span class="sdot pending"></span> <strong>pending</strong> — not yet built this run</li>
    </ul>
    <p><strong>The two chips are independent.</strong> Churn (the bars) is the lane's permanent character; status is today's result. So <em>quiet + ⚑ flagged</em> means a rarely-newsy lane produced an act-now item today — pay extra attention. <em>Firehose + slow day</em> means an always-busy lane had an unusually dead day — also worth noticing. A quiet lane with a short brief is just normal.</p>
    <p><strong>⚑ Flagged</strong> = drop-what-you're-doing: an actively-exploited CVE on a stack you run, or a hard deadline within ~14 days. Expect 0–3 flags on a normal day.</p>
    <p><strong>Tokens</strong> (in the summary line) = total spent by the research agents this run — a volume gauge for cost trending, not an exact bill.</p>
  </div>
  <div class="strip" id="strip"></div>
  <div class="app">
    <nav class="rail" id="rail"></nav>
    <main class="panel">
      <div class="runbar">
        <span class="lbl">Last run</span><span class="val" id="runDate">—</span>
        <span class="lbl">Topics</span><span class="val" id="runCount">—</span>
        <span class="flag" id="runFlag"></span>
      </div>
      <div class="panel-head">
        <div class="eyebrow" id="eyebrow"></div>
        <h2 class="panel-title" id="pTitle"></h2>
      </div>
      <div class="content" id="content"></div>
    </main>
  </div>
</div>

<script>
/* ===== DATA — the routine replaces this whole block each run ===== */
window.BRIEFINGS = {
  generated: "",
  summary: "",
  sections: [
    {id:"oltp",       name:"OLTP & Distributed SQL",   group:"Data layer",              cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"formats",    name:"Open Formats & CDC",       group:"Data layer",              cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"oracle",     name:"Oracle",                   group:"Data layer",              cadence:"Weekly",    freq:1, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"snowflake",  name:"Snowflake",                group:"Data layer",              cadence:"2–3×/week", freq:2, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"databricks", name:"Databricks",               group:"Data layer",              cadence:"2–3×/week", freq:2, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"bigquery",   name:"BigQuery",                 group:"Data layer",              cadence:"2×/week",   freq:2, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"redshift",   name:"Redshift",                 group:"Data layer",              cadence:"Weekly",    freq:1, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"fabric",     name:"Microsoft Fabric / Synapse",group:"Data layer",             cadence:"Weekly",    freq:1, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"challengers",name:"Cloud DW Challengers",     group:"Data layer",              cadence:"2×/week",   freq:2, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"dbhw",       name:"Database Hardware",        group:"Data layer",              cadence:"2×/week",   freq:2, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"appdev",     name:"App Dev (Backend)",        group:"Application layer",        cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"aiappdev",   name:"AI App Dev",               group:"Application layer",        cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"frontend",   name:"Frontend & Web Platform",  group:"Application layer",        cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"devops",     name:"Platform & DevOps",        group:"Application layer",        cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"mobile",     name:"Mobile Development",       group:"Application layer",        cadence:"Weekly",    freq:1, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"aidaily",    name:"AI Daily",                 group:"AI, Research & Hardware",  cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"nl2sql",     name:"NL2SQL / Text-to-SQL",     group:"AI, Research & Hardware",  cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""},
    {id:"aihw",       name:"AI Hardware",              group:"AI, Research & Hardware",  cadence:"Daily",     freq:3, updated:"", status:"pending", md:"", flag_reason:""}
  ]
};
/* ===== end DATA ===== */

(function(){
  var B = window.BRIEFINGS || {sections:[]};
  var GROUPS = ["Data layer","Application layer","AI, Research & Hardware"];
  var rail=document.getElementById("rail"), strip=document.getElementById("strip");
  var byId={}; B.sections.forEach(function(s){byId[s.id]=s;});
  document.getElementById("runDate").textContent = B.generated || "—";
  var done = B.sections.filter(function(s){return s.status&&s.status!=="pending";}).length;
  document.getElementById("runCount").textContent = done+" / "+B.sections.length;
  var urgent = B.sections.filter(function(s){return s.status==="urgent";});
  document.getElementById("runFlag").textContent = urgent.length ? ("⚑ "+urgent.length+" flagged: "+urgent.map(function(s){return s.name;}).join(", ")) : "";
  document.getElementById("subline").textContent = B.generated ? ("last run "+B.generated+(B.summary?" · "+B.summary:"")) : "awaiting first run";
  function meter(f){var s="<span class='meter'>";for(var i=1;i<=3;i++)s+="<i class='"+(i<=f?"on":"")+"'></i>";return s+"</span>";}
  function churn(f){return f===3?"firehose":(f===2?"steady":"quiet");}
  function esc(t){return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  function md2html(src){
    if(!src) return "<p class='pending'>Awaiting first run…</p>";
    var lines=src.replace(/\r/g,"").split("\n"), out=[], i=0, inUl=false;
    function inline(t){
      t=esc(t);
      t=t.replace(/`([^`]+)`/g,function(_,c){return "<code>"+c+"</code>";});
      t=t.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
      t=t.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");
      t=t.replace(/(^|[^*])\*([^*]+)\*/g,"$1<em>$2</em>");
      return t;
    }
    function closeUl(){if(inUl){out.push("</ul>");inUl=false;}}
    for(;i<lines.length;i++){
      var ln=lines[i];
      if(/^\s*$/.test(ln)){closeUl();continue;}
      if(/^---+\s*$/.test(ln)){closeUl();out.push("<hr>");continue;}
      var h=ln.match(/^(#{1,4})\s+(.*)$/);
      if(h){closeUl();var lv=Math.min(h[1].length,3)+1;out.push("<h"+lv+">"+inline(h[2])+"</h"+lv+">");continue;}
      if(/^>\s?/.test(ln)){closeUl();out.push("<blockquote>"+inline(ln.replace(/^>\s?/,""))+"</blockquote>");continue;}
      var li=ln.match(/^\s*[-*]\s+(.*)$/);
      if(li){if(!inUl){out.push("<ul>");inUl=true;}out.push("<li>"+inline(li[1])+"</li>");continue;}
      closeUl();out.push("<p>"+inline(ln)+"</p>");
    }
    closeUl();return out.join("\n");
  }
  GROUPS.forEach(function(g){
    var items=B.sections.filter(function(s){return s.group===g;});
    if(!items.length) return;
    var grp=document.createElement("div");grp.className="group";
    var h=document.createElement("div");h.className="group-h";
    h.innerHTML="<span>"+g+"</span><span>"+items.length+"</span>";grp.appendChild(h);
    items.forEach(function(s){
      var b=document.createElement("button");b.className="nav-item";b.dataset.id=s.id;
      b.innerHTML="<span class='sdot "+(s.status||"pending")+"'></span>"+
        "<span class='nav-main'><span class='nav-name'>"+s.name+"</span>"+
        "<span class='nav-meta'>"+(s.updated?("upd "+s.updated.replace(/^\d{4}-\d{2}-\d{2} /,"")):"pending")+" · "+churn(s.freq)+"</span></span>"+meter(s.freq);
      b.addEventListener("click",function(){select(s.id);});
      grp.appendChild(b);
    });
    rail.appendChild(grp);
  });
  B.sections.forEach(function(s){
    var c=document.createElement("button");c.className="schip";c.dataset.id=s.id;
    c.innerHTML="<span class='sdot "+(s.status||"pending")+"'></span>"+s.name;
    c.addEventListener("click",function(){select(s.id);});strip.appendChild(c);
  });
  var cur=null;
  function select(id){
    var s=byId[id];if(!s)return;cur=id;
    document.getElementById("pTitle").textContent=s.name;
    var st=s.status||"pending";
    var chipCls=st==="urgent"?"chip urgent":(st==="ok"?"chip ok":"chip");
    var stLabel=st==="urgent"?"⚑ flagged":(st==="ok"?"fresh":(st==="slow"?"slow day":"pending"));
    document.getElementById("eyebrow").innerHTML="<span>"+s.group.toUpperCase()+"</span>"+
      "<span class='chip'>"+meter(s.freq)+" "+churn(s.freq)+"</span>"+
      "<span class='"+chipCls+"'>"+stLabel+"</span>"+
      (s.updated?"<span>updated "+s.updated+"</span>":"");
    var banner = (st==="urgent" && s.flag_reason)
      ? "<div class='flagbanner'><span class='fb-h'>⚑ Why this is flagged — act now</span>"+md2html(s.flag_reason)+"</div>"
      : "";
    document.getElementById("content").innerHTML=banner+md2html(s.md);
    document.querySelectorAll(".nav-item").forEach(function(n){n.classList.toggle("active",n.dataset.id===id);});
    document.querySelectorAll(".schip").forEach(function(n){n.classList.toggle("active",n.dataset.id===id);});
    document.querySelector(".panel").scrollTop=0;
  }
  function dateSlug(){return (B.generated||"").slice(0,10)||"undated";}
  function briefMd(s){
    var parts=["# "+s.name,""];
    var meta=[s.group, churn(s.freq), (s.status||"pending").toUpperCase()];
    if(s.updated) meta.push("updated "+s.updated);
    parts.push("_"+meta.join(" · ")+"_","");
    if(s.status==="urgent" && s.flag_reason){
      parts.push("> ⚑ **Act now:** "+s.flag_reason.replace(/\n+/g," "),"");
    }
    parts.push(s.md||"_Awaiting first run._");
    return parts.join("\n");
  }
  function flash(btn,msg){var o=btn.dataset.lbl||btn.textContent;btn.dataset.lbl=o;btn.textContent=msg;setTimeout(function(){btn.textContent=o;},1700);}
  function legacyCopy(text){
    try{var ta=document.createElement("textarea");ta.value=text;ta.setAttribute("readonly","");
      ta.style.position="fixed";ta.style.top="-1000px";ta.style.opacity="0";
      document.body.appendChild(ta);ta.focus();ta.select();ta.setSelectionRange(0,text.length);
      var ok=document.execCommand("copy");document.body.removeChild(ta);return ok;}catch(e){return false;}
  }
  // Copy Markdown to clipboard — the reliable path in a sandboxed artifact iframe (paste into Slack/email/doc).
  function copyMd(text,btn){
    var done=function(ok){flash(btn, ok?"✓ copied!":"⚠ copy blocked");};
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){done(true);},function(){done(legacyCopy(text));});
    }else{ done(legacyCopy(text)); }
  }
  // Export HTML with a layered fallback, best → floor:
  // 1) showSaveFilePicker() — a real native "Save As" dialog on click (Chromium; the genuine Ctrl+S).
  // 2) window.open() — opens the page in a new tab (then Ctrl/Cmd+S) where pop-ups are allowed.
  // 3) clipboard — the only thing that works in a locked-down artifact iframe (paste into a .html file).
  // Note: browsers forbid scripts from synthesising Ctrl+S / the Save dialog directly — (1) is the API for it.
  function exportHtml(name,html,btn){
    if(window.showSaveFilePicker){
      window.showSaveFilePicker({suggestedName:name,types:[{description:"HTML file",accept:{"text/html":[".html"]}}]})
        .then(function(h){return h.createWritable();})
        .then(function(w){return Promise.resolve(w.write(html)).then(function(){return w.close();});})
        .then(function(){flash(btn,"✓ saved");})
        .catch(function(e){ if(e&&e.name==="AbortError") return; openOrCopy(html,btn); });
      return;
    }
    openOrCopy(html,btn);
  }
  function openOrCopy(html,btn){
    var url=null; try{ url=URL.createObjectURL(new Blob([html],{type:"text/html;charset=utf-8"})); }catch(e){}
    var win=null; try{ win=window.open(url||"","_blank","noopener"); }catch(e){}
    if(win){ if(!url){ try{win.document.open();win.document.write(html);win.document.close();}catch(e){} } flash(btn,"↗ opened — Ctrl/Cmd+S to save"); }
    else if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(html).then(function(){flash(btn,"✓ HTML copied");},function(){flash(btn, legacyCopy(html)?"✓ HTML copied":"⚠ blocked");});
    } else { flash(btn, legacyCopy(html)?"✓ HTML copied":"⚠ blocked"); }
    if(url) setTimeout(function(){URL.revokeObjectURL(url);},60000);
  }
  var DOC_CSS="body{margin:0;background:#f6f8fa;color:#1a2230;font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,Roboto,sans-serif;-webkit-font-smoothing:antialiased}"
    +"main{max-width:820px;margin:0 auto;padding:40px 22px 80px}"
    +".kick{font:600 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:#0f6f83;margin:0 0 6px}"
    +"h1{font-size:30px;letter-spacing:-.02em;margin:.2em 0 .1em}"
    +".meta{font:12px/1.4 ui-monospace,Menlo,monospace;color:#6b7684;margin:0 0 18px}"
    +"h2{font-size:16px;margin:28px 0 8px;padding-bottom:5px;border-bottom:1px solid #e2e7ee}h3{font-size:14px;margin:18px 0 6px}"
    +"a{color:#0b6b7e;text-decoration:none;border-bottom:1px solid rgba(11,107,126,.35)}a:hover{border-bottom-color:#0b6b7e}"
    +"code{font:.86em ui-monospace,Menlo,monospace;background:#eef1f5;padding:1px 5px;border-radius:4px}"
    +"ul{padding-left:22px}li{margin:5px 0}"
    +"blockquote{margin:12px 0;padding:8px 14px;border-left:3px solid #0f6f83;background:#eef4f6;border-radius:0 6px 6px 0;color:#48566a}"
    +"hr{border:0;border-top:1px solid #d7dee6;margin:34px 0}"
    +".flag{margin:14px 0;padding:12px 16px;border:1px solid #e6b9b3;border-left:4px solid #c0392b;border-radius:8px;background:#fbeeec;color:#5a1e17}"
    +"@media(prefers-color-scheme:dark){body{background:#0f141a;color:#e7edf4}.kick{color:#3fb6cf}.meta{color:#8592a1}h2{border-bottom-color:#232d39}a{color:#3fb6cf;border-bottom-color:rgba(63,182,207,.4)}code{background:#1a222c}blockquote{background:#161d25;border-left-color:#3fb6cf;color:#a3b0c0}hr{border-top-color:#232d39}.flag{background:#2a1512;border-color:#5a2a24;border-left-color:#f0685b;color:#f3c9c4}}";
  function pageHtml(title,inner){
    return "<!doctype html>\n<html lang='en'><head><meta charset='utf-8'>"
      +"<meta name='viewport' content='width=device-width,initial-scale=1'>"
      +"<title>"+esc(title)+"</title><style>"+DOC_CSS+"</style></head><body><main>"+inner+"</main></body></html>";
  }
  function briefSection(s){
    var meta=[s.group,churn(s.freq),(s.status||"pending").toUpperCase()];
    if(s.updated) meta.push("updated "+s.updated);
    var banner=(s.status==="urgent"&&s.flag_reason)?"<div class='flag'><strong>⚑ Act now — </strong>"+md2html(s.flag_reason)+"</div>":"";
    return "<h1>"+esc(s.name)+"</h1><p class='meta'>"+esc(meta.join(" · "))+"</p>"+banner+"<article>"+md2html(s.md)+"</article>";
  }
  function briefHtml(s){
    return pageHtml(s.name+" — Daily Briefings","<p class='kick'>Daily Briefings · "+esc(B.generated||"")+"</p>"+briefSection(s));
  }
  function allHtml(){
    var done=B.sections.filter(function(s){return s.status&&s.status!=="pending";});
    var head="<p class='kick'>Daily Briefings · "+esc(B.generated||"")+(B.summary?" · "+esc(B.summary):"")+"</p><h1>Daily Briefings</h1>";
    var body=done.map(function(s){return "<section>"+briefSection(s)+"</section>";}).join("<hr>");
    return pageHtml("Daily Briefings — "+(B.generated||""), head+body);
  }
  document.getElementById("copyBriefBtn").addEventListener("click",function(){
    var s=byId[cur]; if(!s) return; copyMd(briefMd(s), this);
  });
  document.getElementById("copyAllBtn").addEventListener("click",function(){
    var head="# Daily Briefings — "+(B.generated||"")+"\n"+(B.summary?"\n"+B.summary+"\n":"");
    var body=B.sections.filter(function(s){return s.status&&s.status!=="pending";})
      .map(function(s){return briefMd(s);}).join("\n\n---\n\n");
    copyMd(head+"\n"+body+"\n", this);
  });
  document.getElementById("htmlBriefBtn").addEventListener("click",function(){
    var s=byId[cur]; if(!s) return; exportHtml("briefing-"+s.id+"-"+dateSlug()+".html", briefHtml(s), this);
  });
  document.getElementById("htmlAllBtn").addEventListener("click",function(){
    exportHtml("daily-briefings-"+dateSlug()+".html", allHtml(), this);
  });
  var hb=document.getElementById("helpBtn"),hp=document.getElementById("helpPanel");
  hb.addEventListener("click",function(){hp.hidden=!hp.hidden;});
  document.getElementById("helpClose").addEventListener("click",function(){hp.hidden=true;});
  var root=document.documentElement,tb=document.getElementById("themeBtn"),ti=document.getElementById("themeIcon");
  function sysDark(){return window.matchMedia&&window.matchMedia("(prefers-color-scheme:dark)").matches;}
  function curDark(){var t=root.getAttribute("data-theme");return t?t==="dark":sysDark();}
  tb.addEventListener("click",function(){var n=curDark()?"light":"dark";root.setAttribute("data-theme",n);ti.textContent=n==="dark"?"◑":"◐";});
  var first=(urgent[0]||B.sections.filter(function(s){return s.status&&s.status!=="pending";})[0]||B.sections[0]);
  if(first) select(first.id);
})();
</script>
```
