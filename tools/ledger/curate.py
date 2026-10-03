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
    # 2026-10-03 hand curation. Order: CISA KEV entries whose due date has ALREADY
    # PASSED, then the one dated cutover inside 14 days, then "no fix exists for
    # somebody", then the two measurement failures that change what a scanner tells
    # you. One row per distinct story -- Apple CVE-2026-86950 is carried in `ongoing`
    # instead (it has a day count there), so its App-Dev-style restatement is
    # deliberately NOT picked, per the 09-18 one-story-one-row rule.
    "CVE-2026-21962 \u2014 CVSS 10.0, CISA KEV, 37 days past due, forensic triage required, fixed since January.",
    "VERIFIED \u2014 GitLab CVE-2026-85706: KEV due date 2026-09-14, now 19 days past",
    "Starlette CVE-2026-48710 (\"BadHost\") \u2014 in CISA KEV since 2026-09-02, due 2026-09-16, now 17 days overdue.",
    "CVE-2026-58704 \u2014 Pixel cellular-modem privilege escalation, KEV due 2026-09-19 (14 days past)",
    "Kestra OSS CVE-2026-49869 is a CVSS 10.0 KEV entry 28 days past due",
    "2026-10-05 14:00 UTC \u2192 2026-10-06 00:00 UTC \u2014 first GitHub Actions macos-14 brownout; jobs fail.",
    "No vendor fix for RHEL 9, RHEL 10 or Ubuntu 24.04 LTS: CVE-2026-97945",
    "Apache Doris 2.0.x / 2.1.x / 3.0.x / 3.1.x \u2014 permanent no-fix status, effective now.",
    "StarRocks CVE-2026-80346 \u2014 no patched release on any line as of 2026-10-03.",
    "Angular \u226419.2.25 will never be patched for the six in-window advisories.",
    "Fastify 4.x is permanently unpatched for four CVEs disclosed 2026-09-04",
    "crystaldba/postgres-mcp CVE-2026-85620 \u2014 Critical, unpatched, and I verified every patch route",
    "Azure Database for PostgreSQL flexible server: built-in PgBouncer is 1.25.2 and you cannot change it",
    "CONTRADICTION WORTH ACTING ON: the NVD record's affected range says \"\u2264 4.0.13\"",
    "CVE-2026-94545 next/og ImageResponse RCE is Critical 9.5 at Vercel and Medium 5.3 at NVD",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # 2026-10-03: caught by the HAND-RUN id-based cross-card check, not by the fuzzy
    # dup_of_picked test -- the two phrasings share too little vocabulary (the 09-18
    # defect, which recurred on 10-02 and again today). CVE-2026-80346 appeared both
    # as a picked `new` row and as its own verification in `ongoing`; one story, one
    # row, and the picked `new` row is the longer survivor.
    "VERIFIED, and the answer is NO: CVE-2026-80346 has no fix on any branch today",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # 2026-10-03: carried rows that outrank most of today's new rows and would
    # otherwise sort below them. Apple's KEV date passed YESTERDAY; Cortex and
    # BCR-2413 are the only two day-precise vendor cutovers inside 14 days; JFrog
    # is 28 days past due with observed exploitation. Pins bypass the COMMENTARY
    # heading filter because dated cutovers are almost always written under
    # "## Heads up" (09-16 rule), and the LONGER wording is pinned (09-15 rule).
    "CVE-2026-86950 \u2014 Apple CoreGraphics OOB write, KEV due date passed 2026-10-02",
    "2026-10-14 (11 days): Cortex claude-4-sonnet and openai-gpt-4.1 end-of-life.",
    "BCR-2413 \u2014 Snowsight sign-in moves to an account-specific host on 2026-10-16 (13 days out)",
    "JFrog Artifactory: three KEV entries, all past due, all under observed exploitation.",
    "2026-09-30 \u2014 PASSED: Supervisor API (Beta) end of life.",
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
