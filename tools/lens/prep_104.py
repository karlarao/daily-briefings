import json, sys, datetime
sys.path.insert(0,'tools/lens')
import countdowns as CD, events_table as ET, patch_radar as PR, longitudinal as LG
TODAY="2026-10-26"; T0=datetime.date.fromisoformat(TODAY)
L=json.load(open('lens/ledger_104.json'))

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

MUST=[
 "jdk-114820-no-vendor-build-keytool","jdk-91403-near-twin-respin-oct21",
 "k8s-oct-patch-overdue-all-four-branches","mariadb-mdev-33966-fix-merged-no-released-build",
 "arrow-rs-60-newest-major-is-the-unpatched-one","mysql-80-server-absent-from-oct-2026-cpu",
 "pip-ensurepip-emsign-no-py39-fix","ray-62593-kev-66d-overdue-gpu-clusters",
 "emudhra-ca-compromise-go-rebuild-not-restart","ca-distrust-go-node-emudhra-oct19-21",
 "cve-2026-21962-ohs-weblogic-kev","apple-coregraphics-86950-exploited",
 "mongodb-82-no-fixed-version","pgbouncer-scram-nonce-preauth-crash-19888",
 "doris-cve-2026-72524-no-fix-on-2x-3x","starrocks-82306-query-detail-no-fix",
 "react-rsc-95-unauth-rce-no-cve","postgres-mcp-85620-unpatched-9-2",
 "nextjs-oct14-two-95-rces-no-13x-14x-fix","vitess-sqli-sextet-no-fix",
 "angular-v19-permanent-eol-unpatched","snowflake-drivers-ocsp-cve-2026-85525",
 "atlassian-21589-kev-overdue-bitbucket-bamboo","litellm-59822-mcp-auth-bypass-kev",
]
MUST=[k for k in MUST if any(r['k']==k for r in L['patch'])]
NEWKEYS={"jdk-91403-near-twin-respin-oct21","arrow-rs-60-newest-major-is-the-unpatched-one",
 "mariadb-mdev-33966-fix-merged-no-released-build","mysql-80-server-absent-from-oct-2026-cpu"}
PR.mark_touched(L['patch'], set(MUST)|NEWKEYS, 'ENRICHED 10-26')

# 10-24 rule: compute |band0 u must_show| BEFORE deciding the cap.
band0=[r for r in L['patch'] if PR.sev_tier(r)==0]
union=len({r['k'] for r in band0} | set(MUST))
print("band0=%d  must_show=%d  |band0 u must_show|=%d"%(len(band0),len(MUST),union))
CAP=35  # 10-25 correction: band0 is a third of the board; a cap driven off it is a list, not a radar
shown=PR.select(L['patch'],T0,CAP,MUST)
try:
    PR.assert_must_show(shown,MUST); print("must-show: all %d present in %d shown (cap %d)"%(len(MUST),len(shown),CAP))
except Exception as e: print("MUST-SHOW FAIL:",e)
print("no-fix register:",PR.count_no_fix(L['patch']))
json.dump([r['k'] for r in shown],open('lens/shown_keys.json','w'),indent=0)
json.dump({'cap':CAP,'union':union,'band0':len(band0),'must':len(MUST)},open('lens/capinfo.json','w'))

ser=LG.series('/home/user/daily-briefings/archive/ledger',TODAY)
st=LG.stats(ser,TODAY)
print("longitudinal rows:",len(ser))
print("last 8 (date,items,urgent):",[(r['date'],r['items'],r['urgent']) for r in ser[-8:]])
json.dump({'series':ser,'stats':st},open('lens/longi.json','w'),indent=1)
json.dump(L,open('lens/ledger_104.json','w'),indent=1)
print("ledger sizes:",{k:len(v) for k,v in L.items() if isinstance(v,list)})
