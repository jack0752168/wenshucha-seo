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
echo "--- [1/4] IndexNow → Bing/Yandex ---"
python3 scripts/push_indexnow.py

echo
echo "--- [2/4] 百度主动推送 ---"
python3 scripts/push_baidu.py

echo
echo "--- [3/4] Google Indexing API ---"
if [ -f scripts/push_google.py ]; then
    python3 scripts/push_google.py
else
    echo "⏭️  push_google.py 暂未实现(等 Jack 配 Google service account)"
fi

echo
echo "--- [4/4] SSL 到期监控 ---"
python3 scripts/ssl_monitor.py

echo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] done"
