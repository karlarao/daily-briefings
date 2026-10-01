#!/usr/bin/env python3
"""Hand-verified fold map for edition 080 (2026-10-01).

Every group below was read ROW BY ROW before being listed here. This is the
09-11 rule: identity is asserted by a human-read map, never by a similarity
threshold -- on the real board true duplicates score LOWER on token overlap
than same-date pairs that must never merge.

Each entry: (survivor_key, [loser_keys], why).
The survivor keeps the OLDEST first_seen and the HIGHEST days of the group,
and every loser key is appended to the survivor's aliases[] so prior-edition
diffs still resolve. assert_alias_safe() then proves no parent key left by
omission.

DECLINED, recorded so the next run does not re-propose it:
  postgres-mcp-85620-unpatched-9-2  vs  postgres-mcp-servers-readonly-bypass
    -- NOT duplicates. The first is crystaldba/postgres-mcp CVE-2026-85620.
       The second is awslabs.postgres-mcp-server CVE-2026-87911 + CVE-2026-85787,
       a DIFFERENT product; it names 85620 only as the companion case. Two
       independent servers failing the same guarantee is two findings.
  jfrog-42018-42016-kev-due-sep25  vs  jfrog-artifactory-82329-kev
    -- NOT duplicates. Distinct KEV entries with distinct due dates
       (2026-09-25 vs 2026-09-05). Each co-names the other's CVEs, which is
       what made the hard-id sweep pair them.
  spring-security-47841-enterprise-only vs spring-sse-59313-fix-behind-support-contract
    -- NOT duplicates. Different primary CVEs that happen to share the
       "fix exists but is paywalled" mechanism.
  snowflake-cves-invisible-to-lockfile-scanners vs snowflake-drivers-ocsp-cve-2026-85525
    -- NOT duplicates. One is the CVE, the other is the scanner-blindness
       finding about it. The second is a distinct, reusable observation.
"""

PATCH_FOLDS = [
    ("mlflow-64849-ssrf-kev-overdue", ["mlflow-64849-kev-ssrf-past-due"],
     "Same CVE-2026-64849, same KEV anchor 2026-09-02, same mechanism "
     "(unauth webhook-test SSRF, redirect re-resolution without IP pinning). "
     "The two rows DISAGREED with each other on the day count -- one said "
     "'26 days ago' in prose, the other '28 days past due' -- which is the "
     "09-30 self-disagreement class. Survivor keeps the richer prose; "
     "daycounts.py then sets both sites to 29 and asserts they agree."),

    ("context7-mcp-cve-2026-75130", ["context7-mcp-cve-2026-75130-unpatched"],
     "Same CVE, same product, same no-fix story; survivor already carries 3 "
     "aliases. MUST preserve the loser's distinctive fact: the advisory pins "
     "affected at <=2.1.2 while npm is at 4.0.3, so a current version is NOT "
     "proof of a patch."),

    ("clickhouse-cve-2026-51992-cvss-9-1-sql-injection-to-rce-via",
     ["clickhouse-cve-2026-51992-create-dictionary"],
     "Same CVE, same mechanism (CREATE DICTIONARY source params), same "
     "affected range (<=26.3.9.8). Survivor is the richer row: advisory lists "
     "patched versions as 'Unknown' and the vendor security changelog carries "
     "no 2026 entries at all."),

    ("fabric-cve-2026-63509-path-traversal", ["fabric-cve-2026-63509-99"],
     "Same CVE. This fold CLOSES a recorded disagreement rather than hiding "
     "one: the loser said 'trackers disagree on whether any customer action "
     "exists', the survivor states the resolved MSRC position (fixed "
     "service-side, no customer action, no proven exploit). Survivor records "
     "that third-party trackers said otherwise."),

    ("tomcat-86350-regression-of-its-own-patch-sep",
     ["tomcat-11026-regression-of-its-own-patch"],
     "Same story, same three CVEs (86350 regression of the 41293 fix, plus "
     "76183), same release date 2026-09-15. Survivor names all three fixed "
     "trains (11.0.26 / 10.1.60 / 9.0.122) and the advisory publication date."),

    ("polaris-register-location-cve", ["polaris-cve-2026-64640"],
     "Same CVE-2026-64640, same endpoint, same fix (1.7.0). They DISAGREED on "
     "severity -- 'low severity' vs 'Medium, 5.3/6.5'. Survivor carries the "
     "specific scores and records that an earlier reading called it low. Also "
     "retires a `due` field holding the literal string 'shipped 2 Aug' "
     "instead of a date, which is the 09-14 defect class."),

    ("mongodb-82-no-fixed-version", ["mongodb-82-eol-unpatched-90"],
     "Same story: MongoDB 8.2 EOL 2026-07-31, excluded from the Aug 11 batch, "
     "CVE-2026-18691 (CVSS 9.0) permanently unpatched on that minor. Survivor "
     "adds the last patch (8.2.12) and the operative framing: remediation is "
     "a version move, not a patch."),

    ("ingress-nginx-unmaintained-cve-2026-4342",
     ["ingress-nginx-archived", "ingress-nginx-cve-2026-4342-fix-conflict"],
     "THREE rows for one story, and the board asserted 'no fix possible' and "
     "'fixed in 1.13.9' at the same time. Verified 2026-10-01 against the "
     "repo's own README and releases.atom: controller-v1.13.9 / v1.14.5 / "
     "v1.15.1 ALL EXIST, all published 2026-03-19 -- the project's FINAL "
     "releases, shipped in the last days of best-effort maintenance. The "
     "README says maintenance ran 'until March 2026' and that afterward there "
     "would be 'no further releases, no bugfixes, and no updates to resolve "
     "any security vulnerabilities'. So BOTH halves are true and never "
     "conflicted. Edition 079's 'Sources now conflict' framing was the wrong "
     "diagnosis: the fix shipped AND the project is permanently unmaintained, "
     "so the NEXT finding will have none."),

    ("libheif-84383-sharp-chain", ["libheif-1232-avif-rce"],
     "GHSA-g89c-p67h-r497 and CVE-2026-84383 are the same advisory for the "
     "same heap overflow in heif_decode_image(), same fix (libheif 1.23.2), "
     "same transitive path through sharp. Survivor keeps the framing that the "
     "scope is every native-codec image pipeline, not just Next.js."),
]

CLAIMS_FOLDS = [
    ("snowflake-gen2-qas-sf8-adaptive",
     ["snowflake-qas-default-sf8", "snowflake-qas-sf8-default"],
     "ONE claim carried under THREE keys, with THREE independent day counts "
     "(14, 6, 2) -- the exact failure the 09-09 note describes, where a fresh "
     "slug for a tracked story is what makes `days` lie. Two of the keys are "
     "a literal WORD-ORDER SWAP of each other "
     "(qas-default-sf8 / qas-sf8-default). All three say bundle 2026_06 turns "
     "Query Acceleration on by default at scale factor 8 (4x the old 2) on "
     "separately-metered serverless credits. Survivor is the oldest "
     "(first_seen 2026-08-14, days 14) and already carries an alias, and it "
     "alone carries the Adaptive-Warehouse detail that folds QAS into compute "
     "credits so the QAS cost column reads zero."),

    ("snowflake-2026-06-undated",
     ["snowflake-2026-06-still-disabled-sep4", "sf-2026-06-interval-qas-sf8"],
     "The board asserted BOTH 'auto-enable STILL undated -- SEVENTH "
     "consecutive edition' AND 'RESOLVED: now Enabled by Default, the flip "
     "landed in the 10.32 window (Sept 4-8)'. That is a live self-"
     "contradiction, not duplication, and the resolution supersedes the "
     "undated row. Also note the loser key `...-still-disabled-sep4` encodes "
     "the OPPOSITE of its own text, which now reads 'RESOLVED ... Enabled by "
     "Default' -- a slug that lies about its contents is worse than a "
     "duplicate, because a probe by key finds the wrong answer. Survivor "
     "keyed on the oldest (first_seen 2026-08-15, days 13) so the day count "
     "stays honest, carrying the RESOLVED text. "
     "`snowflake-interval-units-bcr2359` is deliberately NOT folded here: it "
     "is the INTERVAL semantics claim proper, which outlives the bundle's "
     "enablement-status question."),
]
