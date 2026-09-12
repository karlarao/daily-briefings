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
TD="/tmp/claude-0/-home-user-daily-briefings/61c40223-e837-5487-8b68-4c77176708b7/tasks"
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
