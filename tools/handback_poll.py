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
WANT = next((int(a) for a in sys.argv[1:] if a.isdigit()), 19)


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


def status():
    """One-shot: [(agent-or-topic, handback-count, transcript-bytes)] + done count."""
    agmap = {}
    aj = os.path.join(BASE, "scratchpad/agents.json")
    if os.path.exists(aj):
        try:
            with open(aj, encoding="utf-8") as fh:
                agmap = {aid: tid for tid, aid in json.load(fh).items()}
        except Exception:
            agmap = {}
    rows = []
    for f in sorted(glob.glob(os.path.join(BASE, "tasks", "a*.output"))):
        aid = os.path.basename(f)[: -len(".output")]
        try:
            sz = os.stat(f).st_size
        except OSError:
            sz = 0
        rows.append((agmap.get(aid, aid), hands(f), sz))
    return rows, sum(1 for r in rows if r[1] >= 1)


def poll(want):
    while True:
        files = sorted(glob.glob(os.path.join(BASE, "tasks", "a*.output")))
        done = [f for f in files if hands(f) >= 1]
        print("handback: %d/%d" % (len(done), len(files)), flush=True)
        if len(done) >= want:
            return 0
        time.sleep(60)


# 2026-11-04: the poll loop used to run at MODULE level, so `from handback_poll
# import hands` (to reuse the only non-trivial helper here) hung forever instead
# of importing -- it cost one backgrounded command and a TaskStop. A module whose
# import has side effects is not a library. Loop is behind __main__ now, and
# status() gives the one-shot view a run actually wants mid-flight.
if __name__ == "__main__":
    if "--once" in sys.argv:
        rows, done = status()
        for name, n, sz in rows:
            print("%-12s hands=%d size=%8d" % (name, n, sz))
        print("handback: %d/%d" % (done, len(rows)))
        sys.exit(0)
    sys.exit(poll(WANT))
