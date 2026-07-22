#!/bin/bash
# Mac → 腾讯云 部署 SEO 代码。
# 不走 GitHub:国内服务器拉 github 不稳定(实测 fetch 卡死),SSH 直推可靠。
# 只推代码与配置,运行时数据(state/ logs/ reports/)一律不碰。
set -euo pipefail
SRC=~/wenshucha-seo
DST=root@114.132.74.235:/opt/wenshucha-seo
rsync -az --delete-after \
  --include='scripts/***' --include='content/***' --include='deploy/***' \
  --include='config.yml' --include='README.md' --include='.gitignore' \
  --exclude='*' \
  "$SRC"/ "$DST"/
# token 单独推(不在版本控制里)
if [ -f "$SRC/secrets/baidu_push_token" ]; then
  ssh root@114.132.74.235 'mkdir -p /opt/wenshucha-seo/secrets && chmod 700 /opt/wenshucha-seo/secrets'
  rsync -az "$SRC/secrets/baidu_push_token" root@114.132.74.235:/opt/wenshucha-seo/secrets/
  ssh root@114.132.74.235 'chmod 600 /opt/wenshucha-seo/secrets/baidu_push_token'
fi
echo "✓ 已部署到腾讯云"
