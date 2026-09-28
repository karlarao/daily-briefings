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
    # 2026-09-28 hand curation. The day is a deadline wall: order is cutovers
    # inside 3 days first, then KEV clocks already expired, then "no fix exists
    # for somebody". One row per distinct story; duplicates excluded below.
    "1 Oct 2026 (3 days) \u2014 Native Apps bootstrap, NO opt-out, irreversible.",
    "2026-10-01 (3 days) \u2014 GitHub Actions checks/workflow runs/statuses fall under the Actions retention setting",
    "2026-09-28 (TODAY): OpenAI shuts down gpt-3.5-turbo-instruct, babbage-002",
    "The download page still shows 4.1.3 as \"Latest\" \u2014 verified 2026-09-28",
    "CVE-2026-21962 \u2014 CISA KEV due date passed 32 days ago",
    "CVE-2026-64849 \u2014 MLflow unauthenticated full-read SSRF, CVSS 9.3, in CISA KEV",
    "JFrog Artifactory: four KEV entries, every due date passed, and patching does not end the incident.",
    "Two V8 zero-days sit in CISA KEV and both federal deadlines have expired.",
    "CVE-2026-86350 (Important) is a regression in the fix for CVE-2026-41293",
    "Aurora PostgreSQL has no engine containing the 2026-08-13 batch, 46 days on",
    "PostGIS carries two chained memory-corruption CVEs with NO fix in any stable release",
    "crystaldba/postgres-mcp CVE-2026-85620 is still unfixed, six weeks after the PR was opened.",
    "CVE-2026-82306 has no fixed version named, and NVD has parked it as Deferred.",
    "Next.js 13.x and 14.x have no fix for two Critical unauthenticated RCEs.",
    "16 Oct 2026 (18 days) \u2014 Snowsight account-specific host, no opt-out.",
]

# Hand-verified same-story rows kept OUT of `ongoing`: each restates a row
# already picked or pinned. Per the 09-15 rule the SHORT duplicate is excluded
# and the LONG survivor kept -- never both, and never a row that is also pinned.
EXCLUDE_ONGOING = [
    # 2026-09-28. Each restates a row already picked above; the LONGER survivor
    # is kept and the short duplicate dropped (09-15 rule). Never a pinned row.
    "CVE-2026-21962 is 32 days past its CISA KEV due date, and no CSPU will ever fix it.",
    "GitHub Actions retention now covers checks, workflow runs and statuses \u2014 2026-10-01, three days out.",
    "AKS begins auto-migrating VMAS clusters to Virtual Machines node pools on 2026-09-30, two days out.",
    "(a) Agent Bricks Supervisor API (Beta) \u2014 EOL 2026-09-30, 2 days out.",
    "(a) Play package registration \u2014 2026-09-30, CONFIRMED",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# extract_items scores sev from the TITLE alone, so a dated vendor cutover
# written under "## Heads up" scores `normal` and sorts below a hundred other
# normals -- which is how the single biggest deadline of the day falls off the
# card (2026-09-14). Pins bypass the COMMENTARY heading filter for that reason,
# and a pin that does not match is a FATAL error, not a warning (2026-09-16).
PIN_ONGOING = [
    # 2026-09-28. The 09-30 / 10-01 wall: every one of these is a dated cutover
    # written under a brief's "## Heads up" heading, which the sev heuristic
    # scores `normal`. Without the pin they fall off the card entirely.
    "2026-09-30 (2 days) \u2014 every Play package name must be registered in Play Console",
    "2026-09-30 (2 days) \u2014 AKS auto-migrates VMAS clusters to VM node pools via the auto-upgrader.",
    "2026-09-30 (2 days) \u2014 Agent Bricks Supervisor API (Beta) end of life.",
    "2026-10-01 (3 days) \u2014 Azure Databricks Standard tier retires.",
    "2026-10-01 (3 days) \u2014 Apple's unified EU business terms take effect.",
    "CVE-2026-58704 \u2014 Pixel cellular modem, CISA KEV, remediation due 2026-09-19 (9 days PAST DUE)",
    "MongoDB 8.2 is end-of-life (31 July 2026) and received none of the September CVE batch",
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
            raise SystemExit("ERROR: pick not found (fix the pick text): %s" % pat[:80])
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
