#!/usr/bin/env python3
"""生成《全国劳动争议赔偿数据报告》—— 原创调研数据页

为什么(2026-07-22,白杨SEO方法论):
  GEO 里杠杆最大的单一动作是「发布原创调研数据」——独一无二 + 有决策参考价值
  = AI 最想引用的形态。文书查的判决库是不可复制资产,竞品不会公开做这个。
  一箭三雕:AI 愿引用 + 百度稀缺内容 + 见客户的弹药。

⚠️ 三条不可逾越的诚实红线(违反一次就毁品牌信任,也正是白杨说的「GEO 投毒」):
  1. 样本仅含【获赔判决】(win 41835 + partial 38165,无败诉样本)
     → 任何比例都不得表述为「胜诉率」「支持率」
  2. 【禁止做逐年趋势】—— 采样严重不均(2019 年仅 1 份、2018 年 554 份、
     2020 年 11249 份),画成趋势线是纯误导。只做横截面分布。
  3. 所有数字由本脚本从原始数据实算,禁止手写。改口径先改这里。

数据源: ~/peilema/apps/web/lib/tob-bundle.json (80000 份判决, 2002-2023, 1620 城市)
用法: python3 gen_labor_report.py    # 写 ~/wenshucha-site/data/labor-report/index.html
"""
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

DATA = Path.home() / "peilema/apps/web/lib/tob-bundle.json"
OUT = Path.home() / "wenshucha-site/data/labor-report/index.html"
BASE = "https://www.wenshucha.com"

TERM_CN = {
    "layoff": "经济性裁员",
    "fired": "用人单位辞退 / 解雇",
    "contract_end": "劳动合同到期终止",
    "mutual": "协商一致解除",
    "quit": "劳动者主动 / 被迫离职",
}
# 城市页 slug 由 gen_labor_data_pages.py 用 pypinyin 生成,这里复用同一规则
try:
    from pypinyin import lazy_pinyin
    def slug(c): return "".join(lazy_pinyin(c)).lower()
except ImportError:
    def slug(c): return None


def pctl(a, p):
    a = sorted(a)
    if not a:
        return None
    k = (len(a) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(a) - 1)
    return a[f] + (a[c] - a[f]) * (k - f)


def money(x):
    return f"{x:,.0f}" if x is not None else "—"


def main():
    d = json.loads(DATA.read_text())
    cols, rows = d["cols"], d["rows"]
    i = {c: k for k, c in enumerate(cols)}

    comps = [r[i["compensation_judged"]] for r in rows if r[i["compensation_judged"]]]
    sals = [r[i["monthly_salary"]] for r in rows if r[i["monthly_salary"]]]
    years = sorted({str(r[i["judgement_date"]])[:4] for r in rows if r[i["judgement_date"]]})
    n_city = len({r[i["city"]] for r in rows if r[i["city"]]})
    won = Counter(r[i["plaintiff_won"]] for r in rows if r[i["plaintiff_won"]])

    # 按解除原因
    by_term = defaultdict(list)
    for r in rows:
        if r[i["compensation_judged"]] and r[i["termination_reason"]]:
            by_term[r[i["termination_reason"]]].append(r[i["compensation_judged"]])
    term_rows = sorted(by_term.items(), key=lambda x: -pctl(x[1], 50))

    # 按城市(取样本量 Top20,保证统计意义)
    by_city = defaultdict(list)
    for r in rows:
        if r[i["city"]] and r[i["compensation_judged"]]:
            by_city[r[i["city"]]].append(r[i["compensation_judged"]])
    city_rows = sorted(by_city.items(), key=lambda x: -len(x[1]))[:20]

    # 按工龄分段
    SEGS = ["1 年以内", "1-3 年", "3-5 年", "5-10 年", "10 年以上"]
    by_seg = defaultdict(list)
    for r in rows:
        y, c = r[i["work_years"]], r[i["compensation_judged"]]
        if y is None or not c:
            continue
        b = SEGS[0] if y < 1 else SEGS[1] if y < 3 else SEGS[2] if y < 5 else SEGS[3] if y < 10 else SEGS[4]
        by_seg[b].append(c)

    today = date.today().isoformat()
    N = len(rows)

    # ---------------- 组装 HTML ----------------
    def tr(*cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    dist_rows = "\n".join(
        tr(f"P{p}", money(pctl(comps, p)), desc)
        for p, desc in [(10, "偏低区间"), (25, "四分之一案件低于此数"),
                        (50, "<strong>中位数</strong>"), (75, "四分之一案件高于此数"),
                        (90, "偏高区间")]
    )
    term_tbl = "\n".join(
        tr(TERM_CN.get(k, k), f"{len(v):,}", money(pctl(v, 50)), money(pctl(v, 25)), money(pctl(v, 75)))
        for k, v in term_rows
    )
    seg_tbl = "\n".join(
        tr(b, f"{len(by_seg[b]):,}", money(pctl(by_seg[b], 50))) for b in SEGS if by_seg[b]
    )

    def city_link(c):
        s = slug(c)
        p = Path.home() / f"wenshucha-site/data/labor/{s}.html" if s else None
        return f'<a href="{BASE}/data/labor/{s}.html">{c}</a>' if (p and p.exists()) else c

    city_tbl = "\n".join(
        tr(city_link(c), f"{len(v):,}", money(pctl(v, 50)), money(pctl(v, 25)), money(pctl(v, 75)))
        for c, v in city_rows
    )

    faq = [
        ("劳动争议赔偿一般能拿到多少钱？",
         f"基于 {N:,} 份已获赔付的劳动争议判决样本，赔偿金额中位数为 {money(pctl(comps,50))} 元，"
         f"四分位区间为 {money(pctl(comps,25))} 至 {money(pctl(comps,75))} 元。"
         f"需要注意：本样本仅收录已获赔付的判决，不含败诉案件，因此该数字反映的是"
         f"「打赢之后通常拿到多少」，而不是「打官司能拿到多少」。个案差异极大，"
         f"实际金额取决于工资基数、工作年限、解除原因与当地裁判尺度。"),
        ("工作年限对赔偿金额影响有多大？",
         "影响显著且单调。按本样本分段测算，工作 1 年以内的赔偿中位数为 "
         f"{money(pctl(by_seg[SEGS[0]],50))} 元，10 年以上为 {money(pctl(by_seg[SEGS[4]],50))} 元，"
         "两者相差数倍。这与经济补偿金按工作年限计算的法定逻辑一致。"),
        ("哪种解除原因赔得更多？",
         "在本样本中，" + "、".join(f"{TERM_CN.get(k,k)}（中位 {money(pctl(v,50))} 元）"
                                  for k, v in term_rows[:3]) +
         "。总体规律是：用人单位单方解除的赔偿高于协商一致解除，协商一致又高于劳动者主动离职。"
         "这是数据呈现的分布特征，具体个案仍以事实认定与法律适用为准。"),
        ("这份数据能代表胜诉率吗？",
         "不能。本数据集仅收录已获赔付的判决样本，不包含败诉案件，"
         f"因此样本内「全部支持」与「部分支持」合计即为 100%（{won.get('win',0):,} 份全部支持、"
         f"{won.get('partial',0):,} 份部分支持）。任何据此计算的比例都不构成胜诉率，"
         "也不应作为诉讼前景的判断依据。"),
        ("为什么报告里没有逐年趋势图？",
         "因为本样本各年份的收录量并不均衡（部分年份样本极少），"
         "在采样不均的数据上画趋势线会产生误导。因此本报告只呈现横截面分布，"
         "不做年度对比。这也是我们对所有对外数据的一贯口径。"),
        ("数据来源是什么？可以核验吗？",
         "数据来源于中国裁判文书网公开生效裁判文书，当事人个人信息已脱敏。"
         "各城市页保留真实案号，可回溯原文核验。"),
    ]
    faq_html = "\n".join(
        f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faq
    )
    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a.replace("<strong>", "").replace("</strong>", "")}}
                       for q, a in faq]
    }, ensure_ascii=False)

    dataset_ld = json.dumps({
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "全国劳动争议赔偿数据报告",
        "description": f"基于 {N:,} 份中国裁判文书网公开生效劳动争议判决（{years[0]}-{years[-1]}，"
                       f"覆盖 {n_city:,} 个城市）的赔偿金额分布、解除原因构成与工作年限相关性统计。"
                       "样本仅含已获赔付判决，不含败诉样本，任何比例均不代表胜诉率。",
        "url": f"{BASE}/data/labor-report/",
        "creator": {"@type": "Organization", "name": "文书查",
                    "legalName": "深圳星谱网络科技有限公司", "url": BASE + "/"},
        "temporalCoverage": f"{years[0]}/{years[-1]}",
        "spatialCoverage": {"@type": "Place", "name": "中国大陆"},
        "isBasedOn": "中国裁判文书网公开生效裁判文书",
        "license": f"{BASE}/data/labor-report/",
        "variableMeasured": ["赔偿金额", "月工资", "工作年限", "解除原因", "支持程度", "审理法院所在城市"],
        "dateModified": today,
    }, ensure_ascii=False)

    breadcrumb_ld = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "文书查", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "裁判数据", "item": BASE + "/data/"},
            {"@type": "ListItem", "position": 3, "name": "全国劳动争议赔偿数据报告",
             "item": BASE + "/data/labor-report/"},
        ]}, ensure_ascii=False)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>全国劳动争议赔偿数据报告_{N:,}份判决实证_赔偿金额中位数{money(pctl(comps,50))}元 - 文书查</title>
<meta name="description" content="基于 {N:,} 份公开生效劳动争议判决（{years[0]}-{years[-1]}，覆盖 {n_city:,} 个城市）的实证统计：赔偿金额四分位分布、五类解除原因的赔偿差异、工作年限与赔偿的相关性、20 个主要城市横向对比。样本仅含已获赔付判决，不代表胜诉率。数据可回溯原文核验。">
<meta name="keywords" content="劳动争议赔偿数据,劳动仲裁赔偿标准,经济补偿金数据,违法解除赔偿金,裁员赔偿多少钱,劳动争议判决统计,司法大数据报告,劳动争议大数据">
<link rel="canonical" href="{BASE}/data/labor-report/">
<meta name="robots" content="index,follow,max-snippet:-1">
<meta property="og:title" content="全国劳动争议赔偿数据报告 · {N:,} 份判决实证 | 文书查">
<meta property="og:description" content="赔偿金额中位数 {money(pctl(comps,50))} 元，四分位区间 {money(pctl(comps,25))}–{money(pctl(comps,75))} 元。含解除原因、工作年限、城市三个维度的横截面分布。">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/data/labor-report/">
<script type="application/ld+json">{dataset_ld}</script>
<script type="application/ld+json">{breadcrumb_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
<style>
:root{{--navy:#0e1b2e;--accent:#c8a35a;--accent2:#3a6ea5;--bg:#f7f8fb;--ink:#1a2433;--mut:#5a6677}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
a{{color:var(--accent2)}}
.wrap{{max-width:900px;margin:0 auto;padding:0 22px}}
header{{background:var(--navy);color:#fff;padding:14px 0;position:sticky;top:0;z-index:9}}
header .wrap{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
header a{{color:#fff;text-decoration:none;font-weight:600}}
header nav a{{margin-left:16px;font-weight:400;font-size:14px;opacity:.85}}
.hero{{background:linear-gradient(160deg,#0e1b2e,#16273f);color:#fff;padding:52px 0 44px}}
h1{{font-family:"Songti SC",serif;font-size:30px;line-height:1.35;margin:0 0 14px}}
.hero p{{font-size:17px;color:#cfd8e6;max-width:720px;margin:0 0 20px}}
.kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-top:24px}}
.kpi div{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:11px;padding:15px}}
.kpi b{{display:block;font-size:25px;color:var(--accent);font-family:"Songti SC",serif}}
.kpi span{{font-size:13px;color:#b9c4d4}}
h2{{font-family:"Songti SC",serif;font-size:23px;color:var(--navy);margin:44px 0 12px;border-left:4px solid var(--accent);padding-left:12px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;margin:14px 0;font-variant-numeric:tabular-nums}}
th,td{{padding:10px 13px;text-align:left;border-bottom:1px solid #eef1f5;font-size:15px}}
th{{background:#f0f3f8;color:var(--navy)}}
td:nth-child(n+2){{text-align:right}}
th:nth-child(n+2){{text-align:right}}
.tablewrap{{overflow-x:auto}}
.warn{{background:#fff8ec;border-left:4px solid var(--accent);border-radius:0 10px 10px 0;padding:18px 22px;margin:24px 0}}
.warn strong{{color:var(--navy)}}
details{{background:#fff;border:1px solid #e6eaf0;border-radius:9px;padding:13px 17px;margin:9px 0}}
summary{{font-weight:600;cursor:pointer;color:var(--navy)}}
.cta{{background:var(--navy);color:#fff;border-radius:14px;padding:30px;margin:44px 0;text-align:center}}
.cta a{{display:inline-block;background:var(--accent);color:var(--navy);font-weight:700;text-decoration:none;padding:12px 28px;border-radius:9px;margin:8px 6px}}
.cta a.ghost{{background:transparent;color:#fff;border:1px solid #fff}}
.links a{{display:inline-block;margin:4px 14px 4px 0;font-size:14px}}
.dis{{color:var(--mut);font-size:13px;margin:30px 0;padding-top:16px;border-top:1px solid #e0e5ec}}
footer{{background:var(--navy);color:#aab4c2;padding:26px 0;font-size:13px;margin-top:44px}}
footer a{{color:#fff}}
</style>
</head>
<body>

<header><div class="wrap">
  <a href="{BASE}/">文书查 SinoVerdict</a>
  <nav><a href="{BASE}/case-search/">智能检索</a><a href="{BASE}/legal-ai/">AI 助手</a><a href="{BASE}/data/">裁判数据</a><a href="{BASE}/buyers-guide/">采购指南</a><a href="{BASE}/blog/">洞察</a></nav>
</div></header>

<section class="hero"><div class="wrap">
  <h1>全国劳动争议赔偿数据报告</h1>
  <p>基于 {N:,} 份公开生效劳动争议判决的实证统计（{years[0]}–{years[-1]}，覆盖 {n_city:,} 个城市）。
  只呈现能站得住的横截面分布，不做趋势外推、不给诉讼建议。</p>
  <div class="kpi">
    <div><b>{N:,}</b><span>判决样本</span></div>
    <div><b>{money(pctl(comps,50))}</b><span>赔偿金额中位数（元）</span></div>
    <div><b>{money(pctl(comps,25))}–{money(pctl(comps,75))}</b><span>四分位区间（元）</span></div>
    <div><b>{n_city:,}</b><span>覆盖城市</span></div>
  </div>
</div></section>

<main class="wrap">

<div class="warn">
  <strong>⚠️ 读这份报告之前，请先看清两条边界（很重要）</strong>
  <p><strong>一、本样本仅收录已获赔付的判决，不含败诉案件。</strong>
  样本内「全部支持」{won.get('win',0):,} 份、「部分支持」{won.get('partial',0):,} 份，两者合计即 100%。
  所以<strong>本报告的任何比例都不构成胜诉率</strong>，也不能用来判断"这官司能不能打赢"。
  它回答的是另一个问题：<strong>打赢之后，通常拿到多少。</strong></p>
  <p><strong>二、本报告不做逐年趋势。</strong>
  样本在各年份的收录量并不均衡（部分年份样本极少），在采样不均的数据上画趋势线是误导。
  因此我们只做横截面分布——这也是我们对所有对外数据的一贯口径。</p>
</div>

<h2>一、赔偿金额的整体分布</h2>
<p>用中位数与四分位而非平均值——劳动争议赔偿是明显右偏分布，少数高额个案会把平均值拉高到失真。</p>
<div class="tablewrap"><table>
<thead><tr><th>分位</th><th>金额（元）</th><th>含义</th></tr></thead>
<tbody>
{dist_rows}
</tbody></table></div>
<p>同期样本的月工资中位数为 <strong>{money(pctl(sals,50))} 元</strong>（四分位 {money(pctl(sals,25))}–{money(pctl(sals,75))} 元），
可作为理解赔偿基数的参照。</p>

<h2>二、不同解除原因的赔偿差异</h2>
<p><strong>结论先行：用人单位单方解除的赔偿高于协商一致解除，协商一致又高于劳动者主动离职。</strong>
这与经济补偿金/赔偿金的法定计算逻辑方向一致。</p>
<div class="tablewrap"><table>
<thead><tr><th>解除原因</th><th>样本数</th><th>中位数（元）</th><th>P25</th><th>P75</th></tr></thead>
<tbody>
{term_tbl}
</tbody></table></div>

<h2>三、工作年限与赔偿金额</h2>
<p><strong>结论先行：影响显著且单调递增</strong>——这与经济补偿金按工作年限计算的规则一致。</p>
<div class="tablewrap"><table>
<thead><tr><th>工作年限</th><th>样本数</th><th>赔偿中位数（元）</th></tr></thead>
<tbody>
{seg_tbl}
</tbody></table></div>

<h2>四、主要城市横向对比</h2>
<p>取样本量最大的 20 个城市（样本量小的城市统计意义不足，不列入）。城市名可点开查看该城市的完整数据页与真实案例。</p>
<div class="tablewrap"><table>
<thead><tr><th>城市</th><th>样本数</th><th>中位数（元）</th><th>P25</th><th>P75</th></tr></thead>
<tbody>
{city_tbl}
</tbody></table></div>
<p style="font-size:14px;color:var(--mut)">城市间差异同时受当地工资水平、产业结构与裁判尺度影响，
不宜单独用金额高低评价某地"对劳动者更友好"。</p>

<h2>五、方法说明</h2>
<ul>
  <li><strong>数据来源</strong>：中国裁判文书网公开生效裁判文书，当事人个人信息（姓名、身份证号、联系方式、住址）已脱敏。</li>
  <li><strong>样本范围</strong>：{N:,} 份劳动争议判决，判决年份 {years[0]}–{years[-1]}，覆盖 {n_city:,} 个城市。</li>
  <li><strong>统计口径</strong>：金额取判决认定的赔偿数额；使用中位数与四分位，不使用平均值（右偏分布下平均值失真）。</li>
  <li><strong>已知局限</strong>：① 样本仅含获赔判决，存在选择性偏差；② 各年份收录不均，不适合做时间序列分析；③ 未公开或未上网的判决不在样本内。</li>
  <li><strong>可核验性</strong>：各城市数据页保留真实案号，可回溯中国裁判文书网原文。</li>
</ul>

<div class="cta">
  <h3 style="color:#fff;margin-top:0">需要更细的切片，或要把这套数据接进自己的系统？</h3>
  <p style="color:#cfd8e6">按案由、地域、年份、法院层级的定制统计，以及数据接口与私有化部署，都可以谈。</p>
  <a href="{BASE}/buyers-guide/">采购决策指南 →</a>
  <a class="ghost" href="mailto:chenjiaxin@wenshucha.com?subject=%E5%8A%B3%E5%8A%A8%E4%BA%89%E8%AE%AE%E6%95%B0%E6%8D%AE%E5%92%A8%E8%AF%A2">📩 chenjiaxin@wenshucha.com</a>
</div>

<h2>六、常见问题</h2>
{faq_html}

<section class="links">
  <h2>延伸</h2>
  <a href="{BASE}/data/labor/">各城市劳动争议赔偿数据（{len(city_rows)}+ 城市）</a>
  <a href="{BASE}/data/">裁判文书数据规模与字段结构</a>
  <a href="{BASE}/case-search/">裁判文书智能检索系统</a>
  <a href="{BASE}/legal-ai/">AI 法律助手</a>
  <a href="{BASE}/buyers-guide/">采购决策指南</a>
</section>

<div class="dis">
本报告为文书查基于自建裁判文书数据底座的原创统计，数据来源于中国裁判文书网公开生效裁判文书，当事人个人信息已脱敏。
<strong>样本仅含已获赔付的判决，不含败诉案件，任何比例均不代表胜诉率</strong>；样本各年份收录不均，不适合做趋势分析。
本页内容为数据事实呈现，不构成法律意见或诉讼建议，个案请咨询执业律师。转载引用请注明来源 wenshucha.com。
统计生成日期：{today}。
</div>

</main>

<footer><div class="wrap">文书查 SinoVerdict · 深圳星谱网络科技有限公司 · 商务 131-6872-7779 · <a href="mailto:chenjiaxin@wenshucha.com">chenjiaxin@wenshucha.com</a> · <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">粤ICP备2025437990号-2</a></div></footer>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"✓ 报告已生成 {OUT}")
    print(f"  样本 {N:,} · 城市 {n_city:,} · 年份 {years[0]}-{years[-1]}")
    print(f"  中位数 {money(pctl(comps,50))} 元 · 四分位 {money(pctl(comps,25))}-{money(pctl(comps,75))}")
    print(f"  内链城市页 {sum(1 for c,_ in city_rows if slug(c) and (Path.home()/f'wenshucha-site/data/labor/{slug(c)}.html').exists())} 个")


if __name__ == "__main__":
    main()
