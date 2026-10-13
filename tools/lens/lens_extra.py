#!/usr/bin/env python3
"""Lens build guards that were written in past runs but never landed on main.

Every function here was developed in a session whose branch was not merged, so
each has been RE-DERIVED from scratch at least once (see CLAUDE.md: the
"STILL not on main" notes of 09-10 .. 09-16, and the 10-04 rule that a run must
IMPORT and CALL what yesterday's note claims exists).  They live beside
lens_guard.py so a build gets them for free.

House rule inherited from the 2026-10-05 finding: a guard that cannot fail is
worse than no guard, and a helper that raises must never fall through to a
default that looks like a result.  Everything here raises LensBuildError; none
of it returns a reassuring empty set on error.
"""
from __future__ import annotations
import json, re
from lens_guard import LensBuildError


# ---------------------------------------------------------------------------
# 1. povContent["meta"] — the SEVENTH identity site.
#    Shape is FLAT: {chair: {viewid: "<string>"}}.  A guard written against the
#    plausible nested shape {viewid: {"meta": ...}} matched nothing, raised
#    nothing, and let edition 068 ship "edition 067" left-rail labels on every
#    chair (2026-09-20 finding).  Hence the "changed nothing -> raise".
# ---------------------------------------------------------------------------
_POV_RE = re.compile(
    r'(<script type="application/json" id="povContent">)(.*?)(</script>)', re.S)


def rewrite_pov_meta(html: str, navmeta: dict, *, require: int = 1) -> str:
    """Drive every povContent meta string from one navmeta dict.

    navmeta maps viewid -> the meta text every chair should show.  Raises if the
    block is missing, unparseable, flat-shape-violating, or if NOTHING changed.
    """
    m = _POV_RE.search(html)
    if not m:
        raise LensBuildError("povContent block not found")
    try:
        blob = json.loads(m.group(2))
    except Exception as exc:
        raise LensBuildError(f"povContent is not valid JSON: {exc!r}") from exc
    meta = blob.get("meta")
    if not isinstance(meta, dict) or not meta:
        raise LensBuildError("povContent['meta'] missing or not a dict")

    changed, seen = 0, 0
    for chair, views in meta.items():
        if not isinstance(views, dict):
            raise LensBuildError(
                f"povContent['meta'][{chair!r}] is {type(views).__name__}, "
                "expected dict — the FLAT {chair:{viewid:str}} shape")
        for vid, cur in list(views.items()):
            if not isinstance(cur, str):
                raise LensBuildError(
                    f"povContent['meta'][{chair!r}][{vid!r}] is "
                    f"{type(cur).__name__}, expected str")
            seen += 1
            if vid in navmeta and cur != navmeta[vid]:
                views[vid] = navmeta[vid]
                changed += 1
    if seen == 0:
        raise LensBuildError("povContent['meta'] held no viewid entries")
    if changed < require:
        raise LensBuildError(
            f"rewrite_pov_meta changed {changed} of {seen} entries "
            f"(required >= {require}) — a check that matches nothing is not a check")
    out = m.group(1) + json.dumps(blob, ensure_ascii=False) + m.group(3)
    return html[:m.start()] + out + html[m.end():]


# ---------------------------------------------------------------------------
# 2. Closing tags.  strip_host_wrapper() removes trailing </body></html> pairs
#    unconditionally, so a page staged from STORED source comes out with zero;
#    a builder that appends directly to stored source gets two (2026-09-19 and
#    2026-09-20 findings — the published 069 parent carried two).  Browsers
#    ignore the extra, so it is invisible until someone counts.
# ---------------------------------------------------------------------------
def normalize_closing_tags(html: str) -> str:
    """Collapse to exactly one trailing </body></html>, then assert it. Idempotent."""
    out = re.sub(r"(?:\s*</body>\s*</html>\s*)+$", "\n", html).rstrip() + "\n</body></html>\n"
    nb, nh = out.count("</body>"), out.count("</html>")
    if (nb, nh) != (1, 1):
        raise LensBuildError(
            f"after normalize: {nb} </body> and {nh} </html>, expected 1 and 1")
    return out


# ---------------------------------------------------------------------------
# 3. No parent identity string anywhere in the output.
#    rewrite_identity() + assert_identity_consistent() cover the sites they know.
#    This is the catch-all for the ones nobody listed yet.  It must NOT fire on
#    legitimate historical prose — "CORRECTION (ed. 064)", "carried from 083",
#    "vs edition 083" are backward references and are correct (2026-09-18 and
#    2026-10-04 findings).  Positive controls below use STRINGS, not ints: the
#    10-05 run passed int 83 and got a TypeError out of re.escape on all three
#    "ok raise" lines, i.e. three false passes (a control that raises for the
#    wrong reason reports the guard healthy while testing nothing).
# ---------------------------------------------------------------------------
# "against" and "compared with" join the vocabulary 2026-10-06: the Since-
# yesterday lede legitimately reads "This edition against edition 084", which
# is a backward reference, not a claim to be 084.
_BACKREF = re.compile(
    r"(?:carried (?:forward )?from|vs\.?|versus|against|compared (?:with|to)|"
    r"relative to|since|ed\.|edition)\s*$", re.I)


_LEDGER_BLOCK = re.compile(
    r'<script type="application/json" id="lensLedger">.*?</script>', re.S)


def assert_not_parent_identity(html: str, parent_ed: str, parent_date: str,
                               *, strip_ledger: bool = True,
                               check_date: bool = False) -> None:
    """Refuse a page that still asserts the PARENT's edition or date as its own.

    The embedded ledger is excluded by default: it is a data island holding many
    dated rows, including retired ones that legitimately carry the parent's date.
    A date inside it is data, not an identity assertion -- and leaving it in made
    the guard fire on its own `retired_events` list.

    `check_date` is OFF by default, and that is a deliberate scoping decision
    rather than a weakening (2026-10-06). A lens edition REPORTS dates for a
    living: the Longitudinal table has a row for the parent's date, and a
    correction legitimately says "published 2026-10-05". A blanket scan for the
    parent date therefore collides with correct content every time, and a guard
    that cries wolf is a guard people start bypassing. The parent DATE's genuine
    identity positions -- title, masthead sub, GEN, DSLUG, runbar generated --
    are each driven from one source and read back by
    `lens_guard.assert_identity_consistent`, which compares the rendered value
    against the intended one instead of hunting for a string. What is left here
    is the parent EDITION, which has no legitimate non-identity use outside a
    backward reference, and those are whitelisted above.
    """
    if strip_ledger:
        html = _LEDGER_BLOCK.sub("", html)
    if not isinstance(parent_ed, str) or not isinstance(parent_date, str):
        raise LensBuildError(
            "parent_ed and parent_date must be STRINGS (e.g. '084', not 84) — "
            "an int silently makes this guard a TypeError instead of a check")
    hits = []
    for pat in (rf"[Ee]dition\s+{re.escape(parent_ed)}\b",
                rf"\bED\s*=\s*\"{re.escape(parent_ed)}\"",
                # The runbar puts the label and the value in SEPARATE spans, so
                # "Edition 084" never appears contiguously and the pattern above
                # cannot see it -- the structural blind spot the 2026-09-18 note
                # describes. A positive control for the bare value caught this
                # guard missing it on 2026-10-06.
                rf"<span class=\"val\">{re.escape(parent_ed)}</span>",
                ) + ((re.escape(parent_date),) if check_date else ()):
        for m in re.finditer(pat, html):
            lead = html[max(0, m.start() - 48):m.start()]
            if _BACKREF.search(lead.rstrip()):
                continue                      # legitimate backward reference
            hits.append((m.group(0), lead[-40:].replace("\n", " ")))
    if hits:
        raise LensBuildError(
            f"{len(hits)} unqualified parent-identity assertion(s) survive: {hits[:5]}")


def _selftest_assert_not_parent_identity() -> str:
    """Positive AND negative controls, with strings. Returns 'N/N'."""
    ok = tot = 0
    must_raise = [
        '<span class="val">083</span> Edition 083 here',
        'GEN="x", ED="083", DSLUG="2026-10-04"',
        '<span class="lbl">Edition</span><span class="val">083</span>',
    ]
    # the parent DATE is only an identity assertion under check_date; both the
    # raising and the non-raising side are tested so the scoping cannot rot.
    date_cases = [
        ('<title>Oracle Competitive Lens — 2026-10-04</title>', True, True),
        ('<title>Oracle Competitive Lens — 2026-10-04</title>', False, False),
        ('<td><code>2026-10-04</code></td> published 2026-10-04', True, True),
        ('<td><code>2026-10-04</code></td> published 2026-10-04', False, False),
    ]
    must_pass = [
        'carried from 083', 'carried forward from 083', 'vs edition 083',
        'vs. edition 083', 'CORRECTION (ed. 083)', 'unchanged since 2026-10-04',
        'Edition 085 · Generated 2026-10-06', 'versus edition 083',
    ]
    for s in must_raise:
        tot += 1
        try:
            assert_not_parent_identity(s, "083", "2026-10-04")
        except LensBuildError:
            ok += 1
    for s in must_pass:
        tot += 1
        try:
            assert_not_parent_identity(s, "083", "2026-10-04"); ok += 1
        except LensBuildError:
            pass
    for s, flag, want in date_cases:
        tot += 1
        try:
            assert_not_parent_identity(s, "083", "2026-10-04", check_date=flag)
            got = False
        except LensBuildError:
            got = True
        if got == want:
            ok += 1
    tot += 1                                   # the int-vs-str guard itself
    try:
        assert_not_parent_identity("x", 83, "2026-10-04")   # type: ignore[arg-type]
    except LensBuildError:
        ok += 1
    return f"{ok}/{tot}"


# ---------------------------------------------------------------------------
# 4. Structure: every NAV id has a <section>, every <section> has a NAV entry,
#    and no section carries its own inline panel-head (which renders
#    "undefined" in the global head plus a duplicate below).
# ---------------------------------------------------------------------------
def assert_structure(html: str, expect_sections: int | None = None) -> int:
    sec_ids = re.findall(r'<section class="view[^"]*"\s+id="([^"]+)"', html)
    if not sec_ids:
        sec_ids = re.findall(r'<section[^>]*\bid="(v-[^"]+)"', html)
    nav_ids = re.findall(r'\bid:\s*"(v-[^"]+)"', html)
    if not sec_ids:
        raise LensBuildError("no <section> ids found — selector drift")
    if not nav_ids:
        raise LensBuildError("no NAV ids found — selector drift")
    missing = [i for i in nav_ids if i not in sec_ids]
    orphan = [i for i in sec_ids if i not in nav_ids]
    if missing:
        raise LensBuildError(f"NAV ids with no section (renders empty panel): {missing}")
    if orphan:
        raise LensBuildError(f"sections with no NAV entry (unreachable): {orphan}")
    inline = re.findall(r'<section[^>]*\bid="(v-[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)?'
                        r'<div class="panel-head"', html)
    if inline:
        raise LensBuildError(f"sections carrying an inline panel-head: {inline}")
    for sid in sec_ids:
        m = re.search(r'<section[^>]*\bid="%s"([^>]*)>' % re.escape(sid), html)
        attrs = m.group(1) if m else ""
        for need in ("data-title", "data-eyebrow", "data-chips"):
            if need not in attrs:
                raise LensBuildError(f"section {sid} missing {need}")
    if expect_sections is not None and len(sec_ids) != expect_sections:
        raise LensBuildError(
            f"{len(sec_ids)} sections, expected {expect_sections}")
    return len(sec_ids)


# ---------------------------------------------------------------------------
# 5. Day-count drift detector.  A row's stated day count lives in BOTH its
#    `due`/date prose and its `t` prose; a repair that edits one leaves the
#    other.  The 10-05 run found 9 stale counts its own hand pass missed, and
#    the fix that worked was to drive the repair FROM THIS DETECTOR'S OUTPUT
#    rather than from a hand list — the detector already knows row, field,
#    stated and actual.  Returns a list of dicts; it does NOT repair.
# ---------------------------------------------------------------------------
_DAYS_RE = re.compile(r"(\d{1,4})\s*(?:d\b|days?\b)", re.I)


def daycounts_rows(rows: list, today: str, *, datefield: str = "date",
                   exempt: set | None = None) -> list:
    """Find rows whose stated 'N days' disagrees with |today - row date|."""
    from datetime import date as _d
    exempt = exempt or set()
    y, mo, dd = (int(x) for x in today.split("-"))
    t0 = _d(y, mo, dd)
    out = []
    for r in rows:
        if not isinstance(r, dict) or r.get("k") in exempt:
            continue
        ds = r.get(datefield) or r.get("due") or r.get("announced") or ""
        m = re.search(r"\d{4}-\d{2}-\d{2}", str(ds))
        if not m:
            continue
        ry, rm, rd = (int(x) for x in m.group(0).split("-"))
        actual = abs((t0 - _d(ry, rm, rd)).days)
        for field in ("due", "t", "v", "date"):
            val = r.get(field)
            if not isinstance(val, str):
                continue
            for dm in _DAYS_RE.finditer(val):
                stated = int(dm.group(1))
                if stated != actual and stated < 2000:   # 2026 is a year, not a count
                    out.append({"k": r.get("k"), "field": field,
                                "stated": stated, "actual": actual,
                                "date": m.group(0), "text": val[:90]})
    return out


if __name__ == "__main__":
    print("assert_not_parent_identity self-test:",
          _selftest_assert_not_parent_identity())


# ---------------------------------------------------------------------------
# 6. Identifier probe — the companion `reuse_key` needs and does not have.
#    Measured 2026-10-06: reuse_key's similarity route returned "no peer" for
#    FIVE of eight drafted patch rows that were already on the board
#    (nextjs-og-imageresponse-rce-94545, apple-coregraphics-86950-exploited,
#    fastify-4x-authbypass-no-fix, pgbouncer-scram-nonce-preauth-crash-19888,
#    and a vLLM sibling).  The date route has the mirror defect: it cannot see
#    a same-story row filed under a different date, which is how the 10-12
#    macos-14 brownout nearly got a fresh slug beside the 10-05 and 11-02 rows
#    for the same migration.
#
#    So: never trust a bare "no peer".  Probe by HARD identifier (CVE/GHSA id)
#    and by product noun across the whole section, ignoring dates, first.
# ---------------------------------------------------------------------------
# Bounded on purpose. An unbounded r"(?:CVE|GHSA)[-\w]+" also matches the bare
# word "CVEs", so every parent row mentioning "28 CVEs" collides with every
# other one — 26 false hits on first use, 2026-10-06. The 2026-10-05 note
# warned about exactly this ("bound it to CVE-\\d{4}-\\d+") and it was
# reintroduced anyway; the guard raising is what surfaced it.
_ID_RE = re.compile(r"(?:CVE-\d{4}-\d{4,}|GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4})", re.I)


def probe_identifiers(new_row: dict, parent_rows: list, *, nouns: list | None = None) -> list:
    """Return parent rows sharing a hard id (or a given product noun) with new_row.

    Date-agnostic and similarity-agnostic on purpose: this is the check that
    catches what the other two routes structurally cannot.
    """
    blob = " ".join(str(new_row.get(f, "")) for f in ("k", "t", "due", "date"))
    ids = {i.upper() for i in _ID_RE.findall(blob)}
    nouns = [n.lower() for n in (nouns or [])]
    hits = []
    for r in parent_rows:
        pb = " ".join(str(r.get(f, "")) for f in ("k", "t", "due", "date"))
        pids = {i.upper() for i in _ID_RE.findall(pb)}
        if (ids & pids) or any(n in pb.lower() for n in nouns):
            hits.append(r)
    return hits


def assert_probed(new_rows: list, parent_rows: list, noun_map: dict) -> dict:
    """Probe every drafted row and REFUSE a silent empty result.

    noun_map maps a drafted row's key -> the product nouns to probe for.  A key
    missing from noun_map raises: deciding 'this row needs no probe' has to be
    explicit, because the whole failure mode here is a check that quietly
    matched nothing and was read as 'genuinely new'.
    """
    missing = [r["k"] for r in new_rows if r["k"] not in noun_map]
    if missing:
        raise LensBuildError(
            "no probe nouns declared for: %s — an undeclared row is an "
            "unprobed row" % missing)
    return {r["k"]: [h["k"] for h in probe_identifiers(r, parent_rows,
                                                       nouns=noun_map[r["k"]])]
            for r in new_rows}
