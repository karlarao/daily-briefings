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
    # 2026-10-09 hand curation. Order: KEV clocks expired or inside the bar,
    # then "no fix exists for somebody", then requirements already in force,
    # then dated cutovers, then the board corrections and RESOLUTIONS (a prior
    # edition's urgent resolving is worth as much as a new flag -- 09-12).
    # NOT picked, deliberately: Oracle CVE-2026-21962, the Databricks CLI
    # Terraform removal, the CoreGraphics KEV date, Power BI Desktop, K8s 1.34
    # EOL, the Play API-36 extension and the Atlas log-export cutoff -- all
    # seven are CARRIED in `ongoing` with honest day counts and are PINNED
    # below instead. Putting a 43-day-overdue KEV entry under "New" is false
    # (the 09-18 lesson: two bullets in one brief can produce a new key AND a
    # match, which puts one story on the card twice).
    "CISA added Apache Struts CVE-2016-3081 and Strapi CVE-2023-22894 to KEV on 2026-10-08",
    "Argo CD: four criticals, all CVSS 9.9, patched 7 Oct",
    "pgvector CVE-2026-103484",
    "Next.js 13.x and 14.x will not be patched.",
    "Apache Doris 2.0.x / 2.1.x / 3.0.x / 3.1.x: no fix, ever",
    "StarRocks 3.5 LTS: no release since 3.5.21 (28 Aug)",
    "Postgres MCP Pro's CVSS 9.2 restricted-mode bypass has no fix",
    "The quiet headline: Mongoid shipped eight CVEs on 2026-09-18",
    "Apache Polaris CVE-2026-97395 (CVSS 8.1)",
    "Go 1.27.2 and 1.26.9 (2026-10-08): 15 advisories",
    "Pgpool-II patched seven CVEs on 2026-09-29",
    "Bundle 2026_07 goes enabled-by-default during release 10.37, which is running now.",
    "ODBC \u2192 ADBC: the default flip starts this month",
    "Android developer verification went into effect 2026-09-30",
    "OpenAI shuts down 17 model and fine-tune entries.",
    "Correction to the carried note: this is NOT a database CVE.",
    "Carried item RESOLVED (1/2): CVE-2026-82067 is patched on every supported branch.",
    "Correction to carried context: Aurora PostgreSQL is no longer behind on the 28-CVE batch.",
    "CARRIED-CONTEXT CORRECTION \u2014 the board conflates two containerd advisory batches.",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # 2026-10-09: same-story duplicates of a PINNED row, plus one urgent-scored
    # row that is a release date rather than a deadline. Never exclude a row
    # you also pin (09-15) -- each of these is a DIFFERENT row from its pin.
    "Power BI Desktop from March 2026 or earlier can no longer save/share",
    "Run pq-adbc-advisor against your biggest workspace this week",
    "DuckDB 2.0 GA is expected in the second half of October",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # 2026-10-09: act-now stories that are CARRIED rather than new, so they
    # belong in `ongoing` with their day counts. Pins bypass the COMMENTARY
    # heading filter because dated cutovers are almost always written under
    # "## Heads up" (the 09-16 fix), and a missing pin is a SystemExit by
    # design. Pin the SURVIVING wording (09-15).
    "CVE-2026-21962 is 43 days past its CISA KEV due date",
    "ALREADY IN FORCE \u2014 Databricks CLI v1.20.0 (2026-10-07) removed the Terraform deployment engine",
    "2026-10-13 \u2014 CISA KEV due date for CVE-2026-86950",
    "Already in force this month: Power BI Desktop March 2026 or earlier can no longer save or share",
    "2026-10-27 (18 days): Kubernetes 1.34 end of life",
    "2026-11-01 \u2014 Play target API 36 extension expires",
    "Atlas Push-Based Log Export stops accepting new configurations on 2026-10-30",
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
