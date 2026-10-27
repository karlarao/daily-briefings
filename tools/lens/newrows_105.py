"""Edition 105 new rows. Drafted AFTER the correction pass (the 10-26 ordering:
rows today's briefs merely re-confirm get enriched in place, so only genuinely
new stories reach the drafting stage), and every one probed against same-date
parents with ledger_surgery.reuse_key's advisory before a slug is minted."""

EVENTS = [   # only php2shell survived the reuse_key advisory; 5 of 6 drafts were already on the board

  dict(k="php2shell-kev-due-oct29", date="2026-10-29",
       t="<b>CISA KEV remediation due for PHP <code>CVE-2026-109618</code> and <code>CVE-2026-109619</code> "
         "(&ldquo;php2shell&rdquo;)</b> &mdash; both unauthenticated RCE as the web-worker account, added to "
         "KEV <b>2026-10-26</b> with <code>forensicTriage: Yes</code> and BOD 26-04 obligations. Fixed only in "
         "<b>8.2.35 / 8.3.36 / 8.4.27 / 8.5.12</b> (all 10-21). <b>PHP 8.1 and earlier will never be "
         "patched</b> and CISA's own alert says to take those systems offline. Scoring trap: PHP's CNA rates "
         "both 9.2 with <code>AC:H</code>, NVD gives 109618 <b>9.8</b> at <code>AC:L</code> and 109619 "
         "<b>8.1</b> &mdash; one patch, three numbers. mod_php is confirmed-RCE for both; PHP-FPM is validated "
         "for 109619. <b>The same CVE-2026-109618 reaches the Oracle estate</b> as an out-of-band Security "
         "Alert against Oracle Secure Backup 19.1.0.0.0&ndash;19.1.0.1.0, which bundles PHP.",
       act="Patch to 8.2.35/8.3.36/8.4.27/8.5.12 today; take 8.1-and-older offline; apply the OSB alert patch separately."),
]

PATCH = [
  dict(k="php2shell-two-kev-rce-no-81-fix",
       due="<b>KEV due 2026-10-29</b> &middot; <b>no fix ever for 8.1 and earlier</b>",
       t="<b>PHP CVE-2026-109618 + CVE-2026-109619 (&ldquo;php2shell&rdquo;) &mdash; unauthenticated RCE as the "
         "web-worker account, in CISA KEV since 2026-10-26 with remediation due 2026-10-29 and "
         "<code>forensicTriage: Yes</code>.</b> Fixed in 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12 (10-21). "
         "<b>8.1 and older are never getting it</b>, and <b>8.2's own security support ends 2026-12-31</b>, so "
         "the oldest branch that got the patch has nine weeks left &mdash; anything on 8.2 at year end inherits "
         "the 8.1 situation. Remediation for the unpatched population is a <b>major-version upgrade, which is a "
         "project, not a patch</b>. Three scores for one patch: PHP's CNA 9.2 <code>AC:H</code> for both, NVD "
         "9.8 <code>AC:L</code> for 109618 and 8.1 <code>AC:H</code> for 109619 &mdash; and NVD claims a far "
         "wider floor than the project, with CPE ranges from <b>7.3.0</b> and <b>5.4.0</b> against advisories "
         "that speak only to 8.2+. A related session-upload-progress flaw, CVE-2026-115560, has <b>no release "
         "containing the fix yet</b> (&ldquo;will ship in the next regular release&rdquo;); the "
         "<code>session.upload_progress.enabled=0</code> mitigation must be set in <code>php.ini</code> or the "
         "FPM pool, not via <code>ini_set()</code>.",
       url="https://www.php.net/archive/2026.php"),
  dict(k="litellm-pipeline-signed-trojanized-artifacts",
       due="<b>repin cosign.pub to e82a3c6</b> &middot; <b>signature is not assurance</b>",
       t="<b>LiteLLM's own release pipeline built and signed the trojanized v1.107.0 artifacts, so "
         "<code>cosign verify</code> passes on the poisoned image against the pre-rotation key most "
         "deployments still pin.</b> The canonical 2026-10-23 post-mortem says the production run &ldquo;signed "
         "and published v1.107.0 built from the fork commit&rdquo;; the clean rebuilds moved the verification "
         "key to commit <code>e82a3c6</code> while 1.106.2 and earlier still document <code>0112e53</code>. "
         "Root cause: a master key committed to a public repo on 2025-05-27, force-pushed over but <b>never "
         "revoked</b>, used on 2026-10-10 against the Agent Platform API &mdash; one request returned the "
         "configuration of every managed agent, including an org owner's GitHub CLI OAuth token that was "
         "&ldquo;not associated with a service account and was not scoped down&rdquo; and <b>not subject to "
         "GitHub's super-user 2FA reauth flows</b>. That token overrode branch protection, a second satisfied "
         "the production approval gate, a third deleted the run records; the release source was repointed to a "
         "lookalike fork <code>Berri-AI/litellm</code> that <b>exists only on the attacker's account</b> (and "
         "404s today). <b>The official v1.107.0 git tag is clean</b> &mdash; the payload was injected by "
         "building from the fork, so every control held and the provenance of the <i>input</i> was never "
         "checked. <b>LiteLLM's own pin advice is wrong:</b> it says pin 1.106.2, which documents the old key. "
         "Use a 10-24/10-25 release.",
       url="https://docs.litellm.ai/blog/security-incident-oct-21-2026-attack-chain"),
  dict(k="snowflake-revocation-off-by-default-fleetwide",
       due="<b>CRL ships DISABLED</b> &middot; <b>set it yourself</b>",
       t="<b>Certificate revocation checking is now OFF by default on every Snowflake client line, and the "
         "replacement is no better.</b> Measured per driver: JDBC 4.4.0, Go 2.3.0, Python 4.8.0 and Node.js "
         "3.4.0 (all 09-30) plus ODBC 3.22.0 (10-23) all turned OCSP off by default; ODBC 4.x and Python 5.x "
         "<b>remove OCSP entirely</b> in favour of CRL, and <b>CRL is <code>DISABLED</code> by default</b>. "
         "Node.js has announced OCSP removal in its next major. <b>The sequence is the point:</b> "
         "CVE-2026-85525 was a bug that let a <i>revoked</i> certificate be accepted; the fix repaired OCSP "
         "validation; the next release of every driver then stopped checking revocation at all &mdash; reaching "
         "the same outcome by another route, in the same month a real intermediate-CA key compromise made "
         "revocation matter. Compounding it, the <b>RUSTSEC-2026-0382 distrust shipped only in Python connector "
         "5.1.0 and ODBC 4.2.0</b>; Python <b>4.8.1</b> (10-26, five days later) carries only a certifi bump, "
         "and Snowpark, Snowflake ML, SQLAlchemy and the CLI all still require connector <b>&lt; 5.0.0</b>. "
         "JDBC, Go and Node.js have had <b>no release at all since the disclosure</b>.",
       url="https://docs.snowflake.com/en/release-notes/clients-drivers/jdbc-2026"),
]
