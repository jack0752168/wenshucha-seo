# 知乎问题矿源（2026-08-18 起，Jack：「最大化去找最多的问题，核心是流量最大化」）

## 三个矿口，按价值排序

| 入口 | URL | 为什么值钱 |
|---|---|---|
| **邀请回答** | `zhihu.com/question/waiting?type=invite` | 知乎主动派给我们的，说明账号已进法律话题图谱。**优先级最高** |
| **最新问题** | `zhihu.com/question/waiting?type=new` | 0-2 个回答的新题，抢首答＝永久占坑。**时效性强，当天不答就被别人占了** |
| 为你推荐 | `zhihu.com/question/waiting` | 算法推的，量大但杂 |
| 搜索 | `zhihu.com/search?q=<口语化问法>&type=content` | 补量用，见 ZHIHU-QUESTION-POOL 的搜索词方向 |

## 采集脚本（在已登录的 Chrome 里跑）

```js
const m={};
document.querySelectorAll('a[href*="/question/"]').forEach(a=>{
  const q=(a.href||'').match(/question\/(\d+)/);
  const t=(a.innerText||'').trim();
  if(q&&t.length>6&&!m[q[1]])m[q[1]]=t.slice(0,42);
});
JSON.stringify({n:Object.keys(m).length,list:m})
```

⚠️ **别从列表页读浏览/回答数** —— 卡片 DOM 嵌套不稳，`closest()` 会串到相邻卡片，
实测 20 条全被写成第一条的 36,608/462。**要真数只能逐个开问题页读。**

## 选题优先级（2026-08-18 定）

1. **邀请回答里的产品对口题** —— 例：「类案检索中如何提高检索效率」，这是知乎把我们的
   目标关键词直接送上门
2. **新题抢首答**（回答数 0-2，发布 < 24h）—— 占坑成本最低
3. **真实案例咨询**（回答数 < 10）—— 能用真数据答
4. 工具选型题 —— 只能讲方法，垫底

**永远不碰**：时政/娱乐/股票新股这类高热但与我们无关的（新题列表里一半是这些，直接跳过）。

## 案由轮换

见 PLATFORM-PLAYBOOK「案由轮换」那张基线表。同一案由连答会让数据雷同，
每个案由答 2-3 个就换，并且**每答一个新案由就往基线表加一行** —— 那张横向对比表
是别人给不出的东西（他们只有法条，没有分布）。
