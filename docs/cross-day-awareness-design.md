# Cross-day awareness: pros/cons + a thin ledger-diff design

Companion to [`run-statelessness-and-trends.md`](./run-statelessness-and-trends.md).

This doc captures (1) the trade-off analysis of the current **stateless** design vs.
adding cross-day awareness, and (2) a concrete, low-risk implementation sketch for a
thin **"What's new / What changed / Still ongoing"** layer.

> Status: **discussion only — no prompt changes made.** This is a design record.

---

## Part 1 — Pros & cons

### Strengths of the current stateless design (why you'd keep it)

**1. Correctness by construction — no drift or contamination.**
Each run's trends are derived *only* from 18 briefs generated the same morning, each with
fresh `→ seen in:` attributions. There's no path for a stale claim, a hallucinated "as we
noted yesterday," or a compounding error to leak forward. Every run is independently
auditable: the dashboard you see is fully explained by that run's own briefs. The moment
you feed yesterday's output back in, you lose that guarantee — errors and framing can
snowball across days.

**2. Idempotent and crash-safe.**
Because nothing persists, a re-run is just… another clean run. Same-day reruns overwrite
cleanly. There's no state file to corrupt, migrate, or get out of sync with the branch.
Today's run proved this: 18 parallel agents, one died-and-slow (BigQuery took ~7min), and
the pipeline didn't care because there was no shared mutable state to protect.

**3. The prompt is the entire system.**
"This prompt is the ONLY durable thing" is a huge operational property. You can read one
file and know exactly what the routine does. No hidden history, no "why did it say that —
oh, because of a run three weeks ago." Debugging, editing topics, and reasoning about
behavior all stay tractable. Cross-day awareness breaks this: behavior would now depend on
prompt *plus* accumulated archive state.

**4. The 30-day rolling window already gives you 90% of "memory" — honestly.**
This is the subtle one. Each agent looks back 30 days, so genuinely-ongoing stories *do*
recur naturally (npm worms, HBM pricing, Iceberg v3 all persisted across recent runs). You
already get continuity — you just get it as "still true and still in-window," which is the
*honest* version, rather than an LLM narrating momentum it can't actually measure.

**5. Cheap parallelism, bounded cost.**
Stateless = the 18 agents are embarrassingly parallel with zero coordination. Cost per run
is predictable (~850k tokens today) and doesn't grow as history accumulates.

### Weaknesses of the current design (what you're giving up)

- **No "new since yesterday."** A reader who checks daily re-reads items they already saw,
  with nothing marking what's actually changed. This is the real UX cost.
- **No momentum / trajectory.** It can't say "3rd straight day of npm supply-chain
  incidents" or "DRAM prices cooling vs. last week" — which is often the *most*
  decision-relevant signal.
- **Repetition can feel like noise.** A slow-moving lane (Oracle, Redshift) can show
  near-identical briefs day to day, and the reader has to diff by eye.
- **Flag fatigue risk.** The same urgent item re-flags every day it's in-window with no
  "you've seen this" suppression, so a persistent CVE looks as loud on day 5 as day 1.

### Cross-day awareness: what it'd add, and the true cost

The token con is real but it's arguably the *smaller* cost. Feeding yesterday's briefs (or
a compact digest) into the synthesis step is maybe +40–80k tokens on an ~850k run — call it
~5–10%. Not nothing, but not the dealbreaker.

The **bigger** costs are architectural — trading away the strengths above:

- **You reintroduce state.** Now the run reads `archive/<yesterday>.html` (or a structured
  history file). That file can be missing, malformed, or from a different prompt version.
  You need fallback logic for "no prior run," "prompt changed," "topic added/removed since."
  Complexity moves from linear to stateful.
- **Contamination risk.** Yesterday's framing biases today's read. If yesterday over-flagged
  something, today's "still elevated" inherits the mistake. The clean auditability goes away.
- **Determinism erodes.** Two runs of the same day could differ depending on what history
  existed at run time.

**The pragmatic middle path (if you ever want it):** don't feed raw prior briefs into
research. Keep the 18 agents fully stateless — that preserves strengths #1, #2, #5 for the
expensive part. Only add a *thin* diff layer at the very end: a small structured "headline
ledger" per run (topic → list of item titles + status), and a final synthesis-only step
that compares today's ledger to yesterday's to emit a "What's new / What changed / Still
ongoing" section. That's ~cheap (titles, not full text), keeps research pure, and gives you
the momentum signal without letting yesterday's prose pollute today's briefs.

### Recommendation

For a daily briefing whose job is "what do I need to know today," the current design is
well-matched — the 30-day window already encodes continuity, and statelessness buys you
correctness, simplicity, and predictable cost that are genuinely valuable for an unattended
routine nobody's watching. Keep it as-is unless you specifically feel the pain of "I can't
tell what's new." If/when you do, add the thin ledger-diff layer rather than full cross-day
context feeding — you get 80% of the benefit while protecting the properties that make this
thing robust.

---

## Part 2 — Implementation sketch: the thin ledger-diff layer

The key architectural win: **history only ever touches the ledger and the final diff card —
never the 18 research agents.** Statelessness/correctness/parallelism stay where they're
expensive; memory is paid for only in a thin, cheap, well-isolated layer at the end.

### A. Where it plugs into the run

```
                COLD-START RUN (unchanged parts in ░, new parts in █)
 ┌──────────────────────────────────────────────────────────────────────┐
 │ ░ Step 0  bootstrap: clone, checkout gh-pages, pull                    │
 │ ░ Step 1  NOW = timestamp                                              │
 │ ░ Step 2  build 18 section skeletons                                   │
 └──────────────────────────────────────────────────────────────────────┘
                                   │
       ░ Step 3/4  THE LOOP  (18 agents, FULLY STATELESS — no change)
       ┌───────────────────────────────────────────────────────┐
       │  each agent → md · status · flag_reason               │
       │  agents NEVER see yesterday. research stays pure.      │
       └───────────────────────────────────────────────────────┘
                                   │  (18 briefs done)
                                   ▼
   █ Step 4a  EXTRACT LEDGER  ── cheap, no LLM, pure parsing ────────────┐
   │  for each brief: pull item TITLES + status → today_ledger.json      │
   └─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    ▼                              ▼
   █ Step 4b  LOAD yesterday          ░ (if none → "first run,
   │  archive/ledger/<prev>.json         everything is NEW")
   └──────────────┬───────────────────────────────┘
                  ▼
   █ Step 4c  DIFF  today_ledger  vs  prev_ledger   (pure set ops, no LLM)
   │            → {new[], changed[], ongoing[], dropped[]}
   └──────────────┬───────────────────────────────┘
                  ▼
   ░ Step 4d  SYNTHESIS  "Today's Trends"  (unchanged, sideways read)
   █          + NEW pinned block: "What's new / changed / still ongoing"
   │            fed ONLY the diff object (titles), not yesterday's prose
   └──────────────┬───────────────────────────────┘
                  ▼
   ░ Step 5   finalize → build claude.html
   █          ALSO write archive/ledger/<today>.json   ← tomorrow's input
                  │
   ░ Step 5/5b  archive · commit · push · verify Pages
                  ▼
              ( done )
```

### B. The ledger — small, structured, git-durable

```
archive/ledger/2026-07-08.json        (~a few KB, titles only — NOT full md)
┌───────────────────────────────────────────────────────────────────────┐
│ {                                                                     │
│   "date": "2026-07-08",                                               │
│   "topics": {                                                         │
│     "appdev": {                                                       │
│       "status": "urgent",                                            │
│       "items": [                                                      │
│         { "key": "npm-worm-node-gyp",  "title": "node-gyp worm ...",  │
│           "sev": "critical" },                                       │
│         { "key": "npm-mastra-hijack",  "title": "@mastra hijack ...", │
│           "sev": "critical" },                                       │
│         { "key": "node-june-cves",     "title": "Node 22/24/26 ...",  │
│           "sev": "high" }                                            │
│       ]                                                               │
│     },                                                                │
│     "dbhw": { "status": "ok", "items": [ ... ] },                     │
│     ...  (18 topics)                                                  │
│   }                                                                   │
│ }                                                                     │
└───────────────────────────────────────────────────────────────────────┘

  key  = stable slug for an item (kebab of the headline's core nouns).
         This is the ONLY hard part — see D. Everything else is trivial.
```

### C. The diff — pure set logic, per topic, no model call

```
   prev_keys = { keys in yesterday's ledger[topic] }
   today_keys= { keys in today's  ledger[topic] }

        prev ●───────────────●───────────────● today
             │   DROPPED      │   ONGOING     │    NEW
             │ in prev only   │  in both      │ in today only
             ▼                ▼               ▼
   ┌─────────────────┬──────────────────┬──────────────────┐
   │ was in-window   │ present both days│ first appearance │
   │ yesterday, gone │ → "Still ongoing"│ → "What's new"   │
   │ today (aged out)│                  │                  │
   │ → footnote or   │ if sev/status    │                  │
   │   drop silently │ differs →        │                  │
   │                 │ "What changed"   │                  │
   └─────────────────┴──────────────────┴──────────────────┘

   category(item):
     key not in prev            → NEW
     key in prev, sev changed   → CHANGED   (e.g. high→critical, ok→urgent)
     key in prev, sev same      → ONGOING
     key in today missing       → DROPPED
```

### D. The only real design decision: how items match across days

```
   Two ways to get a stable `key`, cheapest first:

   OPTION 1  (deterministic, $0)                OPTION 2  (LLM-assisted)
   ─────────────────────────────                ────────────────────────
   slug = kebab(headline)                        one extra small model call:
        stopword-strip, sort nouns               "here are today's titles +
   pros: free, reproducible                       yesterday's keys — map each
   cons: reworded headline = "new"                today title to an existing
         (false NEW on rephrase)                  key or mint a new one"
                                                 pros: robust to rewording
                                                 cons: +~5-15k tokens, small
                                                       nondeterminism

   RECOMMENDATION: start OPTION 1. If false-"new" from rewording annoys
   you, upgrade JUST the matching step to OPTION 2 (still no yesterday
   *prose* enters research — only titles↔keys).
```

### E. What the reader finally sees (new pinned card above Today's Trends)

```
 ┌─ ◇ Since yesterday ───────────────────────────────────────────────┐
 │                                                                   │
 │  🆕 NEW (3)                                                        │
 │   • AI Daily — GPT-5.6 public rollout announced for Jul 9        │
 │   • Frontend — Astro 7 stable (Rust compiler)                   │
 │   • Oracle — July 21 CPU pre-announced                          │
 │                                                                   │
 │  🔺 CHANGED (1)                                                    │
 │   • App Dev — npm worm escalated  high → CRITICAL (now ⚑)        │
 │                                                                   │
 │  ➰ STILL ONGOING (2)                                              │
 │   • DB Hardware — DDR5/NAND prices still climbing (day 4)        │
 │   • AI Hardware — HBM4 allocation still gating clusters          │
 │                                                                   │
 │  ⤵ aged out: 2 items fell outside the 30-day window              │
 └───────────────────────────────────────────────────────────────────┘
```

### F. Cost & blast-radius summary

```
 ┌────────────────────┬──────────────────────────────────────────────┐
 │ Research (18 agts) │ UNCHANGED — still stateless, still parallel  │
 │ New durable state  │ archive/ledger/<date>.json  (~few KB/day)    │
 │ Extra tokens/run   │ Option 1: ~0   |   Option 2: ~5–15k (~1–2%)  │
 │ New failure modes  │ only "no/!malformed prev ledger" → treat as  │
 │                    │ first-run (everything NEW). isolated, safe.  │
 │ Correctness impact │ research purity preserved; only the final    │
 │                    │ diff card depends on history.                │
 └────────────────────┴──────────────────────────────────────────────┘
```
