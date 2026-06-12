#!/usr/bin/env python3
"""关键词排名长期跟踪 —— 每天记录,报告显示涨跌趋势

数据源(真实,非爬虫猜测):
  🇨🇳 百度搜索资源平台「流量与关键词」(展现/点击/排名)
  🌍 Google Search Console「Performance」(impressions/clicks/position)
两者都是搜索引擎自己报的真实数据,只覆盖「已经有展现」的词,新站初期稀疏属正常。

历史存 state/rankings_history.json,结构:
  {"snapshots": [{"date":"2026-06-10",
                  "baidu":[{"kw":"裁判文书 金额","rank":5,"impr":1,"clicks":0}],
                  "google":[{"kw":"中国法律文书网","rank":30,"impr":2,"clicks":0}]}]}

用法:
  python3 rankings.py add-snapshot /tmp/snap.json   # 追加今日快照(同日覆盖)
  python3 rankings.py trend --vs 1                   # 对比1天前,输出 markdown(日报用)
  python3 rankings.py trend --vs 7                   # 对比7天前(周报用)
  python3 rankings.py show                           # 看全部历史
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "state" / "rankings_history.json"


def load():
    if HISTORY.exists():
        try:
            return json.loads(HISTORY.read_text())
        except Exception:
            pass
    return {"snapshots": []}


def save(data):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def add_snapshot(snap: dict):
    """snap = {date, baidu:[{kw,rank,impr,clicks}], google:[...]}"""
    data = load()
    snap.setdefault("baidu", [])
    snap.setdefault("google", [])
    # 同日覆盖
    data["snapshots"] = [s for s in data["snapshots"] if s.get("date") != snap["date"]]
    data["snapshots"].append(snap)
    data["snapshots"].sort(key=lambda s: s["date"])
    save(data)
    nb, ng = len(snap["baidu"]), len(snap["google"])
    print(f"✓ 记录 {snap['date']} 快照: 百度 {nb} 词 / Google {ng} 词")


def _index(snap, engine):
    return {row["kw"]: row for row in snap.get(engine, [])}


def _baseline(snapshots, latest_date, vs_days):
    """找 vs_days 天前最接近的快照(没有就取最早的,但不能是 latest 自己)"""
    target = datetime.strptime(latest_date, "%Y-%m-%d") - timedelta(days=vs_days)
    older = [s for s in snapshots if s["date"] < latest_date]
    if not older:
        return None
    # 取日期 <= target 里最近的;没有就取最早的 older
    le = [s for s in older if datetime.strptime(s["date"], "%Y-%m-%d") <= target]
    return (le[-1] if le else older[0])


def _arrow(latest_rank, base_rank):
    """排名越小越好。返回 (符号, 说明)"""
    if base_rank is None:
        return "🆕", "新进榜"
    d = base_rank - latest_rank  # 正=名次前进
    if d > 0:
        return "↑", f"↑{d}"
    if d < 0:
        return "↓", f"↓{-d}"
    return "→", "持平"


def render_trend(vs_days=1, label=None) -> str:
    data = load()
    snaps = data["snapshots"]
    if not snaps:
        return "*关键词排名:* 暂无快照(等下次抓取百度/GSC 后开始记录)"
    latest = snaps[-1]
    base = _baseline(snaps, latest["date"], vs_days)
    base_tag = ("对比 " + base["date"]) if base else "首次记录,无对比基线"
    head = label if label else (latest["date"] + " · " + base_tag)
    L = ["*🎯 关键词排名*（" + head + "）"]

    # 头条:在榜词总数(最直观的增长指标)
    lt = latest.get("totals", {})
    if lt.get("baidu_keywords") is not None:
        line = f"🏆 百度在榜词 {lt['baidu_keywords']} 个,累计点击 {lt.get('baidu_clicks', 0)}"
        bt = base.get("totals", {}) if base else {}
        if bt.get("baidu_keywords") is not None:
            dk = lt["baidu_keywords"] - bt["baidu_keywords"]
            line += f"（词数 {'+' if dk >= 0 else ''}{dk} vs {base['date']}）"
        L.append(line)

    for engine, flag, name in [("baidu", "🇨🇳", "百度"), ("google", "🌍", "Google")]:
        rows = sorted(latest.get(engine, []), key=lambda r: r["rank"])
        if not rows:
            continue
        bidx = _index(base, engine) if base else {}
        L.append(f"{flag} {name}:")
        for r in rows[:8]:
            br = bidx.get(r["kw"])
            _, tag = _arrow(r["rank"], br["rank"] if br else None)
            impr = f" · 展现{r['impr']}" if r.get("impr") else ""
            L.append(f"  • {r['kw']} → 第 {r['rank']} 名 `{tag}`{impr}")
    # 汇总展现趋势
    def total_impr(s):
        return sum(x.get("impr", 0) for x in s.get("baidu", []) + s.get("google", []))
    ti = total_impr(latest)
    if base:
        tb = total_impr(base)
        dd = ti - tb
        ds = f"+{dd}" if dd > 0 else str(dd)
        L.append(f"📊 总展现 {ti}（{ds} vs {base['date']}）")
    else:
        L.append(f"📊 总展现 {ti}（基线）")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("add-snapshot"); a.add_argument("file")
    t = sub.add_parser("trend"); t.add_argument("--vs", type=int, default=1); t.add_argument("--label", default=None)
    sub.add_parser("show")
    args = ap.parse_args()

    if args.cmd == "add-snapshot":
        snap = json.loads(Path(args.file).read_text())
        add_snapshot(snap)
    elif args.cmd == "trend":
        print(render_trend(args.vs, args.label))
    elif args.cmd == "show":
        print(json.dumps(load(), ensure_ascii=False, indent=2))
    else:
        ap.print_help()


if __name__ == "__main__":
    sys.exit(main())
