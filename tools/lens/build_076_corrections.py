#!/usr/bin/env python3
"""Edition 076 — stage 1: ledger corrections, new rows, and the reuse_key advisory.

Corrections run BEFORE any section is generated (the 2026-09-14 build-order rule):
a wrong date or a wrong alias defeats every date-keyed check downstream.
"""
import json, os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(SP), "tools", "lens"))
import lens_links as LL
import ledger_surgery as LS

TODAY = "2026-09-27"
led = json.load(open(os.path.join(SP, "parent_ledger.json")))

BRIEFS = os.path.join(os.path.dirname(SP), "tools", "ledger", "briefs")
corpus = LL.mine_briefs(BRIEFS)
print("mined %d (topic,title,url) link triples from 19 briefs" % len(corpus))

def by_key(route, k):
    for r in led[route]:
        if r["k"] == k:
            return r
    raise SystemExit("key not found: %s/%s" % (route, k))

# ----------------------------------------------------------- corrections
corr = []

# 1. The KEV clock advanced. Oracle's own lane re-verified the whole record today:
#    it is Fusion Middleware (OHS / WLS Proxy Plug-in), the fix has existed since
#    the JANUARY 2026 CPU, and no CSPU carries it because CSPUs ship no FMW
#    web-tier content. The board already said OHS/WebLogic (corrected ed. 073) --
#    only the day count was stale.
r = by_key("patch", "cve-2026-21962-ohs-weblogic-kev")
assert "30d PAST DUE" in r["due"], r["due"]
r["due"] = "2026-08-27 (31d PAST DUE)"
r["t"] = re.sub(r"\b30 days\b", "31 days", r["t"])
if "January 2026 CPU" not in r["t"]:
    r["t"] += (" <b>Re-verified ed. 076:</b> the fix has shipped since the "
               "<b>January 2026 CPU</b> (Rev 1, 20 Jan); the August and September "
               "CSPUs correctly contain zero hits for 21962, because CSPUs carry no "
               "Fusion Middleware web-tier content at all. Anyone waiting for a CSPU "
               "to fix this is waiting for the wrong patch.")
corr.append("cve-2026-21962: 30d -> 31d past due; recorded that the Jan-2026 CPU is the fix and no CSPU will ever carry it")

# 2. parquet-java CVE-2026-73334 -- the board already records it RESOLVED in
#    1.18.1. Today's Open Formats lane measured something sharper and new: NVD's
#    CPE range is wrong at BOTH ends, so the machine-readable field and the
#    human-readable field lead to opposite conclusions.
r = by_key("patch", "parquet-cve-2026-73334-no-fix")
if "wrong at both ends" not in r["t"]:
    r["t"] += (" <b>New ed. 076 — the advisory record itself is the defect.</b> NVD's "
               "CPE range is <code>1.12.2 &le; v &lt; 1.18.0</code>, which is wrong at "
               "<i>both</i> ends against the ASF advisory: it starts at 1.12.2 where ASF "
               "says 1.12, and it <b>excludes 1.18.0, which ASF lists as affected</b>. So a "
               "scanner keyed on NVD's CPE passes a 1.18.0 deployment the project considers "
               "vulnerable, while a human reading the same NVD page (still saying the fix is "
               "&ldquo;presumably 1.19&rdquo;) concludes no fix exists. Truth: 1.18.1, GA 2026-09-04.")
corr.append("parquet-cve-2026-73334: recorded that NVD's CPE range is wrong at both ends and contradicts its own description")

# 3. Iceberg V4 equality deletes -- the wording vote's 72h window closed 09-26
#    with NO [RESULT] mail and the spec PR is still OPEN. Precision matters: the
#    merged language is "prohibited in v4", not "deprecated". Still no V4 date.
r = by_key("events", "iceberg-v4-equality-delete-deprecation")
if "still OPEN" not in r["t"]:
    r["t"] += (" <b>Update (ed. 076):</b> spec PR <b>#17783 is still OPEN</b> (last touched "
               "2026-09-25), and the wording-only <code>[VOTE][SPEC]</code> opened 09-23 with a "
               "72-hour window <b>expired 09-26 with no <code>[RESULT]</code> mail and no merge</b> "
               "— 3 binding +1 and one committer openly questioning whether a second vote was "
               "needed. The direction vote (7 binding / 17 non-binding, no dissent) passed "
               "2026-08-18; that is the only vote that has a result. Two precision points: the "
               "language is <b>&ldquo;prohibited in v4&rdquo;, not &ldquo;deprecated&rdquo;</b>, and a "
               "full scan of the September dev list found <b>zero</b> V4 release-date discussion. "
               "Row stays deliberately undated.")
corr.append("iceberg-v4-equality-delete: spec PR still OPEN, wording vote expired with no RESULT, language is 'prohibited' not 'deprecated', still no V4 date")

# 4. MongoDB CVE-2026-82067 -- the Percona half of this thread RESOLVED.
r = by_key("patch", "mongodb-cve-82067-auth-disabled")
if "7.0.43-23" not in r["t"]:
    r["t"] += (" <b>RESOLVED for Percona (ed. 076):</b> Percona Server for MongoDB "
               "<b>7.0.43-23 (22 Sep)</b> and <b>8.0.32-14 (23 Sep)</b> both carry this fix "
               "(SERVER-131229) plus 9 High upstream CVEs — Percona's lag to upstream is now "
               "<b>9&ndash;12 days, not months</b>, so the &ldquo;packaged distro is months "
               "behind&rdquo; shape does not apply here. What remains unpatched is "
               "<b>MongoDB 8.2 itself</b>: EOL 2026-07-31, and it stopped receiving patches in "
               "May when 8.3 shipped — ~2.5 months before its published EOL date. Its absence "
               "from every affected-versions list since 11 Aug reads as &ldquo;unaffected&rdquo; "
               "to a scanner and means &ldquo;unpatched&rdquo;.")
corr.append("mongodb-cve-82067: Percona shipped the fix (7.0.43-23 / 8.0.32-14); 8.2 remains the unpatched population")

# 5. Doris -- the 4.1.x fix was recorded as WITHDRAWN; today's lane found what
#    actually happened, which is more useful than "withdrawn".
r = by_key("patch", "doris-cve-2026-72524-no-fix-on-2x-3x")
if "4.1.4.1" not in r["t"]:
    r["t"] += (" <b>Clarified ed. 076:</b> the 4.1.x fix is not withdrawn — <b>4.1.4 GA'd "
               "2026-09-14 and was superseded on 2026-09-26 by hotfix 4.1.4.1</b>, still in "
               "PMC vote, described as &ldquo;highly recommended to replace 4.1.4&rdquo; (BE crash "
               "on <code>CASE WHEN</code>+<code>OR</code> over nullable Booleans; partitioned "
               "MTMVs doing a FULL refresh on partition add; VARIANT WAL reads; an aarch64 BE "
               "startup crash on 64 KiB-page kernels). So the CVE remediation target is itself "
               "superseded by an RC — sequence the upgrade so you do not do it twice. A fourth "
               "CVE joined the set: <b>CVE-2026-96443</b>, RCE on the FE via an unvalidated JDBC "
               "driver URL, affecting 2.0.5 through 4.1.3.")
corr.append("doris: 4.1.x fix is not withdrawn -- 4.1.4 superseded by hotfix 4.1.4.1 (in vote); added CVE-2026-96443 FE RCE")

print("\n=== %d corrections applied to the ledger BEFORE section generation ===" % len(corr))
for c in corr:
    print("  *", c)

# ------------------------------------------------- new rows + advisory
def url_for(title, topic=None):
    return LL.find_url(title, corpus, topic) if topic else LL.find_url(title, corpus)

NEW_PATCH = [
  dict(k="tomcat-11026-regression-of-its-own-patch",
       due="2026-09-15",
       t=("<b>Tomcat 11.0.26 fixes 12 CVEs and one of them was introduced by the PREVIOUS "
          "security patch.</b> <code>CVE-2026-86350</code> (Important) is a regression in the "
          "<code>CVE-2026-41293</code> fix that mixes up request headers, and it affects "
          "<b>only 11.0.22&ndash;11.0.25</b> — i.e. exactly the versions you moved to last "
          "cycle. Also Important: CVE-2026-76183 (WebSocket security-constraint bypass), "
          "CVE-2026-78383 (AJP DoS on a missing request body), CVE-2026-77791 (busy-wait DoS "
          "on WebSocket close). <b>8.5.x and 7.0.x are <code>last_affected</code> with no fixed "
          "version</b> — migration, not patch. <b>And your scanner cannot see any of this:</b> "
          "zero of the 12 CVEs announced 15 Sep are in OSV twelve days later (measured today; "
          "only 3 of the 11 from the 25 Aug batch made it). Counter-story: patching promptly is "
          "what exposed you here, which is why &ldquo;applied the fix&rdquo; is a checkpoint, "
          "not a closure."),
       topic="appdev"),
  dict(k="clickhouse-269-breaking-upgrade-oct",
       due="on upgrade",
       t=("<b>ClickHouse 26.9 (2026-09-21) is the most disruptive ClickHouse upgrade in years, "
          "and three of its removals stop a server or a table rather than a query.</b> A server "
          "configured with <code>webassembly_udf_engine = 'wasmedge'</code> <b>will not "
          "start</b>; a table with <code>runningConcurrency</code> in its sorting/partition key "
          "<b>will not load</b>; and an access entity still granted "
          "<code>SYSTEM RELOAD MODEL</code> <b>cannot be parsed</b> — so you must REVOKE it from "
          "every user and role <i>before</i> upgrading. <code>enable_analyzer=0</code> is now "
          "<b>rejected</b> and <code>compatibility</code> no longer reverts it (upstream advice "
          "for plan comparison is literally &ldquo;use a ClickHouse older than 26.9&rdquo;). "
          "Default compression flips <b>LZ4 &rarr; ZSTD(3)</b>, size-aware on MergeTree, with no "
          "runtime rollback on some streams. 26.8 is the LTS line and is being actively "
          "patched (26.8.10&ndash;.13 all landed 09-21&rarr;09-27)."),
       topic="challengers"),
  dict(k="iceberg-rust-encryption-unreadable-in-java",
       due="no fix — RC failed",
       t=("<b>Write-once/read-anywhere just failed at the encryption layer, and a human caught "
          "it, not CI.</b> iceberg-rust 0.11.0 <b>RC2 was voted DOWN on 2026-09-16</b> because "
          "files it encrypted <b>cannot be read by Java</b> — the author of the encryption work "
          "self-reported a <b>-1</b> a day into the vote ("
          "&ldquo;I didn't implement the tamperproofing checks &hellip; which makes the files "
          "unreadable in Java&rdquo;) and the release manager failed the vote rather than ship. "
          "There is still no RC3 and no <code>[RESULT]</code>, so iceberg-rust's released line "
          "remains <b>0.10.1 (1 Aug)</b>. Root cause is a spec gap Iceberg is only now closing: "
          "the key-metadata binary format and two-tier KEK hierarchy were "
          "&ldquo;implementation-specific&rdquo; in name and Java-defined in fact, and the "
          "spec-vote thread says so outright — &ldquo;any other implementation has to "
          "reverse-engineer them from the Java source&rdquo;. Iceberg 1.12.0's last functional "
          "blocker was also encryption (#17984, committing manifest-list keys with the snapshot "
          "that uses them). Every earlier interop battle was about understanding the bytes; this "
          "one is about not being able to decrypt them."),
       topic="formats"),
]

print("\n=== reuse_key advisory: probing %d drafted patch rows against the board ===" % len(NEW_PATCH))
added = 0
for row in NEW_PATCH:
    topic = row.pop("topic")
    row["url"] = url_for(row["t"], topic) or url_for(row["t"])
    # reuse_key returns the DRAFTED key when nothing is declared via same_as --
    # it is advisory-only by design (see its docstring). A caller testing mere
    # truthiness therefore treats every row as a duplicate and adds nothing,
    # which is the 09-11 "inert" bug one layer up. Compare against the draft.
    hit = LS.reuse_key(row, led["patch"], "due", "patch")
    if hit != row["k"]:
        print("  DUPLICATE -> reusing %s (no fresh slug minted)" % hit)
    else:
        led["patch"].append(row)
        added += 1
        print("  new: %-44s url=%s" % (row["k"], (row["url"] or "(archive fallback)")[:56]))
print("added %d patch rows; patch 145 -> %d" % (added, len(led["patch"])))

led["date"] = TODAY
led["edition"] = 76
json.dump(led, open(os.path.join(SP, "ledger_076.json"), "w"), indent=1)
json.dump(corr, open(os.path.join(SP, "corrections_076.json"), "w"), indent=1)
print("\nwrote ledger_076.json  (events=%d patch=%d claims=%d ownclaims=%d promises=%d gaps=%d bench=%d)"
      % (len(led["events"]), len(led["patch"]), len(led["claims"]), len(led["ownclaims"]),
         len(led["promises"]), len(led["gaps"]), len(led["benchmarks"])))
