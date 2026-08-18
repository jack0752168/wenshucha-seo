#!/usr/bin/env bash
# 百度统计一键安装 —— Jack 扫码拿到 ID 后跑这个,30 秒完事
#
# 用法:  bash install_tongji.sh <hm_id>
#   <hm_id> = 百度统计给的那串 32 位十六进制,在「代码管理 → 代码获取」里,
#             形如 hm.src = "https://hm.baidu.com/hm.js?xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#             只要 ? 后面那串,别整段贴。
#
# 为什么写成脚本:2026-08-18 尝试装百度统计,tongji.baidu.com 不认 ziyuan 的
# passport 会话,必须扫码或输密码 —— 密码我不碰,所以卡在这一步。
# 把注入这段固化下来,Jack 一给 ID 就能立刻装完,不用重新摸一遍。
set -euo pipefail
ID="${1:-}"
[[ "$ID" =~ ^[0-9a-f]{32}$ ]] || { echo "❌ ID 应该是 32 位十六进制,你给的是:$ID"; exit 1; }
HOST=root@114.132.74.235

ssh -o ConnectTimeout=30 "$HOST" "ID='$ID' python3 - <<'PY'
import os
from pathlib import Path
ID = os.environ['ID']
SNIP = ('<!--baidu-tongji-->\n<script>\nvar _hmt=_hmt||[];(function(){var hm=document.createElement(\"script\");'
        'hm.src=\"https://hm.baidu.com/hm.js?%s\";var s=document.getElementsByTagName(\"script\")[0];'
        's.parentNode.insertBefore(hm,s);})();\n</script>\n' % ID)
root = Path('/www/wwwroot/wenshucha.com')
done = skip = 0
for f in sorted(root.rglob('*.html')):
    t = f.read_text(encoding='utf-8', errors='replace')
    if 'baidu-tongji' in t: skip += 1; continue
    if '</body>' not in t: continue
    f.write_text(t.replace('</body>', SNIP + '</body>', 1), encoding='utf-8')
    done += 1
print(f'注入 {done} 个页面(已有跳过 {skip})')
PY"

echo "--- 公网验证(热 URL,防缓存假绿)---"
for u in https://www.wenshucha.com/ https://www.wenshucha.com/blog/ https://www.wenshucha.com/data/; do
  n=$(curl -s "$u" | grep -c "hm.baidu.com/hm.js?$ID" || true)
  echo "  $u  →  $([[ $n -gt 0 ]] && echo ✅ 已带统计代码 || echo '❌ 没带,查 proxy_cache')"
done
echo
echo "接下来:回百度统计后台点「代码安装检查」,通过后约 20 分钟出第一批数据。"
