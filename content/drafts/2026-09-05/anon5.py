import urllib.request,urllib.parse,json,re,collections
BASE="http://127.0.0.1:3201"
def call(p):
    qs=urllib.parse.urlencode({k:v for k,v in p.items() if v not in (None,"",[])})
    with urllib.request.urlopen(f"{BASE}/search?{qs}",timeout=90) as r:
        d=json.loads(r.read().decode())
    if isinstance(d,dict) and d.get("error"): raise SystemExit("ES error")
    return d
ANON=re.compile(r'某|甲公司|乙公司|[A-Z]公司')
def run(label,params,maxpg=30):
    seen={}
    for pg in range(1,maxpg+1):
        cs=call(dict(params,size=20,page=pg)).get("cases") or []
        if not cs: break
        for c in cs: seen[c["case_no"]+"|"+(c.get("case_title") or "")]=c
    cases=list(seen.values())
    causes=collections.Counter(c.get("cause","") for c in cases)
    by=collections.defaultdict(lambda:[0,0])
    for c in cases:
        y=(c.get("judgement_date") or "")[:4]
        if not y.isdigit(): continue
        by[y][0]+= 1 if ANON.search(c.get("case_title") or "") else 0
        by[y][1]+=1
    print(f"\n===== {label} =====")
    print("  total:",call(dict(params,size=1)).get("total"),"| 取样:",len(cases),"| 案由:",causes.most_common(3))
    for y in sorted(by):
        a,n=by[y]
        if n>=5: print(f"    {y} | {a}/{n} | {a/n*100:.1f}%")
run("D链 离婚纠纷(婚姻记录)", {"q":"离婚","cause":"离婚纠纷","caseType":"民事","lastYears":"3","excludeAnnouncement":"1"})
