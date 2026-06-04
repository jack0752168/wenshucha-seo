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
DOMAIN = "wenshucha.com"  # 百度推送只支持主域


def push_baidu(urls: list):
    """https://ziyuan.baidu.com/linksubmit/index"""
    endpoint = f"http://data.zz.baidu.com/urls?site=https://{DOMAIN}&token={TOKEN}"
    body = "\n".join(urls).encode("utf-8")
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
