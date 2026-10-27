"""Edition 105 corrections and enrichments — applied to the LEDGER before any
section is generated (the 2026-09-14 build-order rule: correcting the assembled
HTML leaves the rendered table generated from the pre-fix ledger).

Today's probe (probe_board.py) found 5 of 6 drafted corrections were ALREADY
right on the board — CVE-2026-111943's attribution (corrected 10-25), the Java
two-alert sequence (enriched 10-25 with exactly today's finding), BCR-2413's
slip to Feb 2027 (corrected 10-23), Percona's resolution (ed. 074) and the
Redshift ODBC/TLS split. That is the 10-26 pattern holding: the stale thing is
usually the prompt, not the ledger. Only the ones below are genuine.
"""
import re

def _patch(rows, key):
    for r in rows:
        if r.get('k') == key:
            return r
    raise SystemExit("corrections_105: key not on board: %s" % key)


def apply(L, today="2026-10-27"):
    applied = []

    # ---- 1. CORRECTION: the board asserts a "revised 2026-10-20" Kubernetes
    # patch date that today's primary read cannot source anywhere. DevOps
    # measured schedule.yaml still at targetDate 2026-10-13 (now 14 days stale)
    # and LWKD reporting November 10 with NO delay recorded. A date the board
    # states and no primary carries is exactly the 09-11 class of defect.
    r = _patch(L['patch'], 'k8s-oct-patch-overdue-all-four-branches')
    r['due'] = ("<b>1.34 EOL TODAY with 1.34.13 never cut</b> &middot; "
                "<b>fix merged on every branch, tagged in nothing</b>")
    r['t'] = (
      "<span class='corr'>CORRECTED 10-27</span> <b>The &ldquo;revised 2026-10-20&rdquo; date this row "
      "carried is unsourceable, and the deadline it was waiting for has now expired.</b> Re-measured against "
      "both primary artifacts today: <code>schedule.yaml</code> still advertises <code>targetDate: "
      "&quot;2026-10-13&quot;</code> on all four branches (now <b>14 days stale</b>), and Last Week in "
      "Kubernetes Development reports the next round targeted for <b>2026-11-10</b> with cherry-picks due "
      "11-06 and <b>no delay recorded at all</b>. Neither source carries 10-20. So October was folded into "
      "November rather than slipped &mdash; and <b>Kubernetes 1.34 reached upstream end of life today, "
      "2026-10-27, with v1.34.13 never cut.</b> <code>dl.k8s.io</code> still points every supported minor "
      "at the 23 Sep builds: stable-1.34=v1.34.12, 1.35=v1.35.9, 1.36=v1.36.5, 1.37=v1.37.1. "
      "<b>The shape that matters:</b> <code>.go-version</code> reads <b>1.26.10</b> on release-1.34/-1.35/"
      "-1.36/-1.37 while every shipped tag carries <b>1.26.5</b> (v1.34.12) or <b>1.26.8</b> &mdash; so the "
      "<code>crypto/x509</code> fix for CVE-2026-111943 is merged on all four branches and reachable from "
      "<b>no downloadable artifact</b>. git looks patched; every artifact is not; an SBOM-and-CVE pipeline "
      "reports the identical posture before and after the cherry-pick. "
      "<b>containerd is in the same state and worse:</b> nothing has shipped since 2026-10-13, the Go bump "
      "is merged only on <code>release/2.4</code> (CI matrix <code>[1.26.10, 1.27.3]</code>) and is "
      "<b>unmerged on release/2.2 and the 2.3 LTS</b>, both still <code>[1.26.9]</code> &mdash; while "
      "<b>containerd 2.2 reaches EOL 2026-11-06</b>, leaving a Kubernetes 1.36 cluster exactly one supported "
      "runtime, the LTS that has not merged the fix."
    )
    applied.append(('CORRECTED', r['k'], 'unsourceable 10-20 date removed; 1.34 EOL today'))

    # ---- 2. ENRICHMENT: the eMudhra row gains the half nobody is tracking.
    # The Go denylist fixes Certificate.Verify; it does nothing for shelled-out
    # git/helm/kustomize, which is why Argo CD needed a SECOND release.
    r = _patch(L['patch'], 'emudhra-ca-compromise-go-rebuild-not-restart')
    r['t'] = r['t'].rstrip() + (
      " <span class='corr'>ENRICHED 10-27</span> <b>The remediation splits in two and the industry is "
      "tracking one half.</b> The Go denylist repairs <code>Certificate.Verify</code> for Go TLS clients and "
      "does <b>nothing</b> for <code>git</code>, <code>helm</code>, <code>kustomize</code>, <code>curl</code> "
      "or any non-Go process in the same container &mdash; those read the <b>image's own CA store</b>. "
      "Argo CD proved it by needing a second release: 3.3.17/3.4.12/3.5.6 bumped Go, then <b>v3.3.18</b> "
      "deleted <code>emSign_ECC_Root_CA_-_G3.crt</code> from three Dockerfiles because release-3.3's base "
      "image is an unsupported Ubuntu whose <code>ca-certificates</code> are not refreshed at build time. "
      "Only four projects have publicly addressed the image store (Argo CD, OTel Collector requiring Alpine "
      "<code>ca-certificates</code> 20261020-r0, Prometheus 3.15.1/3.13.5, and Docker 29.9.2 warning that "
      "<b>registry chains depending on the revoked intermediates fail image pulls and pushes</b>). "
      "<b>Two facts that narrow the blast radius and the fix:</b> the intermediates were <b>never logged to "
      "Certificate Transparency</b>, so CT-enforcing browsers were structurally safe and the exposed "
      "population is precisely backend HTTP clients and bundled CA bundles, which essentially never enforce "
      "CT; and only <b>one</b> globally-trusted root actually needs removing &mdash; "
      "<code>emSign ECC Root CA - G3</code>, the cross-signer &mdash; plus Sectigo's "
      "<code>AAA Certificate Services</code>. certifi reached that the hard way, dropping four roots on "
      "10-18, <b>restoring the unaffected ones</b> on 10-19 and settling at 118 certs on 10-23. Pulling "
      "G1/G2 breaks unrelated TLS for no security gain, so &ldquo;delete the emSign roots&rdquo; is not a "
      "safe instruction."
    )
    applied.append(('ENRICHED', r['k'], 'image CA store is the second remediation; CT + narrow root set'))

    # ---- 3. ENRICHMENT: Percona is resolved, but the MongoDB reachability story
    # moved for a different reason — the builds carrying the fixes are cut in
    # Jira and not downloadable.
    r = _patch(L['patch'], 'mongodb-82-no-fixed-version')
    r['t'] = r['t'].rstrip() + (
      " <span class='corr'>ENRICHED 10-27</span> <b>Two measurements today, one of which retires a standing "
      "note.</b> (1) <b>Percona Server for MongoDB is no longer the laggard:</b> 8.0.34-15 shipped 10-22 "
      "against upstream 8.0.34, which is the newest <i>publishable</i> 8.0 build, so Percona is at parity "
      "with anything a reader can actually install. (2) <b>But 9.0.5, 8.3.14, 8.0.35 and 7.0.46 all read "
      "<code>releaseDate: 2026-10-26</code> and <code>released: true</code> in MongoDB's Jira while none is "
      "downloadable</b> &mdash; <code>fastdl.mongodb.org</code> 403s all four where 9.0.4 and 8.0.34 return "
      "200, and <code>current.json</code> still names 9.0.4 / 8.3.13 / 8.0.34 / 7.0.45 as current. That "
      "dissolves the board's older &ldquo;9.0.4 shipped on two different days&rdquo; puzzle: Jira's "
      "<code>releaseDate</code> is a <b>build-cut date, not public availability</b>, and the 403-vs-200 "
      "probe proves the ordering. It also means the 8.0 backport of the resharding step-up deadlock "
      "(SERVER-127745, reproduced in production on 8.0.19) sits in a build nobody can install. Meanwhile "
      "<code>current.json</code> still advertises <b>EOL 8.2.12 as <code>production_release: true</code></b> "
      "88 days after 8.2 went end of life, which is the mechanism by which that EOL actually bites."
    )
    applied.append(('ENRICHED', r['k'], 'Percona at parity; fixes cut in Jira but undownloadable'))

    # ---- 4. ENRICHMENT: the advisory-identity row gains today's measured
    # mechanism — a GHSA is only globally resolvable if someone published it
    # globally, and nothing warns you when they did not.
    r = _patch(L['patch'], 'react-rsc-95-unauth-rce-no-cve')
    r['t'] = r['t'].rstrip() + (
      " <span class='corr'>ENRICHED 10-27</span> <b>Thirteen days after publication the advisory is still "
      "absent from the GitHub Advisory Database and OSV</b> &mdash; re-measured on all three surfaces today, "
      "so <code>npm audit</code>, Dependabot and osv-scanner all report clean on a vulnerable tree and the "
      "only remedy is pinning by hand (<code>react-server-dom-webpack</code>/<code>-parcel</code>/"
      "<code>-turbopack</code> 19.0.9 / 19.1.10 / 19.2.9 / 19.3.1). A <b>second</b> React advisory shipped "
      "the same day with the same blind spot: GHSA-h3gv-c5rc-p453, Server Functions DoS at CVSS 4.0 8.2, "
      "also absent from OSV, whose own Impact prose and structured metadata disagree about the affected "
      "range (trust the wider metadata). <b>The mechanism behind this class is now measured:</b> Mobile "
      "established that <code>GHSA-frr6-h895-5pxp</code> &mdash; which an earlier edition read as resolving "
      "nowhere &mdash; <b>does</b> resolve, as a <b>repo-scoped</b> advisory under "
      "<code>dart-lang/sdk/security/advisories/</code>, while <code>github.com/advisories/&lt;id&gt;</code> "
      "404s and the <code>github/advisory-database</code> mirror 404s in both <code>github-reviewed/</code> "
      "and <code>unreviewed/</code>. A repo advisory never published to the global database exists only "
      "under its repo path, so every consumer of the global DB and OSV is blind to it and <b>nothing warns "
      "you that it was never published</b>. The Python side shows the adjacent failure: "
      "<code>GHSA-x547-2835-q547</code> (CVE-2026-115557, CVSS 4.0 9.4) exists only in "
      "<code>unreviewed/</code> with <b>zero affected-package ranges</b>, which is why the UI 404s it and "
      "why no lockfile scan returns it."
    )
    applied.append(('ENRICHED', r['k'], 'repo-scoped vs global advisory mechanism measured'))

    for kind, key, note in applied:
        print("  %-9s %-52s %s" % (kind, key, note))
    print("corrections_105: %d rows touched" % len(applied))
    return L


# ---------------------------------------------------------------------------
# Rows the reuse_key advisory redirected: 5 of 6 drafted events and 2 of 5
# drafted patch rows were already on the board, two with IDENTICAL keys. They
# are enriched in place rather than given fresh slugs -- a new slug for a
# tracked story is precisely what makes `days` lie (2026-09-09).
# ---------------------------------------------------------------------------

ENRICH_EVENTS = {
 "redshift-rejects-tls-1-0-1-1-provisioned-and-serverless-and":
  " <span class='corr'>ENRICHED 10-27</span> <b>4 days out, and the date is now corroborated by a byte-level "
  "measurement rather than a re-read:</b> <code>behavior-changes.html</code> is <b>byte-identical</b> to "
  "yesterday's capture (markdown 35,561 / HTML 57,480), which is independent evidence nothing moved. The "
  "driver trap this row already names is <b>wider than JDBC and Python</b> &mdash; ODBC <b>2.3.0</b> (10-19) "
  "flipped default <code>sslmode</code> to <code>verify-full</code> too, so all three first-party drivers "
  "changed within eleven days, and all three changelogs warn that <b>a future release will fail the "
  "connection on a hostname mismatch unconditionally</b> rather than warn. Measured gap: grepping both "
  "variants of <code>behavior-changes.html</code> and <code>cluster-versions.html</code> for "
  "<code>sslmode</code>, <code>verify-full</code> and <code>verify-ca</code> returns <b>zero hits in all "
  "four</b> &mdash; the connection-behaviour change shipping in the same fortnight as the TLS cutover is "
  "documented only in three GitHub changelogs.",
 "genie-mcp-beta-endpoint-sunset-oct31":
  " <span class='corr'>ENRICHED 10-27</span> <b>4 days out, and two Databricks primary docs now contradict "
  "each other &mdash; with the newer one silent.</b> The built-in-MCP-services page, last updated <b>Oct 23</b> "
  "(a week after the Genie MCP page's Oct 16), still lists <code>/api/2.0/mcp/genie/{genie_space_id}</code> as "
  "a live &ldquo;Workspace MCP endpoint&rdquo; with OAuth scope <code>genie</code> under a Public Preview "
  "heading, carrying <b>no deprecation marker and no date</b>. Anyone tracking that page will not learn the "
  "path dies on Saturday. The same page marks only <code>/api/2.0/mcp/sql</code> as &ldquo;legacy&rdquo;, "
  "without calling it deprecated.",
 "play-target-api-36-extension-2026-11-01":
  " <span class='corr'>ENRICHED 10-27</span> <b>5 days out, and the omission is the finding:</b> Google's own "
  "&ldquo;Upcoming Android and Google Play deadlines&rdquo; timeline <b>does not list this deadline at all</b> "
  "&mdash; its only entries are 2026-08-26, 2026-09-30 and 2027-01-27. The page named &ldquo;upcoming "
  "deadlines&rdquo; is missing the nearest one, while the target-SDK requirements page (updated 2026-10-16) "
  "and Play Console help answer 11926878 agree verbatim on 2026-11-01. Also worth separating from the "
  "submission cliff: apps below <b>API 35</b> are not removed, they <b>stop being discoverable to new users</b> "
  "on devices running newer Android, while already-installed users keep access.",
 "containerd-22-eol-nov6":
  " <span class='corr'>ENRICHED 10-27</span> <b>10 days out, and the compatibility matrix now leaves a "
  "Kubernetes 1.36 cluster exactly ONE supported runtime after the 6th &mdash; the 2.3 LTS, which is the "
  "branch that has not merged the Go fix.</b> containerd's matrix gives 1.36 &rarr; <code>2.3.0+, 2.2.0+</code> "
  "and 1.37 &rarr; <code>2.4.0+, 2.3.0+</code>. Measured branch state today: <code>release/2.4</code>'s CI "
  "matrix reads <code>[1.26.10, 1.27.3]</code> while <b><code>release/2.2</code> and <code>release/2.3</code> "
  "both still read <code>[1.26.9]</code></b> &mdash; so on 2.4 the bump is merged and tagged in nothing, and on "
  "the LTS it is not merged at all. Nothing has shipped since 2026-10-13, six days before the fixed Go. A 1.34 "
  "cluster is worse: every runtime in its row is already EOL except 2.0's extension, explicitly scoped to "
  "&ldquo;usage with Kubernetes 1.33 via GKE&rdquo;.",
 "dotnet-8-9-eol-nov10":
  " <span class='corr'>ENRICHED 10-27</span> <b>14 days out, now inside the act-now window</b>, and confirmed "
  "identically by <code>releases-index.json</code> (<code>support-phase: maintenance</code>, "
  "<code>eol-date: 2026-11-10</code>) and the policy page. The sharpness is in what just happened: on "
  "<b>2026-10-25</b> an out-of-band wave patched all four lines at once &mdash; 8.0.33, 9.0.22, 10.0.14 and "
  "11.0.0-rc.3, each marked <code>latest-release-security: true</code> &mdash; and after the 10th, two of those "
  "four stop receiving that treatment. One upgrade detail that a runtime update does not cover: "
  "<b>NativeAOT binaries keep a linked Brotli decoder and must be republished</b> to clear CVE-2026-111497. "
  ".NET 11 is at RC3 and already in <code>go-live</code> support, but the supported target is .NET 10 LTS.",
}

ENRICH_PATCH = {
 "jdk-114820-no-vendor-build-keytool":
  " <span class='corr'>ENRICHED 10-27</span> <b>The two alerts are two sequential halves of ONE remediation, "
  "which is why the board kept reading a contradiction</b> &mdash; the 10-21 alert for CVE-2026-91403 "
  "&ldquo;distrusts the impacted <b>intermediate</b> CA certificates&rdquo; and lists the <b>base</b> builds "
  "as affected (8u511, 11.0.33, 17.0.21, 21.0.13, 25.0.5, 27.0.1); the 10-24 alert for CVE-2026-114820 "
  "&ldquo;<b>removes</b> the impacted <b>root</b> CA certificates&rdquo; and lists the <b><code>.0.2</code> BPR "
  "builds</b> as affected. So &ldquo;21.0.13.0.2 is fixed&rdquo; and &ldquo;21.0.13.0.2 is not fixed&rdquo; "
  "were both literally true. The fixed train is <b><code>.0.3</code></b>. <b>Measured today: no free OpenJDK "
  "build carries either half.</b> The root removal is <b>JDK-8395690</b>, committed to <code>openjdk/jdk</code> "
  "on 2026-10-24 (&minus;353 lines, deleting <code>comodoaaaca</code>, <code>emsigneccrootcag3</code>, "
  "<code>emsignrootcag1</code>, <code>emsignrootcag2</code>) &mdash; <b>mainline only</b>. "
  "<code>openjdk/jdk21u</code> and <code>openjdk/jdk25u</code> still carry all four files and their "
  "<code>cacerts</code> directory has not been touched since 2026-08-28. <b>Adoptium's newest GA names are "
  "<code>jdk-21.0.13+9</code>, <code>jdk-25.0.5+8</code>, <code>jdk-17.0.21+9</code></b> &mdash; the affected "
  "base builds. Two caveats on the remedy: <code>ops.java/emudhra</code>, cited as authoritative inside "
  "<b>both</b> Oracle alerts, returns <b>403</b>; and <code>openjdk.org/emudhra</code> instructs removing "
  "<b>four</b> roots, <b>two of which are not implicated</b> &mdash; certifi learned that by dropping four on "
  "10-18 and restoring the unaffected ones on 10-19.",
 "pgbouncer-scram-nonce-preauth-crash-19888":
  " <span class='corr'>ENRICHED 10-27</span> <b>The worst of the six is an authentication bypass, and the "
  "stranded population is wider than Debian.</b> CVE-2026-107350 (High, fixed 1.26.1) lets a second "
  "StartupMessage during SCRAM auth log a user in <b>as a different SCRAM user, administrators included</b> "
  "&mdash; affected from 1.17.0. Added to the stranded list measured today: <b>Microsoft's own Azure Linux 3 "
  "advisory records list <code>pgbouncer 1.25.2-1</code> affected by all six with no fixed version</b> "
  "(AZL-103430/103433/105063/108189/108192/108195), and <b>Ubuntu 24.04 LTS and 26.04 LTS</b> show no fixed "
  "version either; only Red Hat Hardened Images (1.26.1-1.hum1) and Debian 14 carry it. Meanwhile Azure's own "
  "concept doc asserts &ldquo;Automatic updates ensure that PgBouncer stays up to date with the latest "
  "features and security patches&rdquo; on the same page that states 1.25.2. The DoS sibling "
  "CVE-2026-107349's precondition is a parameter <b>Azure actually exposes</b>: it bites only when "
  "<code>ignore_startup_parameters</code> is non-empty and omits <code>options</code> &mdash; the shape Azure "
  "has historically recommended for <code>extra_float_digits</code>, so affected fleets are in the precondition "
  "rather than merely in range.",
}


def apply_enrichments(L):
    n = 0
    for sec, m in (("events", ENRICH_EVENTS), ("patch", ENRICH_PATCH)):
        for key, add in m.items():
            for r in L[sec]:
                if r.get('k') == key:
                    assert add.strip() not in r.get('t', ''), "already enriched: %s" % key
                    r['t'] = r['t'].rstrip() + add
                    n += 1
                    break
            else:
                raise SystemExit("enrich target missing: %s/%s" % (sec, key))
    print("enriched %d rows in place (reuse_key advisory redirected these from new slugs)" % n)
    return L
