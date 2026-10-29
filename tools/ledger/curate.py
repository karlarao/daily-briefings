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
    # Severity-ordered. 2026-10-29: the day is a deadline wall plus three
    # genuinely-new no-fix rows. Fragments copied from derive_lists.py probe
    # output; the which-list check ran first (10-27/10-28 rule).
    "Arrow C++/PyArrow 26.0.0",
    "pgvector CVE-2026-103484 (CVSS 8.8) fixed in 0.8.7",
    "A Linux kernel KEV entry added yesterday chains",
    "The alert's Rev 1 (2026-10-25) did NOT list Oracle Secure Backup",
    "containerd's supported-branch table confirms 2.2 goes End of Life",
    "Databricks Runtime 18.2 reaches end of support",
    "TLS 1.0/1.1 connections rejected starting 2026-10-31",
    "MFA Phase 3 \u2014 \"Strong authentication for ALL users\"",
    "OpenAI's Evals platform: existing evals become read-only",
    "PostgreSQL 14 reaches EOL with its final minor release",
    "Doris 3.1 is archived with no further security patches",
    "Next.js 16.4.1 and 15.5.28",
    "remove_training_data",
    "DDR4 16Gb (2Gx8) 3200 spot now averages",
    "Google Play's target-API enforcement began 2026-08-31",
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
    # Short restatements of a row already carried in PICKS above.
    "containerd 2.2 End of Life.",
    "Doris 3.1 is now marked",
    # 2026-10-29: one story twice on the card. The pin fragment matched both
    # the substantive row and its short "Heads up" restatement; drop the short
    # one so the survivor keeps the detail.
    "2026-10-30 (1 day): Atlas",
    # CVE-2026-109618/109619 appeared THREE times: the new Oracle Secure Backup
    # Rev 2 row (kept, it is the new fact), the App Dev "due TODAY" deadline row
    # (kept), and this Oracle restatement of both. Drop the third.
    "PHP2Shell, CVE-2026-109618 + CVE-2026-109619, unauthenticated RCE, added",
    # Oracle carried five ongoing rows; this is the least actionable of them.
    "GoldenGate took 11 patches",
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # Carried dated/KEV rows that the title-only sev heuristic ranks too low.
    # Hand-verified, same pattern as PICKS and the lens fold maps. Pin the
    # SURVIVING (longer) wording, and never pin a row also excluded (10-15).
    "Atlas Push-Based Log Export stops accepting new configurations",
    "Fabric data agent custom-tool integration",
    "Both PHP KEV entries",
    "CVE-2026-21962 is still absent from the October CPU",
    "PgBouncer CVE-2026-107350 (CVSS 8.8) lets anyone holding one",
    "AIStore CVE-2026-65162 (CVSS 10.0) lets an unauthenticated",
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
