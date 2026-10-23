"""Edition 101 ledger surgery: corrections first, then enrichments, then new rows.
Build-order rule (2026-09-14): corrections are applied to the LEDGER before any
section is generated, never to the assembled HTML afterwards."""
import json, sys
sys.path.insert(0, 'tools/lens')

TODAY = "2026-10-23"
L = json.load(open('lens/parent_ledger.json'))
byk = {}
for ln in L:
    if isinstance(L[ln], list):
        for r in L[ln]:
            byk.setdefault(r.get('k'), []).append((ln, r))

def edit(key, **kw):
    hits = byk.get(key)
    if not hits: raise SystemExit("MISSING KEY: %s" % key)
    ln, r = hits[0]
    for f, v in kw.items(): r[f] = v
    return r

C = "<span class='corr'>CORRECTED 10-23</span> "
E = "<span class='corr'>ENRICHED 10-23</span> "

# ============ CORRECTIONS (a wrong field defeats every date-keyed check) ============

# 1. Fabric Runtime 2.0 default: the carried row said "22 days past its own
#    published window with no flip". It HAS flipped, and the Spark version on
#    the board was stale too.
r = edit('fabric-runtime-2-default', date=None)
r['t'] = (C + "<b>Runtime 2.0 IS now the default</b> &mdash; Microsoft's doc (ms.date 2026-10-22, "
  "updated 10-23) states plainly: &ldquo;Runtime 2.0 is the default selection for new workspaces "
  "and environment items.&rdquo; So the three editions of &ldquo;promised late September, no flip, "
  "no day&rdquo; close here &mdash; <b>and the vendor still never published a day</b>, which is why "
  "this row stays undated rather than being backfilled with one. Second correction in the same row: "
  "the board carried Runtime 2.0 as Spark 4.0. It is <b>Apache Spark 4.1 with Delta Lake 4.2</b>, "
  "Python 3.13, Java 21, Scala 2.13, Azure Linux 3.0, end of support 2028-08-31. Delta 4.x features "
  "on it are experimental and Spark-only: enable them and the SQL analytics endpoint and Direct Lake "
  "cannot read the table. ") + r['t']

# 2. Iceberg V4 equality deletes: PR was open, now merged spec text.
r = edit('iceberg-v4-equality-delete-deprecation', date=None)
r['t'] = (C + "<b>The ban is merged spec text now, not a proposal</b> &mdash; PR #17783 "
  "&ldquo;Spec: Forbid writing new equality deletes in v4&rdquo; merged <b>2026-09-29</b>, and "
  "<code>format/spec.md</code> reads &ldquo;Writing new equality deletes is no longer allowed&rdquo; "
  "under Version 4. It is a <b>writer-side</b> ban: readers must still apply existing equality "
  "deletes from v2/v3 tables. <b>V4 still has no date, and this edition can finally say WHY rather "
  "than just reporting the absence:</b> the spec itself states &ldquo;Version 4 is under active "
  "development and has not been formally adopted&rdquo;, and when the baseline AMT vote was called "
  "the release manager wrote that it &ldquo;is <i>not</i> a vote for adoption&rdquo;. Four v4 spec "
  "votes passed inside this window and two more opened 10-22, so the surface is growing and the "
  "adoption date is still absent by design. This board's deliberate undating was right. ") + r['t']

# 3. Doris CVE-2026-72524: carried population was too wide.
r = edit('doris-cve-2026-72524-no-fix-on-2x-3x',
    due="no fix for <b>3.1.x only</b> &mdash; branch ARCHIVED by the vendor, &ldquo;security patches included&rdquo;")
r['t'] = (C + "<b>The affected population is narrower than this board carried, and the vendor's "
  "policy is harsher.</b> NVD's affected set, with <code>defaultStatus: unaffected</code>, is "
  "<b>3.1.0&ndash;3.1.*, 4.0.0&ndash;4.0.7 and 4.1.0&ndash;4.1.3 only</b> &mdash; so 2.0&ndash;2.1.x "
  "and 3.0.x are NOT affected and the carried &ldquo;no fix on 2.x/3.x&rdquo; overstated it. What "
  "replaces it is worse for the population that IS affected: Doris now publishes a maintenance "
  "policy where none existed, listing 4.1 and 4.0 as the only maintained branches and <b>3.1.4 under "
  "&ldquo;Archived Releases&rdquo;, which &ldquo;receive no further releases of any kind, security "
  "patches included&rdquo;</b>. CISA SSVC reads exploitation: none, automatable: no, technicalImpact: "
  "total. No new 4.0.x exists, so no backport is coming. ") + r['t']

# 4. Next.js / sharp: the "patched release that does not patch" framing overstated it.
r = edit('nextjs-oct14-two-95-rces-no-13x-14x-fix',
    due="fixed 15.5.28 / 16.4.1 &middot; <b>sharp 0.34.x has no fix and an existing lockfile is not moved</b>")
r['t'] = (C + "<b>A refinement that matters, measured against the published package metadata.</b> "
  "npm picks the maximum satisfying version across a <code>||</code>, so a <i>fresh</i> install of "
  "<code>next@15.5.28</code> does resolve sharp to 0.35.5 &mdash; &ldquo;a patched release that does "
  "not patch&rdquo; overstated it. The real exposure is narrower and worse: <b>sharp 0.34.x already "
  "satisfies the declared <code>^0.34.3 || ^0.35.5</code> range</b>, so a lockfile pinned there is "
  "not moved by the Next.js bump, is not moved by <code>npm update</code>, and <b>sharp 0.34 has had "
  "no release since 2025-11-06</b>. Run <code>npm ls sharp</code> after upgrading and force "
  "&ge;0.35.5 with an override. Detection also moved: the three Next.js advisories reached OSV and "
  "GitHub's database on <b>2026-10-22</b>, closing an eight-day blind window. ") + r['t']

# 5. Snowsight account host: retired as past, but the vendor moved it out to 2027.
hits = byk.get('snowsight-account-host-oct16')
if hits:
    ln, r = hits[0]
    L['retired_events'] = [x for x in L['retired_events'] if x.get('k') != 'snowsight-account-host-oct16']
    r.pop('retired', None)
    r['date'] = None
    r['t'] = (C + "<b>Un-retired: this did not happen, it moved.</b> The board retired this row as a "
      "passed 2026-10-16 date. BCR-2413 now reads <b>&ldquo;early February 2027 (exact date to be "
      "determined)&rdquo;</b> &mdash; so the day-precise October date is gone from the vendor's page "
      "entirely. Tracking note worth keeping: this date has now moved <b>three times</b> (into bundle "
      "2026_07, out of it on 09-03 into the unbundled table with an October day, and now out to a "
      "month in 2027). The required action is unchanged &mdash; allowlist the "
      "<code>ACCOUNT_PUBLIC</code> host from <code>SYSTEM$ALLOWLIST()</code> alongside the existing "
      "<code>apps-api</code> host &mdash; but there is no day to plan against. ") + r['t']
    L['events'].append(r)

# ============ ENRICHMENTS (same key, today's measurement) ============

r = edit('cve-2026-21962-ohs-weblogic-kev',
    due="KEV due 2026-08-27 (<b>57d PAST DUE</b>) &middot; fix exists since the January 2026 CPU")
r['t'] = (E + "<b>57 days past due, and the October CPU does not mention the id at all</b> &mdash; "
  "re-grepped the full published advisory text today for both <code>CVE-2026-21962</code> and the "
  "bare string <code>21962</code>: <b>zero occurrences in the rendered text and in the raw HTML</b>. "
  "KEV's own notes field points the fix at <code>cpujan2026.html</code>, so a fix has existed for "
  "nine months and this is unpatched by omission rather than unpatchable. "
  "<code>forensicTriage: Yes</code> under BOD 26-04. ") + r['t']

r = edit('apple-coregraphics-86950-exploited',
    due="KEV due 2026-10-13 (<b>10d PAST DUE</b>) &middot; <b>no fix at all for the iOS 18.7 train</b>")
r['t'] = (E + "<b>The stranded population now has names and part numbers.</b> Apple shipped the fix "
  "2026-09-28 in iOS/iPadOS 26.7.1, macOS Tahoe 26.7.1 and macOS Sequoia 15.8.1. The <b>iOS/iPadOS "
  "18.7 train's last update is 18.7.10, dated 2026-08-17 &mdash; six weeks BEFORE the patch</b> "
  "&mdash; and it covers <b>iPhone XS, XS Max, XR and iPad 7th generation, none of which can run "
  "iOS 26</b> (26.7.1 requires iPhone 11 or later). macOS Sonoma is in the same position at 14.8.9. "
  "Apple has published no security content since 09-28 and today's iOS 27.1 shows no CVE entries, so "
  "either the 18.7 train ended with the iOS 27 launch or an 18.7.11 is pending &mdash; in both "
  "readings those devices are unpatched today against an in-the-wild CoreGraphics write. ") + r['t']

r = edit('litellm-59822-mcp-auth-bypass-kev', due="KEV due 2026-09-16 (<b>37d PAST DUE</b>)")
r['t'] = (E + "37 days past due, re-read off the KEV catalog today (version 2026.10.21, 1,754 "
  "entries), unchanged. One precision worth carrying for triage: <code>forensicTriage: <b>No</b></code> "
  "on this entry, unlike the Oracle row &mdash; so it is a patch obligation without the BOD 26-04 "
  "detection work. Three KEV entries now exist for this one gateway package. ") + r['t']

r = edit('litellm-1107-malicious-release-oct21',
    due="<b>NO PATCH UNDOES EXPOSURE</b> &mdash; and the payload survives <code>pip uninstall</code>")
r['t'] = (E + "<b>Two measurements that change the remediation, not just the story.</b> (1) 1.107.0 "
  "is <b>DELETED from PyPI, not yanked</b> &mdash; the JSON API has no <code>1.107.0</code> key among "
  "948 releases, which matters because a yank still resolves for an explicit "
  "<code>litellm==1.107.0</code> pin and a deletion does not. (2) <b>The payload is installed OUTSIDE "
  "the package and survives <code>pip uninstall litellm</code>:</b> the wheels shipped "
  "<code>cook.pth</code>, <code>cook.py</code> and <code>sitecustomize.py</code> under "
  "<code>litellm-1.107.0.data/purelib/</code>, which pip installs at the <b>site-packages root</b>, "
  "and a <code>.pth</code> file executes at <i>every</i> Python interpreter start &mdash; including "
  "<code>pip</code> itself, so a downgrade re-triggers it. Delete the three files and their "
  "<code>__pycache__</code> from a shell, kill the daemon on "
  "<code>/tmp/remote_code_loader.lock</code>, then rebuild the image. The clean per-train releases all "
  "predate the 11:39 UTC window: 1.103.7, 1.104.5, 1.105.3, 1.106.2. Docker <code>latest</code> now "
  "resolves byte-identical to v1.106.2. ") + r['t']

r = edit('emudhra-ca-compromise-go-rebuild-not-restart',
    due="<b>2026-10-27 &mdash; Chrome removes <code>emSign ECC Root CA - G3</code> for all devices</b>")
r['t'] = (E + "<b>This row now has a DATE where it had none, and the hardest part is the one nobody "
  "can patch.</b> Chrome removes <code>emSign ECC Root CA - G3</code> from the Chrome Root Store for "
  "all devices on the morning of <b>2026-10-27</b>, and Google tells operators with certificates "
  "chaining to it to &ldquo;immediately acquire and install&rdquo; a replacement &mdash; eMudhra's own "
  "estimate to Mozilla is ~30,000 certificates. Eight runtimes shipped independent fixes in six days "
  "(Go 1.27.3/1.26.10, Node 26.12.1/24.22.1/22.23.4, uv 0.13.5, Deno 2.9.8, pnpm 11.28.8, certifi "
  "&times;3 with a partial revert, pip 26.2.2, OpenJDK). <b>But as of today Amazon Linux 2023, Amazon "
  "Linux 2, Red Hat and Bottlerocket have no fixed <code>ca-certificates</code> package</b>, so EKS "
  "node images and every container built before the fix carry the old store &mdash; a rebuild job, not "
  "a patch. Two second-order traps measured: <b>Docker Engine 29.9.2 now REJECTS chains containing the "
  "revoked intermediates</b>, so upgrading can break <code>docker pull</code> against your own "
  "registry; and <b>CPython 3.9/3.10 bundle a pip whose vendored bundle still trusts the root, and "
  "3.10 went EOL 2026-10-01</b> &mdash; nineteen days before the pip fix, so no fixed 3.10 will ever "
  "ship. Oracle shipped an out-of-band Security Alert for the same incident on 10-21 "
  "(<b>CVE-2026-91403</b>, CVSS 9.1, Java SE/GraalVM JSSE). ") + r['t']

r = edit('pgvector-103484-ivfflat-oob-no-managed-fix',
    due="<b>zero of seven managed providers ship 0.8.7</b> &mdash; 22 days after GA")
r['t'] = (E + "<b>Measured against every provider's own extension-version doc today, with versions "
  "rather than an assertion:</b> RDS <b>0.8.2</b>, Aurora <b>0.8.2</b>, Cloud SQL <b>0.8.5</b>, "
  "AlloyDB <b>0.8.2.google-1</b>, Azure flexible server <b>0.8.2</b>, Neon <b>0.8.0</b> (0.8.6 on "
  "PG18), Supabase <b>0.8.2</b>. Anything at 0.8.2 or below is also behind the separate 32-bit IVFFlat "
  "overflow fixed in 0.8.6. The gating privilege is only &ldquo;a user who can create an IVFFlat "
  "index&rdquo;, i.e. any app role with <code>CREATE</code> on a schema &mdash; so the compensating "
  "control is revoking <code>CREATE</code> from application roles, or moving those indexes to HNSW, "
  "which is not implicated. Same lane, same shape: <b>Azure's built-in PgBouncer is 1.25.2</b> against "
  "the CVE-2026-107350 authentication bypass fixed in 1.26.1, and Microsoft's own doc says "
  "&ldquo;Azure manages updates of PgBouncer&rdquo; &mdash; there is no customer-side patch. ") + r['t']

r = edit('starrocks-cve-trio-4014',
    due="merged on <code>branch-3.5</code>, <b>UNRELEASED 56 days</b> &middot; reachable only via 4.0.16 / 4.1.6")
r['t'] = (E + "<b>The fixes are now provably on the branch and provably in no release, with dates.</b> "
  "Read from the FE pom today: tag <code>3.5.21</code> carries ranger-plugins-common <b>2.8.0</b>, "
  "httpclient5 <b>5.4.3</b> and bouncycastle <b>1.84</b>; <code>branch-3.5</code> HEAD carries "
  "<b>2.9.0 / 5.6.4 / 1.86</b>, backported on 2026-09-19, 09-23 and 10-08. That is <b>34 days of a "
  "CVSS 9.8 fix sitting on a branch with no tag cut from it</b>, and 56 days since 3.5.21. One "
  "constraint on the escape hatch: after upgrading to 4.1 you can only downgrade to <b>4.0.6 or "
  "later</b>, so 4.0.16 is the shorter jump and carries the same three fixes. &ldquo;3.5 LTS&rdquo; "
  "remains undocumented by the project for a fourth consecutive run. ") + r['t']

r = edit('mongodb-82-no-fixed-version',
    due="<b>8.2.13 named in JIRA, never published</b> &middot; 8.2 terminal at 8.2.12 and EOL 2026-07-31")
r['t'] = (E + "<b>The stranded population is MongoDB 8.2, and the evidence is the vendor's own "
  "tracker.</b> <code>SERVER-131229</code> lists Fix Version/s <b>8.2.13</b>, 8.3.9, 7.0.41, 8.0.30 "
  "and 9.0.0-rc2 &mdash; and the download manifest's newest 8.2 is <b>8.2.12, dated 2026-06-26</b>, "
  "four months old and three months before the disclosure. CVE-2026-82067 (CVSS 4.0 <b>9.2 "
  "Critical</b>) can leave the <b>authorization subsystem silently disabled at startup</b>, giving "
  "unauthenticated network callers arbitrary administrative operations &mdash; and 8.2 has also missed "
  "~23 other server CVEs. <b>Correction to this board's carried reading:</b> Percona Server for "
  "MongoDB is NOT the stranded population &mdash; PSMDB crossed the fix at 7.0.43-23 and 8.0.32-14 in "
  "September and is now at 7.0.45-24 / 8.0.34-15. Note Percona's notes never name the CVE, so grepping "
  "them for the id finds nothing; compare version numbers instead. ") + r['t']

r = edit('k8s-134-eol', date="2026-10-27")
r['t'] = (E + "<b>Kubernetes has shipped no patch release in 30 days, and 1.34 will reach EOL in four "
  "days without its final patch.</b> <code>stable-1.34.txt</code> still returns v1.34.12, tagged "
  "2026-09-23; v1.34.13 had a 10-09 cherry-pick deadline and a 10-13 target. The October batch was "
  "<b>postponed a week to 2026-10-20 specifically to pick up Go's CVE fixes</b> and is now three days "
  "past that revised date with no announced slip. Measured per branch rather than in aggregate, which "
  "corrects this board's earlier reading: v1.32.13 is built on <b>go1.24.13</b>, v1.33.13 on "
  "<b>go1.25.11</b>, v1.34.12 on <b>go1.26.5</b> (22 open stdlib advisories) and v1.35.9 / v1.36.5 / "
  "v1.37.1 on <b>go1.26.8</b> (14). Go 1.24 and 1.25 are out of support, so 1.32 and 1.33 cannot be "
  "rebuilt on a fixed toolchain of their own series at all. Every other Go project in the lane shipped "
  "1.26.10 within 72 hours. ") + r['t']

r = edit('argocd-four-99-criticals-no-v2-fix')
r['t'] = (E + "<b>The fixed versions were right on this board and the dates explain a trap worth "
  "recording:</b> the four advisories published 2026-10-07 with fixes in <b>3.3.15 / 3.4.10 / 3.5.4 / "
  "3.6.0-rc2</b>, but their CVE ids were only assigned 10-13 and 10-20 &mdash; a week or more later "
  "&mdash; which is how they get misattributed to the 3.5.6/3.4.12/3.3.17 releases of 10-20/21, which "
  "are Go 1.26.10 and dompurify bumps naming no CVE. For 2.x the affected range is &ldquo;2.1.0 and "
  "later, with no patch available&rdquo;; the only mitigations are dropping <code>--enable-helm</code> "
  "from <code>kustomize.buildOptions</code> (which breaks Kustomize-rendered Helm charts) and blocking "
  "<code>POST /api/v1/applications/manifestsWithFiles</code> &mdash; and the latter closes only the "
  "upload path, so a kustomization committed to Git stays exploitable. ") + r['t']

r = edit('bq-tabfm-token-pricing-oct30', date="2026-10-30")
r['t'] = (E + "<b>Confirmed on two Google pages today, and the sharp part is that no quota can cap "
  "it.</b> The token quotas that GA'd 2026-10-14 are scoped to Gemini-backed <i>generative</i> "
  "functions; <code>TabFM</code>, <code>TimesFM</code>, <code>AI.PREDICT</code> and "
  "<code>AI.FORECAST</code> return <b>zero hits</b> in the cost-control doc and sit under a separate "
  "&ldquo;Predictive AI functions&rdquo; heading. <code>maximum_bytes_billed</code> caps bytes, not "
  "tokens; a slot reservation covers only the non-inference half. <b>A TabFM token is a table cell</b>, "
  "so the bill scales with rows &times; columns &times; ensembles &mdash; at the documented maximum "
  "shape that is <b>~$27 per 10M-row run at n_ensembles=1 and ~$218 at 8</b>, against zero marginal "
  "cost today for a reservation customer. <code>n_ensembles</code> is service-controlled and "
  "<code>AI.PREDICT</code> exposes no parameter for it, so you cannot compute your own charge exactly. "
  "The only backstop is a Cloud Billing budget. ") + r['t']

json.dump(L, open('lens/ledger_101.json','w'), indent=1)
print("corrections+enrichments applied; sizes:", {k:len(v) for k,v in L.items() if isinstance(v,list)})
