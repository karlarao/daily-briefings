#!/usr/bin/env python3
"""Edition 108: add/enrich ledger rows. Runs AFTER corrections_108.py.

reuse_key's advisory caught FOUR would-be duplicates this run -- its widest
margin yet. Three were patch rows that a DATE-keyed probe could never have
surfaced (the 2026-09-17 Doris lesson), found only by probing identifiers:
  - Next.js two-RCE story  -> already `nextjs-oct14-two-95-rces-no-13x-14x-fix`
  - OpenJDK 114820 no-build -> already `jdk-114820-no-vendor-build-keytool`
  - Linux kernel 46300 KEV  -> already `linux-kernel-46300-kev-due-oct31`
and one event row that WAS date-keyed. All four are enriched in place.
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(SP), "tools", "lens"))
led = json.load(open(os.path.join(SP, "ledger_108.json")))
TODAY = "2026-10-30"

def R(sec, key):
    for r in led[sec]:
        if r["k"] == key:
            return r
    raise SystemExit("MISSING %s/%s" % (sec, key))

new_ev, new_patch, enriched = [], [], []

# ---------- enrich (advisory-caught duplicates: NO new slug) ----------
r = R("events", "linux-kernel-46300-kev-due-oct31")
r["t"] = ("<span class='corr'>ENRICHED 10-30</span> <b>KEV due TOMORROW, and the fix has existed since May "
          "2026 &mdash; so the only question is whether your node image caught up.</b> Upstream fixed it in "
          "5.10.257 / 5.15.208 / 6.1.174 / 6.6.141 / 6.12.91 / 6.18.33 / 7.0.10 and mainline 7.1. Ubuntu rates "
          "it High and describes the impact as local privilege escalation &ldquo;or possibly escape a "
          "container&rdquo; &mdash; a node-kernel container-escape-class bug, not a networking nuisance. "
          "<code>linux-aws</code>, <code>-azure</code>, <code>-gcp</code> and <code>-oracle</code> are all "
          "fixed, <b>except <code>linux-azure-nvidia</code> on 24.04 LTS, still listed &ldquo;vulnerable, work "
          "in progress&rdquo;</b> &mdash; i.e. AKS/Azure GPU node pools on Ubuntu 24.04 have no patched kernel "
          "to go to. Mechanism: <code>skb_try_coalesce()</code> loses the <code>SKBFL_SHARED_FRAG</code> marker, "
          "so ESP input can skip <code>skb_cow_data()</code> and decrypt in place over page-cache-backed frags.")
r["act"] = "Grep node kernels against the fixed list; on Azure GPU pools there is no patched kernel yet."
enriched.append("linux-kernel-46300 (advisory caught my duplicate draft)")

r = R("patch", "nextjs-oct14-two-95-rces-no-13x-14x-fix")
r["t"] = (str(r["t"]) + " <span class='corr'>RE-MEASURED 10-30</span> <b>Both RCEs are unauthenticated and the "
          "second has no workaround at all.</b> The SVG one traces three layers down &mdash; librsvg "
          "CVE-2026-96889 &rarr; <code>sharp</code> &lt; 0.35.5 (CVE-2026-114111) &rarr; your image endpoint &mdash; "
          "so forcing <code>sharp</code> &ge; 0.35.5 mitigates it without a Next upgrade. The <code>use cache</code> "
          "typed-array RCE hits the CURRENT major and the advisory says to upgrade even if you have no such "
          "function. <b>Correction to the third-party trackers: Next 15 did NOT EOL on 2026-10-21</b> &mdash; "
          "Vercel extended Maintenance LTS and will publish 15 security releases through <b>2027-01-31</b>. "
          "14.x/13.x remain &ldquo;Unsupported Versions&rdquo; with the Server Actions DoS unfixable below 15.5.28. "
          "<b>Three of October's eleven Next.js advisories carry no CVE id</b>, so a CVE-keyed gate misses both RCEs.")
enriched.append("nextjs patch row (advisory caught it; Next 15 LTS extension corrected)")

r = R("patch", "jdk-114820-no-vendor-build-keytool")
r["t"] = (str(r["t"]) + " <span class='corr'>MEASURED 10-30</span> <b>The gap is now quantified against Adoptium's "
          "own API: Temurin publishes <code>jdk-27.0.1.0.2+1</code>, <code>jdk-11.0.32.1+1</code> and "
          "<code>jdk8u504-b01</code> &mdash; all fixed &mdash; while its newest GA for the three most-deployed LTS "
          "lines are <code>25.0.5+8</code>, <code>21.0.13+9</code> and <code>17.0.21+9</code>, with no "
          "<code>.0.2</code> build at all.</b> So JDK 17, 21 and 25 have no reachable fix. OpenJDK's own page "
          "corroborates that not all vendors have shipped. One extra step that is easy to miss: on Debian/Ubuntu, "
          "updating <code>ca-certificates-java</code> is <b>NOT sufficient</b> &mdash; "
          "<code>rm -f /etc/ssl/certs/java/cacerts &amp;&amp; update-ca-certificates --fresh</code> is required.")
enriched.append("jdk-114820 (advisory caught it; Adoptium gap measured)")

r = R("patch", "brotli-111497-kev-runtime-wide-scanner-blind")
r["t"] = (str(r["t"]) + " <span class='corr'>SHARPENED 10-30</span> <b>The scanner is now demonstrably wrong in "
          "BOTH directions on this one CVE, which is a different failure from the blindness tracked for six "
          "weeks.</b> Under-reporting: <b>all 4,712 entries in the Go vulnerability database contain none of it</b> "
          "so <code>govulncheck</code> is clean on a KEV item, and npm has no advisory because the vulnerable "
          "component is the Node <i>runtime</i>. Over-reporting: <b>NVD has attached unbounded "
          "<code>clickhouse</code>, <code>duckdb</code> and <code>apache:arrow</code> CPEs</b> so every version of "
          "all three matches forever while neither database vendor has published a word &mdash; and a <b>FIXED</b> "
          "Node still reports brotli 1.2.0 because the fix was cherry-picked without a version bump. "
          "<b>A KEV-blocking gate pointed at Envoy 1.40.x reports a Critical the vendor considers remediated and "
          "cannot tell that from real exposure.</b> Six scorings now exist (NVD 9.8 @3.1, MSRC 8.1 @AC:H, Google "
          "and GitHub 9.2 @4.0, Node &ldquo;High&rdquo;, CISA titling it CWE-252). Ecosystem mapping DID arrive "
          "for PyPI since yesterday (<code>brotli</code> &lt; 1.2.1, <code>brotlicffi</code> &lt; 1.2.1.0). "
          "Three branch-specific fixes: <b>1.0.10 / 1.1.1 / 1.2.1</b> &mdash; a 1.0.9 estate needs 1.0.10.")
enriched.append("brotli-111497 (wrong in both directions; six scorings)")

r = R("patch", "php2shell-two-kev-rce-no-81-fix")
r["t"] = (str(r["t"]) + " <span class='corr'>NEW POPULATION 10-30</span> <b>Oracle Secure Backup 19.1.0.0.0&ndash;"
          "19.1.0.1.0 is affected, and Oracle only said so at Rev 2.</b> Oracle scores CVE-2026-109618 at CVSS "
          "9.8 (AV:N/AC:L/PR:N/UI:N, full C/I/A); the KEV due date was <b>2026-10-29 and has passed</b>. The sharp "
          "part is the revision: <b>Rev 1 on 2026-10-25 did NOT list Oracle Secure Backup; Rev 2 on 2026-10-26 "
          "has as its ONLY change &ldquo;Added Oracle Secure Backup.&rdquo;</b> Anyone who read the alert on day "
          "one and filed it as &ldquo;Communications and Solaris, not mine&rdquo; was wrong 24 hours later &mdash; "
          "re-read the alert, not a cached copy. OSB's web tool runs an HTTP/PHP stack, which is exactly the "
          "exposed surface, and OSB also took SIX more CVEs in the Oct 20 CPU (three remote-unauth at 9.8/9.8/8.6) "
          "on a product whose desupport was announced 2026-05-01.")
enriched.append("php2shell (Oracle Secure Backup population added; Rev1/Rev2 recorded)")

# ---------- genuinely new EVENT rows ----------
new_ev += [
 {"k":"gitlab-97229-kev-due-nov1","date":"2026-11-01",
  "t":("<b>CISA KEV remediation due for GitLab CVE-2026-97229 &mdash; CVSS 10.0, unauthenticated RCE on the "
       "GitLab server via a crafted regular expression in CI/CD configuration.</b> Added to KEV 2026-10-29. The "
       "rare part is CISA's SSVC record: <code>exploitation: active</code>, <b><code>automatable: yes</code></b>, "
       "<code>technicalImpact: total</code> &mdash; <code>automatable: yes</code> means mass scanning, not "
       "targeted use. Affects 19.2 &lt; 19.2.8, 19.3 &lt; 19.3.5, 19.4 &lt; 19.4.2; fixed 2026-10-12. "
       "<b>GitLab.com and Dedicated were patched before publication, so this is self-managed-only.</b> There is "
       "no workaround; GitLab shipped six detection rules instead."),
  "act":"Patch self-managed GitLab to 19.2.8 / 19.3.5 / 19.4.2 today; grep the six detection rules first if you must triage.",
  "url":"https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-4-2-released/"},
 {"k":"aks-azurelinux2-image-removal-oct31","date":"2026-10-31",
  "t":("<b>AKS begins removing Azure Linux 2.0 node images, after which &ldquo;you'll be unable to scale your "
       "node pools.&rdquo;</b> Support and security updates ended 2025-11-30 and the image has been frozen at "
       "<code>202512.06.0</code> since. Fix is upgrading node pools to a supported Kubernetes version or moving "
       "to <code>osSku AzureLinux3</code>. <b>Source disagreement stated rather than resolved:</b> the Learn doc "
       "(updated 2026-10-21) carries the 10-31 image-removal date while the retirement issue it links "
       "(Azure/AKS#4988) describes only the 2025-11-30 support end and was closed 2026-03-23 without mentioning "
       "it &mdash; the doc is the current source."),
  "act":"Check for Azure Linux 2.0 node pools today; they stop scaling tomorrow.",
  "url":"https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions"},
 {"k":"deepseek-v4-flash-0731-retire-nov5","date":"2026-11-05",
  "t":("<b>DeepSeek V4 Flash (0731) retires from Databricks pay-per-token</b> &mdash; announced 2026-10-06, "
       "replacement DeepSeek V4.1 Flash (1017). Distinct from the DBR 18.2 end-of-support row that shares this "
       "date. Note the chain this sits in: today's retirement of V4 Pro (0813) names V4.1 Flash as its target, "
       "and <b>V4.1 Flash itself retires 2026-11-19</b> &mdash; so migrate to the <code>(1017)</code> snapshot, "
       "not the unqualified name, or you do this twice inside three weeks."),
  "act":"Repin to the DeepSeek V4.1 Flash (1017) snapshot, not the unqualified model name.",
  "url":"https://docs.databricks.com/aws/en/machine-learning/retired-models-policy"},
 {"k":"deepseek-v41-flash-retire-nov19","date":"2026-11-19",
  "t":("<b>DeepSeek V4.1 Flash retires on Databricks &mdash; pay-per-token AND provisioned throughput</b> &mdash; "
       "with the surviving snapshot named as V4.1 Flash <code>(1017)</code>, which only reached Unity Gateway on "
       "2026-10-19. This is the far end of a deprecation chain shorter than a migration cycle: the model named as "
       "the replacement for a model retiring TODAY is itself gone in 20 days. Databricks' policy promises only 30 "
       "or 90 days' notice on AWS (the Azure page says three months or more &mdash; the two pages disagree on the "
       "notice period itself)."),
  "act":"Pin a snapshot id, not a model name, or use provisioned throughput for long-term support.",
  "url":"https://docs.databricks.com/aws/en/machine-learning/retired-models-policy"},
 {"k":"documentdb-50-auth-hardening-nov2","date":"2026-11-02",
  "t":("<b>Amazon DocumentDB 5.0 &ldquo;authentication handshake hardening&rdquo; engine patch (3.0.23310 / "
       "3.0.23157), auto-applied in your next maintenance window 30 days after release.</b> AWS assigns no CVE "
       "and gives no detail beyond that phrase plus &ldquo;reduced intermittent latency spikes during routine "
       "internal configuration reloads&rdquo; &mdash; <b>so you cannot assess it, only schedule it.</b> The "
       "matching 8.0 patch shipped 2026-10-19, which puts its auto-apply around 2026-11-18. Both are marked "
       "<code>[in progress]</code>."),
  "act":"Pick your maintenance window rather than inheriting one.",
  "url":"https://docs.aws.amazon.com/documentdb/latest/devguide/release-notes.html"},
]

# ---------- genuinely new PATCH rows ----------
new_patch += [
 {"k":"clickhouse-116366-unauth-rce-no-267-fix",
  "due":"<b>disclosed TODAY</b> &middot; <b>no patch for 26.7 or below</b> &middot; Cloud/BYOC already fixed",
  "t":("<b>ClickHouse CVE-2026-116366 &mdash; unauthenticated RCE on ClickHouse Server, CVSS 4.0 9.5 Critical, "
       "disclosed 2026-10-30 (CVE record published 11:17 UTC, still NVD <code>Received</code>).</b> Fixed only in "
       "v26.10.3.7-stable, v26.9.27.3-stable, v26.8.36.3-lts and v26.3.62.3-lts. <b>The sharpest instance of "
       "&ldquo;patched upstream, unpatched for you&rdquo; this board has carried: 26.7, 26.6, 26.5, 26.4, 26.2, "
       "26.1 and all 25.x/24.x/23.x are OUTSIDE the security-support matrix and get no patch &mdash; even though "
       "26.7 received stable builds on 10-21 and 10-22, so it still LOOKS maintained from the tag list.</b> The "
       "vendor does not disclose the &ldquo;certain conditions&rdquo;, so you cannot self-assess exposure. "
       "At check time the four patched tags were not yet visible on GitHub's tag listing &mdash; the advisory "
       "landed ahead of the public tags, so an <code>apt</code>/<code>docker</code> lag today is expected."),
  "url":"https://clickhouse.com/docs/resources/changelogs/security-changelog"},
 {"k":"edk2-97631-preboot-pxe-rce-no-tag",
  "due":"<b>no reachable fix</b> &middot; <code>master</code> only &middot; first possible tag is <code>stable202611</code>",
  "t":("<b>CVE-2026-97631 &mdash; unauthenticated PRE-BOOT RCE in the EDK II PXE driver, CVSS 4.0 9.5.</b> The "
       "IPv4/IPv6 ICMP-error handlers copy into a fixed 504-byte field without bounding the copy and advance the "
       "destination by a CUMULATIVE rather than per-fragment length. Preconditions are brutally low: the machine "
       "is PXE-booting, and the attacker needs only a unicast ICMP error to the client IP <b>from any network "
       "distance</b> &mdash; no credentials, no adjacency, no user interaction. <b>It executes before Secure Boot "
       "or measured boot verifies anything, so your attestation chain never sees it.</b> Fix merged to "
       "<code>master</code> 2026-10-15 (PR #13302) and exists in <b>no tagged release, no OEM BIOS and no distro "
       "package</b>: <code>edk2-stable202608</code> predates it, Debian marks bookworm, trixie and forky/sid all "
       "vulnerable with nothing fixed, <b>OVMF is affected so every UEFI VM that PXE-boots is in scope</b>, and "
       "Supermicro's own October BIOS advisory names the CVE with no fixed versions. edk2's cadence is "
       "Feb/May/Aug/Nov, so mid-November is the earliest tag. A maintainer records that the <b>embargo was broken "
       "by mistake</b>, making the bug's location public from 10-14. Found by Alex Matrosov and Dan Holmes-Mitra."),
  "url":"https://github.com/tianocore/edk2/security/advisories/GHSA-99cj-7hg9-mp4m"},
 {"k":"pgbouncer-107350-scram-bypass",
  "due":"fixed 1.26.1 &middot; <b>affects 1.17.0&ndash;1.26.0</b> &middot; <b>zero CPE rows, no OSV record</b>",
  "t":("<b>PgBouncer CVE-2026-107350, CVSS 8.8 &mdash; anyone who knows ONE <code>auth_file</code> password can log "
       "in as any other SCRAM user, including PgBouncer admins and backend superusers.</b> The attack is a second "
       "StartupMessage sent during SCRAM auth against a nonexistent database. The affected floor of <b>1.17.0</b> "
       "means essentially every PgBouncer in production. <b>NVD has it <code>Awaiting Analysis</code> with ZERO "
       "CPE configurations and OSV's only <code>pgbouncer</code> entries are Debian mirrors of a 2012 bug</b>, so "
       "no scanner will find it for you &mdash; <code>SHOW VERSION;</code> on the admin console is the only "
       "reliable test. Distinct from the <code>pgbouncer-scram-nonce-preauth-crash</code> row already on this "
       "board: same component and same fixed version, different bug. Siblings in the same release: "
       "CVE-2026-107349 (7.5, unauthenticated infinite loop from an <code>options</code> parameter with an empty "
       "name &mdash; and PgBouncer is single-threaded, so that is a total outage) and CVE-2026-107348 (5.9)."),
  "url":"https://nvd.nist.gov/vuln/detail/CVE-2026-107350"},
 {"k":"claude-code-2-1-313-ssh-backdoor",
  "due":"<b>pulled from all three registries</b> &middot; <b>uninstalling does NOT remediate</b> &middot; no vendor advisory",
  "t":("<b>The Claude Code extension for VS Code/Cursor <code>2.1.313</code> shipped a persistent SSH backdoor</b> "
       "&mdash; the first malicious build of a major lab's own first-party coding extension. Registry facts "
       "verified independently for this edition: <code>2.1.313</code> returns <b>404</b> on npm while 2.1.312 and "
       "2.1.314 resolve (dist-tags <code>latest</code> 2.1.314, <code>stable</code> 2.1.308), and Open VSX lists "
       "2.1.314 published <b>2026-10-30T01:07:38Z with 2.1.313 absent entirely</b> &mdash; the signature of a "
       "yanked build, and a clean build pushed ~7 hours before the first public report. Per the third-party "
       "advisory the payload appends an attacker Ed25519 key (comment <code>svc-telemetry</code>) to "
       "<code>~/.ssh/authorized_keys</code>, opens a reverse tunnel to 134.209.82.225, installs OS-level "
       "persistence, and beacons hostname, git email, public IP and the NAMES of credential-shaped env vars. It "
       "runs when Node loads <code>extension.js</code>, <b>before <code>activate</code></b>, so no interaction is "
       "needed. <b>Attribution is open</b> &mdash; publisher-account compromise and a build-pipeline breach are "
       "very different and the public evidence establishes neither. Authoritative check is the key fingerprint "
       "<code>SHA256:0Z6R+DF64Do2nwQic8a7kkfDLNNk4IiK+2U2Rci4htk</code>, not the comment string."),
  "url":"https://phorion.io/blog/offical-claude-code-vsx-compromise/"},
 {"k":"supermicro-bmc-18450-two-skus-tbd",
  "due":"<b>MBD-X12DGU and MBD-X13SEW-TF-OS1: fix = &ldquo;TBD&rdquo;, no workaround</b> &middot; validation ongoing",
  "t":("<b>Supermicro BMC: eight CVEs disclosed 2026-10-26, led by CVE-2026-18450 (CVSS 9.8, AV:N/AC:L/PR:N/UI:N) "
       "&mdash; the BMC does not fully enforce integrity and encryption for IPMI commands on an active RMCP+ "
       "session, so crafted packets run arbitrary commands unauthenticated over the network.</b> Also "
       "CVE-2026-65220 (8.8, RAKP+ logic flaw escalates an account to administrator), CVE-2026-65211 (7.2, "
       "authenticated admin reads/writes BMC physical memory), CVE-2026-18449 (7.5, hardcoded SMCRAKP key lets a "
       "password hash be cracked) and four more, plus CVE-2026-16521 (7.2, OS command injection in the BMC syslog "
       "function, firing on service restart). Supermicro publishes one fixed version per SKU across X11/H11/M11 "
       "through X14/H14/B14 &mdash; and lists <b>two boards as &ldquo;TBD&rdquo; with no fix and no "
       "workaround</b> while stating it is &ldquo;still testing and validating affected products&rdquo;, so other "
       "SKUs may also lack a build. Found by runZero; not in KEV."),
  "url":"https://www.supermicro.com/en/support/security_center"},
 {"k":"fastlane-asc-session-leak-local",
  "due":"fixed 2.241.2 same-day &middot; <b>no CVE id, no OSV record</b> &middot; gem bump is NOT sufficient",
  "t":("<b>Three High-severity fastlane advisories published 2026-10-26 hand any other local account on a build "
       "host a live App Store Connect session &mdash; no password, no 2FA.</b> GHSA-m67f-ghvw-j7qp (CVSS 7.1, "
       "CWE-276, &le;2.241.1): the Apple ID session cookie is written under "
       "<code>~/.fastlane/spaceship/&lt;apple id&gt;/</code> with default permissions, and the ASC API key under "
       "<code>~/.appstoreconnect/private_keys/</code> is exposed the same way in 2.227.2&ndash;2.241.1. "
       "GHSA-hqmj-jmgc-wmwp (7.6, CWE-22, 2.110.0&ndash;2.241.1): <code>match</code> joins remote storage file "
       "names onto the working directory unchecked, so a <code>..</code> writes anywhere the runner can &mdash; "
       "GCS, S3 and GitLab Secure Files affected, <b>git storage is not</b>. Plus a Swift-Fastfile runner-channel "
       "takeover. <b>None has a CVE id and OSV returns nothing for <code>fastlane</code> at all</b>, so an "
       "<code>osv-scanner</code> run against a Gemfile.lock misses a four-day-old High cluster. <b>The fix does "
       "not protect you from processes under the same account</b> &mdash; a fresh VM/container per job is the real "
       "remediation, which is infrastructure, not a version bump."),
  "url":"https://github.com/fastlane/fastlane/security/advisories"},
]

for r in new_ev:
    r.setdefault("first_seen", TODAY); r["last_seen"] = TODAY
for r in new_patch:
    r.setdefault("first_seen", TODAY); r["last_seen"] = TODAY
led["events"] += new_ev
led["patch"] += new_patch

json.dump(led, open(os.path.join(SP, "ledger_108.json"), "w"), ensure_ascii=False)
print("enriched in place (no new slug):")
for e in enriched: print("   -", e)
print("\nnew event rows: %d  new patch rows: %d" % (len(new_ev), len(new_patch)))
print("totals: events=%d patch=%d claims=%d ownclaims=%d promises=%d gaps=%d benchmarks=%d retired=%d"
      % (len(led["events"]), len(led["patch"]), len(led["claims"]), len(led["ownclaims"]),
         len(led["promises"]), len(led["gaps"]), len(led["benchmarks"]), len(led["retired_events"])))
