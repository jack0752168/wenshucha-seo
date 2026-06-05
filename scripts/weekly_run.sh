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

## 1. 收录量(site:domain query)

EOF

echo
echo "--- [1/2] 收录量检查 ---"
python3 scripts/check_indexed.py | tee -a "$REPORT"

echo
echo "--- [2/3] 生成周报 markdown ---"
echo "[$(date '+%F %T')] report saved to $REPORT"

echo
echo "--- [3/3] 推送周报(iMessage 主 · 微信备份)---"
TITLE="📊 SEO 周报 $WEEKID"

# 1) iMessage(主通道,跟 wenshucha-monitor 同款)
if [ -x ~/.claude/bin/notify-imessage.sh ]; then
    ~/.claude/bin/notify-imessage.sh "$(cat $REPORT)" 2>/dev/null || true
fi

# 2) 微信(备份通道)
if [ -x ~/.claude/bin/notify-wechat.py ]; then
    head -30 "$REPORT" | ~/.claude/bin/notify-wechat.py "$TITLE" 2>/dev/null || true
fi

echo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] done, report=$REPORT"
