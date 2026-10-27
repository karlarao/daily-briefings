"""Edition 101 new rows. Every drafted row is probed against same-date parents
first (the reuse_key advisory, 2026-09-11): five drafted rows were dropped
because the board already carried them."""
import json, sys
sys.path.insert(0, 'tools/lens')
import ledger_surgery as LS

TODAY = "2026-10-23"
L = json.load(open('lens/ledger_101.json'))
existing = {r['k'] for ln in L if isinstance(L[ln], list) for r in L[ln]}

NEW_EVENTS = [
 dict(k="emsign-root-removal-chrome-oct27", date="2026-10-27",
      act="Reissue any certificate chaining to <code>emSign ECC Root CA - G3</code> from another hierarchy, and bump every bundled trust store independently.",
      t=("<b>Chrome removes <code>emSign ECC Root CA - G3</code> from the Chrome Root Store for all "
         "devices</b> after eight eMudhra intermediate CA private keys proved recoverable from their "
         "public certificates (weak generation entropy, reported 2026-10-17, CRLSet-blocked within two "
         "hours). Google says some legitimate certificates will stop working and tells operators to "
         "replace them immediately; eMudhra's estimate to Mozilla is ~30,000 certificates. Mozilla "
         "removed the root in NSS 3.131.1 on 10-20. The same clock lands on Kubernetes 1.34's EOL.")),
 dict(k="rds-postgres-force-upgrade-oct31", date="2026-10-31",
      act="Pick your target minor and schedule it this week, or run a blue/green &mdash; RDS will upgrade you with downtime regardless of the auto-minor setting.",
      t=("<b>RDS for PostgreSQL end of standard support for eight minor versions</b> &mdash; 17.6, "
         "17.5, 16.10, 16.9, 15.14, 15.13, 14.19 and 14.18. Why it requires action rather than just "
         "noting: AWS states it &ldquo;will apply a minor version upgrade <b>even if you haven't "
         "enabled the Auto minor version upgrade option</b>&rdquo; and that &ldquo;automatic upgrades "
         "incur downtime&rdquo;. <b>Correction to the carried count:</b> the &ldquo;14 versions&rdquo; "
         "figure was two tables added together &mdash; 8 standard-support minors plus 6 Extended "
         "Support builds (12.22-rds.* and 11.22-rds.*) whose extended support ends the same day.")),
 dict(k="play-billing-library-7-cliff-nov1", date="2026-11-01",
      act="Confirm Play Console &rarr; Policy status is clear for Billing Library, and migrate to PBL 8+ before you need to ship.",
      t=("<b>Google Play Billing Library 7 extension expires</b> &mdash; after it, new apps and "
         "updates must use PBL 8 or later. Kept as a row distinct from the target-API-36 cliff that "
         "shares this date, on the 09-13 lesson that two deadlines sharing a month are not one "
         "deadline. Enforcement is a <b>publishing</b> gate, not a runtime one: already-installed apps "
         "on PBL 7 keep transacting, so the symptom is a blocked release rather than broken billing. "
         "Google's own page is internally inconsistent &mdash; the banner says &ldquo;version 8 or "
         "later&rdquo; while the table gives v8 its own 2027-08-31 deadline.")),
]

NEW_PATCH = [
 dict(k="atlassian-21589-kev-overdue-bitbucket-bamboo",
      due="KEV due 2026-10-18 (<b>5d PAST DUE</b>) &middot; <code>forensicTriage: Yes</code>",
      t=("<b>CVE-2026-21589, unauthenticated arbitrary file access, is in CISA KEV five days past due "
         "and it covers CI/CD infrastructure</b> &mdash; Bitbucket Data Center and Bamboo Data Center, "
         "added 2026-10-15 with forensic-triage obligations under BOD 26-04, so detection work is "
         "required even after patching. <b>Atlassian scores it 9.3 under CVSS 4.0 while NVD's 3.1 is "
         "7.5</b> &mdash; a 1.8-point gap across which a &ldquo;block Criticals&rdquo; gate flips. "
         "Fixed: Bitbucket DC 9.4.26 / 10.2.8 / 10.5.1, Bamboo DC 10.2.24 / 12.1.12, Crucible and "
         "Fisheye 4.9.15. No binary patches &mdash; maintenance releases only.")),
 dict(k="hudi-variant-wrong-rows-no-release",
      due="<b>fix merged to 1.2.x, carried by NO release</b> &middot; triggering config ON by default",
      t=("<b>Apache Hudi 1.2.0 and 1.2.1 silently return wrong rows</b> for nullable VARIANT columns on "
         "Merge-on-Read snapshot reads under Spark 4.1, and the vendor states the fix is on the 1.2.x "
         "branch but &ldquo;no release carries that fix yet&rdquo;. Four symptoms: a top-level VARIANT "
         "set to null by an update reads back as a struct of nulls so <code>v IS NULL</code> misses the "
         "row; a VARIANT nested in a struct can <b>crash the executor JVM</b>; multi-path extraction "
         "throws <code>NegativeArraySizeException</code>; and a VARIANT added by <code>ALTER TABLE</code> "
         "cannot be read from files written before it. <b>The first raises no error</b>, and "
         "<code>spark.sql.variant.pushVariantIntoScan</code> is on by default in Spark 4.1 &mdash; set "
         "it false. Carried here as a no-reachable-fix row because a silent wrong answer is at least as "
         "actionable as a CVE.")),
 dict(k="react-rsc-95-rce-repo-only-advisory",
      due="fixed 19.0.9 / 19.1.10 / 19.2.9 / 19.3.1 &middot; <b>invisible to every scanner, 9 days on</b>",
      t=("<b>A CVSS 9.5 unauthenticated RCE in React Server Components that no scanner will tell you "
         "about</b> &mdash; GHSA-xqc2-xf4c-x3h3, published 2026-10-14 as a repository advisory on "
         "<code>facebook/react</code> with <b>no CVE assigned</b>. Measured today: "
         "<code>github.com/advisories/&lt;id&gt;</code> <b>404</b>, "
         "<code>api.osv.dev/v1/vulns/&lt;id&gt;</code> <b>404</b>, and the npm bulk advisory endpoint "
         "returns <b>zero</b> advisories for <code>react-server-dom-webpack@19.3.0</code> and its "
         "<code>-turbopack</code>/<code>-parcel</code> siblings. The four patch releases say only "
         "&ldquo;React Server Components: Improve transport protocol&rdquo;. The contrast is the "
         "finding: the Next.js advisories published the same day <i>did</i> enter both databases on "
         "10-22. Bump by hand. The December-2025 RSC RCE (CVE-2025-55182) is in KEV, so this family's "
         "exploitation history is not hypothetical.")),
 dict(k="gosnowflake-v1-patched-version-none",
      due="<b>patched version published as the literal string &ldquo;None&rdquo;</b> &middot; /v2 module migration only",
      t=("<b>Snowflake publishes its own Go v1 driver's fix for CVE-2026-86597 as &ldquo;None&rdquo;, "
         "and its platform still accepts that driver.</b> Four sources agree there is no v1 fix: the "
         "GitHub advisory table says patched &ldquo;None&rdquo;; GO-2026-6665 carries "
         "<code>introduced: 0</code> with <b>no <code>fixed</code> and no <code>last_affected</code> at "
         "all</b>; the GHSA range says <code>last_affected: 1.19.1</code> (the newest v1 release); and "
         "the prose names only v2.2.0. The leak is serious even at CVSS 6.5 &mdash; auth tokens, "
         "<b>query-result master keys</b>, pre-signed URLs and SAML assertions written to diagnostic "
         "logs. The v1 line has had no release since 2026-04-08 while Snowflake's client policy still "
         "sets the Go floor at 1.11.2. Unusually, this one is <b>not</b> scanner-blind: govulncheck and "
         "osv-scanner both flag it forever, with no version that clears it.")),
 dict(k="mongo-go-driver-v1-107325-no-fix",
      due="<b>no v1 backport</b> &middot; fixed only in v2.9.2, a different module path",
      t=("<b>mongo-go-driver v1 has no fix for CVE-2026-107325</b> (CVSS 4.0 8.2 High / 3.1 5.9 Medium), "
         "an unauthenticated panic-DoS. MongoDB lists &ldquo;1.1.0 to 1.17.10 and prior&rdquo; affected "
         "and names only 2.9.2 as fixed; GODRIVER-4136 shows no v1 backport and the newest v1 release is "
         "1.17.10 (2026-09-10). Moving off it means <code>go.mongodb.org/mongo-driver</code> &rarr; "
         "<code>/v2</code> &mdash; a migration, not a bump. Honest scoping: the trigger is narrow, "
         "requiring the app to call <code>bson.RawArray.Validate</code> or "
         "<code>bsoncore.Array.Validate</code> on externally supplied raw BSON; the normal wire path is "
         "not affected. No v1 end-of-support date is published.")),
]

for row in NEW_EVENTS:
    adv = LS.reuse_key(row, L['events'], 'date', 'events')
    print("EVENT  %-44s advisory: %s" % (row['k'], adv or "no same-date parent"))
for row in NEW_PATCH:
    print("PATCH  %-44s" % row['k'])

for row in NEW_EVENTS:
    assert row['k'] not in existing, row['k']
    row.update(first_seen=TODAY, last_seen=TODAY, days=1, aliases=[])
    L['events'].append(row)
for row in NEW_PATCH:
    assert row['k'] not in existing, row['k']
    row.update(first_seen=TODAY, last_seen=TODAY, days=1, aliases=[])
    L['patch'].append(row)

json.dump(L, open('lens/ledger_101.json','w'), indent=1)
print("\nsizes:", {k:len(v) for k,v in L.items() if isinstance(v,list)})
