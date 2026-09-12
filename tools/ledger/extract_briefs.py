#!/usr/bin/env python3
"""Pull each finished research agent's final brief out of its transcript.

Usage:  python3 extract_briefs.py <session-dir> [--force]
        (session-dir is the one containing tasks/; $BRIEF_SESSION_DIR also works)

Rewrite the AGENTS map below each run -- agent ids are minted per launch.

Why this exists: re-typing a 15-20k-token brief into a Write call once per agent
costs ~40k tokens of context per topic and risks transcription drift. The agent's
final message is already on disk in its .jsonl; parse it there instead.

Maps agentId -> topic id, finds the LAST assistant text block, splits the
STATUS / FLAG_REASON / BRIEF contract out of it, and writes
  briefs/<id>.md  briefs/<id>.status  briefs/<id>.tokens
which is exactly what assemble.py + ledger.py + build.py consume.

Safe to re-run: it skips an agent whose .md already exists unless --force.
"""
import json, os, re, sys, glob

# BASE is the session dir that holds tasks/ (the harness prints it in every
# agent launch result). Override with $BRIEF_SESSION_DIR or argv[1].
BASE = os.environ.get("BRIEF_SESSION_DIR") or (
    sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "")
if not BASE:
    raise SystemExit("usage: extract_briefs.py <session-dir> [--force]  "
                     "(or set $BRIEF_SESSION_DIR)")
TASKS = os.path.join(BASE, "tasks")
BRIEFS = os.path.join(BASE, "scratchpad/tools/ledger/briefs")

# REWRITE THIS EVERY RUN: agent ids are minted per launch. Map each research
# agent's id (from its launch result) to the topic id it was given.
AGENTS = {
    "aa85aa86613b33379": "aidaily",
    "a1497bd0c7a5702dc": "aiappdev",
    "aa10adae4472b7576": "nl2sql",
    "a3541c07ccb6db00d": "aihw",
    "aaebca0463a008052": "dbhw",
    "aaa9c32336402dff4": "challengers",
    "ab40921c75e00d6fa": "oltp",
    "aa94db2694ca2b429": "mongodb",
    "a2f4668e6cbe0400e": "appdev",
    "ad17ce627390bc042": "frontend",
    "a19da6fedbf59db11": "devops",
    "a0c5ea98568a52e65": "mobile",
    "a9a87988be3300778": "formats",
    "a0638da4431e24453": "oracle",
    "a0be5f56e4aa68dad": "snowflake",
    "afa58f93f481491d1": "databricks",
    "a36819b9107f97c5e": "bigquery",
    "ac40103de42c2c885": "redshift",
    "aacadf22a802c77bb": "fabric",
}


def final_text(path):
    """Last assistant message's concatenated text blocks, plus token usage."""
    last, usage = None, 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            m = d.get("message") or {}
            if d.get("type") == "assistant" and m.get("role") == "assistant":
                parts = [c.get("text", "") for c in (m.get("content") or [])
                         if isinstance(c, dict) and c.get("type") == "text"]
                txt = "\n".join(p for p in parts if p.strip())
                if txt.strip():
                    last = txt
                u = m.get("usage") or {}
                if u:
                    usage = max(usage, (u.get("input_tokens", 0) or 0)
                                + (u.get("output_tokens", 0) or 0)
                                + (u.get("cache_read_input_tokens", 0) or 0)
                                + (u.get("cache_creation_input_tokens", 0) or 0))
    return last, usage


def split_contract(txt):
    """Pull STATUS / FLAG_REASON / BRIEF out of the agent's return value.

    Agents wrap these in backticks, bold them, or add a stray '---' line; be
    liberal in what is accepted and strict about what is written.
    """
    status = "ok"
    m = re.search(r"^[`*\s]*STATUS[`*]*\s*:?\s*[`*]*\s*(urgent|slow|ok)\b",
                  txt, re.M | re.I)
    if m:
        status = m.group(1).lower()

    flag = ""
    m = re.search(r"^[`*\s]*FLAG_?REASON[`*]*\s*:?\s*(.*?)(?=^[`*\s]*BRIEF[`*]*\s*:)",
                  txt, re.M | re.S | re.I)
    if m:
        flag = m.group(1).strip()
        # an "empty" marker in any of the shapes agents actually emit
        if re.match(r"^[`*\(\[_\s]*(empty|none|n/?a)\b", flag, re.I) or not flag:
            flag = ""
        flag = flag.strip().strip("`").strip()

    m = re.search(r"^[`*\s]*BRIEF[`*]*\s*:?\s*\n?(.*)$", txt, re.M | re.S | re.I)
    body = m.group(1) if m else txt
    # strip a leading horizontal rule / stray fence the agent may have added
    body = re.sub(r"\A(\s*-{3,}\s*\n)+", "", body).strip()

    # Some agents append a note addressed to the orchestrator AFTER the brief
    # ("Report to the caller", "Environment notes for the run owner"). That is
    # agent-to-agent chatter, not briefing content -- it must not reach the
    # dashboard, and it must not reach the step-4c extractor as fake headlines.
    # Cut at the first such marker that appears after the Filtered-out section.
    # Agents phrase this half a dozen ways ("Report to the caller", "Report for
    # the caller", "Report to caller", "Environment notes for the run owner",
    # "Report for the run owner"), so match the shape rather than the wording:
    # an optional rule, then Report/Notes aimed at the caller/run owner.
    TAIL = re.compile(
        r"\n(?:-{3,}\s*\n)?\s*\*{0,2}"
        r"(?:(?:Report|Notes?|Summary)\s+(?:to|for)\s+(?:the\s+)?"
        r"(?:caller|run[\s-]?owner|orchestrator)"
        r"|Caller report"
        r"|Environment notes?(?:\s+(?:to|for)\s+(?:the\s+)?\w+(?:\s+\w+)?)?)"
        r"\b[:\s*]", re.I)
    mt = TAIL.search(body)
    if mt:
        body = body[:mt.start()].rstrip()

    if status != "urgent":
        flag = ""
    return status, flag, body


def main():
    force = "--force" in sys.argv
    os.makedirs(BRIEFS, exist_ok=True)
    done, skipped, missing = [], [], []
    for aid, tid in AGENTS.items():
        md_path = os.path.join(BRIEFS, tid + ".md")
        if os.path.exists(md_path) and not force:
            skipped.append(tid)
            continue
        link = os.path.join(TASKS, aid + ".output")
        if not os.path.exists(link):
            missing.append(tid)
            continue
        txt, usage = final_text(os.path.realpath(link))
        if not txt or "BRIEF" not in txt.upper():
            missing.append(tid + "(no-brief)")
            continue
        status, flag, body = split_contract(txt)
        if len(body) < 400:
            missing.append(tid + "(short:%d)" % len(body))
            continue
        open(md_path, "w", encoding="utf-8").write(body + "\n")
        with open(os.path.join(BRIEFS, tid + ".status"), "w", encoding="utf-8") as fh:
            fh.write("status: %s\n" % status)
            if flag:
                fh.write("flag_reason: %s\n" % flag)
        open(os.path.join(BRIEFS, tid + ".tokens"), "w").write("%d\n" % usage)
        done.append("%s[%s,%dc,%dtok]" % (tid, status, len(body), usage))
    print("extracted: %s" % (", ".join(done) or "-"))
    print("already had: %s" % (", ".join(skipped) or "-"))
    print("not ready: %s" % (", ".join(missing) or "-"))


if __name__ == "__main__":
    main()
