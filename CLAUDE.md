# Daily Briefings — notes for Claude sessions

This container is ephemeral. The ONLY durable state is (a) this repo and (b) the
scheduler's stored prompt. This file is the session memory — read it, keep it
current, and update it when a workflow decision is made.

## Maintenance workflow for routine changes (ESTABLISHED — do not re-ask)

When a change to the daily-briefings routine is agreed with Karl:

1. **Repo-side changes** (settings, tools, docs, specs): make them directly,
   commit, push. No step-by-step approval needed.
   - `.claude/settings.json` permission changes must land on BOTH `main` and
     `gh-pages` (a session may start on one branch and the routine checks out
     the other).
   - `gh-pages` may be pushed directly (it is the routine's publish branch).
     `main` changes go on the session's designated `claude/*` branch, pushed
     for Karl to merge (open a PR only if he asks).
2. **Stored-prompt changes** (anything altering the routine's instructions):
   only Karl can edit the scheduler. Deliver BOTH files, every time:
   - the updated PUBLIC spec `pages-briefings-routine-prompt.md` on `main`
     (private addendum and private artifact URL redacted — never add them);
   - the full PRIVATE prompt (public spec + the Oracle-lens addendum spliced
     between step 5b and step 6) as a file sent to Karl via SendUserFile, for
     copy-paste into the scheduled task. NEVER commit the private version —
     it contains the private lens artifact URL.

Ask only when a change is destructive or genuinely outside this workflow.

## Permission allowlist (why it exists — do not remove)

`.claude/settings.json` pre-approves the read-only Bash text tools (sed, grep,
head, tail, cat, awk, cut, wc, sort, uniq), each rule in both spellings
(`Bash(cmd *)` and `Bash(cmd:*)`) because docs show both formats and an
unmatched rule is harmless. Reason: on 2026-08-28 a research subagent parked
~23 hours on a permission prompt for a `sed -n` slice of a spilled WebFetch
file — nobody is present to approve prompts in scheduled runs. If a new
read-only command starts prompting, extend the list on BOTH branches.

**NEVER write `~/.claude/settings.json` from a run — and it isn't needed
(re-proven 2026-08-31, superseding the 2026-08-30 conclusion).** Two findings
from the 08-31 deep dive, both demonstrated live:

1. **Writes to `~/.claude/settings.json` prompt EVERY time, regardless of any
   allowlist.** It is Claude Code's own config file; the harness gates writes
   to it behind a manual approval that no allow rule can pre-approve. Proven
   three ways in one session: a python3 heredoc write (prompted, denied), a
   direct Write-tool call (prompted, denied), and a sandbox-bypass retry
   (prompts by design). The step-0 "merge-write bootstrap" was therefore a
   chicken-and-egg dead end — the write that grants permissions itself needs
   a permission nobody is present to grant. It also spammed Karl's phone with
   prompts for five days.
2. **The Artifact tool ran with ZERO prompts** on 2026-08-31 — `action:"list"`,
   `action:"read"` (1.1MB fetch), and the full lens publish to the existing
   URL — with NO `~/.claude/settings.json` present at all, only the repo-level
   `"Artifact"` rule. The 2026-08-30 "user-level only" conclusion is stale
   (harness behavior changed, or that failure had another cause). Keep the
   `Artifact` rule in the repo file on both branches.

Also observed 08-31: this remote harness auto-approves sandbox-safe Bash
(git, ls, python3, date ran without being allowlisted). The read-only text-tool
allowlist stays as harmless belt-and-suspenders for other harness versions.
Optional extra belt-and-suspenders (Karl's side only): the claude.ai
environment's setup script can write `~/.claude/settings.json` at container
boot, outside the permission system — one line:
`mkdir -p ~/.claude && cat /home/user/daily-briefings/.claude/settings.json > ~/.claude/settings.json`.
If a future harness regresses to the 08-30 behavior, that is the fix — never
an in-run write. If an Artifact call DOES prompt in an unattended run, skip 5c
per the addendum and put one line in the notification; do not retry a
"Denied by user" result.

## Watchdog philosophy (agreed 2026-08-29)

Stall detection is by transcript inactivity (flatline ~10 min), NEVER by
runtime — long-running agents with a heartbeat are healthy and must not be
killed. The publish deadline binds the dashboard, not the agents: ship on time
with completed briefs, fold stragglers in with a follow-up commit.

Addendum 2026-08-31: **container suspension silently kills background
subagents.** The session VM slept ~12h mid-run; on resume all 11 in-flight
research agents showed "running"-looking transcripts that never advanced, and
the harness had lost their tasks entirely (`No task found`). The watchdog's
uniform simultaneous flatline across every agent is the signature — when you
see it, don't wait per-agent: verify one task id, then relaunch the whole
batch. Relaunch worked cleanly; the run finished the same day.
