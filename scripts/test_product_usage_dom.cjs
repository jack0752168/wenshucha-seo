// DOM logic only. This does not claim browser rendering or mobile visual QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8');
class Element {
  constructor(){this.textContent='';this.innerHTML='';this.options=[];this.selectedIndex=0;this.dataset={};this.classList={add(){},toggle(){}};}
  appendChild(item){this.options.push(item);}
  get value(){return this.options[this.selectedIndex]?.value??this.inputValue??'';}
  set value(v){this.inputValue=v;const i=this.options.findIndex(x=>String(x.value)===String(v));if(i>=0)this.selectedIndex=i;}
}
const elements=new Map(),el=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
for(const id of ['snapshot-data','history-data']){
  el(id).textContent=html.match(new RegExp('<script id="'+id+'" type="application/json">([\\s\\S]*?)</script>'))[1];
}
const buttons=['today','7d','30d'].map(window=>Object.assign(new Element(),{dataset:{window}}));
const document={getElementById:el,querySelectorAll:()=>buttons,createElement:()=>new Element()};
const context=vm.createContext({document,console,Date,JSON,Math,String,Object,Boolean});
for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],context);
for(const button of buttons){button.onclick();assert(el('research-time').textContent.includes('實際窗口'));assert(el('mcp-metrics').innerHTML.includes('未知'));assert(el('stages').innerHTML.includes('試用入口操作'));}
assert(el('quality').innerHTML.includes('本次讀取'));assert(el('quality').innerHTML.includes('已知 QA 設定'));
assert(el('comparison').textContent.length>0);
console.log('PASS DOM: 3 windows, unknown money/keys, QA/read-attempt labels, history comparison; visual QA not performed');
