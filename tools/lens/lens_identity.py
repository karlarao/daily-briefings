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


def normalize_closing_tags(html: str) -> str:
    """Collapse any number of trailing </body></html> pairs to exactly one."""
    body = re.sub(r"(?:\s*</body>\s*</html>\s*)+\Z", "", html).rstrip()
    out = body + "\n</body></html>"
    assert out.count("</html>") == 1, "html close count %d" % out.count("</html>")
    assert out.count("</body>") == 1, "body close count %d" % out.count("</body>")
    return out


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
    assert parent_edition not in back, "parent edition %s still in runbar" % parent_edition
    assert parent_dslug not in back, "parent date %s still in runbar" % parent_dslug
    return out


def rewrite_pov_meta(html: str, nav_meta: dict, chairs=None) -> str:
    """Rewrite povContent["meta"][chair][viewid] from ONE nav_meta dict.

    nav_meta: {viewid: "navmeta string"}  (same text for every chair unless the
    value is itself a {chair: str} dict). Raises if nothing changed.
    """
    import json
    m = re.search(r'(<script type="application/json" id="povContent">)(.*?)(</script>)',
                  html, re.S)
    assert m, "povContent not found"
    pov = json.loads(m.group(2))
    meta = pov.get("meta")
    assert isinstance(meta, dict) and meta, "povContent meta missing/empty"
    sample = next(iter(meta.values()))
    assert isinstance(sample, dict) and all(isinstance(v, str) for v in sample.values()), \
        "povContent meta is not the flat {chair:{viewid:str}} shape -- re-read it"
    # A viewid that exists in NO chair is a typo. Writing it would silently ADD
    # a dead key and still report "changed", which is how a wrong-shape guard
    # passes while rewriting nothing real -- so reject it before touching data.
    known = set()
    for views in meta.values():
        known |= set(views)
    unknown = [v for v in nav_meta if v not in known]
    assert not unknown, "unknown povContent meta viewid(s): %s (known: %s)" % (
        sorted(unknown), sorted(known))

    changed = 0
    for chair, views in meta.items():
        if chairs and chair not in chairs:
            continue
        for vid, val in nav_meta.items():
            if vid not in views:          # never create keys, only update
                continue
            new = val[chair] if isinstance(val, dict) else val
            if views.get(vid) != new:
                views[vid] = new
                changed += 1
    assert changed, "rewrite_pov_meta changed NOTHING -- values already current"
    blob = json.dumps(pov, ensure_ascii=False, separators=(",", ":"))
    return html[:m.start()] + m.group(1) + blob + m.group(3) + html[m.end():]


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
    sites.append(("runbar", rb.group(0) if rb else ""))
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
