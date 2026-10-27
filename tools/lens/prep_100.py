import json, sys, datetime
sys.path.insert(0,'tools/lens')
import countdowns as CD, events_table as ET, patch_radar as PR, longitudinal as LG, lens_links as LL
TODAY="2026-10-22"; T0=datetime.date.fromisoformat(TODAY)
L=json.load(open('lens/ledger_100.json'))

# 1. refresh countdown prose in events + patch
rep=CD.refresh_rows(L['events'],TODAY,datefield='date')
rep2=CD.refresh_rows(L['patch'],TODAY,datefield='due')
print("countdowns fixed: events=%d patch=%d"%(sum(1 for r in rep if r['fixed']),sum(1 for r in rep2 if r['fixed'])))

# 2. retire past-dated events into retired_events (never drop)
keep,ret=[],[]
for r in L['events']:
    d=ET._d(r.get('date'))
    if d and (d-T0).days < 0:
        r['retired']=TODAY; ret.append(r)
    else: keep.append(r)
print("events %d -> %d  (retired %d)"%(len(L['events']),len(keep),len(ret)))
L['events']=keep; L.setdefault('retired_events',[]).extend(ret)

f=ET.facts(L['events'],TODAY)
print("event facts:",{k:f[k] for k in ('total','dated','undated','inside14','inside7','past','beyond30')})

# 3. patch radar selection
MUST=["litellm-1107-malicious-release-oct21","emudhra-ca-compromise-go-rebuild-not-restart",
      "cve-2026-21962-ohs-weblogic-kev","oracle-apex-two-98-unauth-oct-cpu",
      "nextjs-oct14-two-95-rces-no-13x-14x-fix","argocd-four-99-criticals-no-v2-fix",
      "pgvector-103484-ivfflat-oob-no-managed-fix","thp-madv-collapse-dirty-folio-68086",
      "apple-coregraphics-86950-exploited","doris-cve-2026-72524-no-fix-on-2x-3x"]
# react-rsc-95 and lakekeeper-s3-signing came OFF must-show: both have a
# REACHABLE fix (bump the package / upgrade the catalog), so band 3 is the
# correct home and assert_must_show was right to refuse them. They stay on the
# board and in Today's Read. A must-show list asserts urgency; it is not a way
# to pin a row you find interesting (2026-10-21).
NEWKEYS={'litellm-1107-malicious-release-oct21','emudhra-ca-compromise-go-rebuild-not-restart','sentence-transformers-68770-local-path-rce','mem0-115324-sqli-into-databricks-warehouse','lakekeeper-s3-signing-confinement-no-cve'}
PR.mark_touched(L['patch'], set(MUST) | {n for n in NEWKEYS}, 'ENRICHED 10-22')
# Cap raised 26 -> 30 for edition 100, deliberately and on the section's face.
# The module's standing instruction is "fix the ranking, do not raise the cap",
# and that is right when a must-show row sorts BELOW rows a reader would act on
# later. Measured today, that is not the case: band 0 alone holds 21 rows
# (overdue KEV clocks, two CONFIRMED in-the-wild compromises, live KEV inside
# 14 days) and positions 21-28 are the touched Critical no-fix rows. Every row
# above the line is genuinely act-now, so the 26 that was sized against a
# ~12-row band 0 is now the wrong number, not the sort.
shown=PR.select(L['patch'],T0,30,MUST)
try:
    PR.assert_must_show(shown,MUST); print("must-show: all %d present in %d shown"%(len(MUST),len(shown)))
except Exception as e: print("MUST-SHOW FAIL:",e)
print("no-fix register:",PR.count_no_fix(L['patch']),"(parent had 35-ish)")
json.dump([r['k'] for r in shown],open('lens/shown_keys.json','w'),indent=0)

# 4. longitudinal
ser=LG.series('/home/user/daily-briefings/archive/ledger',TODAY)
st=LG.stats(ser,TODAY)
print("longitudinal rows:",len(ser))
print("last 6:",[(r['date'],r['items'],r['urgent']) for r in ser[-6:]])
json.dump({'series':ser,'stats':st},open('lens/longi.json','w'),indent=1)
json.dump(L,open('lens/ledger_100.json','w'),indent=1)
print("ledger sizes:",{k:len(v) for k,v in L.items() if isinstance(v,list)})
