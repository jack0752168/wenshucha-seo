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
echo "--- [0b] 同步 wenshucha-site(含 blog/ 新文章)到 nginx ---"
# Claude 写完文章 push 后,最迟次日 09:00 自动上线,不需手动 OrcaTerm
if [ -f deploy/sync-wenshucha-site.sh ]; then
    bash deploy/sync-wenshucha-site.sh && echo "  ✓ wenshucha-site 已同步(含 blog)" || echo "  ⚠️ 同步失败"
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
echo "--- [4/6] SSL 到期监控 ---"
python3 scripts/ssl_monitor.py 2>&1 | tee /tmp/seo_daily_ssl.out

echo
echo "--- [5/7] 主动优化动作(刷新 sitemap / 健康检查 / 统计页数变化)---"
python3 scripts/daily_optimizer.py > /tmp/seo_daily_optimizer.md 2>&1
tail -10 /tmp/seo_daily_optimizer.md

echo
echo "--- [6/7] 抓取漏斗体检(nginx 一手数据:蜘蛛来没来/推送有没有用)---"
# 2026-07-22 教训:以前只报「我跑了没」,从不报「有没有用」,内页 13 个月没被抓都没发现。
# 这一步是整个日报里唯一的疗效仪表,永远不许删。
python3 scripts/crawl_health.py 2>&1 | tee /tmp/seo_daily_crawl.out
# 漏斗历史留档(weekly 算周环比用;必须 --jsonl 单行,--json 多行会毁掉按行解析)
python3 scripts/crawl_health.py --jsonl >> state/crawl_history.jsonl 2>/dev/null || true

echo
echo "--- [7/7] 生成人话日报 ---"
# 把这次跑的所有 raw 输出拼起来,喂给 narrative builder
{
  echo "=== INDEXNOW ==="
  cat /tmp/seo_daily_indexnow.out 2>/dev/null
  echo "=== BAIDU ==="
  cat /tmp/seo_daily_baidu.out 2>/dev/null
  echo "=== SSL ==="
  cat /tmp/seo_daily_ssl.out 2>/dev/null
  echo "=== CRAWL ==="
  cat /tmp/seo_daily_crawl.out 2>/dev/null
} | python3 scripts/build_daily_narrative.py > /tmp/seo_daily_narrative.md

DAILY_DIR="$ROOT/reports/daily"
mkdir -p "$DAILY_DIR"
TODAY=$(date '+%Y-%m-%d')
cp /tmp/seo_daily_narrative.md "$DAILY_DIR/$TODAY.md"
cp /tmp/seo_daily_narrative.md "$DAILY_DIR/latest.md"
echo "  ✓ 日报已写到 $DAILY_DIR/$TODAY.md"

# 同时拷到 nginx 对外隐藏目录(给 Mac 本机 cron 拉 → 推 iMessage)
# Lighthouse 直接推 iMessage 不可行(macOS 专属),只能用 Mac 中转
RELAY_DIR=/www/wwwroot/wenshucha.com/_relay_r9k3m2v8x1q5w7n4
if mkdir -p "$RELAY_DIR" 2>/dev/null; then
    cp /tmp/seo_daily_narrative.md "$RELAY_DIR/daily.md" 2>/dev/null || true
    echo "  ✓ 日报已拷到 nginx relay 目录(Mac 中转用)"
fi

# Lighthouse 上推 iMessage 不可行(/root/.claude/bin/ 不存在,osascript 是 macOS 专属)
# iMessage 推送由 Mac 本机 cron 从 RELAY_DIR 拉(见上面 cp)
# 仅尝试微信备份(如果 hermes 通道恰好可用)
if [ -x ~/.claude/bin/notify-wechat.py ]; then
    head -25 "$DAILY_DIR/$TODAY.md" | ~/.claude/bin/notify-wechat.py "🌱 SEO 日报 $(date '+%-m月%-d日')" 2>/dev/null || true
fi

# 清理临时文件
rm -f /tmp/seo_daily_indexnow.out /tmp/seo_daily_baidu.out /tmp/seo_daily_ssl.out /tmp/seo_daily_crawl.out /tmp/seo_daily_narrative.md

echo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] done"
