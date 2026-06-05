#!/usr/bin/env python3
"""把 daily_run 的 raw 输出 → 「人话」日报

回答 Jack 三个问题:
1. 体系还活着吗?(健康度)
2. 有没有进展?(对比昨天)
3. 看什么指标算真进展?(可执行建议)

输入(stdin):IndexNow + 百度 + SSL 监控的混合 raw 输出
输出(stdout):markdown 格式日报
"""
import json
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state" / "daily_state.json"
STATE_FILE.parent.mkdir(exist_ok=True, parents=True)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def parse_input(raw: str) -> dict:
    data = {
        "indexnow": [],
        "indexnow_total_urls": 0,
        "indexnow_hosts_ok": 0,
        "ssl": [],
        "ssl_alerts": [],
        "baidu_success": 0,
        "baidu_remain": None,
    }

    # IndexNow:✓ wenshucha.com pushed 8 urls HTTP 200
    for m in re.finditer(r"[✓✗]\s+(\S+\.\S+)\s+pushed\s+(\d+)\s+urls\s+HTTP\s+(\d+)", raw):
        host, n, code = m.group(1), int(m.group(2)), int(m.group(3))
        data["indexnow"].append({"host": host, "urls": n, "code": code})
        if 200 <= code < 300:
            data["indexnow_total_urls"] += n
            data["indexnow_hosts_ok"] += 1

    # SSL:✓ wenshucha.com 81d exp=2026-08-25 by R12
    for m in re.finditer(r"([✓⚠🔥])\s+(\S+\.\S+)\s+(\d+)d\s+exp=(\S+)", raw):
        tag, host, days, exp = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        entry = {"tag": tag, "host": host, "days": days, "exp": exp}
        data["ssl"].append(entry)
        if days < 30:
            data["ssl_alerts"].append(entry)

    # 百度推送:{"remain":N,"success":M}(顺序不定)
    rm = re.search(r'"remain"\s*:\s*(\d+)', raw)
    sm = re.search(r'"success"\s*:\s*(\d+)', raw)
    if sm:
        data["baidu_success"] = int(sm.group(1))
    if rm:
        data["baidu_remain"] = int(rm.group(1))

    return data


def build(data: dict) -> str:
    today = datetime.now().strftime("%-m月%-d日")

    state = load_state()
    today_pushes = data["indexnow_total_urls"] + data["baidu_success"]
    yesterday_pushes = state.get("yesterday_pushes_total", 0)
    week_pushes = state.get("week_pushes_total", 0) + today_pushes
    if datetime.now().weekday() == 0:  # 周一清零
        week_pushes = today_pushes
    state["yesterday_pushes_total"] = today_pushes
    state["week_pushes_total"] = week_pushes
    state["last_run"] = datetime.now().isoformat()
    save_state(state)

    indexnow_total_hosts = len(data["indexnow"])
    healthy = (
        indexnow_total_hosts > 0
        and data["indexnow_hosts_ok"] == indexnow_total_hosts
        and not data["ssl_alerts"]
    )

    L = []
    L.append(f"🌱 *SEO 日报 · {today}*")
    L.append("")

    # 一句话总结
    L.append("*一句话:*")
    if healthy:
        delta = today_pushes - yesterday_pushes
        delta_str = (
            f"+{delta} vs 昨天" if delta > 0
            else (f"{delta} vs 昨天" if delta < 0 else "持平昨天")
        )
        L.append(f"✅ 体系健康活着,今天推了 {today_pushes} URLs({delta_str}),无故障。")
    else:
        if data["ssl_alerts"]:
            hosts = ", ".join(s["host"] for s in data["ssl_alerts"])
            L.append(f"⚠️ SSL 告警:{hosts} 即将到期,该续证书了。")
        elif indexnow_total_hosts and data["indexnow_hosts_ok"] != indexnow_total_hosts:
            failed = [x["host"] for x in data["indexnow"] if not (200 <= x["code"] < 300)]
            L.append(f"⚠️ {len(failed)} 个站推送失败:{', '.join(failed)}")
        else:
            L.append("⚠️ 体系跑出来但数据异常,需要看 log")

    L.append("")

    # 今天体系
    L.append("*今天 daemon 跑了什么:*")
    if indexnow_total_hosts:
        L.append(f"• IndexNow 推 {data['indexnow_total_urls']} URLs 给 Bing/Yandex(`{data['indexnow_hosts_ok']}/{indexnow_total_hosts}` 站成功)")
    if data["baidu_success"]:
        rem = f"(还剩 {data['baidu_remain']} 次配额)" if data["baidu_remain"] is not None else ""
        L.append(f"• 百度推送 {data['baidu_success']} URLs {rem}")
    if data["ssl"]:
        min_ssl = min(data["ssl"], key=lambda s: s["days"])
        L.append(f"• SSL 全绿(最近到期 `{min_ssl['host']}` 还有 {min_ssl['days']} 天 = {min_ssl['exp']})")
    L.append("")

    # 累计
    L.append(f"*本周累计推送:* {week_pushes} URLs")
    L.append("")

    # 插入 daily_optimizer 输出(如果存在)
    opt_file = Path("/tmp/seo_daily_optimizer.md")
    if opt_file.exists():
        L.append("─" * 30)
        L.append(opt_file.read_text())
        L.append("─" * 30)
        L.append("")

    # 进展评估(诚实)
    L.append("*有没有真进展?*")
    L.append("当前能看的指标 = 体系健康度 ✅ + 推送量 ✅(领先指标,证明 daemon 在跑)")
    L.append("")
    L.append("真效果(收录 / 排名 / 流量)要 30-90 天才出来,且需要接 GSC API / GA4 后日报才能自动显示真数字。")
    L.append("")

    # 看什么算进展
    L.append("*看什么算真进展(从快到慢):*")
    L.append("1. 收录量 ↑(7-30 天反应) — 接 GSC API 解锁")
    L.append("2. 关键词排名 ↑(30-90 天) — 「裁判文书 API / 律所私有 AI」从 100+ 名往前爬")
    L.append("3. 自然流量 ↑(60-180 天) — GA4 organic search")
    L.append("4. 转化(180+ 天) — 律所/政府商务来电、peilema 9.9 购买、sinoverdict 邮件咨询")
    L.append("")

    # 你能做的(加速)
    L.append("*你能加速的事(可选):*")
    L.append("• 给 GSC service account JSON → 日报开始有真数据")
    L.append("• 给 GA4 measurement ID → 流量接入")
    L.append("• 写 1 篇 SEO 长文(主题池 60 题待选,可代写)")
    L.append("")
    L.append("_自动生成 · 腾讯云 Lighthouse_")

    return "\n".join(L)


def main() -> int:
    raw = sys.stdin.read()
    data = parse_input(raw)
    print(build(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
