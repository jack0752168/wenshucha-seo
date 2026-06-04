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
echo "--- [2/2] 生成 + 推送周报 ---"
if [ -f scripts/generate_weekly_report.py ]; then
    python3 scripts/generate_weekly_report.py "$REPORT"
else
    # fallback: 直接微信推 report 头部
    if [ -x ~/.claude/bin/notify-wechat.py ]; then
        head -30 "$REPORT" | ~/.claude/bin/notify-wechat.py "【wenshucha SEO 周报 $WEEKID】"
    fi
fi

echo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] done, report=$REPORT"
