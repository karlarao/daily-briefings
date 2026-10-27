#!/usr/bin/env python3
"""Edition-098 ledger corrections. Applied BEFORE any section is generated
(the 2026-09-14 build-order rule: a fix applied to the assembled HTML leaves the
rendered table generated from the pre-fix ledger).

Most corrections I drafted from today's briefs turned out to be ALREADY APPLIED
on the board -- the Snowflake allowlist row is already keyed as the Cortex-models
RBAC retirement, the Redshift ODBC EOS already reads 2026-12-31, Fabric already
carries the Spring-2027 milestone, and Percona is already RESOLVED. That is the
2026-09-17 lesson holding: check the board before drafting a correction. What
follows is only what genuinely moved.
"""
import json, re, sys

TODAY = "2026-10-20"
led = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "parent_ledger.json"))
applied, skipped = [], []


def patch_row(section, key, **changes):
    for r in led.get(section, []):
        if isinstance(r, dict) and r.get("k") == key:
            for f, v in changes.items():
                if callable(v):
                    new = v(r.get(f, ""))
                else:
                    new = v
                if new is None or new == r.get(f):
                    continue
                r[f] = new
            applied.append("%s/%s" % (section, key))
            return r
    skipped.append("%s/%s (NOT FOUND)" % (section, key))
    return None


# ---------------------------------------------------------------- 1 ---------
# CVE-2026-21962: the KEV clock advanced a day, and "tomorrow's CPU" is now
# today's. Today's Oracle lane adds the sharper fact: the CPU advisory itself
# had not published at 13:31 UTC, so the re-patch cannot even be planned yet.
patch_row(
    "patch", "cve-2026-21962-ohs-weblogic-kev",
    due="2026-08-27 (54d PAST DUE)",
    t=lambda s: (s.replace("RE-MEASURED 10-19", "RE-MEASURED 10-20")
                  .replace("53 days past due, and tomorrow's CPU does not retire it.",
                           "54 days past due, and today's CPU does not retire it "
                           "&mdash; nor can you read it yet.")
                  .replace("both products take NEW patches in the 2026-10-20 CPU",
                           "both products take NEW patches in today's CPU")
                 + " <span class='corr'>10-20</span> <b>And the advisory is not"
                   " readable yet:</b> at 13:31 UTC <code>cpuoct2026.html</code>"
                   " still served the <i>pre-release announcement</i> with <b>zero"
                   " CVE identifiers</b>, so the component-level patch numbers for"
                   " the re-patch do not exist publicly at the time of writing."),
)

# ---------------------------------------------------------------- 2 ---------
# containerd: the board already recorded the CVE ids (ed. 073) but still said
# they reached no database. Today's DevOps lane measured both landing in OSV on
# 2026-10-19 -- so the ~48-day blind window is CLOSED, which is the half of this
# story the board was still carrying as open.
patch_row(
    "patch", "containerd-checkpoint-restore",
    due="fixed 2.2.7/2.3.4 · in OSV 10-19 (blind window closed)",
    t=lambda s: s + (" <span class='corr'>CLOSED 10-20</span> <b>The scanner-blind"
                     " half of this row is now closed.</b> Both ids reached OSV on"
                     " <b>2026-10-19</b> &mdash; CVE-2026-95837 as"
                     " <code>GO-2026-6791</code> and the unpack sibling"
                     " CVE-2026-95838 as <code>GO-2026-6796</code> &mdash; so the"
                     " blind window ran <b>~48 days</b> from the 2026-09-01"
                     " publication and has ended. The remediation is unchanged and"
                     " still the hard part: <b>2.1.x gets no patch</b>, the feature"
                     " is removed outright in 2.4.0, and re-enabling restore via"
                     " <code>enable_experimental_restore_via_create</code>"
                     " reintroduces the flaw."),
)

# ---------------------------------------------------------------- 3 ---------
# Iceberg V4: the baseline Adaptive Metadata Tree spec MERGED 2026-10-14, which
# settles the manifest layout and makes v4 manifests Parquet-only. Still no date,
# and the row stays deliberately undated -- the spec itself says v4 "is under
# active development and has not been formally adopted."
patch_row(
    "events", "iceberg-v4-equality-delete-deprecation",
    t=lambda s: (s.replace("ADVANCED 10-19", "ADVANCED 10-20")
                 + " <span class='corr'>10-20</span> <b>The baseline AMT spec"
                   " MERGED on 2026-10-14</b> (18 +1, 9 binding, no dissent), and"
                   " Amogh Jahagirdar was explicit it is a vote to <i>merge</i>,"
                   " not to adopt. Consequences now in the spec: a <b>single root"
                   " manifest per snapshot</b>, root and leaf manifests in"
                   " <b>Parquet</b> where v1&ndash;v3 are Avro, and &mdash; the"
                   " part to plan around &mdash; <b>the v4 manifest schema is not"
                   " compatible with v1&ndash;v3</b>. A table upgraded from an"
                   " earlier version keeps its Avro manifests, but any new or"
                   " rewritten manifest must be a v4 Parquet manifest. The"
                   " <code>file</code> type passed on 10-19. <b>Still no date:</b>"
                   " the spec reads “Version 4 is under active development and"
                   " has not been formally adopted”, so this row stays"
                   " deliberately undated for a fourth consecutive edition."),
)

# ---------------------------------------------------------------- 4 ---------
# The Oracle CPU row: it fires TODAY, and the thing worth recording is that the
# advisory had not published when we measured it.
patch_row(
    "events", "oracle-cpu-oct-2026",
    t=lambda s: (s.replace("lands 2026-10-20 &mdash; 1 day &mdash;",
                           "lands TODAY, 2026-10-20 &mdash;")
                 + " <span class='corr'>10-20</span> <b>Measured today: the"
                   " advisory had not published.</b> At 13:31 UTC the page still"
                   " served the <b>pre-release announcement</b> with zero CVE"
                   " identifiers (Oracle normally publishes ~20:00 UTC). The"
                   " pre-release confirms <b>1,283 patches</b>, and the shape"
                   " inside our own stack is the story: <b>APEX takes two, both"
                   " remotely exploitable without authentication at CVSS 9.8</b>,"
                   " Java SE takes <b>55 with 49 remote-unauthenticated</b>, MySQL"
                   " takes <b>98 topping out at 9.8</b> &mdash; while the"
                   " <b>Database Server itself takes 13, max 8.8</b>. So an APEX"
                   " operator has a 9.8 unauthenticated flaw whose fixed version"
                   " cannot be read yet."),
)

json.dump(led, open("ledger_corrected.json", "w"), ensure_ascii=False)
print("applied:  %s" % ("\n          ".join(applied) or "-"))
print("NOT FOUND: %s" % ("; ".join(skipped) or "none"))
print("\nalso CHECKED and found ALREADY CORRECT on the board (no edit made):")
for k in ("snowflake-cortex-models-allowlist-rbac-nov18 (already keyed as the "
          "Cortex-models RBAC retirement, not a network allowlist)",
          "redshift-odbc-1x-eos-dec31 (already 2026-12-31, extension reflected)",
          "fabric-odbc-desktop-gateway-spring-2027 (4th milestone already carried)",
          "percona-psmdb-unpatched-auth-off (already RESOLVED 2026-09-22/23)"):
    print("  - %s" % k)
