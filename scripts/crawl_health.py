#!/usr/bin/env python3
"""抓取漏斗体检 —— 每天回答「蜘蛛来没来、抓了啥、推送有没有用」

为什么有这个脚本(2026-07-22 Jack 发火):
  原来的日报只报「百度推送 HTTP 200 / sitemap 已刷新 / 健康检查全绿」——
  全是「我自己跑了没」,没有一条是「有没有用」。结果 13 个月里百度蜘蛛
  98.4% 的抓取砸在首页,41 篇 blog 只被抓 6 次、/data/ 0 次、sitemap 0 次,
  自动化天天报绿灯。nginx 日志就在本机,是唯一一手证据,却从没人看。

老司机漏斗(每级有自己的指标,断在哪级修哪级):
  推送 → 抓取 → 收录 → 展现 → 点击
  本脚本管前两级(nginx 日志);后三级靠 Mac 浏览器抓百度后台(rankings.py)。

每天检查五件事(超标 → 日报置顶红字):
  1. 百度抓取集中度:首页占比 > 85% = 蜘蛛进不了内页
  2. 百度覆盖率:sitemap 声明的 URL 里,百度从来没抓过的比例
  3. sitemap 本身有没有被蜘蛛读过(robots 指错时这里第一个发现)
  4. 蜘蛛吃到的 404 比例(死链烧抓取预算)
  5. 推送→抓取转化:昨天/近7天推给百度的 URL,到底有没有被抓
     (转化率是判断「推送这条通道值不值得占配额」的唯一标准)

用法:
  python3 crawl_health.py              # markdown(日报用)
  python3 crawl_health.py --json      # 结构化(含完整未抓清单,供 push_baidu 排队)
  python3 crawl_health.py --days 30
"""
import argparse
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUSH_LOG = ROOT / "state" / "push_log.jsonl"     # push_baidu.py 每天成功后追加
LOG_CANDIDATES = [
    "/www/wwwlogs/wenshucha.com.log",
    "/var/log/nginx/wenshucha.com.log",
]
SITEMAP = Path("/www/wwwroot/wenshucha.com/sitemap.xml")

# 阈值:超了就报警(定了就别悄悄放宽;要改带着理由改注释)
HOME_SHARE_MAX = 0.85      # 首页抓取占比上限
BAIDU_UNCRAWLED_MAX = 0.30 # sitemap 里百度从没抓过的比例上限
SPIDER_404_MAX = 0.05      # 蜘蛛吃 404 的比例上限

BOTS = {
    "百度": re.compile(r"Baiduspider", re.I),
    "Google": re.compile(r"Googlebot", re.I),
    "Bing": re.compile(r"bingbot", re.I),
    "360": re.compile(r"360Spider", re.I),
    "搜狗": re.compile(r"Sogou", re.I),
}
# nginx combined: ip - - [time] "METHOD path proto" status size "ref" "ua"
LINE = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)[^"]*" (\d{3}) ')


def find_log():
    for p in LOG_CANDIDATES:
        if Path(p).exists():
            return Path(p)
    return None


def parse_ts(s):
    try:
        return datetime.strptime(s.split()[0], "%d/%b/%Y:%H:%M:%S")
    except Exception:
        return None


def norm_path(p):
    p = p.split("?")[0].split("#")[0]
    return p or "/"


def sitemap_urls():
    """sitemap 里声明的 path 集合 —— 这是我们对搜索引擎的承诺清单。"""
    if not SITEMAP.exists():
        return set()
    try:
        txt = SITEMAP.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return set()
    out = set()
    for m in re.finditer(r"<loc>\s*([^<\s]+)\s*</loc>", txt):
        out.add(norm_path(re.sub(r"^https?://[^/]+", "", m.group(1)) or "/"))
    return out


def scan(log: Path, days: int):
    cutoff = datetime.now() - timedelta(days=days)
    stats = {n: {"hits": 0, "paths": Counter(), "status": Counter()} for n in BOTS}
    ever_any = set()                    # 任一蜘蛛全历史抓过
    baidu_ts = defaultdict(list)        # 百度单独记时间:Google 抓过≠百度抓过,混算会把盲区藏起来
    sitemap_fetch_all = 0
    opener = gzip.open if log.suffix == ".gz" else open
    with opener(log, "rt", errors="ignore") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            _ip, ts_s, _meth, path, status = m.groups()
            bot = next((n for n, rx in BOTS.items() if rx.search(line)), None)
            if not bot:
                continue
            clean = norm_path(path)
            ever_any.add(clean)
            ts = parse_ts(ts_s)
            if bot == "百度" and ts:
                baidu_ts[clean].append(ts)
            if "sitemap" in clean.lower():
                sitemap_fetch_all += 1
            if ts and ts < cutoff:
                continue
            s = stats[bot]
            s["hits"] += 1
            s["paths"][clean] += 1
            s["status"][status] += 1
    return stats, ever_any, baidu_ts, sitemap_fetch_all


def push_conversion(baidu_ts: dict, days: int = 7):
    """近 N 天推送的 URL,推送后到底被百度抓了没 —— 推送通道的疗效。"""
    if not PUSH_LOG.exists():
        return None
    now = datetime.now()
    rows = []
    for line in PUSH_LOG.read_text().splitlines():
        try:
            r = json.loads(line)
            ts = datetime.fromisoformat(r["ts"])
        except Exception:
            continue
        if (now - ts).days > days:
            continue
        for u in r.get("urls", []):
            rows.append((norm_path(re.sub(r"^https?://[^/]+", "", u)), ts))
    if not rows:
        return None
    crawled = lag_days = 0
    lags = []
    for path, pts in rows:
        after = [t for t in baidu_ts.get(path, []) if t >= pts]
        if after:
            crawled += 1
            lags.append((min(after) - pts).total_seconds() / 86400)
    return {
        "pushed": len(rows),
        "crawled": crawled,
        "rate": round(crawled / len(rows), 4),
        "median_lag_days": round(sorted(lags)[len(lags) // 2], 1) if lags else None,
    }


def build(days: int):
    log = find_log()
    if not log:
        return {"ok": False, "reason": "找不到 nginx 日志(本机可能不是站点服务器)"}

    stats, ever_any, baidu_ts, sitemap_fetch = scan(log, days)
    declared = sitemap_urls()
    baidu_ever = set(baidu_ts)
    baidu_uncrawled = sorted(declared - baidu_ever) if declared else []
    any_uncrawled = sorted(declared - ever_any) if declared else []
    conv = push_conversion(baidu_ts)

    bd = stats["百度"]
    home_hits = bd["paths"].get("/", 0) + bd["paths"].get("/index.html", 0)
    home_share = (home_hits / bd["hits"]) if bd["hits"] else 0.0
    tot_st = sum(bd["status"].values()) or 1
    r404 = bd["status"].get("404", 0) / tot_st

    alerts = []
    if bd["hits"] == 0:
        alerts.append(f"🔴 近 {days} 天**百度蜘蛛一次都没来** — 站点可能被降权或不可达")
    else:
        if home_share > HOME_SHARE_MAX:
            alerts.append(
                f"🔴 **抓取预算烧在首页**:百度近 {days} 天抓 {bd['hits']} 次,首页占 "
                f"{home_share:.0%}(阈值 {HOME_SHARE_MAX:.0%})→ 内页进不去,发文=白发"
            )
        if declared and len(baidu_uncrawled) / len(declared) > BAIDU_UNCRAWLED_MAX:
            alerts.append(
                f"🔴 **百度从没抓过 {len(baidu_uncrawled)}/{len(declared)} 个页面**"
                f"({len(baidu_uncrawled)/len(declared):.0%},阈值 {BAIDU_UNCRAWLED_MAX:.0%})"
                f" — 这些页在百度眼里不存在"
            )
        if sitemap_fetch == 0:
            alerts.append("🔴 **sitemap.xml 从来没被蜘蛛读过** — 先查 robots.txt 的 Sitemap 是否吃 301")
        if r404 > SPIDER_404_MAX:
            alerts.append(f"🟠 蜘蛛吃到 {r404:.0%} 的 404(阈值 {SPIDER_404_MAX:.0%})— 死链在烧预算")
    if conv and conv["pushed"] >= 5 and conv["rate"] < 0.2:
        alerts.append(
            f"🟠 **推送→抓取转化 {conv['rate']:.0%}**({conv['crawled']}/{conv['pushed']})"
            f" — 推送通道基本没换来抓取,别指望它,先修内链/权重"
        )

    return {
        "ok": True,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "days": days,
        "log": str(log),
        "baidu_hits": bd["hits"],
        "home_share": round(home_share, 4),
        "top_paths": bd["paths"].most_common(8),
        "status": dict(bd["status"]),
        "sitemap_declared": len(declared),
        "baidu_uncrawled_n": len(baidu_uncrawled),
        "baidu_uncrawled": baidu_uncrawled,      # 完整清单:push_baidu 用它排优先队列
        "any_uncrawled_n": len(any_uncrawled),
        "sitemap_fetch_all_time": sitemap_fetch,
        "push_conversion": conv,
        "other_bots": {k: v["hits"] for k, v in stats.items() if k != "百度"},
        "alerts": alerts,
    }


def render(d):
    if not d.get("ok"):
        return f"*🕷 抓取体检*:跳过（{d.get('reason')}）"
    L = [f"*🕷 抓取漏斗*（近 {d['days']} 天 · nginx 一手数据）"]
    L += d["alerts"] or ["✅ 抓取分布正常"]
    cov = d["sitemap_declared"] - d["baidu_uncrawled_n"]
    line = (f"百度抓 {d['baidu_hits']} 次 · 首页占 {d['home_share']:.0%} · "
            f"百度覆盖 {cov}/{d['sitemap_declared']}")
    c = d.get("push_conversion")
    if c:
        lag = f",中位 {c['median_lag_days']} 天" if c["median_lag_days"] is not None else ""
        line += f" · 推送转化 {c['crawled']}/{c['pushed']}{lag}"
    L.append(line)
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--jsonl", action="store_true",
                    help="单行紧凑 JSON(写 crawl_history.jsonl 用;多行会毁掉按行解析)")
    a = ap.parse_args()
    data = build(a.days)
    if a.jsonl:
        # 历史档不存完整未抓清单(每天 80+ 条会把文件撑爆),只留计数
        slim = {k: v for k, v in data.items() if k not in ("baidu_uncrawled", "top_paths")}
        print(json.dumps(slim, ensure_ascii=False))
    elif a.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render(data))
