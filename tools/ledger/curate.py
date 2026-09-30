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
    # 2026-09-30 hand curation, edition 079. Order: exploited-or-past-due KEV
    # first, then "no fix exists for you" by mechanism, then the cutovers that
    # genuinely require action today or tomorrow, then the day's resolution.
    # Text copied from the EXTRACTED briefs (not the handback messages) because
    # the extractor strips markdown and typographic quotes will not match.
    "CVE-2026-86950 \u2014 CoreGraphics OOB write, actively exploited",
    "WSO2 CVE-2026-5430 \u2014 CVSS 10.0, in KEV, due 2026-09-27, and the fix is subscription-gated",
    "CVE-2026-82329 (JFrog 9.8 Critical) is independent and worse",
    "LiteLLM CVE-2026-59822 is in CISA KEV and 14 days past due",
    "CVE-2026-97945: pmd_modify() discards the hardware dirty bit",
    "MetaMCP: unauthenticated RCE, CVSS 9.8, no fix exists",
    "mcp-chrome-bridge: any web page can drive your browser agent",
    "(d) Fix only in a pre-release: PostGIS CVE-2026-73515",
    "(d) Fix only in an unmerged PR: postgres-mcp CVE-2026-85620",
    "Starlette 0.x has a KEV CVE and no backport",
    "Angular \u226419.2.25: two NEW permanently-unpatched Highs this window",
    "Next.js September security release lands TODAY (2026-09-30)",
    "CVE-2026-96443 \u2014 JDBC driver URL validation bypass",
    "BCR-2437 \u2014 Native Apps bootstrap core capabilities, 2026-10-01, and uninstall is the only opt-out",
    "STANDING ITEM RESOLVED \u2014 Aurora PostgreSQL shipped the whole batch on 2026-09-29, at 47 days",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # DELIBERATELY EMPTY for edition 079.
    # The 09-15 and 09-29 notes both record the same self-inflicted failure: the
    # within-topic fold runs BEFORE pinning, so excluding a row can delete the
    # survivor a PIN is trying to keep, and on 09-29 an exclusion would have
    # removed a story from the card entirely. With pins sorting first and the
    # list capped at 12, exclusion buys nothing here and can only cost. Leaving
    # it empty removes the trap rather than navigating it.
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # Hand-verified assertions that these carried rows matter today. Every one
    # was confirmed to be in `ongoing` (not `new`) before being listed -- the
    # 09-29 trap. Longer/surviving wording chosen per the 09-15 rule.
    "CVE-2026-21962 is 34 days past due and the monthly CSPU stream will not fix it",
    "CVE-2026-82067 \u2014 CVSS 9.2 (v4.0)",
    "PgBouncer 1.26.0 (2026-09-23) fixes three CVEs",
    "CVE-2026-31377 \u2014 CVSS 7.5 HIGH, unauthenticated",
    "Agent Bricks Supervisor API (Beta) reaches end of life TODAY",
    "Azure Databricks Standard tier: auto-upgrade to Premium on 2026-10-01",
    # NB: the extracted row uses a STRAIGHT apostrophe (0x27), not U+2019 --
    # the fatal pin guard caught a U+2019 here on the first run. Anchor the
    # substring PAST the apostrophe so the quote style cannot matter at all.
    "unified EU business terms take effect 2026-10-01",
    "GitHub Actions retention begins governing checks",
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
