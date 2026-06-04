#!/usr/bin/env python3
"""每周收录量检查(site: 查询)
通过 Google / 百度 / Bing 的 site:domain 查询,看搜索引擎收录了多少页

注意:scrape 搜索结果页可能被反爬,这里只做简单 GET + 解析结果数字
更准确的方法是注册各家站长平台后用 API,但 Tier 2 才做
"""
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pip3 install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yml").read_text())

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 wenshucha-seo/1.0"


def fetch_count(url: str, host: str, parser_pattern: str):
    """从搜索结果页 fetch + 用 regex 提取结果数字"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        m = re.search(parser_pattern, html)
        return int(m.group(1).replace(",", "")) if m else None
    except Exception as e:
        return f"ERR: {e}"


def check_google(domain: str):
    """Google site: 查询"""
    url = f"https://www.google.com/search?q=site%3A{urllib.parse.quote(domain)}"
    # Google 结果数字格式 "About X results" 或 "约 X 条结果"
    return fetch_count(url, domain, r"(?:About|约)\s+([\d,]+)\s+(?:results|个结果)")


def check_baidu(domain: str):
    """百度 site: 查询"""
    url = f"https://www.baidu.com/s?wd=site%3A{urllib.parse.quote(domain)}"
    # 百度结果数字格式 "百度为您找到相关结果约X个"
    return fetch_count(url, domain, r"找到相关结果?约?([\d,]+)\s*个")


def check_bing(domain: str):
    """Bing site: 查询"""
    url = f"https://www.bing.com/search?q=site%3A{urllib.parse.quote(domain)}"
    return fetch_count(url, domain, r"([\d,]+)\s+results")


def main():
    print("Search engine indexed page count (site:domain query):\n")
    print(f"{'host':<35} {'Google':>10} {'Bing':>10} {'Baidu':>10}")
    print("-" * 68)

    for site in CONFIG["sites"]:
        host = site["host"]
        g = check_google(host)
        b = check_bing(host)
        bd = check_baidu(host)
        print(f"{host:<35} {str(g):>10} {str(b):>10} {str(bd):>10}")

    print(
        "\n注:scrape 可能被反爬返回 None / ERR;"
        "真正可靠的方式是接入 Google Search Console + 百度站长平台 API(Tier 2)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
