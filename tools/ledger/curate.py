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
    # Per-run hand curation: substrings of the titles to surface on the card,
    # in display order, most severe first. Rewrite every run. Empty is valid --
    # the card then shows nothing as "new" and new_more carries the whole count.
    # 2026-09-15: KEV deadlines first, then unpatched CVEs, then silent-corruption
    # bugs, then the dated cutovers inside 14 days. One row per distinct story.
    "LiteLLM CVE-2026-59822 — MCP auth bypass, in CISA KEV",
    "CVE-2026-85046 — V8 type confusion, exploited in the wild",
    "CVE-2026-87491 — V8 out-of-bounds write, exploited in the wild",
    "Electron stable is behind both fixes",
    "CVE-2026-82067 — authorization subsystem stays in its default disabled state",
    "CVE-2026-85620 — crystaldba/postgres-mcp restricted-mode bypass",
    "CVE-2026-87911 — awslabs.postgres-mcp-server executes OS commands",
    "CVE-2026-73334 has no fixed version",
    "parquet-java 1.18.0 shipped two silent data-corruption regressions",
    "silently duplicate every row",
    "Context7 MCP CVE-2026-75130 — prompt injection with no vendor-named fix",
    "Angular ≤19.2.25: six advisories in the window, none of them fixable",
    "JFrog Artifactory: third KEV pair in a month",
    "Node 20 is removed from GitHub Actions runners on 2026-09-23",
    "Reader accounts auto-upgrade to Workspaces on 2026-09-20",
    "Istio's first GCP-artifact scream test is TODAY",
    "Rust build-time dropper: arrayref 0.3.10",
]

# Hand-verified same-story rows to keep out of `ongoing`: each restates a story
# already carried in PICKS above, and the fuzzy dup check does not catch it
# because the two phrasings share little vocabulary. A hand-read list beats a
# loosened threshold here -- same reasoning as the lens fold_map.
EXCLUDE_ONGOING = [
    # Per-run: ongoing rows that restate something already in PICKS and that the
    # fuzzy dup check misses because the two phrasings share little vocabulary.
    # 2026-09-15: the App Dev Starlette rows restate the LiteLLM/Starlette KEV
    # pick (same 09-16 deadline, different lane); the second Redshift TLS row
    # restates the pinned one.
    "Starlette CVE-2026-48710 is in CISA KEV with a 2026-09-16 due date",
    "2026-09-16 (tomorrow) — CISA KEV due date for Starlette",
    # NOTE: do NOT exclude the Redshift TLS row here. The within-topic fold runs
    # BEFORE pinning, so the short "2026-09-30 — TLS 1.0/1.1 connections
    # rejected." row is folded into the longer "...15 days out" one; excluding
    # the survivor then drops the deadline entirely and the pin reports
    # "not found". Pin the surviving (longer) wording instead.
]


# Ongoing rows that MUST appear regardless of the sev heuristic's verdict.
# Why this exists (2026-09-14): ledger.extract_items scores sev from the title
# alone, so "Workspace entitlement control is enforced ... as of 2026-09-14 and
# opt-out is gone" scored `normal` -- no CVE id, no deprecation keyword -- and
# sorted below 113 other normals, even though it is the day's single biggest
# vendor deadline and its topic is flagged urgent. A hand-verified pin beats
# loosening the ranking, same reasoning as PICKS and the lens fold_map.
PIN_ONGOING = [
    # Per-run: ongoing rows that MUST appear regardless of the sev heuristic.
    # 2026-09-15: three carried deadlines that are bigger than most of today's
    # new rows and would otherwise sort below them.
    "CVE-2026-21962 — CVSS 10.0, in CISA KEV since 2026-08-24",
    "TLS 1.0/1.1 connections rejected starting 2026-09-30",
    "Workspace entitlement control is enforced as of 2026-09-14",
    "Supervisor API (Beta) reaches end of life",
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

    ong = [r for r in raw["ongoing"]
           if is_news(r) and not dup_of_picked(r) and not excluded(r)]
    ong.sort(key=lambda r: (rank.get(r.get("_sev"), 2), -int(r.get("days") or 0)))
    pinned = [r for r in ong if any(x in r["title"] for x in PIN_ONGOING)]
    for x in PIN_ONGOING:
        if not any(x in r["title"] for r in pinned):
            print("WARN: pin not found: %s" % x[:60], file=sys.stderr)
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
