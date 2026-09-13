#!/bin/bash
# Auto-approve Bash commands that use ONLY the read-only tool set the routine is
# already allowed to run, so an unattended run never parks on a permission
# prompt because of the SHAPE of a command. Sister of artifact-allow.sh.
#
# WHY THE ALLOWLIST IS NOT ENOUGH. `Bash(cp *)` style rules match the first word
# of each `&&`-piece. On 2026-09-07 and again 2026-09-12 the run wrote
#     SP="/tmp/..." && cp ... && wc -c ... && python3 - <<'PY' ... PY
# and the first piece is a variable assignment, which no rule can match, so the
# whole compound prompted. On 09-12 nobody was present: the session parked,
# the container suspended, all 19 research agents died, and the day's edition
# shipped seven hours late. A prompt in an unattended run is a kill switch.
#
# WHAT THIS HOOK DOES. It reads the full command, strips heredoc bodies, quoted
# strings and leading VAR=... assignments, splits into pieces, and allows the
# command only if EVERY piece's command word is in ALLOW. It grants nothing the
# allowlist did not already grant (python3 and cp were allowlisted on 09-07);
# it only stops the assignment/heredoc/`$(...)` shapes from defeating the rules.
# Two hard refusals sit on top: anything touching a `.claude/settings` file, and
# any redirect into a `.claude/` directory (the 2026-09-02 killer line) — those
# fall through to the normal prompt no matter what.
#
# On ANY doubt it prints nothing and exits 0, which means "no opinion": the
# normal permission flow runs unchanged. It never emits a deny.
# Logs one line per firing to /tmp/claude-bash-hook.log (event, mode, verdict).
input=$(cat)
python3 - "$input" <<'EOF'
import json, sys, re, datetime

try:
    d = json.loads(sys.argv[1])
except Exception:
    d = {}
ev = d.get("hook_event_name", "")
cmd = (d.get("tool_input") or {}).get("command") or ""

# Commands the routine is allowed to run unattended. Everything here is either
# already in .claude/settings.json permissions.allow, auto-approved by the cloud
# harness as sandbox-safe (git, ls, date), or a shell control word.
ALLOW = {
    # the allowlisted read-only text tools
    "sed", "grep", "head", "tail", "cat", "awk", "cut", "wc", "sort", "uniq",
    # allowlisted 2026-09-07 for the lens build and ledger scripts
    "cp", "mkdir", "python3",
    # what the routine's own steps use (step 0, step 5, watchdog)
    "git", "cd", "ls", "date", "echo", "printf", "touch", "stat", "diff",
    "tr", "seq", "basename", "dirname", "sleep", "true", "test", "[", ":",
    "set", "export", "pwd", "wc", "env", "which", "type",
    # shell control words seen as a "command" after splitting
    "for", "while", "until", "do", "done", "if", "then", "else", "elif", "fi",
    "case", "esac", "in", "break", "continue", "return",
}

def refuse(reason):
    return None, reason

def check(cmd):
    if not cmd.strip():
        return refuse("empty")
    # Hard refusals — regardless of anything else below.
    if re.search(r"\.claude/settings", cmd):
        return refuse("touches a .claude/settings file")
    if re.search(r">>?\s*\S*\.claude/", cmd):
        return refuse("redirect into a .claude/ directory")
    if re.search(r"(^|[\s;&|])(sudo|su|curl|wget|nc|ssh|scp|rm|dd|chmod|chown|eval|source)\b", cmd):
        return refuse("uses a command outside the read-only set")

    s = cmd
    # 1. Drop heredoc bodies: `<<'TAG'` / `<<TAG` / `<<-TAG` up to a line == TAG.
    #    Their contents are the interpreter's, not the shell's.
    while True:
        m = re.search(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n", s)
        if not m:
            break
        tag = m.group(2)
        end = re.search(r"^\s*%s\s*$" % re.escape(tag), s[m.end():], re.M)
        s = s[:m.start()] + " " + (s[m.end() + end.end():] if end else "")
    # 2. Blank out quoted strings so operators inside them do not split.
    s = re.sub(r"'[^']*'", "''", s)
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    # 3. Lift `$(...)` and backtick substitutions out as their own pieces.
    pieces = []
    def lift(m):
        pieces.append(m.group(1))
        return " "
    for _ in range(6):
        s2 = re.sub(r"\$\(([^()]*)\)", lift, s)
        s2 = re.sub(r"`([^`]*)`", lift, s2)
        if s2 == s:
            break
        s = s2
    # 4. Split on the shell operators and newlines.
    pieces += re.split(r"&&|\|\||\||;|&|\n", s)
    for p in pieces:
        p = p.strip()
        # strip leading VAR=... assignments (the 09-12 shape) and a leading `!`
        p = re.sub(r"^(!\s*)?(\w+=(\"\"|''|\S*)\s*)+", "", p).strip()
        if not p:
            continue
        # strip redirects / brace / paren noise before the first word
        p = re.sub(r"^[({]\s*", "", p)
        word = p.split()[0]
        word = word.rsplit("/", 1)[-1]           # /usr/bin/python3 -> python3
        word = word.strip("()}{")
        if word.startswith("$") or word in ("''", '""'):
            return refuse("command word is a variable or literal: %r" % word)
        if word not in ALLOW:
            return refuse("command not in read-only set: %r" % word)
    return True, "every piece is a read-only/allowlisted command"

ok, why = check(cmd)
line = "%s %s mode=%s verdict=%s reason=%s cmd=%s\n" % (
    datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), ev,
    d.get("permission_mode"), "allow" if ok else "pass", why,
    cmd.replace("\n", "\\n")[:160])
try:
    open("/tmp/claude-bash-hook.log", "a").write(line)
except Exception:
    pass

if not ok:
    sys.exit(0)                     # no opinion -> normal permission flow
if ev == "PermissionRequest":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest",
                                             "behavior": "allow"}}))
elif ev == "PreToolUse":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "allow",
                                             "permissionDecisionReason":
                                             "read-only command set pre-approved by repo hook"}}))
EOF
exit 0
