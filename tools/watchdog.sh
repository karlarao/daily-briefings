#!/usr/bin/env bash
# Step-4f watchdog. Stall is not slow.
#
# CRITICAL (2026-09-11 finding, re-verified 2026-09-12): tasks/<id>.output are
# SYMLINKS into ~/.claude/projects/.../subagents/agent-<id>.jsonl. `stat -c %Y`
# on the symlink returns the SYMLINK's own mtime, frozen at creation — so every
# agent reads as flatlined ~10 min in. Always `stat -Lc` to follow the link.
#
# 2026-09-12 also supersedes the 2026-09-08 "the pulse does not exist in this
# harness" addendum: the transcripts here are real files that grow (290KB-500KB
# within 4 minutes of launch). The signal exists; it was the unfollowed symlink
# that made it look absent.
TD="${TASKS_DIR:-${CLAUDE_SESSION_TASKS:-}}"
# Fall back to the session's tasks/ dir relative to this script when the env var
# is unset. Added 2026-09-17: setting TASKS_DIR inline means writing
# `TASKS_DIR=… bash watchdog.sh`, and a Bash compound that STARTS with a VAR=
# assignment matches no permission rule, so the whole command prompts — the
# exact shape that parked the 09-12 and 09-15 runs. The script finds its own
# tasks/ dir instead. Layout: <session>/scratchpad/tools/watchdog.sh -> <session>/tasks
if [ -z "$TD" ] || [ ! -d "$TD" ]; then
  TD="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)/tasks"
fi
if [ -z "$TD" ] || [ ! -d "$TD" ]; then
  echo "watchdog: set TASKS_DIR to this session's tasks/ dir" >&2; exit 2
fi
NOW=$(date +%s)
STALL=${1:-600}   # seconds of no transcript growth before an agent is "parked"
live=0; parked=0
for f in "$TD"/a*.output; do
  [ -e "$f" ] || continue
  id=$(basename "$f" .output)
  m=$(stat -Lc %Y "$f" 2>/dev/null) || continue
  sz=$(stat -Lc %s "$f" 2>/dev/null)
  age=$((NOW - m))
  if [ "$age" -gt "$STALL" ]; then
    printf 'PARKED  %s  age=%ss  size=%s\n' "$id" "$age" "$sz"; parked=$((parked+1))
  else
    live=$((live+1))
  fi
done
printf 'watchdog: %d live, %d parked (>%ss without transcript growth)\n' "$live" "$parked" "$STALL"
