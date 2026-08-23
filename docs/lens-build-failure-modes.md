# Lens build — failure modes and guards

Record of five silent failure modes found while rebuilding the Oracle Competitive
Lens, and the guards added to catch them. The first four were found in a single
build on 2026-08-10; the fifth on 2026-08-20, after weeks of accumulation. None of
them would have raised an error, and none are visible on the rendered page — that
is what makes them worth writing down.

## Why this class of bug exists

The public dashboard (`claude.html`) is **rebuilt from scratch** every morning from
19 stateless research briefs. If a run goes wrong, the output is obviously wrong.

The lens is different. It is **built by inheritance**: fetch the previous edition's
published page, splice today's sections into it, and republish. It works that way
because the lens carries running state the briefs cannot regenerate — an append-only
Benchmark Scoreboard, an accumulating Promise Tracker, standing attack lines, gaps
that have been open since edition 001.

That inheritance is the whole point, and it is also the hazard. **Every run inherits
the previous run's state, including its mistakes**, and a page that renders correctly
is not evidence that it did. Guards live in `tools/lens/lens_guard.py`; run
`python3 tools/lens/lens_guard.py` to self-test them.

---

## 1. Stale parent

**What happened.** The build fetches the current published lens to use as its
template. On 2026-08-10 that fetch returned a copy from **2026-08-08** — two days
stale, despite a documented 15-minute cache TTL. The build treated it as yesterday's
edition and proceeded.

**Why it is silent.** A stale page is perfectly self-consistent. Its title, masthead
and embedded ledger all agree with each other; they simply describe an older day. The
build had no independent notion of what the parent *should* be, so it believed the
page about itself.

**What it would have cost.** Edition 029 had 106 ledger rows; the 028 copy had 85.
Publishing on the wrong parent would have reverted 21 rows — 11 promises, 14 events,
9 patch entries, among others — with no error and no visual cue. Promise and event
rows are append-only accumulations whose sources have already scrolled past, so they
would not have come back on the next run.

**Guard.** `assert_parent_fresh(parent, expect_date=..., expect_edition=..., today=...)`

Pass `expect_date`/`expect_edition` from an **authoritative source** — the artifact
listing, which is server-side metadata — never from the fetched page itself. It also
refuses a parent dated on or after today, and one older than `max_age_days` (default
4), which catches a missed edition rather than a cache fault.

---

## 2. Shrinking append-only ledger

**What happened.** Today's authoring pass produced its own ledger. Any row it did not
happen to re-mention simply vanished, including sections explicitly documented as
append-only.

**Why it is silent.** The page still renders a full, plausible Promise Tracker. You
only notice by diffing against an edition nobody re-reads.

**Guard.** `assert_no_regression(new, parent, sections=ACCUMULATING)`

`ACCUMULATING = ("benchmarks", "promises", "gaps", "patch")`. These may never come
back smaller than the parent. The error names the lost keys, so the failure is
actionable rather than just a count mismatch.

`merge_parent(ledger, parent, superseded=...)` does the carry-forward. Rows today
deliberately re-keyed go in `superseded` as `{section: {parent_key: today_key}}` so
they are dropped rather than duplicated; everything else the parent has and today
lacks is carried verbatim. The map makes each decision auditable instead of a silent
union — reviewable in the diff, unlike a blanket merge.

---

## 3. Unspliced section (class drift)

**What happened.** Edition 029 marked the landing section `class="view active"`. The
splice matched `class="view"` **literally**, so it never matched, and the section kept
edition 029's text while every other section updated.

**Why it is silent.** The regex over the other 13 sections succeeded, and the
verification step counted sections with the *same* faulty pattern — so the assert
agreed with the bug. It landed on `v-read`, the default-visible "Today's Read" panel:
the single most-read section on the page.

**Guard.** `splice_sections(html, sections, chips, expect=N)`

Tolerant class match (`class="view[^"]*"`), plus two asserts: the number spliced
equals `expect`, and every id in `sections` actually matched. The second is the one
that matters — it catches an id that silently stops existing after a template edit.

> Verification must not reuse the pattern it is verifying. That is what let this one
> through: the check and the bug shared a regex, so the check confirmed the bug.

---

## 4. Host wrapper accumulation

**What happened.** A *served* artifact page is
`[host frame-runtime]<body>[stored source]</body></html>`. Building from the served
copy embeds ~15 KB of host runtime and an extra closing pair into the stored source,
which compounds one layer per edition. Edition 029 had already accumulated three
`</body></html>` pairs.

**Guard.** `strip_host_wrapper(html)` — returns stored source, and is idempotent, so
it is safe on a page that is already clean.

---

## 5. Verifiability drift

**What happened.** The routine's citation rule says every factual item in every lens
section carries an inline source link — the primary URL from the day's briefs, a
dated archive-page fallback, or an explicit "(unsourced — verify)" marker. The help
panel documented the policy. But no renderer enforced it, so the daily builds drifted
into prose attributions ("Seen in: *topic*") that nothing can click, and inheritance
copied the linkless style forward faithfully. Found on 2026-08-20 at edition 040: **14
links across ~15 sections**, all but one of them in Claim Watch — Events (21 rows),
Patch Radar (19), Benchmarks (11), Promises (35), Dossiers (40), Mirror, Gaps,
Questions, Skills, Build, Today's Read and Since-yesterday had none at all. The owner
could not verify a single carried row without hunting manually.

Two structural causes compounded it. The ledger schema was titles-only (`{k, t,
dates}`), so a carried row had no URL anywhere in machine-readable state to render.
And the primary URLs live in the day's brief markdowns, which exist only in the
run's ephemeral scratchpad — a link not captured on the day an item first appears
was simply gone.

**Guard.** `assert_page_link_coverage(html)` — walks every in-page section *and*
every chair's flipped view bodies inside `#povContent`, chunks each into citation
units per `LINK_POLICY` (cards, gaps, table rows, sig bullets, talk tracks), and
fails the build listing every unit that carries neither an `<a href>` nor the
literal unsourced marker. All failures are reported in one error so a build sees
the full damage, not just the first section.

**Constructive half.** `tools/lens/lens_links.py` — mines `(headline, url, topic)`
from the day's briefs, resolves each item same-topic-first with IDF-weighted token
matching (precision over recall: a wrong primary link is worse than the archive
fallback), and `cite(url, *dates)` renders the fallback chain
`primary → archive MM-DD → (unsourced — verify)`. New ledger rows persist the mined
URL in a `url` field so carried rows keep their citation without re-mining.

---

## Related: static nav metadata

Not a build bug so much as a missing step. The left-rail `meta:` strings are
hand-written in the template and are **not** derived from the section chips, so they
persist until something rewrites them. Edition 029 shipped 028's counts, and 030
inherited them verbatim — including the label `vs edition 028`.

**Guard.** `refresh_nav(html, navmeta, expect=N)` rewrites them and asserts each one
took. Derive the values from the merged ledger so the rail and the panel cannot
disagree.

Same shape, same cause: `rewrite_identity()` replaces the title/masthead/const
rewrites, which had been literal string matches keyed to the previous edition's date.
Those no-op silently the moment the parent changes, leaving yesterday's identity on
today's page. It is now pattern-based and asserts exactly one match each.

---

## The pattern

Every one of these is the same shape:

> The build inherits state, assumes the inherited state is what it expects, and
> verifies its work using the same assumption that was wrong.

The general defence is to make the build **state its expectations up front and fail
loudly** when reality disagrees — rather than discovering the mismatch by diffing two
published editions after the fact. Concretely:

- assert the parent's identity against an **external** source, not the parent itself
- assert monotonicity on anything append-only
- assert that each rewrite **took**, counting matches, not just that it ran
- never verify with the same pattern that performed the operation
- make every editorial rule a machine-checked rule — a citation policy that lives
  only in the help panel is a policy inheritance will erode (failure mode 5)
