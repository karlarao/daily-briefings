#!/usr/bin/env python3
"""Rewrite curate.py's PICKS / PIN_ONGOING / EXCLUDE_ONGOING from the RAW rows.

Why this exists (2026-10-19 finding): those lists are matched by SUBSTRING
against the raw row titles, and the briefs use em/en dashes and curly quotes
where a human retypes ASCII -- so a hand-typed target silently misses every
row. curate.py makes a missing PIN fatal (2026-09-16) but a missing PICK is
only a warning, so a mistyped pick quietly drops the day's most consequential
row off the card. Type a LOOSE fragment; this resolves it against the real rows
and writes the EXACT slice into curate.py -- the same discipline as
interpolating a number instead of typing it.

Usage:
    python3 derive_lists.py probe "<loose fragment>" [...]
    python3 derive_lists.py write picks.txt pins.txt excl.txt
"""
import json, os, re, sys, unicodedata

SP = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(SP, "whatsnew.raw.json")

_DASHES = "‐‑‒–—―−"
_SQUOTE = "‘’‛"
_DQUOTE = "“”"


def _fold(ch):
    if ch in _DASHES:
        return "-"
    if ch in _SQUOTE:
        return "'"
    if ch in _DQUOTE:
        return '"'
    if ch.isspace():
        return " "
    return ch.lower()


def normmap(s):
    """Return (normalised, idx) where idx[i] is the ORIGINAL offset of norm[i].

    Whitespace runs collapse to one space, so the mapping is NOT 1:1 and cannot
    be recovered by re-walking the original afterwards -- that was the bug in the
    first cut of this helper (it returned 'ejectsTLS1.0/1.1' for a clean target).
    The index map has to be built while normalising.
    """
    s = unicodedata.normalize("NFKC", s)
    out, idx, prev_space = [], [], False
    for i, ch in enumerate(s):
        f = _fold(ch)
        if f == " ":
            if prev_space or not out:
                continue
            prev_space = True
        else:
            prev_space = False
        out.append(f)
        idx.append(i)
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def norm(s):
    return normmap(s)[0]


def resolve(target, rows):
    """[(row, exact_slice)] -- the exact substring of the title the target names."""
    t = norm(target)
    hits = []
    for r in rows:
        title = unicodedata.normalize("NFKC", r["title"])
        n, idx = normmap(title)
        i = n.find(t)
        if i < 0:
            continue
        hits.append((r, title[idx[i]:idx[i + len(t) - 1] + 1]))
    return hits


def _selftest():
    rows = [
        {"title": "Redshift rejects TLS 1.0/1.1 — 2026-10-31, 11 days out"},
        {"title": "DBR 10.4 LTS reaches end of life – 2026-11-01"},
        {"title": "pgvector  CVE-2026-103484   fixed in 0.8.7"},
        {"title": "Snowflake’s “CoWork” default flips 10-26"},
    ]
    cases = [
        ("rejects TLS 1.0/1.1 - 2026-10-31", "rejects TLS 1.0/1.1 — 2026-10-31"),
        ("end of life - 2026-11-01", "end of life – 2026-11-01"),
        ("pgvector CVE-2026-103484 fixed", "pgvector  CVE-2026-103484   fixed"),
        ("snowflake's \"cowork\" default", "Snowflake’s “CoWork” default"),
        ("no such row at all", None),
    ]
    ok = 0
    for t, want in cases:
        h = resolve(t, rows)
        got = h[0][1] if h else None
        if got == want:
            ok += 1
        else:
            print("  FAIL %r -> %r want %r" % (t, got, want))
    return "%d/%d" % (ok, len(cases))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    if mode == "selftest":
        print("derive_lists self-test:", _selftest())
        return
    raw = json.load(open(RAW))
    if mode == "probe":
        pool = raw["new"] + raw["changed"] + raw["ongoing"]
        for target in sys.argv[2:]:
            hits = resolve(target, pool)
            print("== %r -> %d hit(s)" % (target, len(hits)))
            for r, exact in hits[:6]:
                print("   [%s/%s] %s" % (r.get("topic", "?"), r.get("sev", "?"), r["title"][:160]))
                print("     exact: %r" % exact)
        return
    if mode == "write":
        blocks = {}
        for name, path, pool in (
                ("PICKS", sys.argv[2], raw["new"]),
                ("PIN_ONGOING", sys.argv[3], raw["ongoing"]),
                ("EXCLUDE_ONGOING", sys.argv[4], raw["ongoing"])):
            lines, miss = [], []
            for target in open(path, encoding="utf-8"):
                target = target.strip()
                if not target or target.startswith("#"):
                    continue
                hits = resolve(target, pool)
                if not hits:
                    miss.append(target)
                    continue
                lines.append(hits[0][1])
            if miss:
                print("MISS in %s: %s" % (name, json.dumps(miss, ensure_ascii=False)),
                      file=sys.stderr)
                raise SystemExit(2)
            blocks[name] = lines
        src = open(os.path.join(SP, "curate.py"), encoding="utf-8").read()
        for name, lines in blocks.items():
            body = "%s = [\n%s\n]" % (
                name, "\n".join("    %s," % json.dumps(x, ensure_ascii=False) for x in lines))
            pat = re.compile(r"^%s = \[.*?^\]" % name, re.S | re.M)
            src, n = pat.subn(lambda m, b=body: b, src)
            if n != 1:
                raise SystemExit("could not rewrite %s (matched %d)" % (name, n))
            print("%s: %d entries" % (name, len(lines)))
        open(os.path.join(SP, "curate.py"), "w", encoding="utf-8").write(src)
        return
    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
