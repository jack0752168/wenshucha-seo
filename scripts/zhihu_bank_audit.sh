#!/bin/bash
# 知乎银行稿队列体检 —— 2026-09-05 建
#
# 为什么存在：银行稿过夜必腐坏，已实测四种形态（见 PUBLISH-LOG 09-05）：
#   ① 开场「前面答主」失准（点名的人不在线／点错最对症那条）
#   ② 时间副词过期（「刚才现查」「挂出来六个小时」）
#   ③ 问题页热度腐坏（totals 冲过 30，硬闸门作废）
#   ④ 答数自述数字过期（「前面十一个回答」变成十三个）
# 每轮开工手写 5-6 次 Chrome API 调用去验这些，是纯重复劳动。
#
# 用法：
#   bash ~/wenshucha-seo/scripts/zhihu_bank_audit.sh          # 本地部分 + 生成 JS
#   然后把打印出来的 JS 整段贴进已登录 Chrome 的知乎页执行，拿线上部分。
#
# 本脚本【只读】，不发布、不改稿。

CLAIM=~/wenshucha-seo/content/drafts/.zhihu-claim
ROOT=~/wenshucha-seo

echo "═══════════════ 一、队列清单（来源＝抢占锁目录） ═══════════════"
QIDS=()
PUBLOCK=()
declare -a DRAFTS
# 2026-09-06 11:2x 修：state 提取原来只认小写（'state[:=] *[a-z]+'），
#   而已发布的锁写的是大写 `state: PUBLISHED` ⇒ 匹配不到、显示 state=?，
#   于是 5 篇早已发布的锁每轮都被当成待发队列列出来（09-06 11:0x 实测名义 9 篇、真实只有 4 篇）。
#   后果不是误报那么轻：体检报告虚高会让人以为「银行有货」，进而低估当天要现写几篇。
# 处置＝正则改 [A-Za-z_]+ 并统一折成小写；state=published 的锁移出队列、单列结案区，
#   但仍计入 LOCKED（否则「有稿无锁」那节会把它们反过来误报成漏锁）。
for f in "$CLAIM"/*; do
  b=$(basename "$f"); [[ "$b" == "README.md" ]] && continue
  [[ "$b" =~ ^[0-9]+$ ]] || continue
  # 2026-09-07 16:2x 修（治因，不是治标）：原来取 head -1 ＝【首行】state。
  #   锁文件是【追加写】的：选题时写 state=banked，发布成功后在文件末尾追加 state=published，
  #   首行永远停在 banked ⇒ 已发布的题每轮都被重新列进待发队列，取用即【重投＝覆盖线上回答】。
  #   09-06 11:2x 已在 qid 2079321719463064463 上踩过一次，当时只手工改了那一个锁文件的首行、
  #   没动脚本 ⇒ 09-07 在 qid 1988688681624684147 上【原样复发】（首行 banked、次行 published，
  #   而该题 11:31:34 已入库 aid=2080256902005535895）。
  #   新口径＝【终态优先】：文件内任意一处出现 published/discarded（含 PUBLISHED-BY-OTHER-RUNNER）
  #   即判结案，只有全程没有终态时才回落到首行。追加写的语义下，终态一旦出现就不可逆。
  allstate=$(grep -oE 'state[:=] *[A-Za-z_]+' "$f" | sed 's/.*[:=] *//' | tr 'A-Z' 'a-z')
  if grep -qE '^(published|discarded)$' <<<"$allstate"; then
    state=$(grep -E '^(published|discarded)$' <<<"$allstate" | head -1)
  else
    # 2026-09-07 17:4x 修（与上面 16:2x 的终态优先同源，是它漏掉的第二层）：
    #   非终态之间原来也取 head -1 ＝【首次写入】的 state 胜出。锁是追加写的，
    #   claimed（选题占位）→ banked（稿子写完）这条推进因此永远显示不出来：
    #   qid 2000657090675499210 首行 claimed、末行 banked、稿与 inject 包都在，
    #   脚本却报 state=claimed ⇒ 读者会按「占位锁、没稿」处理，
    #   而该锁 16:3x 的处置建议正是「没稿就删锁释放选题」——那会连稿一起丢。
    #   追加写语义下【最后一次写入才是当前状态】，故非终态改取 tail -1。
    #   终态仍然优先且不可逆（终态一旦出现，后面写什么都不该翻案）。
    state=$(tail -1 <<<"$allstate")
  fi
  draft=$(grep -oE 'draft[:=] *[^ ]+\.md' "$f" | head -1 | sed 's/.*[:=] *//')
  [[ -z "$draft" ]] && draft=$(grep -oE '(content/)?drafts/[0-9-]+/[A-Za-z0-9_.-]+\.md' "$f" | head -1)
  if [[ "$state" == "published" || "$state" == "discarded" ]]; then
    PUBLOCK+=("$b")
    echo "  qid=$b  state=$state  ⇒ 已结案，不进队列"
    continue
  fi
  QIDS+=("$b"); DRAFTS+=("$draft")
  echo "  qid=$b  state=${state:-?}  draft=${draft:-未记录}"
done
echo "  待发队列合计 ${#QIDS[@]} 篇（已结案 ${#PUBLOCK[@]} 篇不计）"

echo
echo "═══════════════ 二、本地腐坏扫描（形态②④：时间副词 / 答数自述） ═══════════════"
for i in "${!QIDS[@]}"; do
  q="${QIDS[$i]}"; d="${DRAFTS[$i]}"
  echo "--- qid $q ---"
  # 定位稿子：锁里记的路径可能相对 repo 根，也可能相对 drafts/
  p=""
  for cand in "$ROOT/$d" "$ROOT/content/$d" "$ROOT/content/drafts/$d"; do
    [[ -f "$cand" ]] && { p="$cand"; break; }
  done
  [[ -z "$p" ]] && p=$(grep -rl "$q" "$ROOT"/content/drafts/2026-*/ 2>/dev/null | grep '\.md$' | grep -v inject | head -1)
  if [[ -z "$p" ]]; then echo "  ⚠️ 找不到稿件文件，人工确认"; continue; fi
  echo "  稿：${p#$ROOT/}"
  # 只扫正文区（BODY-START 之后 / 「## 正文」之后），避开稿头自检清单里的自我描述
  body=$(awk '/BODY-START|^## 正文/{f=1;next} /BODY-END/{f=0} f' "$p")
  [[ -z "$body" ]] && body=$(cat "$p")
  t=$(printf '%s' "$body" | grep -nE "刚才|刚刚|今天|昨天|今日|此刻|这题挂出来|个小时|现查|刚查|方才|眼下" | head -8)
  if [[ -n "$t" ]]; then echo "  🔴 时间副词命中（形态②，必须逐条判是否会过期）:"; printf '%s\n' "$t" | sed 's/^/     /'; 
  else echo "  ✅ 时间副词：正文零命中"; fi
  n=$(printf '%s' "$body" | grep -nE "[0-9一二三四五六七八九十两]+ *(个|条|位)? *(回答|答主)|十几个|几位答主|前面.{0,4}答主" | head -8)
  if [[ -n "$n" ]]; then echo "  ⚠️ 答数自述（形态④，须与线上 totals 对上）:"; printf '%s\n' "$n" | sed 's/^/     /'; 
  else echo "  ✅ 答数自述：正文零命中"; fi
  # 形态⑤·折叠红线词（2026-09-06 新增，当轮就抓到一处真命中）
  # 为什么加：08-21 qid 2015079598409404928 因正文出现「加微信」被 community 折叠，
  #   记忆 reference_zhihu_fold_trigger_wechat_promo 定的红线是「付费墙照旧如实写，
  #   但绝不许抄『加微信』『开通更多用量』这类词，一律改中性表述」。
  #   但本脚本此前只扫时间副词与答数自述，**红线词一个字都没扫**——
  #   09-06 08:3x 取用 2075995722890192228 时人工才发现正文写着「用超了要另外开通」，
  #   它已经在队列里躺了 14 个小时、过了两轮「全绿」体检。⇒ 全绿曾经是假的。
  # 处置：命中不等于必须删，等长改成中性表述即可（该篇「另外开通」→「是收费的」，
  #   段数字数不变，lint 结果一致）。
  r=$(printf '%s' "$body" | grep -nE "加微信|微信号|扫码|开通|更多用量|私信我|联系我|加我|VX|vx|威信" | head -8)
  if [[ -n "$r" ]]; then echo "  🔴 折叠红线词命中（形态⑤，发前必须改成中性表述）:"; printf '%s\n' "$r" | sed 's/^/     /'; 
  else echo "  ✅ 折叠红线词：正文零命中"; fi
done

echo
echo "═══════════════ 三、线上部分：把下面整段贴进已登录 Chrome 执行 ═══════════════"
echo "（验形态①③：totals <30 硬闸门 + 开场点名的答主是否仍在线）
⚠️ 必须在 **www.zhihu.com** 源的标签页里执行。在 zhuanlan.zhihu.com 上跑会 HTTP 404（跨源），
   2026-09-08 实测：8 个 qid 全 404 → totals 全 null → 旧判据 `null<30` 在 JS 里为 true → **8 个全报 PASS**（假阳性）。
   判据已改成三态：typeof totals==='number' 才判 PASS/FAIL，否则 UNKNOWN。**UNKNOWN 一律不投。**"
echo
printf 'const QS=[%s];\n' "$(printf '"%s",' "${QIDS[@]}" | sed 's/,$//')"
echo
echo "═══════════════ 二之二、锁完整性自检（有稿无锁 / 有锁无稿） ═══════════════"
# 为什么加（2026-09-05 21:1x）：「写稿」与「建锁」不是原子操作，漏建锁当天已复发两次
#   （14:0x 修过一次，18:21 的 2075995722890192228 与 19:20 的 2076517924555191866 又双双漏建，
#    队列名义 7/7、实际只有 5 篇有锁）。漏锁的后果是第二 runner 看不到占用 ⇒ 可能重复选到同一题。
# 这一节把「靠人记得建锁」换成「每轮体检自动报出来」，不修复原子性，但保证漏了当轮就被抓到。
LOCKED=$(printf '%s\n' "${QIDS[@]}" "${PUBLOCK[@]}" | grep -E '^[0-9]+$' | sort -u)
# 从今日与昨日的 drafts 目录里，按【文件名带 qid】和【稿头写了 qid】两条路取候选
CAND=$(
  for d in "$ROOT"/content/drafts/$(date +%Y-%m-%d) "$ROOT"/content/drafts/$(date -v-1d +%Y-%m-%d 2>/dev/null); do
    [[ -d "$d" ]] || continue
    for f in "$d"/*.md; do
      [[ -f "$f" ]] || continue
      [[ "$f" == *.bak-* || "$f" == *inject* ]] && continue
      basename "$f" | grep -oE '[0-9]{9,}'
      grep -oE '^\s*(qid|question_id)[:= ]+\**([0-9]{9,})' "$f" 2>/dev/null | grep -oE '[0-9]{9,}'
    done
  done | sort -u
)
# 已发布的 qid 不该再报（它们不需要锁）——用台账真文章行兜底排除
# 🔴 2026-09-06 20:1x 修（这是个「假绿」bug，比漏报更毒）：
#   旧条件 `c ~ /知乎回答/` 是**子串**匹配，于是台账里标了
#   「知乎回答（**银行稿·未投递**）」的**待发**稿也被当成已发布塞进 PUBQ，
#   NOLOCK 那一步再把它们从「有稿无锁」里减掉 ⇒ 报 ✅ 零命中。
#   实测本轮：qid 7862373219（物业服务合同，19:3x 新写）**确实有稿无锁**，
#   脚本却报零命中；且因无锁不进 QIDS，它的腐坏扫描与线上体检整篇漏做。
#   撞车代价是真的——09-06 09:43:17 第二 runner 就抢发过同一份稿。
#   新口径＝第 2 列必须【以「知乎回答」开头】且【不含「未投递」/「银行稿」】。
#   保留 startsWith 而非全等，是因为已发布行存在
#   「知乎回答（**清积压·续发，非新题**）」这类合法后缀（qid 654077779）。
PUBQ=$(awk -F'|' '{for(i=1;i<NF;i++){c=$i;n=$(i+1);gsub(/^[ \t]+|[ \t]+$/,"",c);gsub(/[ \t*]/,"",n);sub(/^Q/,"",n);sub(/[^0-9].*$/,"",n); if(index(c,"知乎回答")==1 && c !~ /未投递|银行稿/ && n ~ /^[0-9]+$/ && length(n)>=6){print n; break}}}' \
  "$ROOT/content/drafts/PUBLISH-LOG.md" 2>/dev/null | sort -u)
NOLOCK=$(comm -23 <(printf '%s\n' $CAND | sort -u) <(printf '%s\n' $LOCKED | sort -u) | comm -23 - <(printf '%s\n' $PUBQ | sort -u))
if [[ -n "$NOLOCK" ]]; then
  echo "  🔴 有稿无锁（且台账里查不到已发布）——建稿时漏建锁，第二 runner 看不到占用："
  printf '     %s\n' $NOLOCK
  echo "     处置：确认确是待发银行稿 ⇒ 立刻在 .zhihu-claim/ 补锁；若是废稿 ⇒ 在台账写一行结案，别留悬空。"
else
  echo "  ✅ 有稿无锁：零命中"
fi
for i in "${!QIDS[@]}"; do
  q="${QIDS[$i]}"; d="${DRAFTS[$i]}"
  [[ -z "$d" ]] && echo "  ⚠️ 有锁无稿路径：qid $q 的锁没记 draft=，每轮都得靠 grep 全库兜底找稿，请补进锁文件"
done

cat <<'JS'
let out={};
for(const q of QS){
  let names=[],off=0,totals=null;
  for(let p=0;p<3;p++){
    const r=await fetch('/api/v4/questions/'+q+'/answers?limit=20&offset='+off
      +'&include=data%5B*%5D.author%2Ccontent&order_by=default',{credentials:'include'});
    if(r.status!==200){names.push('HTTP'+r.status);break;}
    const j=await r.json();
    if(totals===null&&j.paging) totals=j.paging.totals;
    (j.data||[]).forEach(a=>names.push((a.author&&a.author.name||'?')
      +'|'+String(a.content||'').replace(/<[^>]+>/g,'').length+'字'));
    if(j.paging&&j.paging.is_end)break; off+=20;
  }
  out[q]={totals:totals, gate:(typeof totals==='number' ? (totals<30?'PASS':'🔴FAIL >30 该稿作废') : '⚠️UNKNOWN 没拿到 totals，别当 PASS'), answerers:names};
}
JSON.stringify(out,null,1);
JS
echo
echo "═══════════════ 判读 ═══════════════"
echo "  gate FAIL          ⇒ 形态③问题页热度腐坏，稿子作废，别浪费 CAP 名额"
echo "  totals 与②④对不上 ⇒ 改开场数字"
echo "  点名的人不在 answerers 里 ⇒ 形态①，重写开场"
echo "  ⚠️ answerers 只能人工比对：稿里点名有的带 @ 有的不带，正则挑不干净，不装能自动判"
echo "  ⚠️ 本脚本【不】替代投前 60 秒拉 answers API 定当日入库数（防第二 runner 撞车）"
