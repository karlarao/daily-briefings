"""Hand-verified same-story fold for patch[] — edition 070.

Why a hand map and not a threshold (2026-09-11, measured): on this board true
duplicates score LOWER on token Jaccard than same-date pairs that must never
merge, because each duplicate is an independent re-summary sharing almost no
vocabulary with its twin. There is no threshold that keeps these and rejects
the rest. Every group below was read in full before folding; the survivor is
the row with the richest prose or the one re-asserted today, and every loser
key is preserved in the survivor's aliases[] so prior-edition diffs resolve.
"""
import json, sys
sys.path.insert(0, ".")
import ledger_surgery as LS

L = json.load(open("ledger_070.json"))
parent_patch = [dict(r) for r in L["patch"]]

GROUPS = {
 # survivor                              : losers
 "pg-28-cves-aug13": ["postgresql-28-cve-batch-2026-08-13", "postgres-aug-2026-28-cves",
                      "pg-aug-2026-28-cves", "postgres-28-cve-release",
                      "pg-cve-2026-14669-poc-public"],
 "go-module-checksum-verification-bypass-cve-2026-56864-cve-20": ["go-gosumdb-bypass-aug", "go-module-transparency-bypass"],
 "nextjs-critical-rce-aug25": ["nextjs-libheif-rce-2026-08-25", "nextjs-cve-2026-75604-windows-rce",
                               "nextjs-75604-unauth-rce-public-poc", "nextjs-aug-2026-criticals",
                               "nextjs-avif-windows-rce-1633", "next-js-critical-aug-26",
                               "next-js-unauthenticated-rce-via-avif-in-the-image-optimizati",
                               "next-js-unauthenticated-rce-on-windows-hosted-servers-cve-20"],
 "mongodb-cve-2026-18691-sasl": ["mongodb-18691-keyfile-rotate", "cve-2026-18691-mongo-intracluster"],
 "mongodb-bi-connector-cvss-95": ["mongodb-shipped-20-server-cves-at-once-topped-by-cve-2026-18", "mongodb-jul-aug-cve-waves",
                                  "mongodb-aug11-sep3-waves"],
 "spring-91-cves-aug20": ["spring-91-advisories-one-day"],
 "npm-chaindrop-shai-hulud-ongoing": ["shai-hulud-keyv-cacheable-worm", "chaindrop-npm-worm-444"],
 "context7-mcp-cve-2026-75130": ["context7-mcp-injection", "context7-mcp-prompt-injection",
                                 "context7-mcp-cve-75130-unfixed"],
 "mongodb-bi-connector-odbc-95": ["mongodb-bi-connector-odbc-cves"],
 "mongodb-82-no-fixed-version": ["mongodb-82-no-august-patch"],
 "doris-fe-http-auth-2026": ["doris-fe-http-auth"],
 "cve-2026-61211-dbms-cloud": ["cve-2026-61211-rdbms"],
 "oracle-cpu-oct-20-next": ["oracle-cpu-ru-oct20", "oracle-quarterly-cpu-next-rus"],
 "cspu-aug-2026-clusterware-96": ["oracle-cspu-aug-2026-clusterware"],
}

byk = {r["k"]: r for r in L["patch"]}
missing = [k for k in list(GROUPS) + [x for v in GROUPS.values() for x in v] if k not in byk]
if missing:
    raise SystemExit("fold map names keys not on the board: %s" % missing)

folded = 0
for surv, losers in GROUPS.items():
    s = byk[surv]
    al = set(s.get("aliases") or [])
    for lk in losers:
        al.add(lk)
        al.update(byk[lk].get("aliases") or [])
        # carry the loser's day count forward: the story is older than the
        # survivor's own key if a folded row saw it first.
        if byk[lk].get("first_seen") and (not s.get("first_seen") or byk[lk]["first_seen"] < s["first_seen"]):
            s["first_seen"] = byk[lk]["first_seen"]
        s["days"] = max(s.get("days") or 0, byk[lk].get("days") or 0)
        folded += 1
    s["aliases"] = sorted(al)

drop = {x for v in GROUPS.values() for x in v}
L["patch"] = [r for r in L["patch"] if r["k"] not in drop]

LS.assert_alias_safe(L["patch"], parent_patch, "patch")
json.dump(L, open("ledger_070.json", "w"), indent=1)
print("patch folded: %d rows merged into %d survivors" % (folded, len(GROUPS)))
print("patch: %d -> %d rows" % (len(parent_patch), len(L["patch"])))
print("assert_alias_safe: every parent key still present or aliased — OK")
