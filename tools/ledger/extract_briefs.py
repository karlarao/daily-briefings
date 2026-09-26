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

# Agent ids are minted per launch, so this map changes every run. Since
# 2026-09-17 the run writes <session>/scratchpad/agents.json as {topic: agentId}
# right after launching (the ids are in hand there anyway) and this file reads
# it -- no source edit needed. The literal map below is only the fallback for a
# session that did not write that file.
_AGENTS_JSON = os.path.join(BASE, "scratchpad/agents.json")
AGENTS = {}
if os.path.exists(_AGENTS_JSON):
    try:
        with open(_AGENTS_JSON, encoding="utf-8") as fh:
            AGENTS = {aid: tid for tid, aid in json.load(fh).items()}
    except Exception as exc:                       # malformed -> fall back
        print("warn: could not read %s (%s); using built-in map"
              % (_AGENTS_JSON, exc), file=sys.stderr)
        AGENTS = {}
if not AGENTS:
    AGENTS = {
        "a7f779151f5c53d4b": "aidaily",
        "a299d564639db72f8": "aiappdev",
        "ac5ee44f7aef7188b": "nl2sql",
        "ad6d25c9b0367d3df": "aihw",
        "a8d92de70c405b95a": "dbhw",
        "afe479cc30c91d281": "challengers",
        "a0d33107d01580bcd": "oltp",
        "a9ae33773a304b3e1": "mongodb",
        "adea67548840ed8cf": "formats",
        "a4e07a0256b8e4f38": "appdev",
        "a0b1e3989461cca7c": "frontend",
        "a586cdcbff60c678e": "devops",
        "a1ecd820706b2d41c": "mobile",
        "a02ed62f8ccbb037e": "oracle",
        "a07217f4a3163a2e6": "snowflake",
        "a50f07c5859bcea55": "databricks",
        "ae5dc8c0676f4b429": "bigquery",
        "ab93208e2d7de8227": "redshift",
        "a8f0f9e2e9ed29e0e": "fabric",
    }


def final_text(path):
    """Last assistant message's concatenated text blocks, plus token usage."""
    last, handback, usage = None, "", 0
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
                # 2026-09-21: in this harness an agent returns its brief through a
                # SubagentHandback tool call, and its trailing *text* block is only a
                # short "handing back" stub -- 11 of 19 agents this run. The full
                # STATUS/FLAG_REASON/BRIEF contract is the handback's `message`
                # field. Keep it and prefer whichever of the two is the real brief.
                for c in (m.get("content") or []):
                    if (isinstance(c, dict) and c.get("type") == "tool_use"
                            and c.get("name") == "SubagentHandback"):
                        hb = (c.get("input") or {}).get("message") or ""
                        if hb.strip():
                            handback = hb
                u = m.get("usage") or {}
                if u:
                    usage = max(usage, (u.get("input_tokens", 0) or 0)
                                + (u.get("output_tokens", 0) or 0)
                                + (u.get("cache_read_input_tokens", 0) or 0)
                                + (u.get("cache_creation_input_tokens", 0) or 0))
    # Prefer the handback when it actually carries the contract, or when the
    # trailing text block is clearly just a stub. Never silently drop a longer
    # real brief in favour of a shorter one.
    if handback:
        has_contract = re.search(r"^[`*\s]*BRIEF[`*]*\s*:", handback, re.M | re.I)
        if has_contract or len(handback) > len(last or ""):
            last = handback
    return last, usage


# Caller-directed chatter some agents append: strip it so it never reaches the
# dashboard or gets mined as a fake headline by step 4c.
#
# 2026-09-26: this pattern MUST stay narrow. It previously also matched a bare
# "Environment note:", which SHARED_RULES explicitly asks agents to write as an
# in-brief note under the TL;DR -- so the stripper ate 17 of 19 briefs at their
# second paragraph and left ~500-char stubs that still parsed. The bare form is
# gone; only an explicitly caller-DIRECTED heading matches now.
_TAIL = re.compile(
    # Edition 074 found the opposite failure: agents write this section as a
    # "## Environment notes for the run owner" HEADING, and a prefix allowing
    # only `**` matched none of them, so 112 chatter lines were mined as fake
    # headlines. Allow a heading marker AND bold; both days' fixes, one pattern.
    r"\n(?:-{3,}\s*\n)?\s*#{0,4}\s*\*{0,2}"
    r"(?:(?:Report|Notes?|Summary|Environment\s+notes?)\s+(?:to|for)\s+(?:the\s+)?"
    r"(?:caller|run[\s-]?owner|orchestrator|run\s+owner)"
    r"|Caller report)"
    r"\b[:\s*]", re.I)


def _strip_caller_chatter(body):
    """Drop a caller-directed trailing section -- but only if it IS a tail.

    Guard rail (2026-09-26): a heading match near the TOP of the brief is not a
    tail, it is a false positive, and acting on it silently destroys the brief.
    Refuse any strip that would remove more than half the text.
    """
    m = _TAIL.search(body)
    if not m:
        return body
    kept = body[:m.start()].rstrip()
    if len(kept) < 0.5 * len(body.strip()):
        return body          # not a tail -- leave the brief intact
    return kept


def _split_trailing_contract(txt):
    """Trailing-contract shape: <brief> ... \nSTATUS: ok\nFLAG: ...

    Returns None when the text does not end in a status block, so the caller
    can fall through to the original header-contract parser.
    """
    m = None
    for m in re.finditer(r"^[`*\s>-]*STATUS[`*]*\s*:?\s*[`*]*\s*(urgent|slow|ok)\b",
                         txt, re.M | re.I):
        pass
    if not m:
        return None
    status = m.group(1).lower()
    tail = txt[m.end():]
    flag = ""
    fm = re.search(r"^[`*\s>-]*FLAG(?:_?REASON)?[`*]*\s*:?\s*(.*)$",
                   tail, re.M | re.S | re.I)
    if fm:
        flag = fm.group(1).strip()
    if re.match(r"^[`*\(\[_\s]*(empty|none|n/?a)\b", flag, re.I):
        flag = ""
    flag = flag.strip().strip("`").strip()
    body = txt[:m.start()].rstrip()
    # drop a trailing rule the agent may have put above the status block
    body = re.sub(r"(?:\n\s*-{3,}\s*)+\Z", "", body).rstrip()
    # caller-directed chatter can also land ABOVE the status block; strip it
    # with the same shape-matching rule the header-contract parser uses.
    body = _strip_caller_chatter(body)
    if status != "urgent":
        flag = ""
    return status, flag, body


def split_contract(txt):
    """Pull STATUS / FLAG_REASON / BRIEF out of the agent's return value.

    Agents wrap these in backticks, bold them, or add a stray '---' line; be
    liberal in what is accepted and strict about what is written.
    """
    if not re.search(r"^[`*\s]*BRIEF[`*]*\s*:", txt, re.M | re.I):
        alt = _split_trailing_contract(txt)
        if alt:
            return alt

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
    # Use the same narrowed pattern + tail guard as the trailing-contract path,
    # so the two parsers cannot disagree about what counts as caller chatter
    # (2026-09-26: they did, and this one ate 17 briefs at their 2nd paragraph).
    body = _strip_caller_chatter(body)

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
        if not txt or not ("BRIEF" in txt.upper() or "STATUS" in txt.upper()):
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
