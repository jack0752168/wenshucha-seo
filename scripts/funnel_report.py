#!/usr/bin/env python3
"""First-party funnel counts: completed dates, anonymous sessions, server receipts."""
import argparse
import collections
import datetime as dt
import json
import os
from pathlib import Path
import subprocess

SGT = dt.timezone(dt.timedelta(hours=8))
REMOTE = r'''
import json,pathlib
root=pathlib.Path('/opt/wenshucha-seo/state/funnel')
meta=root/'tracking-state.json'
events=root/'events.jsonl'
qa=root/'qa-events.jsonl'
def rows(path):
 out=[]
 if path.exists():
  for line in path.open():
   try:out.append(json.loads(line))
   except ValueError:pass
 return out
leads=[]
for p in pathlib.Path('/opt/wenshucha-leads/report').glob('*.json'):
 try:
  r=json.loads(p.read_text());leads.append({k:r.get(k) for k in ['id','received_at','funnel','kind','bot','self']})
 except ValueError:pass
for r in rows(pathlib.Path('/opt/mcp-applications/applications.jsonl')):
 leads.append({'id':r.get('id'),'received_at':r.get('ts'),'funnel':r.get('funnel'),'kind':'mcp','bot':r.get('bot'),'self':r.get('self')})
print(json.dumps({'meta':json.loads(meta.read_text()) if meta.exists() else None,'events':rows(events),'qa':rows(qa),'receipts':leads}))
'''

def fetch():
    command = ["python3", "-"] if Path("/opt/wenshucha-seo/state/funnel").exists() else ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "root@114.132.74.235", "python3 -"]
    r = subprocess.run(command, input=REMOTE, text=True, capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError("funnel evidence unavailable")
    return json.loads(r.stdout)

def day(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(SGT).date()

def summarize(data, target):
    meta = data.get("meta") or {}
    started = meta.get("started_at")
    if not started or day(started) > target:
        return {"date": str(target), "status": "unmeasured", "started_at": started, "counts": None, "rates": None}
    groups = collections.defaultdict(set)
    sources = collections.defaultdict(lambda: collections.defaultdict(set))
    seen = set()
    times = collections.defaultdict(lambda: collections.defaultdict(list))
    for event in data.get("events", []):
        if event.get("qa") or event.get("self") or event.get("bot") or day(event["received_at"]) != target: continue
        eid = event.get("eid")
        if eid in seen: continue
        seen.add(eid)
        sid, name, source = event.get("sid"), event.get("event"), event.get("source", "other")
        if not sid: continue
        groups[name].add(sid); sources[source][name].add(sid)
        times[sid][name].append(dt.datetime.fromisoformat(event['received_at'].replace('Z','+00:00')).timestamp())
    receipts = [r for r in data.get("receipts", []) if r.get("received_at") and day(r["received_at"]) == target and not (r.get("funnel") or {}).get("qa") and not r.get("bot") and not r.get("self")]
    receipts = list({(r.get('kind'), r.get('id')): r for r in receipts if r.get('id')}.values())
    receipt_sids = {r["funnel"]["sid"] for r in receipts if (r.get("funnel") or {}).get("sid")}
    groups["lead_received"].update(receipt_sids)
    for r in receipts:
        ctx = r.get("funnel") or {}
        if ctx.get("sid"):
            sources[ctx.get("source", "other")]["lead_received"].add(ctx["sid"])
            times[ctx['sid']]['lead_received'].append(dt.datetime.fromisoformat(r['received_at'].replace('Z','+00:00')).timestamp())
    landing = groups["page_view"]
    progression = {sid: min(times[sid]['page_view']) for sid in landing}
    stages = []
    for event_name in ['search_success','fulltext_open','lead_received']:
        next_stage = {}
        for sid, prior in progression.items():
            later = [when for when in times[sid][event_name] if when >= prior]
            if later: next_stage[sid] = min(later)
        progression = next_stage; stages.append(set(progression))
    search, read, lead = stages
    counts = {"landing_sessions": len(landing), "search_success_sessions": len(search), "fulltext_open_sessions": len(read), "search_to_read_to_lead_sessions": len(lead), "search_empty_sessions": len(groups["search_empty"]), "search_error_sessions": len(groups["search_error"]), "fulltext_partial_sessions": len(groups["fulltext_partial"]), "report_cta_sessions": len(groups["cta_report"]), "report_demand_start_sessions": len(groups["lead_start"]), "report_demand_receipts": sum(r.get('kind') == 'report' for r in receipts), "mcp_demand_receipts": sum(r.get('kind') == 'mcp' for r in receipts), "demand_sessions": len(groups["lead_received"]), "contact_click_sessions": len(groups["contact_email"] | groups["contact_phone"])}
    def rate(a, b): return round(a / b, 4) if b else None
    return {"date": str(target), "status": "partial_first_day" if day(started) == target else "observed", "started_at": started, "counts": counts, "rates": {"landing_to_search": rate(len(search), len(landing)), "search_to_fulltext": rate(len(read), len(search)), "fulltext_to_demand": rate(len(lead), len(read))}, "source_session_counts": {k: {name: len(v) for name, v in values.items()} for k, values in sources.items()}, "limits": ["anonymous sessions are not identified people", "contact clicks are not submitted demands", "submitted demands are not paid orders", "old MCP receipts without funnel context remain unattributed", "cross-day sessions are counted within each day; no historical conversion baseline exists", "cookies blocked or deleted can break cross-domain joins"]}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); ap.add_argument("--date"); ap.add_argument("--input"); ap.add_argument("--qa-sid"); args = ap.parse_args()
    data = json.loads(Path(args.input).read_text()) if args.input else fetch()
    if args.qa_sid:
        found = [r for r in data.get("qa", []) if r.get("sid") == args.qa_sid]
        print(json.dumps({"sid": args.qa_sid, "events": dict(collections.Counter(r["event"] for r in found))})); return
    target = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(SGT).date() - dt.timedelta(days=1)
    result = summarize(data, target)
    if args.json: print(json.dumps(result, ensure_ascii=False)); return
    if result["status"] == "unmeasured":
        print("*🧭 昨日轉化漏斗:* 尚未開始量測，不能報0或比較轉化率。")
        print("*📨 昨日實際提交需求:* 此日期尚未建立統一量測，數量未知。")
        return
    c = result["counts"]
    partial = "（上線首日，僅涵蓋上線後時段）" if result["status"] == "partial_first_day" else ""
    print(f"*🧭 昨日轉化漏斗{partial}:* 進站 {c['landing_sessions']} → 成功檢索 {c['search_success_sessions']} → 展開庫內正文 {c['fulltext_open_sessions']} → 需求提交 {c['search_to_read_to_lead_sessions']}（同訪次鏈）")
    print(f"*📨 昨日實際提交需求:* 合計 {c['report_demand_receipts'] + c['mcp_demand_receipts']} 筆（研究報告 {c['report_demand_receipts']} · MCP機構申請 {c['mcp_demand_receipts']}）；按服務端回執去重、排除QA／自訪／已知爬蟲。")
    print(f"_部分正文 {c['fulltext_partial_sessions']} 訪次 · 檢索失敗 {c['search_error_sessions']} 訪次；聯絡點擊／需求提交都不代表付費。_")

if __name__ == "__main__":
    try: main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        print("*🧭 轉化漏斗:* 資料讀取失敗，狀態未知，不報0。")
        raise SystemExit(2)
