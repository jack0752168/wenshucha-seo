#!/bin/bash
# 算银行稿问题页热度腐坏速率(答/小时),并外推到指定时刻
# 用法: ./rate.sh [外推目标时刻,默认明早10:00]
set -e
F="$(dirname "$0")/snapshot.tsv"
[ -f "$F" ] || { echo "无快照,先跑收工快照"; exit 1; }
TARGET="${1:-$(date -v+1d +%Y-%m-%dT10:00)}"
TS=$(date -j -f "%Y-%m-%dT%H:%M" "$TARGET" +%s 2>/dev/null) || { echo "时刻格式错: $TARGET"; exit 1; }
printf "%-22s %6s %6s %8s %10s  %s\n" QID 首测 最新 答/小时 "外推@$TARGET" 判定
awk -F'\t' '$1!~/^#/ && NF>=3 {print}' "$F" | sort -t$'\t' -k2,2 -k1,1 | awk -F'\t' -v ts="$TS" '
{ q=$2; if(!(q in first)){first[q]=$3; ft[q]=$1} last[q]=$3; lt[q]=$1; note[q]=$4 }
END{
  for(q in first){
    cmd="date -j -f \"%Y-%m-%dT%H:%M\" \"" ft[q] "\" +%s"; cmd|getline f; close(cmd)
    cmd2="date -j -f \"%Y-%m-%dT%H:%M\" \"" lt[q] "\" +%s"; cmd2|getline l; close(cmd2)
    dh=(l-f)/3600
    rate = (dh>0.5) ? (last[q]-first[q])/dh : 0
    proj = (ts>l) ? last[q] + rate*(ts-l)/3600 : last[q]
    verdict = (last[q]>30) ? "作废(已破30)" : (proj>30 ? "优先发(将破30)" : (dh<=0.5 ? "样本不足" : "安全"))
    printf "%-22s %6d %6d %8.2f %10.1f  %s\n", q, first[q], last[q], rate, proj, verdict
  }
}'
