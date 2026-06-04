#!/bin/bash
# wenshucha-seo Lighthouse 一键安装脚本
#
# 一次性配:
#   1. 更新 /root/sync-wenshucha-site.sh(加 IndexNow key 拉取)
#   2. 立刻同步一次(让 IndexNow key 上线)
#   3. pip install pyyaml(IndexNow 推送脚本依赖)
#   4. 注册 3 个 cron(/15 拉 SEO repo / 0 9 daily / 0 10 周一 weekly)
#   5. mkdir logs
#   6. 跑一次 daily_run.sh 验证 IndexNow 推送成功
#
# 用法(在 Lighthouse 上跑):
#   curl -sSL https://raw.githubusercontent.com/jack0752168/wenshucha-seo/main/install.sh | bash
# 或:
#   git clone https://github.com/jack0752168/wenshucha-seo.git /opt/wenshucha-seo
#   cd /opt/wenshucha-seo && bash install.sh

set -e
SEO_DIR=/opt/wenshucha-seo
SITE_DIR=/www/wwwroot/wenshucha.com
SITE_REPO=https://raw.githubusercontent.com/jack0752168/wenshucha-site/main
INDEXNOW_KEY=a8f3b9c2d1e5f7a8b9c0d1e2f3a4b5c6

echo "============================================================"
echo "wenshucha-seo install"
echo "============================================================"

# 1) git clone SEO repo if not present
if [ ! -d $SEO_DIR/.git ]; then
    echo "[1/6] git clone wenshucha-seo → $SEO_DIR"
    rm -rf $SEO_DIR
    git clone https://github.com/jack0752168/wenshucha-seo.git $SEO_DIR
else
    echo "[1/6] $SEO_DIR already cloned, pulling latest"
    cd $SEO_DIR && git pull origin main --quiet
fi

# 2) 更新 sync-wenshucha-site.sh(加 IndexNow key 到拉取列表)
echo "[2/6] 更新 /root/sync-wenshucha-site.sh"
cat > /root/sync-wenshucha-site.sh <<'SYNC'
#!/bin/bash
cd /www/wwwroot/wenshucha.com || exit 1
R=https://raw.githubusercontent.com/jack0752168/wenshucha-site/main
for f in index.html robots.txt sitemap.xml favicon.svg og-image.svg a8f3b9c2d1e5f7a8b9c0d1e2f3a4b5c6.txt; do
  curl -fsSL -z "$f" -o "$f.tmp" "$R/$f" 2>/dev/null
  if [ -s "$f.tmp" ]; then mv "$f.tmp" "$f"; else rm -f "$f.tmp"; fi
done
SYNC
chmod +x /root/sync-wenshucha-site.sh

# 3) 立刻跑一次 sync(让 IndexNow key 上线)
echo "[3/6] 立刻同步一次"
bash /root/sync-wenshucha-site.sh
if [ -f $SITE_DIR/${INDEXNOW_KEY}.txt ]; then
    echo "    ✓ IndexNow key 已就位: $SITE_DIR/${INDEXNOW_KEY}.txt"
else
    echo "    ⚠️  IndexNow key 文件未到位,手动 wget 兜底"
    wget -q -O "$SITE_DIR/${INDEXNOW_KEY}.txt" "$SITE_REPO/${INDEXNOW_KEY}.txt"
fi

# 4) pip install pyyaml
echo "[4/6] 安装 Python 依赖"
pip3 install pyyaml --quiet 2>&1 | tail -2 || true

# 5) 注册 cron(去重)
echo "[5/6] 注册 cron"
( crontab -l 2>/dev/null | grep -v 'wenshucha-seo'; \
  echo "*/15 * * * * cd $SEO_DIR && git pull origin main --quiet  # wenshucha-seo"; \
  echo "0 9 * * * cd $SEO_DIR && bash scripts/daily_run.sh >> logs/daily.log 2>&1  # wenshucha-seo"; \
  echo "0 10 * * 1 cd $SEO_DIR && bash scripts/weekly_run.sh >> logs/weekly.log 2>&1  # wenshucha-seo"; \
) | crontab -
echo "    ✓ cron 已注册:"
crontab -l | grep wenshucha-seo

# 6) mkdir logs + 跑一次 daily_run 验证
echo "[6/6] 跑一次 daily_run 验证 IndexNow 推送"
mkdir -p $SEO_DIR/logs
cd $SEO_DIR && bash scripts/daily_run.sh

echo
echo "============================================================"
echo "✓ wenshucha-seo install DONE"
echo "============================================================"
echo "下一步:Jack 注册百度站长平台拿 token 后,把 token 放到"
echo "       $SEO_DIR/secrets/baidu_push_token"
echo "       百度主动推送自动启用"
