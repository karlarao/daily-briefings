import json, sys, datetime
sys.path.insert(0,'tools/lens')
import countdowns as CD, events_table as ET, patch_radar as PR, longitudinal as LG
TODAY="2026-10-23"; T0=datetime.date.fromisoformat(TODAY)
L=json.load(open('lens/ledger_101.json'))

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
      "cve-2026-21962-ohs-weblogic-kev","oracle-apex-two-98-unauth-oct-cpu",
      "pgvector-103484-ivfflat-oob-no-managed-fix","argocd-four-99-criticals-no-v2-fix",
      "apple-coregraphics-86950-exploited","mongodb-82-no-fixed-version",
      "atlassian-21589-kev-overdue-bitbucket-bamboo","hudi-variant-wrong-rows-no-release",
      "react-rsc-95-rce-repo-only-advisory","starrocks-cve-trio-4014",
      "doris-cve-2026-72524-no-fix-on-2x-3x","nextjs-oct14-two-95-rces-no-13x-14x-fix",
      "litellm-59822-mcp-auth-bypass-kev","k8s-134-eol"]
MUST=[k for k in MUST if any(r['k']==k for r in L['patch'])]
NEWKEYS={"atlassian-21589-kev-overdue-bitbucket-bamboo","hudi-variant-wrong-rows-no-release",
         "react-rsc-95-rce-repo-only-advisory","gosnowflake-v1-patched-version-none",
         "mongo-go-driver-v1-107325-no-fix"}
PR.mark_touched(L['patch'], set(MUST)|NEWKEYS, 'ENRICHED 10-23')
shown=PR.select(L['patch'],T0,30,MUST)
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
json.dump(L,open('lens/ledger_101.json','w'),indent=1)
print("ledger sizes:",{k:len(v) for k,v in L.items() if isinstance(v,list)})
