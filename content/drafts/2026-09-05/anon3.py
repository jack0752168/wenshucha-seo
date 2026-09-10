import urllib.request,urllib.parse,json,re,collections,time
BASE="http://127.0.0.1:3201"
def call(p):
    qs=urllib.parse.urlencode({k:v for k,v in p.items() if v not in (None,"",[])})
    with urllib.request.urlopen(f"{BASE}/search?{qs}",timeout=60) as r: return json.loads(r.read().decode())
base={"q":"录用通知","cause":"缔约过失","caseType":"民事","lastYears":"3","excludeAnnouncement":"1","size":20}
seen={}
for pg in range(1,40):
    cs=call(dict(base,page=pg)).get("cases") or []
    if not cs: break
    for c in cs: seen[c["case_no"]+"|"+(c.get("case_title") or "")]=c
cases=list(seen.values())
ANON=re.compile(r'某|甲公司|乙公司|[A-Z]公司')
# 1) 判据误伤自查:被判脱敏的样本随机看
import random; random.seed(7)
hits=[c for c in cases if ANON.search(c.get("case_title") or "")]
print("=== 被判「脱敏」的样本 10 条(人工核) ===")
for c in random.sample(hits,10): print("  ",c.get("case_no"),"|",re.sub(r'<[^>]+>','',c.get("case_title") or "")[:50])
miss=[c for c in cases if not ANON.search(c.get("case_title") or "")]
print("\n=== 被判「实名」的样本 10 条 ===")
for c in random.sample(miss,10): print("  ",c.get("case_no"),"|",re.sub(r'<[^>]+>','',c.get("case_title") or "")[:50])
# 2) 裁判日期口径交叉验证
by=collections.defaultdict(lambda:[0,0])
nodate=0
for c in cases:
    jd=(c.get("judgement_date") or "")[:4]
    if not jd.isdigit(): nodate+=1; continue
    a=1 if ANON.search(c.get("case_title") or "") else 0
    by[jd][0]+=a; by[jd][1]+=1
print(f"\n=== 口径二:按 judgement_date(裁判日期) === 无日期 {nodate} 条")
for y in sorted(by):
    a,n=by[y]; print(f"  {y} | {a}/{n} | {a/n*100:.1f}%")
