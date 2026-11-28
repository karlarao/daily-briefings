#!/usr/bin/env python3
"""Exit when every agent transcript holds a real SubagentHandback TOOL CALL.

Why not grep: the literal string "SubagentHandback" appears in every agent's
system prompt as a tool DEFINITION, so `grep -q SubagentHandback` matches
within seconds of launch and a poller built on it always fires immediately
(observed 2026-10-20: 19/19 "done" ~15 min in, with zero agents finished).
The only real signal is a content block with type=="tool_use" and
name=="SubagentHandback".

Re-measured 2026-11-18, and the failure is worse than a slow poller: a run that
tested handback with `grep -q SubagentHandback` saw 19/19 "handed back" ~7 min
after launch and then got `not ready: <topic>(no-brief)` from the extractor for
all 19, because none had finished. The string lives in each agent's own tool
list inside its user/attachment records, so the match is there from second one
(3 matching lines in a fresh transcript, the first two type=user/type=attachment).
That run also re-derived this very lesson from scratch, because 2026-11-17's
branch had DROPPED this module from the lineage -- a module that falls out of
main-track takes its documented lessons with it.
"""
import json, glob, os, sys, time

def _tasks_dir():
    """Locate the session's tasks/ dir, which holds the agent transcript links.

    This used to be dirname^3 of __file__, which was right while the module sat
    in <session>/scratchpad/tools/ and became WRONG the moment it was promoted
    to <repo>/tools/ -- there it resolves to the repo's PARENT and status()
    silently returns zero rows, i.e. a clean bill of health for a directory it
    never looked in (2026-11-18; same class as longitudinal.py's output path on
    2026-11-10). A path that changes meaning when a file moves must not be a
    silent default: --base wins, then $CLAUDE_SESSION_DIR, then a walk up from
    cwd, and failing all three we say so instead of reporting 0/0.
    """
    args = sys.argv[1:]
    if "--base" in args:
        cand = [args[args.index("--base") + 1]]
    else:
        cand = []
        if os.environ.get("CLAUDE_SESSION_DIR"):
            cand.append(os.environ["CLAUDE_SESSION_DIR"])
        here = os.path.abspath(os.path.dirname(__file__))
        d = os.path.abspath(os.curdir)
        for _ in range(6):
            cand.append(d)
            d = os.path.dirname(d) or "/"
        for _ in range(4):
            cand.append(here)
            here = os.path.dirname(here) or "/"
    for c in cand:
        if glob.glob(os.path.join(c, "tasks", "a*.output")):
            return c
    return None


BASE = _tasks_dir()
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
    if BASE is None:
        raise SystemExit("handback_poll: no tasks/a*.output found -- pass --base "
                         "<session dir> or set CLAUDE_SESSION_DIR. Refusing to "
                         "report 0/0 for a directory I never read.")
    agmap = {}
    aj = os.path.join(BASE, "scratchpad/agents.json")
    if os.path.exists(aj):
        try:
            with open(aj, encoding="utf-8") as fh:
                agmap = {aid: tid for tid, aid in json.load(fh).items()}
        except Exception:
            agmap = {}
    rows = []
    now = time.time()
    for f in sorted(glob.glob(os.path.join(BASE, "tasks", "a*.output"))):
        aid = os.path.basename(f)[: -len(".output")]
        # stat() follows the symlink into
        # ~/.claude/projects/.../subagents/agent-<id>.jsonl, which is where the
        # real transcript lives; stat on the UNfollowed link gives a fixed mtime
        # and every agent then reads as flatlined (2026-09-11).
        try:
            st = os.stat(f)
            sz, age = st.st_size, int(now - st.st_mtime)
        except OSError:
            sz, age = 0, -1
        rows.append((agmap.get(aid, aid), hands(f), sz, age))
    return rows, sum(1 for r in rows if r[1] >= 1)


def poll(want):
    if BASE is None:
        raise SystemExit("handback_poll: no tasks/a*.output found -- pass --base "
                         "<session dir> or set CLAUDE_SESSION_DIR.")
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
        for name, n, sz, age in rows:
            print("%-12s hands=%d size=%8d age=%4ds" % (name, n, sz, age))
        print("handback: %d/%d  live=%d" % (done, len(rows), len(rows) - done))
        # A quiet transcript is NOT a parked agent: an agent composing a 35-50k
        # final message writes nothing until it completes (2026-11-11). Sample
        # size twice ~150s apart and compare SIZE, never a single age reading.
        sys.exit(0)
    sys.exit(poll(WANT))
