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

## How Pages is served — the `gh-pages` branch

This repo serves Pages from the **root of the `gh-pages` branch** (classic model). Two branches,
two jobs:

```
main        (source)            gh-pages   (published site — served at the repo root)
├── pages-briefings-...-prompt.md   ├── index.html    # static Claude-vs-Codex landing page
└── README.md                       ├── claude.html   # Claude side — REBUILT + pushed every run
                                     ├── codex.html    # Codex side — pending
                                     └── .nojekyll     # serve HTML verbatim (no Jekyll)
```

- **`main`** holds the *source*: the routine prompt and this README.
- **`gh-pages`** IS the *site*: whatever is at its root is what `karlarao.github.io/daily-briefings/`
  serves. `index.html` is static (edit it here directly); `claude.html` is overwritten each run.

## How the Claude routine publishes

The routine runs attached to this repo (already cloned & authenticated by the GitHub App — no PAT).
Each run it: checks out `gh-pages`, researches the 18 briefs, rebuilds `claude.html` locally, then
does **one** commit + `git push origin gh-pages` at the end (one Pages build per run). It leaves
`index.html` / `codex.html` untouched, and sends a single push notification only if the push failed
or a brief flagged something act-now urgent.

Full mechanics live in [`pages-briefings-routine-prompt.md`](pages-briefings-routine-prompt.md).

## One-time GitHub Pages setup

Repo **Settings → Pages → Build and deployment → Deploy from a branch → `gh-pages` / `(root)`**.
The root `.nojekyll` is already present so Pages serves the HTML as-is.
