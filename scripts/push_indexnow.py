#!/usr/bin/env python3
"""IndexNow 主动推送 URL → Bing / Yandex / Seznam / Naver

完全免费,不需要 API key 注册(只需在站点根目录放一个 {key}.txt 文件)
每日跑一次,把 config.yml 里 urls_to_push 推一遍
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pip3 install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yml").read_text())
KEY = CONFIG["global"]["indexnow_key"]

# IndexNow 通用端点(Bing 自动同步给 Yandex / Seznam / Naver)
ENDPOINT = "https://api.indexnow.org/IndexNow"


def push_host(host: str, urls: list) -> dict:
    """对单个 host 批量推 URL"""
    payload = {
        "host": host,
        "key": KEY,
        "keyLocation": f"https://{host}/{KEY}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {
                "host": host,
                "urls": len(urls),
                "status": resp.status,
                "ok": 200 <= resp.status < 300,
            }
    except urllib.error.HTTPError as e:
        # 422 = key not valid(检查 keyLocation),429 = rate limit
        return {"host": host, "urls": len(urls), "status": e.code, "ok": False, "error": str(e)}
    except Exception as e:
        return {"host": host, "urls": len(urls), "status": None, "ok": False, "error": str(e)}


# tob 不在 config.yml 里(它的 URL 是 Next.js 动态生成的,手工维护会立刻过时),
# 直接吃它自己的 sitemap。过滤规则与 push_baidu.py 保持一致 ——
# 2026-09-01 Jack 定案：只推类案检索及其相关，工作台/AI 助手不推。
TOB_SITEMAP = "https://tob.wenshucha.com/sitemap.xml"
TOB_ALLOW = ("/cases", "/sifa", "/analytics")
TOB_DENY = ("/tob", "/ai")


def tob_urls(limit=10000):
    """IndexNow 没有每日配额(不像百度 10 条/天),所以能推多少推多少。"""
    import re
    try:
        xml = urllib.request.urlopen(TOB_SITEMAP, timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  ✗ 取 tob sitemap 失败: {e}")
        return []
    out = []
    for u in re.findall(r"<loc>([^<]+)</loc>", xml):
        path = u.split("tob.wenshucha.com", 1)[-1] or "/"
        if any(path.startswith(d) for d in TOB_DENY):
            continue
        if any(path.startswith(a) for a in TOB_ALLOW):
            out.append(u)
    return out[:limit]


def main():
    results = []
    for site in CONFIG["sites"]:
        r = push_host(site["host"], site["urls_to_push"])
        results.append(r)
        flag = "✓" if r["ok"] else "✗"
        msg = f"  {flag} {r['host']:35} pushed {r['urls']} urls  HTTP {r['status']}"
        if not r["ok"] and "error" in r:
            msg += f"  ({r['error'][:60]})"
        print(msg)

    # 2026-09-01 实测：一次推 233 条被 IndexNow 返 403（限流），
    # 同样的 key/keyLocation 单条推返 200 ⇒ 不是配置问题，是批量太大。
    # 分批 50 条 + 批间隔 2 秒，实测可过。
    tu = tob_urls()
    if tu:
        import time
        BATCH = 50
        okn = failn = 0
        for i in range(0, len(tu), BATCH):
            chunk = tu[i:i + BATCH]
            r = push_host("tob.wenshucha.com", chunk)
            (okn := okn) if False else None
            if r["ok"]:
                okn += len(chunk)
            else:
                failn += len(chunk)
                print(f"    ✗ 第 {i//BATCH + 1} 批 {len(chunk)} 条 HTTP {r['status']}")
            if i + BATCH < len(tu):
                time.sleep(2)
        allok = failn == 0
        results.append({"host": "tob.wenshucha.com", "urls": okn,
                        "status": 200 if allok else 403, "ok": allok})
        print(f"  {'✓' if allok else '✗'} {'tob.wenshucha.com':35} pushed {okn} urls"
              + (f"  (失败 {failn})" if failn else "  HTTP 200"))

    ok = sum(1 for r in results if r["ok"])
    print(f"IndexNow push: {ok}/{len(results)} hosts OK")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
