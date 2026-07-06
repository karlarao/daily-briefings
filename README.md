# daily-briefings

Auto-generated engineering-news dashboard — **18 topics** researched daily through a working
software / performance-engineer lens, rendered to one self-contained HTML page and published to
**GitHub Pages** via `git push`.

**Public site:** https://karlarao.github.io/daily-briefings/

## Head-to-head — same prompt, two agents

Both sides run the *identical* 18-brief spec and the *identical* dashboard template; only the
search backend, execution model, model, and run date differ.

| Side | Output | Produced by | Status |
|---|---|---|---|
| **Claude** | [`docs/claude.html`](docs/claude.html) | Claude Code cloud routine (WebSearch) → `git push` | live |
| **Codex** | `docs/codex.html` | GitHub Actions → OpenAI Responses API (`web_search`) | pending |

`docs/index.html` is a static landing page linking both.

## Layout

```
pages-briefings-routine-prompt.md   # the routine prompt (paste into ONE Claude Code cloud routine)
docs/
  index.html    # static Claude-vs-Codex landing page (committed once, not touched by the routine)
  claude.html   # Claude side — REBUILT + pushed every run (placeholder until the first run)
  codex.html    # Codex side — pending
  .nojekyll     # tells Pages to serve the HTML verbatim
```

## How the Claude routine publishes

The routine runs attached to this repo (already cloned & authenticated by the GitHub App — no PAT).
Each run it: bootstraps the repo, researches the 18 briefs, rebuilds `docs/claude.html` locally, then
does **one** commit + `git push` at the end (one Pages build per run). It sends a single push
notification only if the push failed, or if a brief flagged something act-now urgent.

Full mechanics live in [`pages-briefings-routine-prompt.md`](pages-briefings-routine-prompt.md).

## One-time GitHub Pages setup

Repo **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `/docs`**.
The `docs/.nojekyll` file is already present so Pages serves the HTML as-is.
