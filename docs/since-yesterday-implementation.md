# "Since yesterday" — implementation record

Implemented 2026-07-08. This documents what actually shipped, completing the series:

1. [`run-statelessness-and-trends.md`](./run-statelessness-and-trends.md) — why the pipeline is stateless and what that trades away
2. [`cross-day-awareness-design.md`](./cross-day-awareness-design.md) — the pros/cons analysis and the thin ledger-diff design proposal
3. **This doc** — what was built, how it differs from the proposal, and what running it on real data taught us

---

## What shipped

A pinned **◇ Since yesterday** card on the dashboard, directly under Today's Trends, showing a day-over-day diff of the briefing headlines:

- **🆕 New** — items in today's briefs that weren't in yesterday's (curated top ~12, severity-ordered, plus a "+N more newly-surfaced items" count)
- **🔺 Changed** — same story, real movement, each with a short note (e.g. *"escalated — now flagged ⚑"*, *"preview → public"*, *"deadline has now passed"*)
- **➰ Still ongoing** — same story, still running, with a day counter (*"day 2"*)
- **⤵ footnote** — how many of yesterday's items did not resurface today

Matching is **Option 2 from the design doc: LLM story-level matching**, so a story survives rewording — *"node-gyp worm hits 57 pkgs"* matches yesterday's *"'Miasma' — Red Hat npm namespace compromised"* — and can even follow a story that moved topics (the @mastra hijack appeared under Frontend yesterday and under App Dev, flagged urgent, today).

The core design constraint held: **the 18 research subagents remain 100% stateless.** Only the end-of-run diff step and the render layer look backward.

## Where it lives

| Piece | Location |
|---|---|
| Routine prompt changes (steps 4c, 5; data contract; template) | `pages-briefings-routine-prompt.md` on branch `claude/bold-bardeen-pw0bhy` — [PR #1](https://github.com/karlarao/daily-briefings/pull/1) |
| Daily headline ledger (the diff's durable state) | `archive/ledger/<YYYY-MM-DD>.json` on `gh-pages` |
| Live dashboard with the card | `claude.html` on `gh-pages` (rebuilt 2026-07-08 with a real Jul-7-vs-Jul-8 diff) |

Commits on the PR branch:

- `fb6115f` — the feature: step 4c (ledger build → prior-ledger load → LLM match → categorize), step 5 ledger persistence, `window.BRIEFINGS.whatsnew` contract, template card/CSS/copy/export wiring
- `f1eb554` — review fixes from a fresh-model pass (underscore→asterisk italics for the md exporter, aged-out count no longer dropped on quiet days, dead CSS removed)
- `e659caa` — refinements from the first real-data run (see below)

## The pipeline change (step 4c, summarized)

```
18 briefs done (stateless, unchanged)
        │
  (i)   BUILD TODAY'S LEDGER      titles-only index: per topic, the bold headline
        │                         bullets → {key, title, sev, first_seen, days_seen}
  (ii)  LOAD PRIOR LEDGER         latest archive/ledger/<date>.json BEFORE today;
        │                         none → whatsnew=null, skip (graceful first run)
  (iii) MATCH & DIFF (LLM)        same underlying story even if reworded; within
        │                         topic first, cross-topic if the story moved →
        │                         NEW / CHANGED(note) / ONGOING(days) / not-resurfaced
  (iv)  STAMP & CURATE            matched: first_seen=prior, days_seen+1; assemble
        │                         whatsnew {prev_date, new[], new_more, changed[],
        │                         ongoing[], aged_out}
step 5  PERSIST                   write archive/ledger/<today>.json with the run
```

Key properties carried over from the design doc, verified in implementation:

- **Same-day reruns** diff against *yesterday* (the load rule is "latest date BEFORE today"), and the day's ledger is overwritten — one ledger per date, that day's latest run.
- **First run** with no prior ledger shows no card and seeds the ledger silently.
- **The ledger is titles/keys only** (~few KB/day) — yesterday's *prose* never enters today's run.

## The first real run (Jul 7 vs Jul 8) — actual numbers

The diff was executed manually on 2026-07-08 against the two real runs (246 headline items today, ~200 yesterday):

| Bucket | Count | Notes |
|---|---|---|
| Auto-matched (token overlap) | 71 | near-identical phrasing across days |
| LLM-matched (reworded / moved / advanced) | 38 | the part slugs can't do |
| Excluded (meta bullets, same-story duplicates) | 26 | e.g. "Quiet elsewhere", a Heads-up restating a CVE item |
| NEW | 111 | 12 shown on the card, `new_more: 99` |
| CHANGED (with notes) | 12 | worms escalated to ⚑, GPT-5.6 preview→public, DirtyClone variant, Oracle CPU dated, Redshift UDF deadline passed… |
| ONGOING (day 2) | 6 shown | MCP stateless spec, DDR5/NAND surge, K8s deadlines, Play API-36 gate… |
| Not resurfaced from yesterday | 88 | mostly research variance, not window expiry |

## What real data taught us (the `e659caa` refinements)

Two design gaps only became visible with real runs:

1. **NEW needs curation, not just listing.** Each day's research re-surfaces a *different subset* of the same 30-day window, so the raw "no prior match" set is large (~111) and mostly "newly **surfaced**", not "newly **happened**". The prompt now caps the displayed NEW list at ~10–15 severity-ordered items and carries the remainder in a `new_more` count; meta/context bullets and same-story duplicates are excluded from lists *and* counts.
2. **"Aged out" was a misleading label.** Most of the 88 unmatched prior items weren't literally window-expired — they just weren't re-surfaced by today's agents. The card now says *"did not resurface today (aged out of the window or not re-surfaced by today's research)"* and the prompt warns not to read the number as an expiry count.

## Ledger schema

```json
// archive/ledger/2026-07-08.json  (titles/keys only — never full brief text)
{
  "date": "2026-07-08",
  "topics": {
    "appdev": {
      "status": "urgent",
      "items": [
        { "key": "npm-worms-actively-spreading",
          "title": "npm worms are actively spreading (Shai-Hulud / Miasma lineage)",
          "sev": "urgent",          // urgent | high | normal
          "first_seen": "2026-07-07",
          "days_seen": 2 }
      ]
    }
  }
}
```

`whatsnew` (in `window.BRIEFINGS`, `null` when there is no prior ledger):

```json
{ "prev_date": "2026-07-07",
  "new":     [ { "topic": "AI Daily", "title": "…" } ],
  "new_more": 99,
  "changed": [ { "topic": "App Dev (Backend)", "title": "…", "note": "escalated — now flagged ⚑ …" } ],
  "ongoing": [ { "topic": "Database Hardware", "title": "…", "days": 2 } ],
  "aged_out": 88 }
```

## Verification performed

- `new Function()` syntax check on the full template script after every edit
- Headless Chromium (Playwright) tests: populated card (groups, notes, day counters, `+N more` row, footnote), `whatsnew: null` (no card, no errors), empty diff + aged-out count, clipboard copy, HTML export (asterisk italics render to `<em>`), flagged-brief banner unaffected
- The live page itself: built, screenshot-inspected, pushed as `bd9717c`, and the GitHub Pages deployment for that commit verified **success** via the Actions API

## Activation status

- **Live today (one-time):** the 2026-07-08 dashboard at `claude.html` carries the card, hand-built from the real Jul-7/Jul-8 diff. Ledgers exist for 2026-07-08.
- **Not yet automated:** the scheduled routine runs a *pasted copy* of the prompt. Until [PR #1](https://github.com/karlarao/daily-briefings/pull/1) is merged **and** the routine config is updated with the merged prompt, the next scheduled run rebuilds the page with the old template (card disappears) — it returns permanently, automated, once the routine prompt is updated. The 2026-07-08 ledger is already in place as its diff base.
