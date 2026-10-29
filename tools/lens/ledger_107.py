#!/usr/bin/env python3
"""Edition 107 ledger pass: corrections FIRST, then new rows, then countdowns.

Build order matters (09-14 rule): a correction applied to the rendered HTML
after section generation leaves the generated table still showing the old
value. Everything here mutates the ledger dict only.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_surgery as LS
import countdowns as CD

TODAY = "2026-10-29"
SP = os.path.dirname(os.path.abspath(__file__))
led = json.load(open(os.path.join(SP, "parent_ledger.json")))

def row(sec, key):
    for r in led.get(sec, []):
        if r.get("k") == key:
            return r
    raise SystemExit("row not found: %s/%s" % (sec, key))

applied = []

# ---------------------------------------------------------------- correction 1
# The board asserted the Brotli fix was "unreachable on every live Envoy
# branch". Today's DevOps lane read the primary bulletins: Istio named fixed
# versions on 2026-10-15, twelve days BEFORE the KEV listing, and Envoy
# declared five branches patched on 10-23. The *pin* observation survives and
# is the interesting part -- Envoy still pins a pre-fix 2026-09-30 Brotli
# snapshot because the root cause is CWE-252 (unchecked return value), so
# Envoy fixed its own CALL SITE rather than bumping the library. That is why
# v1.40.0 could ship on 10-13, eight days before upstream brotli 1.2.1 existed.
r = row("patch", "brotli-111497-kev-runtime-wide-scanner-blind")
r["due"] = ("KEV due <b>2026-11-10</b> (12 days) &middot; "
            "<b>fixed upstream 1.0.10 / 1.1.1 / 1.2.1</b> &middot; "
            "<b>NO patched Arrow/PyArrow release exists</b>")
r["t"] = (r["t"].rstrip()
    + " <b>CORRECTED 10-29:</b> the board read &ldquo;unreachable on every live Envoy "
      "branch&rdquo;. Wrong, and the primary bulletins say so. Istio published fixed "
      "versions on <b>2026-10-15</b> (1.31.2 / 1.30.6 / 1.29.9) &mdash; twelve days "
      "BEFORE the KEV listing &mdash; and Envoy declared 1.40.0 / 1.39.3 / 1.38.6 / "
      "1.37.8 / 1.36.12 patched. The <i>pin</i> observation stands and is the real "
      "finding: Envoy <code>MODULE.bazel</code> at v1.40.2 and at <code>main</code> "
      "still pins <code>brotli 1.2.0-260930-42a2ed4.envoy</code>, a pre-fix snapshot, "
      "because the root cause is CWE-252 (unchecked return value) &mdash; so Envoy "
      "fixed its own CALL SITE instead of bumping the library. That is how v1.40.0 "
      "shipped 10-13, eight days before upstream brotli 1.2.1 existed. "
      "<b>NEW unpatched population, 10-29:</b> <b>Apache Arrow C++ and PyArrow "
      "26.0.0 bundle Brotli v1.0.9</b>, inside the affected 1.0.3&ndash;1.2.0 range. "
      "The bump to 1.2.1 landed on Arrow <code>main</code> TODAY (GH-55165) and on "
      "<b>no release branch</b>; there is no <code>maint-26.0.1</code> in flight and "
      "27.0.0 is ~January, so a BROTLI-compressed Parquet file feeds attacker bytes "
      "to the vulnerable decoder with no patched release to move to. A build that "
      "dynamically links a system Brotli &ge;1.0.10 is fine; wheel/vcpkg/bundled "
      "builds are not. <b>Five scorings now, and the spread is attack complexity:</b> "
      "NVD 9.8 at <code>AC:L</code> against Microsoft 8.1 at <code>AC:H</code>, with "
      "Google CNA and GitHub at 9.2 on CVSS 4.0 &mdash; and MSRC's temporal vector "
      "still read <code>E:U</code> (Exploit Unproven) on a document revised two days "
      "AFTER CISA listed it as actively exploited.")
applied.append("brotli-111497: Envoy/Istio reachability CORRECTED + Arrow/PyArrow 26.0.0 bundled-1.0.9 ENRICHED + five-score spread")

# ---------------------------------------------------------------- correction 2
# Day count, plus a precision fix the Oracle lane caught in my own prompt line:
# the corroborating OHS/WebLogic shape is three CVEs across TWO product
# entries, not one component patched three times.
r = row("patch", "cve-2026-21962-ohs-weblogic-kev")
r["due"] = ("KEV due 2026-08-27 (<b>63d PAST DUE</b>) &middot; "
            "fix exists since the January 2026 CPU")
r["t"] = (r["t"].rstrip()
    + " <b>RE-MEASURED 10-29:</b> 63 days past due, and the id returns <b>zero hits</b> "
      "in both <code>cpuoct2026.html</code> and the full verbose risk matrix &mdash; "
      "sixth consecutive edition with that result, so a fix has existed since January "
      "and this is unpatched by omission. <b>Precision correction to the corroborating "
      "shape:</b> the same CPU patched the OHS / WebLogic Proxy Plug-in surface with "
      "three CVEs (CVE-2026-87346, -83379, -87300, all 8.7 unauthenticated with scope "
      "change, byte-identical vectors) spread across <b>TWO product entries</b> &mdash; "
      "Oracle HTTP Server, and WebLogic Server Proxy Plug-in &mdash; not one component "
      "patched three times, as the board's wording implied.")
applied.append("cve-2026-21962: 62d -> 63d + OHS shape is 3 CVEs across 2 product entries, not 1 component x3")

# ------------------------------------------------------------------- new rows
NEW_EVENTS = [
  dict(k="linux-kernel-46300-kev-due-oct31", date="2026-10-31",
       t="<b>CISA KEV remediation due date for CVE-2026-46300</b> (Linux kernel, CVSS 7.8 local, "
         "<code>forensicTriage: Yes</code>), added to KEV 2026-10-28. "
         "<code>skb_try_coalesce()</code> loses the <code>SKBFL_SHARED_FRAG</code> marker, so ESP "
         "input decrypts shared fragments in place over page-cache-backed data. <b>The reason it "
         "matters beyond its score:</b> CISA states outright that it is chained with "
         "CVE-2026-109618 and CVE-2026-109619 to implant PHP webshells and <b>run commands as "
         "root</b> &mdash; so patching the PHP pair whose KEV date is TODAY does not close the "
         "chain. Fix is reachable and old: NVD first published 2026-05-23 and every current stable "
         "and longterm kernel carries it (7.2.13, 6.18.59, 6.12.114, 6.6.160, 6.1.190). "
         "Patch-and-reboot, not a no-fix situation.",
       act="Patch kernels to a current stable/longterm and reboot; do not treat the PHP patch as sufficient."),
  dict(k="dbr-18-2-eos-nov5", date="2026-11-05",
       t="<b>Databricks Runtime 18.2 reaches end of support</b> &mdash; the only runtime with an EoS "
         "date between September and December 2026. At EoS Databricks stops backporting fixes AND "
         "<b>the version can no longer be selected when you create or update a compute resource</b>; "
         "existing workloads keep running unsupported, and the policy reserves the right to remove a "
         "version &ldquo;at any time after support ends, without notice&rdquo;, at which point those "
         "workloads fail. Asymmetry the policy page glosses: it describes EoS as three years after GA, "
         "which is the <b>LTS</b> rule &mdash; 18.2 is a Standard release and got six months "
         "(May 5 &rarr; Nov 5). Move pinned jobs to 18 LTS (Spark 4.1.0, EoS 2029-06-10) or 19.",
       act="Re-pin jobs off DBR 18.2 to 18 LTS or 19 before the 5th; after it you cannot select 18.2 for new or updated compute."),
  dict(k="snowflake-mfa-phase3-window-closes-oct31", date="2026-10-31",
       t="<b>Snowflake MFA Phase 3 &mdash; &ldquo;Strong authentication for ALL users&rdquo; &mdash; "
         "documented rollout window (&ldquo;Aug. 2026 - Oct. 2026&rdquo;) closes.</b> It blocks "
         "password authentication for every NON-HUMAN user and fully deprecates "
         "<code>TYPE=LEGACY_SERVICE</code>, migrating existing LEGACY_SERVICE objects to "
         "<code>TYPE=SERVICE</code>, which cannot authenticate with a password. Enforcement is "
         "per-account on a rolling basis with a notification carrying your date, and the rollout page "
         "lists <b>no dates after October 2026</b> &mdash; so there is no documented runway past the "
         "31st. Excluded: SSO users, reader accounts, trial accounts, Snowflake Postgres.",
       act="Run SHOW USERS; move anything still LEGACY_SERVICE, or any service identity holding a password, to key-pair or OAuth."),
  dict(k="openai-evals-readonly-oct31-shutdown-nov30", date="2026-10-31",
       t="<b>OpenAI's Evals platform makes existing evals read-only</b>, with the dashboard and API "
         "shutting down 2026-11-30 and the documented migration path pointing at <b>third-party "
         "Promptfoo</b>. Two distinct actions on two dates: get anything you still need to AUTHOR out "
         "before the 31st, and get the DATA out before 11-30. Shutting down alongside it on 11-30: the "
         "<code>v1/prompts</code> API and reusable prompt objects (migration is &ldquo;move reusable "
         "prompt content into your application code&rdquo;) and Agent Builder (migrate to the Agents "
         "SDK or ChatGPT Workspace Agents; ChatKit survives).",
       act="Export evals, graders and run history now; stand up the replacement harness before 11-30."),
]

# reuse_key advisory: make a duplicate VISIBLE before it ships. Advisory only --
# it never silently reuses or silently ignores (09-11 correction).
print("=== reuse_key advisory: same-date parents for each drafted event ===")
for nr in NEW_EVENTS:
    peers = [r for r in led["events"] if r.get("date") == nr["date"]]
    print("  %s  (%s)  -> %d same-date parent row(s)" % (nr["k"], nr["date"], len(peers)))
    for p in peers:
        print("       [%s] %s" % (p["k"], re.sub(r"<[^>]+>", "", str(p.get("t", "")))[:88]))

existing = {r["k"] for r in led["events"]}
added = 0
for nr in NEW_EVENTS:
    if nr["k"] in existing:
        print("  SKIP (key already present): %s" % nr["k"]); continue
    nr.update(first_seen=TODAY, last_seen=TODAY, days=1)
    led["events"].append(nr); added += 1

# ---------------------------------------------------------------- countdowns
ev_before = len(led["events"])
CD.refresh_rows(led["events"], TODAY, datefield="date")
CD.refresh_rows(led["patch"], TODAY, datefield="due")
assert len(led["events"]) == ev_before, "countdown refresh must not add or drop rows"

json.dump(led, open(os.path.join(SP, "ledger_107.json"), "w"), ensure_ascii=False)
print("\n=== corrections applied ===")
for a in applied: print("  -", a)
print("new event rows added: %d" % added)
print("sizes: events=%d patch=%d claims=%d ownclaims=%d promises=%d benchmarks=%d gaps=%d retired=%d"
      % (len(led["events"]), len(led["patch"]), len(led["claims"]), len(led["ownclaims"]),
         len(led["promises"]), len(led["benchmarks"]), len(led["gaps"]), len(led["retired_events"])))
