#!/bin/bash
# ⏳ 复核（止损线④）取数脚本 —— 2026-09-05 建
#
# 为什么存在：这个坑今天之前已经独立踩过两次，每次都在浪费一轮的开工时间去人工排查：
#   · 09-02 07:5x：把 2076572388515386924 当成未入库的 qid，实为 Q664580472 的 aid
#   · 09-05 20:1x：一口气报出 5 条「未入库」，逐条查完 5 条全是行内加粗的 aid
# 根因：台账正文里 aid 也写成 `**2074442882241523743**` 这种加粗形式，
#       任何「grep 加粗数字」的写法都会把 aid 一起捞成 qid，且 aid 永远查不到 ⇒ 稳定假阳性。
# 另一层污染（已有记忆 reference_zhihu_ledger_grep_narrative_pollution）：
#       空跑行 / 结案行 / 口径订正行第 3 栏是「—」，不是 qid，会被计数类 grep 多算。
#
# 唯一正确口径：只认「第 2 栏恰为 知乎回答、第 3 栏为纯数字」的真文章行，取第 3 栏。
# 用法：bash ~/wenshucha-seo/scripts/zhihu_pending_audit.sh <线上qid清单文件>
#       线上清单从 Chrome 拿：creators/creations/v2/answer 全量翻页取 data[].data.question_id
#       （注意字段在 data[].data 里嵌套一层，不是 data[] 顶层——顶层没有 question_id）
# 本脚本【只读】。

LOG=~/wenshucha-seo/content/drafts/PUBLISH-LOG.md
ONLINE="$1"

if [[ ! -f "$ONLINE" ]]; then
  echo "用法: $0 <线上qid清单文件（每行一个或逗号分隔）>"; exit 2
fi

tr ',' '\n' < "$ONLINE" | grep -oE '^[0-9]+$' | sort -u > /tmp/.zh_online.txt
echo "线上 qid（去重）: $(wc -l < /tmp/.zh_online.txt)"

# 真文章行：第 2 栏 知乎回答，第 3 栏纯数字（允许 ** 包裹）
# 台账存在两种栏位排列（2026-09-05 20:3x 发现，别再只认第一种）：
#   标准： 日期 | 知乎回答 | qid | 标题 | ...
#   变体： 日期 | 叙述文字 | 知乎回答 | qid | ...     ← 复核行/结案行常用
# 所以不能写死 $2/$3，要扫全部栏位找「某栏含 知乎回答 且下一栏是纯数字」。
awk -F'|' '
  {
    hit=0;
    for (i=1; i<NF; i++) {
      c=$i; n=$(i+1);
      gsub(/^[ \t]+|[ \t]+$/,"",c); gsub(/[ \t*]/,"",n);
      # qid 有三种写法（08-17~08-28 早期用 Q 前缀，且常与标题黏在一栏）：
      #   `2078742019149767782` / `**2078742019149767782**` / `Q309992362「标题…」`
      sub(/^Q/,"",n); sub(/[^0-9].*$/,"",n);
      if (c ~ /知乎回答/ && n ~ /^[0-9]+$/ && length(n)>=6) { print n "\t" $0; hit=1; break; }
    }
  }' "$LOG" > /tmp/.zh_rows.txt

cut -f1 /tmp/.zh_rows.txt | sort -u > /tmp/.zh_all_qid.txt
grep -P '\t.*⏳' /tmp/.zh_rows.txt 2>/dev/null | cut -f1 | sort -u > /tmp/.zh_pending.txt
[[ -s /tmp/.zh_pending.txt ]] || grep '⏳' /tmp/.zh_rows.txt | cut -f1 | sort -u > /tmp/.zh_pending.txt

echo "台账真文章行 qid（去重）: $(wc -l < /tmp/.zh_all_qid.txt)"
echo "其中标 ⏳ 的 qid: $(wc -l < /tmp/.zh_pending.txt)"
echo
echo "═══ ⏳ 差集（标⏳ 且线上查不到）＝ 止损线④ 判据 ═══"
comm -23 /tmp/.zh_pending.txt /tmp/.zh_online.txt > /tmp/.zh_diff.txt
if [[ -s /tmp/.zh_diff.txt ]]; then
  echo "🔴 $(wc -l < /tmp/.zh_diff.txt) 条真待查："
  while read -r q; do
    echo "  --- $q ---"
    grep -n "$q" "$LOG" | cut -c1-200 | sed 's/^/     /'
  done < /tmp/.zh_diff.txt
  echo
  echo "  ⚠️ 逐条人工确认后再判止损线④：先确认它出现在第 3 栏（是 qid），"
  echo "     不是正文里被加粗的 aid。本脚本已按栏位过滤，理论上不会再混入 aid，"
  echo "     但台账格式若被手改破坏，仍需人眼过一遍。"
else
  echo "✅ 差集为空 ⇒ 零真待查，止损线④未触发"
fi
echo
echo "═══ 线上有、台账无（提示：多为格式异类，非抢发判据）═══"
comm -13 /tmp/.zh_all_qid.txt /tmp/.zh_online.txt > /tmp/.zh_rev.txt
if [[ -s /tmp/.zh_rev.txt ]]; then
  echo "ℹ️ $(wc -l < /tmp/.zh_rev.txt) 条线上有、台账真文章行无。"
  sed 's/^/  /' /tmp/.zh_rev.txt
  echo "  ⚠️ 这一栏是【提示，不是判据】。2026-09-05 实测非零几乎全是格式异类："
  echo "     · 第 2 栏写成「知乎·同步发文失败」「知乎回答区」等变体（不含连续「知乎回答」四字）"
  echo "     · qid 被塞进标题栏、第 3 栏放的是 aid（如 631302291）"
  echo "     判「第二 runner 抢发」前必须先 grep 全文确认台账真的一个字都没提过它。"
else
  echo "✅ 无"
fi

echo
echo "═══ 台账有、线上无 ═══"
comm -23 /tmp/.zh_all_qid.txt /tmp/.zh_online.txt > /tmp/.zh_fwd.txt
if [[ -s /tmp/.zh_fwd.txt ]]; then
  echo "ℹ️ $(wc -l < /tmp/.zh_fwd.txt) 条："
  sed 's/^/  /' /tmp/.zh_fwd.txt
  echo "  ⚠️ 正常情形＝【银行稿（写好未发）】或【已报废稿】，都不是丢稿。"
  echo "     2026-09-05 实测 3 条：2 篇银行稿 + 1 篇撞死羊题（过夜 0→97 答，触 30 闸门报废）。"
  echo "     只有当这条同时标着 ⏳ 时才是真问题——那种情况会出现在上面的 ⏳ 差集里。"
else
  echo "✅ 无"
fi
