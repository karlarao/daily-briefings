#!/usr/bin/env python3
"""Guards for the Oracle Competitive Lens daily build.

The lens is not rebuilt from scratch each day. It is produced by fetching the
previous edition's published page and splicing today's sections into it, which
means every run inherits the previous run's state — including its mistakes.

Five failure modes have actually occurred. Each one is silent: the page renders,
the assertions of the day pass, and the damage is only visible by diffing against
an edition nobody re-reads. The functions here are the guards that catch them.

  1. STALE PARENT      A cached fetch returned a 2-day-old edition. The build
                       treated it as yesterday's, so a day of accumulated ledger
                       rows would have been silently reverted.
                       -> assert_parent_fresh()

  2. SHRINKING LEDGER  Sections documented as append-only (Promise Tracker, Patch
                       Radar, Benchmarks, Gaps) lost rows because today's authoring
                       pass simply did not re-mention them.
                       -> assert_no_regression()

  3. UNSPLICED SECTION An edition added class="view active" to the landing section.
                       The splice matched class="view" literally, so the section
                       silently kept the PREVIOUS day's text.
                       -> splice_sections() + its count assert

  4. HOST WRAPPER      Building from a *served* artifact page carries the host's
                       injected frame-runtime and an extra </body></html>, which
                       compound on every subsequent edition.
                       -> strip_host_wrapper()

  5. VERIFIABILITY     Cards and table rows drifted from inline source links to
     DRIFT             prose attributions ("Seen in: <topic>") that nothing can
                       click. Found 2026-08-20 at edition 040: 14 links across
                       ~15 sections, all but one in Claim Watch — inheritance had
                       copied the linkless style forward for weeks while the help
                       panel still documented the citation policy. Every factual
                       unit must carry a primary <a href>, an "archive MM-DD"
                       fallback link, or an explicit "(unsourced — verify)".
                       -> assert_link_coverage() / archive_link()

Usage sketch:

    parent_html = strip_host_wrapper(fetched_page)
    parent = load_ledger(parent_html)
    assert_parent_fresh(parent, expect_date="2026-08-09", expect_edition=29,
                        today="2026-08-10")
    carried = merge_parent(ledger, parent, superseded=SUPERSEDED)
    html = splice_sections(parent_html, sections, chips)
    html = refresh_nav(html, navmeta)
    assert_no_regression(load_ledger(html), parent)
"""
from __future__ import annotations

import datetime as _dt
import json
import re

__all__ = [
    "LensBuildError", "strip_host_wrapper", "load_ledger", "assert_parent_fresh",
    "merge_parent", "assert_no_regression", "splice_sections", "refresh_nav",
    "rewrite_identity", "ACCUMULATING",
    "ARCHIVE_BASE", "UNSOURCED", "LINK_POLICY", "archive_link",
    "assert_link_coverage", "assert_page_link_coverage",
]


class LensBuildError(AssertionError):
    """Raised when a guard trips. Always fatal: never build past one of these."""


# Sections that only ever grow. Losing a row here is data loss, not editing.
ACCUMULATING = ("benchmarks", "promises", "gaps", "patch")

_LEDGER_RE = re.compile(r'(<script type="application/json" id="lensLedger">)(.*?)(</script>)', re.S)
_SECTION_RE = re.compile(r'(<section class="view[^"]*"[^>]*id="([^"]+)"[^>]*>)(.*?)</section>', re.S)
_NAV_RE = re.compile(r'\{id:"([^"]+)",\s*name:"([^"]+)",\s*meta:"([^"]*)"')


# --------------------------------------------------------------- wrapper ---
def strip_host_wrapper(html: str, anchor: str = "<title>Oracle Competitive Lens") -> str:
    """Return stored-artifact source from a page that may be a *served* copy.

    A served artifact page is  [host frame-runtime]<body>[stored source]</body></html>.
    Publishing that verbatim re-embeds the runtime and appends another closing pair,
    so the wrapper compounds one layer per edition. Idempotent: a page that is
    already stored-source passes through untouched.
    """
    i = html.find(anchor)
    if i < 0:
        raise LensBuildError(f"anchor {anchor!r} not found — is this a lens page?")
    body = html[i:]
    body = re.sub(r"(?:\s*</body>\s*</html>\s*)+$", "\n", body)
    if "__FRAME_PREAMBLE" in body:
        raise LensBuildError("host frame-runtime survived the strip")
    return body


# ---------------------------------------------------------------- ledger ---
def load_ledger(html: str) -> dict:
    m = _LEDGER_RE.search(html)
    if not m:
        raise LensBuildError("no #lensLedger block found")
    return json.loads(m.group(2))


def write_ledger(html: str, ledger: dict) -> str:
    out, n = _LEDGER_RE.subn(
        lambda m: m.group(1) + json.dumps(ledger, ensure_ascii=False) + m.group(3), html)
    if n != 1:
        raise LensBuildError(f"ledger write touched {n} blocks, expected 1")
    return out


# ------------------------------------------------------------- freshness ---
def assert_parent_fresh(parent: dict, expect_date: str | None = None,
                        expect_edition: int | None = None,
                        today: str | None = None,
                        max_age_days: int = 4) -> None:
    """Refuse to build on a parent that is not the edition we think it is.

    This is the guard for the cache bug. Pass expect_date/expect_edition from an
    authoritative source (the artifact listing), NOT from the fetched page itself —
    a stale page is perfectly self-consistent and will happily confirm its own date.
    """
    pdate, ped = parent.get("date"), parent.get("edition")
    if not pdate or ped is None:
        raise LensBuildError(f"parent ledger has no date/edition: {pdate!r}/{ped!r}")
    if expect_date is not None and pdate != expect_date:
        raise LensBuildError(
            f"STALE PARENT: fetched edition is dated {pdate}, expected {expect_date}. "
            "The fetch was probably served from cache — re-fetch before building.")
    if expect_edition is not None and ped != expect_edition:
        raise LensBuildError(
            f"STALE PARENT: fetched edition {ped}, expected {expect_edition}.")
    if today is not None:
        d0 = _dt.date.fromisoformat(pdate)
        d1 = _dt.date.fromisoformat(today)
        if d0 >= d1:
            raise LensBuildError(f"parent dated {pdate} is not before today {today}")
        if (d1 - d0).days > max_age_days:
            raise LensBuildError(
                f"parent is {(d1 - d0).days} days old ({pdate} vs {today}); "
                f"max_age_days={max_age_days}. An edition is probably missing.")


# ----------------------------------------------------------------- merge ---
def merge_parent(ledger: dict, parent: dict, superseded: dict | None = None,
                 sections: tuple | None = None, drop_events_before: str | None = None):
    """Carry parent rows that today's pass did not re-report.

    `superseded` maps {section: {parent_key: today_key}} for rows today deliberately
    re-keyed — those are dropped rather than duplicated. Everything else in the
    parent that is absent from today is carried forward verbatim.

    Returns (carried_count, dropped_past_events, carried_keys).
    """
    superseded = superseded or {}
    sections = sections or tuple(k for k, v in parent.items() if isinstance(v, list))
    carried, keys = 0, []
    for sec in sections:
        today_rows = ledger.setdefault(sec, [])
        have = {r["k"] for r in today_rows}
        sup = superseded.get(sec, {})
        for row in parent.get(sec, []):
            if row["k"] in have or row["k"] in sup:
                continue
            today_rows.append(dict(row))
            carried += 1
            keys.append(f"{sec}/{row['k']}")
    dropped = 0
    if drop_events_before and "events" in ledger:
        before = len(ledger["events"])
        ledger["events"] = [e for e in ledger["events"]
                            if e.get("date", "9999-99-99") >= drop_events_before]
        ledger["events"].sort(key=lambda e: e.get("date", "9999-99-99"))
        dropped = before - len(ledger["events"])
    return carried, dropped, keys


def assert_no_regression(new: dict, parent: dict,
                         sections: tuple = ACCUMULATING) -> None:
    """An append-only section may never come back smaller than its parent."""
    bad = []
    for sec in sections:
        n, p = len(new.get(sec, [])), len(parent.get(sec, []))
        if n < p:
            lost = {r["k"] for r in parent.get(sec, [])} - {r["k"] for r in new.get(sec, [])}
            bad.append(f"{sec}: {p} -> {n} (lost {', '.join(sorted(lost)) or '?'})")
    if bad:
        raise LensBuildError("APPEND-ONLY SECTION SHRANK:\n  " + "\n  ".join(bad))


# ---------------------------------------------------------------- splice ---
def splice_sections(html: str, sections: dict, chips: dict | None = None,
                    expect: int | None = None) -> str:
    """Replace each <section class="view..."> body by id.

    The class match is deliberately tolerant: an edition that marks the landing
    section class="view active" must still be spliced. A literal class="view"
    pattern skips it silently and the section keeps yesterday's text.
    """
    chips = chips or {}
    seen = []

    def sub(m):
        tag, sid, inner = m.group(1), m.group(2), m.group(3)
        seen.append(sid)
        if sid in chips:
            tag = re.sub(r'data-chips="[^"]*"', f'data-chips="{chips[sid]}"', tag)
        return tag + sections.get(sid, inner) + "</section>"

    out, n = _SECTION_RE.subn(sub, html)
    if expect is not None and n != expect:
        raise LensBuildError(f"spliced {n} sections, expected {expect}: saw {seen}")
    missing = set(sections) - set(seen)
    if missing:
        raise LensBuildError(f"sections never matched (typo or class drift?): {sorted(missing)}")
    return out


def refresh_nav(html: str, navmeta: dict, expect: int | None = None) -> str:
    """Rewrite the static left-rail `meta:` strings.

    This block is hand-written in the template and is NOT derived from the section
    chips, so it silently keeps the previous edition's counts — including the
    "vs edition NNN" label — unless a build rewrites it.
    """
    def sub(m):
        sid, meta = m.group(1), m.group(3)
        if sid not in navmeta:
            return m.group(0)
        return m.group(0).replace(f'meta:"{meta}"', f'meta:"{navmeta[sid]}"')

    out, n = _NAV_RE.subn(sub, html)
    if expect is not None and n != expect:
        raise LensBuildError(f"nav rewrite saw {n} entries, expected {expect}")
    stale = [sid for sid in navmeta if f'meta:"{navmeta[sid]}"' not in out]
    if stale:
        raise LensBuildError(f"nav entries did not take: {stale}")
    return out


def rewrite_identity(html: str, edition: str, dslug: str, gen: str) -> str:
    """Pattern-based title/masthead/const rewrite.

    Literal replacements keyed to the previous edition's date no-op silently the
    moment the parent changes, leaving yesterday's identity on today's page.
    """
    subs = [
        (r"<title>Oracle Competitive Lens — \d{4}-\d{2}-\d{2}</title>",
         f"<title>Oracle Competitive Lens — {dslug}</title>"),
        (r'<span class="sub">edition \d+ · generated [^<]*</span>',
         f'<span class="sub">edition {edition} · generated {gen}</span>'),
        (r'GEN\s*=\s*"[^"]*",\s*ED\s*=\s*"[^"]*",\s*DSLUG\s*=\s*"[^"]*"',
         f'GEN = "{gen}", ED="{edition}", DSLUG="{dslug}"'),
    ]
    for pat, rep in subs:
        html, n = re.subn(pat, rep, html)
        if n != 1:
            raise LensBuildError(f"identity rewrite matched {n} times for {pat!r}, expected 1")
    return html


# -------------------------------------------------------- link coverage ---
# Guard 5: VERIFIABILITY DRIFT. The lens's citation rule (every factual item
# carries a primary link, an "archive MM-DD" fallback, or an explicit unsourced
# marker) has no renderer to enforce it, so inheritance happily propagates
# linkless prose ("Seen in: <topic>") forever. This guard makes the rule fatal.
#
# Citation fallback order for any item:
#   1. primary URL mined from that day's briefs      -> <a>src</a> (or named label)
#   2. dated public-dashboard archive page where the  -> archive_link(first_seen)
#      item surfaced (ledger rows carry first_seen /
#      date / announced, so this is derivable)
#   3. genuinely no source in hand                    -> the literal UNSOURCED text
#
# New ledger rows should also persist the mined primary URL in a "url" field so
# tomorrow's carried rows keep their citation without re-mining.

ARCHIVE_BASE = "https://karlarao.github.io/daily-briefings/archive/"
UNSOURCED = "(unsourced — verify)"

# What counts as one citable factual unit in each view. A unit passes when it
# contains an <a href> or the UNSOURCED marker. "section" = one link anywhere
# in the view is enough (used where rows are pure aggregates of linked data).
LINK_POLICY = {
    "v-read":         "li",       # attention bullets; the lede prose is exempt
    "v-wn":           "li",
    "v-claims":       "card",
    "v-mirror":       "card",
    "v-questions":    "talk",
    "v-gaps":         "gap",
    "v-events":       "tr",
    "v-perf":         "li",
    "v-patch":        "tr",
    "v-bench":        "tr",
    "v-promises":     "tr",
    "v-longitudinal": "section",  # links the raw ledger dir; per-day rows are derived
    "v-build":        "card",
    "v-skills":       "card",
    "v-dossiers":     "tr",
}

_POV_RE = re.compile(r'(<script type="application/json" id="povContent">)(.*?)(</script>)', re.S)


def archive_link(date: str, base: str = ARCHIVE_BASE) -> str:
    """Fallback citation anchor: the dated dashboard archive, labeled 'archive MM-DD'."""
    _dt.date.fromisoformat(date)  # raises on a non-date (e.g. the literal "carried")
    return (f'<a href="{base}{date}.html" target="_blank" rel="noopener">'
            f'archive {date[5:]}</a>')


def _units(body: str, kind: str):
    """Yield (index, chunk) citation units of `kind` from a section/view body."""
    if kind == "section":
        yield 0, body
    elif kind == "card":
        # chunk from each card open to the next card (nesting-tolerant)
        starts = [m.start() for m in re.finditer(r'<div class="card">', body)]
        for i, s in enumerate(starts):
            yield i, body[s:starts[i + 1] if i + 1 < len(starts) else len(body)]
    elif kind == "gap":
        starts = [m.start() for m in re.finditer(r'<div class="gap">', body)]
        for i, s in enumerate(starts):
            yield i, body[s:starts[i + 1] if i + 1 < len(starts) else len(body)]
    elif kind == "tr":
        for i, m in enumerate(re.finditer(r"<tr>(.*?)</tr>", body, re.S)):
            if "<td" in m.group(1):          # skip header rows
                yield i, m.group(1)
    elif kind == "li":
        for i, m in enumerate(re.finditer(r"<li>(.*?)</li>", body, re.S)):
            yield i, m.group(1)
    elif kind == "talk":
        for i, m in enumerate(re.finditer(r'<p class="talk">(.*?)</p>', body, re.S)):
            yield i, m.group(1)
    else:
        raise LensBuildError(f"unknown link-policy kind {kind!r}")


def _bare_units(bodies: dict, policy: dict, label: str = ""):
    """Return (units_checked, [descriptions of units with no citation])."""
    bad, checked = [], 0
    for sid, body in bodies.items():
        kind = policy.get(sid)
        if kind is None:
            continue
        for i, chunk in _units(body, kind):
            checked += 1
            if "<a href=" in chunk or UNSOURCED in chunk:
                continue
            text = " ".join(re.sub(r"<[^>]+>", " ", chunk).split())[:70]
            bad.append(f"{label}{sid}[{kind} #{i}]: {text}")
    return checked, bad


def _raise_drift(bad: list) -> None:
    head = "\n  ".join(bad[:25])
    more = f"\n  ... and {len(bad) - 25} more" if len(bad) > 25 else ""
    raise LensBuildError(
        f"VERIFIABILITY DRIFT: {len(bad)} factual units carry no source link, "
        f"no archive fallback, and no {UNSOURCED!r} marker:\n  {head}{more}")


def assert_link_coverage(bodies: dict, policy: dict = LINK_POLICY,
                         label: str = "") -> int:
    """Every citation unit in every supplied view body must carry a citation.

    `bodies` maps view id -> body HTML. Returns the number of units checked.
    """
    checked, bad = _bare_units(bodies, policy, label)
    if bad:
        _raise_drift(bad)
    return checked


def assert_page_link_coverage(html: str, policy: dict = LINK_POLICY) -> int:
    """assert_link_coverage over the whole page — in-page sections plus every
    chair's flipped view bodies inside #povContent — reported as ONE error so a
    build sees the full damage, not just the first section. Returns units checked."""
    bodies = {sid: inner for _tag, sid, inner in _SECTION_RE.findall(html)}
    checked, bad = _bare_units(bodies, policy)
    m = _POV_RE.search(html)
    if m:
        pov = json.loads(m.group(2))
        for chair, views in pov.get("content", {}).items():
            chair_bodies = {sid: v.get("h", "") for sid, v in views.items()}
            c, b = _bare_units(chair_bodies, policy, label=f"{chair}/")
            checked += c
            bad += b
    if bad:
        _raise_drift(bad)
    return checked


# ------------------------------------------------------------- self-test ---
if __name__ == "__main__":
    page = (
        '<title>Oracle Competitive Lens — 2026-01-01</title>'
        '<span class="sub">edition 001 · generated 2026-01-01 09:00 EDT</span>'
        '<script type="application/json" id="lensLedger">'
        '{"date":"2026-01-01","edition":1,"promises":[{"k":"a"},{"k":"b"}],"patch":[],'
        '"benchmarks":[],"gaps":[]}</script>'
        '<section class="view active" id="v-read" data-chips="old">OLD READ</section>'
        '<section class="view" id="v-wn" data-chips="old">OLD WN</section>'
        '<script>var NAV=[{id:"v-read", name:"Read", meta:"stale"},'
        '{id:"v-wn", name:"Since yesterday", meta:"vs edition 000"}];'
        'GEN = "2026-01-01 09:00 EDT", ED="001", DSLUG="2026-01-01"</script>'
    )
    served = '<html><head><script>window.__FRAME_PREAMBLE={}</script></head><body>' + page + '</body></html></body></html>'

    src = strip_host_wrapper(served)
    assert "__FRAME_PREAMBLE" not in src and not src.rstrip().endswith("</html>")
    assert strip_host_wrapper(src) == src, "strip must be idempotent"

    par = load_ledger(src)
    assert_parent_fresh(par, expect_date="2026-01-01", expect_edition=1, today="2026-01-02")
    for bad in (dict(expect_date="2026-01-02"), dict(expect_edition=99)):
        try:
            assert_parent_fresh(par, today="2026-01-02", **bad)
        except LensBuildError:
            pass
        else:
            raise SystemExit(f"freshness guard failed to trip on {bad}")
    try:
        assert_parent_fresh(par, today="2026-01-30")
    except LensBuildError:
        pass
    else:
        raise SystemExit("age guard failed to trip")

    led = {"date": "2026-01-02", "edition": 2, "promises": [{"k": "b"}], "patch": [],
           "benchmarks": [], "gaps": [], "events": [{"k": "past", "date": "2026-01-01"},
                                                    {"k": "soon", "date": "2026-01-05"}]}
    carried, dropped, keys = merge_parent(led, par, drop_events_before="2026-01-02")
    assert carried == 1 and keys == ["promises/a"], (carried, keys)
    assert dropped == 1 and [e["k"] for e in led["events"]] == ["soon"]
    assert_no_regression(led, par)

    try:
        assert_no_regression({"promises": [], "patch": [], "benchmarks": [], "gaps": []}, par)
    except LensBuildError as e:
        assert "promises" in str(e)
    else:
        raise SystemExit("regression guard failed to trip")

    out = splice_sections(src, {"v-read": "NEW READ", "v-wn": "NEW WN"},
                          chips={"v-read": "fresh"}, expect=2)
    assert "NEW READ" in out and "OLD READ" not in out, "active-class section not spliced"
    assert 'data-chips="fresh"' in out
    try:
        splice_sections(src, {"v-nope": "x"}, expect=2)
    except LensBuildError as e:
        assert "v-nope" in str(e)
    else:
        raise SystemExit("missing-section guard failed to trip")

    out = refresh_nav(out, {"v-wn": "vs edition 001"}, expect=2)
    assert 'meta:"vs edition 001"' in out and "vs edition 000" not in out

    out = rewrite_identity(out, "002", "2026-01-02", "2026-01-02 09:00 EDT")
    assert "<title>Oracle Competitive Lens — 2026-01-02</title>" in out
    assert 'edition 002 · generated 2026-01-02 09:00 EDT' in out
    assert 'ED="002"' in out and "2026-01-01" not in out.split("lensLedger")[0]
    try:
        rewrite_identity(out, "003", "2026-01-03", "x")  # title already rewritten once
    except LensBuildError:
        raise SystemExit("identity rewrite should still match a well-formed page")

    # guard 5: verifiability drift
    good_card = ('<div class="card"><p class="card-basis">claim · '
                 '<a href="https://example.com/x">src</a></p></div>')
    marked_card = f'<div class="card"><p>claim {UNSOURCED}</p></div>'
    bare_card = '<div class="card"><p>claim with nothing</p></div>'
    n = assert_link_coverage({"v-claims": good_card + marked_card,
                              "v-events": "<tr><th>h</th></tr><tr><td>e · "
                                          + archive_link("2026-01-01") + "</td></tr>"})
    assert n == 3, n  # two cards + one data row; the header row is exempt
    try:
        assert_link_coverage({"v-claims": good_card + bare_card})
    except LensBuildError as e:
        assert "VERIFIABILITY DRIFT" in str(e) and "card #1" in str(e)
    else:
        raise SystemExit("link-coverage guard failed to trip")
    try:
        archive_link("carried")
    except ValueError:
        pass
    else:
        raise SystemExit("archive_link must reject non-dates")
    pov_page = (page.replace("OLD READ", '<ul class="sig"><li>bare bullet</li></ul>')
                + '<script type="application/json" id="povContent">'
                  '{"content":{"oracle":{"v-claims":{"h":"' + bare_card.replace('"', '\\"') + '"}}}}'
                  '</script>')
    try:
        assert_page_link_coverage(pov_page)
    except LensBuildError as e:
        assert "v-read[li #0]" in str(e) and "oracle/v-claims" in str(e)
    else:
        raise SystemExit("page-wide link-coverage guard failed to trip")

    print("lens_guard self-test OK — all 5 failure modes trip their guard")
