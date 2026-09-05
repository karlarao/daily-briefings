#!/bin/bash
# Auto-approve the built-in Artifact tool so the unattended briefings routine can
# republish the lens without parking on "Needs your approval". Wired from
# .claude/settings.json as both a PermissionRequest hook (fires in Manual /
# Accept-edits mode, where the publish prompt appears) and a PreToolUse hook
# (belt and suspenders). Logs one line per firing to /tmp so a run can show
# which permission mode it was in. See CLAUDE.md, "Artifact prompt" section.
input=$(cat)
python3 - "$input" <<'EOF'
import json, sys, datetime
try:
    d = json.loads(sys.argv[1])
except Exception:
    d = {}
ev = d.get("hook_event_name", "")
line = "%s %s tool=%s mode=%s action=%s url=%s\n" % (
    datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), ev,
    d.get("tool_name"), d.get("permission_mode"),
    (d.get("tool_input") or {}).get("action", "publish"),
    (d.get("tool_input") or {}).get("url", "-"))
try:
    open("/tmp/claude-artifact-hook.log", "a").write(line)
except Exception:
    pass
if ev == "PermissionRequest":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "behavior": "allow"}}))
elif ev == "PreToolUse":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                      "permissionDecisionReason": "Artifact tool pre-approved by repo hook"}}))
EOF
exit 0
