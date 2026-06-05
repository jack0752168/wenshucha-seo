#!/usr/bin/env python3
"""百度主动推送 stub

⚠️ 需要 Jack 先做的:
  1. 进 https://ziyuan.baidu.com 注册账号 + 添加 wenshucha.com
  2. 拿到「普通收录」推送 token
  3. 把 token 填到 ~/wenshucha-seo/secrets/baidu_push_token(在 Lighthouse 上)
     这个文件在 .gitignore 里,不会进 repo

token 拿到后这个脚本会自动每天跑
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
SECRET = ROOT / "secrets" / "baidu_push_token"

if not SECRET.exists():
    print("⏭️  跳过百度推送:secrets/baidu_push_token 不存在(等 Jack 注册百度站长平台后回填)")
    sys.exit(0)

TOKEN = SECRET.read_text().strip()
# 百度推送 site 必须跟站长平台验证时填的一致;我们验证的是 www.wenshucha.com
DOMAIN = "www.wenshucha.com"


def normalize_for_baidu(url: str) -> str:
    """百度 site=www.wenshucha.com 时推送 URL 也要带 www。
    把 https://wenshucha.com → https://www.wenshucha.com,
    把 https://mcp.wenshucha.com 这种其他子域过滤掉(它们不在该 site 下)
    """
    if url.startswith("https://wenshucha.com"):
        return url.replace("https://wenshucha.com", "https://www.wenshucha.com", 1)
    if url.startswith("https://www.wenshucha.com"):
        return url
    return None  # 其他子域,百度不会接受


def push_baidu(urls: list):
    """https://ziyuan.baidu.com/linksubmit/index"""
    endpoint = f"http://data.zz.baidu.com/urls?site=https://{DOMAIN}&token={TOKEN}"
    normalized = [u for u in (normalize_for_baidu(u) for u in urls) if u]
    if not normalized:
        print("没有 www.wenshucha.com 的 URL 可推送")
        return 0
    print(f"准备推送 {len(normalized)} 个 URL 到百度:")
    for u in normalized:
        print(f"  · {u}")
    body = "\n".join(normalized).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "text/plain"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"百度推送: HTTP {resp.status}")
            print(resp.read().decode("utf-8", errors="replace"))
            return 0
    except urllib.error.HTTPError as e:
        print(f"百度推送失败 HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")
        return 1


def main():
    urls = []
    for site in CONFIG["sites"]:
        if site["host"] == DOMAIN:
            urls.extend(site["urls_to_push"])
    if not urls:
        print("没有可推送的 URL")
        return 0
    return push_baidu(urls)


if __name__ == "__main__":
    sys.exit(main())
