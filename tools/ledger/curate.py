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
    "there is no reachable fix if you run 26.4",
    "Azure Database for PostgreSQL's built-in PgBouncer is 1.25.2",
    "LiteLLM: unauthenticated file read leaks LITELLM_MASTER_KEY",
    "React: unauthenticated RCE in React Server Components",
    "No reachable fix: Node driver SRV host verification",
    "Foundry's Fabric data agent custom tool is retired 2026-11-06",
    "TLS 1.2 minimum: IN FORCE since 2026-10-31",
    "Google Play's target-API extension window closed on 2026-11-01",
    "Legacy Snowflake Notebooks: execution AND editing stop in November 2026",
    "Fabric Spark returns wrong local times in BC, Alberta and Manitoba",
    "Next.js 13.x and 14.x get no patched release",
    "No reachable fix: SERVER-131805 data loss is unpatched",
    "Pinot — the only fix is a major upgrade",
    "PostgreSQL 14's final release is 2026-11-12",
    "The carried CVE-2026-21962 is unchanged and now 68 days past",
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
    # 2026-10-29: 10 of 13 raw `changed` rows are sev-classifier artifacts --
    # the title-only heuristic re-deriving a different band for the same fact.
    # Seventh consecutive run of this shape. Kept: the MongoDB Go-driver v1
    # no-fix row, the new Parquet KMS-URL flaw, and the .NET 8/9 EOL date.
    # NOTE: matched by PLAIN substring, not dash-normalised (10-28) -- these
    # fragments deliberately contain no dash characters.
    "RDS for PostgreSQL minors 17.6",
    "Ops Manager 8.0.27",
    "DBMS_VECTOR privilege",
    "VPD component",
    "Cross-engine ABAC went GA",
    "errors on the Terraform bundle engine",
    "ODBC 2.3.0 fixes a stack buffer overflow",
    "vLLM CVE-2026-114053",
    "LiteLLM CVE-2026-114612: an internal_user escalates",
    "CVE-2026-111943",
]

EXCLUDE_ONGOING = [

]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    "GitLab CVE-2026-97229 (CVSS 10.0) is in CISA KEV",
    "Patching to the KEV fix leaves you exploitable: CVE-2026-110264",
    "DBR 18.2 end of support is 2026-11-05 (2 days out)",
    "PHP2Shell hits Oracle Secure Backup",
    "variantShredding is added automatically",
    "DuckDB 1.4 support ends",
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
    ongoing = ongoing[:15]

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
