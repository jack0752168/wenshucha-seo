#!/usr/bin/env python3
"""关键词资产库 —— 白杨方法论里的「长尾关键词记录单」

为什么(2026-07-22):
  白杨把这个当所有后续动作的地基。我们有 590 个词散在 81 个文件的 meta 里,
  但没有台账:不知道哪个词对应哪个页、哪些词重复打架、哪些页在抢同一个词、
  哪些词已经有展现。结果就是「每天不知道该优化什么」。

  他给的最小字段只要两列(关键词 + 对应 URL),三个用途:
    ① 写文时直接调用做内链锚文本
    ② 避免时间久了忘记哪些词做过
    ③ 把每日工作从「盯主词排名」变成「有明确待办」

本脚本在此基础上多带三样我们自己需要的:
  · 词分类(白杨五类词:品牌/产品/痛点/场景/长尾)—— 决定该做成什么页、转化价值
  · 冲突检测(白杨硬约束:不同栏目的长尾词不得交叉重叠,防站内自己打架)
  · 抓取状态(接 crawl_health 的 nginx 一手数据:这页百度抓过没)

用法:
  python3 kw_registry.py                 # 生成 content/keyword_registry.md + .json
  python3 kw_registry.py --conflicts     # 只看词冲突
  python3 kw_registry.py --orphans       # 只看「有词但百度没抓过」的页
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path.home() / "wenshucha-site"
OUT_MD = ROOT / "content" / "keyword_registry.md"
OUT_JSON = ROOT / "state" / "keyword_registry.json"
BASE = "https://www.wenshucha.com"

# 白杨五类词的判别规则(按优先级匹配,一词只归一类)
CLASSIFY = [
    ("品牌词", r"文书查|SinoVerdict|星谱"),
    ("痛点词", r"怎么|如何|多少钱|靠谱吗|哪个好|能不能|为什么|坑|风险|失败|难|问题|幻觉|翻车"),
    ("场景词", r"20\d\d|最新|新规|司法解释|年报|季|招标|采购|验收|立项"),
    ("产品词", r"系统|平台|工具|助手|API|MCP|软件|服务|部署|方案"),
]


def classify(kw: str) -> str:
    for name, rx in CLASSIFY:
        if re.search(rx, kw, re.I):
            return name
    # 3 个词以上/较长 = 长尾;否则算核心词
    return "长尾词" if len(kw) >= 8 else "核心词"


def url_of(f: Path) -> str:
    rel = f.relative_to(SITE).as_posix()
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[:-len('index.html')]}"
    return f"{BASE}/{rel}"


def crawled_paths():
    """问 crawl_health 要「百度从没抓过」的清单(nginx 一手数据)。拿不到返回 None。"""
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "crawl_health.py"), "--json"],
            capture_output=True, text=True, timeout=120,
        )
        d = json.loads(r.stdout)
        if d.get("ok"):
            return set(d.get("baidu_uncrawled", []))
    except Exception:
        pass
    return None


def collect():
    rows = []
    for f in sorted(SITE.rglob("*.html")):
        if ".git" in f.parts:
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'<meta name="keywords" content="([^"]*)"', t)
        if not m:
            continue
        ti = re.search(r"<title>(.*?)</title>", t, re.S)
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", ti.group(1))).strip() if ti else f.stem
        kws = [k.strip() for k in m.group(1).split(",") if k.strip()]
        rows.append({"file": str(f.relative_to(SITE)), "url": url_of(f),
                     "title": title, "kws": kws})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conflicts", action="store_true")
    ap.add_argument("--orphans", action="store_true")
    a = ap.parse_args()

    rows = collect()
    uncrawled = crawled_paths()

    # 词 → 页面映射(冲突检测)
    kw2pages = defaultdict(list)
    for r in rows:
        for k in r["kws"]:
            kw2pages[k].append(r["url"])
    conflicts = {k: v for k, v in kw2pages.items() if len(v) > 1}

    if a.conflicts:
        print(f"词冲突 {len(conflicts)} 个(同一个词被多个页面抢):")
        for k, v in sorted(conflicts.items(), key=lambda x: -len(x[1]))[:30]:
            print(f"  「{k}」× {len(v)}")
            for u in v:
                print(f"      {u.replace(BASE,'')}")
        return 0

    if a.orphans:
        if uncrawled is None:
            print("拿不到 nginx 抓取数据(本机不是站点服务器)")
            return 0
        orp = [r for r in rows if r["url"].replace(BASE, "") in uncrawled]
        print(f"有关键词但百度从没抓过的页: {len(orp)}/{len(rows)}")
        for r in orp[:40]:
            print(f"  {r['url'].replace(BASE,'')}  ({len(r['kws'])} 词)")
        return 0

    # 分类统计
    bycat = defaultdict(set)
    for k in kw2pages:
        bycat[classify(k)].add(k)

    today = date.today().isoformat()
    L = [
        "# 关键词资产库",
        "",
        f"> 自动生成 {today} · `python3 scripts/kw_registry.py`",
        "> 依据白杨方法论的「长尾关键词记录单」。最小字段=关键词+对应URL,",
        "> 用途:写文时调用做内链锚文本 / 避免重复做词 / 把工作变成有明确待办。",
        "",
        f"**{len(rows)} 个页面 · {len(kw2pages)} 个去重词 · {len(conflicts)} 个词冲突**",
        "",
        "## 一、按白杨五类词分布",
        "",
        "| 类型 | 词数 | 搜索意图 | 该做成什么页 | 转化价值 |",
        "|---|---|---|---|---|",
    ]
    META = {
        "品牌词": ("已认定你,只找入口", "首页 / 品牌介绍 / 联系方式", "★★★★★（量最小）"),
        "产品词": ("知道要什么,没认准谁家", "产品详情 / 案例 / 价格说明", "★★★★"),
        "痛点词": ("找解决方案,可能还不知道有你", "干货长文 + 咨询入口", "★★★★"),
        "场景词": ("特定情境下的临时需求", "场景专题 / 时令推荐", "★★"),
        "长尾词": ("已经很具体,目的性强", "问答型 / 对比评测 / 长尾专题", "★★★（总量大）"),
        "核心词": ("宽泛,竞争最激烈", "栏目页", "★★"),
    }
    for c in ["品牌词", "产品词", "痛点词", "场景词", "长尾词", "核心词"]:
        if c in bycat:
            i, p, v = META[c]
            L.append(f"| **{c}** | {len(bycat[c])} | {i} | {p} | {v} |")
    L += ["",
          "> ⚠️ 分类由规则自动判定,边界词可能归错。**用来看结构比例,别当精确统计。**",
          ""]

    # 冲突段(白杨硬约束)
    L += ["## 二、词冲突（白杨硬约束：不同栏目的长尾词不得交叉重叠）", ""]
    if conflicts:
        L.append(f"**{len(conflicts)} 个词被多个页面同时抢**——站内自己打架，会互相稀释排名。")
        L += ["", "| 关键词 | 抢的页面数 | 页面 |", "|---|---|---|"]
        for k, v in sorted(conflicts.items(), key=lambda x: -len(x[1]))[:25]:
            paths = "<br/>".join(u.replace(BASE, "") for u in v[:4])
            L.append(f"| {k} | {len(v)} | {paths} |")
        L += ["", "**处理原则**：一词一页。留意图最匹配的那个页保住这个词，其余页把该词从 keywords 里删掉，",
              "改用各自的差异化长尾词。", ""]
    else:
        L += ["✅ 无冲突。", ""]

    # 抓取状态
    L += ["## 三、抓取状态（nginx 一手数据）", ""]
    if uncrawled is None:
        L += ["_本机拿不到 nginx 日志（不是站点服务器）。在腾讯云上跑本脚本可得。_", ""]
    else:
        orp = [r for r in rows if r["url"].replace(BASE, "") in uncrawled]
        L.append(f"**{len(orp)}/{len(rows)} 个带词页面，百度从来没抓过** —— "
                 f"这些页上的关键词等于没做。")
        L += ["", "> 白杨排名三原则：相关性只决定**能不能被收录**。这些页卡在第一环，",
              "> 在抓取修好之前，给它们加词、改标题都是空转。", ""]

    # 全量台账
    L += ["## 四、全量台账（关键词 → URL）", "",
          "| 页面 | 标题 | 关键词 |", "|---|---|---|"]
    for r in sorted(rows, key=lambda x: x["file"]):
        p = r["url"].replace(BASE, "")
        ti = r["title"][:38].replace("|", "丨")
        kw = "、".join(r["kws"][:8]) + ("…" if len(r["kws"]) > 8 else "")
        L.append(f"| `{p}` | {ti} | {kw} |")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(
        {"date": today, "pages": len(rows), "keywords": len(kw2pages),
         "conflicts": {k: v for k, v in conflicts.items()},
         "by_category": {k: sorted(v) for k, v in bycat.items()},
         "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"✓ {len(rows)} 页 · {len(kw2pages)} 词 · {len(conflicts)} 个冲突")
    print(f"  → {OUT_MD}")
    for c in ["品牌词", "产品词", "痛点词", "场景词", "长尾词", "核心词"]:
        if c in bycat:
            print(f"    {c:5s} {len(bycat[c]):4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
