#!/usr/bin/env python3
"""Guards for the Oracle Competitive Lens daily build.

The lens is not rebuilt from scratch each day. It is produced by fetching the
previous edition's published page and splicing today's sections into it, which
means every run inherits the previous run's state — including its mistakes.

Four failure modes have actually occurred. Each one is silent: the page renders,
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

    print("lens_guard self-test OK — all 4 failure modes trip their guard")
