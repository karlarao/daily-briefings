# -*- coding: utf-8 -*-
"""Edition 080 lens assembly. Applies all five documented build guards plus the
structural ones added since, and rewrites all SEVEN identity sites."""
import os as _os
# Resolve sibling modules relative to THIS file so a future run can import these
# from tools/lens/ instead of from one session's dead scratchpad. The original
# build ran with absolute scratchpad paths; that is what made edition 079's
# sections_079.py unusable as anything but a transcript.
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_SP = _os.environ.get("LENS_SCRATCH", _HERE)
import sys, json, re, hashlib
SP = _SP
sys.path.insert(0, SP + "/tools/lens"); sys.path.insert(0, SP + "/lens")
import lens_guard as G
import sections_080_skills as SK, sections_080_build as BD
import sections_080_shared as SH, sections_080_read as RD, sections_080_long as LG

ED, DSLUG, GEN = "080", "2026-10-01", "2026-10-01 09:47 EDT"
PARENT_ED = "079"
html = open(SP + "/lens/index.html", encoding="utf-8").read()
L = json.load(open(SP + "/lens/ledger_wip.json"))
L["date"], L["edition"] = DSLUG, int(ED)
parent = G.load_ledger(html)

# ---- GUARD 1: parent freshness. Confirmed against Artifact action:"list"
#      metadata earlier in this run ("Oracle Competitive Lens — 2026-09-30").
G.assert_parent_fresh(parent, expect_date=None)
assert parent["date"] == "2026-09-30" and int(parent["edition"]) == int(PARENT_ED), (parent["date"], parent["edition"])
print("guard 1  parent freshness .......... OK (edition %s, %s; not on/after today)" % (PARENT_ED, parent["date"]))

# ---- GUARD 4: host wrapper. A page staged via action:"read" with path is already
#      stored source, so strip_host_wrapper would remove its single closing pair.
#      normalize_closing_tags (called last) is the collapse-then-assert fix.
n_close_before = html.count("</body></html>")
assert n_close_before == 1, n_close_before
print("guard 4  host wrapper .............. OK (stored source, 1 closing pair in)")

# ---- shared + chair-flipped section bodies
long_h = LG.build_longitudinal()[0]
wn_h   = LG.build_wn(parent, L)
shared = {"v-events": SH.EVENTS_H, "v-patch": SH.PATCH_H,
          "v-longitudinal": long_h, "v-wn": wn_h}
pov = {
 "oracle":     {"v-read": RD.ORACLE_READ,     "v-skills": SK.ORACLE_SKILLS,     "v-build": BD.ORACLE_BUILD},
 "snowflake":  {"v-read": RD.SNOWFLAKE_READ,  "v-skills": SK.SNOWFLAKE_SKILLS,  "v-build": BD.SNOWFLAKE_BUILD},
 "databricks": {"v-read": RD.DATABRICKS_READ, "v-skills": SK.DATABRICKS_SKILLS, "v-build": BD.DATABRICKS_BUILD},
 "bigquery":   {"v-read": RD.BIGQUERY_READ,   "v-skills": SK.BIGQUERY_SKILLS,   "v-build": BD.BIGQUERY_BUILD},
}
CHIPS = {
 "v-events": "%d rows · -14d..+60d window" % SH.EV_N,
 "v-patch":  "%d of %d rows · 22 no-fix" % (SH.PA_N, len(L["patch"])),
 "v-longitudinal": "85 ledgers · 11 urgent lanes",
 "v-wn": "vs 079 · quarterly re-rank",
 "v-read": "11 of 19 lanes urgent",
 "v-skills": "7 bets · RE-RANKED 10-01 · next 2027-01-01",
 "v-build": "6 bets · re-ranked 10-01 · 1 sharpened",
 "v-claims": "%d tracked · carried from 079" % len(L["claims"]),
 "v-mirror": "%d own claims · carried from 079" % len(L["ownclaims"]),
 "v-gaps": "%d open · carried from 079" % len(L["gaps"]),
 "v-bench": "%d audited rows · carried from 079" % len(L["benchmarks"]),
 "v-promises": "%d rows · carried from 079" % len(L["promises"]),
}

# ---- GUARD 3: splice by SECTION ID with a count assert. expect= is the page's
#      TOTAL section count (visited), not the number replaced -- the 09-12 rule.
#      The flipped shells are seeded with the ORACLE body so FIRST PAINT is not
#      blank (the 09-09 finding).
to_splice = dict(shared)
for vid, body in pov["oracle"].items():
    to_splice[vid] = body
html = G.splice_sections(html, to_splice, chips=CHIPS, expect=15)
print("guard 3  splice by id .............. OK (%d sections replaced, 15 visited)" % len(to_splice))

# ---- povContent: all four chairs, bodies + chips
m = re.search(r'(<script type="application/json" id="povContent">)(.*?)(</script>)', html, re.S)
P = json.loads(m.group(2))
for chair, views in pov.items():
    for vid, body in views.items():
        P["content"][chair][vid]["h"] = body
        P["content"][chair][vid]["c"] = CHIPS[vid]
        P["meta"][chair][vid] = CHIPS[vid]
    for vid in P["meta"][chair]:
        if vid in CHIPS: P["meta"][chair][vid] = CHIPS[vid]
    for vid in P["content"][chair]:
        if vid in CHIPS: P["content"][chair][vid]["c"] = CHIPS[vid]
blob = json.dumps(P, ensure_ascii=False).replace("</", "<\\/")
html = html[:m.start(2)] + blob + html[m.end(2):]
print("identity 6/7  povContent meta + .c .. OK (4 chairs x %d views)" % len(P["meta"]["oracle"]))

# ---- identity 1-3: title, masthead, GEN/ED/DSLUG
html = G.rewrite_identity(html, ED, DSLUG, GEN)
print("identity 1-3  title/masthead/consts  OK")

# ---- identity 4: the runbar. MEASURED THIS RUN, correcting the 09-18 note:
#      rewrite_identity on the main-track (union) lens_guard DOES now rewrite the
#      runbar's Edition and Generated spans -- the 09-18 note said it provably
#      changed nothing there, and that is stale for this version of the tool.
#      What it still does NOT touch is the three run-specific fields below, and
#      "Skills review" is the one that matters today because the re-rank moves it.
#      Each is rewritten by its own anchored substitution with a count check, and
#      all six spans are then read back. Historical prose like "(ed. 071)" must
#      NOT be touched -- a blanket substitution would corrupt the correction record.
assert 'class="val">080<' in html, "rewrite_identity should have set the runbar edition"
for lbl, want in (("Inputs", "19 briefs &middot; 85d ledger"),
                  ("Run tokens", "~3750k"),
                  ("Skills review", "2027-01-01")):
    pat = r'(<span class="lbl">%s</span><span class="val">)([^<]*)(</span>)' % re.escape(lbl)
    html, n = re.subn(pat, lambda m, w=want: m.group(1) + w + m.group(3), html, count=1)
    assert n == 1, "runbar field %r did not take (n=%d)" % (lbl, n)
rb_now = dict(re.findall(r'<span class="lbl">([^<]*)</span><span class="val">([^<]*)</span>', html)[:6])
assert rb_now.get("Edition") == ED, rb_now
assert rb_now.get("Generated") == GEN, rb_now
assert rb_now.get("Skills review") == "2027-01-01", rb_now
assert "84d ledger" not in html and "~3945k" not in html, "a stale runbar value survived"
print("identity 4  runbar: 2 fields by rewrite_identity + 3 rewritten here, all 6 read back OK")
print("            (corrects the 09-18 note: rewrite_identity DOES cover Edition/Generated now)")

# ---- identity 5: var NAV (refresh_nav asserts each entry took)
html = G.refresh_nav(html, CHIPS)
print("identity 5  var NAV ................ OK")

# ---- identity 7: section-shell data-chips is what FIRST PAINT reads; splice
#      already set it for the ids in CHIPS, assert it stuck for the flipped ones.
for vid in ("v-read", "v-skills", "v-build", "v-wn"):
    assert re.search(r'id="%s"[^>]*data-chips="[^"]*"' % vid, html), vid
print("identity 7  section-shell data-chips  OK")

# ---- embed the ledger, then the structural guards
html = G.write_ledger(html, L)
G.assert_not_parent_identity(html, PARENT_ED)
n_sec = G.assert_structure(html)
n_tab = G.assert_table_shape(html)
html = G.normalize_closing_tags(html)
assert html.count("</body></html>") == 1, html.count("</body></html>")
n_cited = G.assert_page_link_coverage(html)
G.assert_identity_consistent(html, ED, DSLUG, GEN)
print("guard 2/alias  (done pre-build via assert_alias_safe on 7 sections)")
print("guard 5  link coverage ............. OK (%d cited units, 0 uncited)" % n_cited)
print("assert_structure ................... OK (%d sections opened==closed)" % n_sec)
print("assert_table_shape ................. OK (%d tables)" % n_tab)
print("normalize_closing_tags ............. OK (1 pair)")
print("assert_identity_consistent ......... OK")
open(SP + "/lens/out_080.html", "w", encoding="utf-8").write(html)
par = len(open(SP + "/lens/index.html", encoding="utf-8").read())
print("\nwrote out_080.html  %d bytes  (parent %d, delta %+d)" % (len(html), par, len(html)-par))
