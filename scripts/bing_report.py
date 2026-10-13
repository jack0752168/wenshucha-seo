#!/usr/bin/env python3
"""Persist verified Bing UI/API readings; never substitute traffic pixels for CTR."""
import argparse
import datetime as dt
import fcntl
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / 'state/bing-search-performance.json'
SGT = dt.timezone(dt.timedelta(hours=8))
TARGET = 'https://tob.wenshucha.com/cases'
REASONS = {'login_required', 'browser_busy', 'data_unavailable', 'tool_policy', 'network_error'}

def timestamp(s):
    value = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    if value.tzinfo is None: raise ValueError('timestamp needs timezone')
    return value

def validate(reading, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if reading.get('site') != 'https://wenshucha.com/' or reading.get('scope') != 'query_served_page_web' or reading.get('query') != '裁判文书' or reading.get('url') != TARGET:
        raise ValueError('wrong site or scope')
    observed = timestamp(reading['observed_at'])
    start, end = [dt.date.fromisoformat(reading[k]) for k in ['date_start','date_end']]
    if observed > now + dt.timedelta(minutes=5) or start > end or end >= observed.astimezone(SGT).date(): raise ValueError('immature or future dates')
    for key in ['impressions','clicks']:
        if type(reading.get(key)) is not int or reading[key] < 0: raise ValueError('invalid counts')
    if reading['clicks'] > reading['impressions']: raise ValueError('inconsistent counts')
    if reading.get('source') not in {'bing_webmaster_csv','bing_webmaster_ui','bing_webmaster_api'}: raise ValueError('unverified source')
    if not isinstance(reading.get('evidence'), str) or not reading['evidence'].strip(): raise ValueError('evidence required')
    result = {key: reading[key] for key in ['site','scope','query','url','observed_at','date_start','date_end','impressions','clicks','source','evidence']}
    if reading.get('avg_position') is not None:
        pos = reading['avg_position']
        if isinstance(pos, bool) or not isinstance(pos, (float,int)) or not math.isfinite(pos) or pos <= 0: raise ValueError('invalid position')
        result['avg_position'] = pos
    # Ratio of sums, not an average of rounded daily percentages.
    result['ctr'] = result['clicks'] / result['impressions'] if result['impressions'] else None
    return result

def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {'history': [], 'latest': None}

def update(reading=None, reason=None):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load()
        if reading:
            reading = validate(reading)
            if state.get('latest') and timestamp(reading['observed_at']) < timestamp(state['latest']['observed_at']): raise ValueError('older reading cannot overwrite latest')
            state['latest'] = reading
            state['history'] = (state.get('history', []) + [reading])[-90:]
            state['last_attempt'] = {'at':reading['observed_at'],'status':'verified'}
        else:
            if reason not in REASONS: raise ValueError('unsupported failure')
            state['last_attempt'] = {'at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':reason}
        temp = STATE.with_suffix('.tmp')
        temp.write_text(json.dumps(state,ensure_ascii=False)+'\n');temp.chmod(0o600);temp.replace(STATE)
        return state

def publish(state):
    # Validated aggregate data only. No browser credentials or API keys leave the Mac.
    code = "import pathlib\np=pathlib.Path('/opt/wenshucha-seo/state/bing-search-performance.json')\np.parent.mkdir(parents=True,exist_ok=True)\nt=p.with_suffix('.incoming');t.write_text(" + repr(json.dumps(state,ensure_ascii=False)) + ");t.chmod(0o600);t.replace(p)\nprint('bing snapshot synced')\n"
    r = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','root@114.132.74.235','python3 -'],input=code,capture_output=True,text=True,timeout=45)
    if r.returncode: raise RuntimeError('snapshot sync failed; local evidence retained')

def report(state, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    reading = state.get('latest')
    if not reading: return '*📈 Bing 點擊率:* 尚無核驗數據，未知，不報0。'
    reading = validate(reading, now)
    age = (now-timestamp(reading['observed_at'])).total_seconds()/3600
    attempt = state.get('last_attempt') or {}
    notes = []
    if age >= 36: notes.append(f'讀數已 {age/24:.1f} 天未更新')
    if attempt.get('status') not in (None,'verified'): notes.append('本輪讀取受阻：'+attempt['status'])
    ctr = f"{reading['ctr']:.2%}" if reading['ctr'] is not None else '無曝光，CTR未定義'
    verified = timestamp(reading['observed_at']).astimezone(SGT).strftime('%m/%d %H:%M')
    line = f"*📈 Bing 點擊率:* {ctr} · 點擊 {reading['clicks']} / 曝光 {reading['impressions']}（{reading['date_start']}～{reading['date_end']}；最近核驗 {verified}）"
    line += '\n_範圍：Web「裁判文书」→ /cases；平台成熟窗口，非昨日單日或全站。_'
    position = reading.get('avg_position')
    position_label = f'{position:.2f}' if position is not None else '未知'
    line += f'\n_平台均位 {position_label}；同頁／查詢的裝置交叉與其他詞構成未核驗，不以整域分布代替。_'
    if notes: line += '\n⚠️ '+ '；'.join(notes)+'；以上為最後核驗值，不冒充今日新數據。'
    return line

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['record','unavailable','report']);ap.add_argument('--input');ap.add_argument('--reason',choices=sorted(REASONS));ap.add_argument('--sync-server',action='store_true');ap.add_argument('--json',action='store_true');args=ap.parse_args()
    if args.action=='record':
        if not args.input: raise ValueError('input required')
        state=update(reading=json.loads(Path(args.input).read_text()))
    elif args.action=='unavailable': state=update(reason=args.reason)
    else: state=load()
    if args.sync_server: publish(state)
    print(json.dumps(state,ensure_ascii=False) if args.json else report(state))

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,KeyError,RuntimeError,subprocess.TimeoutExpired):
        print('*📈 Bing 點擊率:* 資料讀取或同步失敗，未知；不得填0或冒充已更新。')
        raise SystemExit(2)
