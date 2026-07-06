# GitHub Pages Runbook — Daily Briefings

Operational notes for publishing the auto-generated dashboard to GitHub Pages, plus
the failure modes we actually hit and how to fix them. Written for **the next person**
*and* **the LLM** running the scheduled routine.

> TL;DR — The routine writes `claude.html` to the **root of the `gh-pages` branch** and
> pushes once per run. GitHub Pages auto-builds and serves it. The content is almost never
> the problem; the **Pages *deploy* step** is the flaky part. If the live site looks stale,
> it's a failed/stuck deploy or a cache — not your data. Verify via git + the Actions API,
> not the browser.

---

## 1. How publishing works (the mental model)

```
scheduled run (ephemeral VM, nothing persists)
   │  build claude.html from the prompt template + fresh 18-brief data
   ▼
commit + push  ──►  gh-pages branch (root)
                     ├── index.html    (static landing page — NOT touched by the routine)
                     ├── claude.html    (the dashboard — OVERWRITTEN every run)
                     └── .nojekyll      (serve HTML verbatim; skip Jekyll)
   │
   ▼
GitHub "pages build and deployment" workflow fires automatically on push
   │  uploads a github-pages artifact, then deploys it
   ▼
served at  https://<owner>.github.io/<repo>/            (index.html)
           https://<owner>.github.io/<repo>/claude.html (the dashboard)  ◄── the real URL
```

Key facts:
- **Pages source = `gh-pages` / root.** This is set once in repo settings and is
  **independent of the repo's default branch** (see §6 — the default branch is a red herring).
- **`.nojekyll` must exist at the root**, or Jekyll may mangle/ignore files. The routine
  `touch`es it every run defensively.
- The routine touches **only `claude.html`** (and `.nojekyll`). `index.html` is the
  hand-written landing page and is left alone.
- **One push per run** → one Pages build per run. Don't push per-topic.

---

## 2. First-time setup (do this once)

1. Create the `gh-pages` branch with `index.html`, `claude.html` (a placeholder is fine),
   and an empty `.nojekyll` at the root.
2. Repo **Settings → Pages → Build and deployment → Source: "Deploy from a branch"**,
   **Branch: `gh-pages` / `/ (root)`**. Save.
3. Wait for the first "pages build and deployment" run to go green (Actions tab).
4. Confirm `https://<owner>.github.io/<repo>/claude.html` loads.

That's it. From then on every push to `gh-pages` auto-deploys.

---

## 3. The failure modes we actually hit (and the fixes)

These are real, from this session. Expect them.

### 3a. Transient "Deployment failed, try again later"
The build/artifact uploads fine, the deployment is *created*, then the final status check
fails:
```
Created deployment for <sha> …
Getting Pages deployment status...
##[error]Deployment failed, try again later.
```
This is a **GitHub backend hiccup, not your content.** The committed `claude.html` on
`gh-pages` is correct; Pages just keeps serving the last *successful* deploy.

**Fix:** re-run the failed "pages build and deployment" job (Actions → the run → "Re-run
failed jobs"), **or** push a fresh commit (see 3b, which is more reliable).

### 3b. Re-run gets stuck `queued` and never starts
After re-running the failed deploy, the new run can sit in **`queued`** in the Pages deploy
queue and never execute (we saw it stuck ~6 min with `total_jobs: 0`).

**Fix (most reliable):** push a **fresh commit** to `gh-pages`. Pages uses a concurrency
group, so a new deploy **supersedes** the stuck one and runs cleanly. A content-neutral
change is enough — e.g. append a trailing HTML comment:
```bash
printf '\n<!-- redeploy %s -->\n' "$(date -u +%FT%TZ)" >> claude.html
git add claude.html && git commit -m "redeploy: force fresh Pages build" && git push origin gh-pages
```
(The routine writes the whole file each run anyway, so a normal next run also clears a stuck
deploy — you only need this for a manual out-of-band fix.)

### 3c. Browser / CDN cache shows the old page after a good deploy
GitHub's CDN and your browser cache aggressively. After a deploy goes green you may still see
the old page.

**Fix:** hard-refresh (`Cmd/Ctrl + Shift + R`) or open an incognito window. Give the CDN a
minute. If incognito shows the new page, it was purely a local cache.

---

## 4. How to diagnose "the site looks stale" — in order

**Do not trust the browser.** Check the source of truth top-down:

1. **Is the correct content on the branch?**
   ```bash
   git fetch origin gh-pages
   git show origin/gh-pages:claude.html | head -1        # expect the dashboard <title>
   git show origin/gh-pages:claude.html | grep -c "hasn't published"   # expect 0 (placeholder gone)
   ```
   If this is correct (it usually is), the problem is the deploy, not the data.

2. **Did the Pages deploy for that commit succeed?** Check the "pages build and deployment"
   workflow. Via the GitHub API / MCP:
   - list workflow runs filtered to `branch: gh-pages`, look at the top run's
     `head_sha`, `status`, `conclusion`.
   - `conclusion: failure` → §3a. `status: queued` and not moving → §3b.
   - Get the failed job logs to see the exact error.

3. **Is it just cache?** → §3c (hard-refresh / incognito).

4. **Default branch?** Irrelevant to Pages — do **not** chase this (see §6).

> ⚠️ **Cloud-execution caveat:** in the remote agent environment the outbound proxy
> **blocks `*.github.io`** (403 on CONNECT). So you **cannot** `curl`/WebFetch the live Pages
> URL to verify from inside a run. Verify via **git** (`git show origin/gh-pages:claude.html`)
> and the **Actions API** (workflow run status/logs) instead. A 403 to github.io from the
> sandbox says nothing about whether Pages is healthy.

---

## 5. Data lifecycle — what happens to old runs

- **Live site: overwritten.** Each run rebuilds `claude.html` and commits over the previous
  one. The dashboard renders only the current run's `window.BRIEFINGS`, so only the latest
  briefs are visible. File size stays ~150 KB; it does not grow.
- **Git history: nothing is lost.** Each run is a **new commit** on `gh-pages`
  (`briefings <timestamp>`). The full prior `claude.html` — all 18 briefs — lives in the
  previous commit. `gh-pages` is effectively a chronological archive, one commit per run.
  - Read an old run: `git show <commit>:claude.html > old.html` (or GitHub → `claude.html`
    → History → pick a version).
- **No archive UI.** The dashboard is a "today's snapshot" board by design; there's no
  date-picker. If you want browsable history, change the routine to also write a dated copy
  (e.g. `claude-YYYY-MM-DD.html`) plus an index page — small prompt change, not done today.

---

## 6. Branch layout & the "default branch" gotcha

Branches you'll see and what they're for:

| Branch | Role |
|---|---|
| `main` | Source of truth: the routine prompt (`pages-briefings-routine-prompt.md`), README, this runbook. |
| `gh-pages` | The **published site** (`index.html`, `claude.html`, `.nojekyll`). Pages serves this. |
| `claude/new-session-*`, `claude/<name>` | Auto-created working branches from Claude Code **web** sessions. Tend to accumulate; usually stale. |

**Why the default branch may be a `claude/new-session-*` branch:** when a repo is first
initialized *inside* a Claude Code web session, that session commits on an auto-named
`claude/new-session-<id>` branch. The **first branch pushed to a brand-new empty GitHub repo
becomes the default branch.** If nobody changes it afterward, the default stays pointed at
that original session branch even after real work moves to `main`/`gh-pages`.

**Does it matter?** For the pipeline, **no** — Pages is bound to `gh-pages`/root and the
routine checks out `gh-pages` explicitly, so neither cares about the default branch. The only
real downsides are human-facing:
- `git clone` checks out the (stale) default branch; new PRs default their base to it.
- The repo homepage shows the stale branch's files + a perpetual "main had recent pushes" nag.
- `claude/*` branches slowly pile up (one per web session).

**Cleanup (optional, one-time):** Settings → General → Default branch → set to `main`
(can't be done via API/`gh` in the sandbox — it's a manual UI step), then delete the stale
`claude/*` branches (GitHub blocks deleting the *default* branch, so reorder first).

> **Status 2026-07-06: DONE.** Default branch switched to `main` (manual UI step). The stale
> `claude/*` session branches were force-pointed at `main`'s HEAD (zero-diff aliases; the
> sandbox's git gateway 403s ref-*deletion*, so the branch *names* need one manual trash-icon
> click on the Branches page — content-wise there is nothing left on them).

---

## 7. Checklist for the LLM running the routine

Follow the routine prompt, but bake in these hard-won steps:

1. **Bootstrap:** `git checkout gh-pages && git pull --ff-only`, `touch .nojekyll`, set the
   commit author. (Default branch is irrelevant — always operate on `gh-pages` explicitly.)
2. **Build** `claude.html` = template + the run's `window.BRIEFINGS` (JSON-encode `md` /
   `flag_reason`; un-escape stray `&amp;`/`&lt;`/`&gt;` that sneak in from tool transport).
3. **One push** at the end: `git add claude.html .nojekyll && git commit && git push origin gh-pages`.
4. **Self-verify the deploy** (don't assume the push = a live update):
   - Check the "pages build and deployment" run for your commit SHA.
   - `failure` → re-run failed jobs. `queued`/stuck → push a fresh commit to supersede it (§3b).
   - Can't reach github.io from the sandbox (proxy 403) — verify via git + Actions API only.
5. **Notify** per the routine's rules (push failed → notify; else only if something is urgent).
   A stuck/failed *deploy* that you couldn't clear is itself notification-worthy ("published to
   gh-pages but Pages deploy failed/stuck").

---

## 8. Quick reference

```bash
# What's actually on the published branch right now
git show origin/gh-pages:claude.html | head -1

# History of the dashboard (each entry = one run)
git log --oneline --follow -- claude.html      # run on gh-pages

# Recover a past run
git show <commit>:claude.html > past-run.html

# Force a fresh Pages deploy (clears a stuck/failed one)
printf '\n<!-- redeploy %s -->\n' "$(date -u +%FT%TZ)" >> claude.html
git add claude.html && git commit -m "redeploy: force fresh Pages build" && git push origin gh-pages
```

Live URLs:
- Landing: `https://<owner>.github.io/<repo>/`
- Dashboard: `https://<owner>.github.io/<repo>/claude.html`  ← the one people want

---

*Captured from a live setup/debug session: initial publish, a transient Pages deploy failure,
a stuck deploy queue, cache confusion, and the default-branch red herring — all resolved by a
fresh commit to `gh-pages` + a hard refresh.*
