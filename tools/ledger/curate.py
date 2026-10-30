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
    "Claude Code for VS Code/Cursor 2.1.313 shipped a backdoor",
    "GitLab CE/EE CVE-2026-97229 — unauthenticated RCE on the GitLab server",
    "Linux kernel CVE-2026-46300 (\"Fragnesia\")",
    "ClickHouse CVE-2026-116366 — unauthenticated RCE on ClickHouse Server",
    "CVE-2026-97631 — EDK II NetworkPkg/UefiPxeBcDxe ICMP buffer overflow",
    "eight RDS for PostgreSQL minor versions reach end of standard support",
    "MFA Phase 3 \"Strong authentication for all users\" window",
    "AKS has a one-day cliff: Azure Linux 2.0 node images",
    "TabFM on BigQuery moved to token billing",
    "DBR 10.4 LTS reaches end of life 2026-11-01",
    "Every NuGet.org API key created before 2026-08-17 expires",
    "PostgreSQL 14's final-ever patch release",
    "Supermicro BMC: eight CVEs disclosed 2026-10-26",
    "Next.js: unauthenticated RCE in use cache functions returning typed arrays",
    "\"Upgrading alone changes nothing\" is a new and worse shape",
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
    # 2026-10-29: 10 of 13 raw `changed` rows are sev-classifier artifacts --
    # the title-only heuristic re-deriving a different band for the same fact.
    # Seventh consecutive run of this shape. Kept: the MongoDB Go-driver v1
    # no-fix row, the new Parquet KMS-URL flaw, and the .NET 8/9 EOL date.
    # NOTE: matched by PLAIN substring, not dash-normalised (10-28) -- these
    # fragments deliberately contain no dash characters.
    "RDS for PostgreSQL minors 17.6",
    "Ops Manager 8.0.27",
    "DBMS_VECTOR privilege",
    "VPD component",
    "Cross-engine ABAC went GA",
    "errors on the Terraform bundle engine",
    "ODBC 2.3.0 fixes a stack buffer overflow",
    "vLLM CVE-2026-114053",
    "LiteLLM CVE-2026-114612: an internal_user escalates",
    "CVE-2026-111943",
]

EXCLUDE_ONGOING = [
    "2026-10-31 (TOMORROW) — TLS 1.0/1.1 connections rejected on both provisioned",
    "CISA KEV due date for CVE-2026-109618 / CVE-2026-109619 was 2026-10-29",
    "2026-11-06 (7 days): containerd 2.2 End of Life.",
    "Oracle APEX 24.1.x and 24.2.x have no publicly named fixed build",
    "CVE-2026-111497 re-read from primary records: CISA KEV dateAdded",
    "CISA KEV: CVE-2026-111497 remediation due 2026-11-10 — 11 days.",
    "2026-11-10 (11 days): CISA KEV remediation due for CVE-2026-111497 (Brotli), with BOD",
    "CVE-2026-111497 (Brotli decoder out-of-bounds write) is in CISA KEV, added 2026-10-27",
    "Audit your Go go.mod by hand, not with a scanner",
    "Next.js 14.x and 13.x are listed as \"Unsupported Versions\" on Vercel's own",
    "Oracle Secure Backup also took six CVEs in the October 20 CPU",
    "The JVM's first attempt at the same bug, CVE-2026-91403",
    "CVE-2026-21962 is 64 days past its KEV due date of 2026-08-27, with forensic-triage",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    "PgBouncer SCRAM authentication bypass, CVE-2026-107350",
    "Oracle Secure Backup 19.1.0.0.0–19.1.0.1.0 is affected by CVE-2026-109618",
    "CVE-2026-114820 (OpenJDK security-libs/java.security",
    "Apache Arrow 26.0.1 RC1 staged 2026-10-30",
    "missing BSON array length validation in the MongoDB Go driver",
    "Redshift rejects TLS 1.0/1.1 connections from 2026-10-31",
    "Atlas Push-Based Log Export stops accepting new configurations TODAY",
    "containerd 2.2 reaches End of Life on 2026-11-06",
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
