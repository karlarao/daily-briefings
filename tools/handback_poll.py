#!/usr/bin/env python3
"""Exit when every agent transcript holds a real SubagentHandback TOOL CALL.

Why not grep: the literal string "SubagentHandback" appears in every agent's
system prompt as a tool DEFINITION, so `grep -q SubagentHandback` matches
within seconds of launch and a poller built on it always fires immediately
(observed 2026-10-20: 19/19 "done" ~15 min in, with zero agents finished).
The only real signal is a content block with type=="tool_use" and
name=="SubagentHandback".
"""
import json, glob, os, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WANT = int(sys.argv[1]) if len(sys.argv) > 1 else 19


def hands(path):
    n = 0
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                c = (r.get("message") or {}).get("content")
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_use" \
                                and b.get("name") == "SubagentHandback":
                            n += 1
    except Exception:
        pass
    return n


while True:
    files = sorted(glob.glob(os.path.join(BASE, "tasks", "a*.output")))
    done = [f for f in files if hands(f) >= 1]
    print("handback: %d/%d" % (len(done), len(files)), flush=True)
    if len(done) >= WANT:
        sys.exit(0)
    time.sleep(60)
