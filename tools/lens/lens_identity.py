#!/usr/bin/env python3
"""Identity-site rewrites the on-main lens_guard.rewrite_identity() does NOT cover.

History (why each exists):
  * runbar  -- 2026-09-18/09-11. The runbar carries label and value in SEPARATE
    spans (`<span class="lbl">Edition</span><span class="val">109</span>`), so a
    pattern like `Edition 109` never matches: the literal never appears
    contiguously. Patch the span VALUES by label, then read back and assert the
    parent's edition/date are gone. Several `Edition 0NN` strings elsewhere in the
    page are legitimate historical prose ("CORRECTION (ed. 064)") and must NOT be
    rewritten -- a blanket substitution would corrupt the correction record.
  * povContent meta -- 2026-09-20. The real shape is FLAT,
    {chair: {viewid: "<navmeta string>"}}, not {viewid: {"meta": ...}}. A guard
    written against the plausible nested shape matched nothing, raised nothing,
    and let two stale editions ship. Drive every value from ONE dict and RAISE if
    nothing changed -- a guard that can match zero things and still pass is not a
    guard.
  * closing tags -- 2026-09-20. strip_host_wrapper() removes trailing
    </body></html> pairs unconditionally, so stored source (which already has
    exactly one) comes out with zero; a builder that appends directly to stored
    source instead gets two, and the next edition inherits them. Browsers ignore
    the second, so it is invisible until someone counts. Collapse-then-assert is
    safe on any input and idempotent.
"""
import re


# 2026-11-02: `rewrite_pov_meta` and `normalize_closing_tags` were written here
# on 2026-11-01 against `origin/main`, which does not carry `lens_extra.py` -- so
# the tree ended up with TWO implementations of each, and the one a future run
# imported would have been whichever module it happened to find. They now
# DELEGATE to `lens_extra`, which is the maturer module (its `rewrite_pov_meta`
# has since absorbed this file's unknown-viewid rejection, so nothing is lost).
# `rebuild_runbar` and `assert_no_stale_identity` below are unique to this file.
from lens_extra import (                                      # noqa: F401
    normalize_closing_tags,
    rewrite_pov_meta as _rewrite_pov_meta_impl,
)


def rewrite_pov_meta(html: str, nav_meta: dict, chairs=None) -> str:
    """Delegate to lens_extra.rewrite_pov_meta (one implementation, not two).

    `chairs` was never used by any caller; it is rejected rather than silently
    ignored, because a parameter that does nothing is worse than none.
    """
    if chairs is not None:
        raise NotImplementedError(
            "chairs= is not supported; lens_extra.rewrite_pov_meta drives every "
            "chair from one nav_meta dict, which is the invariant this guard exists "
            "to enforce")
    return _rewrite_pov_meta_impl(html, nav_meta)


def rebuild_runbar(html: str, *, edition: str, gen: str, model: str,
                   inputs: str, tokens: str, skills_review: str,
                   flag: str, parent_edition: str, parent_dslug: str) -> str:
    """Rebuild the whole <div class="runbar"> and read it back."""
    m = re.search(r'<div class="runbar">.*?</div>', html, re.S)
    assert m, "runbar not found"
    def sp(lbl, val):
        return '<span class="lbl">%s</span><span class="val">%s</span>' % (lbl, val)
    bar = ('<div class="runbar">'
           + sp("Edition", edition) + sp("Generated", gen) + sp("Model", model)
           + sp("Inputs", inputs) + sp("Run tokens", tokens)
           + sp("Skills review", skills_review)
           + '<span class="flag">' + flag + '</span></div>')
    out = html[:m.start()] + bar + html[m.end():]
    back = re.search(r'<div class="runbar">.*?</div>', out, re.S).group(0)
    assert edition in back and gen in back, "runbar rewrite did not take"
    # Check the parent EDITION only where an edition value can appear -- the
    # labelled spans -- not anywhere in the runbar string. 2026-11-02: a bare
    # `parent_edition not in back` failed a CORRECT runbar because the flag line
    # named GitLab CVE-2026-110264, which contains "110". A guard that fails on
    # correct content is the thing that trains people to bypass guards
    # (2026-09-16), and an edition number is 2-4 digits, so bare substring
    # matching against free prose is guaranteed to collide eventually.
    vals = re.findall(r'<span class="val">([^<]*)</span>', back)
    for bad, what in ((parent_edition, "edition"), (parent_dslug, "date")):
        hit = [v for v in vals if v.strip() == bad]
        assert not hit, "parent %s %s still in a runbar value span" % (what, bad)
    assert parent_dslug not in back, "parent date %s still in runbar" % parent_dslug
    return out


def assert_no_stale_identity(html: str, parent_edition: str, parent_dslug: str,
                             allow_prose: bool = True) -> None:
    """Fail if the parent's edition/date survive anywhere they are not prose.

    Legitimate survivors: historical correction prose ("ed. 064"), the ledger's
    own first_seen/last_seen dates, and archive-fallback citation anchors. So we
    only police the identity SITES: title, masthead, JS constants, runbar, NAV,
    povContent meta and the section-shell data-chips.
    """
    sites = []
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    sites.append(("title", t.group(1) if t else ""))
    rb = re.search(r'<div class="runbar">.*?</div>', html, re.S)
    # The runbar's own FLAG line is free prose naming CVEs, and a 2-4 digit
    # edition number collides with it (2026-11-02: "GitLab CVE-2026-110264"
    # contains "110"). Police the labelled VALUE spans, which is where an
    # identity assertion can actually live, not the whole div.
    sites.append(("runbar", " | ".join(
        re.findall(r'<span class="val">([^<]*)</span>', rb.group(0))) if rb else ""))
    nv = re.search(r"var NAV\s*=.*?;", html, re.S)
    sites.append(("NAV", nv.group(0) if nv else ""))
    pm = re.search(r'id="povContent">(.*?)</script>', html, re.S)
    if pm:
        import json
        sites.append(("povmeta", json.dumps(json.loads(pm.group(1)).get("meta", {}))))
    # The Since-yesterday chip legitimately NAMES the parent edition ("vs edition
    # 109") -- that is its entire job. A blanket parent-edition check fails on
    # correct content, and a guard that fails on correct content trains you to
    # bypass guards (2026-09-16). So strip the known-legitimate references first
    # and police what is left.
    LEGIT = (
        re.compile(r"vs\s+edition\s+0?" + re.escape(parent_edition)),
        re.compile(r"carried\s+from\s+0?" + re.escape(parent_edition)),
        re.compile(r"\(ed\.\s*0?" + re.escape(parent_edition) + r"\)"),
    )
    for name, blob in sites:
        for pat in LEGIT:
            blob = pat.sub("", blob)
        for bad in (parent_edition, parent_dslug):
            assert bad not in blob, (
                "stale %r survives in %s (and it is not a legitimate "
                "'vs edition'/'carried from' reference)" % (bad, name))
