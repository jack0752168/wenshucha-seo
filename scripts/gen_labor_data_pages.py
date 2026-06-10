#!/usr/bin/env python3
"""程序化 SEO:用 80k 劳动争议判决数据批量生成「[城市]劳动争议赔偿数据」静态页

每页都是真实数据聚合(样本数/金额分布/胜诉率/解除原因/真实案例),
不是薄门页 —— 别人没这数据抄不了。质量门:城市样本数 ≥ MIN_CASES 才生成。

数据源: ~/peilema/apps/web/lib/tob-bundle.json (cols: doc_id case_no case_title
  court province city reason judgement_date work_years termination_reason
  compensation_judged monthly_salary plaintiff_won body_excerpt)

输出: ~/wenshucha-site/data/labor/<city>.html + index.html
定位: 挂在文书查(数据产品)域名,对 B 端证明数据深度,吃 C 端长尾,内链导流 peilema 计算器

用法: python3 gen_labor_data_pages.py [--min N] [--limit M] [--dry]
"""
import argparse
import html
import json
import re
import statistics
from pathlib import Path
from collections import defaultdict, Counter

try:
    from pypinyin import lazy_pinyin
except ImportError:
    raise SystemExit("需要 pypinyin: pip3 install pypinyin")


def slug_of(city: str) -> str:
    """城市名 → 拼音 slug 做文件名/URL(中文文件名会让服务器 tar/cp 出错)"""
    return "".join(lazy_pinyin(city)).lower()

# 当事人 PII 脱敏:判决书摘录里可能含邮箱/手机号/身份证,展示前抹掉
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"1[3-9]\d{9}")
_IDCARD = re.compile(r"\d{17}[\dXx]")
_BANK = re.compile(r"\d{16,19}")


def redact(text: str) -> str:
    if not text:
        return text
    text = _EMAIL.sub("[邮箱已隐去]", text)
    text = _IDCARD.sub("[证件号已隐去]", text)
    text = _BANK.sub("[卡号已隐去]", text)
    text = _PHONE.sub("[手机号已隐去]", text)
    return text

DATA = Path.home() / "peilema/apps/web/lib/tob-bundle.json"
OUT = Path.home() / "wenshucha-site/data/labor"
BASE = "https://www.wenshucha.com/data/labor"
MIN_CASES = 40  # 质量门:样本数 < 40 不生成(统计无意义 + 防薄页)

# termination_reason 实际取值: layoff / fired / contract_end / mutual / quit
TERM_CN = {
    "layoff": "经济性裁员",
    "fired": "用人单位辞退/解雇",
    "contract_end": "劳动合同到期终止",
    "mutual": "协商一致解除",
    "quit": "劳动者主动/被迫离职",
}
# plaintiff_won 实际只有 win / partial(本数据集只收录获赔判决,无败诉样本)
WON_CN = {"win": "诉请获完全支持", "partial": "诉请获部分支持"}


def pct(values, p):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = int(k)
    if f + 1 < len(s):
        return s[f] + (s[f + 1] - s[f]) * (k - f)
    return s[f]


def yuan(x):
    return f"{x:,.0f}" if x is not None else "—"


def load_rows():
    d = json.loads(DATA.read_text())
    cols = d["cols"]
    idx = {c: i for i, c in enumerate(cols)}
    return d["rows"], idx


def aggregate(rows, idx):
    by_city = defaultdict(list)
    for r in rows:
        city = r[idx["city"]]
        if city:
            by_city[city].append(r)
    return by_city


def city_stats(rows, idx):
    comps = [r[idx["compensation_judged"]] for r in rows
             if r[idx["compensation_judged"]] not in (None, 0)]
    sals = [r[idx["monthly_salary"]] for r in rows
            if r[idx["monthly_salary"]] not in (None, 0)]
    yrs = [r[idx["work_years"]] for r in rows if r[idx["work_years"]] is not None]
    won = Counter(r[idx["plaintiff_won"]] for r in rows if r[idx["plaintiff_won"]])
    term = Counter(r[idx["termination_reason"]] for r in rows if r[idx["termination_reason"]])
    dates = [r[idx["judgement_date"]] for r in rows if r[idx["judgement_date"]]]
    return {
        "n": len(rows),
        "comp_n": len(comps),
        "comp_p25": pct(comps, 25), "comp_med": pct(comps, 50), "comp_p75": pct(comps, 75),
        "comp_max": max(comps) if comps else None,
        "sal_med": pct(sals, 50),
        "yrs_med": statistics.median(yrs) if yrs else None,
        "won": won, "term": term,
        "year_min": min(dates)[:4] if dates else "—",
        "year_max": max(dates)[:4] if dates else "—",
        "province": rows[0][idx["province"]] if rows else "",
    }


def top_cases(rows, idx, k=5):
    """挑赔偿金额最高的几个真实案例做展示(有金额 + 有摘录)"""
    cand = [r for r in rows if r[idx["compensation_judged"]] not in (None, 0)
            and r[idx["body_excerpt"]]]
    cand.sort(key=lambda r: r[idx["compensation_judged"]], reverse=True)
    return cand[:k]


def full_support_rate(won):
    """完全支持占比(样本均为获赔判决,故只在 win/partial 间分布)"""
    total = sum(won.values())
    if not total:
        return None
    return 100 * won.get("win", 0) / total


def render_page(city, st, cases, idx):
    e = html.escape
    prov = st["province"]
    fr = full_support_rate(st["won"])
    fr_str = f"{fr:.0f}%" if fr is not None else "—"
    title = f"{city}劳动争议赔偿金额数据:{st['n']}份获赔判决的金额分布 | 文书查"
    desc = (f"基于{st['n']}份{city}法院劳动争议获赔判决({st['year_min']}–{st['year_max']})的数据分析:"
            f"判赔金额中位数{yuan(st['comp_med'])}元,四分位区间{yuan(st['comp_p25'])}–{yuan(st['comp_p75'])}元。"
            f"按解除原因分类,含真实案例与裁判文书原文。样本为劳动者获支持的判决。")
    slug = slug_of(city)

    # 解除原因分布
    term_rows = "".join(
        f"<tr><td>{e(TERM_CN.get(k, k))}</td><td>{v}</td><td>{100*v/st['n']:.0f}%</td></tr>"
        for k, v in st["term"].most_common()
    )
    # 胜诉结果分布
    won_rows = "".join(
        f"<tr><td>{e(WON_CN.get(k, k))}</td><td>{v}</td><td>{100*v/sum(st['won'].values()):.0f}%</td></tr>"
        for k, v in st["won"].most_common()
    )
    # 真实案例
    case_html = ""
    for r in cases:
        cn = e(str(r[idx["case_no"]]))
        ct = e(str(r[idx["case_title"]]))
        comp = yuan(r[idx["compensation_judged"]])
        tr = TERM_CN.get(r[idx["termination_reason"]], r[idx["termination_reason"]] or "")
        won = WON_CN.get(r[idx["plaintiff_won"]], r[idx["plaintiff_won"]] or "")
        excerpt = e(redact(str(r[idx["body_excerpt"]]))[:160])
        case_html += f"""<div class="case">
      <div class="case-h"><span class="cno">{cn}</span><span class="camt">判赔 {comp} 元</span></div>
      <div class="ct">{ct}</div>
      <div class="cmeta">{e(str(tr))} · {e(str(won))} · 工龄 {r[idx['work_years']]} 年</div>
      <p class="cx">{excerpt}…</p>
    </div>"""

    faq = [
        (f"{city}劳动争议赔偿金一般是多少?",
         f"根据本站收录的{st['comp_n']}份{city}劳动争议获赔判决,判赔金额"
         f"四分位区间为 {yuan(st['comp_p25'])}–{yuan(st['comp_p75'])} 元,中位数 {yuan(st['comp_med'])} 元。"
         f"具体金额取决于工龄、月工资基数与解除合法性,以上为历史判决统计,非个案预测。"),
        (f"{city}这组数据的样本是怎么选的?",
         f"样本为{city}法院劳动争议判决中劳动者诉请获完全或部分支持的 {st['n']} 份判决,"
         f"其中完全支持约 {fr_str}、其余为部分支持。本数据集不含驳回案例,"
         f"所以它反映的是「获赔时金额大致落在什么区间」,不代表整体胜诉率,请勿据此判断打官司一定赢。"),
        ("这些数据来自哪里?可靠吗?",
         "数据来自中国裁判文书网公开判决,经文书查结构化处理。每个案例标注真实案号,"
         "可回链原文核验。本页为信息性数据分析,不构成法律意见。"),
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
    faq_ld = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq],
    }
    dataset_ld = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": f"{city}劳动争议判决数据集",
        "description": desc,
        "creator": {"@type": "Organization", "name": "文书查 SinoVerdict",
                    "url": "https://www.wenshucha.com"},
        "temporalCoverage": f"{st['year_min']}/{st['year_max']}",
        "variableMeasured": ["赔偿金额", "月工资", "工龄", "胜诉结果", "解除原因"],
    }
    bc_ld = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "文书查", "item": "https://www.wenshucha.com/"},
            {"@type": "ListItem", "position": 2, "name": "裁判数据", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 3, "name": f"{city}劳动争议", "item": f"{BASE}/{slug}.html"},
        ],
    }

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="keywords" content="{e(city)}劳动争议赔偿,{e(city)}劳动仲裁赔偿标准,{e(city)}违法解除赔偿金,{e(city)}劳动争议胜诉率,裁判文书数据">
<link rel="canonical" href="{BASE}/{slug}.html">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="article">
<script type="application/ld+json">{json.dumps(dataset_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc_ld, ensure_ascii=False)}</script>
<style>
:root{{--navy:#0e1b2e;--accent:#c8a35a;--bg:#f7f8fb;--ink:#1a2433;--mut:#5a6677}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:860px;margin:0 auto;padding:0 20px}}
header{{background:var(--navy);color:#fff;padding:14px 0}}
header .wrap{{display:flex;justify-content:space-between;align-items:center}}
header a{{color:#fff;text-decoration:none;font-weight:600}}
h1{{font-family:"Songti SC",serif;font-size:28px;line-height:1.3;margin:28px 0 8px}}
.sub{{color:var(--mut);margin-bottom:24px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:24px 0}}
.stat{{background:#fff;border:1px solid #e6eaf0;border-radius:10px;padding:16px}}
.stat .v{{font-size:24px;font-weight:700;color:var(--navy)}}
.stat .l{{color:var(--mut);font-size:13px;margin-top:4px}}
h2{{font-family:"Songti SC",serif;font-size:21px;margin:36px 0 12px;color:var(--navy)}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #eef1f5}}
th{{background:#f0f3f8;color:var(--navy);font-size:14px}}
.case{{background:#fff;border:1px solid #e6eaf0;border-radius:10px;padding:16px;margin:12px 0}}
.case-h{{display:flex;justify-content:space-between;font-size:14px}}
.cno{{color:var(--mut)}}.camt{{color:var(--accent);font-weight:700}}
.ct{{font-weight:600;margin:6px 0}}
.cmeta{{color:var(--mut);font-size:13px}}
.cx{{color:#3a4658;font-size:14px;margin:8px 0 0}}
.cta{{background:var(--navy);color:#fff;border-radius:12px;padding:24px;margin:36px 0;text-align:center}}
.cta a{{display:inline-block;background:var(--accent);color:var(--navy);font-weight:700;text-decoration:none;padding:11px 26px;border-radius:8px;margin:8px 6px}}
.cta a.ghost{{background:transparent;color:#fff;border:1px solid #fff}}
details{{background:#fff;border:1px solid #e6eaf0;border-radius:8px;padding:12px 16px;margin:8px 0}}
summary{{font-weight:600;cursor:pointer;color:var(--navy)}}
.dis{{color:var(--mut);font-size:13px;margin:28px 0;padding-top:16px;border-top:1px solid #e0e5ec}}
footer{{background:var(--navy);color:#aab4c2;padding:24px 0;font-size:13px;margin-top:40px}}
footer a{{color:#fff}}
</style>
</head>
<body>
<header><div class="wrap"><a href="https://www.wenshucha.com/">文书查 SinoVerdict</a><a href="{BASE}/">← 全部裁判数据</a></div></header>
<main class="wrap">
  <h1>{e(city)}劳动争议赔偿金额数据</h1>
  <div class="sub">基于 {st['n']} 份{e(city)}法院劳动争议<b>获赔判决</b>({st['year_min']}–{st['year_max']}) · 数据来自中国裁判文书网</div>

  <div class="stats">
    <div class="stat"><div class="v">{yuan(st['comp_med'])}</div><div class="l">判赔金额中位数(元)</div></div>
    <div class="stat"><div class="v">{yuan(st['comp_p25'])}–{yuan(st['comp_p75'])}</div><div class="l">金额四分位区间(元)</div></div>
    <div class="stat"><div class="v">{fr_str}</div><div class="l">诉请获完全支持占比</div></div>
    <div class="stat"><div class="v">{st['n']}</div><div class="l">获赔判决样本数</div></div>
  </div>

  <div style="background:#fff7e6;border:1px solid #f0d9a0;border-radius:8px;padding:12px 16px;font-size:14px;color:#5a4a25">
    ⓘ 本页样本为{e(city)}劳动争议中<b>劳动者诉请获支持(完全或部分)的判决</b>,不含被驳回的案例。
    因此它回答的是「获赔时金额大致在什么范围」,<b>不代表整体胜诉率</b>,请勿据此认为打官司必赢。
  </div>

  <h2>赔偿金额分布</h2>
  <p>这 {st['comp_n']} 份获赔判决中,判赔金额从低到高的四分位:
  25 分位 <b>{yuan(st['comp_p25'])}</b> 元、中位 <b>{yuan(st['comp_med'])}</b> 元、75 分位 <b>{yuan(st['comp_p75'])}</b> 元,
  最高一例判赔 <b>{yuan(st['comp_max'])}</b> 元。当地样本月工资中位 {yuan(st['sal_med'])} 元,工龄中位 {st['yrs_med']} 年。</p>

  <h2>按解除原因看</h2>
  <table><tr><th>解除原因</th><th>案件数</th><th>占比</th></tr>{term_rows}</table>

  <h2>支持程度分布</h2>
  <table><tr><th>裁判结果</th><th>案件数</th><th>占比</th></tr>{won_rows}</table>

  <h2>真实高额判赔案例</h2>
  {case_html}

  <div class="cta">
    <div style="font-size:18px;font-weight:700;margin-bottom:8px">想知道你自己的情况能赔多少?</div>
    <div style="color:#cdd6e2;font-size:14px">输入工龄、工资、解除原因,1 分钟测算赔偿区间</div>
    <a href="https://peilema.wenshucha.com/">免费测算赔偿 →</a>
    <a class="ghost" href="https://www.wenshucha.com/#api-pricing">企业需要全量数据/API</a>
  </div>

  <h2>常见问题</h2>
  {faq_html}

  <div class="dis">数据来源:中国裁判文书网公开判决,经文书查结构化处理,样本为部分收录(且仅含劳动者获支持的判决)非全量,
  当事人个人信息已脱敏。本页为信息性数据分析,不构成法律意见或个案结果承诺,胜诉与否及金额因案而异,具体维权请咨询执业律师。</div>
</main>
<footer><div class="wrap">文书查 SinoVerdict · 1.5 亿裁判文书数据 · 商务 131-6872-7779 · <a href="mailto:chenjiaxin@wenshucha.com">chenjiaxin@wenshucha.com</a></div></footer>
</body>
</html>"""


def render_index(pages):
    e = html.escape
    rows = ""
    for city, st in sorted(pages, key=lambda x: -x[1]["n"]):
        rows += (f'<tr><td><a href="{slug_of(city)}.html">{e(city)}劳动争议赔偿数据</a></td>'
                 f'<td>{st["province"]}</td><td>{st["n"]}</td>'
                 f'<td>{yuan(st["comp_med"])}</td></tr>')
    title = "全国各城市劳动争议赔偿数据 | 文书查裁判数据"
    desc = f"覆盖 {len(pages)} 个城市的劳动争议判决数据分析,赔偿金额、胜诉率、解除原因分布,数据来自中国裁判文书网。"
    return f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}/">
<style>
body{{margin:0;background:#f7f8fb;color:#1a2433;font:16px/1.7 -apple-system,"PingFang SC",sans-serif}}
.wrap{{max-width:860px;margin:0 auto;padding:0 20px}}
header{{background:#0e1b2e;color:#fff;padding:14px 0}}header a{{color:#fff;text-decoration:none;font-weight:600}}
h1{{font-family:"Songti SC",serif;font-size:28px;margin:28px 0 8px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;margin:20px 0}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #eef1f5}}th{{background:#f0f3f8;color:#0e1b2e}}
a{{color:#0e1b2e}}
</style></head><body>
<header><div class="wrap"><a href="https://www.wenshucha.com/">文书查 SinoVerdict</a></div></header>
<main class="wrap"><h1>全国各城市劳动争议赔偿数据</h1>
<p style="color:#5a6677">基于中国裁判文书网公开判决的结构化分析,覆盖 {len(pages)} 个城市。点击查看各地赔偿金额、胜诉率、解除原因分布。</p>
<table><tr><th>城市</th><th>省份</th><th>样本数</th><th>判赔中位(元)</th></tr>{rows}</table>
</main></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=MIN_CASES)
    ap.add_argument("--limit", type=int, default=0, help="只生成前 N 个城市(0=全部达标的)")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    rows, idx = load_rows()
    by_city = aggregate(rows, idx)

    qualified = []
    for city, crows in by_city.items():
        if len(crows) >= args.min:
            qualified.append((city, crows))
    qualified.sort(key=lambda x: -len(x[1]))
    if args.limit:
        qualified = qualified[: args.limit]

    print(f"达标城市(样本≥{args.min}): {len(qualified)} 个")
    pages_meta = []
    if not args.dry:
        OUT.mkdir(parents=True, exist_ok=True)
    for city, crows in qualified:
        st = city_stats(crows, idx)
        cases = top_cases(crows, idx)
        pages_meta.append((city, st))
        if not args.dry:
            (OUT / f"{slug_of(city)}.html").write_text(render_page(city, st, cases, idx), encoding="utf-8")
    if not args.dry:
        (OUT / "index.html").write_text(render_index(pages_meta), encoding="utf-8")
        print(f"✓ 生成 {len(qualified)} 个城市页 + index.html → {OUT}")
    else:
        for city, st in pages_meta[:20]:
            print(f"  {city}({st['province']}): {st['n']}份, 中位{yuan(st['comp_med'])}元")

    # 输出 sitemap 片段(写文件,供主流程插入 sitemap.xml)
    sm_lines = [f"{BASE}/"] + [f"{BASE}/{slug_of(city)}.html" for city, _ in qualified]
    if not args.dry:
        (OUT / "_sitemap_urls.txt").write_text("\n".join(sm_lines), encoding="utf-8")
    print(f"\n=== {len(sm_lines)} 条 sitemap URL 已写 {OUT}/_sitemap_urls.txt ===")


if __name__ == "__main__":
    main()
