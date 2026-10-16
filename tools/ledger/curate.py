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

PICKS = [
    # 2026-10-16 hand curation (edition 094). Order: KEV clocks already expired,
    # then the cutover firing TODAY, then unauthenticated RCEs, then "no
    # reachable fix for somebody", then dated cutovers inside 14 days.
    # Rewritten every run against TODAY's wording. PICKS bypass the COMMENTARY
    # heading filter by design, so a dated cutover written under "## Heads up"
    # can still be picked -- which is most of them.
    #
    # 09-18 RULE APPLIED FOUR TIMES TODAY. These stories sit in BOTH `new` (a
    # fresh key off one bullet) and `ongoing` (a match off another bullet in the
    # same brief); putting a carried story under "New" is simply false. In each
    # case the pick is DROPPED and the carried row kept with its honest day
    # count, pinned below: BCR-2413 (day 2, fires today), Pixel CVE-2026-58704
    # (day 2, 27 days past KEV due), StarRocks CVE-2026-80346 (day 2, still no
    # fix on any train) and BigQuery TabFM token billing (day 8).
    "Apple CVE-2026-86950 — KEV deadline expired 13 Oct",
    "macos-14 is being browned out right now",
    "Next.js: two unauthenticated RCEs (CVSS v4 9.5)",
    "Storybook: Critical 9.4 dev-server code injection",
    "Argo CD: four CVSS 9.9 repo-server RCEs",
    "AMD TLBI Erratum #1718 — the workaround shipped",
    "PgBouncer 1.26.1 fixes an 8.8 SCRAM auth bypass",
    "URGENT / no fix your tooling will find: eight Mongoid CVEs",
    "CVE-2026-85620 — postgres-mcp restricted-mode bypass",
    "fast-jwt dropped five advisories at once",
    "ORDS is the one to pre-stage",
    "2026-10-20 — Oracle JDK 21 leaves permissive licensing",
    "2026-10-23 (7 days) — OpenAI legacy snapshot shutdown",
    "Apache Doris 2.0.x / 2.1.x / 3.0.x / 3.1.x: five September CVEs",
    "PostgreSQL's output_plugin_libraries GUC",
    "2026-10-30 (14 days) — THE FLAG. Three pay-per-token models retire",
]

EXCLUDE_ONGOING = [
    # "Worth your weekend" exercises the extractor caught as headlines. Real
    # content in the brief, but not "what changed since the last run".
    # NOTE (09-15): never exclude a row that PIN_ONGOING also names -- the fold
    # runs before pinning, so an exclude can delete the row a pin is trying to
    # keep and the pin then reports "not found". None of these is pinned.
    "Run pq-adbc-advisor against your biggest workspace",
    "Select AI for Java",
    "October 2026 Pixel bulletin adds three Pixel-specific Criticals",
]


PIN_ONGOING = [
    # Carried dated cutovers and carried KEV clocks the title-only sev heuristic
    # ranks `normal` because they carry no CVE id in the headline, yet are the
    # most consequential dated items on the card. A pin bypasses the COMMENTARY
    # filter (09-16) and must name the SURVIVING wording -- never a row that
    # EXCLUDE_ONGOING also kills (09-15). None of these is in the exclude list.
    #
    # The first fires TODAY and scores `normal` on the title-only heuristic,
    # which is exactly why the pin mechanism exists.
    "2026-10-16 (TODAY) — BCR-2413, Snowsight account-specific sign-in host",
    "Google Pixel CVE-2026-58704 — 27 days past its KEV due date",
    "StarRocks CVE-2026-80346 — no fix on any train, 51 days and counting",
    "2026-10-30 (14 days) — TabFM on BigQuery moves to token billing",
    "2026-10-30 — legacy Teams and Outlook activities can no longer be ADDED",
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
