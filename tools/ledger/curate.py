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
    # --- actively exploited, in CISA KEV ---
    "AI-agent swarm mass-exploited PaperCut NG/MF",
    "GitLab CVE-2026-85706 — CVSS 10.0, unauthenticated arbitrary file read, in CISA KEV since 09-11",
    "CISA KEV due date for CVE-2026-21962 was 2026-08-27 and has passed",
    # The DevOps brief carries the same GitLab CVE from the CI/CD angle. One
    # story, one row -- the App Dev phrasing above names the fixed versions.
    # --- unpatched for someone, which is this window's dominant CVE shape ---
    "CVE-2026-82067 — current state: fixed upstream, still open on Percona",
    "Angular SSR: two High + two Moderate advisories",
    # --- hard deadlines inside 14 days ---
    "September 2026 CSPU confirmed for Tuesday 2026-09-15",
    "Reader accounts lose Legacy Dashboards on 2026-09-20 (8 days out)",
    "GHEC self-hosted runners below 2.329.0 lose registration and execution",
    # Databricks entitlement enforcement (14 Sep) is deliberately NOT picked:
    # it matched an existing key and shows in `changed`, where the day count
    # and the movement say more than listing it as new would.
    # --- resolution of a prior edition's urgent: worth as much as a new one ---
    "parquet-java 1.18.1 is GA as of 2026-09-04, not an RC",
    # --- notable non-urgent ---
    "Three StarRocks CVEs disclosed Aug 28–29",
    "Astro had the same libheif/sharp RCE — Critical, fixed in 7.2.8",
    "Redis 8.10.1 and the 8.8/8.6/8.4/8.2/7.4/7.2/6.2 backports",
    "The Iceberg V4 equality-delete deprecation vote PASSED on 2026-08-20",
    "KMS permission enforcement on Serverless APIs is live and can break your IaC",
    "The ODBC→ADBC transition hit GA in the September 2026 Fabric what's-new",
]


def main():
    raw = json.load(open(os.path.join(SP, "whatsnew_raw.json")))
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
    new_more = len(remaining)

    # ---- changed: keep all real movement ----
    changed = sorted(raw["changed"], key=lambda r: rank.get(r.get("_sev"), 2))

    # ---- ongoing: the ones that still matter ----
    # A story must not appear in two lists -- the Heads-up restatement of an
    # item and the item itself are the same news to a reader.
    picked_words = [set(L.content_words(r["title"])) for r in picked]

    def dup_of_picked(r):
        w = set(L.content_words(r["title"]))
        return any(w and pw and len(w & pw) / len(w | pw) >= 0.45 for pw in picked_words)

    ong = [r for r in raw["ongoing"] if is_news(r) and not dup_of_picked(r)]
    ong.sort(key=lambda r: (rank.get(r.get("_sev"), 2), -int(r.get("days") or 0)))
    ongoing = ong[:12]

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
