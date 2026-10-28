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
    # 2026-10-28. Ordered by severity/impact. The lead is the window's new KEV clock.
    # Stories that ALSO appear in `ongoing` with a day count are deliberately NOT
    # picked here and are pinned below instead (the 10-18/10-26/10-27 double-listing
    # shape: two bullets in one brief produce a new key AND a match, and putting a
    # carried deadline under "New" is simply false). That is why the PHP KEV pair,
    # the Redshift TLS cutover, the Genie MCP sunset, the Play target-API extension,
    # Vitess v23.0 EOL, the RDS force-upgrade and CVE-2026-21962 are pins, not picks.
    "Brotli decoder out-of-bounds write, brotli 1.0.3 through 1.2.0",
    "Envoy pins brotli at commit",
    "leak LITELLM_MASTER_KEY to an unauthenticated attacker",
    "Doris CVE-2026-31377, CVSS 3.1 7.5 HIGH",
    "kernel-6.19+ startup guard reads",
    "CVE-2026-85620 still has no fixed release",
    "Next.js Image Optimization SVG RCE affects",
    "Fabric data agent as a custom tool in Microsoft Foundry stops being supported",
    "The October patch round cut TODAY",
    "raised the minimum SGA_TARGET from 724 MB",
    "Oracle Text indexes transported by TTS",
    "in-memory point-lookup workloads",
    "still carry released: true",
    "Three High-severity fastlane advisories landed",
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
    # 2026-10-28. 22 of 24 raw `changed` rows are classifier artifacts: the sev
    # heuristic scores from the title alone, so a reworded carried headline reads as
    # a severity move while the fact sat still. Sixth consecutive run of this shape.
    # The Brotli row is excluded for a DIFFERENT reason worth distinguishing: it is
    # also a `new` pick, so leaving it here would put one story on the card twice.
    "Brotli decoder out-of-bounds write, added to CISA KEV",
    "Measured scanner blindness: the canonical OSV record",
    "CVE-2026-107349's precondition is NOT what yesterday's board said",
    "YugabyteDB v2024.2 LTS reaches end of maintenance",
    "Why I am not flagging the September/October server CVE batches",
    "Atlas Auto Upgrade EOL is still",
    "Oracle Essbase 21.8.3.0.0 took 38 new patches",
    "JDBC MIN_TLS_VERSION/MAX_TLS_VERSION deprecated",
    "Apache Hive catalog endpoint in the Lakehouse runtime catalog went GA",
    "All three first-party drivers changed the default sslmode",
    "JDBC 2.3.0 switches DataSource serialization",
    "ODBC 2.3.0 fixes a stack buffer overflow",
    "CVE-2026-69843, Microsoft Fabric elevation of privilege",
    "DuckDB 2.0.0 LTS \"Cinnamon Teal\" shipped",
    "DuckDB 1.4 support ends 2026-11-17",
    ".NET 8.0 (LTS) and .NET 9.0 (STS) both reach end of support",
    "PHP 8.2 security support ends",
    "Pydantic AI Agent.to_web() CSRF",
    "CVE-2026-12770 (LiteLLM admin key handler) now carries FOUR scores",
    "Nuxt 3 has been end-of-life since 2026-08-05",
    "Flux v2.10.0 (26 Oct) raises the minimum",
    "Before any upgrade to GKE 1.37",
]

EXCLUDE_ONGOING = [
    # 2026-10-28: nothing excluded. Every row a reader needs is either picked or
    # pinned, and excluding a pinned row is what broke the card on 10-15.
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # 2026-10-28. Carried deadlines and overdue KEV clocks that the title-only sev
    # heuristic ranks below hundreds of `normal` rows and which would otherwise fall
    # off the card entirely (the 09-14 shape). Pin the SURVIVING/longer wording and
    # never exclude a row you also pin (the 10-15 rule). A missing pin is fatal.
    "PHP CVE-2026-109618 and CVE-2026-109619 are due",
    "Oracle Secure Backup 19.1.0.0.0",
    "CVE-2026-21962 (CVSS 10.0",
    "Ray CVE-2025-62593 is still in CISA KEV",
    "RDS for PostgreSQL minors 17.6",
    "minimum TLS of 1.2",
    "mcp/genie is sunset",
    "target-API extension expires",
    "Push-Based Log Export stops accepting",
    "TabFM moves to token pricing",
    "Vitess v23.0 reaches end of life",
    "zod < 4.6.6",
    "LiteLLM CVE-2026-114612",
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
