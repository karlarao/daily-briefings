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

**NEVER write `~/.claude/settings.json` (or anything outside the repo) from the
routine** — settled 2026-09-04 after the 2026-09-02 and 2026-09-03 runs both
parked forever on line 1 of the stored prompt (`mkdir -p ~/.claude && cat … >
~/.claude/settings.json`). Reproduced in-session: `cat` of the repo file alone
is allowed; `mkdir -p ~/.claude` alone is denied; the Write tool on
`/root/.claude/settings.json` is denied. Two independent causes: (1) `mkdir`
is not on the allowlist and every segment of a `&&` chain must match; (2) cloud
sessions gate all writes outside the working directory, and Claude's own
settings files are always gated — an allowlist cannot pre-approve editing the
allowlist. So the "merge-write user settings" idea (added 2026-08-30 because
the repo-level `Artifact` rule was not honored) is a chicken-and-egg: the line
meant to prevent prompts IS an unapprovable prompt. Consequence: the step-5c
lens publish may prompt once at the very end — accepted, non-fatal, and covered
by 5c's notification rule. The repo `"Artifact"` rule stays in
`.claude/settings.json` (harmless). If a durable fix is ever found it has to be
on the scheduler side (a routine-level permission mode), not in the prompt.

## Watchdog philosophy (agreed 2026-08-29)

Stall detection is by transcript inactivity (flatline ~10 min), NEVER by
runtime — long-running agents with a heartbeat are healthy and must not be
killed. The publish deadline binds the dashboard, not the agents: ship on time
with completed briefs, fold stragglers in with a follow-up commit.
