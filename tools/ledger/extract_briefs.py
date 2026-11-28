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
# 2026-11-26: do NOT raise here. A module-level `raise SystemExit` makes every
# function in this file unreachable without a session dir -- including
# --selftest, which could never run no matter where the __main__ block sat.
# Same class as the 2026-11-19 `patch_radar --selftest` no-op and the 2026-11-04
# "a module whose import has side effects is not a library" finding. main()
# raises instead, so importing this module is free.
_USAGE = ("usage: extract_briefs.py <session-dir> [--force|--selftest]  "
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


_CONTRACT_RE = (
    re.compile(r"^[`*\s]*BRIEF[`*]*\s*:", re.M | re.I),
    re.compile(r"^[`*\s>-]*STATUS[`*]*\s*:?\s*[`*]*\s*(?:urgent|slow|ok)\b", re.M | re.I),
)


def _has_contract(txt):
    """True when txt carries EITHER contract shape the parsers accept.

    Symmetric by design: both candidates are judged by the same predicate, so
    "which of these is the real brief" cannot depend on which slot it arrived in.
    """
    return any(p.search(txt or "") for p in _CONTRACT_RE)


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
        # 2026-11-26: prefer the handback when it carries EITHER contract shape --
        # the `BRIEF:` header marker OR a trailing `STATUS: <ok|slow|urgent>` line.
        # Length alone is NOT a safe discriminator: aiappdev emitted the full brief
        # as BOTH a trailing text block and a handback, 798 chars apart, and the text
        # block won the tiebreak. The text copy had no STATUS trailer, so the lane
        # silently parsed as `ok` while the agent had returned `urgent` on a KEV
        # clock and four provider cutovers -- exactly the 2026-11-21 failure class
        # (a status that parses perfectly and is simply wrong). The handback IS the
        # agent's final report by definition; the contract marker is what proves a
        # candidate is the real brief rather than a copy of it.
        # The contract marker decides VALIDITY; length only breaks a tie between
        # two candidates that are both valid parses. Written as a decision table
        # because the first cut collapsed cases 3 and 4 -- `hb_contract or ...`
        # short-circuits, so a contract-bearing handback won even when the text
        # block was both valid AND longer, which is the one shape that silently
        # loses content (the 2026-09-21 "never drop a longer real brief" rule).
        # The selftest below caught that on its first run.
        hb_contract = _has_contract(handback)
        last_contract = _has_contract(last or "")
        if hb_contract and not last_contract:
            last = handback                  # only the handback parses
        elif last_contract and not hb_contract:
            pass                             # only the trailing text parses
        elif len(handback) > len(last or ""):
            last = handback                  # both or neither -> longer wins
    return last, usage


_TAIL = re.compile(
    r"\n(?:-{3,}\s*\n)?\s*\*{0,2}"
    r"(?:(?:Report|Notes?|Summary)\s+(?:to|for)\s+(?:the\s+)?"
    r"(?:caller|run[\s-]?owner|orchestrator)"
    r"|Caller report"
    r"|Environment notes?(?:\s+(?:to|for)\s+(?:the\s+)?\w+(?:\s+\w+)?)?)"
    r"\b[:\s*]", re.I)


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
    mt = _TAIL.search(body)
    if mt:
        body = body[:mt.start()].rstrip()
    if status != "urgent":
        flag = ""
    return status, flag, body


def split_contract(txt):
    """Pull STATUS / FLAG_REASON / BRIEF out of the agent's return value.

    Agents wrap these in backticks, bold them, or add a stray '---' line; be
    liberal in what is accepted and strict about what is written.
    """
    # Try the TRAILING-contract parser first, unconditionally. It returns None
    # unless the text actually ends in a status block, so this is safe for the
    # header shape and strictly more capable for everything else.
    #
    # Why unconditionally (2026-11-14): the dispatch used to try it only when no
    # leading `BRIEF:` marker existed. The frontend lane emitted BOTH -- a
    # leading "BRIEF: frontend — ..." title line AND a trailing
    # STATUS/FLAG_REASON block (followed by a "RUN-OWNER NOTES" section) -- a
    # hybrid neither shape anticipated. The `BRIEF:` marker sent it down the
    # header path, which found STATUS inside the body but silently returned an
    # EMPTY flag_reason for an `urgent` lane, so the dashboard would have
    # rendered a flagged brief with no red "why this is flagged" banner. The
    # brief body itself was unaffected, which is what made the loss invisible:
    # only an explicit "every urgent section has a flag_reason" assertion
    # caught it. This is the 2026-09-13 dual-parser contract drift recurring in
    # a third shape, so the dispatch now prefers the parser that reads the END
    # of the reply, where the contract is specified to live.
    # Accept the trailing result ONLY if it actually yielded a brief. The
    # trailing parser also matches a STATUS line at the TOP of a header-shape
    # reply, where everything "before the status block" is empty -- trying it
    # first unconditionally therefore returned a 0-character brief for the
    # header shape. Gating on a non-empty brief keeps both shapes working and
    # is what the 4-case self-test below pins.
    alt = _split_trailing_contract(txt)
    if alt and alt[2].strip():
        return alt

    # 2026-11-26: default to "pending", NEVER "ok". `ok` is the one value in the
    # vocabulary that SUPPRESSES a flag, and a parser is not entitled to assert
    # that nothing needs doing. This is the 2026-11-24 rule ("when a parse
    # failure has to pick a value it must pick the LOUD one") applied one layer
    # up from assemble.py, where it was fixed first -- and this is the layer that
    # actually produced today's dropped `urgent`. assemble.py already maps
    # anything outside the vocabulary to "pending" and reports it as not-ready,
    # so the two layers agree. Every lane writes an explicit STATUS line per the
    # contract, so there is no shape that is legitimately silent about status.
    status = "pending"
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
    if not BASE:
        raise SystemExit(_USAGE)
    os.makedirs(BRIEFS, exist_ok=True)
    done, skipped, missing = [], [], []
    suspect = []
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
        # 2026-11-16: a brief extracted while its transcript was still being
        # flushed can be a DIFFERENT, earlier text block -- narration-prefixed
        # ("I have enough primary-sourced material. Writing the brief.") and
        # missing its tail. Two of 19 landed that way this run, and the only
        # visible symptom was a non-zero apply_harness_tokens delta on exactly
        # those lanes. A real brief opens with its TL;DR, so anything before
        # that is the agent talking to itself: say so loudly rather than
        # writing it silently. The durable fix is to extract AFTER the agent's
        # completion notification and re-run with --force once all lanes are
        # in; this is the detector for when that did not happen.
        # The OUTPUT FORMAT contract starts the brief at **TL;DR**, so anything
        # before it is narration and is STRIPPED, not just reported -- edition
        # 125 shipped an Oracle brief whose first rendered line was "I have what
        # I need. Writing the brief." Report every strip so a silent fix never
        # hides an incomplete transcript.
        if "TL;DR" in body[:2000]:
            i = body.find("**TL;DR")
            if i < 0:
                i = body.find("TL;DR")
            pre = body[:i].strip()
            if pre:
                suspect.append("%s(stripped %dc narration)" % (tid, len(pre)))
                body = body[i:].lstrip()
        open(md_path, "w", encoding="utf-8").write(body + "\n")
        with open(os.path.join(BRIEFS, tid + ".status"), "w", encoding="utf-8") as fh:
            fh.write("status: %s\n" % status)
            if flag:
                fh.write("flag_reason: %s\n" % flag)
        open(os.path.join(BRIEFS, tid + ".tokens"), "w").write("%d\n" % usage)
        done.append("%s[%s,%dc,%dtok]" % (tid, status, len(body), usage))
    if suspect:
        print("NARRATION STRIPPED (also a signal the transcript may have been "
              "incomplete; re-run --force after the completion notification): %s"
              % ", ".join(suspect))
    print("extracted: %s" % (", ".join(done) or "-"))
    print("already had: %s" % (", ".join(skipped) or "-"))
    print("not ready: %s" % (", ".join(missing) or "-"))



def _selftest():
    """Controls for final_text()'s handback-vs-trailing-text preference.

    Added 2026-11-26 after the length tiebreak silently dropped an `urgent`.
    EVERY case is run in BOTH directions -- a known-bad input that must flip to
    the handback AND a known-good input that must NOT be clobbered -- because a
    preference rule that only ever prefers one side is not a preference rule.
    """
    import json as _json, os as _os, tempfile as _tf

    def _rec(text=None, handback=None):
        content = []
        if text is not None:
            content.append({"type": "text", "text": text})
        if handback is not None:
            content.append({"type": "tool_use", "name": "SubagentHandback",
                            "input": {"message": handback}})
        return _json.dumps({"type": "assistant",
                            "message": {"role": "assistant", "content": content,
                                        "usage": {"input_tokens": 1, "output_tokens": 1}}})

    def _run(recs):
        d = _tf.mkdtemp()
        p = _os.path.join(d, "t.jsonl")
        open(p, "w", encoding="utf-8").write("\n".join(recs) + "\n")
        return final_text(p)[0]

    STAT = "\nSTATUS: urgent\nFLAG_REASON: a KEV clock expires tomorrow\n"
    cases = [
        # (label, trailing text, handback, which must win)
        # 1. THE 2026-11-26 BUG: handback has the STATUS contract, the trailing
        #    text copy does not, and the handback is SHORTER. Must still win.
        ("bug: shorter handback has STATUS, text does not",
         "B" * 29794, "B" * 28996 + STAT, "hb"),
        # 2. INVERSE CONTROL: a contractless handback must NOT clobber a
        #    contract-bearing text block, even though both are "the handback".
        ("inverse: contractless handback, text has STATUS",
         "C" * 500 + STAT, "handing back, see above", "last"),
        # 3. BOTH carry STATUS -> longer wins, in both directions.
        ("both have STATUS, handback longer",
         "D" * 100 + STAT, "D" * 900 + STAT, "hb"),
        ("both have STATUS, text longer",
         "E" * 900 + STAT, "E" * 100 + STAT, "last"),
        # 4. NEITHER carries a contract -> longer wins (the 2026-09-21 stub case).
        ("neither has a contract, handback longer",
         "handing back", "F" * 900, "hb"),
        ("neither has a contract, text longer",
         "G" * 900, "handing back", "last"),
        # 5. The BRIEF: header shape still wins on its own (2026-09-13 dual parser).
        ("handback carries BRIEF: header, shorter",
         "H" * 900, "BRIEF: Topic\n\n**TL;DR** short", "hb"),
    ]
    ok = 0
    for label, text, hb, want in cases:
        got = _run([_rec(text=text, handback=hb)])
        winner = "hb" if got == hb else ("last" if got == text else "?")
        if winner == want:
            ok += 1
        else:
            print("  FAIL %-46s wanted=%s got=%s" % (label, want, winner))
    # 6. A transcript with no handback at all must return the text unchanged.
    if _run([_rec(text="plain")]) == "plain":
        ok += 1
    else:
        print("  FAIL no-handback transcript")
    total = len(cases) + 1

    # --- split_contract: the status default must be LOUD, not quiet -----------
    # Each case is paired: a reply that DOES declare a status must still parse to
    # that status (no regression), and a reply that declares none must come back
    # "pending" rather than the one value that suppresses a flag.
    contract_cases = [
        ("header shape, urgent",
         "STATUS: urgent\nFLAG_REASON: a KEV clock expires tomorrow\nBRIEF: x\n\nbody",
         "urgent"),
        ("header shape, ok",
         "STATUS: ok\nBRIEF: x\n\nbody", "ok"),
        ("trailing shape, urgent",
         "**TL;DR** body text\n\nSTATUS: urgent\nFLAG_REASON: why\n", "urgent"),
        ("trailing shape, ok",
         "**TL;DR** body text\n\nSTATUS: ok\n", "ok"),
        # THE FIX: a complete-looking brief with no STATUS line anywhere. This is
        # the shape that silently became `ok` on 2026-11-26 and dropped a flag.
        ("no status line anywhere -> pending",
         "**TL;DR** a complete brief that never declares a status\n\n## News\n- x",
         "pending"),
    ]
    for label, txt, want in contract_cases:
        got = split_contract(txt)[0]
        total += 1
        if got == want:
            ok += 1
        else:
            print("  FAIL %-40s wanted=%s got=%s" % (label, want, got))

    print("extract_briefs selftest: %d/%d %s"
          % (ok, total, "PASS" if ok == total else "FAIL"))
    return ok == total


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(0 if _selftest() else 1)
    main()
