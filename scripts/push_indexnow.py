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

    ok = sum(1 for r in results if r["ok"])
    print(f"IndexNow push: {ok}/{len(results)} hosts OK")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
