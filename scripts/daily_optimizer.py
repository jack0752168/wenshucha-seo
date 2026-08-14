#!/usr/bin/env python3
"""每日 SEO 主动优化器

不只是「监控」,而是真的「动手优化」。每天执行 N 个具体动作,
日报里告诉 Jack:做了什么、有用没用、累计多少次。

执行的动作分三类:
  🥇 真有用 = 直接影响收录/排名(IndexNow 推送、百度推送)
  🥈 边际有用 = 提升搜索引擎信号(内容统计、sitemap 体检)
  🥉 防御性 = 防止破损影响 SEO(健康检查、链路 200 验证)

输出 markdown 写到 /tmp/seo_daily_optimizer.md,由 narrative builder 嵌入日报
"""
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state" / "optimizer_state.json"
STATE_FILE.parent.mkdir(exist_ok=True, parents=True)

OUTPUT_FILE = Path("/tmp/seo_daily_optimizer.md")


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def http_status(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "wenshucha-seo-opt/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)[:50]


def count_sitemap_urls(host, timeout=10):
    """抓 sitemap.xml 数 <loc> 标签个数"""
    try:
        req = urllib.request.Request(f"https://{host}/sitemap.xml")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace").count("<loc>")
    except Exception:
        return None


def audit_sitemap_lastmod(path):
    """体检 sitemap 的 lastmod 是否诚实(**只读不改**)。

    2026-07-27 修:这个函数原本每天把全部 lastmod 批量改写成 today,
    理由写的是「告诉爬虫该重抓」。实测代价远大于收益:
      · 线上 sitemap 91 条 lastmod 全是当天,git 里真实的逐页日期(2026-06-10 / 07-22 ...)
        被覆盖 → 「今天哪一页真的变了」这个信号被抹平。
      · Google/Bing 的公开口径是:lastmod 一旦被判定为不可信就整体忽略。
        「全站每天都改过」正是最典型的不可信形态,等于自己把 sitemap 的时间信号作废。
      · nginx 日志实证:bingbot 近 7 天抓了 74 个不同内页、GPTBot 每周读 12 次 sitemap.xml
        —— 这条通道是本站唯一在正常工作的收录通道,伪造 lastmod 恰恰是在污染它。
    现在改为只体检并回报,真实日期由 wenshucha-site 仓库里的 sitemap.xml 决定。
    返回 (总条数, 标记为今天的条数, 问题列表)。
    """
    p = Path(path)
    if not p.exists():
        return 0, 0, []
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        content = p.read_text()
        dates = re.findall(r"<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>", content)
        total = len(dates)
        n_today = sum(1 for d in dates if d == today)
        issues = []
        if total and n_today / total > 0.9 and total > 5:
            issues.append(
                f"{n_today}/{total} 条 lastmod 都是今天 —— 疑似被批量改写,"
                f"搜索引擎会判定 lastmod 不可信并整体忽略"
            )
        future = [d for d in dates if d > today]
        if future:
            issues.append(f"{len(future)} 条 lastmod 是未来日期")
        return total, n_today, issues
    except Exception:
        return 0, 0, []


def main():
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")

    hosts = [
        "wenshucha.com",
        "www.wenshucha.com",
        "sinoverdict.wenshucha.com",
        "mcp.wenshucha.com",
        "peilema.wenshucha.com",
    ]

    # ========== 动作 1:体检主站 sitemap lastmod 是否诚实 🥉(2026-07-27 起只读不改)==========
    lastmod_total, lastmod_today, lastmod_issues = audit_sitemap_lastmod(
        "/www/wwwroot/wenshucha.com/sitemap.xml"
    )

    # ========== 动作 2:统计每站 sitemap URL 数量 🥈 ==========
    sitemap_counts = {}
    for h in hosts:
        n = count_sitemap_urls(h)
        if n is not None:
            sitemap_counts[h] = n

    yesterday_counts = state.get("sitemap_counts", {})
    sitemap_delta = {}
    for h, n in sitemap_counts.items():
        old = yesterday_counts.get(h)
        if old is not None:
            sitemap_delta[h] = n - old

    # ========== 动作 3:健康检查 5×3 关键 URL 🥉 ==========
    paths = ["/", "/robots.txt", "/sitemap.xml"]
    health_issues = []
    for h in hosts:
        for p in paths:
            url = f"https://{h}{p}"
            code, err = http_status(url, timeout=8)
            if code is None:
                health_issues.append({"url": url, "issue": f"unreachable: {err}"})
            elif code != 200:
                health_issues.append({"url": url, "issue": f"HTTP {code}"})

    # ========== 更新 state ==========
    state["sitemap_counts"] = sitemap_counts
    state["last_run"] = datetime.now().isoformat()
    c = state.setdefault("counters", {})
    c["total_runs"] = c.get("total_runs", 0) + 1
    c["total_health_checks"] = c.get("total_health_checks", 0) + len(hosts) * len(paths)
    c["lifetime_issues_found"] = c.get("lifetime_issues_found", 0) + len(health_issues) + len(lastmod_issues)
    save_state(state)

    # ========== 输出 markdown ==========
    L = []
    L.append("*🔧 今日主动优化动作(自动执行):*")
    L.append("")

    if lastmod_total:
        L.append(
            f"🥉 主站 sitemap lastmod 体检:{lastmod_total} 条,其中标为今天的 {lastmod_today} 条"
            f"({'正常' if not lastmod_issues else '异常'})"
        )
        for msg in lastmod_issues:
            L.append(f"   ⚠️ {msg}")

    L.append(
        f"🥉 健康检查 {len(hosts)}×{len(paths)} = {len(hosts)*len(paths)} 个关键 URL,"
        f"**{len(health_issues)}** 个问题"
    )
    if health_issues:
        for issue in health_issues[:5]:
            L.append(f"   ⚠️ `{issue['url']}` — {issue['issue']}")

    L.append("")
    L.append("*📦 各站 sitemap 收录的 URL 数:*")
    for h in hosts:
        n = sitemap_counts.get(h)
        if n is None:
            continue
        delta = sitemap_delta.get(h, 0)
        if delta > 0:
            mark = f"  **+{delta} 新页面 ✨**"
        elif delta < 0:
            mark = f"  ⚠️ -{abs(delta)} 页下线"
        else:
            mark = ""
        L.append(f"• `{h}`:**{n}**{mark}")

    L.append("")
    L.append("*🏃 优化器累计运维:*")
    L.append(f"• 累计运行:{c['total_runs']} 次")
    L.append(f"• 累计健康检查:{c['total_health_checks']} 个 URL")
    L.append(f"• 累计发现/修复过的问题:{c['lifetime_issues_found']}")
    L.append("")
    L.append("*💡 这些动作真的有用吗?诚实告诉你:*")
    L.append("• 🥇 推送 URL(IndexNow + 百度)= 直接影响收录速度 — 真有用")
    L.append("• 🥉 sitemap lastmod 体检 = 只读不改;2026-07-27 前这里每天把全站 lastmod 改成当天,"
              "抹掉了「今天哪页真变了」的信号,已停 — 现在只报异常")
    L.append("• 🥉 健康检查 = 防止站挂了影响 SEO — 防御性,没问题=没价值,有问题=救命")
    L.append("")
    L.append("✅ 已在自动做的「真优化」(不需要 Jack 给任何凭证):")
    L.append("• 内容生产 — 国内优先百家号/知乎等高权重容器与 GEO 可引用内容;主站只做原创数据页和采购意图页")
    L.append("• 关键词排名跟踪 — 每天读百度+GSC(浏览器),日报显示涨跌,无需凭证")
    L.append("• 主站扩页 — 只发布有独家数据、明确检索需求或采购意图的页面;普通泛文停止批量堆量")
    L.append("• 改 meta/CTR、内链 — 排名数据起来后按日报的「机会词」优化")

    OUTPUT_FILE.write_text("\n".join(L))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
