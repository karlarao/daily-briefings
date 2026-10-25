#!/usr/bin/env python3
"""Edition-103 new rows. Identity is DECLARED here (09-11 rule); reuse_key is
advisory only and prints every same-date parent row so a duplicate is visible
before it ships."""
import json, sys
sys.path.insert(0, 'tools/lens')
import ledger_surgery as LS

TODAY = "2026-10-25"
L = json.load(open('lens/ledger_103.json'))
existing = {r['k'] for ln in L if isinstance(L[ln], list) for r in L[ln]}

NEW_PATCH = [
 dict(k="jdk-114820-no-vendor-build-keytool", due="<b>no Temurin or Corretto build carries the fix</b> &middot; interim remedy is four <code>keytool -delete</code> calls",
   t=("<b>CVE-2026-114820 (CVSS 9.1, <code>javax.net.ssl</code>) was published 2026-10-24 and affects JDK "
      "8, 11, 17, 21, 25 and 27 &mdash; every supported line &mdash; and as of today no vendor build carries "
      "the fix.</b> Measured: Temurin's newest GA builds are <code>jdk-27.0.1.0.2+1</code>, "
      "<code>jdk-25.0.5+8</code>, <code>jdk-21.0.13+9</code>, <code>jdk-17.0.21+9</code>, "
      "<code>jdk-11.0.32.1+1</code>, <code>jdk8u504-b01</code>, all from the 10-21 CPU; Corretto 21's newest "
      "is 21.0.13.0.10 (10-23). OpenJDK tracks the fix as <b>JDK-8395690</b> and tells you to look for it in "
      "your vendor's release note; nothing published so far names it. So the interim remediation is manual "
      "surgery: delete <b>four</b> aliases from each runtime's <code>cacerts</code> &mdash; "
      "<code>emsignrootcag1</code>, <code>emsignrootcag2</code>, <code>emsigneccrootcag3</code> and "
      "<b><code>comodoaaaca</code></b>. That last alias is the tell: the compromised intermediates were "
      "<b>cross-signed by Sectigo</b> and chain to AAA Certificate Services as well, so removing the emSign "
      "roots alone leaves a valid path. Note the JDK removes <b>G1</b>, which Mozilla explicitly declined to "
      "remove. <b>On Debian/Ubuntu updating <code>ca-certificates-java</code> is documented NOT to work</b> "
      "(&ldquo;a long-standing bug in the latter&rdquo;) &mdash; the workaround is "
      "<code>rm -f /etc/ssl/certs/java/cacerts &amp;&amp; update-ca-certificates --fresh</code>. This is "
      "&ldquo;patched upstream, unbuildable for you&rdquo; on the most widely deployed server runtime there "
      "is."),
   url="https://openjdk.org/emudhra"),
 dict(k="pip-ensurepip-emsign-no-py39-fix", due="<b>Python 3.9 has no reachable fix at all</b> &middot; certifi floor &ge;2026.10.19",
   t=("<b><code>python -m venv</code> still hands out a pip whose vendored certifi trusts the compromised "
      "root, on every CPython from 3.9 to 3.12 &mdash; measured from each branch's "
      "<code>ensurepip/__init__.py</code> and each pip's <code>vendor.txt</code>.</b> 3.9 and 3.10 ship pip "
      "23.0.1 / certifi 2022.12.7; 3.11 ships pip 24.0 / certifi 2023.7.22; 3.12 ships pip 25.0.1 / certifi "
      "2024.8.30. Only 3.13+ ships pip 26.2.2 with certifi 2026.10.19. <b>Python 3.9 has no reachable fix:</b> "
      "pip 26.2.2 is the only fixed pip and declares <code>requires_python &gt;=3.10</code>, while 3.9's "
      "ceiling is pip 26.0.1 vendoring certifi 2026.1.4. <b>Updating the OS trust store does not help, and "
      "the reason is one line of pip's own source:</b> "
      "<code>_create_truststore_ssl_context()</code> builds a truststore context and then calls "
      "<code>ctx.load_verify_locations(certifi.where())</code> &mdash; it <b>unions</b> vendored certifi in; "
      "and pip 23.0.1 vendors <b>no truststore at all</b>, so it never consults the OS store. Sharper still: "
      "<b>Python 3.15.0, GA only 16 days ago, shipped <code>ensurepip</code> pip 26.2.1 &rarr; certifi "
      "2026.6.17 &rarr; the compromised root</b>, as did 3.14.8 and 3.13.16 &mdash; you need 3.15.1 / 3.14.9 "
      "/ 3.13.17. <b>A brand-new runtime GA is not evidence of a current trust store, and no dependency "
      "scanner reports a PEM file inside a wheel.</b>"),
   url="https://raw.githubusercontent.com/pypa/pip/26.2.2/src/pip/_vendor/vendor.txt"),
 dict(k="k8s-oct-patch-overdue-all-four-branches", due="<b>12 days overdue on all four branches</b> &middot; next window 2026-11-10, AFTER 1.34's EOL",
   t=("<b>The October Kubernetes patch round is 12 days past target on 1.34, 1.35, 1.36 and 1.37 "
      "simultaneously, and the CA fix is merged into all four branches with no release cut from any of "
      "them.</b> Read from the authoritative schedule data file rather than the rendered page: each branch "
      "carries a <code>next</code> entry (1.34.13, 1.35.10, 1.36.6, 1.37.2) with cherry-pick deadline "
      "2026-10-09 and <code>targetDate: 2026-10-13</code>; the last tag from any branch is 2026-09-23. "
      "<b>Four branches missing the same date is a release-process event, not four coincidences</b> &mdash; "
      "and September also slipped eight days. <code>.go-version</code> reads <b>1.26.10</b> on all four "
      "release branches, i.e. the eMudhra denylist is in-tree and unreachable except by building from the "
      "branch. <b>1.34 goes EOL 2026-10-27 and the next monthly window is 2026-11-10, fourteen days after "
      "that EOL</b>, so 1.34.13 likely never ships. Managed runway differs by 56 days across clouds: AKS "
      "2026-11-30, EKS 2026-12-02, GKE 2027-01-25 &mdash; all covered by vendor backports, not by the "
      "project. Worth recording how this was nearly misread: a rendered-page read suggested 1.34 lists no "
      "next patch at all, which would have become &ldquo;1.34.13 was cancelled&rdquo; &mdash; a materially "
      "different story from &ldquo;12 days overdue with two days of branch life left&rdquo;."),
   url="https://raw.githubusercontent.com/kubernetes/website/main/data/releases/schedule.yaml"),
 dict(k="ray-62593-kev-66d-overdue-gpu-clusters", due="KEV due 2026-08-20 (<b>66d PAST DUE</b>) &middot; <code>forensicTriage: Yes</code> &middot; fixed <code>ray 2.52.0</code>",
   t=("<b>A CISA KEV entry sits on the distributed runtime most GPU training and serving clusters run, 66 days "
      "past its due date &mdash; and finding it corrects a negative result this board shipped yesterday.</b> "
      "Ray <b>CVE-2025-62593</b> (added 2026-08-17, due <b>2026-08-20</b>, <code>forensicTriage: Yes</code>) "
      "is a DNS-rebinding/CSRF chain (CWE-94 + CWE-352) that turns a developer opening a malicious page in "
      "Firefox or Safari into <b>remote code execution on the Ray head node</b> &mdash; a host holding the "
      "cluster's credentials. CVSS v4 <code>AV:N/AC:L/AT:N/PR:N/UI:P/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H</code>. "
      "Fixed in <code>ray 2.52.0</code>; current is 2.59.0 and backports 2.57.1 / 2.58.1 shipped 2026-10-21, "
      "so the fix is reachable on three branches. CISA's required action invokes <b>BOD 26-04 forensic "
      "triage</b>, not patch-only. <b>The correction:</b> yesterday's AI Hardware brief reported that no KEV "
      "entry touches a GPU, accelerator, AI cluster or inference stack &mdash; <b>true for the 33 entries "
      "added in this window, false for the catalog as a whole</b>. A catalog-wide sweep does confirm the "
      "narrower claim: <b>zero NVIDIA entries ever, zero Mellanox</b>, and only two Intel entries, both "
      "pre-2018 and neither accelerator-related."),
   url="https://github.com/ray-project/ray/security/advisories/GHSA-q279-jhrf-cc6v"),
]

NEW_EVENTS = [
 dict(k="iceberg-v4-amt-baseline-merged-parquet-only", date=None,
   t=("<b>The Iceberg V4 baseline spec (adaptive metadata tree) merged 2026-10-14, and V4 manifests are "
      "Parquet-only.</b> The vote passed 18 +1 (9 binding, 0 against) and PR #16025 is in main. Tables "
      "upgraded from v1&ndash;v3 keep their existing Avro manifests, but <b>any new or rewritten manifest "
      "must be a V4 Parquet manifest</b> &mdash; so tooling that reads Iceberg manifests directly with an "
      "Avro reader has a V4 expiry date. Four more v4 votes landed or opened in the window, all of them "
      "things engines must implement: monotonically increasing snapshot timestamps (passed 10-12), the "
      "<code>file</code> type (passed 10-19, and adding one such column moves <code>last-column-id</code> "
      "forward by <b>7</b>), table constraints with <code>primary-key</code> <b>replacing identifier field "
      "IDs in v4</b> (opened 10-22), and a move from per-column <code>tight_bounds</code> to a file-level "
      "<code>tight_stats</code> flag that makes <code>count(1) WHERE col IS NULL</code> metadata-answerable "
      "(opened 10-22). <b>V4 still has no date</b>, deliberately: the spec says &ldquo;Version 4 is under "
      "active development and has not been formally adopted.&rdquo; A proposal to drop ORC and Avro as V4 "
      "<i>data</i> formats is now on the table with real pushback, naming Vortex, Lance and Nimble as reasons "
      "to keep that layer pluggable."),
   act="Inventory <code>SELECT file_format, count(*) FROM db.table.files GROUP BY 1</code> across the estate &mdash; it tells you whether V4's Parquet-only manifest layer is a non-event or a migration.",
   url="https://github.com/apache/iceberg/pull/16025"),
]

for r in NEW_PATCH:
    assert r['k'] not in existing, 'duplicate key: '+r['k']
    LS.reuse_key(r, L['patch'], 'due', 'similarity')
    r.setdefault('first_seen', TODAY); r['last_seen']=TODAY; r['days']=1
    L['patch'].append(r)
for r in NEW_EVENTS:
    LS.reuse_key(r, L['events'], 'date', 'similarity')
    assert r['k'] not in existing, 'duplicate key: '+r['k']
    r.setdefault('first_seen', TODAY); r['last_seen']=TODAY; r['days']=1
    L['events'].append(r)

json.dump(L, open('lens/ledger_103.json','w'), indent=1)
print('added %d patch rows, %d event rows'%(len(NEW_PATCH),len(NEW_EVENTS)))
print('patch %d  events %d'%(len(L['patch']),len(L['events'])))
