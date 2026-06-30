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

try:
    import rankings  # 同目录,关键词排名跟踪
except Exception:
    rankings = None

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

    # ★ 主体 = 关键词 + 排名涨跌(Jack 只看这个,其余全砍)
    if rankings is not None:
        try:
            L.append(rankings.render_trend(vs_days=1))
        except Exception:
            L.append("*🎯 关键词排名:* 今日未抓到数据(待 Mac 任务读百度后台)")
    else:
        L.append("*🎯 关键词排名:* 跟踪模块未就绪")
    L.append("")

    # 一行体系状态:正常就一句带过,出事才细说(Jack 不想看运维细节)
    if data["ssl_alerts"]:
        hosts = ", ".join(s["host"] for s in data["ssl_alerts"])
        L.append(f"⚠️ *SSL 告警:* {hosts} 即将到期,该续证书")
    else:
        bd = f"百度推送 {data['baidu_success']}" if data["baidu_success"] else "⚠️ 百度推送 0(查配额)"
        L.append(f"_体系正常 · {bd} · IndexNow {data['indexnow_total_urls']} · SSL 全绿_")

    return "\n".join(L)


def main() -> int:
    raw = sys.stdin.read()
    data = parse_input(raw)
    print(build(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
