#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Private static dashboard and immutable snapshots; never deploy under webroot."""
import argparse
import csv
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import uuid

from product_usage_source import SG, collect

ROOT = Path(__file__).resolve().parents[1]


def fetch():
    if Path('/var/lib/wsc-research/research.sqlite').exists():
        return collect()
    code = Path(__file__).with_name('product_usage_source.py').read_text()
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','root@114.132.74.235','cd /opt/wenshucha-seo/scripts && /usr/bin/python3 -'],input=code,text=True,capture_output=True,timeout=40)
    if result.returncode: raise ValueError('source_unavailable')
    return json.loads(result.stdout)


def atomic(path, text):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex)
    with temp.open('x') as file:
        os.chmod(temp,0o600);file.write(text)
    temp.replace(path)


def merged(attempt, previous):
    display=json.loads(json.dumps(attempt))
    for name in ('research','web'):
        component=attempt.get(name,{'status':'unknown'})
        if component.get('status')!='observed' and previous and previous.get(name,{}).get('status')=='observed':
            display[name]=json.loads(json.dumps(previous[name]));display[name]['status']='stale'
            display[name]['last_successful_at']=previous[name].get('as_of')
            display[name]['failure_reason']='source_unavailable_or_invalid'
    return display


def accounts_csv(data):
    file=io.StringIO();writer=csv.writer(file)
    columns=['account','registered_at','first_research_at','last_research_at','last_use_at','behavior','used_plans','remaining','next_expiry_at','refunded_slots','data_as_of','source_status']
    writer.writerow(columns)
    research=data.get('research',{})
    for row in research.get('accounts',[]):
        values={**row,'used_plans':'/'.join(row['used_plans']),'data_as_of':research.get('as_of'),'source_status':research.get('status')}
        writer.writerow([values.get(key) for key in columns])
    return file.getvalue()


def markdown(data):
    research=data.get('research',{});web=data.get('web',{});lines=['# 文書查內部產品使用日報', '', '更新：'+str(data['generated_at']), '研究資料：'+str(research.get('as_of'))+' / '+research.get('status','unknown'), '網站資料：'+str(web.get('as_of'))+' / '+web.get('status','unknown'), '', '非測試帳號不等於真人或付費客戶。']
    for key,label in [('today','今天'),('7d','近7天'),('30d','近30天')]:
        r=research.get('windows',{}).get(key,{})
        lines.extend(['', '## '+label, '新增非測試註冊：'+str(r.get('new_registered_accounts'))+'；首次發起研究帳號：'+str(r.get('first_research_accounts'))+'；目前完成研究：'+str(r.get('completed_tasks'))+'；退還研究名額：'+str(r.get('refunded_slots')), '研究窗口：'+json.dumps(research.get('window_bounds',{}).get(key),ensure_ascii=False), '網站窗口：'+json.dumps(web.get('window_bounds',{}).get(key),ensure_ascii=False), 'MCP：'+json.dumps(web.get('windows',{}).get(key,{}).get('mcp_application_receipts'),ensure_ascii=False)+' 筆機構申請回執；原生Key用量未接入。'])
    lines.extend(['','註冊來源、微信詢單及收款：unknown。funnel_daily 含 QA，不作客戶數或完整跨站歸因。'])
    return '\n'.join(lines)+'\n'


def html_page(data, history, snapshot):
    # Data is exclusively anonymous analytics. Escape script delimiters anyway.
    encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    links=''.join('<li><a href="'+name+'">'+name.split('/')[-1]+'</a></li>' for name in history)
    page='''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>文書查｜內部產品使用復盤</title><style>
*{box-sizing:border-box}body{margin:0;background:#eef2f7;color:#1d2c43;font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang TC",sans-serif}header{background:#13233c;color:#fff;padding:30px max(20px,calc((100% - 1220px)/2))}header h1{margin:4px 0;font-size:28px}.eyebrow{color:#9fc7df;letter-spacing:2px;font-size:12px}.wrap{max-width:1260px;padding:24px 20px;margin:auto}.toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.tabs{display:flex;gap:8px}button{border:1px solid #bfd0df;background:#fff;padding:9px 17px;border-radius:8px;color:#20344b;cursor:pointer}button.active{background:#243f65;color:white}.products{display:grid;grid-template-columns:1.6fr 1fr;gap:20px;margin:20px 0}.panel{background:white;border:1px solid #dce3ed;border-radius:14px;padding:24px;margin-bottom:20px;min-width:0}.panel h2{margin:0 0 8px;font-size:21px}.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:18px 0}.metric{padding:15px;border:1px solid #e1e6ef;border-radius:10px}.metric b{display:block;font-size:29px;color:#255b70}.muted{font-size:13px;color:#62748a}.badge{display:inline-block;border-radius:6px;padding:3px 8px;background:#e4f2ea;color:#236344;font-size:12px}.warn{background:#fff3d9;color:#825b1d;padding:13px 16px;border-radius:8px;margin:12px 0}.stale{background:#fbe8df;color:#8c4321}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:11px 9px;border-bottom:1px solid #e5e9ef;vertical-align:top;min-width:100px}th{color:#617289;font-weight:600}a{color:#246b91}input{font:inherit;padding:9px 12px;border:1px solid #becbdb;border-radius:7px;max-width:100%}.chart{height:115px;display:flex;gap:4px;align-items:end;padding:8px 0}.bar{flex:1;min-width:2px;background:#36788e;position:relative;border-radius:3px 3px 0 0}.bar.unknown{background:repeating-linear-gradient(45deg,#ccd5e1,#ccd5e1 3px,#edf1f6 3px,#edf1f6 6px)}.bar:hover:after{content:attr(data-tip);position:absolute;bottom:100%;background:#13233c;color:white;white-space:nowrap;font-size:11px;padding:4px;z-index:2}.links{display:flex;gap:15px;flex-wrap:wrap}.limit-list{padding-left:20px}code{font-size:12px;overflow-wrap:anywhere}footer{padding:10px 0 30px;font-size:13px;color:#64758a}@media(max-width:780px){.products{grid-template-columns:1fr}header h1{font-size:24px}.panel{padding:18px}.wrap{padding:16px 12px}.metrics{gap:9px}.metric{padding:11px}.metric b{font-size:25px}}
</style></head><body><header><div class="eyebrow">WENSHUCHA · INTERNAL ONLY</div><h1>產品使用，分開看清楚。</h1><div id="freshness"></div><div class="muted" style="color:#bac9da">本機／內部靜態報表 · 不含客戶郵箱、案情、文書、密碼或 Key</div></header><main class="wrap"><div class="toolbar"><div class="tabs"><button data-window="today" class="active">今天</button><button data-window="7d">近 7 天</button><button data-window="30d">近 30 天</button></div><div class="links"><a href="SNAPSHOT">本次 JSON</a><a href="CSV">匿名帳號 CSV</a><a href="MD">可回看日報</a></div></div><div id="mode"></div><div class="products"><section class="panel"><h2>類案研究 <span id="research-status" class="badge"></span></h2><div id="research-time" class="muted"></div><div id="research-note"></div><div class="metrics" id="research-metrics"></div><div id="research-states"></div><p class="muted">窗口按任務發起日期分組，完成／退名額為目前狀態。名額退還不是現金退款；帳號不等於真人。</p></section><section class="panel"><h2>MCP <span id="web-status" class="badge"></span></h2><div id="web-time" class="muted"></div><div class="metrics" id="mcp-metrics"></div><p class="muted">只接可信網站入口與機構申請回執。獨立 Key 原生調用、付費人數及實收金額尚未接入，保持未知。</p><div id="mcp-quality"></div></section></div>
<section class="panel"><h2>從看介紹，到真的使用</h2><div id="stages"></div><p class="muted">這些是不同資料來源的分層觀察，不能相除當完整跨站轉化率。funnel_daily 的查看方案／聯絡／授權操作含 QA，單獨標示。</p></section><section class="panel"><h2>近 30 天研究發起趨勢</h2><div class="chart" id="chart"></div><p class="muted">實色：現存資料可觀察日；斜紋：最早現存紀錄前／未知。沒有倒填舊訪客數。</p><div id="returns"></div></section>
<section class="panel"><div class="toolbar"><h2>匿名帳號使用明細</h2><input id="filter" placeholder="篩選匿名代號 R-…" aria-label="篩選匿名帳號"></div><p class="muted">全部非測試帳號；列內狀態為累計，時間窗指標見上方。團隊額度為共享值，不能逐帳號加總。</p><div class="table-wrap"><table><thead><tr><th>帳號／行為</th><th>註冊／首次研究</th><th>最近使用／回訪</th><th>研究狀態</th><th>使用方案</th><th>有效額度／到期</th></tr></thead><tbody id="accounts"></tbody></table></div></section>
<section class="panel"><h2>排除與資料品質</h2><div id="quality"></div></section><details class="panel"><summary>歷史快照：保留原檔，不覆寫過去日期</summary><ul>HISTORY</ul></details><footer>內部使用。匿名點擊不是研究完成，人工額度不是付款，微信開窗不是已收到詢單；來源不足時保持 unknown。</footer></main>
<script id="snapshot-data" type="application/json">DATA</script><script>
const d=JSON.parse(document.getElementById('snapshot-data').textContent), r=d.research||{}, w=d.web||{};let selected='today';const $=id=>document.getElementById(id);const f=x=>x===null||x===undefined?'未知':String(x);const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const when=x=>x?new Date(x).toLocaleString('zh-TW',{timeZone:'Asia/Singapore',hour12:false}):'未知';const labels={awaiting_confirmation:'待確認',queued:'排隊',running:'執行中',completed:'完成',failed:'失敗',cancelled:'取消',no_result:'無可用文書'};const behavior={registered_only:'帳號存在／未見研究',research_started:'已發起研究',research_failed:'研究未完成',completed_research:'有完成研究'};function metric(name,value){return '<div class="metric"><span class="muted">'+name+'</span><b>'+f(value)+'</b></div>';}function badge(id,s){$(id).textContent=s||'unknown';if(s!=='observed')$(id).classList.add('stale');}
$('freshness').textContent='更新嘗試：'+when(d.generated_at);badge('research-status',r.status);badge('web-status',w.status);$('research-time').textContent='研究資料截止：'+when(r.as_of);$('web-time').textContent='網站資料截止：'+when(w.as_of);if(d.mode!=='production')$('mode').innerHTML='<p class="warn">合成測試／離線回放，非本次正式客戶資料。</p>';if(r.status==='stale'||w.status==='stale')$('mode').innerHTML+='<p class="warn">本次部分來源讀取失敗，正在顯示最後成功資料；舊快照未被覆寫。</p>';
function render(){for(const [component,id,label] of [[r,'research-time','研究'],[w,'web-time','網站']]){const bounds=(component.window_bounds||{})[selected]||{};$(id).textContent=label+'資料截止：'+when(component.as_of)+'；實際窗口：'+when(bounds.start)+' → '+when(bounds.end);}const a=(r.windows||{})[selected]||{},b=(w.windows||{})[selected]||{},c=b.cta_sessions||{},ops=a.qa_mixed_operations||{};$('research-note').innerHTML=r.account_count===0?'<p class="warn">目前未觀測到非測試帳號研究。已排除 '+f((r.exclusions||{}).reserved_test_domain)+' 個保留測試域帳號。</p>':'';$('research-metrics').innerHTML=metric('非測試帳號（目前總數）',r.account_count)+metric('本窗首次發起研究帳號',a.first_research_accounts)+metric('本窗完成研究帳號',a.completed_accounts)+metric('本窗完成研究次數',a.completed_tasks);$('research-states').textContent='最近一次研究使用：'+when((r.accounts||[]).map(x=>x.last_use_at).filter(Boolean).sort().slice(-1)[0])+'；本窗新增註冊 '+f(a.new_registered_accounts)+' · 實際操作帳號 '+f(a.active_accounts)+' · 退還研究名額 '+f(a.refunded_slots)+'；'+Object.entries(labels).map(([s,l])=>l+' '+f((a.states||{})[s])).join(' / ');$('mcp-metrics').innerHTML=metric('MCP 入口點擊訪次',b.mcp_cta_sessions)+metric('機構申請回執',b.mcp_application_receipts)+metric('獨立 Key 真調用',null)+metric('已核收款',null);$('mcp-quality').textContent='本窗網站資料品質：'+f(b.status);const stage=[['研究介紹入口訪次',c.research_intro,'排 QA/self/bot，按事件去重'],['進研究應用訪次',c.research_app,'不能追認註冊來源'],['新增非測試註冊',a.new_registered_accounts,'按 register 活動；非真人認證'],['發起研究',Object.values(a.states||{}).reduce((n,v)=>n+v,0),'非測試帳號任務'],['完成研究',a.completed_tasks,'按發起窗、目前完成狀態'],['查看方案操作',ops.pricing_view??0,'含 QA，只是操作數'],['聯絡開窗操作',ops.contact_open??0,'含 QA，非詢單'],['人工授權操作',ops.entitlement_granted??0,'含 QA，非已收款'],['已核實詢單／收款',null,'沒有憑證，不補 0']];$('stages').innerHTML='<div class="table-wrap"><table><tr><th>階段</th><th>本窗</th><th>判讀</th></tr>'+stage.map(([l,v,n])=>'<tr><td>'+l+'</td><td>'+f(r.status==='unknown'&&!l.includes('入口')&&!l.includes('應用')?null:v)+'</td><td>'+n+'</td></tr>').join('')+'</table></div>';}
document.querySelectorAll('[data-window]').forEach(b=>b.onclick=()=>{selected=b.dataset.window;document.querySelectorAll('[data-window]').forEach(x=>x.classList.toggle('active',x===b));render();});
const trend=r.trend||[],maximum=Math.max(1,...trend.map(x=>x.started||0));$('chart').innerHTML=trend.map(x=>'<div class="bar '+(x.started===null?'unknown':'')+'" style="height:'+(x.started===null?14:Math.max(3,x.started/maximum*100))+'%" data-tip="'+x.day+'：'+f(x.started)+'"></div>').join('');const ret=r.return_7d||{};$('returns').textContent='7日內跨日回訪：'+(ret.rate===null||ret.rate===undefined?'未知（成熟觀察窗不足或尚無研究帳號）':(ret.rate*100).toFixed(1)+'%')+'；成熟帳號 '+f(ret.mature_accounts)+'，未成熟 '+f(ret.immature_accounts)+'.';
function rows(){const filter=$('filter').value.toLowerCase(),items=(r.accounts||[]).filter(x=>x.account.toLowerCase().includes(filter));$('accounts').innerHTML=items.length?items.map(x=>'<tr><td><code>'+esc(x.account)+'</code><br>'+esc(behavior[x.behavior]||'未知')+'</td><td>'+when(x.registered_at)+'<br>首次研究：'+when(x.first_research_at)+'</td><td>'+when(x.last_use_at)+'<br>操作日期數：'+f(x.distinct_use_days)+'<br>7日回訪：'+esc(({not_started:'未研究',immature:'觀察窗未成熟',returned:'有跨日回訪',not_observed:'未觀測到'})[x.return_7d]||'未知')+'</td><td>'+Object.entries(labels).map(([s,l])=>l+' '+f(x.states[s])).join('<br>')+'<br>退名額 '+f(x.refunded_slots)+'</td><td>'+esc(x.used_plans.join(' / ')||'未見研究方案')+'</td><td>剩餘 '+f(x.remaining)+(x.quota_shared_with_other_accounts?'（團隊共享）':'')+'<br>'+when(x.next_expiry_at)+'</td></tr>').join(''):'<tr><td colspan="6">'+(r.status==='unknown'?'研究資料未知，沒有填成0。':'目前沒有符合條件的非測試帳號。')+'</td></tr>';}$('filter').oninput=rows;
$('quality').innerHTML='<p>來源讀取品質：<code>'+esc(JSON.stringify(w.quality||{}))+'</code></p><p>研究排除：<code>'+esc(JSON.stringify(r.exclusions||{}))+'</code></p><p>網站排除：<code>'+esc(JSON.stringify(w.exclusions||{}))+'</code></p><ul class="limit-list">'+[...(r.limits||[]),...(w.limits||[])].map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';render();rows();
</script></body></html>'''
    return page.replace('SNAPSHOT',snapshot).replace('href="CSV"','href="'+snapshot.replace('.json','.csv')+'"').replace('href="MD"','href="'+snapshot.replace('.json','.md')+'"').replace('HISTORY',links).replace('DATA',encoded)


def save(attempt, output):
    resolved=output.resolve()
    if str(resolved).startswith('/www/wwwroot/') or 'wenshucha-site' in resolved.parts:
        raise ValueError('refusing_public_dashboard_destination')
    output.mkdir(parents=True,exist_ok=True,mode=0o700)
    if attempt.get('schema_version')!=1 or not isinstance(attempt.get('generated_at'),str):
        raise ValueError('invalid_snapshot_header')
    for key in ('research','web'):
        component=attempt.get(key,{})
        if not isinstance(component,dict): raise ValueError('invalid_component')
        if component.get('status')=='observed' and (not component.get('as_of') or not isinstance(component.get('windows'),dict)):
            raise ValueError('invalid_observed_component')
    previous=None
    if (output/'last-good.json').exists():
        try:previous=json.loads((output/'last-good.json').read_text())
        except (OSError,ValueError):previous=None
    if previous and previous.get('mode')!=attempt.get('mode'): previous=None
    view=merged(attempt,previous)
    now=dt.datetime.fromisoformat(attempt['generated_at'].replace('Z','+00:00'))
    name='snapshots/'+now.astimezone(SG).date().isoformat()+'/'+now.strftime('%H%M%S%f')+'-'+uuid.uuid4().hex[:8]+'.json'
    path=output/name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with path.open('x') as file:
        os.chmod(path,0o600);file.write(json.dumps(view,ensure_ascii=False,indent=2)+'\n')
    atomic(path.with_suffix('.csv'),accounts_csv(view));atomic(path.with_suffix('.md'),markdown(view))
    good=json.loads(json.dumps(previous or {'schema_version':1,'mode':attempt.get('mode'),'generated_at':attempt['generated_at']}))
    updated=False
    for key in ('research','web'):
        if attempt.get(key,{}).get('status')=='observed':good[key]=attempt[key];updated=True
    if updated:
        good['mode']=attempt.get('mode')
        good['generated_at']=attempt['generated_at']
        atomic(output/'last-good.json',json.dumps(good,ensure_ascii=False,indent=2)+'\n')
    atomic(output/'latest.json',json.dumps(view,ensure_ascii=False,indent=2)+'\n')
    history=sorted((str(p.relative_to(output)) for p in (output/'snapshots').rglob('*.json')),reverse=True)[:60]
    atomic(output/'index.html',html_page(view,history,name))
    return {'snapshot':name,'research_status':view.get('research',{}).get('status'),'web_status':view.get('web',{}).get('status')}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'reports/internal/product-usage');ap.add_argument('--input',type=Path);ap.add_argument('--quiet',action='store_true');args=ap.parse_args()
    try:
        attempt=json.loads(args.input.read_text()) if args.input else fetch()
        if args.input:attempt['mode']='offline_fixture_or_replay'
    except (OSError,ValueError,subprocess.SubprocessError):attempt={'schema_version':1,'mode':'production','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'research':{'status':'unknown'},'web':{'status':'unknown'}}
    result=save(attempt,args.output)
    if not args.quiet:print(json.dumps({'internal_dashboard':str(args.output/'index.html'),**result},ensure_ascii=False))
    return 0 if all(attempt.get(key,{}).get('status')=='observed' for key in ('research','web')) else 2


if __name__=='__main__':raise SystemExit(main())
