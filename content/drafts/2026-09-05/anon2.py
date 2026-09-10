import urllib.request, urllib.parse, json, re, collections, time
BASE="http://127.0.0.1:3201"
def call(path,params):
    qs=urllib.parse.urlencode({k:v for k,v in params.items() if v not in (None,"",[])})
    with urllib.request.urlopen(f"{BASE}{path}?{qs}",timeout=60) as r:
        d=json.loads(r.read().decode())
    if isinstance(d,dict) and d.get("error"): raise SystemExit("ES error")
    return d
base={"q":"录用通知","cause":"缔约过失","caseType":"民事","lastYears":"3","excludeAnnouncement":"1","size":20}
seen={}; 
for pg in range(1,40):
    d=call("/search",dict(base,page=pg)); cs=d.get("cases") or []
    if not cs: break
    for c in cs: seen[c["case_no"]+"|"+(c.get("case_title") or "")]=c
    time.sleep(0.05)
cases=list(seen.values())
print("去重后样本:",len(cases),"/ total 643")
cc=collections.Counter(c.get("cause","") for c in cases)
print("案由全样本分布:",cc.most_common(5))
ANON=re.compile(r'某|甲公司|乙公司|[A-Z]公司')
YEAR=re.compile(r'[（(](\d{4})[)）]')
by=collections.defaultdict(lambda:[0,0]); tot=[0,0]
for c in cases:
    t=c.get("case_title") or ""
    m=YEAR.search(c.get("case_no") or ""); y=m.group(1) if m else "?"
    a=1 if ANON.search(t) else 0
    by[y][0]+=a; by[y][1]+=1; tot[0]+=a; tot[1]+=n if False else 1
print("\n案号年份 | 脱敏/总 | 脱敏率")
for y in sorted(by):
    a,n=by[y]; print(f"  {y} | {a}/{n} | {a/n*100:.1f}%")
print(f"  合计 | {tot[0]}/{tot[1]} | {tot[0]/tot[1]*100:.1f}%")
# 程序/文书类型/省份 全样本核对
for f in ["procedure","province","court"]:
    print(f"\n--- {f} (全样本) ---", collections.Counter(c.get(f,"") for c in cases).most_common(6))
print("\n样本示例:")
for c in cases[:6]: print("  ",c.get("case_no"),"|",c.get("court"),"|",(c.get("case_title") or "")[:44])
