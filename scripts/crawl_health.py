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

每天检查六件事(超标 → 日报置顶红字):
  1. 百度抓取集中度:首页占比 > 85% = 蜘蛛进不了内页
  2. 百度覆盖率:sitemap 声明的 URL 里,百度从来没抓过的比例
  3. 百度自己有没有读 robots/sitemap(不能拿 Google/Bing 的抓取冒充百度)
  4. 蜘蛛吃到的 404 比例(死链烧抓取预算)
  5. 推送→抓取转化:昨天/近7天推给百度的 URL,到底有没有被抓
     (转化率是判断「推送这条通道值不值得占配额」的唯一标准)
  6. 已收录的 MCP 子站契约:核心产品回链/ICP/私钥路径是否回归

用法:
  python3 crawl_health.py              # markdown(日报用)
  python3 crawl_health.py --json      # 结构化(含完整未抓清单,供 push_baidu 排队)
  python3 crawl_health.py --days 30
"""
import argparse
import gzip
import json
import re
import socket
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUSH_LOG = ROOT / "state" / "push_log.jsonl"     # push_baidu.py 每天成功后追加
IP_CACHE = ROOT / "state" / "bot_ip_cache.json"  # ip → 反查主机名(FCrDNS 结果缓存)
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

# ── UA 不算数,IP 才算数(2026-07-29 加) ────────────────────────────────
# 为什么:User-Agent 谁都能伪造。我们自己每天用 `curl -A Baiduspider` 验页面是否
# 对百度可见,这些自测请求会被按 UA 统计成"百度抓了内页",把「百度覆盖 x/N」
# 和「推送转化」一起刷成假绿灯(2026-07-29 实锤:近 7 天所谓 12 个被百度抓过的
# 内页,全部来自本机 VPN 出口 202.68.183.224 的自测 curl;真百度只抓了 / )。
# 判定方法 = 各家官方推荐的 FCrDNS:反查 IP 得主机名 → 主机名后缀须属该引擎 →
# 再正查主机名确认解析回同一 IP。三步都过才算真蜘蛛。
BOT_RDNS_SUFFIX = {
    "百度": (".crawl.baidu.com", ".baidu.com", ".baidu.jp"),
    "Google": (".googlebot.com", ".google.com"),
    "Bing": (".search.msn.com",),
    "360": (".360.cn", ".so.com", ".qihoo.net"),
    "搜狗": (".sogou.com",),
}
# rDNS 查不到时的兜底(仅百度:国内 DNS 抖动概率高,别因为一次解析失败就误报
# 「百度一次都没来」)。这几段是日志里已被 FCrDNS 确认过的百度自有段。
BAIDU_FALLBACK_PREFIX = ("220.181.", "116.179.", "111.206.", "180.76.",
                         "123.125.71.", "180.101.24", "220.196.160.", "59.83.208.")


def load_ip_cache():
    try:
        return json.loads(IP_CACHE.read_text())
    except Exception:
        return {}


def save_ip_cache(cache):
    try:
        IP_CACHE.parent.mkdir(parents=True, exist_ok=True)
        IP_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
    except Exception:
        pass


def rdns_host(ip, cache):
    """FCrDNS 的前两步(反查 + 正查确认),结果永久缓存。返回主机名或 ''。"""
    if ip in cache:
        return cache[ip]
    socket.setdefaulttimeout(3)   # 13 个月日志里有上千个爬虫 IP,不设上限会把日报拖死
    host = ""
    try:
        h = socket.gethostbyaddr(ip)[0]
        # 正查确认:防止别人把自己的 rDNS 设成 xxx.baidu.com
        try:
            _, _, ips = socket.gethostbyname_ex(h)
            host = h if ip in ips else ""
        except Exception:
            host = h            # 正查失败不算作弊证据,接受反查结果
    except socket.herror:
        host = ""               # 无 PTR 记录 = 不是任何官方蜘蛛
    except Exception:
        host = "?"              # DNS 抖动/超时,不下结论,走兜底
    cache[ip] = host
    return host


def is_real_bot(ip, bot, cache):
    host = rdns_host(ip, cache)
    if host == "?":             # 解析不了 → 只有百度走网段兜底,其余按不可信处理
        return bot == "百度" and ip.startswith(BAIDU_FALLBACK_PREFIX)
    if not host:
        return False
    return host.lower().endswith(BOT_RDNS_SUFFIX.get(bot, ()))


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
    discovery_all = {n: Counter() for n in BOTS}    # 各蜘蛛全历史 robots/sitemap 读取
    discovery_window = {n: Counter() for n in BOTS} # 各蜘蛛近 N 天 robots/sitemap 读取
    cache = load_ip_cache()
    spoof = Counter()                   # 被剔除的伪装请求(近 N 天),按「bot@ip」计
    opener = gzip.open if log.suffix == ".gz" else open

    # 第一遍:只挑出爬虫行(13 个月日志 56 万行里约 10 万行),顺手收集待验 IP
    rows = []
    with opener(log, "rt", errors="ignore") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            bot = next((n for n, rx in BOTS.items() if rx.search(line)), None)
            if not bot:
                continue
            ip, ts_s, _meth, path, status = m.groups()
            rows.append((ip, bot, parse_ts(ts_s), norm_path(path), status))

    # 反查并发做:全量日志里有近 2000 个爬虫 IP,串行 rDNS 会把日报拖到一小时以上
    todo = sorted({ip for ip, _b, _t, _p, _s in rows} - set(cache))[:400]
    # 每次最多解析 400 个新 IP:调用方(push_baidu/kw_registry)给的 subprocess 超时是
    # 120 秒,缓存丢了的那次全量解析会超时 → 宁可分几天补齐,不要让整条链断掉。
    if todo:
        with ThreadPoolExecutor(max_workers=32) as ex:
            for ip, host in zip(todo, ex.map(lambda i: rdns_host(i, {}), todo)):
                cache[ip] = host

    verdict = {}                        # (ip,bot) → 真假,单次运行内只判一次
    for ip, bot, ts, clean, status in rows:
        key = (ip, bot)
        if key not in verdict:
            verdict[key] = is_real_bot(ip, bot, cache)
        if not verdict[key]:            # UA 伪装(含我们自己的自测 curl)→ 一律不算抓取
            if not ts or ts >= cutoff:
                spoof[f"{bot}@{ip}"] += 1
            continue
        ever_any.add(clean)
        if bot == "百度" and ts:
            baidu_ts[clean].append(ts)
        resource = None
        if "sitemap" in clean.lower():
            resource = "sitemap"
        elif clean.lower() == "/robots.txt":
            resource = "robots"
        if resource:
            discovery_all[bot][resource] += 1
        if ts and ts < cutoff:
            continue
        s = stats[bot]
        s["hits"] += 1
        s["paths"][clean] += 1
        s["status"][status] += 1
        s.setdefault("path_status", Counter())[(clean, status)] += 1
        if resource:
            discovery_window[bot][resource] += 1
    save_ip_cache(cache)
    return stats, ever_any, baidu_ts, discovery_all, discovery_window, spoof


def canonical_probe():
    """每天主动验唯一首页；不跟跳转，否则 /index.html 回 200 或循环都会被藏起来。"""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect)

    def one(url):
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "wenshucha-seo-canonical-check"})
        try:
            with opener.open(req, timeout=15) as resp:
                return resp.status, resp.headers.get("Location", "")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Location", "")
        except Exception as exc:
            return 0, str(exc)

    root = one("https://www.wenshucha.com/")
    index = one("https://www.wenshucha.com/index.html")
    return {"root_status": root[0], "index_status": index[0], "index_location": index[1]}


def mcp_contract_probe():
    """唯一已被百度收录的子站不能再把流量送进死链，也不能暴露私钥台账。"""
    def get(url, read_body=False):
        req = urllib.request.Request(url, headers={"User-Agent": "wenshucha-seo-contract-check"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read(200_000).decode("utf-8", errors="ignore") if read_body else ""
                return resp.status, body
        except urllib.error.HTTPError as exc:
            return exc.code, ""
        except Exception as exc:
            return 0, str(exc)

    status, html = get("https://mcp.wenshucha.com/", read_body=True)
    private_status, _ = get("https://mcp.wenshucha.com/trial-keys-private.md")
    issues = []
    if status != 200:
        issues.append(f"首页 HTTP {status}")
    else:
        required = {
            "智能检索回链": "https://www.wenshucha.com/case-search/",
            "AI 助手回链": "https://www.wenshucha.com/legal-ai/",
            "完整备案号": "粤ICP备2025437990号-2",
        }
        for label, needle in required.items():
            if needle not in html:
                issues.append(f"缺{label}")
        if "paileme.wenshucha.com" in html or "peilema.wenshucha.com" in html:
            issues.append("仍含赔了吗死链")
    if private_status != 404:
        issues.append(f"私钥路径应 404,实际 {private_status}")
    return {
        "home_status": status,
        "private_status": private_status,
        "issues": issues,
        "ok": not issues,
    }


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

    stats, ever_any, baidu_ts, discovery_all, discovery_window, spoof = scan(log, days)
    declared = sitemap_urls()
    baidu_ever = set(baidu_ts)
    baidu_uncrawled = sorted(declared - baidu_ever) if declared else []
    any_uncrawled = sorted(declared - ever_any) if declared else []
    conv = push_conversion(baidu_ts)
    canonical = canonical_probe()
    mcp_contract = mcp_contract_probe()

    bd = stats["百度"]
    home_hits = bd["paths"].get("/", 0) + bd["paths"].get("/index.html", 0)
    home_share = (home_hits / bd["hits"]) if bd["hits"] else 0.0
    tot_st = sum(bd["status"].values()) or 1
    r404 = bd["status"].get("404", 0) / tot_st

    alerts = []
    if canonical["root_status"] != 200:
        alerts.append(
            f"🔴 **唯一首页探针失败**:根首页应为 200,实际 {canonical['root_status']} — 立即检查重写循环/站点故障"
        )
    if canonical["index_status"] != 301 or canonical["index_location"] != "https://www.wenshucha.com/":
        alerts.append(
            f"🔴 **重复首页未合并**:/index.html 应 301 到 /,实际 "
            f"{canonical['index_status']} → {canonical['index_location'] or '无 Location'}"
        )
    if not mcp_contract["ok"]:
        alerts.append("🔴 **MCP 已收录入口回归**:" + "；".join(mcp_contract["issues"]))
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
        if discovery_all["百度"]["sitemap"] == 0:
            alerts.append("🔴 **百度从未读取 sitemap.xml** — 其他蜘蛛读取不算百度发现,检查站点信任/robots/后端提交")
        if discovery_all["百度"]["robots"] == 0:
            alerts.append("🟠 **百度从未读取 robots.txt** — 内页发现主要依赖首页内链与主动推送")
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
        "baidu_sitemap_fetch_all_time": discovery_all["百度"]["sitemap"],
        "baidu_robots_fetch_all_time": discovery_all["百度"]["robots"],
        "baidu_sitemap_fetch_window": discovery_window["百度"]["sitemap"],
        "baidu_robots_fetch_window": discovery_window["百度"]["robots"],
        # 兼容旧历史字段,但告警永远只看百度自己的计数。
        "sitemap_fetch_all_time": sum(v["sitemap"] for v in discovery_all.values()),
        "discovery_fetch_all_time": {k: dict(v) for k, v in discovery_all.items()},
        "discovery_fetch_window": {k: dict(v) for k, v in discovery_window.items()},
        "canonical_probe": canonical,
        "mcp_contract_probe": mcp_contract,
        "push_conversion": conv,
        "other_bots": {k: v["hits"] for k, v in stats.items() if k != "百度"},
        "spoofed_hits": sum(spoof.values()),
        "spoofed_top": spoof.most_common(5),
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
    if d.get("spoofed_hits"):
        # 这句必须挂在同一行:日报只透传以「百度抓」开头的那一行,另起一行会被丢掉,
        # 而「数字只算真蜘蛛」正是这份数据可信的前提,不能在日报里消失。
        line += f" · 已剔除 UA 伪装 {d['spoofed_hits']} 次(含本机自测 curl)"
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
