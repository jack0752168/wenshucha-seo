#!/bin/bash
# 每周一 10:00 SEO 自动化编排
# 1) 收录量检查(Google/Bing/百度 site:domain)
# 2) 关键词排名监控(stub,需 Tier 2 接入站长平台 API)
# 3) 生成 SEO 周报 → 微信推送

set +e

cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
TS=$(date '+%Y-%m-%d %H:%M:%S')
WEEKID=$(date '+%Y-W%U')
REPORT="reports/weekly/${WEEKID}.md"

mkdir -p reports/weekly

echo "============================================================"
echo "[$TS] wenshucha-seo weekly run (week=$WEEKID)"
echo "============================================================"

# 生成报告 header
cat > "$REPORT" <<EOF
# SEO 周报 · $WEEKID
生成时间: $TS

## 1. 关键词排名趋势(本周 vs 上周)

EOF

echo
echo "--- [1/3] 关键词排名趋势 ---"
python3 scripts/rankings.py trend --vs 7 --label "本周 vs 上周" 2>/dev/null | tee -a "$REPORT" || echo "(暂无排名快照)" | tee -a "$REPORT"

echo "" >> "$REPORT"
echo "## 2. 抓取漏斗周趋势(nginx 一手数据)" >> "$REPORT"
echo "" >> "$REPORT"
# 用 daily_run 每天留的 crawl_history.jsonl 算周环比:内页占比/百度覆盖/推送转化
python3 - >> "$REPORT" 2>/dev/null <<'PYEOF'
import json
from pathlib import Path
hist = Path("state/crawl_history.jsonl")
rows = []
if hist.exists():
    for line in hist.read_text().splitlines():
        try:
            d = json.loads(line)
            if d.get("ok"):
                rows.append(d)
        except Exception:
            pass
# 同一天多条只留最后一条
by_day = {}
for d in rows:
    by_day[d.get("date", "?")] = d
rows = [by_day[k] for k in sorted(by_day)][-14:]
if not rows:
    print("(漏斗历史尚未积累,daily_run 每天写一条,下周起有周环比)")
else:
    print("| 日期 | 百度抓取 | 首页占比 | 百度覆盖 | 推送转化 |")
    print("|---|---|---|---|---|")
    for d in rows[-7:]:
        cov = f"{d['sitemap_declared']-d['baidu_uncrawled_n']}/{d['sitemap_declared']}"
        c = d.get("push_conversion")
        conv = f"{c['crawled']}/{c['pushed']}" if c else "—"
        print(f"| {d['date']} | {d['baidu_hits']} | {d['home_share']:.0%} | {cov} | {conv} |")
    a, b = rows[0], rows[-1]
    print()
    print(f"- 首页占比 {a['home_share']:.0%} → {b['home_share']:.0%}"
          f"(越低越好,>85% 说明内页还是进不去)")
    print(f"- 百度未抓页 {a['baidu_uncrawled_n']} → {b['baidu_uncrawled_n']}(目标每周递减)")
PYEOF
echo "" >> "$REPORT"
echo "> 收录量/Google 排名不在此抓取:本机是国内腾讯云服务器,连不上 Google(被墙)、百度也没有读取 API,site: 抓取必然失败。这类数据由 Mac 端浏览器读百度站长+GSC 后写入排名快照。" >> "$REPORT"
echo
echo "--- [2/3] (跳过 site: 抓取:国内服务器连不上Google/Baidu无读API,见周报说明)---"

echo
echo "--- [2/3] 生成周报 markdown ---"
echo "[$(date '+%F %T')] report saved to $REPORT"

echo
echo "--- [3/3] 写周报到 nginx 中转目录 + 微信备份 ---"
# 拷到 nginx 隐藏目录(给 Mac 本机 cron 拉 → 推 iMessage,周一 10:15)
RELAY_DIR=/www/wwwroot/wenshucha.com/_relay_r9k3m2v8x1q5w7n4
if mkdir -p "$RELAY_DIR" 2>/dev/null; then
    cp "$REPORT" "$RELAY_DIR/weekly.md" 2>/dev/null || true
    echo "  ✓ 周报已拷到 nginx relay 目录(Mac 中转用)"
fi

# 微信备份(如果 hermes 通道恰好可用)
if [ -x ~/.claude/bin/notify-wechat.py ]; then
    head -30 "$REPORT" | ~/.claude/bin/notify-wechat.py "📊 SEO 周报 $WEEKID" 2>/dev/null || true
fi

echo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] done, report=$REPORT"
