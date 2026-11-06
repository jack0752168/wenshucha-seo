#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only, bounded product analytics. Raw identifiers never leave this process."""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3

SG = dt.timezone(dt.timedelta(hours=8))
STATES = ('awaiting_confirmation', 'queued', 'running', 'completed', 'failed', 'cancelled', 'no_result')
PLANS = {'trial', 'pass', 'monthly', 'annual', 'team', 'personal'}


def iso(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).isoformat() if ms is not None else None


def epoch(value):
    return int(dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000)


def windows(now):
    midnight = dt.datetime.fromtimestamp(now / 1000, SG).replace(hour=0, minute=0, second=0, microsecond=0)
    return {name: {'start': int((midnight-dt.timedelta(days=n-1)).timestamp()*1000), 'end': now}
            for name, n in [('today', 1), ('7d', 7), ('30d', 30)]}


def anonymous(raw):
    return 'R-' + hashlib.sha256(('wsc-research-dashboard-v1:' + str(raw)).encode()).hexdigest()[:12]


def qa_domain(email):
    domain = str(email).lower().rsplit('@', 1)[-1]
    return domain in {'example.com', 'example.org', 'example.net', 'test', 'invalid', 'localhost'} or domain.endswith(('.test', '.invalid', '.localhost', '.example'))


def research(db_path, now, known_qa=()):
    db = sqlite3.connect(Path(db_path).resolve().as_uri()+'?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
        for table, maximum in [('users', 5000), ('tasks', 100000), ('followups', 100000), ('activity', 500000), ('ledger', 100000), ('credit_packs', 25000), ('ledger_packs', 100000)]:
            if db.execute('SELECT count(*) FROM '+table).fetchone()[0] > maximum:
                raise ValueError('bounded_query_limit')
        users = [dict(r) for r in db.execute('SELECT id,email,org FROM users')]
        regs = {r['user']: r['at'] for r in db.execute("SELECT user,min(created) at FROM activity WHERE kind LIKE 'register:%' GROUP BY user")}
        tasks = [dict(r) for r in db.execute('SELECT id,user,status,created FROM tasks')]
        followups = [dict(r) for r in db.execute('SELECT user,created FROM followups')]
        ledger = {r['task']: r['status'] for r in db.execute('SELECT task,status FROM ledger')}
        packs = {r['id']: dict(r) for r in db.execute('SELECT id,org,plan,credits,starts,expires FROM credit_packs')}
        assignment = {r['task']: r['pack'] for r in db.execute('SELECT task,pack FROM ledger_packs')}
        mixed = [dict(r) for r in db.execute("SELECT day,event,sum(n) n FROM funnel_daily WHERE day>=? AND day<=? GROUP BY day,event", (dt.datetime.fromtimestamp(windows(now)['30d']['start']/1000,SG).date().isoformat(),dt.datetime.fromtimestamp(now/1000,SG).date().isoformat()))]
        used = collections.Counter(assignment[t] for t, status in ledger.items() if status in ('reserved', 'charged') and t in assignment)
        included, excluded = {}, collections.Counter()
        for u in users:
            if qa_domain(u['email']): excluded['reserved_test_domain'] += 1
            elif anonymous(u['id']) in known_qa: excluded['explicit_known_qa'] += 1
            else: included[u['id']] = u
        by_user = collections.defaultdict(list)
        for t in tasks:
            if t['user'] in included: by_user[t['user']].append(t)
        activity = collections.defaultdict(list)
        for f in followups:
            if f['user'] in included: activity[f['user']].append(f['created'])
        rows, all_actions, kept = [], {}, []
        mature = returned = immature = 0
        for uid, u in included.items():
            ts = by_user[uid]
            actions = sorted([t['created'] for t in ts] + activity[uid]); all_actions[uid] = actions
            first = min((t['created'] for t in ts), default=None)
            counts = collections.Counter(t['status'] for t in ts)
            active = [p for p in packs.values() if p['org'] == u['org'] and p['starts'] <= now < p['expires']]
            quota = [{'plan': p['plan'] if p['plan'] in PLANS else 'unknown', 'limit': p['credits'], 'remaining': max(0, p['credits']-used[p['id']]), 'expires_at': iso(p['expires'])} for p in active]
            return_state = 'not_started'
            if first is not None:
                if now < first+7*86400000: immature += 1; return_state = 'immature'
                else:
                    mature += 1
                    returned_here = any(first < x <= first+7*86400000 and dt.datetime.fromtimestamp(x/1000, SG).date() != dt.datetime.fromtimestamp(first/1000, SG).date() for x in actions)
                    returned += int(returned_here); return_state = 'returned' if returned_here else 'not_observed'
            plans = sorted({packs[assignment[t['id']]]['plan'] if t['id'] in assignment and assignment[t['id']] in packs and packs[assignment[t['id']]]['plan'] in PLANS else 'unknown' for t in ts})
            row = {'account': anonymous(uid), 'registered_at': iso(regs.get(uid)), 'first_research_at': iso(first), 'last_research_at': iso(max((t['created'] for t in ts), default=None)), 'last_use_at': iso(max(actions, default=None)), 'states': {s: counts[s] for s in STATES}, 'unknown_state_count': sum(n for s,n in counts.items() if s not in STATES), 'refunded_slots': sum(ledger.get(t['id'])=='refunded' for t in ts), 'used_plans': plans, 'active_quota': quota, 'remaining': sum(p['remaining'] for p in quota), 'next_expiry_at': min((p['expires_at'] for p in quota if p['remaining']), default=None), 'quota_shared_with_other_accounts': sum(x['org']==u['org'] for x in included.values()) > 1, 'distinct_use_days': len({dt.datetime.fromtimestamp(x/1000, SG).date() for x in actions}), 'return_7d': return_state, 'behavior': 'completed_research' if counts['completed'] else 'research_failed' if counts['failed'] or counts['no_result'] else 'research_started' if ts else 'registered_only'}
            rows.append(row); kept.extend(ts)
        metrics = {}
        for name, span in windows(now).items():
            lo, hi = span['start'], span['end']
            subset = [t for t in kept if lo <= t['created'] <= hi]
            counts = collections.Counter(t['status'] for t in subset)
            day_lo=dt.datetime.fromtimestamp(lo/1000,SG).date().isoformat()
            allowed_ops={'landing_view','example_open','trial_click','trial_registered','research_submitted','research_completed','research_refunded','plan_select','pricing_view','contact_open','contact_copy','contact_qr_save','entitlement_granted'}
            operations=collections.Counter()
            for item in mixed:
                if item['day']>=day_lo and item['event'] in allowed_ops:operations[item['event']]+=item['n']
            metrics[name] = {'new_registered_accounts': sum(lo <= regs[u] <= hi for u in included if u in regs), 'registration_time_unknown_accounts': sum(u not in regs for u in included), 'active_accounts': sum(any(lo<=a<=hi for a in actions) for actions in all_actions.values()), 'first_research_accounts': sum(r['first_research_at'] is not None and lo<=epoch(r['first_research_at'])<=hi for r in rows), 'completed_accounts': len({t['user'] for t in subset if t['status']=='completed'}), 'completed_tasks': counts['completed'], 'states': {s: counts[s] for s in STATES}, 'refunded_slots': sum(ledger.get(t['id'])=='refunded' for t in subset),'qa_mixed_operations':dict(operations)}
        floor = min([v for v in regs.values() if v is not None]+[t['created'] for t in tasks], default=None)
        trend = []
        for i in range(30):
            start = windows(now)['30d']['start']+i*86400000
            observed = floor is not None and start+86400000 > floor
            daytasks = [t for t in kept if start <= t['created'] < min(start+86400000, now+1)]
            trend.append({'day': dt.datetime.fromtimestamp(start/1000, SG).date().isoformat(), 'started': len(daytasks) if observed else None, 'completed_current_state': sum(t['status']=='completed' for t in daytasks) if observed else None})
        return {'status': 'observed', 'as_of': iso(now), 'window_bounds':{k:{x:iso(y) for x,y in v.items()} for k,v in windows(now).items()}, 'account_count': len(included), 'accounts': sorted(rows,key=lambda x:x['account']), 'windows': metrics, 'trend': trend, 'retained_record_floor': iso(floor), 'backlog': {s: sum(t['status']==s for t in kept) for s in ('awaiting_confirmation','queued','running')}, 'return_7d': {'mature_accounts': mature, 'immature_accounts': immature, 'returned_accounts': returned if mature else None, 'rate': returned/mature if mature else None}, 'exclusions': {'all_accounts': len(users), **dict(excluded), 'tasks_from_excluded_accounts': sum(t['user'] not in included for t in tasks), 'account_self_bot_flags': 'not_recorded'}, 'limits': ['非測試帳號不等於已驗證真人或付費客戶；帳號資料未記self/bot，無法由網站旗標跨站排除此類帳號。', '窗口按研究發起時間分組；完成/退名額是目前狀態，沒有逐任務完成或退款時間。', '回訪定義為首次研究後7日內跨新加坡日期再研究/續問，未成熟不報0%。', '註冊來源、微信詢單與付款沒有憑證，保持unknown；人工授權不是收款。', '額度是帳號所在團隊的有效包；共享團隊不可跨帳號相加。']}
    finally:
        db.rollback(); db.close()


def log_rows(path, limit=16*1024*1024):
    if not path.exists(): return [], {'status':'unknown','reason':'missing_log'}
    size = path.stat().st_size; truncated = size > limit
    with path.open('rb') as f:
        if truncated: f.seek(size-limit); f.readline()
        raw = f.read(limit)
    rows, invalid = [], 0
    for line in raw.splitlines():
        try:
            row=json.loads(line)
            if not isinstance(row,dict): raise ValueError('invalid_log_shape')
            rows.append(row)
        except (ValueError, UnicodeError): invalid += 1
    return rows, {'status':'partial' if truncated or invalid else 'observed','tail_truncated':truncated,'invalid_rows':invalid,'bytes_read':len(raw)}


def web(root, now, application_log):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent) if '__file__' in globals() and __file__!='<stdin>' else '/opt/wenshucha-seo/scripts')
    from funnel_report import product_ctas
    meta = json.loads((root/'tracking-state.json').read_text())
    events, quality = log_rows(root/'events.jsonl')
    qa, qa_quality = log_rows(root/'qa-events.jsonl')
    leads, lead_quality = log_rows(application_log)
    excluded = collections.Counter(); accepted = []; seen = set()
    for e in events:
        if e.get('qa'): excluded['qa_in_natural_log']+=1;continue
        if e.get('self'): excluded['self']+=1;continue
        if e.get('bot'): excluded['bot']+=1;continue
        if not e.get('eid') or not e.get('sid'): excluded['missing_receipt_identity']+=1;continue
        if e['eid'] in seen: excluded['duplicate_event_id']+=1;continue
        seen.add(e['eid'])
        try:e['_at']=epoch(e['received_at'])
        except (KeyError,ValueError,TypeError):excluded['invalid_timestamp']+=1;continue
        accepted.append(e)
    leadseen=set(); cleanleads=[]
    for row in leads:
        if row.get('bot') or row.get('self') or (row.get('funnel') or {}).get('qa'):excluded['qa_self_bot_application']+=1;continue
        identity=row.get('id')
        if not identity:excluded['application_without_receipt_id']+=1;continue
        if identity in leadseen:excluded['duplicate_application_receipt']+=1;continue
        leadseen.add(identity)
        try:at=epoch(row.get('ts') or row.get('received_at'))
        except (ValueError,TypeError,AttributeError):excluded['invalid_application_time']+=1;continue
        cleanleads.append(at)
    periods={};today=dt.datetime.fromtimestamp(now/1000,SG).date()
    for name, span in windows(now).items():
        subset=[e for e in accepted if span['start']<=e['_at']<=now]
        product=product_ctas(subset,meta.get('research_cta_tracking_started_at'),today)
        mcp_events=[e for e in subset if e.get('event')=='cta_mcp']
        start=meta.get('research_cta_tracking_started_at')
        partial=not start or epoch(start)>span['start'] or quality['status']!='observed'
        periods[name]={'status':'partial' if partial else 'observed','cta_sessions':product['session_counts'], 'mcp_cta_sessions':len({e['sid'] for e in mcp_events}) if quality['status']!='unknown' else None,'mcp_application_receipts':sum(span['start']<=at<=now for at in cleanleads) if lead_quality['status']=='observed' else None,'research_registered_source':None,'research_contact_intent':None,'research_verified_inquiries':None,'research_verified_payments':None}
        if quality['status']!='observed':
            periods[name]['cta_sessions']={key:None for key in product['session_counts']}
            periods[name]['mcp_cta_sessions']=None
    return {'status':'observed' if quality['status']=='observed' else 'unknown','as_of':iso(now),'window_bounds':{k:{x:iso(y) for x,y in v.items()} for k,v in windows(now).items()},'windows':periods,'exclusions':{'qa_log_rows':len(qa) if qa_quality['status']!='unknown' else None,**dict(excluded)},'quality':{'events':quality,'qa':qa_quality,'mcp_receipts':lead_quality},'started_at':meta.get('started_at'),'research_cta_started_at':meta.get('research_cta_tracking_started_at'),'native_mcp_tool_calls':None,'native_mcp_active_keys':None,'mcp_verified_payments':None,'limits':['網站CTA是匿名去重訪次，不是研究完成或客戶人數。','MCP僅接既有網站入口與機構申請回執；獨立Key原生調用/付款尚未接入。','研究應用funnel_daily含QA且沒有逐帳號來源，不能跨站歸因。']}


def collect(db_path='/var/lib/wsc-research/research.sqlite', log_root='/opt/wenshucha-seo/state/funnel', application_log='/opt/mcp-applications/applications.jsonl', now=None):
    now=now if now is not None else int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
    result={'schema_version':1,'generated_at':iso(now),'windows':{key:{k:iso(v) for k,v in span.items()} for key,span in windows(now).items()},'mode':'production'}
    for name, function in [('research',lambda:research(db_path,now)),('web',lambda:web(Path(log_root),now,Path(application_log)))]:
        try:result[name]=function()
        except (OSError,ValueError,sqlite3.Error,KeyError,TypeError,AttributeError):result[name]={'status':'unknown','as_of':None,'reason':'source_unavailable_or_invalid'}
    return result


if __name__=='__main__':
    print(json.dumps(collect(),ensure_ascii=False))
