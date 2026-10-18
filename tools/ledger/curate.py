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
    # 2026-10-18 hand curation (edition 096). Order: unauthenticated Criticals and
    # silent-data-loss first, then "no reachable fix for somebody", then dated
    # cutovers inside 14 days. Rewritten every run against TODAY's wording.
    # PICKS bypass the COMMENTARY heading filter by design.
    #
    # FOUR PICKS EXIST BECAUSE THE TITLE-ONLY sev HEURISTIC SCORED THEM `normal`
    # (the 2026-09-14 failure class): the MongoDB renameCollection data-loss bug
    # (no CVE id in the title), the TabFM billing flip, the macos-14 brownout and
    # the AMD TLBI erratum. Each is the most consequential item in its lane.
    #
    # 09-18 RULE APPLIED SEVEN TIMES. These stories sit in BOTH `new` and
    # `ongoing`; the pick is DROPPED and the carried row pinned with its honest
    # day count: Genie MCP (d15), Oracle CVE-2026-21962 (d8), Doris no-fix (d8),
    # Apple CVE-2026-86950 (d3), Struts KEV (d2), Argo CD 9.9s (d2), K8s 1.34 (d2).
    "Cross-database renameCollection on a sharded cluster can permanently lose your data",
    "pgvector 0.8.7 fixes arbitrary code execution from an ordinary database user",
    "PgBouncer 1.26.1 fixes a SCRAM authentication bypass",
    "Next.js: unauthenticated RCE via the Image Optimization API",
    "The concrete consequence, measured against OSV today",
    "CVE-2026-31377 \u2014 unauthenticated remote access to the FE meta service",
    "No fix exists for 5.0, 6.0 or 8.2",
    "Bundle 2026_06 generally enabled per release 10.37",
    "Strong-authentication Phase 3 is rolling now and ends this month",
    "2026-10-31 (13 days) \u2014 minimum TLS 1.2 enforced",
    "2026-10-30 \u2014 TabFM on BigQuery switches to token-based pricing",
    "2026-10-19 \u2192 2026-11-02 \u2014 macos-14 runner brownouts",
    "AMD TLBI Erratum #1718: the CPU can fail to invalidate a TLB entry",
    "Every Oracle CVE currently in CISA KEV already has a fix",
    "Opus 5.5 and Haiku 5.5 both make breaking changes to the things you actually set",
    ".NET patch day 2026-10-13 is the biggest single drop this window",
]

EXCLUDE_ONGOING = [
    # One story, one row, regardless of which list it came from (09-18, generalised
    # 10-17). Both of these are second facets of a story already picked or pinned.
    # NOTE (09-15): never exclude a row that PIN_ONGOING also names.
    "Azure's built-in PgBouncer is documented at 1.25.2",
    "Argo CD 3.6.0-rc2 also lands two breaking changes",
]


PIN_ONGOING = [
    # Carried KEV clocks and dated cutovers the title-only sev heuristic ranks
    # `normal`, plus the seven 09-18-rule carries above. A pin bypasses the
    # COMMENTARY filter (09-16) and must name the SURVIVING wording (09-15).
    "2026-10-31 (13 days) \u2014 Beta Genie MCP endpoint",
    "CVE-2026-21962: CISA KEV due date 2026-08-27",
    "Apache Doris 2.0.x, 2.1.x, 3.0.x, 3.1.x \u2014 no security fix exists",
    "CVE-2026-86950 \u2014 Apple CoreGraphics out-of-bounds write",
    "KEV, due date passed: Apache Struts CVE-2016-3081",
    "Argo CD: four CVSS 9.9 Criticals",
    "2026-10-27 \u2014 upstream Kubernetes 1.34 EOL",
    "CVE-2026-104850 / GHSA-6qxp-vccf-f47h",
    "CVE-2026-86597 \u2014 Snowflake drivers write auth tokens",
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
