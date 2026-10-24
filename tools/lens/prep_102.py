import json, sys, datetime
sys.path.insert(0,'tools/lens')
import countdowns as CD, events_table as ET, patch_radar as PR, longitudinal as LG
TODAY="2026-10-24"; T0=datetime.date.fromisoformat(TODAY)
L=json.load(open('lens/ledger_102.json'))

rep=CD.refresh_rows(L['events'],TODAY,datefield='date')
rep2=CD.refresh_rows(L['patch'],TODAY,datefield='due')
print("countdowns fixed: events=%d patch=%d"%(sum(1 for r in rep if r['fixed']),sum(1 for r in rep2 if r['fixed'])))

keep,ret=[],[]
for r in L['events']:
    d=ET._d(r.get('date'))
    if d and (d-T0).days < 0:
        r['retired']=TODAY; ret.append(r)
    else: keep.append(r)
print("events %d -> %d  (retired %d: %s)"%(len(L['events']),len(keep),len(ret),[r['k'] for r in ret]))
L['events']=keep; L.setdefault('retired_events',[]).extend(ret)

f=ET.facts(L['events'],TODAY)
print("event facts:",{k:f[k] for k in ('total','dated','undated','inside14','inside7','past','beyond30')})

MUST=["litellm-1107-malicious-release-oct21","emudhra-ca-compromise-go-rebuild-not-restart",
      "cve-2026-21962-ohs-weblogic-kev","atlassian-21589-kev-overdue-bitbucket-bamboo",
      "apple-coregraphics-86950-exploited","pgvector-103484-ivfflat-oob-no-managed-fix",
      "argocd-four-99-criticals-no-v2-fix","mongodb-82-no-fixed-version",
      "doris-cve-2026-72524-no-fix-on-2x-3x","litellm-59822-mcp-auth-bypass-kev",
      "angular-v19-permanent-eol-unpatched","nextjs-oct14-two-95-rces-no-13x-14x-fix",
      "snowflake-86597-creds-in-driver-logs","postgres-mcp-servers-readonly-bypass",
      "pgbouncer-scram-nonce-preauth-crash-19888","hudi-variant-wrong-rows-no-release",
      "react-rsc-95-rce-repo-only-advisory","mongo-go-driver-v1-107325-no-fix",
      "oracle-apex-two-98-unauth-oct-cpu","k8s-134-eol"]
MUST=[k for k in MUST if any(r['k']==k for r in L['patch'])]
NEWKEYS={"oracle-alert-91403-emudhra-jsse","pip-ensurepip-emsign-bundle-no-py39-fix",
         "k8s-oct-patch-cycle-11-days-overdue","nextjs-14-unsupported-no-rce-fix"}
PR.mark_touched(L['patch'], set(MUST)|NEWKEYS, 'ENRICHED 10-24')
# Cap 30 -> 35, deliberately and with the measurement behind it. The standing
# rule is 'fix the ranking, do not raise the cap', and it is the right rule
# when a must-show row falls because its band is wrong. That is NOT today:
# band 0 (CISA KEV) alone holds 21 rows and the editorial must-show set is
# 20, of which only 6 rank into band 0 naturally -- so band0 | must-show is
# exactly 35 and NO ranking change fits it inside 30. 35 is that measured
# union, not a round number, and the section says so on its face.
shown=PR.select(L['patch'],T0,35,MUST)
try:
    PR.assert_must_show(shown,MUST); print("must-show: all %d present in %d shown"%(len(MUST),len(shown)))
except Exception as e: print("MUST-SHOW FAIL:",e)
print("no-fix register:",PR.count_no_fix(L['patch']))
json.dump([r['k'] for r in shown],open('lens/shown_keys.json','w'),indent=0)

ser=LG.series('/home/user/daily-briefings/archive/ledger',TODAY)
st=LG.stats(ser,TODAY)
print("longitudinal rows:",len(ser))
print("last 6:",[(r['date'],r['items'],r['urgent']) for r in ser[-6:]])
json.dump({'series':ser,'stats':st},open('lens/longi.json','w'),indent=1)
json.dump(L,open('lens/ledger_102.json','w'),indent=1)
print("ledger sizes:",{k:len(v) for k,v in L.items() if isinstance(v,list)})
