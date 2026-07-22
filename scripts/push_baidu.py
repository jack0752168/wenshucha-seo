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
     抓过了自动出队;都抓过了才轮转保鲜 —— 不再人肉维护"必推名单"
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
from datetime import datetime, date
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

DOMAIN = "www.wenshucha.com"
LIMIT = 10
HOME = {"https://www.wenshucha.com", "https://www.wenshucha.com/"}


def normalize_for_baidu(url: str):
    """site=www 所以 URL 也要 www;去锚点(百度把 /#x 当首页,白烧配额);其他子域过滤。"""
    url = url.split("#", 1)[0]
    if not url:
        return None
    if url.startswith("https://wenshucha.com"):
        return url.replace("https://wenshucha.com", "https://www.wenshucha.com", 1)
    if url.startswith("https://www.wenshucha.com"):
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

    # 未抓的按 config 顺序(即业务优先级)排;轮转段按天错开起点
    slots = LIMIT
    picked = never[:slots]
    rest_slots = slots - len(picked)
    if rest_slots > 0 and done:
        start = (date.today().timetuple().tm_yday * rest_slots) % len(done)
        picked += (done + done)[start:start + rest_slots]

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
            try:
                success = int(json.loads(body).get("success", 0))
            except Exception:
                success = 0
            STATE_DIR.mkdir(exist_ok=True)
            PUSH_STATE.write_text(json.dumps({"date": str(date.today()), "success": success}))
            if success > 0:
                with PUSH_LOG.open("a") as f:
                    f.write(json.dumps({
                        "ts": datetime.now().isoformat(timespec="seconds"),
                        "urls": urls[:success] if success <= len(urls) else urls,
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
    for site in CONFIG["sites"]:
        if site["host"] in ("wenshucha.com", "www.wenshucha.com"):
            urls.extend(site["urls_to_push"])
    if not urls:
        print("config.yml 没有 wenshucha.com 主站 URL")
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
