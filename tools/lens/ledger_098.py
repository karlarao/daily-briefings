#!/usr/bin/env python3
"""Edition-098 ledger: enrich existing rows, add only genuinely-new ones, retire
past-dated events.

The probe result is the headline: of ~12 rows I drafted from today's briefs, the
board already tracked Go's CONNECT desync set INCLUDING the x/net split, Argo CD's
four 9.9s with no v2 fix, Next.js's 10-14 pair with no 13.x/14.x fix, pgvector on
managed Postgres, Angular v19's permanent EOL, NVIDIA AIStore's two-major-hop
remediation, Node.js's 10-21 releases and LiteLLM's unnumbered 9.9. Enrich, do not
mint -- a fresh slug for a tracked story is exactly what makes `days` lie.
"""
import json, datetime

TODAY = "2026-10-20"
led = json.load(open("ledger_corrected.json"))
log = []


def enrich(section, key, add):
    for r in led[section]:
        if isinstance(r, dict) and r.get("k") == key:
            r["t"] = r.get("t", "") + add
            log.append("ENRICHED %s/%s" % (section, key))
            return True
    log.append("!! MISSING %s/%s" % (section, key))
    return False


# --- enrich two tracked rows rather than minting near-duplicate slugs ---------
enrich("patch", "pgbouncer-scram-nonce-preauth-crash-19888",
       " <span class='corr'>WORSE 10-20</span> <b>1.26.1 fixes three CVEs and the"
       " new one is an auth bypass, not a crash.</b> <b>CVE-2026-107350 (CVSS"
       " 8.8)</b> affects <b>every build from 1.17.0 through 1.26.0</b>: a second"
       " StartupMessage sent during SCRAM auth against a non-existent database is"
       " not rejected and <i>switches the user being logged in as</i>, so a client"
       " holding any one <code>auth_file</code> user's password becomes any other"
       " SCRAM user &mdash; including PgBouncer admins and backend superusers."
       " Alongside it CVE-2026-107349 (7.5, unauthenticated infinite loop) and"
       " CVE-2026-107348 (5.9). The containment story is unchanged and is why this"
       " row stays open: <b>Azure's service-managed pooler is still 1.25.2</b>,"
       " inside the affected range, and you cannot upgrade it &mdash; the only"
       " remedy is to move off <code>:6432</code> to a self-managed 1.26.1 or"
       " firewall it. A pooler version is now a credential-boundary fact.")

enrich("patch", "starrocks-80346-drop-mv-authz-no-fix",
       " <span class='corr'>NEW MECHANISM 10-20</span> <b>A sixth kind of"
       " no-reachable-fix: patched in git, never released as a binary.</b> Today's"
       " lane diffed the poms rather than trusting the notes. Released tag"
       " <b>3.5.21</b> &mdash; 53 days old and the newest on the branch &mdash;"
       " declares Apache Ranger <b>2.8.0</b>, Bouncy Castle <b>1.84</b> and"
       " httpclient5 <b>5.4.3</b>, while <code>branch-3.5</code> HEAD already"
       " declares <b>2.9.0 / 1.86 / 5.6.4</b>. So the fixes for"
       " <b>CVE-2026-42537</b> (Ranger RCE via JDBC URL injection, <b>9.8,"
       " unauthenticated</b>) and <b>CVE-2026-71290</b> (httpclient5 TLS hostname"
       " verification <i>silently</i> disabled in default config, <b>9.1</b>) are"
       " merged and unreleased. A reviewer reading the branch concludes"
       " “fixed”; a scanner reading the released artifact's pom finds the"
       " vulnerable versions; and no advisory names StarRocks at all. Remedy: build"
       " from <code>branch-3.5</code> or move to <b>4.0.16</b>. The only reliable"
       " check is to diff the tag's pom against the branch's.")

# --- genuinely new rows -------------------------------------------------------
NEW_PATCH = [
  dict(k="snowflake-86597-creds-in-driver-logs",
       due="patched 2026-09-03, disclosed 2026-10-05 · NO fix for gosnowflake v1",
       url="https://github.com/snowflakedb/snowflake-connector-nodejs/security/advisories/GHSA-qqj6-54q6-cxv6",
       t="<b>Six Snowflake drivers wrote authentication tokens, query-result"
         " encryption keys, pre-signed storage URLs and SAML assertions into"
         " diagnostic logs (CVE-2026-86597).</b> Anyone with read access to the log"
         " destination &mdash; a filesystem, an aggregator, or a <b>CI artifact"
         " store</b> &mdash; gets usable credentials. Two things make this worse"
         " than its ~6.5 score. <b>Patching does not undo it:</b> the remediation"
         " is to rotate every token, key and SAML artefact that could have been"
         " logged and purge the log and artifact stores. And <b>the fixes shipped"
         " silently on 2026-09-03 while the advisory only published 2026-10-05</b>"
         " &mdash; a 32-day window in which operators had no reason to rotate."
         " Fixed: Python 4.7.3, Go <b>v2</b> 2.2.0, JDBC 4.3.4, Node 3.3.0, ODBC"
         " 3.20.0, PHP PDO 4.2.0. <b>There is no fix for <code>gosnowflake</code>"
         " v1</b>: OSV marks 1.19.1 last-affected with no fixed event, and"
         " Snowflake's support policy ships security updates “only on the"
         " latest client versions” &mdash; so the remedy is a breaking"
         " <code>/v2</code> module-path migration. Note also that meeting"
         " Snowflake's own enforced ODBC minimum (3.5.0) still leaves you"
         " vulnerable; the fix is 3.20.0."),
  dict(k="oracle-apex-two-98-unauth-oct-cpu",
       due="2026-10-20 · fixed version NOT PUBLISHED at time of writing",
       url="https://www.oracle.com/security-alerts/cpuoct2026.html",
       t="<b>OURS, and the sharpest thing in today's CPU: Oracle APEX takes two"
         " CVEs that are remotely exploitable <i>without authentication</i> at"
         " CVSS 9.8</b>, affecting 26.1.0&ndash;26.1.4 plus the 24.1.x and 24.2.x"
         " lines. The operational problem is that <b>you cannot act on it yet</b>:"
         " at 13:31 UTC <code>cpuoct2026.html</code> still served the pre-release"
         " announcement with zero CVE identifiers, so the fixed version and patch"
         " numbers are not published. For scale, the Database Server itself takes"
         " <b>13 patches at max 8.8</b> in the same CPU &mdash; the database kernel"
         " is now a rounding error in Oracle's own CVE volume, and the exposure in"
         " an Oracle estate sits in the web and tooling tiers."),
  dict(k="mcp-ts-111768-optin-fix-off-by-default",
       due="patched 1.32.0 / 2.3.0 · fix is OPT-IN and OFF by default",
       url="https://github.com/modelcontextprotocol/typescript-sdk/security/advisories/GHSA-46jr-4wx8-v453",
       t="<b>The MCP SDKs shipped twelve advisories in 30 days, and the defining"
         " property is that upgrading is not the fix.</b> <b>CVE-2026-111768</b>"
         " (High, 7.5): one request under the default 4 MiB body limit can OOM-kill"
         " the Node process because the SDK bounded neither array elements nor"
         " object keys during validation. The patched releases add"
         " <code>maxToolInputElements</code> &mdash; <b>off by default</b> &mdash;"
         " so you must set it on <code>McpServer</code> <i>and</i> lower"
         " <code>maxRequestBodySize</code>, since the new option covers only tool"
         " arguments. <b>Five of six TypeScript advisories and the Python OAuth one"
         " need a second, separate action after the version bump</b>, and the Python"
         " case is the worst: omitting <code>issuer=</code> emits only a"
         " <code>DeprecationWarning</code>, <b>which Python hides by default</b>, so"
         " the insecure path is silent until 3.0 makes it an error. “We are on"
         " the patched version” has become a meaningless statement; a patch"
         " policy now needs a configuration assertion beside the version check."),
  dict(k="sveltekit-2-security-patch-is-the-major",
       due="no fix on 2.x — fixed only in the breaking 3.0.0",
       url="https://github.com/sveltejs/kit/security/advisories/GHSA-prjg-x2qj-wj3g",
       t="<b>SvelteKit 2's security patch <i>is</i> a major-version migration.</b>"
         " Four advisories published 2026-10-05 all declare affected"
         " <code>&lt; 3.0.0</code> and patched <b>3.0.0</b>. SvelteKit 2's last"
         " release is <b>2.70.3 (2026-08-18)</b>; there is no <code>2x</code>"
         " dist-tag and no backport. And 3.0.0 drags a language major with it:"
         " Node 22.17, Vite 8.0.12, Svelte 5.57.1 and <b>TypeScript 6</b>, with"
         " <code>svelte.config.js</code> gone, <code>$lib</code> replaced by a"
         " <code>#lib</code> alias, and <code>$app/stores</code> removed. That is a"
         " multi-day migration priced as a patch. Storybook, which backported a"
         " Critical to four lines in a single day, is the proof this is maintainer"
         " policy rather than technical necessity."),
]

NEW_EVENTS = [
  dict(k="fabric-foundry-custom-tool-retire-nov6", date="2026-11-06",
       url="https://community.fabric.microsoft.com/t5/Fabric-Updates-Blog/Retiring-the-Fabric-data-agent-custom-tool-in-Microsoft-Foundry/ba-p/5374418",
       act="Migrate every Foundry agent off the Fabric data-agent custom tool onto the Fabric IQ (OneLake Catalog) tool, and rewrite the agent instructions to name each data agent.",
       t="<b>The Fabric data-agent <i>custom-tool</i> integration in Microsoft"
         " Foundry stops being supported on 2026-11-06</b> &mdash; the only"
         " day-precise Fabric date in the window. Migration is a real change, not a"
         " rename: publish the data agent with a detailed description, add the"
         " Fabric IQ tool, select the agent from the catalog, <b>rewrite the Foundry"
         " agent's instructions to name each data agent</b>, remove the old custom"
         " tool and retest; code-based integrations need"
         " <code>azure-ai-projects&gt;=2.2.0</code> and a new"
         " <code>RemoteTool</code> connection pointing at the agent's <b>MCP"
         " endpoint</b>. Upside: multiple data agents per Foundry agent, where the"
         " old path allowed exactly one. Worth noting for the affordance register"
         " that Microsoft's own migration sample sets"
         " <code>require_approval=\"never\"</code>."),
  dict(k="supabase-tls12-cbc-ciphers-nov10", date="2026-11-10",
       url="https://supabase.com/changelog",
       act="Confirm every client reaching a Supabase project HTTP API negotiates a modern TLS 1.2 suite; a client without one simply fails to connect.",
       t="<b>Supabase disables a subset of TLS 1.2 CBC ciphers on project HTTP APIs"
         " on 2026-11-10.</b> Clients without modern TLS support will <i>fail to"
         " connect</i> rather than degrade. Separately on the same board: the Hono,"
         " H3, Elysia and NestJS adapters in <code>@supabase/server</code> are"
         " deprecated and <b>removed 2026-12-01</b>."),
]

NEW_BENCH = [
  dict(k="mlperf-endpoints-v1-provisioned-power", date="2026-10-13",
       url="https://mlcommons.org/2026/10/open-submissions-endpoints-v1-0/",
       t="<b>MLPerf Endpoints v1.0 opened for submissions on 2026-10-13 and makes"
         " <i>provisioned power</i> a mandatory metric &mdash; a first for the"
         " MLPerf family.</b> The system under test is a <b>URL</b>, so hardware"
         " vendors, hyperscalers, neoclouds and managed API providers land on the"
         " same axes: concurrency, interactivity (tokens/s/user), system throughput,"
         " <b>TTFT P90</b> and provisioned power, swept across load and plotted as a"
         " Pareto frontier. Submissions are <b>rolling</b> rather than round-based,"
         " still peer-reviewed and audited. <b>First results expected November"
         " 2026</b> (month precision). This partially answers this board's own"
         " standing gap row: it will be the first apples-to-apples"
         " perf-per-provisioned-watt figure citable in a procurement argument, and"
         " the first thing capable of separating the three-way memory split &mdash;"
         " Maia 300 at 288 GB/18 TB/s, Intel's D-Series at 480 GB/1.5 TB/s, and HBF"
         " at roughly half HBM bandwidth with ~14x the capacity."),
]

for r in NEW_PATCH:
    led["patch"].append(r); log.append("NEW patch/%s" % r["k"])
for r in NEW_EVENTS:
    led["events"].append(r); log.append("NEW events/%s" % r["k"])
for r in NEW_BENCH:
    led["benchmarks"].append(r); log.append("NEW benchmarks/%s" % r["k"])

# --- retire events whose date has passed (keep them in retired_events) --------
def d(s):
    try: return datetime.date.fromisoformat(str(s)[:10])
    except Exception: return None

t0 = d(TODAY)
keep, retired = [], []
for r in led["events"]:
    dd = d(r.get("date"))
    if dd is not None and dd < t0:
        rr = dict(r); rr["retired"] = TODAY
        retired.append(rr)
    else:
        keep.append(r)
led["events"] = keep
# retired_events is a list of FULL ROW DICTS (2026-10-19 lesson) -- 67 of 69
# existing entries are dicts; appending bare key strings crashes set() in the
# alias-aware regression check.
led.setdefault("retired_events", []).extend(retired)
log.append("RETIRED %d past-dated events: %s" % (len(retired), ", ".join(r["k"] for r in retired)))

json.dump(led, open("ledger_098.json", "w"), ensure_ascii=False)
print("\n".join(log))
print("\nsection sizes now:")
for k in ("events","patch","claims","ownclaims","promises","gaps","benchmarks","skills","buildbets","retired_events"):
    print("  %-16s %d" % (k, len(led.get(k, []))))
