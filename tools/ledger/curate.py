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
    # 2026-10-12 hand curation (edition 090). Order: KEV clocks expiring today or
    # tomorrow, then today/tomorrow vendor cutovers, then "no fix exists for
    # somebody", then the dated cliffs inside 14 days.
    # Rewritten every run against TODAY's wording. PICKS bypass the COMMENTARY
    # heading filter by design, so a dated cutover written under "## Heads up"
    # can still be picked -- which is most of them.
    # NOTE (09-18 rule): four stories that LOOK like today's biggest news are
    # deliberately NOT here -- the Snowflake 10-14 model removal, the Aurora
    # 28-CVE correction, the Atlas log-export retirement and the Genie MCP
    # sunset all MATCHED existing dictionary keys, so they are carried rows with
    # honest day counts and they belong in `ongoing` as pins. Filing a carried
    # story under "New" is the failure that put one story on the card twice.
    "CISA KEV due date for CVE-2026-86950",
    "The real Struts KEV entry is CVE-2016-3081",
    "Second KEV entry in this lane, also expired 2026-10-11",
    "macos-14 brownout is live right now",
    "Azure Storage GPv1 retirement, forced and irreversible",
    "10.37 (Oct 8",
    "BCR-2413, a network change with no opt-out",
    "Argo CD: four CVSS 9.9 Criticals, and the 2.x line gets nothing",
    "OpenAI shuts down a large legacy batch",
    "Already past due: CVE-2026-21962",
    "is in CISA KEV, added 2026-09-02",
    "Aurora PostgreSQL ships pgvector 0.8.2",
    "CONFIRMED, unchanged: Azure's built-in PgBouncer is 1.25.2",
    "status is now a published policy",
    "StarRocks 3.5 LTS has had no release since 3.5.21",
    "The 8.2 gap, stated precisely",
    "is still unfixed, and the project looks dormant",
    "Equality deletes are now PROHIBITED in Iceberg V4",
    "Vercel has pre-announced an out-of-band",
    "one is an unauthenticated auth bypass with no fix for v4",
    "Percona Server for MongoDB has shipped the fix",
    # The run's sharpest correction: our own lead CVE id was a phantom.
    "CVE-2026-61882 DOES NOT EXIST",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # Meta/negative-result and weekend-exercise bullets: real content in the
    # brief, but not "what changed since the last run".
    "No product in this lane is in CISA KEV",
    "No BigQuery security bulletin was published",
    "Inventory your pgvector version everywhere",
    "Read the Pgpool-II watchdog CVEs as an architecture review",
    "Dry-run the scene-lifecycle migration",
    "Why nothing here is urgent, stated explicitly",
    # same-story second key for a row picked above
    "TODAY, 14:00 UTC 12 Oct",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # Carried dated cutovers the title-only sev heuristic ranks `normal` because
    # they carry no CVE id and no deprecation keyword, yet are the most
    # consequential dated items on the card. A pin bypasses the COMMENTARY
    # filter (09-16) and must name the SURVIVING wording -- never a row that
    # EXCLUDE_ONGOING also kills (09-15).
    "hard model removal",                       # Snowflake, 2026-10-14, queries FAIL
    "Genie MCP Beta endpoint",                  # Databricks, 2026-10-31
    "TabFM on BigQuery switches to token billing",   # 2026-10-30
    "Atlas Push-Based Log Export stops accepting NEW configurations",  # 2026-10-30
    # Two board RESOLUTIONS. A prior edition's urgent resolving is worth as much
    # as a new flag (09-12), and both of these retire a carried "no fix" claim.
    "Aurora is no longer behind on the 28-CVE batch",
    # The new urgent that is a carried key rather than a new one.
    "pgvector 0.8.7 fixes CVE-2026-103484",
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
