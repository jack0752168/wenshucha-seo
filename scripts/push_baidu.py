#!/usr/bin/env python3
"""百度普通收录 API 推送(每天 daily_run 自动调用)

文书查面向国内市场,百度是主战场。
token 配置在 config.yml global.baidu_push_token(优先)或 secrets/baidu_push_token(兜底)
"""
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

# token 优先从 config.yml 读,兜底 secrets 文件
TOKEN = (CONFIG.get("global") or {}).get("baidu_push_token", "").strip()
if not TOKEN:
    SECRET = ROOT / "secrets" / "baidu_push_token"
    if SECRET.exists():
        TOKEN = SECRET.read_text().strip()

if not TOKEN:
    print("⏭️  跳过百度推送:config.yml 未设 baidu_push_token 且 secrets/baidu_push_token 不存在")
    sys.exit(0)

# 百度 site 必须与站长平台验证时填的一致
DOMAIN = "www.wenshucha.com"


def normalize_for_baidu(url: str) -> str:
    """百度 site=www.wenshucha.com 时推送 URL 也要带 www。
    把 https://wenshucha.com → https://www.wenshucha.com
    其他子域(sinoverdict/mcp/peilema)过滤掉
    """
    if url.startswith("https://wenshucha.com"):
        return url.replace("https://wenshucha.com", "https://www.wenshucha.com", 1)
    if url.startswith("https://www.wenshucha.com"):
        return url
    return None


def push_baidu(urls: list):
    endpoint = f"http://data.zz.baidu.com/urls?site=https://{DOMAIN}&token={TOKEN}"
    normalized = [u for u in (normalize_for_baidu(u) for u in urls) if u]
    if not normalized:
        print("没有 www.wenshucha.com 的 URL 可推送")
        return 0
    print(f"百度推送 {len(normalized)} 个 URL:")
    for u in normalized:
        print(f"  · {u}")
    body = "\n".join(normalized).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=body,
        headers={"Content-Type": "text/plain"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = resp.read().decode("utf-8", errors="replace")
            print(f"✓ 百度推送: HTTP {resp.status} → {result}")
            return 0
    except urllib.error.HTTPError as e:
        print(f"✗ 百度推送失败 HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")
        return 1


def main():
    urls = []
    matched_hosts = ("wenshucha.com", "www.wenshucha.com")
    for site in CONFIG["sites"]:
        if site["host"] in matched_hosts:
            urls.extend(site["urls_to_push"])
    if not urls:
        print("config.yml 没有 wenshucha.com 主站 URL")
        return 0
    return push_baidu(urls)


if __name__ == "__main__":
    sys.exit(main())
