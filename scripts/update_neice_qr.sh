#!/usr/bin/env bash
# 更新内测群二维码 —— 微信群码 7 天过期,到期跑这个换新的
#
# 用法: bash update_neice_qr.sh ~/Downloads/新二维码.jpg
#
# 二维码在【两个站】都要换,而且两边的上线方式完全不同 —— 这是最容易漏的地方:
#   · www.wenshucha.com  静态站,git push → 服务器 sync 脚本拉 tarball,几秒生效
#   · tob.wenshucha.com  Next.js standalone,public/ 下的图【必须重新构建 + rsync + 重启】,
#                        只 git push 不会上线(2026-09-02 就是这么翻的车:推了 GitHub 以为
#                        改完了,Jack 打开还是旧付费墙)
set -euo pipefail
SRC="${1:-}"
[ -f "$SRC" ] || { echo "❌ 找不到文件: $SRC"; echo "用法: bash update_neice_qr.sh <二维码图片路径>"; exit 1; }
SRV=root@114.132.74.235

echo "=== 1/3 www.wenshucha.com(静态站) ==="
mkdir -p ~/wenshucha-site/img && cp "$SRC" ~/wenshucha-site/img/neice-qr.jpg
cd ~/wenshucha-site
git add img/neice-qr.jpg
git commit -q -m "更新内测群二维码(微信群码 7 天过期)" 2>/dev/null || echo "  (无变化)"
git push -q origin main && echo "  ✓ 已推 GitHub"
ssh -o ConnectTimeout=30 $SRV "bash /root/sync-wenshucha-site.sh 2>&1 | tail -1"

echo "=== 2/3 tob.wenshucha.com(Next.js,必须重新构建) ==="
mkdir -p ~/peilema/apps/web/public && cp "$SRC" ~/peilema/apps/web/public/neice-qr.jpg
cd ~/peilema
git pull -q --rebase 2>/dev/null || true
git add apps/web/public/neice-qr.jpg
git commit -q -m "更新内测群二维码" 2>/dev/null || echo "  (无变化)"
git push -q origin main && echo "  ✓ 已推 GitHub"
cd ~/peilema/apps/web
echo "  构建中(1-3 分钟)…"
npx next build >/tmp/qr_build.log 2>&1 || { echo "  ❌ 构建失败,看 /tmp/qr_build.log"; exit 1; }
echo "  ✓ 构建完成"
ssh -o ConnectTimeout=25 $SRV "cd /www/wwwroot && rm -rf peilema.bak && cp -a peilema peilema.bak" 
# 顺序要害:先 rsync 再重启。Next standalone 启动时吃 .next/static 快照,反了会拿到旧资源。
rsync -az --delete .next/standalone/apps/web/ $SRV:/www/wwwroot/peilema/apps/web/
rsync -az .next/standalone/node_modules/ $SRV:/www/wwwroot/peilema/node_modules/ || true
rsync -az --delete .next/static/ $SRV:/www/wwwroot/peilema/apps/web/.next/static/
rsync -az public/ $SRV:/www/wwwroot/peilema/apps/web/public/
ssh -o ConnectTimeout=30 $SRV "systemctl restart peilema && sleep 5 && systemctl is-active peilema" | sed 's/^/  服务: /'

echo "=== 3/3 清缓存 + 公网验证 ==="
# 这台机宝塔在 http 层开了全局 proxy_cache,不清的话热 URL 照返旧响应
ssh -o ConnectTimeout=30 $SRV "find /www/server/nginx/proxy_cache_dir -type f -delete 2>/dev/null; nginx -s reload" || true
sleep 3
ok=1
for u in https://www.wenshucha.com/img/neice-qr.jpg https://tob.wenshucha.com/neice-qr.jpg; do
  c=$(curl -s -o /dev/null -w '%{http_code}' "$u"); s=$(curl -s -o /dev/null -w '%{size_download}' "$u")
  printf "  %-46s HTTP %s  %sB\n" "$u" "$c" "$s"
  [ "$c" = "200" ] || ok=0
done
[ "$ok" = "1" ] && echo "  ✅ 两站都已上线" || { echo "  ❌ 有站没生效"; exit 1; }
