#!/usr/bin/env python3
"""
Step-4c ledger tooling for the daily-briefings routine.

Three commands:

  extract   briefs/*.md  ->  <date>.json      (today's titles-only headline ledger)
  match     <date>.json + keys.json           -> match report (new/changed/ongoing/aged_out)
  finalize  writes keys.json back + emits whatsnew.json

Why this file exists in the repo: it was rewritten from scratch on 2026-09-04,
2026-09-06 and again on 2026-09-08 because it only ever lived in an ephemeral
session scratchpad. The matcher thresholds below are the *retuned* ones from
2026-09-08 (see CLAUDE.md "Two silent drifts"); losing them costs a day of
bad day-counts, so the script is version-controlled now.

MATCHER CONTRACT (do not loosen without re-eyeballing the weakest merges):
  - deterministic first: draft key == entry key, or draft key in entry aliases
  - fuzzy: SAME TOPIC only, candidate entries with last_seen within 45 days
        accept if   ratio >= 0.90
              or    ratio >= 0.62 AND (shared strong anchor OR jaccard >= 0.50)
    where a "strong anchor" is a HARD identifier only (CVE/GHSA id, dotted
    version, bundle id like 2026_06, alphanumeric part name) -- NOT any word
    over three characters, which is what made the pre-09-08 matcher useless.
  - never merge two items that both appear in TODAY's run
  - when unsure, do not merge (a missed match costs one day of "new" noise;
    a wrong merge poisons days_seen forever)

TALLY GUARD (flag-independent, protects reruns AND backfills):
  never bump seen_count for a story whose last_seen is already today.

RE-RUN SAFETY: `finalize` is only safe to re-run after restoring keys.json to
its pre-run state (`git checkout archive/ledger/keys.json`) -- otherwise the
guard is the only thing between you and a double count.
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher

WINDOW_DAYS = 45
AGED_OUT_DAYS = 7
RETURNING_DAYS = 7

# ---------------------------------------------------------------- extraction

LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^\s)]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
SKIP_HEADINGS = {"filtered out"}

STOP = set("""a an the and or but of for to in on at by with from as is are was were be been
being it its this that these those has have had will would can could should may might must
new now not no than then there their they you your our we us he she them what which who whom
into over under after before more most less least other another such same own just also very
about across against among around behind below beside between beyond during except inside
outside since through toward under until upon within without per via vs versus if when while
because so both each few many some all any both did does do done get gets got""".split())


def strip_links(text):
    return LINK_RE.sub(lambda m: m.group(1), text)


def first_url(text):
    m = LINK_RE.search(text)
    return m.group(2) if m else None


def norm_title(text):
    # Drop link markdown ENTIRELY (label included) -- trailing "[source](url) ·
    # [docs](url)" citations otherwise dominate the string and wreck similarity.
    t = LINK_RE.sub("", text)
    t = t.replace("**", "").replace("*", "").replace("`", "")
    t = re.sub(r"[·|]\s*$", "", t)
    t = re.sub(r"\s+", " ", t).strip(" ·-—")
    return t


# The dictionary's titles run ~73 chars (median). Today's bullets run 200-400.
# Comparing a 400-char bullet against a 73-char entry tanks SequenceMatcher no
# matter how good the thresholds are, so headline titles are cut to their first
# sentence and capped. (Root cause of the 2026-09-09 under-merge.)
TITLE_CAP = 200


def headline(text):
    t = norm_title(text)
    # first sentence: a period/!/? followed by space + capital, where the period
    # is not part of a version number ("18.6") or an abbreviation.
    m = re.search(r"(?<![0-9A-Z])[.!?](?=\s+[A-Z(])", t)
    if m and m.start() >= 40:
        t = t[:m.start() + 1]
    if len(t) > TITLE_CAP:
        cut = t.rfind(" ", 0, TITLE_CAP)
        t = t[:cut if cut > 60 else TITLE_CAP].rstrip(" ,;:·-—") + "…"
    return t


def content_words(title):
    ws = re.findall(r"[a-z0-9][a-z0-9._/-]*", title.lower())
    return [w for w in ws if w not in STOP and len(w) > 2]


# A strong anchor is a HARD identifier only. Generic nouns are deliberately
# excluded -- that was the 2026-09-08 bug.
CVE_RE = re.compile(r"\bcve-\d{4}-\d{4,7}\b", re.I)
GHSA_RE = re.compile(r"\bghsa-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}\b", re.I)
VER_RE = re.compile(r"\b\d+\.\d+(?:\.\d+)*\b")
BUNDLE_RE = re.compile(r"\b(?:19|20)\d{2}_\d{2}\b")
# alphanumeric part / model names: at least one letter AND one digit, e.g.
# "gb200", "epyc9755", "ddr5", "hbm4", "pcie6", "mi355x"
PART_RE = re.compile(r"\b(?=[a-z]*\d)(?=\d*[a-z])[a-z0-9]{3,}\b", re.I)


def strong_anchors(title):
    t = title.lower()
    out = set()
    out.update(m.group(0) for m in CVE_RE.finditer(t))
    out.update(m.group(0) for m in GHSA_RE.finditer(t))
    out.update(m.group(0) for m in BUNDLE_RE.finditer(t))
    out.update(m.group(0) for m in VER_RE.finditer(t))
    for m in PART_RE.finditer(t):
        w = m.group(0)
        if not VER_RE.fullmatch(w) and w not in ("2026", "2025"):
            out.add(w)
    return out


def slug(title, maxwords=7):
    ws = content_words(title)[:maxwords]
    s = "-".join(re.sub(r"[^a-z0-9]+", "", w) for w in ws if re.sub(r"[^a-z0-9]+", "", w))
    return s[:80] or "item"


HIGH_HINTS = re.compile(
    r"\b(cve-|ghsa-|zero-day|actively exploited|exploited in the wild|kev\b|"
    r"end of life|end-of-life|\beol\b|deprecat|removal|removed on|sunset|"
    r"breaking change|auto-enable|auto-enabled|enforcement|deadline|"
    r"must upgrade|withdraw)", re.I)


def extract_items(md, topic_status, flag_reason):
    """Return the topic's headline items from its markdown brief."""
    items = []
    heading = ""
    last = None          # the item a continuation line belongs to
    for raw in md.replace("\r", "").split("\n"):
        h = re.match(r"^#{1,4}\s+(.*)$", raw)
        if h:
            heading = h.group(1).strip().lower()
            last = None
            continue
        if heading in SKIP_HEADINGS:
            continue
        li = re.match(r"^([ \t]*)[-*]\s+(.*)$", raw)
        if not li:
            # Continuation of the previous bullet. The briefs put their
            # "[source](url) · [docs](url)" citations on this line, so the
            # headline's primary link usually lives HERE, not on the bullet.
            if last is not None and raw.strip():
                if not last["url"]:
                    last["url"] = first_url(raw)
            elif not raw.strip():
                last = None
            continue
        indent, body = li.group(1), li.group(2).strip()
        if len(indent.replace("\t", "    ")) >= 4:
            # sub-bullet: detail, not a headline -- but it may carry the link
            if last is not None and not last["url"]:
                last["url"] = first_url(body)
            continue
        title = headline(body)
        if len(title) < 15:
            last = None
            continue
        if re.fullmatch(r"(source|docs|changelog|link)s?[:.]?", title, re.I):
            last = None
            continue
        last = {"title": title, "url": first_url(body), "_heading": heading}
        items.append(last)

    flag_anchors = strong_anchors(flag_reason or "")
    flag_norm = norm_title(flag_reason or "")
    for it in items:
        sev = "normal"
        if HIGH_HINTS.search(it["title"]):
            sev = "high"
        if topic_status == "urgent" and flag_norm:
            shared = strong_anchors(it["title"]) & flag_anchors
            if shared or ratio(it["title"], flag_norm) >= 0.55:
                sev = "urgent"
        it["sev"] = sev

    # de-dup within the topic (same slug twice in one brief)
    seen, out = set(), []
    for it in items:
        k = slug(it["title"])
        if k in seen:
            continue
        seen.add(k)
        it["key"] = k
        it.pop("_heading", None)
        out.append(it)
    return out


# ------------------------------------------------------------------ matching

def ratio(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def partial_ratio(a, b):
    """Best ratio of the shorter string against any window of the longer one.

    Plain SequenceMatcher.ratio() divides by total length, so a title that says
    the same thing plus a trailing clause scores far below a real match. The
    dictionary's stored titles run ~73 chars and today's run ~158, so that
    length asymmetry alone was suppressing genuine merges. This is the standard
    fuzzy "partial ratio" and it is length-robust in exactly that direction.
    """
    a, b = a.lower(), b.lower()
    if len(a) > len(b):
        a, b = b, a
    n = len(a)
    if n < 20 or len(b) - n > 400:
        return SequenceMatcher(None, a, b).ratio()
    best = 0.0
    # step in quarter-windows: enough resolution, bounded cost
    step = max(1, n // 4)
    for i in range(0, len(b) - n + 1, step):
        r = SequenceMatcher(None, a, b[i:i + n]).ratio()
        if r > best:
            best = r
            if best > 0.97:
                break
    return best


def jaccard(a_words, b_words):
    sa, sb = set(a_words), set(b_words)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def load_keys(path):
    if not os.path.exists(path):
        return {"entries": {}}
    try:
        d = json.load(open(path))
        if isinstance(d, dict) and isinstance(d.get("entries"), dict):
            return d
    except Exception:
        pass
    return {"entries": {}}


def match_all(today, today_date, keys):
    """Attach a canonical key to each of today's items. Mutates `today`."""
    entries = keys["entries"]
    alias_index = {}
    for k, e in entries.items():
        alias_index[k] = k
        for a in e.get("aliases", []):
            alias_index.setdefault(a, k)

    cutoff = (datetime.strptime(today_date, "%Y-%m-%d") - timedelta(days=WINDOW_DAYS)).date()

    # candidates bucketed by topic, restricted to the 45-day window
    by_topic = {}
    for k, e in entries.items():
        try:
            ls = datetime.strptime(e.get("last_seen", ""), "%Y-%m-%d").date()
        except Exception:
            continue
        if ls < cutoff:
            continue
        for t in e.get("topics", []):
            by_topic.setdefault(t, []).append(k)

    claimed = set()          # entry keys already taken by an item TODAY
    cache = {}               # cand key -> (title, content_words, anchors)
    stats = {"exact": 0, "fuzzy": 0, "new": 0}
    weakest = []

    for tid, tdata in today["topics"].items():
        for it in tdata["items"]:
            draft = it["key"]
            ek = alias_index.get(draft)
            if ek and ek in entries and ek not in claimed:
                it["_entry"] = ek
                it["_how"] = "exact"
                claimed.add(ek)
                stats["exact"] += 1
                continue

            title = it["title"]
            anc = strong_anchors(title)
            cw = content_words(title)

            # Cheap prune first: token overlap costs a set op, ratio costs O(n*m).
            # Only the handful of candidates that share real vocabulary are worth
            # scoring properly.
            shortlist = []
            for cand in by_topic.get(tid, []):
                if cand in claimed:
                    continue
                ce = cache.get(cand)
                if ce is None:
                    ct = entries[cand].get("title", "")
                    ce = cache[cand] = (ct, content_words(ct), strong_anchors(ct))
                j = jaccard(cw, ce[1])
                if j >= 0.30 or (anc & ce[2]):
                    shortlist.append((j, cand, ce))
            shortlist.sort(key=lambda x: -x[0])

            best, best_r, best_why = None, 0.0, ""
            for j, cand, (ct, _cwc, canc) in shortlist[:8]:
                r = ratio(title, ct)
                pr = partial_ratio(title, ct)
                shared_anchor = bool(anc & canc)
                ok = (r >= 0.90
                      or (r >= 0.62 and (shared_anchor or j >= 0.50))
                      or (pr >= 0.78 and (shared_anchor or j >= 0.45))
                      or (j >= 0.60 and shared_anchor))
                if not ok:
                    continue
                score = max(r, pr * 0.98) + (0.10 if shared_anchor else 0.0)
                if score > best_r:
                    best, best_r, best_why = cand, score, (
                        "r=%.2f p=%.2f%s j=%.2f" % (r, pr, "+anchor" if shared_anchor else "", j))
            if best:
                it["_entry"] = best
                it["_how"] = "fuzzy"
                claimed.add(best)
                stats["fuzzy"] += 1
                weakest.append((best_r, tid, title[:70], entries[best].get("title", "")[:70], best_why))
            else:
                it["_entry"] = None
                it["_how"] = "new"
                stats["new"] += 1

    weakest.sort(key=lambda x: x[0])
    return stats, weakest[:15]


# ------------------------------------------------------------- categorization

def prior_ledger_path(dirpath, today_date):
    dates = []
    for fn in os.listdir(dirpath):
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.json", fn)
        if m and m.group(1) < today_date:
            dates.append(m.group(1))
    if not dates:
        return None, None
    d = max(dates)
    return os.path.join(dirpath, d + ".json"), d


SEV_RANK = {"normal": 0, "high": 1, "urgent": 2}


def build(today, today_date, keys, prior, prior_date, names):
    entries = keys["entries"]
    prior_sev = {}
    if prior:
        for tid, td in prior.get("topics", {}).items():
            for it in td.get("items", []):
                prior_sev[it.get("key")] = it.get("sev", "normal")

    new, changed, ongoing = [], [], []

    for tid, tdata in today["topics"].items():
        disp = names.get(tid, tid)
        for it in tdata["items"]:
            ek = it.get("_entry")
            row = {"topic": disp, "title": it["title"]}
            if it.get("url"):
                row["url"] = it["url"]
            row["_sev"] = it["sev"]

            if ek is None:
                it["first_seen"] = today_date
                it["days_seen"] = 1
                new.append(row)
                continue

            e = entries[ek]
            it["first_seen"] = e.get("first_seen", today_date)
            try:
                gap = (datetime.strptime(today_date, "%Y-%m-%d").date()
                       - datetime.strptime(e["last_seen"], "%Y-%m-%d").date()).days
            except Exception:
                gap = 0
            psev = prior_sev.get(ek)
            if gap > RETURNING_DAYS:
                row["note"] = "returning after %d days" % gap
                new.append(row)
            elif psev and SEV_RANK.get(it["sev"], 0) != SEV_RANK.get(psev, 0):
                row["note"] = "%s → %s" % (psev, it["sev"])
                changed.append(row)
            else:
                # build() runs BEFORE stamp(), so seen_count is still the
                # pre-bump value; today's appearance makes it +1.
                row["days"] = int(e.get("seen_count", 0)) + 1
                ongoing.append(row)

    # aged out: entries whose last_seen is exactly AGED_OUT_DAYS before today
    target = (datetime.strptime(today_date, "%Y-%m-%d")
              - timedelta(days=AGED_OUT_DAYS)).strftime("%Y-%m-%d")
    aged_out = sum(1 for e in entries.values() if e.get("last_seen") == target)

    return {"prev_date": prior_date, "new": new, "changed": changed,
            "ongoing": ongoing, "aged_out": aged_out}


def stamp(today, today_date, keys):
    """Write today's matches back into the dictionary. Tally guard included."""
    entries = keys["entries"]
    bumped = guarded = created = 0
    for tid, tdata in today["topics"].items():
        for it in tdata["items"]:
            ek = it.get("_entry")
            if ek is None:
                nk = it["key"]
                n = 2
                while nk in entries:
                    nk = "%s-%d" % (it["key"], n)
                    n += 1
                entries[nk] = {"title": it["title"], "topics": [tid],
                               "first_seen": today_date, "last_seen": today_date,
                               "seen_count": 1, "aliases": []}
                if it.get("url"):
                    entries[nk]["url"] = it["url"]
                it["key"] = nk
                it["first_seen"] = today_date
                it["days_seen"] = 1
                created += 1
                continue
            e = entries[ek]
            if it["key"] != ek and it["key"] not in e.setdefault("aliases", []):
                e["aliases"].append(it["key"])   # audit trail for every merge
            e["title"] = it["title"]
            if tid not in e.setdefault("topics", []):
                e["topics"].append(tid)
            if it.get("url") and not e.get("url"):
                e["url"] = it["url"]
            # ---- TALLY GUARD ----
            if e.get("last_seen") == today_date:
                guarded += 1
            else:
                e["seen_count"] = int(e.get("seen_count", 0)) + 1
                bumped += 1
            e["last_seen"] = today_date
            it["key"] = ek
            it["first_seen"] = e.get("first_seen", today_date)
            it["days_seen"] = int(e.get("seen_count", 1))
    return {"bumped": bumped, "guarded": guarded, "created": created}


def clean(today):
    for tdata in today["topics"].values():
        for it in tdata["items"]:
            it.pop("_entry", None)
            it.pop("_how", None)
            it.pop("url", None)
    return today


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--ledger-dir", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--sections", required=True,
                    help="JSON file: [{id,name,status,flag_reason}] in dashboard order")
    ap.add_argument("--out", required=True, help="where to write whatsnew.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    secs = json.load(open(a.sections))
    names = {s["id"]: s["name"] for s in secs}

    today = {"date": a.date, "topics": {}}
    for s in secs:
        p = os.path.join(a.briefs, s["id"] + ".md")
        md = open(p).read() if os.path.exists(p) else ""
        items = extract_items(md, s.get("status", "ok"), s.get("flag_reason", ""))
        today["topics"][s["id"]] = {"status": s.get("status", "pending"), "items": items}

    total = sum(len(t["items"]) for t in today["topics"].values())
    print("extracted %d items across %d topics" % (total, len(today["topics"])), file=sys.stderr)

    keys_path = os.path.join(a.ledger_dir, "keys.json")
    keys = load_keys(keys_path)
    print("dictionary: %d entries" % len(keys["entries"]), file=sys.stderr)

    stats, weakest = match_all(today, a.date, keys)
    print("match: exact=%(exact)d fuzzy=%(fuzzy)d new=%(new)d" % stats, file=sys.stderr)
    print("--- 15 weakest accepted fuzzy merges (eyeball these) ---", file=sys.stderr)
    for sc, tid, t, ct, why in weakest:
        print("  [%s %s] %s\n            <- %s" % (tid, why, t, ct), file=sys.stderr)

    prior_path, prior_date = prior_ledger_path(a.ledger_dir, a.date)
    prior = json.load(open(prior_path)) if prior_path else None
    wn = build(today, a.date, keys, prior, prior_date, names)

    st = stamp(today, a.date, keys)
    print("stamp: bumped=%(bumped)d guarded=%(guarded)d created=%(created)d" % st, file=sys.stderr)

    if not a.dry_run:
        keys["generated"] = a.date
        json.dump(keys, open(keys_path, "w"), indent=0, sort_keys=True)
        json.dump(clean(today), open(os.path.join(a.ledger_dir, a.date + ".json"), "w"), indent=0)
    json.dump(wn, open(a.out, "w"), indent=1)
    print("whatsnew: new=%d changed=%d ongoing=%d aged_out=%d (vs %s)"
          % (len(wn["new"]), len(wn["changed"]), len(wn["ongoing"]), wn["aged_out"], wn["prev_date"]),
          file=sys.stderr)


if __name__ == "__main__":
    main()
