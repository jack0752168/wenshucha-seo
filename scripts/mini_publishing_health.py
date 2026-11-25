#!/usr/bin/env python3
"""Read-only publishing health: delivery is not publication. No browser or writes on mini."""
import datetime as dt
import json
from pathlib import Path
import re
import subprocess

REMOTE = r'''
from pathlib import Path
import json,re,datetime
h=Path.home();root=h/'wenshucha-seo';schedule=json.loads((h/'.dsh/storages/schedule.json').read_text());log=(root/'content/drafts/PUBLISH-LOG.md').read_text();out={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'platforms':{}}
for key,term in [('zhihu','知乎'),('baijiahao','百家')]:
 rows=[l for l in log.splitlines() if re.match(r'2026-\d\d-\d\d',l) and term in l and ('已发布' in l or '已發布' in l) and not any(t in l for t in ['未发布','未發布','BLOCKER','草稿未'])]
 dates=[re.match(r'(\d{4}-\d{2}-\d{2})',l).group(1) for l in rows]
 data={'last_ledger_publication_date':max(dates) if dates else None,'ledger_is_not_current_backend':True}
 for task in schedule['tables']['tasks'].values():
  r=task.get('record',{})
  if term in r.get('title',''):data.update({'schedule_status':task.get('status'),'last_delivery':task.get('lastDelivery'),'next_delivery':r.get('scheduledAt')})
 p=root/('state/publishing-'+key+'-recovery.json')
 if p.exists():
  recovery=json.loads(p.read_text());data['last_browser_check']={k:recovery.get(k) for k in ['checked_at','status','publication_attempted','restriction']}
 out['platforms'][key]=data
print(json.dumps(out,ensure_ascii=False))
'''

def assess(snapshot):
    now=dt.datetime.fromisoformat(snapshot['checked_at']);today=now.astimezone(dt.timezone(dt.timedelta(hours=8))).date()
    for data in snapshot['platforms'].values():
        date=data.get('last_ledger_publication_date')
        data['days_since_ledger_publication']=(today-dt.date.fromisoformat(date)).days if date else None
        check=data.get('last_browser_check',{});status=check.get('status')
        at=check.get('checked_at');fresh=False
        if at:
            fresh=0 <= (now-dt.datetime.fromisoformat(at)).total_seconds() <= 86400
        if status=='account_restricted' and fresh:data['business_status']='blocked_account_restricted'
        elif date is None:data['business_status']='unknown_publication_evidence'
        elif data['days_since_ledger_publication']>=3:data['business_status']='stale_publication_requires_investigation'
        else:data['business_status']='recent_ledger_publication_requires_backend_verification'
        data['browser_evidence_fresh']=fresh
    snapshot['limits']=['No browser action or publication attempted.','A delivered reminder or active schedule never proves execution or publication.','Ledger age is an alert, not proof of root cause; current account gate evidence has its own timestamp.']
    return snapshot

if __name__=='__main__':
    try:
        r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','codex-mini','/Users/jack/es-mini/python/bin/python3 -'],input=REMOTE,text=True,capture_output=True,timeout=30,check=True)
        result=assess(json.loads(r.stdout))
    except (subprocess.SubprocessError,ValueError,OSError) as e:
        result={'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'unknown','reason':type(e).__name__}
    print(json.dumps(result,ensure_ascii=False,indent=2))
