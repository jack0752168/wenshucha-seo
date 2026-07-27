#!/usr/bin/env python3
"""从线上 sitemap.xml 重建 config.yml 的 urls_to_push(规范 URL,按商业价值排序)

为什么需要它(2026-07-27):
  urls_to_push 一直是人肉维护的清单,写了 13 个月后已经和 sitemap 脱节:
    · 57 条里 50 条写的是非 www —— 而站点 2026-07-23 起已统一规范主域为 www,
      非 www 一律 301。IndexNow 收到的是「跳转起点」,不是终点。
    · 4 条 #锚点(/#solution /#faq ...)—— 片段 URL 对 IndexNow/百度都是重复首页,
      sitemap 07-23 已清掉,推送队列却漏清。
    · 漏了 sitemap 里 40 个城市数据页 —— 而 nginx 日志实证 bingbot / GPTBot
      恰恰在抓这些页(近 7 天 bingbot 抓了 74 个不同内页,百度只抓首页)。
  sitemap.xml 是本站唯一的 URL 真相源,推送队列就该从它派生,而不是另开一份人肉清单。

排序 = 业务优先级(百度每天配额只有 10 条,靠顺序决定先推谁):
  首页 → 产品/赚钱页 → 数据枢纽页 → /blog/ → 博客文章(lastmod 新的在前)→ 城市数据页

用法:
  python3 scripts/sync_push_urls.py wenshucha-main            # 干跑,只打印 diff
  python3 scripts/sync_push_urls.py wenshucha-main --write    # 写回 config.yml
"""
import re
import sys
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pip3 install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yml"

# 赚钱页永远排在博客之前(百度配额 10 条/天,顺序即优先级)
MONEY_PATHS = ["/case-search/", "/legal-ai/", "/buyers-guide/"]


def fetch_sitemap(url: str):
    """返回 [(loc, lastmod)],lastmod 缺失记空串。"""
    req = urllib.request.Request(url, headers={"User-Agent": "wenshucha-seo-sync"})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml = r.read().decode("utf-8", "replace")
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>(.*?)</loc>", block)
        if not loc:
            continue
        lm = re.search(r"<lastmod>(.*?)</lastmod>", block)
        out.append((loc.group(1).strip(), lm.group(1).strip() if lm else ""))
    return out


def rank(loc: str, host: str):
    """越小越先推。"""
    p = loc.split(host, 1)[-1] or "/"
    if p in ("/", ""):
        return (0, "")
    if p in MONEY_PATHS:
        return (1, str(MONEY_PATHS.index(p)))
    if p.startswith("/data/labor/"):        # 40 个城市页,量大排最后
        return (6, p)
    if p.startswith("/data"):               # /data/ /data/labor-report/ 等枢纽页
        return (2, p)
    if p == "/blog/":
        return (3, "")
    if p.startswith("/blog/"):
        return (4, p)
    return (5, p)


def build(site: dict):
    entries = fetch_sitemap(site["sitemap"])
    host = site["host"]
    bad = [l for l, _ in entries if "#" in l or not l.startswith(f"https://{host}/") and l.rstrip("/") != f"https://{host}"]
    # 博客按 lastmod 倒序(新文先推),其余按 rank 内的路径序
    lastmod = {l: lm for l, lm in entries}
    locs = sorted({l for l, _ in entries})
    locs.sort(key=lambda l: (rank(l, host), "" if rank(l, host)[0] != 4 else ""))
    blog = [l for l in locs if rank(l, host)[0] == 4]
    blog.sort(key=lambda l: lastmod.get(l, ""), reverse=True)
    ordered = [l for l in locs if rank(l, host)[0] < 4] + blog + [l for l in locs if rank(l, host)[0] > 4]
    ordered.sort(key=lambda l: rank(l, host)[0])  # 稳定排序,组内顺序保持上面的结果
    return ordered, bad


def splice(text: str, site_name: str, urls: list) -> str:
    """只替换该 site 的 urls_to_push 块,config.yml 其余部分逐字节不动。"""
    lines = text.splitlines()
    # 找到 "- name: <site_name>"
    start = next(i for i, l in enumerate(lines) if l.strip() == f"- name: {site_name}")
    key = next(i for i in range(start, len(lines)) if lines[i].strip() == "urls_to_push:")
    indent = len(lines[key]) - len(lines[key].lstrip())
    end = key + 1
    while end < len(lines) and (lines[end].strip().startswith("- ") or lines[end].strip().startswith("#") or not lines[end].strip()):
        # 块内允许注释与空行,遇到同级别 key(如 check_ssl:)即停
        cur_indent = len(lines[end]) - len(lines[end].lstrip())
        if lines[end].strip() and cur_indent <= indent and not lines[end].strip().startswith("- "):
            break
        end += 1
    block = [" " * (indent + 2) + f"- {u}" for u in urls]
    return "\n".join(lines[:key + 1] + block + lines[end:]) + "\n"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    site_name = sys.argv[1]
    write = "--write" in sys.argv

    text = CONFIG_PATH.read_text()
    cfg = yaml.safe_load(text)
    site = next(s for s in cfg["sites"] if s["name"] == site_name)
    old = list(site["urls_to_push"])
    new, bad = build(site)

    print(f"site {site_name}  host={site['host']}")
    print(f"  旧清单 {len(old)} 条 → 新清单 {len(new)} 条(源:{site['sitemap']})")
    non_canon = [u for u in old if not u.startswith(f"https://{site['host']}/")]
    frags = [u for u in old if "#" in u]
    print(f"  旧清单里非规范主域 {len(non_canon)} 条 / #锚点 {len(frags)} 条")
    added = [u for u in new if u not in old]
    dropped = [u for u in old if u not in new]
    print(f"  新增 {len(added)} 条,移除 {len(dropped)} 条(移除的多是非 www 旧写法/锚点)")
    if bad:
        print(f"  ⚠️ sitemap 里有 {len(bad)} 条非本 host 或带锚点的 URL,请先修 sitemap:{bad[:5]}")
    print("  前 8 条(推送顺序):")
    for u in new[:8]:
        print("   ", u)

    if write:
        CONFIG_PATH.write_text(splice(text, site_name, new))
        # 写完自检:能被 yaml 解析,且该 site 的清单确实变成 new
        chk = yaml.safe_load(CONFIG_PATH.read_text())
        got = next(s for s in chk["sites"] if s["name"] == site_name)["urls_to_push"]
        assert got == new, "写回后清单不一致"
        others = {s["name"]: len(s["urls_to_push"]) for s in chk["sites"]}
        print(f"  ✅ 已写回 config.yml 并通过 YAML 复核;各站清单条数 {others}")
    else:
        print("  (干跑,未写回。加 --write 生效)")


if __name__ == "__main__":
    main()
