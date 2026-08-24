#!/usr/bin/env python3
"""百家号自演化引擎 —— 用真实阅读量决定明天怎么发

为什么要这个(2026-08-14 Jack 定案:「要演化、要有数据、以流量为优先」):
  在此之前我们优化的全是过程指标(发了几篇、进没进首页)。但后台实测显示:
    07-31 类案同判  阅读 46 · 收藏 6 · 分享 11   → 互动率 37%
    07-24 量刑建议  阅读 47 · 收藏 2 · 分享 2
    07-29 争议焦点  阅读 26 · 收藏 1 · 分享 2
    08-13/14 共 23 篇 阅读几乎全 0
  → 内容质量没问题(互动率远高于常态 1-3%),瓶颈是曝光。
  → 所以北极星指标 = 阅读量,一切编排围绕它做 A/B。

🔴 2026-08-21 大改:归因判据从「平均阅读」换成「中位阅读」。
   阅读量是长尾分布,单篇 205 阅读的爆文会把它所在那一格的均值顶到全场第一,
   而该格中位数其实是全场最低(实测 slot=下午15-16:均值 16.7 全场第一 / 中位 2.0 全场最后,n=27)。
   照均值给建议 = 把 2/3 的篇数挪到实际最差的时段。
   现在的规则:均值榜首与中位榜首不一致 → 输出「说不清」,不给调整建议。

⚠️ 读后台那张表时:六个数字的图标顺序是
   👁阅读 / 💬评论 / 👍点赞 / ☆收藏 / ↗分享 / ¥收益
   第一个是阅读量,不是推荐量。2026-08-14 曾按位置猜错,据此得出「点击率≈0」的
   错误诊断并差点推翻整套内容策略。**先截图看图标,别按位置猜。**

数据流:
  分发任务发文时 → 记 metrics.jsonl 一行(article_id + 本次实验的各维度标签)
  次日/48h 后    → 回后台读阅读量,回填同一行的 reads 字段
  下次发文前     → 跑本脚本,拿到「今天该怎么发」的建议

用法:
  python3 bjh_evolve.py              # 输出归因分析 + 今日建议
  python3 bjh_evolve.py --json       # 机器可读,供排程任务解析
"""
import json
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "state" / "bjh_metrics.jsonl"

# 实验维度:每篇发文时必须打上这些标签,才能做归因
DIMS = ["title_style", "word_type", "slot", "length_band"]

# 每个维度的合法取值(排程任务照这个打标)
DIM_VALUES = {
    "title_style": ["模板型", "问句型", "反常识型"],   # 模板型=「XX怎么办？N个YY与清单」
    "word_type": ["产品邻近", "办案方法", "信源型"],
    "slot": ["早7-9", "午11-13", "下午15-16", "晚19-20", "其他"],
    "length_band": ["<1500", "1500-2000", ">2000"],
}

MIN_SAMPLES = 3        # 每格样本少于这个数,不下结论
MATURE_HOURS = 48      # 发布满这么久才算数据成熟


def load():
    if not STORE.exists():
        return []
    out = []
    for line in STORE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def mature(rows):
    """只用发布满 48h 且已回填阅读量的行做归因"""
    now = datetime.now()
    out = []
    for r in rows:
        if r.get("reads") is None:
            continue
        try:
            t = datetime.fromisoformat(r["published_at"])
        except (KeyError, ValueError):
            continue
        if (now - t) >= timedelta(hours=MATURE_HOURS):
            out.append(r)
    return out


def attribute(rows):
    """按维度分组算平均阅读量;样本不足的标出来,不下结论"""
    res = {}
    for dim in DIMS:
        buckets = defaultdict(list)
        for r in rows:
            v = r.get(dim)
            if v:
                buckets[v].append(r.get("reads", 0))
        res[dim] = {
            v: {
                "n": len(xs),
                "avg_reads": round(sum(xs) / len(xs), 1),
                "median_reads": round(statistics.median(xs), 1),
                "max": max(xs),
                # 峰值占该格总阅读的比重:越接近 1 说明均值全靠一篇爆文撑着
                "peak_share": round(max(xs) / sum(xs), 2) if sum(xs) else 0.0,
                "conclusive": len(xs) >= MIN_SAMPLES,
            }
            for v, xs in buckets.items()
        }
    return res


def untested(rows):
    """哪些取值还从没试过 —— 演化的下一步就该试它们"""
    seen = {d: {r.get(d) for r in rows if r.get(d)} for d in DIMS}
    return {d: [v for v in DIM_VALUES[d] if v not in seen.get(d, set())] for d in DIMS}


def recommend(attr, gaps, n_mature, n_total):
    """输出今天的编排建议。没数据就说没数据,不硬凑。"""
    rec = {"ready": n_mature >= MIN_SAMPLES, "n_mature": n_mature, "n_total": n_total,
           "actions": [], "explore": [], "warnings": []}

    if n_mature < MIN_SAMPLES:
        rec["warnings"].append(
            f"成熟样本仅 {n_mature} 条(需 ≥{MIN_SAMPLES})。**这一轮不做任何优化决策**,"
            f"照当前配置继续发,先把数据攒够。禁止拿 1-2 篇的表现下结论。")
        for d, vs in gaps.items():
            if vs:
                rec["explore"].append(f"{d} 还没试过:{'/'.join(vs)}")
        return rec

    for dim, buckets in attr.items():
        ok = {v: s for v, s in buckets.items() if s["conclusive"]}
        if len(ok) < 2:
            rec["warnings"].append(f"{dim}:只有 {len(ok)} 个取值样本够,无法对比,继续攒")
            continue
        # 🔴 2026-08-21 大改:判据从均值改成中位数。
        # 原因:阅读量是长尾分布,一篇 205 阅读的爆文能把整格均值抬到最高,而该格
        # 中位数其实是全场最低。实测 slot=下午15-16 均值 16.7(全场第一)但中位仅 2.0
        # (全场最后,n=27),照均值建议会把 2/3 篇数挪到实际最差的时段。
        # 规则:均值榜首与中位榜首不一致 → 判「说不清」,不给建议,只记录证据。
        best_med = max(ok.items(), key=lambda kv: kv[1]["median_reads"])
        worst_med = min(ok.items(), key=lambda kv: kv[1]["median_reads"])
        best_avg = max(ok.items(), key=lambda kv: kv[1]["avg_reads"])

        if best_avg[0] != best_med[0]:
            rec["warnings"].append(
                f"{dim}:**均值与中位数打架,判说不清,本轮不据此调整**。"
                f"均值榜首「{best_avg[0]}」(均 {best_avg[1]['avg_reads']}/中位 {best_avg[1]['median_reads']},"
                f"峰 {best_avg[1]['max']} 一篇就占该格总阅读 {int(best_avg[1]['peak_share']*100)}%),"
                f"中位榜首却是「{best_med[0]}」(均 {best_med[1]['avg_reads']}/中位 {best_med[1]['median_reads']})。"
                f"前者是「偶尔爆一篇、多数接近 0」的高方差,不等于稳定更好。")
            continue

        if best_med[1]["median_reads"] <= 0:
            rec["warnings"].append(f"{dim}:所有取值中位阅读都是 0,这个维度目前无区分度")
            continue
        lift = (best_med[1]["median_reads"] - worst_med[1]["median_reads"]) / max(worst_med[1]["median_reads"], 0.5)
        if lift >= 0.5:
            rec["actions"].append(
                f"{dim}:「{best_med[0]}」中位 {best_med[1]['median_reads']} 阅读(均 {best_med[1]['avg_reads']},n={best_med[1]['n']}),"
                f"「{worst_med[0]}」中位只有 {worst_med[1]['median_reads']}(n={worst_med[1]['n']})"
                f" → 下一批把「{best_med[0]}」比例提到 2/3,但**保留至少 1 篇对照**,别一把梭")
        else:
            rec["actions"].append(f"{dim}:各取值中位差异 <50%,无显著优劣,维持现状并继续观察")

    for d, vs in gaps.items():
        if vs:
            rec["explore"].append(f"{d} 还没试过:{'/'.join(vs)} —— 每批留 1 篇去试")

    return rec


def main():
    rows = load()
    mrows = mature(rows)
    attr = attribute(mrows)
    gaps = untested(mrows)
    rec = recommend(attr, gaps, len(mrows), len(rows))

    if "--json" in sys.argv:
        print(json.dumps({"attribution": attr, "recommendation": rec},
                         ensure_ascii=False, indent=2))
        return

    print(f"# 百家号自演化分析 · {date.today()}")
    print(f"\n样本:总 {len(rows)} 条,成熟(≥{MATURE_HOURS}h 且已回填阅读) {len(mrows)} 条\n")

    if not mrows:
        print("⚠️  还没有任何成熟样本。先让分发任务按 DIMS 打标记录,48h 后回填阅读量。")
        print("\n需要记录的维度:")
        for d, vs in DIM_VALUES.items():
            print(f"  {d}: {' / '.join(vs)}")
        return

    print("## 归因(北极星 = 阅读量)\n")
    for dim, buckets in attr.items():
        print(f"### {dim}")
        for v, s in sorted(buckets.items(), key=lambda kv: -kv[1]["median_reads"]):
            flag = "" if s["conclusive"] else "  ⚠️样本不足"
            skew = "  🔴均值被单点撑起" if s["peak_share"] >= 0.5 and s["n"] >= MIN_SAMPLES else ""
            print(f"  {v:<10} 中位 {s['median_reads']:>5} · 均 {s['avg_reads']:>6} · 峰 {s['max']:>4} · n={s['n']}{flag}{skew}")
        print()

    print("## 今天怎么发\n")
    for a in rec["actions"]:
        print(f"  ✅ {a}")
    for e in rec["explore"]:
        print(f"  🔬 {e}")
    for w in rec["warnings"]:
        print(f"  ⚠️  {w}")


if __name__ == "__main__":
    main()
