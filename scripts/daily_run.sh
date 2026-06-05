#!/bin/bash
# 每日 09:00 SEO 自动化编排
# 0) self-update(tarball 拉最新 wenshucha-seo,避免 git clone 在境内不稳)
# 1) IndexNow 主动推 URL 给 Bing / Yandex
# 2) 百度推送(如果 Jack 已配 token)
# 3) Google Indexing API(如果 Jack 已配 service account)
# 4) SSL 到期监控(<30 天告警)

set +e  # 单个失败不中断其他

cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "============================================================"
echo "[$TS] wenshucha-seo daily run"
echo "============================================================"

echo
echo "--- [0/4] self-update from GitHub tarball ---"
if [ -d "$ROOT" ] && [ -w "$ROOT" ]; then
    cd /tmp && rm -rf wenshucha-seo-main seo.tar.gz
    if curl -sSLo seo.tar.gz https://codeload.github.com/jack0752168/wenshucha-seo/tar.gz/main; then
        tar xzf seo.tar.gz
        # 保留 logs/ 和 secrets/(.gitignore 内,不被 tar 覆盖)
        cp -rf wenshucha-seo-main/. "$ROOT/" 2>/dev/null && echo "  ✓ updated"
        rm -rf wenshucha-seo-main seo.tar.gz
    else
        echo "  ⚠️  tarball 拉取失败,跳过更新继续跑"
    fi
    cd "$ROOT"
fi

echo
echo "--- [1/5] IndexNow → Bing/Yandex ---"
python3 scripts/push_indexnow.py 2>&1 | tee /tmp/seo_daily_indexnow.out

echo
echo "--- [2/5] 百度主动推送 ---"
python3 scripts/push_baidu.py 2>&1 | tee /tmp/seo_daily_baidu.out

echo
echo "--- [3/5] Google Indexing API ---"
if [ -f scripts/push_google.py ]; then
    python3 scripts/push_google.py
else
    echo "⏭️  push_google.py 暂未实现(等 Jack 配 Google service account)"
fi

echo
echo "--- [4/5] SSL 到期监控 ---"
python3 scripts/ssl_monitor.py 2>&1 | tee /tmp/seo_daily_ssl.out

echo
echo "--- [5/5] 生成人话日报 + 推 Telegram ---"
# 把这次跑的所有 raw 输出拼起来,喂给 narrative builder
{
  echo "=== INDEXNOW ==="
  cat /tmp/seo_daily_indexnow.out 2>/dev/null
  echo "=== BAIDU ==="
  cat /tmp/seo_daily_baidu.out 2>/dev/null
  echo "=== SSL ==="
  cat /tmp/seo_daily_ssl.out 2>/dev/null
} | python3 scripts/build_daily_narrative.py > /tmp/seo_daily_narrative.md

DAILY_DIR="$ROOT/reports/daily"
mkdir -p "$DAILY_DIR"
TODAY=$(date '+%Y-%m-%d')
cp /tmp/seo_daily_narrative.md "$DAILY_DIR/$TODAY.md"
cp /tmp/seo_daily_narrative.md "$DAILY_DIR/latest.md"
echo "  ✓ 日报已写到 $DAILY_DIR/$TODAY.md"

# 推 Telegram(主通道)
if [ -f secrets/telegram_bot_token ] && [ -f secrets/telegram_chat_id ]; then
    python3 scripts/notify_telegram.py "🌱 SEO 日报 $(date '+%-m月%-d日')" "$DAILY_DIR/$TODAY.md" || true
fi

# 微信备份(如果可用)
if [ -x ~/.claude/bin/notify-wechat.py ]; then
    head -25 "$DAILY_DIR/$TODAY.md" | ~/.claude/bin/notify-wechat.py "SEO 日报 $(date '+%-m月%-d日')" 2>/dev/null || true
fi

# 清理临时文件
rm -f /tmp/seo_daily_indexnow.out /tmp/seo_daily_baidu.out /tmp/seo_daily_ssl.out /tmp/seo_daily_narrative.md

echo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] done"
