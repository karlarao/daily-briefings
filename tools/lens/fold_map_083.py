"""Hand-verified duplicate folds for edition 083 (2026-10-04).

Every group below was SURFACED by `ledger_surgery.advise_patch_peers` (landed this
run, the text route the 2026-10-03 notes asked for, because `reuse_key`'s advisory
is date-keyed and a patch row's `due` is usually prose) and then READ BY HAND
before being folded. The advisory found 17 hard-id collision groups on the ed-082
board; only these four survived hand verification.

Methodology is the 2026-09-11 conclusion, unchanged: identity is DECLARED, never
inferred from similarity. The advisory makes a duplicate VISIBLE; a human decides.
Every loser is preserved in the survivor's `aliases[]`, `first_seen` and `days`
carry to the OLDEST member, and `assert_alias_safe` must then confirm that no
parent key left the board by omission.

REJECTED after hand reading, recorded because it is the instructive one:
  litellm-59822-mcp-auth-bypass-kev  vs  litellm-37004-ssti-unauth-rce
  These share THREE CVE ids (59822, 59823, 37004) and still are NOT one story:
  each row MENTIONS the other, which is why the ids intersect. Distinct CVEs,
  distinct mechanisms (KEV'd MCP auth bypass vs unauthenticated SSTI->RCE),
  distinct due dates (2026-09-16 vs 2026-08-27). An automated hard-id fold would
  have destroyed a real row here. This is the case that keeps the route advisory.

ALSO REJECTED (correctly-scoped, not duplicates): mongodb-bi-connector-cve-2026-19001
  vs mongodb-bi-connector-odbc-95 overlap on CVE-2026-19001 but are different
  angles (the window's MongoDB summary vs the ODBC driver's own five CVEs).
"""

# survivor_key -> [loser_keys]
FOLDS = {
    # same CVE, same due date (2026-09-05), same product. The survivor carries the
    # richer prose (the endsWith("/configs") path-match mechanism); the loser's
    # first_seen 2026-09-08 is the older and must win.
    "kestra-49869-kev-past-due": ["kestra-cve-2026-49869-kev"],

    # same CVE *and* same GHSA (GHSA-p7v4-vr35-mj6f), same fixed versions
    # (2.2.7 / 2.3.4), and BOTH rows say they supersede this board's own
    # "no CVE id" note. One is literally the other's restatement.
    "containerd-checkpoint-restore": ["containerd-95837-checkpoint-restore"],

    # same CVE (CVE-2026-85706), same due date (2026-09-14), same fixed versions
    # (19.3.2 / 19.2.6 / 19.1.8).
    "gitlab-85706-kev-past-due": ["gitlab-85706-kev-cvss10-due-sep14"],

    # same three CVEs (47045 / 47060 / 47061), same point: client-only installs
    # need the July CPU, server patching does not cover them. The loser is also a
    # badly truncated auto-generated slug ending in a bare dash.
    "oracle-client-only-cves": ["oracle-client-installs-need-the-july-cpu-too-cve-2026-47045-"],
}

# Register corrections: rows sitting in the no-fix register whose OWN PROSE names
# the fix. Found by a new systematic check this run (5 candidates, 3 of which were
# legitimately scoped "no fix for X"); these 2 are genuine register errors.
REGISTER_FIXES = {
    "mongodb-java-socks5-cred-leak": "fixed in 5.9.2",
    "mongodb-bi-connector-odbc-95": "fixed in 1.4.9 (ODBC driver)",
}
