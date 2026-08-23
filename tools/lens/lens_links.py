#!/usr/bin/env python3
"""Citation mining for the Oracle Competitive Lens (guard 5's constructive half).

The lens is a synthesis pass over the day's 19 briefs, whose markdowns hold the
primary URLs — but those markdowns live only in the run's ephemeral scratchpad,
so a link not captured on the day an item first appears is gone. This module:

  1. mines (title -> url) pairs from the day's brief markdowns,
  2. resolves a citation for any lens item via the fallback chain
     primary URL -> archive_link(date) -> lens_guard.UNSOURCED,
  3. is what populates the ledger rows' "url" field so carried rows keep
     their citation across editions without re-mining.

Usage in a daily build:

    corpus = mine_briefs("briefs/")            # dir of <topic>.md from this run
    row["url"] = find_url(row["t"], corpus)    # persist on NEW ledger rows
    html_anchor = cite(row.get("url"), row.get("first_seen"))

Run `python3 lens_links.py` for the self-test.
"""
from __future__ import annotations

import difflib
import glob
import os
import re

from lens_guard import UNSOURCED, archive_link

# "- **Headline** — ..." bullets; the first URL in the bullet's next few lines
_BULLET_RE = re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*", re.M)
_URL_RE = re.compile(r"\((https?://[^\s)]+)\)")
_WORD_RE = re.compile(r"[a-z0-9.]{3,}")
_STOP = {"the", "and", "for", "with", "from", "into", "that", "this", "are",
         "was", "now", "new", "has", "have", "its", "per", "not", "still"}


def mine_briefs(briefs_dir: str) -> list[tuple[str, str, str]]:
    """Return [(headline, first_url_in_bullet, topic), ...] across every brief .md.

    `topic` is the markdown's file stem (oltp, snowflake, aihw, ...), so callers
    can restrict matching to the lane an item belongs to — the same
    same-topic-first rule the dashboard's ledger matcher uses.
    """
    corpus = []
    for path in sorted(glob.glob(os.path.join(briefs_dir, "*.md"))):
        topic = os.path.splitext(os.path.basename(path))[0]
        text = open(path).read()
        lines = text.split("\n")
        for i, ln in enumerate(lines):
            m = _BULLET_RE.match(ln)
            if not m:
                continue
            title = m.group(1).strip().rstrip(":—-–").strip()
            for j in range(i, min(i + 4, len(lines))):
                u = _URL_RE.search(lines[j])
                if u:
                    corpus.append((title, u.group(1), topic))
                    break
    return corpus


def _tokens(s: str) -> set:
    return {w for w in _WORD_RE.findall(s.lower()) if w not in _STOP}


def find_url(title: str, corpus: list[tuple[str, str, str]],
             topics: set | None = None, min_cover: float = 0.34) -> str | None:
    """Best primary URL for `title`, or None when no bullet plausibly matches.

    Lens titles are long re-summaries, not quotes of the brief headline, so raw
    sequence similarity misses real matches ("26.7: 313x on GROUP BY" vs
    "26.7 is the meatiest perf release") while generic words ("memory",
    "stable", "release") happily pair unrelated stories across vendors. Three
    defenses, in order of importance:

      * `topics` restricts candidates to the item's own lane(s) — the same
        same-topic-first rule the dashboard's ledger matcher uses. Without it
        matching runs corpus-wide and the bar is effectively higher.
      * a match must share an *anchor* token: one with a digit (versions,
        CVEs, multipliers) or one rare corpus-wide (product names).
      * score is IDF-mass of shared tokens over the *smaller* side's mass,
        because a 40-token claim can never "cover" much of itself with a
        10-token headline, and vice versa.

    Falsely linking a plausible-but-wrong primary source is worse than falling
    back to the dated archive page, so unmatched simply returns None.
    """
    import math
    df: dict = {}
    for cand_title, _u, _t in corpus:
        for t in _tokens(cand_title):
            df[t] = df.get(t, 0) + 1
    n = max(1, len(corpus))

    def idf(t: str) -> float:
        return math.log(n / (1 + df.get(t, 0))) + 1.0

    def mass(tokens) -> float:
        return sum(idf(t) for t in tokens)

    def anchors(tokens: set) -> set:
        # A digit token only anchors if the corpus doesn't see it everywhere:
        # "26.7" or "61211" identifies a story, "2026" identifies nothing.
        rare = max(2, n // 50)
        digit_cap = max(4, n // 12)
        out = set()
        for t in tokens:
            d = df.get(t, 0)
            if any(c.isdigit() for c in t):
                if 0 < d <= digit_cap:
                    out.add(t)
            elif 0 < d <= rare:
                out.add(t)
        return out

    want = _tokens(title)
    # Tokens the corpus has never seen have no discriminating power for
    # ranking within it; measure over the corpus-known part of the title.
    known = {t for t in want if df.get(t, 0) > 0}
    if not known:
        return None
    want_anchors = anchors(want)
    best, best_key = None, (0.0, 0.0)
    for cand_title, url, cand_topic in corpus:
        if topics is not None and cand_topic not in topics:
            continue
        have = _tokens(cand_title)
        shared = known & have
        if len(shared) < min(2, len(known)):
            continue
        if want_anchors and not (want_anchors & shared):
            continue
        cover = mass(shared) / max(1e-9, min(mass(known), mass(have)))
        if cover < min_cover:
            continue
        seq = difflib.SequenceMatcher(None, title.lower(), cand_title.lower()).ratio()
        if (cover, seq) > best_key:
            best, best_key = url, (cover, seq)
    return best


def cite(url: str | None, *dates: str | None, label: str = "src") -> str:
    """One citation anchor via the fallback chain.

    url present            -> <a href=url>label</a>
    else first parseable   -> archive_link(date)   ("archive MM-DD")
         YYYY-MM-DD date
    else                   -> the literal UNSOURCED marker
    """
    if url:
        safe = url.replace('"', "%22")
        return f'<a href="{safe}" target="_blank" rel="noopener">{label}</a>'
    for d in dates:
        if d and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            return archive_link(d)
    return UNSOURCED


# ------------------------------------------------------------- self-test ---
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "x.md"), "w").write(
            "## Cat\n"
            "- **ClickHouse 26.7 is the meatiest perf release of the window** — blah.\n"
            "  [release blog](https://clickhouse.com/blog/clickhouse-release-26-07)\n"
            "- **Patch 204 (1.0.394035, Aug 11, CURRENT track)** — blah\n"
            "  [notes](https://docs.aws.amazon.com/redshift/latest/mgmt/cluster-versions.html)\n")
        corpus = mine_briefs(td)
    assert len(corpus) == 2, corpus
    assert find_url("ClickHouse 26.7: 313x on GROUP BY shapes", corpus) \
        == "https://clickhouse.com/blog/clickhouse-release-26-07"
    assert find_url("Patch 204: native Iceberg v3 read/write", corpus) \
        == "https://docs.aws.amazon.com/redshift/latest/mgmt/cluster-versions.html"
    assert find_url("Entirely unrelated headline about kittens", corpus) is None

    a = cite("https://example.com/a?x=1")
    assert 'href="https://example.com/a?x=1"' in a and ">src<" in a
    b = cite(None, "carried", "2026-08-15")
    assert "archive 08-15" in b and "2026-08-15.html" in b
    assert cite(None, None) == UNSOURCED

    print("lens_links self-test OK")
