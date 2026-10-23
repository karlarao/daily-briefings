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
    "litellm 1.107.0 shipped a credential stealer plus an hourly remote-code loader",
    "Kubernetes 1.34 reaches end of life 2026-10-27 (4 days out) and v1.34.13 has still not shipped",
    "pgvector 0.8.7 (fix for CVE-2026-103484) is offered by zero of seven managed Postgres services",
    "Chrome removes emSign ECC Root CA - G3 from the Chrome Root Store for all devices on Tuesday morning",
    "Argo CD's four CVSS 9.9 repo-server criticals have no patch for 2.x, ever",
    "React Server Components unauthenticated RCE, CVSS 4.0 9.5, fixed in 19.0.9",
    "Apache Hudi 1.2.0 and 1.2.1, Spark 4.1, VARIANT columns, MoR snapshot reads: wrong results",
    "StarRocks branch-3.5 now pins Ranger 2.9.0, HttpClient5 5.6.4 and BouncyCastle 1.86",
    "Apache Doris 3.1.x is now formally archived",
    "CVE-2026-21589 (Atlassian unauthenticated arbitrary file access) is in CISA KEV",
    "CPython 3.9 and 3.10 still bundle pip releases whose vendored certificate bundle",
    "2026-10-26 (3 days out) — agent dashboard_data_access begins rolling out defaulting to TRUE",
    "Percona Server for MongoDB has the CVE-2026-82067 fix on both live branches",
    "DDR4 16Gb (2Gx8) 3200 spot session average $82.87 vs DDR5",
    "DuckDB 2.0.0 LTS \"Cinnamon Teal\" shipped 2026-10-21",
    "mongosync 1.22 supports neither MongoDB 8.3 nor 9.0",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
# Rows whose only "movement" is the title-only `sev` heuristic re-deriving a
# different band on a REWORDED headline, while the underlying fact did not move.
# The 19 research agents restate carried items in fresh words every run, so a
# "urgent -> normal" note on an unchanged fact is a classifier artifact, not
# news -- and the spec's "do not invent movement" rule says to drop it. Added
# 2026-10-23, when 3 of 7 `changed` rows were of this shape. Substring match,
# same convention as EXCLUDE_ONGOING; resolve fragments with derive_lists.py.
EXCLUDE_CHANGED = [
    'pymongo 3.13.0 (the last 3.x',
    'Client minimum-version floors rose on 2026-09-30',
    "JDBC 2.3.0's DataSource serialization moved",
]

EXCLUDE_ONGOING = [
    "2026-10-31 (8 days): TLS 1.0/1.1 rejected, minimum TLS 1.2 enforced",
    "2026-10-31 (8 days): Beta Genie MCP endpoint /api/2.0/mcp/genie sunsets.",
    "2026-10-30 (7 days) — TabFM billing moves to tokens",
    "2026-10-13 KEV due date, now 10 days past — Apple CVE-2026-86950",
    "CVE-2026-21962 (Oracle HTTP Server / WebLogic Server Proxy Plug-in) is 57 days past",
    "Oracle APEX 24.1.x and 24.2.x have no publicly named fixed build",
    "2026-10-27 (4 days) — Kubernetes 1.34 end of life, almost certainly without v1.34.13",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    "TLS 1.0/1.1 connections rejected from 2026-10-31 (8 days out), provisioned clusters AND serverless workgroups",
    "The Beta Genie MCP endpoint https://<workspace-hostname>/api/2.0/mcp/genie is sunset on 2026-10-31",
    "TabFM token billing starts 10/30/2026 (7 days out) at $0.05/mtok input",
    "Apple CVE-2026-86950 (CoreGraphics out-of-bounds write, CWE-787) is 10 days past its CISA KEV due date",
    "2026-11-01 (9 days) — Google Play Billing Library 7 extension deadline",
    "2026-11-06 — the Microsoft Foundry \"Microsoft Fabric\" custom tool for Fabric data agents stops being supported",
    "2026-10-31 (8 days) — RDS for PostgreSQL end of standard support for eight minor versions",
    "CVE-2026-82067 — \"authorization may remain in a default disabled state during server startup\"",
    "CVE-2026-21962 still unpatched by omission — 57 days past KEV due",
    "Oracle APEX CVE-2026-101521, CVSS 9.8, unauthenticated over HTTPS, affects 24.1.0",
    "next@15.5.28 still declares optionalDependencies.sharp",
    "mongo-go-driver v1 has no fix for CVE-2026-107325",
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
    changed = [r for r in raw["changed"]
               if not any(x in r["title"] for x in EXCLUDE_CHANGED)]
    changed = sorted(changed, key=lambda r: rank.get(r.get("_sev"), 2))

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
    ongoing = (pinned + rest)[:15]

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
