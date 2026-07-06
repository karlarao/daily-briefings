# daily-briefings

Auto-generated engineering-news dashboard — **18 topics** researched daily through a working
software / performance-engineer lens, rendered to one self-contained HTML page and published to
**GitHub Pages** via `git push`.

**Public site:** https://karlarao.github.io/daily-briefings/ · **Claude:** [`/claude.html`](https://karlarao.github.io/daily-briefings/claude.html)

## Head-to-head — same prompt, two agents

Both sides run the *identical* 18-brief spec and the *identical* dashboard template; only the
search backend, execution model, model, and run date differ.

| Side | Output | Produced by | Status |
|---|---|---|---|
| **Claude** | `claude.html` | Claude Code cloud routine (WebSearch) → `git push` | live |
| **Codex** | `codex.html` | GitHub Actions → OpenAI Responses API (`web_search`) | pending |

`index.html` is a static landing page linking both.

## How to read the dashboard

(Also available in the dashboard itself — the **`? help`** button, top right.)

- **◆ Today's Trends** (pinned at the top, default landing view) — one synthesis pass across all
  the briefs: converging themes per group plus cross-cutting ones, each citing its source briefs
  ("→ seen in: …"). The 5-minute read when you can't do all 18; on a day with no real convergence
  it says so instead of inventing patterns.
- **Refresh** — every topic is re-researched from scratch on every run; `upd <timestamp>` is when.
  Nothing is skipped, ever.
- **Bars = churn** — how much news the lane *typically* produces, not how often it's refreshed:
  `▮▮▮ firehose` (news practically daily: OLTP, Frontend, AI Daily…) · `▮▮ steady` (Snowflake,
  Databricks, BigQuery…) · `▮ quiet` (slow-moving lane: Oracle, Redshift, Fabric, Mobile…).
- **Status dots = what today's research found** — green `fresh` (nothing act-now), red `⚑ flagged`
  (act-now item; the red banner in the brief names it), grey `slow day` (genuinely little news
  today), hollow `pending` (not yet built this run).
- **The two chips are independent.** Churn is the lane's permanent character; status is today's
  result. `quiet + ⚑ flagged` = a rarely-newsy lane produced an act-now item — pay extra attention.
  `firehose + slow day` = an always-busy lane had an unusually dead day — also worth noticing.
- **⚑ Flagged** = drop-what-you're-doing: an actively-exploited CVE on a stack you run, or a hard
  deadline within ~14 days. Expect 0–3 flags on a normal day.
- **Tokens** = spend by the research subagents that run — a volume gauge for cost trending, not
  an exact bill. The summary line carries the total, each brief's header shows its own count, and
  the **`Σ tokens`** button opens a sorted per-topic breakdown with share bars. The "N slow"
  segment appears in the summary only when at least one lane had a slow day.

## How Pages is served — the `gh-pages` branch

This repo serves Pages from the **root of the `gh-pages` branch** (classic model). Two branches,
two jobs:

```
main        (source, default branch)    gh-pages   (published site — served at the repo root)
├── pages-briefings-...-prompt.md       ├── index.html    # static Claude-vs-Codex landing page
├── GITHUB-PAGES-RUNBOOK.md             ├── claude.html   # Claude side — REBUILT + pushed every run
└── README.md                           └── .nojekyll     # serve HTML verbatim (no Jekyll)
                                        (codex.html — Codex side, pending; not on the branch yet)
```

- **`main`** holds the *source*: the routine prompt, the [Pages ops runbook](GITHUB-PAGES-RUNBOOK.md),
  and this README.
- **`gh-pages`** IS the *site*: whatever is at its root is what `karlarao.github.io/daily-briefings/`
  serves. `index.html` is static (edit it here directly); `claude.html` is overwritten each run.

## How the Claude routine publishes

The routine runs attached to this repo (already cloned & authenticated by the GitHub App — no PAT).
Each run it: checks out `gh-pages`, researches the 18 briefs, rebuilds `claude.html` locally, then
does **one** commit + `git push origin gh-pages` at the end (one Pages build per run), and finally
**verifies the Pages deployment actually succeeded** (re-triggering with an empty commit if the
deploy failed or stalled — GitHub Pages deploys flake intermittently). It leaves `index.html` /
`codex.html` untouched, and sends a single push notification only if the publish (push **or** Pages
deploy) failed or a brief flagged something act-now urgent.

Full mechanics live in [`pages-briefings-routine-prompt.md`](pages-briefings-routine-prompt.md).

## One-time GitHub Pages setup

Repo **Settings → Pages → Build and deployment → Deploy from a branch → `gh-pages` / `(root)`**.
The root `.nojekyll` is already present so Pages serves the HTML as-is.
