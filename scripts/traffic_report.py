#!/usr/bin/env python3
"""文书查真实流量看板 —— 两个口径并排,别再只看一个数

为什么有这个(2026-08-18):
  Jack 问「最近访问量多少」,第一版按 nginx 裸日志算出日均 2 万 PV,是假的。
  真值约 58。差 300 倍。四层污染:后端 API 25.6 万、自己人(EPN+服务器回源)2.9 万、
  伪装 Chrome 的爬虫、伪造 baidu referer 的腾讯云扫描器(占「搜索来源」的 39%)。

  所以同一天做了两件事:
    ① 上了首方分析像素 /px.gif —— 只有真浏览器跑 JS 才会打,天然干净。08-18 14:00 起有数据。
    ② 把 referer 口径的清洗规则固化下来 —— 这个能回溯,是唯一能看历史趋势的东西。

  两个口径都放进看板:像素看「现在有多少真人」,referer 看「搜索这条线是涨是跌」。

⚠️ 像素也不是绝对干净:实测 Bytespider(字节爬虫)会跑 JS 并打像素。所以像素日志仍要按 UA 过滤,
   只是量小、UA 干净,比主日志好筛得多。

用法:
  python3 traffic_report.py             # 终端输出
  python3 traffic_report.py --html out.html
"""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HOST = "root@114.132.74.235"
PX_LOG = "/www/wwwlogs/wenshucha.px.log"
MAIN_LOG = "/www/wwwlogs/wenshucha.com.log"
TOB_LOG = "/www/wwwlogs/tob.wenshucha.com.log"

# 远端一次跑完,只回传 JSON —— 日志 180MB,别拉回本地
REMOTE = r'''
import re, json, os
from collections import Counter, defaultdict
from datetime import datetime, timedelta

LINE = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) ([^"]*?) \S+" (\d{3}) (\d+) "([^"]*)" "([^"]*)"')
MON = {m: i for i, m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(), 1)}
BOT = re.compile(r'bot|spider|crawler|slurp|bytespider|python-requests|curl|wget|headless|'
                 r'scrapy|okhttp|go-http|java/|semrush|ahrefs|petal|gptbot|claudebot|ccbot|'
                 r'perplexity|amazonbot|dataforseo|censys|zgrab', re.I)
OURS = {'202.68', '114.132'}          # Jack 的 EPN 出口 + 服务器自己回源
SRC = re.compile(r'baidu|google|bing|sogou|so\.com|360|zhihu|baijiahao|toutiao|doubao|'
                 r'yuanbao|chatgpt|perplexity|kimi|metaso|weixin|xiaohongshu', re.I)
# 扫描器伪造 referer 时打的路径:站上根本没有这些东西
FAKE = re.compile(r'^/(files/|images/|portfolio\.html|search\?|.*\.(php|asp|jsp|xlsx|zip|sql|bak))', re.I)

def ts(s):
    d, t = s.split(':', 1); day, mo, yr = d.split('/')
    return datetime(int(yr), MON[mo], int(day), int(t[0:2]), int(t[3:5]), int(t[6:8]))

def norm(ref):
    h = ref.split('/')[2] if '://' in ref else ref[:24]
    h = re.sub(r'^(www|cn|m)\.', '', h).split(':')[0]
    for k, v in (('baidu', '百度'), ('bing', 'Bing'), ('google', 'Google'), ('zhihu', '知乎'),
                 ('baijiahao', '百家号'), ('so.com', '360'), ('sogou', '搜狗'),
                 ('doubao', '豆包'), ('yuanbao', '元宝'), ('chatgpt', 'ChatGPT'),
                 ('perplexity', 'Perplexity'), ('kimi', 'Kimi'), ('metaso', '秘塔')):
        if k in h:
            return v
    return h

out = {}

# ① 像素口径 —— 真浏览器
px = {'days': {}, 'paths': Counter(), 'refs': Counter(), 'bots': 0, 'ours': 0, 'total': 0}
if os.path.exists('%(PX)s'):
    for raw in open('%(PX)s', 'rb'):
        m = LINE.match(raw.decode('utf-8', 'replace'))
        if not m: continue
        ip, t, meth, path, code, size, ref, ua = m.groups()
        px['total'] += 1
        if BOT.search(ua): px['bots'] += 1; continue
        if '.'.join(ip.split('.')[:2]) in OURS: px['ours'] += 1; continue
        d = ts(t).strftime('%%Y-%%m-%%d')
        q = dict(p.split('=', 1) for p in path.split('?', 1)[-1].split('&') if '=' in p)
        import urllib.parse as U
        px['days'].setdefault(d, {'pv': 0, 'ips': []})
        px['days'][d]['pv'] += 1
        px['days'][d]['ips'].append(ip)
        px['paths'][U.unquote(q.get('p', '?'))[:48]] += 1
        r = U.unquote(q.get('r', ''))
        if r and 'wenshucha.com' not in r: px['refs'][norm(r)] += 1
for d in px['days']: px['days'][d]['uv'] = len(set(px['days'][d].pop('ips')))
px['paths'] = px['paths'].most_common(15); px['refs'] = px['refs'].most_common(12)
out['pixel'] = px

# ② referer 口径 —— 能回溯,看趋势
now = datetime.now(); win = {'近30天': 30, '前30天': 60, '再前30天': 90}
ref_b = {k: Counter() for k in win}; land = Counter(); fake_n = 0; daily = defaultdict(Counter)
for raw in open('%(MAIN)s', 'rb'):
    m = LINE.match(raw.decode('utf-8', 'replace'))
    if not m: continue
    ip, t, meth, path, code, size, ref, ua = m.groups()
    if not ref or ref == '-' or 'wenshucha.com' in ref or not SRC.search(ref): continue
    if code != '200' or FAKE.match(path): fake_n += 1; continue
    T = ts(t); age = (now - T).days
    e = norm(ref)
    for k, dmax in win.items():
        if age < dmax and age >= dmax - 30: ref_b[k][e] += 1; break
    if age < 30:
        land[path.split('?')[0][:44]] += 1
        daily[T.strftime('%%Y-%%m-%%d')][e] += 1
out['referer'] = {'windows': {k: v.most_common() for k, v in ref_b.items()},
                  'fake_dropped': fake_n, 'landing': land.most_common(12),
                  'daily': {d: dict(c) for d, c in sorted(daily.items())[-30:]}}

# ③ tob 子站(知乎深链的落点)—— 08-18 才开始有日志
tob = {'total': 0, 'refs': Counter(), 'paths': Counter(), 'since': None}
if os.path.exists('%(TOB)s'):
    for raw in open('%(TOB)s', 'rb'):
        m = LINE.match(raw.decode('utf-8', 'replace'))
        if not m: continue
        ip, t, meth, path, code, size, ref, ua = m.groups()
        if BOT.search(ua) or '.'.join(ip.split('.')[:2]) in OURS: continue
        tob['total'] += 1
        if tob['since'] is None: tob['since'] = ts(t).strftime('%%Y-%%m-%%d %%H:%%M')
        if ref and ref != '-' and 'wenshucha.com' not in ref: tob['refs'][norm(ref)] += 1
        tob['paths'][path.split('?')[0][:40]] += 1
tob['refs'] = tob['refs'].most_common(10); tob['paths'] = tob['paths'].most_common(10)
out['tob'] = tob

print(json.dumps(out, ensure_ascii=False))
''' % {"PX": PX_LOG, "MAIN": MAIN_LOG, "TOB": TOB_LOG}


def fetch():
    """日志在生产机上。本机(Mac)走 SSH;如果就在生产机上跑(daily_run.sh),直接就地执行。"""
    if Path(MAIN_LOG).exists():          # 已经在生产机上
        r = subprocess.run(["python3", "-"], input=REMOTE,
                           capture_output=True, text=True, timeout=300)
    else:
        r = subprocess.run(["ssh", "-o", "ConnectTimeout=45", HOST, "python3 -"],
                           input=REMOTE, capture_output=True, text=True, timeout=300)
    line = [l for l in r.stdout.splitlines() if l.startswith("{")]
    if not line:
        print("取数失败:", r.stderr[-500:], file=sys.stderr)
        sys.exit(2)
    return json.loads(line[-1])


def render_text(d):
    px, rf, tob = d["pixel"], d["referer"], d["tob"]
    print("=" * 58)
    print("① 首方像素口径(只有真浏览器会打,08-18 14:00 起)")
    print("=" * 58)
    if not px["days"]:
        print("  还没有数据 —— 像素刚上,等真人来访。")
    for day in sorted(px["days"]):
        v = px["days"][day]
        print(f"  {day}   PV {v['pv']:>5}   UV {v['uv']:>4}")
    print(f"  (同期剔除:爬虫 {px['bots']} · 自己人 {px['ours']} · 总请求 {px['total']})")
    if px["refs"]:
        print("\n  来源:")
        for k, v in px["refs"]: print(f"    {k:<16}{v:>5}")
    if px["paths"]:
        print("\n  页面:")
        for k, v in px["paths"][:8]: print(f"    {k:<44}{v:>5}")

    print("\n" + "=" * 58)
    print("② referer 口径(可回溯,看趋势)")
    print("=" * 58)
    for k in ("再前30天", "前30天", "近30天"):
        rows = rf["windows"].get(k) or []
        tot = sum(v for _, v in rows)
        s = " / ".join(f"{a} {b}" for a, b in rows[:6])
        print(f"  {k:<8}{tot:>5} 次  日均 {tot/30:>4.1f}   {s}")
    print(f"\n  被判为伪造 referer 剔除:{rf['fake_dropped']} 次")
    print("\n  落地页:")
    for k, v in rf["landing"][:8]: print(f"    {k:<44}{v:>5}")

    print("\n" + "=" * 58)
    print("③ tob.wenshucha.com(知乎深链的落点)")
    print("=" * 58)
    print(f"  日志自 {tob['since']} 起 · 非机器请求 {tob['total']}")
    for k, v in tob["refs"]: print(f"    {k:<16}{v:>5}")
    if not tob["refs"]: print("    (还没有外部来源)")




# ——————————————————————————————————————————————
# 日报模式:2026-08-18 Jack 定案「以后每天的日报就给访问数和访问来源」
# 口径纪律(别再退化成裸数):
#   · 报昨天整天,不报今天 —— 09:00 跑的时候今天才过了 9 小时,拿来比会一直显示"跌"
#   · 访问数以像素为准(只有真浏览器跑 JS),不用 nginx 裸行数
#   · 来源已剔掉伪造 referer(腾讯云 43.x 段冒充百度打不存在的路径,占原始数的 39%)
#   · 样本太小的时候明说"样本小",不给百分比 —— 日均只有个位数,涨跌%全是噪声
# ——————————————————————————————————————————————
def render_daily(d):
    from datetime import date, timedelta
    px, rf, tob = d["pixel"], d["referer"], d["tob"]
    y = (date.today() - timedelta(days=1)).isoformat()
    y2 = (date.today() - timedelta(days=2)).isoformat()
    L = []

    # ① 访问数(像素口径)
    yd = px["days"].get(y)
    if yd:
        prev = px["days"].get(y2)
        delta = ""
        if prev and prev["pv"]:
            pct = (yd["pv"] - prev["pv"]) / prev["pv"] * 100
            delta = f"({pct:+.0f}%)" if abs(pct) >= 10 else "(基本持平)"
        L.append(f"*📊 昨日访问:* {yd['pv']} PV · {yd['uv']} 人 {delta}")
        vals = [v["pv"] for k, v in sorted(px["days"].items())[-7:]]
        if len(vals) >= 3:
            L.append(f"_近 {len(vals)} 天日均 {sum(vals)/len(vals):.0f} PV_")
    else:
        n = len(px["days"])
        L.append(f"*📊 昨日访问:* 像素暂无昨日数据"
                 + (f"(已累计 {n} 天)" if n else "(像素 08-18 才上线)"))

    # ② 访问来源(referer 口径,可回溯)
    day_src = rf["daily"].get(y) or {}
    if day_src:
        tot = sum(day_src.values())
        pairs = sorted(day_src.items(), key=lambda kv: -kv[1])
        L.append(f"*🔎 昨日搜索/AI 来源:* 共 {tot} 次 —— "
                 + "、".join(f"{k} {v}" for k, v in pairs))
    else:
        L.append("*🔎 昨日搜索/AI 来源:* 0 次")

    # ③ 30 天构成(单日样本太小,月度构成才是能看的)
    w = rf["windows"].get("近30天") or []
    if w:
        tot30 = sum(v for _, v in w)
        L.append(f"_近 30 天合计 {tot30} 次(日均 {tot30/30:.1f})· "
                 + " / ".join(f"{k} {v}" for k, v in w[:4]) + "_")

    # ④ 知乎深链有没有真导流 —— 这是目前唯一在建的转化路径
    if tob["refs"]:
        L.append("*🔗 tob 子站外部来源:* "
                 + "、".join(f"{k} {v}" for k, v in tob["refs"][:5]))

    return "\n".join(L)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--daily", action="store_true", help="日报用的紧凑块")
    ap.add_argument("--dump", help="把原始 JSON 存到文件")
    a = ap.parse_args()
    data = fetch()
    if a.dump:
        Path(a.dump).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif a.daily:
        print(render_daily(data))
    else:
        render_text(data)
