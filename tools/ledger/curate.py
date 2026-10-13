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
    # 2026-10-13 hand curation (edition 091). Order: KEV clocks expiring today
    # or already expired, then today/tomorrow vendor cutovers, then "no fix
    # exists for somebody", then the dated cliffs inside 14 days.
    # Rewritten every run against TODAY's wording. PICKS bypass the COMMENTARY
    # heading filter by design, so a dated cutover written under "## Heads up"
    # can still be picked -- which is most of them.
    # NOTE (09-18 rule, applied again today): the stories that FEEL like the
    # day's biggest news are not automatically "new". Oracle CVE-2026-21962,
    # the Struts KEV entry, LiteLLM CVE-2026-59822, pgvector CVE-2026-103484,
    # K8s 1.34 EOL, Snowflake BCR-2442, the Doris EOL branches, the Spring
    # paywall, the Redshift ODBC extension and the BigQuery TabFM cutover all
    # MATCHED existing dictionary keys -- they are carried rows with honest day
    # counts and they belong in `ongoing` as pins. Ten of them, this run.
    "CVE-2026-86950 (Apple CoreGraphics OOB write) is in CISA KEV",
    "Strapi CVE-2023-22894 joined KEV the same day",
    "CVE-2026-58704 (Pixel cellular modem) is a zero-click",
    "claude-4-sonnet reaches end-of-life 2026-10-14",
    "Snowsight sign-in traffic moves to an account-specific host",
    "The macos-14 runner is in active brownout",
    "OpenAI legacy shutdown (10 days)",
    "AMD TLBI Erratum #1718 is fixed in mainline",
    "fixed three unauthenticated bugs; Azure's built-in pooler is still 1.25.2",
    "Argo CD v2.x",
    # 09-18 rule applied: "MongoDB 8.2 is EOL ... unpatchable Critical" was
    # picked here on the first pass and is the SAME story as the carried
    # CVE-2026-82067 row, which sits in `ongoing` at day 4. One story, one
    # row -- the carried one wins because its day count is honest. The freed
    # slot goes to the AI Hardware flag, which was otherwise off the card.
    "NVIDIA AIStore ships 8 CVEs, two Critical",
    "CVE-2026-104711 (S2-075, 2026-10-05) has no fix for 2.3.x or 2.5.x",
    "Next.js 13.x and 14.x are confirmed EOL",
    "Gradle published three High advisories on 2026-10-07",
    "October 2026 Critical Patch Update confirmed for 2026-10-20",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # Hand-verified same-story rows: each restates a story already carried in
    # PICKS or PIN_ONGOING, and the fuzzy dup check does not catch it because
    # the two phrasings share little vocabulary.
    "PASSED 2026-10-11 (2 days ago): CISA KEV remediation due dates",
    "TabFM billing switches to tokens",
    # Meta/negative-result and weekend-exercise bullets: real content in the
    # brief, but not "what changed since the last run".
    "No Oracle CVE other than CVE-2026-21962",
    "No mobile cross-platform supply-chain advisories",
    "Run the TLS audit now",
    "Dry-run the 9.0 memory cap",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # Carried dated cutovers and carried KEV clocks the title-only sev heuristic
    # ranks `normal` because they carry no CVE id in the headline or no
    # deprecation keyword, yet are the most consequential dated items on the
    # card. A pin bypasses the COMMENTARY filter (09-16) and must name the
    # SURVIVING wording -- never a row that EXCLUDE_ONGOING also kills (09-15).
    "CVE-2026-21962 is 47 days past its CISA KEV due date",   # 47d past, forensic triage
    "Apache Struts CVE-2016-3081 entered CISA KEV on 2026-10-08",  # due 10-11, expired
    "LiteLLM MCP authentication bypass, is in CISA KEV",      # 27d past due
    "is unfixable on every major managed Postgres",           # pgvector CVE-2026-103484
    "Kubernetes 1.34 upstream end of life",                   # 2026-10-27, 14 days
    "Cortex Agent/Analyst evaluation defaults move to metric v3",  # BCR-2442, TODAY
    "Apache Doris 2.0.x",                                     # branches permanently unfixed
    "Spring CVE-2026-59313: both halves of the claim confirmed",  # paywalled fix
    "ODBC 1.x end of support EXTENDED",                       # a board CORRECTION: 09-30 -> 12-31
    "TabFM on BigQuery moves to token-based billing on 2026-10-30",
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
    changed = sorted(raw["changed"], key=lambda r: rank.get(r.get("_sev"), 2))

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
    ongoing = (pinned + rest)[:12]

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
