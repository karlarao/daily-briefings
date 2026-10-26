#!/usr/bin/env python3
"""Edition-104 corrections, applied to the LEDGER before any section is generated
(the 2026-09-14 build-order rule). Every row below was probed with probe_board.py
first (the 10-08 rule); seven drafted corrections were dropped because the board
was already right -- Aurora RESOLVED, StarRocks disabled-by-default, the Doris
archive, the React RSC fix list, the eMudhra CVSS spread, MongoDB 8.2's EOL, and
the RSC "fixed but invisible" wording were all already recorded correctly."""
import json, sys
L = json.load(open('lens/ledger_104.json'))
idx = {r['k']: r for sec in L if isinstance(L[sec], list) for r in L[sec] if isinstance(r, dict) and 'k' in r}
TODAY = "2026-10-26"
applied = []

def fix(key, due=None, prepend=None):
    r = idx.get(key)
    if r is None:
        raise SystemExit("MISSING KEY: " + key)
    if due is not None:
        r['due'] = due
    if prepend:
        r['t'] = prepend + " " + r['t']
    r['last_seen'] = TODAY
    applied.append(key)

# 1. THE DAY'S HEADLINE: the JDK fix now exists -- behind a support contract.
fix('jdk-114820-no-vendor-build-keytool',
    due="<b>Oracle shipped; every free OpenJDK build did not</b> &middot; interim remedy is still four <code>keytool -delete</code> calls",
    prepend=("<b>CORRECTED 10-26 &mdash; the shape changed from &ldquo;no vendor build exists&rdquo; to "
             "&ldquo;patched for paying customers only&rdquo;, which is a different and worse thing.</b> Oracle's Security "
             "Alert (Rev 1, 24 Oct) says it &ldquo;provides Java updates which removes the set of impacted root CA "
             "certificates related to eMudhra&rdquo;, and <code>oracle.com/java/technologies/downloads</code> now serves "
             "<b>17.0.21.0.3</b> and <b>21.0.13.0.3</b> &mdash; one BPR above the <code>&hellip;0.2</code> builds the advisory "
             "lists as affected &mdash; through the Patch Availability Document, i.e. a support-contract gate. The free "
             "distributions have nothing, and the proof is a direct in-tree probe rather than a release note: "
             "<b><code>openjdk/jdk21u</code> and <code>openjdk/jdk25u</code> still return HTTP 200 for all four cert files</b> "
             "(<code>emsignrootcag1</code>, <code>emsignrootcag2</code>, <code>emsigneccrootcag3</code>, "
             "<code>comodoaaaca</code>) under <code>src/java.base/share/data/cacerts/</code>, while mainline "
             "<code>openjdk/jdk</code> 404s all four with the control cert <code>digicertglobalrootca</code> still 200. "
             "No build cut from jdk21u/jdk25u can carry the removal yet. Measured vendor ceilings: Temurin 21.0.13+9 / "
             "25.0.5+8 / 27.0.1.0.2+1, Corretto 21.0.13.0.10, Microsoft 21.0.13.0.2 / 25.0.5.0.2 &mdash; <b>all at or below "
             "the affected boundary</b>. And the release notes cannot settle it: Microsoft's notes for those same builds "
             "claim they fix all three advisories while the same page reads &ldquo;Coming soon&rdquo; and &ldquo;Branch link "
             "TBD&rdquo;. <b>Verify the build you deploy</b> with OpenJDK's <code>CheckCerts.java</code> or "
             "<code>keytool -list -cacerts | grep -i emsign</code>, not with a changelog."))

# 2. K8s: the real slip is 6 days, not 13 -- and the fix is merged in git with no tag.
fix('k8s-oct-patch-overdue-all-four-branches',
    due="<b>13 days past the published target, 6 past the revised one</b> &middot; <b>fix merged on every branch, tagged in nothing</b>",
    prepend=("<b>ENRICHED 10-26 with the measurement that reframes it, and a second number the board was reading "
             "wrong.</b> <code>schedule.yaml</code> still advertises <code>targetDate: 2026-10-13</code> on all four "
             "branches, but LWKD records the round being <b>deliberately postponed one week to 2026-10-20</b> to pick up "
             "Go's CVE fixes &mdash; and the machine-readable schedule was never updated. So tooling that watches "
             "<code>schedule.yaml</code> reads a 13-day slip where the real slip is <b>6</b>, and nothing reconciles them: "
             "any &ldquo;patch overdue&rdquo; alert is currently wrong in one direction or the other. The sharper finding is "
             "what the delay withholds: <b><code>.go-version</code> on <code>release-1.34</code>, <code>-1.35</code>, "
             "<code>-1.36</code> and <code>-1.37</code> all read <code>1.26.10</code> today, while the newest shipped tags "
             "read 1.26.5 (v1.34.12) and 1.26.8</b>. The maintainers did the work; the binary does not exist. That is a "
             "distinct shape from an EOL branch or a paywalled fix &mdash; an SBOM-and-CVE pipeline reports the <i>same</i> "
             "posture before and after the fix was written, because every scanner reads versions. Corroboration that this "
             "is release-engineering throughput and not a content hold: v1.38.0-alpha.3 was due 21 Oct and is also uncut."))

# 3. PgBouncer: a second, larger stranded population.
fix('pgbouncer-scram-nonce-preauth-crash-19888',
    due="fixed 1.26.1 &middot; <b>unreachable on Azure (pinned 1.25.2) AND on Debian 12/13 (no fixed version at all)</b>",
    prepend=("<b>ENRICHED 10-26 &mdash; there is a second and larger stranded population, and it is not a managed "
             "service.</b> <b>Debian 12 (bookworm) and Debian 13 (trixie) list all six CVEs as <code>open</code> with no "
             "fixed version</b>; the tracker resolves only <code>sid</code>/<code>forky</code>. Trixie ships 1.24.1, "
             "patched only for the earlier May batch. So on current Debian stable the CVSS 8.8 SCRAM auth bypass "
             "(<code>CVE-2026-107350</code>, one known <code>auth_file</code> password logs you in as any other SCRAM "
             "user including PgBouncer admins and backend superusers, introduced 1.17.0) has <b>no distro fix at all</b>. "
             "Azure's own doc meanwhile still advertises that it &ldquo;ensures PgBouncer stays up to date with the latest "
             "features and security patches&rdquo; while pinning 1.25.2, last bumped July 2026 at a cadence of roughly two "
             "bumps a year. <b>One binary, three different answers to &ldquo;are we patched?&rdquo;, and the "
             "distinguishing variable is the supply chain rather than the version.</b>"))

# 4. MongoDB 8.2: the advisory is now the thing that hides the exposure.
fix('mongodb-82-no-fixed-version',
    prepend=("<b>ENRICHED 10-26.</b> Two surfaces now actively mislead an 8.2 operator. MongoDB's advisory page lists "
             "<code>CVE-2026-82067</code>'s affected range as 8.3.0&ndash;&lt;8.3.9 / 8.0.0&ndash;&lt;8.0.30 / "
             "7.0.0&ndash;&lt;7.0.41 &mdash; <b>8.2 appears neither as affected nor as fixed</b> &mdash; while "
             "<code>SERVER-131229</code> carries fixVersion 8.2.13. And <code>release-notes/8.2/</code> still states 8.2 "
             "&ldquo;is supported for both MongoDB Atlas and on-premises deployments&rdquo;, with zero occurrences of "
             "&ldquo;end of life&rdquo; or &ldquo;July 31, 2026&rdquo; on the page. <b>The generalisable mechanism: once a "
             "branch goes EOL it silently drops off the affected list, so the advisory stops being a way to discover you "
             "are exposed &mdash; an EOL branch looks <i>clean</i> in an advisory-driven inventory.</b>"))

# 5. postgres-mcp: the upgrade that looks like the fix is not.
fix('postgres-mcp-85620-unpatched-9-2',
    due="no fix &middot; PR #200 open <b>71 days</b> &middot; <b>and the lookalike &ldquo;upgrade&rdquo; is also unfixed</b>",
    prepend=("<b>ENRICHED 10-26 with a trap worth more than the day count.</b> A reader searching PyPI for the product "
             "name finds <b><code>postgres-mcp-pro</code> 0.4.2</b> &mdash; same summary string, higher version number, "
             "uploaded 2026-08-21 &mdash; and it is a <b>third-party fork, not an upstream patch</b>. Read line-by-line "
             "today: its <code>_validate_node</code> recurses into <code>list</code> and <code>tuple</code> attributes "
             "only when the element is itself a <code>Node</code>, which is exactly the shape PR #200 exists to fix, "
             "because <code>FuncCall</code> nodes live inside <i>nested</i> tuples under "
             "<code>RangeFunction.functions</code>. Upstream <code>main</code> has the identical un-recursed loop. "
             "<b>Installing it to &ldquo;get past 0.3.0&rdquo; leaves you vulnerable and swaps a known maintainer for an "
             "unknown one.</b> The scanner story is also now reproducible: a POST to <code>api.osv.dev/v1/query</code> "
             "for <code>postgres-mcp</code> 0.3.0 on PyPI returns <code>{}</code>, because the record is GIT-range-only "
             "with no PyPI ecosystem entry and no GHSA alias."))

# 6/7. Countdown-only refreshes.
fix('ray-62593-kev-66d-overdue-gpu-clusters',
    due="KEV due 2026-08-20 (<b>67d PAST DUE</b>) &middot; <code>forensicTriage: Yes</code> &middot; fix released 339 days ago",
    prepend=("<b>RE-READ 10-26:</b> unchanged in every KEV field, and the arithmetic is now the finding &mdash; "
             "<b>ray 2.52.0 shipped 2025-11-21, so the fix has existed for 339 days</b> against a 67-day-overdue KEV "
             "entry. Unpatched by omission, not by unavailability; current is 2.59.0. Note 2.57.1 and 2.58.1 both landed "
             "2026-10-21 and are <i>not</i> security releases &mdash; two same-day patches that look like a backport "
             "wave and are not."))

fix('doris-cve-2026-72524-no-fix-on-2x-3x',
    prepend=("<b>RE-READ 10-26 and the project now states the failure mode in its own words</b>, which is unusual enough "
             "to quote: the download page lists maintained branches as &ldquo;4.1, 4.0&rdquo; and files 3.1.4 under "
             "Archived Releases with &ldquo;These versions receive no further releases of any kind, security patches "
             "included. <b>A vulnerability found in one of them stays unfixed there, permanently.</b>&rdquo; 3.1.4 shipped "
             "2025-12-29, <b>nine months before the advisory</b>. Affected set re-read verbatim from NVD's copy of the ASF "
             "advisory: &ldquo;from 3.1.0 through 3.1.*, from 4.0.0 through 4.0.7, and from 4.1.0 through 4.1.3&rdquo;. "
             "The connectors are archived on the same terms, so a pinned Flink/Spark/Kafka Doris connector sits on the "
             "same cliff as the engine."))

json.dump(L, open('lens/ledger_104.json','w'), indent=1)
print("corrections applied to %d rows:" % len(applied))
for k in applied:
    print("   ", k)
