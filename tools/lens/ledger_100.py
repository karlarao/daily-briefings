"""Edition 100 ledger surgery: corrections/enrichments, then new rows."""
import json, sys, re
sys.path.insert(0, 'tools/lens')
import ledger_surgery as LS, countdowns as CD

TODAY = "2026-10-22"
L = json.load(open('lens/parent_ledger.json'))
byk = {}
for ln in L:
    if isinstance(L[ln], list):
        for r in L[ln]:
            byk.setdefault(r.get('k'), []).append((ln, r))

def edit(key, **kw):
    hits = byk.get(key)
    if not hits:
        raise SystemExit("MISSING KEY: %s" % key)
    ln, r = hits[0]
    for f, v in kw.items():
        r[f] = v
    return r

C = "<span class='corr'>ENRICHED 10-22</span> "

# ---- 1. Oracle KEV day count: 55 -> 56, plus the product precision ----
r = edit('cve-2026-21962-ohs-weblogic-kev',
    due="KEV due 2026-08-27 (<b>56d PAST DUE</b>) &middot; fix exists since the January 2026 CPU")
r['t'] = (C + "<b>56 days past due</b>, and the October CPU is now confirmed not to retire it &mdash; a "
  "grep of the published advisory finds <b>zero</b> mentions of the id. Precision worth keeping for a "
  "DB-lane reader: the KEV product is <b>Oracle HTTP Server and the WebLogic Server Proxy Plug-in</b>, "
  "not the RDBMS kernel &mdash; the exposure is the HTTP tier in front of a database-backed app "
  "(classically OHS/<code>mod_wl_ohs</code> fronting ORDS or APEX), which is exactly the tier a DBA "
  "does not own. <code>forensicTriage: Yes</code>. ") + r['t']

# ---- 2. APEX: NVD confirms the gap; 26.2 is a reachable path for 26.1.x only ----
r = edit('oracle-apex-two-98-unauth-oct-cpu',
    due="2026-10-20 &middot; <b>no fixed build named by Oracle OR NVD</b> for 24.1.x / 24.2.x")
r['t'] = (C + "<b>A second primary source now confirms the gap rather than closing it.</b> NVD published "
  "the record 2026-10-20T22:18Z (<code>Awaiting Analysis</code>, outcome stated as &ldquo;takeover of "
  "Oracle APEX&rdquo;) listing the <i>identical</i> affected ranges with <b>no fixed-version field</b>; "
  "<code>apex.oracle.com</code> 403'd for a second consecutive day. So 24.1.22 / 24.2.21 / 26.1.5 remain "
  "<b>inference, not a read</b>. What IS authoritative: <b>APEX 26.2 shipped 2026-10-06</b>, is outside "
  "every affected range and is publicly downloadable &mdash; so <b>26.1.x has a reachable remedy and "
  "24.1.x / 24.2.x have none at all</b>. ") + r['t']

# ---- 3. THP 68086: the mechanism is new and it is worse than a backport delay ----
r = edit('thp-madv-collapse-dirty-folio-68086',
    due="fixed ONLY in stable 7.1.4 &mdash; <b>no backport to any longterm series, and no upstream carrier left</b>")
r['t'] = (C + "<b>The reason this will never trickle down is that the code was deleted, not patched.</b> "
  "kernel.org lists exactly one unaffected range, <code>7.1.4 &le; 7.1.*</code>; the fix "
  "(<code>2dfe9f5c91d0</code>) is a stable-only backport of a change whose mainline twin is commit "
  "<code>044925f9b565</code> &mdash; <i>&ldquo;mm: fs: remove filemap_nr_thps*() functions and their "
  "users&rdquo;</i>. Debian still marks bookworm 6.1.190-1 and trixie 6.12.113-1 vulnerable and fixes "
  "only in forky/sid 7.2.11-1; a grep of <code>ChangeLog-6.12.114</code> for <code>khugepaged</code> "
  "returns zero. <b>So the correct framing is &ldquo;no backport to any longterm kernel&rdquo;, not "
  "&ldquo;no fix anywhere&rdquo;.</b> Also worth not acting on: Ubuntu's tracker marks 26.10 vulnerable "
  "while shipping linux 7.3.0, a kernel where the vulnerable code no longer exists &mdash; a tracker "
  "artifact, not evidence. ") + r['t']

# ---- 4. October CPU: SIX rows at 10.0, not one ----
r = edit('oracle-cpu-oct-20-next')
r['t'] = (C + "<b>Correction to the 10-21 reading: there are SIX rows at CVSS 10.0, not one.</b> "
  "Counting the matrix directly &mdash; CVE-2026-101809 (E-Business Suite Workflow Notification Mailer), "
  "CVE-2026-87337 (Access Manager Authentication Engine), CVE-2026-91231 / -91216 / -91221 (SOA Suite "
  "adapters and Fabric Layer over T3/IIOP) and CVE-2026-91299 (JD Edwards Orchestrator). The &ge;9.8 "
  "breakdown is <b>6 &times; 10.0, 15 &times; 9.9, 49 &times; 9.8</b>. The DB-lane point is unchanged "
  "&mdash; Database Server's own maximum is 9.8 and none of the six is the database &mdash; but "
  "&ldquo;max 10.0 is one EBS row&rdquo; was an undercount. ") + r['t']

# ---- 5. Iceberg V4: the ban is now MERGED spec text ----
r = edit('iceberg-v4-equality-delete-deprecation')
r['t'] = (C + "<b>The ban is now merged spec text, and V4 still has no date.</b> PR <b>#17783</b> "
  "&ldquo;Spec: Forbid writing new equality deletes in v4&rdquo; <b>merged 2026-09-29</b>, and "
  "<code>format/spec.md</code> on <code>main</code> now lists it as a v4 change while opening with "
  "&ldquo;Version 4 is under active development and has not been formally adopted.&rdquo; The &ldquo;File "
  "type&rdquo; vote passed 2026-10-19 (8 binding / 19 non-binding / 0 &minus;1). Equality deletes remain "
  "creatable in v2 and v3 only. <b>The migration route exists and shipped</b>: Iceberg 1.12.0's Flink "
  "<code>ConvertEqualityDeletes</code> task converts them to deletion vectors &mdash; and #17630 in that "
  "same release fixes <i>deleted rows reappearing after a failed conversion cycle</i>, so 1.12.0 is the "
  "floor. Row stays deliberately <b>undated</b>. ") + r['t']

# ---- 6. Fabric Runtime 2.0: window elapsed, now 22 days past ----
r = edit('fabric-runtime-2-default')
r['t'] = (C + "<b>22 days past the published window and still no flip.</b> The Runtime 2.0 page still "
  "carries the unchanged forward-looking sentence promising the default switch &ldquo;in late September "
  "2026&rdquo;, while the runtime overview states &ldquo;By default, all new workspaces currently use "
  "Runtime 1.3.&rdquo; The row stays TBD, and the reason is now stronger than &ldquo;no day was "
  "published&rdquo;: <b>the vendor's own window has elapsed with no flip and no new date</b>. ") + r['t']

# ---- 7. Redshift TLS: pre-flight queries + the driver change riding alongside ----
r = edit('redshift-rejects-tls-1-0-1-1-provisioned-and-serverless-and')
r['t'] = (C + "<b>9 days out, re-read today, date and scope unchanged &mdash; and AWS now publishes the "
  "pre-flight query per flavour</b>: provisioned reads <code>sslversion</code> from "
  "<code>STL_CONNECTION_LOG</code>, serverless reads <code>ssl_version</code> from "
  "<code>SYS_CONNECTION_LOG</code>. The trap worth naming: <b>JDBC 2.3.0 and the Python driver 2.2.0 "
  "both flipped default <code>sslmode</code> to <code>verify-full</code></b> in the same three-week "
  "window, so the driver upgrade you perform to satisfy the TLS floor silently adds a hostname check "
  "&mdash; test CNAME, proxy and PrivateLink endpoints, which is exactly where names do not match. ") + r['t']

# ---- 8. parquet CVE-2026-73334: NVD still contradicts itself ----
r = edit('parquet-cve-2026-73334-no-fix')
r['t'] = (C + "<b>Re-measured: the NVD contradiction persists, unchanged.</b> Its description still tells "
  "readers to expect the fix &ldquo;presumably in version 1.19&rdquo; while its own CPE range "
  "(1.12.2 &le; v &le; 1.18.0) agrees 1.18.1 is clean; <code>lastModified</code> is still 2026-09-10. "
  "And the machine-readable side is worse than stale: <b>there is no OSV or GHSA record at all</b> "
  "&mdash; <code>GET /v1/vulns/CVE-2026-73334</code> 404s and <code>parquet-hadoop</code> returns zero "
  "vulnerabilities at every version. A human reading the record and a scanner reading it reach "
  "<i>opposite</i> conclusions, and neither is right. ") + r['t']

# ---- NEW ROWS (5) — probed against the board first ----
NEW = [
 dict(k="litellm-1107-malicious-release-oct21",
   due="<b>NO PATCH UNDOES EXPOSURE</b> &mdash; rotate every credential those hosts could read",
   t=("<b>LiteLLM 1.107.0 was a MALICIOUS release, and the entry point was the release pipeline rather "
      "than a maintainer account.</b> Live on PyPI 11:39&ndash;13:23 UTC on 2026-10-21 and on the "
      "Docker/GHCR <code>latest</code>, <code>main-latest</code> and <code>main-stable</code> tags "
      "11:46&ndash;14:20 UTC. All seven wheels and the sdist carried <code>cook.pth</code> + "
      "<code>cook.py</code> plus a <code>sitecustomize.py</code> loader &mdash; and because "
      "<code>.pth</code> and <code>sitecustomize</code> execute at <b>interpreter startup</b>, the "
      "payload ran in <i>every</i> Python process on the box, including <code>pip</code> itself when "
      "used to inspect or repair the install. It took SSH/GPG/TLS private keys, AWS/Azure/GCP/"
      "Kubernetes/Docker/Vault/Terraform credentials, <code>.netrc</code>, <code>.env</code>, browser "
      "cookies, IMDS credentials and &mdash; the part that makes a gateway different in kind &mdash; "
      "<b>the LiteLLM proxy database, where every upstream provider key in a fleet is concentrated</b>. "
      "The attacker overrode branch protection and built from the lookalike org <code>Berri-AI</code> "
      "(upstream is <code>BerriAI</code>), so the <b>GitHub source stayed clean</b> and reading the repo "
      "told you nothing. <b>Version pinning was therefore the wrong control; digests and build "
      "provenance are the right one.</b> Last known good 1.106.2. Second LiteLLM supply-chain "
      "compromise in seven months.")),
 dict(k="emudhra-ca-compromise-go-rebuild-not-restart",
   due="<b>no single CVE</b> &mdash; Go needs a REBUILD, and EOL runtimes get nothing",
   t=("<b>A trust-store compromise is a build-system problem, and five of the six runtimes that fixed it "
      "minted no CVE.</b> The eMudhra / emSign intermediate CA keys were declared compromised "
      "(2026-10-20/21; uv's advisory names <b>emSign ECC Root CA - G3</b> and rates it High with "
      "&ldquo;no known CVE&rdquo;). Remediation differs per runtime and that is the whole problem: Node "
      "and Deno shipped a new bundle, Python shipped a new <b>pip</b> carrying a new <b>certifi</b>, uv "
      "shipped a vendored bundle <i>and</i> new managed CPython builds, and <b>Go compiled a "
      "<code>crypto/x509</code> denylist INTO the binary</b> (CVE-2026-111943, Go 1.27.3 / 1.26.10) "
      "&mdash; so a statically linked Go service needs a <b>rebuild, not a restart</b>, and "
      "<code>go version -m</code> on deployed artifacts is the only inventory. Go does not name the CA; "
      "Node's release the next day names the eMudhra intermediate compromise outright, so the "
      "attribution is only available by reading both vendors. <b>A reader who patches to latest "
      "everywhere still misses every statically linked Go binary and every venv whose pip was not "
      "separately upgraded &mdash; and the scanner number never moves, because there is nothing to "
      "match.</b> EOL lines (Node &le;20, Go &le;1.25, Python 3.10) get nothing.")),
 dict(k="sentence-transformers-68770-local-path-rce",
   due="fixed 5.6.0 (current 6.2.0) &mdash; reachable",
   t=("<b>sentence-transformers CVE-2026-68770, CVSS 9.8, unauthenticated: loading a model from a LOCAL "
      "path bypassed <code>trust_remote_code</code> and executed custom Python.</b> If you load embedding "
      "or reranker models from a model cache, an artifact store or an S3 sync &mdash; anything a build "
      "pipeline writes &mdash; you were executing whatever <code>modules.json</code> pointed at "
      "regardless of the consent flag. Fixed in 5.6.0; 6.2.0 tightens further by requiring module paths "
      "to be relative with no <code>..</code>, even with <code>trust_remote_code=True</code>. Relevant "
      "to any RAG or vector pipeline that treats a local model directory as trusted input.")),
 dict(k="mem0-115324-sqli-into-databricks-warehouse",
   due="fixed mem0 1.0.8 &mdash; but OSV had no record on publication day",
   t=("<b>CVE-2026-115324: SQL injection in mem0's Databricks vector store, CVSS 4.0 9.2 Critical, "
      "published 2026-10-22 &mdash; today.</b> <code>mem0/vector_stores/databricks.py</code> interpolates "
      "memory text, metadata and message names straight into <code>insert()</code> and "
      "<code>update()</code>, so <b>attacker-influenced stored memory executes SQL on your configured "
      "Databricks SQL warehouse</b>. The shape is what matters: the injection vector is content an agent "
      "<i>writes</i>, not a request a user sends, so request-inspecting controls never see it &mdash; "
      "agent memory is now a path from untrusted content into a production warehouse. Affected "
      "0.1.117 &lt; 1.0.8. <b>Scanner caveat:</b> OSV's <code>mem0ai</code> record carried no entry for "
      "this id on publication day, so a lockfile scan reports clean until ingestion catches up.")),
 dict(k="lakekeeper-s3-signing-confinement-no-cve",
   due="fixed 0.13.7 / 0.14.1 (2026-10-16) &mdash; <b>no CVE, no GHSA, empty advisories page</b>",
   t=("<b>Lakekeeper was signing S3 requests for objects OUTSIDE the table location, and nothing in any "
      "advisory feed will tell you.</b> 0.13.7 and 0.14.1 (both 2026-10-16) confine remote signing to "
      "objects inside the table location and to known parameters and headers, refuse writes using an "
      "encryption key other than the warehouse's, stop tables setting "
      "<code>write.object-storage.path</code>, and confine expired-metadata cleanup to the table "
      "location. That is a <b>credential-vending confinement fix</b> &mdash; the highest-consequence "
      "shape a catalog can have, because the catalog is now the de facto storage firewall. There is "
      "<b>no CVE, no GHSA and an empty GitHub advisories page</b>, so operators on &le;0.13.6 or 0.14.0 "
      "get no signal from any tool. Act on the release notes. Same month: Nessie 0.108.8 stopped vended "
      "GCS credentials reaching sibling prefixes sharing a name, and Unity Catalog OSS 0.7.0 lists "
      "unlabelled AWS credential-vending hardening.")),
]
for n in NEW:
    adv = LS.reuse_key(n, L['patch'], 'due', 'similarity')
    print("  advisory for %-48s -> %s" % (n['k'], adv if adv else 'no same-date parent'))
L['patch'].extend(NEW)

json.dump(L, open('lens/ledger_100.json','w'), indent=1)
print("\nedits applied. patch %d -> %d  (+%d new)" % (len(L['patch'])-len(NEW), len(L['patch']), len(NEW)))
