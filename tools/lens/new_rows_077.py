#!/usr/bin/env python3
"""Edition 077 new ledger rows, drafted then run past reuse_key's advisory."""

TODAY = "2026-09-28"

NEW_PATCH = [
    dict(k="postgis-73514-73515-no-stable-fix", due="no fix in any stable release",
         t=("<b>PostGIS carries two chained memory-corruption CVEs with NO fix in any stable "
            "release, 46 days after disclosure.</b> CVE-2026-73514 (CVSS 3.1 <b>8.8</b> / 4.0 "
            "8.7) is an out-of-bounds <b>write</b> in <code>address_standardizer</code>'s "
            "<code>classify_link()</code>, reachable by any database user who can point "
            "<code>standardize_address()</code> at a rules table; CVE-2026-73515 (8.1) is an "
            "out-of-bounds <b>read</b> in the FlatGeobuf property decoder. Chained, the "
            "researcher flipped <code>rolsuper</code> in backend cache to reach superuser/RCE "
            "and demonstrated it against <b>Neon, Supabase, Xata, AWS Aurora, Google AlloyDB "
            "and Azure Postgres</b>. The fixes exist only in <b>3.7.0beta2 and later RCs</b> "
            "&mdash; 3.7.0 is still at rc2 (2026-09-08) and the newest stable tarballs, 3.6.4 "
            "and 3.5.7 (both June), carry neither. Managed providers patched out of band; "
            "<b>self-managed PostGIS has no fixed stable release to install</b>. Drop "
            "<code>address_standardizer</code> and revoke the FlatGeobuf entry points. This is "
            "the third distinct no-fix mechanism on the board: fix exists only in pre-release."),
         url="https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-73514"),
    dict(k="tomcat-86350-regression-of-its-own-patch-sep", due="2026-09-15",
         t=("<b>The security patch WAS the vulnerability.</b> Apache Tomcat 11.0.26 / 10.1.60 / "
            "9.0.122 (released 15 Sep, advisories published 23 Sep) fix 12 CVEs, and the worst "
            "of them &mdash; <b>CVE-2026-86350</b>, Important &mdash; is a <b>regression "
            "introduced by the fix for CVE-2026-41293</b>. Inconsistent HTTP/2 request "
            "interpretation can <b>mix request headers between users</b>: a cross-tenant data "
            "leak, not a DoS. The affected range is <b>11.0.22&ndash;11.0.25 only</b> &mdash; "
            "exactly the builds you moved to when you patched CVE-2026-41293, so the people who "
            "patched fastest are the exposed population, and a scanner comparing you against "
            "&ldquo;latest&rdquo; can never show this shape because you <i>were</i> on latest. "
            "Two of the twelve are regressions or incomplete fixes of earlier security patches "
            "(CVE-2026-86248 likewise re-opens CVE-2026-34500). Also in the batch: a WebSocket "
            "security-constraint bypass (CVE-2026-76183) and OpenSSL/OpenSSL-FFM <b>silently "
            "ignoring CRLs</b> when the certificate comes from a keystore (CVE-2026-73581)."),
         url="https://tomcat.apache.org/security-11.html"),
    dict(k="mlflow-64849-kev-ssrf-past-due", due="2026-09-02 (26d PAST DUE)",
         t=("<b>MLflow CVE-2026-64849, CVSS 9.3, CISA KEV, remediation deadline passed 26 days "
            "ago.</b> <code>POST /api/2.0/mlflow/webhooks/{id}/test</code> is unauthenticated "
            "and validates the URL once, but the delivery path <b>follows redirects and "
            "re-resolves the hostname without pinning the validated address</b> &mdash; so a "
            "redirect or DNS rebind reaches cloud metadata (169.254.169.254) and the endpoint "
            "returns <code>response_status</code> <i>and</i> <code>response_body</code> to the "
            "caller. Full unauthenticated read SSRF. Fixed in 3.15.0 (on PyPI since July); "
            "3.16.1 preferred, which also covers the AI Gateway SSRF (CVE-2026-71211, whose OSV "
            "record has <b>no fixed version</b> so remediation cannot be computed) and a "
            "<code>statsmodels</code> flavor that <b>silently bypasses "
            "<code>MLFLOW_ALLOW_PICKLE_DESERIALIZATION=False</code></b> &mdash; GHSA-only, no "
            "CVE id, so a CVE-keyed gate cannot see it. This is the self-managed tracking "
            "server, not Databricks-managed MLflow, but plenty of Databricks shops run one."),
         url="https://github.com/mlflow/mlflow/security/advisories/GHSA-7gwp-5pfp-969j"),
    dict(k="starrocks-82306-query-detail-no-fix", due="no fix named · NVD Deferred",
         t=("<b>StarRocks CVE-2026-82306 has no fixed version named for the 3.5 LTS line, and "
            "NVD has parked it as <code>Deferred</code>.</b> CVSS 3.1 6.5 "
            "(<code>AV:N/AC:L/PR:L/UI:N/C:H</code>): <code>/api/query_detail</code> "
            "&ldquo;returns unfiltered query history for all users&rdquo;, so any authenticated "
            "low-privilege user reads <b>every other user's SQL text, execution plans and "
            "profiling data &mdash; including statements containing credentials</b>. The "
            "underlying report also covers six <b>unauthenticated</b> FE metadata REST handlers "
            "exposing cluster topology and database sizes. NVD carries no CPE configuration and "
            "no fix reference; the only version boundary anywhere is the description's "
            "&ldquo;through 4.0.13&rdquo;, and <b>StarRocks shipped no release at all in the "
            "30-day window</b> (newest is 3.5.21, 2026-08-28, whose notes cover dependency CVEs "
            "only). Compensating control until a fix exists: block "
            "<code>/api/query_detail</code> and the FE metadata handlers at the proxy."),
         url="https://nvd.nist.gov/vuln/detail/CVE-2026-82306"),
]

NEW_EVENTS = [
    # Only ONE of four drafted event rows survived reuse_key's advisory: the
    # Snowflake BCR-2437, GitHub Actions retention and AKS VMAS rows were all
    # already on the board and are enriched in corrections_077 instead.
    dict(k="openai-legacy-instruct-shutdown-sep28", date="2026-09-28",
         t=("<b>OpenAI shuts down <code>gpt-3.5-turbo-instruct</code>, <code>babbage-002</code>, "
            "<code>davinci-002</code> and <code>gpt-3.5-turbo-1106</code> TODAY</b> (announced "
            "2025-09-26), with <code>gpt-5.4-cyber</code> following on 1 Oct on only 20 days' "
            "notice and Gemini's <code>antigravity-preview-05-2026</code> on 5 Oct &mdash; the "
            "latter's replacement changed parameter naming from snake_case to PascalCase, so it "
            "is a code change, not a model-string swap. A larger legacy batch "
            "(<code>gpt-4</code>, <code>o1</code>, <code>o3-mini</code>, <code>o4-mini</code>) "
            "follows 23 Oct."),
         act="Grep the codebase and prompt configs for those model ids and repoint them today.",
         url="https://developers.openai.com/api/docs/deprecations"),
]
