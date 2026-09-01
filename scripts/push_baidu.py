#!/usr/bin/env python3
"""百度普通收录 API 推送(每天 daily_run 自动调用)

文书查面向国内市场,百度是主战场。
token 只放 secrets/baidu_push_token(2026-07-22 起,曾明文泄露在公开仓库);
config.yml 里的 baidu_push_token 仅作历史兜底,应保持为空。

老司机版选队逻辑(2026-07-22 重写,此前的教训都写在下面,别改回去):
  1. 配额 = 每天 10 条,超量整批被拒 → 永远只发 LIMIT 条
  2. 首页永不推:nginx 日志实证百度 13 个月抓 23113 次、98.4% 全在首页,
     再推是白扔配额还把蜘蛛往首页引
  3. 优先队列 = 闭环:先推「百度从来没抓过的页」(crawl_health 从 nginx 日志算),
     但 14 天内推过的自动冷却,先覆盖没推过的页;抓过了自动出队
  4. 推前验活:每条先 GET 线上,非 200 不占配额并写 state/push_broken.json
     (曾把 /calc 这种 404 天天推给百度)
  5. 当天已推成功就跳过(幂等,防手动重跑浪费)
  6. 每次成功写 state/push_log.jsonl,crawl_health 隔天用它算「推送→抓取转化率」
     —— 转化率是这条通道唯一的疗效指标
"""
import json
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pip3 install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yml").read_text())
STATE_DIR = ROOT / "state"
PUSH_STATE = STATE_DIR / "push_state.json"     # {date, success} 幂等标记
PUSH_LOG = STATE_DIR / "push_log.jsonl"        # 追加式台账,转化率数据源
BROKEN = STATE_DIR / "push_broken.json"        # 验活失败的 URL,供人排查

TOKEN = (CONFIG.get("global") or {}).get("baidu_push_token", "").strip()
if not TOKEN:
    SECRET = ROOT / "secrets" / "baidu_push_token"
    if SECRET.exists():
        TOKEN = SECRET.read_text().strip()

# 2026-09-01：加 --site 参数，为把配额挪到 tob 做准备。
#   起因：主域索引量卡在 2、几十天零变化，而 nginx 日志实证百度**正在爬 tob 的真内容页**
#   （14 天 209 次，抓 /tob、/cases、/api/cases/search2），主域那边近 2 万次全砸首页。
#   主域推了十三个月毫无起色，继续占用每天 10 条配额是浪费。
#   ⚠️ 换 site 前该域名必须先在百度站长验证通过，否则整批落进 not_same_site 静默作废。
SITES = {
    "www": {"domain": "www.wenshucha.com",
            "alias": ("https://wenshucha.com",),
            "sitemap": "https://www.wenshucha.com/sitemap.xml"},
    "tob": {"domain": "tob.wenshucha.com",
            "alias": (),
            "sitemap": "https://tob.wenshucha.com/sitemap.xml"},
}
_sel = "www"
for _i, _a in enumerate(sys.argv):
    if _a == "--site" and _i + 1 < len(sys.argv):
        _sel = sys.argv[_i + 1]
SITE = SITES.get(_sel) or SITES["www"]
DOMAIN = SITE["domain"]
LIMIT = 10
PUSH_COOLDOWN_DAYS = 14
HOME = {f"https://{DOMAIN}", f"https://{DOMAIN}/"}


def normalize_for_baidu(url: str):
    """URL 必须和 site= 注册的主机完全一致,否则百度静默丢进 not_same_site。
    去锚点(百度把 /#x 当首页,白烧配额);非本站主机一律过滤。"""
    url = url.split("#", 1)[0]
    if not url:
        return None
    for a in SITE["alias"]:
        if url.startswith(a):
            return url.replace(a, f"https://{DOMAIN}", 1)
    if url.startswith(f"https://{DOMAIN}"):
        return url
    return None


def baidu_uncrawled_paths():
    """问 crawl_health 要「百度从来没抓过」的 path 清单(nginx 日志一手数据)。
    拿不到(比如在 Mac 上跑)就返回 None,退回轮转模式。"""
    try:
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "crawl_health.py"), "--json"],
            capture_output=True, text=True, timeout=120,
        )
        d = json.loads(out.stdout)
        if d.get("ok"):
            return set(d.get("baidu_uncrawled", []))
    except Exception:
        pass
    return None


def alive(url: str) -> bool:
    """推前验活:非 200 不许占配额。301 也算死 —— 该推跳转后的终点,不是起点。"""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "wenshucha-seo-push-check"})
    try:
        # 不跟随跳转没法用 urllib 简单做,改用 opener 禁止重定向
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        opener = urllib.request.build_opener(NoRedirect)
        with opener.open(req, timeout=15) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        return e.code == 200
    except Exception:
        return False


def last_push_times() -> dict:
    """读取成功推送台账。URL 最近一次推送时间用于冷却轮转,避免天天重推同 10 页。"""
    latest = {}
    if not PUSH_LOG.exists():
        return latest
    for line in PUSH_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            row = json.loads(line)
            ts = datetime.fromisoformat(row["ts"])
        except Exception:
            continue
        for raw in row.get("urls", []):
            u = normalize_for_baidu(raw)
            if u and (u not in latest or ts > latest[u]):
                latest[u] = ts
    return latest


def rotate_by_push_history(urls: list, latest: dict) -> list:
    """未推过 → 已过冷却期(最久未推优先) → 冷却中的最旧记录。

    同组保留 config/sitemap 的原始顺序,所以业务优先级不会丢;只有已经消耗过
    配额的 URL 才会向后让位。103 个未抓页因此约 11 天能全部覆盖一轮。
    """
    now = datetime.now()
    cutoff = now - timedelta(days=PUSH_COOLDOWN_DAYS)
    indexed = list(enumerate(urls))

    def key(item):
        i, u = item
        ts = latest.get(u)
        if ts is None:
            return (0, datetime.min, i)
        if ts < cutoff:
            return (1, ts, i)
        return (2, ts, i)

    return [u for _i, u in sorted(indexed, key=key)]


def select(urls: list) -> list:
    normalized = list(dict.fromkeys(u for u in (normalize_for_baidu(u) for u in urls) if u))
    normalized = [u for u in normalized if u not in HOME]
    if not normalized:
        return []

    uncrawled = baidu_uncrawled_paths()
    if uncrawled is not None:
        def path_of(u):
            p = u.replace("https://" + DOMAIN, "") or "/"
            return p
        # sitemap 里百度没抓过、但 config 忘了列的页,自动并进候选池
        # (config 顺序=业务优先级,所以补充页排在 config 页之后)
        known = {path_of(u) for u in normalized}
        extras = [f"https://{DOMAIN}{p}" for p in sorted(uncrawled)
                  if p not in known and p != "/"]
        if extras:
            normalized += extras
            print(f"(sitemap 补充 {len(extras)} 条 config 漏列的未抓页进候选池)")
        never = [u for u in normalized if path_of(u) in uncrawled]
        done = [u for u in normalized if path_of(u) not in uncrawled]
        print(f"(闭环队列:百度未抓 {len(never)} 条排最前,已抓 {len(done)} 条轮转保鲜)")
    else:
        never, done = [], normalized
        print("(拿不到 nginx 抓取数据,退回纯轮转)")

    # 不能用 never[:10]:在百度不抓取时会把同一批 10 页重复推一辈子。
    # 先按成功推送历史冷却轮转,让每日 10 条真正覆盖完整 sitemap。
    latest = last_push_times()
    never = rotate_by_push_history(never, latest)
    done = rotate_by_push_history(done, latest)
    cooling = sum(
        1 for u in never
        if u in latest and latest[u] >= datetime.now() - timedelta(days=PUSH_COOLDOWN_DAYS)
    )
    if never:
        print(f"(推送轮转:冷却 {PUSH_COOLDOWN_DAYS} 天,未抓队列中 {cooling} 条近期已推将后排)")

    slots = LIMIT
    picked = never[:slots]
    rest_slots = slots - len(picked)
    if rest_slots > 0 and done:
        picked += done[:rest_slots]

    # 验活:死的剔掉、记账,用候补顶上
    broken, out, pool = [], [], never[slots:] + done
    for u in picked:
        (out if alive(u) else broken).append(u)
    for u in pool:
        if len(out) >= LIMIT or len(out) >= len(picked):
            break
        if u not in out and u not in broken and alive(u):
            out.append(u)
    if broken:
        BROKEN.write_text(json.dumps(
            {"date": str(date.today()), "broken": broken}, ensure_ascii=False, indent=2))
        print(f"🟠 验活失败 {len(broken)} 条已剔除(见 state/push_broken.json):")
        for u in broken:
            print(f"   ✗ {u}")
    return out[:LIMIT]


def push(urls: list) -> int:
    endpoint = f"http://data.zz.baidu.com/urls?site=https://{DOMAIN}&token={TOKEN}"
    print(f"百度推送 {len(urls)} 个 URL:")
    for u in urls:
        print(f"  · {u}")
    req = urllib.request.Request(
        endpoint, data="\n".join(urls).encode("utf-8"),
        headers={"Content-Type": "text/plain"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(f"✓ 百度推送: HTTP {resp.status} → {body}")
            # 百度原样返回 success / remain / not_same_site / not_valid,
            # 以前只取 success 就丢掉了,导致「推送到底健不健康」事后无从复核
            # (2026-07-24:被推的 URL 域名和站长属性对不上会静默落进 not_same_site)
            try:
                api = json.loads(body)
            except Exception:
                api = {}
            try:
                success = int(api.get("success", 0))
            except Exception:
                success = 0
            STATE_DIR.mkdir(exist_ok=True)
            PUSH_STATE.write_text(json.dumps({"date": str(date.today()), "success": success}))
            if success > 0:
                # 百度可能同时返回 success 与逐条拒绝清单。不能简单记录
                # urls[:success]，否则被拒 URL 会误入 14 天冷却，真正成功页反而
                # 没有台账。先剔除明确拒绝项，再按 success 数截取。
                rejected = set(api.get("not_same_site") or []) | set(api.get("not_valid") or [])
                accepted = [u for u in urls if u not in rejected][:success]
                with PUSH_LOG.open("a") as f:
                    f.write(json.dumps({
                        "ts": datetime.now().isoformat(timespec="seconds"),
                        "urls": accepted,
                        "api": {k: api.get(k) for k in
                                ("success", "remain", "not_same_site", "not_valid")
                                if api.get(k) is not None},
                    }, ensure_ascii=False) + "\n")
            return 0
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"✗ 百度推送失败 HTTP {e.code}: {detail}")
        if "over quota" in detail:
            # 配额没了就是没了,标记今天别再试,明天队列自然重排
            STATE_DIR.mkdir(exist_ok=True)
            PUSH_STATE.write_text(json.dumps({"date": str(date.today()), "success": 0,
                                              "note": "over quota"}))
            return 0
        return 1


def main():
    if not TOKEN:
        print("⏭️  跳过百度推送:secrets/baidu_push_token 不存在")
        return 0
    plan_only = "--plan" in sys.argv
    if not plan_only and PUSH_STATE.exists():
        try:
            st = json.loads(PUSH_STATE.read_text())
            if st.get("date") == str(date.today()) and st.get("success", 0) > 0:
                print(f"⏭️  今天已推过 {st['success']} 条,跳过(幂等)")
                return 0
        except Exception:
            pass
    urls = []
    if DOMAIN == "www.wenshucha.com":
        for site in CONFIG["sites"]:
            if site["host"] in ("wenshucha.com", "www.wenshucha.com"):
                urls.extend(site["urls_to_push"])
    else:
        # tob 不在 config.yml 里管，直接吃它自己的 sitemap（237 条）
        try:
            xml = urllib.request.urlopen(SITE["sitemap"], timeout=20).read().decode("utf-8", "replace")
            import re as _re
            urls = _re.findall(r"<loc>([^<]+)</loc>", xml)
            # 2026-09-01 Jack 定案：主推【类案检索 /cases】，律师工作台 /tob 暂不推。
            # sitemap 是按站点结构排的，/tob 在最前、/cases 排第 9 —— 每天只有 10 条配额，
            # 照原序推等于把弹药打在不推的产品上。这里按主推优先级重排。
            # 见记忆 project_tob_push_cases_not_workbench
            PRIO = ("/cases", "/sifa", "/analytics", "/ai")
            def _rank(u):
                path = u.split(DOMAIN, 1)[-1] or "/"
                for i, pre in enumerate(PRIO):
                    if path.startswith(pre):
                        return (i, len(path))
                return (len(PRIO) + (1 if path.startswith("/tob") else 0), len(path))
            urls.sort(key=_rank)
            print(f"({DOMAIN} sitemap 取到 {len(urls)} 条，已按主推优先级重排：/cases 优先，/tob 垫底)")
        except Exception as e:
            print(f"取 {DOMAIN} sitemap 失败: {e}")
            return 0
    if not urls:
        print(f"没有可推的 {DOMAIN} URL")
        return 0
    picked = select(urls)
    if not picked:
        print("没有可推 URL")
        return 0
    if plan_only:
        print(f"(--plan 干跑,不占配额)明日队列 {len(picked)} 条:")
        for u in picked:
            print(f"  · {u}")
        return 0
    return push(picked)


if __name__ == "__main__":
    sys.exit(main())
