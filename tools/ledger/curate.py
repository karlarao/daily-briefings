#!/usr/bin/env python3
"""Curate the raw step-4c diff into a 60-second "Since yesterday" card.

The raw match output is honest but unreadable (600+ "new" rows, because the 19
research agents reword every headline and the dictionary was built by an older
extractor). Per the routine spec the card lists only what a reader should
actually notice, and `new_more` carries the count of the remaining genuinely-new
items -- with commentary bullets ("Worth your weekend", "Signals worth
watching") excluded from BOTH the list and the count, since they are the
agents' own analysis rather than news.
"""
import json, os, sys, re

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import ledger as L

# Headings whose bullets are the agents' own analysis or restatement rather than
# news, so they are excluded from BOTH the card and the `new_more` count.
# "heads up" joined the set on 2026-09-11: its bullets are overwhelmingly
# restatements of a CVE/deadline item already carried under a news heading in the
# same brief, and counting them twice was the bulk of the over-production
# (unmatched-news 467 -> 311 on the day it was added). That run never landed the
# change in version control; 2026-09-12 did.
COMMENTARY = {"worth your weekend", "signals worth watching", "filtered out", "heads up"}

# Titles hand-picked for the card, in display order. Matched by substring
# against the raw rows so wording stays exactly as the brief published it.
PICKS = [
    "GPUStack CVE-2026-102895 — CVSS 9.8, exploited in the wild",
    "Chrome 158 kills client-side XSLT on 2026-11-17",
    "52 CVEs, 32 at CVSS 8.8, fixed in 18.7",
    "there is no fix at all for 8.1 or 8.2",
    "PgBouncer 1.26.1 (2026-10-14) fixes an authentication bypass",
    "databricks-deepseek-v4-1-flash retires 2026-11-19",
    "Vite: Critical (CVSS 4.0 = 9.1) unauthenticated RCE in the dev server",
    "The Vite advisory names two fix versions that do not exist on npm",
    ".NET 8 (LTS) and .NET 9 (STS) reached end of support on 2026-11-10",
    "November CSPU ships Tuesday 2026-11-17 (3 days out): 652 new security patches",
    "Cost/performance shift — in an audited TPC-H config, DRAM is now 56.6%",
    "Execution risk at NVIDIA became a named variable on 2026-11-12",
    "Three September authorization CVEs still have NO fixed release for the 2.x",
    "Measured gotcha: Node 22's bundled Brotli still reports version 1.1.0",
    "Legacy Notebook execution end has been withdrawn",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
# Rows whose only "movement" is the title-only `sev` heuristic re-deriving a
# different band on a REWORDED headline, while the underlying fact did not move.
# The 19 research agents restate carried items in fresh words every run, so a
# "urgent -> normal" note on an unchanged fact is a classifier artifact, not
# news -- and the spec's "do not invent movement" rule says to drop it. Added
# 2026-10-23, when 3 of 7 `changed` rows were of this shape. Substring match,
# same convention as EXCLUDE_ONGOING; resolve fragments with derive_lists.py.
EXCLUDE_CHANGED = [
    "CVE-2026-125120's fix shipped 91 days before anyone was told about it.",
]

EXCLUDE_ONGOING = [
    "2026-11-18 (4 days out) — CISA KEV remediation due, Apple CVE-2024-27834 (WebKit). forensicTriage: No.",
    "2026-12-02 (18 days out) — pull_request_target permanently blocked by default",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    "GitLab CVE-2026-97229 — CVSS 3.1 10.0 Critical",
    "CVE-2026-118383: use-after-free in replication, reachable without authentication",
    "pgvector CVE-2026-103484 (CVSS 8.8) is unpatchable on managed Postgres",
    "Brotli CVE-2026-111497 is reachable through PyArrow",
    "Starting 2026-11-18, Databricks automatically adds the variantShredding",
    "php2shell — CVE-2026-109618 and CVE-2026-109619 are both in CISA KEV",
    "2026-11-17 (3 days out) — DuckDB 1.4 end of life.",
    "ingress-nginx CVE-2026-116472 (2026-11-05): Kubernetes says, in writing, that it will not fix",
    "BCR-2391 — Azure allowlists must carry Snowflake Network Identifiers by",
    "2026-11-16 (2 days out) — Apple age-rating content descriptors required at submission",
    "WebKit CVE-2024-27834 — KEV due 2026-11-18 (4 days out), actively exploited",
    "MCP SDKs: bearer-token audience confusion in both official implementations",
    "14.25 is the final PostgreSQL 14 release.",
    "EKS 1.31 end of extended support is 2026-11-26 — 12 days out, and the auto-upgrade is irreversible",
    "GitHub Actions pull_request_target brownout window 2: 2026-11-16, 16:00–18:00 UTC (2 days out) — a brownout is not the end of it",
    "TabFM token pricing: two vendor surfaces, two dates",
]


def main():
    raw = json.load(open(os.path.join(SP, "whatsnew.raw.json")))
    secs = json.load(open(os.path.join(SP, "sections.json")))

    # title -> heading, so commentary bullets can be excluded from the count
    heading_of = {}
    for s in secs:
        p = os.path.join(SP, "briefs", s["id"] + ".md")
        if not os.path.exists(p):
            continue
        md = open(p).read()
        cur = ""
        for line in md.replace("\r", "").split("\n"):
            h = re.match(r"^#{1,4}\s+(.*)$", line)
            if h:
                cur = h.group(1).strip().lower()
                continue
            li = re.match(r"^([ \t]*)[-*]\s+(.*)$", line)
            if li and len(li.group(1).replace("\t", "    ")) < 4:
                heading_of[L.headline(li.group(2).strip())] = cur

    def is_news(row):
        return heading_of.get(row["title"], "") not in COMMENTARY

    rank = {"urgent": 0, "high": 1, "normal": 2}

    # ---- new ----
    picked, used = [], set()
    for pat in PICKS:
        for i, r in enumerate(raw["new"]):
            if i in used:
                continue
            if pat in r["title"]:
                picked.append(r)
                used.add(i)
                break
        else:
            print("WARN: pick not found: %s" % pat[:60], file=sys.stderr)
    remaining = [r for i, r in enumerate(raw["new"]) if i not in used and is_news(r)]
    # Fold same-story restatements within a topic before counting. The spec
    # excludes same-story duplicates from the lists AND the counts; this code
    # only excluded commentary headings, which is why new_more ran hot for
    # weeks (543 on 09-10, 311 on 09-11). One CVE covered in a brief's news
    # section, again under "Heads up" and again as a weekend item is one piece
    # of news, not three.
    folded, seen_sets = [], []
    for r in sorted(remaining, key=lambda r: rank.get(r.get("_sev"), 2)):
        ws = set(L.content_words(r["title"]))
        if any(t == r["topic"] and ws and s and len(ws & s) / len(ws | s) >= 0.40
               for t, s in seen_sets):
            continue
        folded.append(r)
        seen_sets.append((r["topic"], ws))
    new_more = len(folded)

    # ---- changed: keep all real movement ----
    changed = [r for r in raw["changed"]
               if not any(x in r["title"] for x in EXCLUDE_CHANGED)]
    changed = sorted(changed, key=lambda r: rank.get(r.get("_sev"), 2))

    # ---- ongoing: the ones that still matter ----
    # A story must not appear in two lists -- the Heads-up restatement of an
    # item and the item itself are the same news to a reader.
    picked_words = [set(L.content_words(r["title"])) for r in picked]

    def dup_of_picked(r):
        w = set(L.content_words(r["title"]))
        return any(w and pw and len(w & pw) / len(w | pw) >= 0.45 for pw in picked_words)

    def excluded(r):
        return any(x in r["title"] for x in EXCLUDE_ONGOING)

    # A PIN is a hand-verified assertion that the row matters, so it overrides the
    # COMMENTARY heading filter. Why (2026-09-16): dated vendor cutovers are almost
    # always written under a brief's "## Heads up" heading, which is_news() strips --
    # so the Snowflake reader-account deletion (4 days out, unrecoverable), the
    # Databricks entitlement enforcement and the Supervisor API EOL all vanished from
    # the card while scoring as pins "not found". Same failure class as the 09-14
    # sev-heuristic miss: the most consequential dated item falls off the card.
    # Pins are still subject to explicit EXCLUDE_ONGOING and to dup-of-picked.
    pinned = [r for r in raw["ongoing"]
              if any(x in r["title"] for x in PIN_ONGOING)
              and not dup_of_picked(r) and not excluded(r)]
    for x in PIN_ONGOING:
        if not any(x in r["title"] for r in pinned):
            raise SystemExit("ERROR: pin not found (fix the pin text): %s" % x)
    pinned.sort(key=lambda r: (rank.get(r.get("_sev"), 2), -int(r.get("days") or 0)))
    ong = [r for r in raw["ongoing"]
           if is_news(r) and not dup_of_picked(r) and not excluded(r)]
    ong.sort(key=lambda r: (rank.get(r.get("_sev"), 2), -int(r.get("days") or 0)))
    rest = [r for r in ong if r not in pinned]

    # Dedupe ONGOING against ITSELF, not only against PICKS. Why (2026-11-01):
    # dup_of_picked() guards the new/ongoing boundary but nothing guarded
    # ongoing-vs-ongoing, so a pinned GitLab KEV row and that same brief's
    # "## Heads up" restatement of it both reached the card -- the 09-18
    # one-story-twice shape arriving through a different door, worked around
    # that day with a hand-written EXCLUDE_ONGOING entry. Same criterion as
    # dup_of_picked (same topic, content-word Jaccard >= 0.45) and applied in
    # priority order, so a pin always wins over the restatement that follows it
    # and an explicit EXCLUDE_ONGOING is no longer needed for this case.
    # Two measures, because one is not enough (measured 2026-11-02). Symmetric
    # Jaccard misses the commonest real duplicate on this card: the SAME story
    # written once as a terse "## Heads up" line and once as a full paragraph.
    # The paragraph's extra content words sit in the union and drag the score
    # under any sane threshold -- two Fabric Foundry rows for the 2026-11-06
    # cutover scored below 0.45 and both shipped. That is the 2026-09-09
    # length-asymmetry finding in a new place: a symmetric measure is the wrong
    # tool when the two sides differ in length. So also test the OVERLAP
    # COEFFICIENT (intersection over the SMALLER side), which asks the right
    # question -- "is the short row essentially contained in the long one?".
    # Guards against over-merging: same topic only, the shorter row must carry
    # at least 5 content words, and priority order is preserved so a pin always
    # survives and the restatement is what gets dropped.
    def dup_of_kept(r, w, keep_words):
        for t, kw in keep_words:
            if t != r["topic"] or not w or not kw:
                continue
            inter = len(w & kw)
            if inter / len(w | kw) >= 0.45:
                return True
            if min(len(w), len(kw)) >= 5 and inter / min(len(w), len(kw)) >= 0.60:
                return True
        return False

    ongoing, keep_words = [], []
    for r in pinned + rest:
        w = set(L.content_words(r["title"]))
        if dup_of_kept(r, w, keep_words):
            continue
        ongoing.append(r)
        keep_words.append((r["topic"], w))
    # Cap the card, but NEVER let the cap eat a PIN. Why (2026-11-14): this run
    # wrote 16 pins against a flat `ongoing[:15]`, and the one that fell off was
    # the Apple age-rating cutover -- a vendor deadline 2 days out on a lane
    # flagged urgent. It sorted last among the pins because `sev` is derived from
    # the TITLE ALONE and scored it `normal`, which is the 2026-09-14 defect
    # exactly, arriving through the cap instead of through the ranking. The
    # pin-not-found check above only proves a pin reached `pinned`; it says
    # nothing about surviving truncation, so the loss was silent.
    # A pin is a hand-verified assertion that the row matters, so pins are kept
    # whole and the cap applies to the unpinned remainder.
    kept_pins = [r for r in ongoing if any(x in r["title"] for x in PIN_ONGOING)]
    kept_rest = [r for r in ongoing if r not in kept_pins]
    ongoing = kept_pins + kept_rest[:max(0, 15 - len(kept_pins))]
    for x in PIN_ONGOING:
        if not any(x in r["title"] for r in ongoing):
            raise SystemExit("ERROR: pin dropped after dedupe/cap: %s" % x)

    out = {
        "prev_date": raw["prev_date"],
        "new": [strip(r) for r in picked],
        "new_more": new_more,
        "changed": [strip(r) for r in changed],
        "ongoing": [strip(r) for r in ongoing],
        "aged_out": raw["aged_out"],
    }
    json.dump(out, open(os.path.join(SP, "whatsnew.json"), "w"), ensure_ascii=False, indent=1)
    print("curated: new=%d (+%d more) changed=%d ongoing=%d aged_out=%d"
          % (len(out["new"]), new_more, len(out["changed"]), len(out["ongoing"]), out["aged_out"]))


def strip(r):
    return {k: v for k, v in r.items() if not k.startswith("_")}


if __name__ == "__main__":
    main()
