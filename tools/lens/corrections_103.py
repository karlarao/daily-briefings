#!/usr/bin/env python3
"""Edition-103 ledger surgery. Corrections FIRST (09-14 build-order rule), then
enrichments, then new rows. Every key was probed against the board before being
touched, so a row that was already right is not "corrected" again (10-08 rule).

Worth recording: five rows today's briefs appeared to correct were ALREADY right
on the board (doris affected-set, percona-psmdb RESOLVED, iceberg #17783 merged,
mcp-ts 1.31.0, BCR-2413 Feb 2027). Those were corrections to the PROMPT this run
wrote from carried notes, not to the ledger. Probing first is what separated them.
"""
import json, sys
sys.path.insert(0, 'tools/lens')

L = json.load(open('lens/ledger_103.json'))
idx = {}
for ln in L:
    if isinstance(L[ln], list):
        for r in L[ln]:
            idx.setdefault(r.get('k'), []).append((ln, r))

applied, skipped = [], []

def edit(key, *, due=None, prepend=None, note=''):
    hits = idx.get(key)
    if not hits:
        skipped.append(key + '(absent)'); return None
    ln, r = hits[0]
    if due is not None: r['due'] = due
    if prepend: r['t'] = prepend + (r.get('t') or '')
    applied.append(key + ('/' + note if note else ''))
    return r

C = "<span class='corr'>CORRECTED 10-25</span> "
E = "<span class='corr'>ENRICHED 10-25</span> "

# ============================ CORRECTIONS ============================

# 1. The eMudhra row conflated TWO CVEs in TWO TLS stacks as one disputed score.
edit('ca-distrust-go-node-emudhra-oct19-21',
  due="Go 1.27.3 / 1.26.10 &middot; <b>rebuild required</b> &middot; NVD carries <b>no CVSS at all</b>",
  prepend=(C + "<b>The &ldquo;vendor disagreement&rdquo; this row recorded was two different CVEs in two "
   "different TLS stacks, not one CVE scored differently &mdash; today's Oracle lane settled it.</b> "
   "<b>CVE-2026-111943</b> is the <b>Go <code>crypto/x509</code></b> record (GO-2026-6809, aliased to "
   "RUSTSEC-2026-0381/0382/0383), which Red Hat scores <b>6.8</b> at "
   "<code>AV:N/AC:H/PR:N/UI:R</code> and rates <b>Important</b> &mdash; not Medium &mdash; while <b>NVD "
   "carries no CVSS at all</b> (&ldquo;Awaiting Analysis&rdquo;, zero metrics). Oracle's records are "
   "<b>CVE-2026-91403</b> and <b>CVE-2026-114820</b> against <b>JSSE</b>, both <b>9.1</b> with "
   "<code>AC:L</code> and <code>UI:N</code>. The gap is entirely in the vector &mdash; Go's requires high "
   "attack complexity and user interaction, Oracle's requires neither &mdash; and Oracle's <i>published</i> "
   "score is 9.1, revised up from the 8.1 preliminary this board carried. "
   "<b>Three lanes independently tried to reconcile a &ldquo;seven-point disagreement&rdquo; that does not "
   "exist.</b> The mechanism is now also known: the eight intermediates are <b>P-384 keys whose private "
   "scalars are all below 256</b>, trivially recoverable from the certificates, all from a single "
   "<b>2025-04-30 key ceremony</b>. And <b>no CT log entries exist for them</b>, so CT-enforcing browsers "
   "were never exposed &mdash; this is disproportionately a <b>backend</b> problem. "),
  note='two-cves-not-one')

# 2. Vitess: the key says "sextet"; the real October count is 17, 16 invisible to OSV.
edit('vitess-sqli-sextet-no-fix',
  due="fixed 23.0.8 / 24.0.5 &middot; <b>16 of 17 advisories are absent from OSV</b>",
  prepend=(C + "<b>The October count is 17 advisories, not six &mdash; and 16 of them are invisible to every "
   "scanner, checked one id at a time.</b> Two waves: v23.0.7/v24.0.4 (10-01) carried two, v23.0.8/v24.0.5 "
   "(10-13) carried fourteen, plus CVE-2026-104252 on 10-15. Querying "
   "<code>api.osv.dev/v1/vulns/&lt;id&gt;</code> for all seventeen returns <b>404 for sixteen</b>; the only "
   "one present is CVE-2026-104252, <b>the lowest-impact item in the set</b>. The advisory pages say why: "
   "&ldquo;No known CVE.&rdquo; Ten of the sixteen are <b>High-severity SQL injection in the query path</b> "
   "&mdash; multibyte charset handling, <code>convert_tz()</code> in VStream filters, Online DDL identifiers "
   "run as the DBA user, and trailing-comment splitting that hides SQL from parsing, planning <i>and ACL "
   "checks</i>. <code>govulncheck</code> against <code>vitess.io/vitess</code> surfaces exactly one of "
   "seventeen. Those patch releases also <b>enforce CRLs in all SSL modes, refuse several CRL configurations "
   "at startup, reject unsupported <code>sql_mode</code> values and restrict nine connection character "
   "sets</b> &mdash; a security patch wearing a patch-release version number. "),
  note='17-not-6')

# 3. Storybook: 9.4, and NOT the lane's highest.
edit('storybook-94-dev-server-story-rewrite',
  due="patched 10.6.2 / 9.1.21 / 8.6.19 &middot; reached the GitHub Advisory DB <b>9 days late</b>",
  prepend=(C + "<b>CVE-2026-114125 scores 9.4, which is <i>not</i> the highest in its lane, and it took nine "
   "days to become discoverable.</b> The vector "
   "<code>CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:P/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H</code> computes to <b>9.4</b>, "
   "below the <b>9.5</b> shared by the React RSC RCE and the Next.js image RCE. It was published 2026-10-12 "
   "and only entered the GitHub Advisory Database on <b>2026-10-21</b> &mdash; the same 8-to-9-day index lag "
   "the Next.js advisories showed. EPSS 0.375%. <code>@storybook/addon-mcp</code> is in the affected set at "
   "10.6.0, fixed 10.6.2. The companion CVE-2026-114126 leaks the dev server's <b>WebSocket auth token to any "
   "client that can load its HTML</b>, so any host on the LAN can reach it by IP. "),
  note='9.4-not-highest')

# 4. Angular: the two SSR packages have DIFFERENT last-affected ceilings.
edit('angular-v19-permanent-eol-unpatched',
  due="no fix (EOL) &middot; <code>platform-server</code> &le;19.2.25 but <code>@angular/ssr</code> &le;<b>19.2.27</b>",
  prepend=(C + "<b>A single &ldquo;&le;19.2.25&rdquo; rule under-reports, because the two SSR packages have "
   "different ceilings.</b> Today's Frontend lane counted <b>four</b> in-window advisories with no fixed "
   "version for the &le;19 line: CVE-2026-101895 (High, DoS via malformed DOCTYPE), CVE-2026-88058 (High, XSS "
   "via unescaped processing-instruction nodes) and CVE-2026-111754 (Moderate, open redirect) all carry "
   "<code>last_affected: 19.2.25</code> on <b><code>@angular/platform-server</code></b> &mdash; but "
   "CVE-2026-104871 (Moderate, path traversal in <code>CommonEngine</code> on Windows) is against "
   "<b><code>@angular/ssr</code></b>, whose last-affected is <b>19.2.27</b>. The hard evidence that "
   "&ldquo;ever&rdquo; is the right word: the repo shipped 22.x, 21.x and 20.x releases through 2026-10-14 "
   "and <b>zero 19.x releases</b>. "),
  note='two-ceilings')

# 5. Fabric 63509: not an aggregator error -- both records are first-class.
edit('fabric-cve-2026-63509-path-traversal',
  due="service-side fixed, <code>Customer Action Required: No</code> &middot; MSRC <b>9.9</b> vs NVD <b>8.8</b>",
  prepend=(C + "<b>The score gap is the Scope metric, and it is not an aggregator error &mdash; both records are "
   "first-class and on the record.</b> MSRC (secondary CNA, <code>secure@microsoft.com</code>) publishes "
   "<b>9.9</b> at <code>CVSS:3.1/AV:N/AC:L/PR:L/UI:N/<b>S:C</b>/C:H/I:H/A:H</code>; NVD (primary) publishes "
   "<b>8.8</b> with the identical vector except <b><code>S:U</code></b>, and <b>re-analyzed the record on "
   "2026-10-18</b> &mdash; so the 8.8 is a deliberate NVD judgement, not a stale auto-score. Microsoft is "
   "authoritative on scope: it operates the service and is the only party that can say whether the traversal "
   "crosses a tenant boundary. <b>A policy thresholding on NVD's number rates this a High rather than a "
   "Critical.</b> Also confirmed: the October 2026 MSRC release contains <b>zero</b> Fabric-family CVEs "
   "across 3,012 vulnerabilities, and all three carried Fabric CVEs have no Remediations entry, no FixedBuild "
   "and no patch URL &mdash; there is nothing to install. "),
  note='scope-not-aggregator')

# ============================ ENRICHMENTS ============================

# 6. The Oracle side of eMudhra: a SECOND alert whose affected set is the first's fix set.
edit('emudhra-ca-compromise-go-rebuild-not-restart',
  due="<b>2026-10-27 &mdash; Chrome removes <code>emSign ECC Root CA - G3</code></b> &middot; <b>patch Java TWICE</b>",
  prepend=(E + "<b>Oracle shipped two out-of-band Security Alerts four days apart, and the second one's "
   "affected builds ARE the first one's fix builds.</b> CVE-2026-91403 (2026-10-21, CVSS 9.1) distrusts the "
   "compromised <b>intermediate</b> CAs and affects Java SE 8u511, 11.0.33, 17.0.21, 21.0.13, 25.0.5, 27.0.1. "
   "CVE-2026-114820 (2026-10-24, CVSS 9.1, same component and vector) removes the compromised <b>root</b> CAs "
   "and affects <b>8u511-b32, 11.0.33.0.2, 17.0.21.0.2, 21.0.13.0.2, 25.0.5.0.2, 27.0.1.0.2</b> &mdash; the "
   "very builds that remediate 91403. That is <b>three Java patch events in five days</b> (20 Oct CPU &rarr; "
   "21 Oct alert &rarr; 24 Oct alert), and OpenJDK's own page says to act &ldquo;immediately &mdash; even if "
   "you have updated your runtime in the past few days&rdquo;. <b>If you patched Java last week you are not "
   "done.</b> "),
  note='patch-java-twice')

# 7. MongoDB 8.2: the board said "named in JIRA, never published" -- now measured.
edit('mongodb-82-no-fixed-version',
  due="<b>48 fixes tagged for an 8.2.13 that has <code>released=false</code></b> &middot; 8.2 EOL 86d ago at 8.2.12",
  prepend=(E + "<b>Measured against MongoDB's own Jira API: <code>fixVersion = 8.2.13</code> carries "
   "<b>48 SERVER tickets</b>, and 8.2.13 has <code>released=false</code> / <code>releaseDate=null</code>.</b> "
   "The branch was patched and the build was never cut. The list is heavily security: <b>SERVER-131229</b> is "
   "the fix for <b>CVE-2026-82067</b> (authorization can remain disabled at server startup, CVSS 4.0 "
   "<b>9.2</b>), alongside an intra-cluster SASL allowlist gap enabling a PLAIN downgrade, a heap memory "
   "disclosure in the multi-planner, an integer overflow in <code>explodeForSort</code>, and "
   "<code>authenticationMechanisms</code> not enforced on the MONGODB-X509 SASL path. <b>Every one of these "
   "reached 7.0.41 / 8.0.30 / 8.3.9 / 9.0</b> &mdash; 8.2 is the only branch where the fix is in git and in no "
   "tarball. The advisory's CPE ranges omit 8.2 entirely, which reads as &ldquo;unaffected&rdquo; to a "
   "scanner. <b>This is the sharpest unreachable-fix measurement the board has carried</b>, and the route to "
   "it &mdash; <code>jira.mongodb.org/rest/api/2/project/SERVER/versions</code> plus a fixVersion JQL search "
   "&mdash; is how you tell a <i>not yet shipped</i> fix from a <i>never shipped</i> one on any branch. "),
  note='48-tickets-measured')

# 8. Snowflake 85525: the scanner-blindness story only HALF closed.
edit('snowflake-drivers-ocsp-cve-2026-85525',
  due="patched 2026-09-03 &middot; <b>no GHSA / GO- / PYSEC record &mdash; scanners report nothing</b>",
  prepend=(E + "<b>Yesterday's board recorded that scanner blindness on the Snowflake driver CVEs had closed. "
   "It closed for 86597 only &mdash; and the half still open is the higher-scoring bug.</b> "
   "GHSA-qqj6-54q6-cxv6 does now resolve across six package entries in four ecosystems, but "
   "<b>CVE-2026-85525 has no GHSA, no <code>GO-</code> and no <code>PYSEC</code> record anywhere in OSV</b> "
   "&mdash; queried by package for Go v1 (5 advisories), Go <code>/v2</code> (2), PyPI (16) and Maven (7), it "
   "appears in <b>none</b>. Its only OSV presence is the auto-minted CVE-level record with "
   "<code>aliases: null</code>, <code>package: null</code> and a GIT range. So pip-audit, Dependabot, "
   "osv-scanner and govulncheck surface the 6.5 log-leak bug and <b>silently miss the 7.4 revocation "
   "bypass</b> (<code>technicalImpact: total</code>). <b>And the sequel is worse:</b> 27 days after shipping "
   "this fix, Snowflake <b>turned OCSP revocation checking off by default across six drivers in 24 days</b> "
   "&mdash; Go 2.3.0, JDBC 4.4.0, Node 3.4.0 and ODBC 4.0.0 on 09-30, ODBC 3.22.0 on 10-23, and Python 5.1.0 "
   "removed <code>OCSP_MODE</code> outright. The old fail-close settings "
   "(<code>disableOCSPChecks=false</code>, <code>insecureMode=false</code>, "
   "<code>DisableOCSPCheck=false</code>) are now <b>accepted but ignored</b>. Patch to remediate the bypass, "
   "take the next minor, and you are back to not validating revocation by a different route. "),
  note='half-closed-plus-ocsp-off')

# 9. The DB-MCP read-only bypass row gains a second unpatched server and a blast radius.
edit('postgres-mcp-servers-readonly-bypass',
  due="<b>no fixed version for either server</b> &middot; 529,340 monthly installs on the unpatched one",
  prepend=(E + "<b>Two unpatched critical read-only bypasses now, not one &mdash; and the blast radius is "
   "measured.</b> <code>crystaldba/postgres-mcp</code> CVE-2026-85620 (CVSS 9.2) is <b>51 days old with no "
   "release in 17 months</b>; the community fix sits unmerged as PR #200, and a 2026-09-23 comment reports "
   "<code>main</code> is still bypassable via <code>lo_export</code>, <code>dblink_exec</code> and "
   "<code>pg_terminate_backend</code> &mdash; so the CVE's confidentiality-only vector "
   "<b>understates</b> it. It took <b>529,340 PyPI downloads last month against 8,353</b> for AWS's patched "
   "equivalent: <b>63&times; more installs on the unpatched server</b>. The second is Bytebase "
   "<code>dbhub</code> CVE-2026-79536 (CVSS 9.1), and <code>main</code> was read today: the MySQL token "
   "scanner has a careful <code>--</code> branch and <b>no <code>#</code> branch at all</b>, while "
   "<code>multipleStatements: true</code> remains &mdash; and dbhub's own code comment says <b>DDL escapes "
   "its transaction-level backstop</b> via implicit commit, so the classifier is the only defence. <b>Four "
   "CVEs across three vendors share one root cause: read-only enforced by parsing the SQL string instead of "
   "by the database.</b> The only enforcement that holds is a read-only transaction plus a least-privilege "
   "role. "),
  note='dbhub-plus-downloads')

# 10. Next.js: the OSV index date this board carried was wrong, and the sharp union is narrower.
edit('nextjs-oct14-two-95-rces-no-13x-14x-fix',
  due="fixed 15.5.28 / 16.4.1 &middot; <b>a patched install can still resolve sharp 0.34.x</b>",
  prepend=(C + "<b>The index date was wrong and the sharp escape hatch is narrower than carried.</b> "
   "GHSA-673q-mjm6-r5xr entered OSV on <b>2026-10-22</b>, not 10-14 &mdash; "
   "<code>published: 2026-10-22T16:42:31Z</code> &mdash; an <b>8-day</b> blind window, and it has <b>no CVE "
   "alias</b> (<code>aliases: null</code>), so a CVE-keyed query misses it too. The "
   "<code>||</code> union exists <b>only on the 15.5.28 backport</b>, which declares "
   "<code>sharp: &quot;^0.34.3 || ^0.35.5&quot;</code> &mdash; the <code>0.34.x</code> arm survives, sharp's "
   "own fix is <b>0.35.5</b>, and <b>sharp 0.34 has had no release since 2025-11-06</b>. So a 15.5.28 install "
   "resolving sharp 0.34.x is on the &ldquo;patched&rdquo; Next.js and still vulnerable, and the version-range "
   "matcher calls it clean. 16.4.1 is a plain <code>^0.35.5</code> with no union. <b>Check "
   "<code>npm ls sharp</code>, not your <code>next</code> version.</b> One root cause, two scores: sharp rates "
   "it <b>Local 8.9</b>, Next.js rates it <b>Network 9.5</b> &mdash; one metric apart &mdash; and only "
   "sharp's record carries the mitigations, including that <b>the official Node.js binaries are not built "
   "PIE</b>. "),
  note='osv-10-22-and-union')

# 11. Doris: five 3.1 releases, not one.
edit('doris-cve-2026-72524-no-fix-on-2x-3x',
  prepend=(C + "<b>3.1.4 is the <i>last</i> 3.1 release, not the only one</b> &mdash; Apache published five "
   "(3.1.0 2025-09-04, 3.1.1 09-26, 3.1.2 10-27, 3.1.3 11-24, 3.1.4 12-29), confirmed against both the "
   "release index and the signed-artifact directories. The download page shows only 3.1.4 under Archived "
   "because that is the newest 3.1. The operational conclusion is unchanged &mdash; no 3.1.x carries the fix "
   "&mdash; but the stated fact was wrong. Two things worth adding: <b>NVD's record is still "
   "<code>vulnStatus: Deferred</code> with no <code>configurations</code> field at all</b> 41 days on, so a "
   "CPE-matching scanner returns zero; and <b>VeloDB Cloud 4.1 &mdash; the line VeloDB's own page recommends "
   "for new deployments &mdash; is built on Apache Doris 3.1</b>, the archived branch, with no public backport "
   "notice. Ask that vendor in writing for a build number. "),
  note='five-releases')

json.dump(L, open('lens/ledger_103.json','w'), indent=1)
print('corrections applied (%d): %s' % (len(applied), ', '.join(applied)))
print('skipped: %s' % (', '.join(skipped) or '-'))
