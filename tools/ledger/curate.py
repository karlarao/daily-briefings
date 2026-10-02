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
    # 2026-10-02 hand curation. Order: CISA KEV entries whose due date has already
    # PASSED, then "no fix exists for somebody", then dated cutovers inside 14 days,
    # then requirements already in force. One row per distinct story. The two Apple/
    # Pixel KEV rows, JFrog, Oracle CVE-2026-21962, postgres-mcp, Azure PgBouncer,
    # Starlette and the Snowflake/Databricks cutovers are carried in `ongoing`
    # instead, where they have day counts -- so their restatements here are
    # deliberately NOT picked (the 09-15 one-story-one-row rule).
    "GitLab CVE-2026-85706 \u2014 CVSS 10.0, unauthenticated arbitrary file read, KEV due date 18 days gone",
    "Linux-kernel KEV trio, due 2026-09-21, now 11 days over",
    "ACT NOW \u2014 LiteLLM CVE-2026-59822 is in CISA KEV, confirmed exploited",
    "CVE-2026-97945 \u2014 no fix for RHEL 9, RHEL 10 (Fix deferred) or Ubuntu 24.04 LTS",
    "The Next.js AVIF RCE (CVSS 9.5) is unpatched on every 13.x and 14.x app",
    "One Critical and one High Next.js vulnerability are unpatched in every version today",
    "Four Angular SSR advisories explicitly abandon",
    "archived Doris branches will never be patched",
    "StarRocks CVE-2026-80346 (CVSS 7.1) has no fix on any branch",
    "Fastify: seven advisories on 2026-09-30, five HIGH, and Fastify 4.x gets nothing",
    "first of eight October macos-14 brownout windows",
    "Google shuts down antigravity-preview-05-2026",
    "BCR-2413: Snowsight sign-in and API traffic move to an account-specific host",
    "Already in force 2026-09-23: Node 20 removed from Actions runners",
    "Already in force 2026-09-29: self-hosted runners below 2.329.0 cannot register",
    "Apple now rejects uploads with MinimumOSVersion below 13.0",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # 2026-10-02. Each is the SHORT twin of a row pinned below; per the 09-15 rule
    # the short duplicate is excluded and the longer survivor kept, never both.
    # The JFrog row is excluded for a second, stronger reason: it says THREE KEV
    # entries where the App Dev lane found FOUR, and it repeats the "rotate the
    # Access token signing key" remediation that the App Dev lane disproved
    # against the vendor advisory text. The pinned App Dev row is the correct one.
    "JFrog Artifactory: three KEV entries, every due date passed",
    "CVE-2026-21962 \u2014 KEV due date 2026-08-27, 36 days past due as of today",
    "claude-4-sonnet and openai-gpt-4.1 die on 2026-10-14. 12 days.",
    # Caught by the cross-card shared-CVE check (the 09-18 defect): the picked
    # new row carries the action and the no-fix status for CVE-2026-97945, and
    # this ongoing row is the mechanism explanation of the SAME story. The fuzzy
    # dup_of_picked at 0.45 misses it because the two wordings share little
    # vocabulary -- which is exactly why the id-based check is run by hand.
    "pmd_modify() drops the hardware dirty bit",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # 2026-10-02: carried KEV entries and dated cutovers that outrank most of
    # today's new rows. Pins bypass the COMMENTARY heading filter because dated
    # vendor cutovers are almost always written under "## Heads up". Each pin is
    # the SURVIVING (longer) wording of its story; its short twin is in
    # EXCLUDE_ONGOING above. Never pin and exclude the same row (09-15).
    "CVE-2026-86950 \u2014 Apple CoreGraphics out-of-bounds write, CVSS 8.8, KEV due TODAY",
    "CVE-2026-58704 \u2014 Pixel cellular modem improper authorization, High, 13 days past its KEV due date",
    "JFrog Artifactory: four KEV entries, every due date already passed",
    "ACT NOW \u2014 crystaldba/postgres-mcp CVE-2026-85620 is unpatched, 118 days after it was reported",
    "Azure Database for PostgreSQL's built-in PgBouncer is documented as 1.25.2",
    "CVE-2026-21962 is 36 days past its KEV due date, and the fix is older than the KEV listing",
    "Cortex claude-4-sonnet and openai-gpt-4.1 end of life; calls referencing them fail for every account",
    "Agent Bricks Supervisor API: END OF LIFE 2026-09-30",
    "Azure Databricks Standard tier \u2192 Premium: automatic upgrade landed 2026-10-01",
    "Starlette CVE-2026-48710 is KEV, 16 days overdue, and 0.x will never be fixed",
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
