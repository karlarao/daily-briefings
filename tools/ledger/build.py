#!/usr/bin/env python3
"""
Rebuild claude.html by replacing ONLY the DATA block of the existing template.

The template (style + script below the DATA markers) is never touched -- that is
the contract in the routine prompt. Encoding is done once by json.dumps, then
verified by parsing the emitted block back (the "never double-escape" rule).
"""
import json, re, sys, argparse, os

MARK_A = "/* ===== DATA — the routine replaces this whole block each run ===== */"
MARK_B = "/* ===== end DATA ===== */"

FIELDS = ["id", "name", "group", "cadence", "freq", "updated", "status", "tokens", "md", "flag_reason"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--sections", required=True)
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--synthesis", default="")
    ap.add_argument("--whatsnew", default="")
    ap.add_argument("--generated", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    tpl = open(a.template, encoding="utf-8").read()
    i, j = tpl.index(MARK_A), tpl.index(MARK_B)
    head, tail = tpl[:i], tpl[j + len(MARK_B):]

    secs = json.load(open(a.sections))
    out_secs = []
    for s in secs:
        p = os.path.join(a.briefs, s["id"] + ".md")
        md = open(p, encoding="utf-8").read().strip() if os.path.exists(p) else ""
        row = {k: s.get(k, "") for k in FIELDS}
        row["md"] = md
        row["tokens"] = int(s.get("tokens", 0) or 0)
        row["freq"] = int(s["freq"])
        if not md:
            row["status"] = "pending"
            row["updated"] = ""
        out_secs.append(row)

    synth = open(a.synthesis, encoding="utf-8").read().strip() if a.synthesis and os.path.exists(a.synthesis) else ""
    wn = json.load(open(a.whatsnew)) if a.whatsnew and os.path.exists(a.whatsnew) else None
    if wn:
        for k in ("new", "changed", "ongoing"):
            for r in wn.get(k, []):
                r.pop("_sev", None)

    data = {
        "generated": a.generated,
        "summary": a.summary,
        "model": a.model,
        "synthesis": synth,
        "whatsnew": wn,
        "sections": out_secs,
    }

    blob = json.dumps(data, ensure_ascii=False, indent=None)
    # guard: a literal "</script" inside any string would close the tag early.
    blob_js = blob.replace("</", "<\\/")

    # ---- assertions (the "never double-escape" contract) ----
    back = json.loads(blob)
    assert back["synthesis"] == synth, "synthesis round-trip mismatch"
    if synth:
        assert "\n" in back["synthesis"], "synthesis lost its real newlines"
        assert "\\n" not in back["synthesis"], "synthesis contains a literal backslash-n"
    for s in back["sections"]:
        if s["md"]:
            assert "\\n" not in s["md"], "md for %s contains a literal backslash-n" % s["id"]
    assert len(back["sections"]) == len(secs)

    block = MARK_A + "\nwindow.BRIEFINGS = " + blob_js + ";\n" + MARK_B
    html = head + block + tail
    open(a.out, "w", encoding="utf-8").write(html)

    done = sum(1 for s in out_secs if s["status"] not in ("", "pending"))
    print("wrote %s  (%d bytes, %d/%d topics built, synthesis=%s, whatsnew=%s)"
          % (a.out, len(html.encode()), done, len(out_secs), bool(synth), bool(wn)), file=sys.stderr)


if __name__ == "__main__":
    main()
