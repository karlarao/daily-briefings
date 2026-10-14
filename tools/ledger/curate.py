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
    # 2026-10-14 hand curation (edition 092). Order: KEV clocks already expired,
    # then "no reachable fix for somebody", then dated cutovers inside 14 days.
    # Rewritten every run against TODAY's wording. PICKS bypass the COMMENTARY
    # heading filter by design, so a dated cutover written under "## Heads up"
    # can still be picked -- which is most of them.
    #
    # 09-18 RULE APPLIED FOUR TIMES TODAY. These stories are in BOTH `new` (a
    # fresh key off one bullet) and `ongoing` (a match off another bullet in the
    # same brief), and putting a carried story under "New" is simply false. In
    # each case the pick is DROPPED and the carried row kept with its honest day
    # count, pinned below: Kubernetes 1.34 EOL (day 3), ubuntu-latest -> 26.04
    # (day 12), and the BigQuery TabFM cutover (day 7). The fourth is a
    # cross-lane overlap rather than a key split: LiteLLM CVE-2026-59822 is in
    # `new` from BOTH AI App Dev and AI Daily, so only the App Dev wording --
    # which carries the reachable fix version -- is picked.
    #
    # ONE DELIBERATE EXCEPTION, recorded because it bends the 09-18 rule.
    # Oracle CVE-2026-21962 is a 48-day-old story that the matcher gave a FRESH
    # key (the day count in the headline changes every run, which is exactly
    # what defeats the fuzzy match), and there is no carried row to pin instead.
    # It is picked anyway because its own title states "48 days overdue" -- the
    # row is self-labelling, so no reader is misled about its age. The 09-18
    # rule exists to stop a DAY COUNT lying; here the title carries the truth.
    "PgBouncer 1.26.1 — SCRAM authentication bypass, patched today, no backport.",
    "Mongoid CVE-2026-93762: unauthenticated CVSS 4.0 9.2",
    "AIStore: CVSS 10.0 unauthenticated RCE, and the fix is a one-way two-hop migration.",
    "CVE-2026-21962 — CVSS 10.0, CISA KEV, due 2026-08-27, now 48 days overdue",
    "KEV due 2026-10-13, now 1 day past due, and the fix is in the OLD train",
    "KEV due 2026-09-19, now 25 days past due, forensicTriage",
    "LiteLLM's KEV clock is 28 days past due.",
    "Argo CD's 2026-10-07 batch: four CVSS 9.9 Criticals, and v2.x has no patch for them.",
    "shmem/tmpfs THP loses the dirty bit on zap, and there is no fix for 6.12/6.6/6.1 LTS",
    "crystaldba/postgres-mcp — CVSS 9.2 Critical, unauthenticated, NO FIX.",
    "Storybook: Critical CVSS 9.4 — a malicious website can rewrite your story files",
    "Angular ≤19.2.25: seven High advisories with no fixed version",
    "any authenticated user can drop a legacy synchronous MV in any database, and there is still no fix",
    "Go 1.25 is EOL and did not get the 2026-10-08 batch of 15 stdlib CVEs.",
    "Oracle JDK 21 drops to the OTN licence with the 20 October 2026 CPU — 6 days out.",
    "2026-10-14 (today): Cortex eval metric version v1 and judge model claude-4-sonnet reach end of life",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # "Worth your weekend" exercises that the extractor caught as headlines.
    # Real content in the brief, but not "what changed since the last run".
    "Dry-run the 9.0 per-operation memory limit",
    "Run EXPLAIN CHANGES against every dynamic table DDL change",
    "Audit SELinuxMount exposure before touching 1.37",
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
    # ranks `normal` because they carry no CVE id in the headline, yet are the
    # most consequential dated items on the card. A pin bypasses the COMMENTARY
    # filter (09-16) and must name the SURVIVING wording -- never a row that
    # EXCLUDE_ONGOING also kills (09-15). None of these is in the exclude list.
    "2026-10-27 — Kubernetes 1.34 EOL",              # 13 days, carried at day 3
    "ubuntu-latest migrates from Ubuntu 24.04 to 26.04",  # auto-flip starts 10-19
    "TLS 1.0/1.1 connections rejected from 2026-10-31",   # 17 days, ranked `normal`
    "TabFM on BigQuery moves to token-based billing",     # 2026-10-30, ranked `normal`
    "Genie One MCP Beta endpoint",                   # 2026-10-31 sunset
    "Atlas Push-Based Log Export",                   # 2026-10-30 stops new configs
    "variantShredding is added automatically",        # 2026-11-18, breaks DBR 15.4
    "All three JFrog Artifactory CVEs are now in CISA KEV",  # exploited in the wild
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
