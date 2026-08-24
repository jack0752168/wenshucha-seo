# 三平台分发作战手册（百家号 / 知乎 / 搜狐号）

> 每次跑分发任务前必读。方法论依据：`~/.claude/skills/baiyang-cn-seo-playbook/`
> 定位纲领：记忆 `core_wenshucha_product_positioning`

---

## 一、定位（凌驾一切，写偏了整篇作废）

**卖的是产品**：裁判文书智能检索系统 + AI 法律助手。对标 **Alpha、北大法宝**。
**读者是「用工具办案的人」**：律师、检察官、法官助理 —— **不是买服务器的 IT。**

内容配比：
- **80% 办案人视角** —— 类案怎么撈得准、检索报告怎么出、AI 哪些活能交出去
- **15% 选型视角** —— 不贬低竞品，用「该问哪几个问题」表达
- **5% 部署采购** —— 辅线，服务决策链上的 IT/采购角色

> ⚠️ 站上 41 篇存量长文有 20 篇是 IT/部署向的，**不要直接搬**。要用它们的技术底料，
> 重写成办案人能看懂、用得上的角度。

### 选题唯一来源：关键词台账（2026-07-29 白杨化重构）

**`~/wenshucha-seo/content/keyword-ledger.md`** —— 白杨五类词 + 信源型。
写文前查台账挑 ⬜ 待写的词；发完把状态改 ✅ 附 article_id。台账没合适词才自拟，自拟后先补进台账。

### 选题两类（2026-07-26 AI 引用诊断后加，交替发）

**A. 办案人视角（主力，占多数）** —— 类案怎么撈准、检索报告怎么出、AI 哪些活能交出去。建专业信任。

**B. 信源型（每周 ≥1 篇，专为进 AI 引用池）** —— 2026-07-26 秘塔实测：AI 被问「裁判文书数据库有哪些/类案检索用哪个好」时，引用的是**「检索工具清单 / 对比 / 数据库介绍」类聚合文**（见记忆 [[project_wenshucha_geo_baseline]]），而文书查 0 次被提及。所以要定期发这类形态，让 AI 下次能把我们列进去：
- 《律所类案检索：主流裁判文书数据库怎么选（含 XX 对比）》
- 《文书查：1.6 亿裁判文书检索数据库能力介绍》
- 《免费 vs 付费裁判文书检索平台，各自适合什么场景》
> ⚠️ **诚实铁律**：客观列举竞品**不贬低**；文书查只用真实事实（1.6 亿 / 五大类 / 可核验 / 免费试用 / 私有化），**禁编客户数、评分、排名**。为 GEO 夸大 = 白杨说的「投毒」，一次毁品牌。

---

## 二、养号期纪律（第 1–2 周，铁律）

**全文零链接、零电话、零邮箱、零「联系我们」。**

白杨的原话案例就是知乎：新号没养号直接留联系方式 → 文章被删。
第 3 周起再逐步在文末加 wenshucha.com 回链。

**同时禁止**：刷阅读量、堆关键词、为 GEO 编造数字（「GEO 投毒」）。

---

## 三、平台改写规则（同一话题树，改四件事：标题/开头/词密度/标签）

### 百家号（吃百度权重，主力）
| 项 | 规则 |
|---|---|
| 标题 | **关键词前置**，直白。「XX怎么做」「XX选型」句式 |
| 开头 | 首段直接点题（搜索摘要取这段） |
| 词密度 | **2%–8%**（比公众号宽松） |
| 长度 | 2000–4000 字 |
| 加分 | 引用权威数据、给可执行清单 |

## ★ 知乎：已攻破，可全自动到【发布】（2026-08-14 实测）★

**七月记的「知乎 SPA 驱动不了」是错的，已推翻。** 19 篇积压稿从今天起可以自动发。

### 编辑器是 Draft.js —— 这是全部难点的根源

`document.querySelector('[contenteditable=true]').className` = `public-DraftEditor-content`，
父容器 `DraftEditor-editorContainer`。Draft.js 维护 **immutable EditorState**，DOM 只是渲染结果。

⚠️ **`execCommand('insertText')` 对它无效**——DOM 看起来写进去了、innerText 读回也对，
但 Draft 的 model 没更新，保存时以 model 为准。
**2026-08-14 实测踩坑**：用 execCommand 灌 28 段，innerText 读回 2034 字、段数 28，
结果发布出去线上只有 **1 段 92 字**（只剩最后一次 insertText 那段）。差点当成功交付。

### ✅ 破法：paste 事件注入

```js
const b=[...document.querySelectorAll('[contenteditable=true]')][0];
b.focus();
const r=document.createRange(); r.selectNodeContents(b);       // 选中全部现有内容
const s=getSelection(); s.removeAllRanges(); s.addRange(r);
document.dispatchEvent(new Event('selectionchange'));           // ★ 让 Draft 同步 SelectionState
const dt=new DataTransfer();
dt.setData('text/plain', paragraphs.join('\n'));                // \n 会被 Draft 切成独立 block
b.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));
```

- `selectNodeContents` + 手动派发 `selectionchange` 是关键，少了这步 paste 会插在开头而不是替换
- paste 替换选区 → 一次调用同时完成「清空旧内容」和「灌新内容」
- `\n` 分隔 → Draft.js 自动切成多个 block，**不需要 insertParagraph**

### 标题是 textarea，不是 contenteditable

```js
const ta=document.querySelector('textarea');
const set=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
ta.focus(); set.call(ta,TITLE);
ta.dispatchEvent(new Event('input',{bubbles:true}));
ta.dispatchEvent(new Event('change',{bubbles:true}));
```

### 🚨 判据（这条最重要，2026-08-14 被骗过一次）

| 判据 | 可信吗 |
|---|---|
| `b.innerText` 的长度/段数 | ❌ **会骗人**，DOM 写进去了不代表 Draft model 有 |
| `b.querySelectorAll('[data-block="true"]').length` | ✅ Draft 的真实 block 数 |
| 底部「字数：N」 | ⚠️ **有延迟**，刚灌完仍显示旧值；**刷新页面后才准** |
| **重载 `/edit` 页再读 block 数** | ✅✅ **最硬**，直接验证服务端存了什么 |
| 线上文章页 `.Post-RichTextContainer` 的 `p` 数 | ✅✅ 终极判据 |

**发布前必须重载 /edit 复核一次**，别信刚灌完的读数。

### 🔴 2026-08-18 三条新坑（文章区，一轮里全踩了）

**① paste 注入后不能立刻 navigate 走 —— 草稿根本没落库。**
灌完 29 段、`[data-block]` 读回 29，我只等 4 秒就导航去重载复核，
结果服务端只剩 **1 block / 0 字**（标题倒是存住了）。
Draft 的 model 有内容 ≠ 服务端有内容，中间还隔着一次自动保存。
**破法：paste 后等到页面出现「草稿保存中」并再多等，总计 ≥30 秒再离开。**
→ 这条把「重载 /edit 复核」的价值坐实了：不复核这次就会把空文章发出去。

**② 「发布」按钮旁边还有个「发布设置」，`/发布/` 正则会先命中它。**
`filter(b=>/发布/.test(b.innerText))` 返回 `["发布设置","发布"]`，取 `[0]` 点了个寂寞。
**必须用 `innerText.replace(/[\u200b\n]/g,'').trim()==='发布'` 精确等值取。**
（按钮文字里有零宽空格 `\u200b`，不 strip 会匹配失败。）

**③ 点了发布、toast 出「发布中」、按钮消失 —— 仍可能回落成草稿。**
第一次这样之后重载 /edit，底部状态明明白白写着「**3 分钟前 · 草稿**」，按钮还是「发布」。
**文章区的好处是状态可读**，不像回答区只能猜：
| 读到什么 | 含义 |
|---|---|
| 底部「N 分钟前 · 草稿」+ 按钮是「发布」 | 没发出去，可以安全再点 |
| 按钮变「更新」 | 已发布过 |
| `/p/{id}` 跳知乎首页 | 尚未公开（可能在队列，也可能真没发） |
**同一个 `/p/{id}` 重复点发布只会更新同一篇，不会产生副本** —— 这点和回答区相反，
所以文章区在「状态明确显示为草稿」时是可以再点的，不受回答区那条「绝不重试」约束。

**④ 当日第 5 篇之后开始进队列（本次观察，待复现）。**
08-18 早间连发 4 篇文章都是秒发、URL 立刻可访问；
11:40 之后发的第 5、6、7 篇全部卡「发布中…」，20 分钟后 `/p/{id}` 仍跳首页。
与 08-17 回答区「第一条秒发、后续进队列」是同一形状，疑似账号级当日频次节流。
**处置照旧：不重试，次日复核。** 但排程上值得考虑：知乎单日超过 4 篇之后，
发出去的当轮基本验不到结果，报告里就该直接写 ⏳ 而不是耗回合去等。

### 🔴 2026-08-18（14:50 实测）知乎文章区有「当日公开约 2 篇」的硬墙 —— 本节推翻同日早些时候的「队列会自行落地」

**现象**：当天提交 9 篇文章，**只有最早的 2 篇真正公开**（11 点前后），此后每一篇点发布都是
按钮变「发布中...」→ 永远不变，底部状态恒为「刚刚 · 草稿」，无弹框、无 toast、无报错。

**硬证据（三条，缺一不可）**
1. `/creator/manage/creation/article` 今日只有 2 条「发布于 N 小时前」；
   `/creator/manage/creation/draft?type=article` 里 **9 篇文章草稿 = 当日 11:40 之后提交的全部**。
2. 直接开 `zhuanlan.zhihu.com/p/{id}` → **重定向到知乎首页**，3 小时后仍如此。
3. 给 `fetch` 和 `XMLHttpRequest` 都挂拦截器后再点发布，**publish/articles 相关请求一条都没发**
   —— 卡在前端提交之前，既不是服务端拒绝，也不是网络问题。

**所以这两条要改掉：**
- ❌ 旧：「当日第 5 篇之后进队列，20 分钟后 /p/{id} 仍跳首页，处置照旧不重试、次日复核。」
  ✅ 新：**那不是队列，是没发出去。** 次日必须**重发**（开 /edit 点发布），坐等不会自己好。
- ❌ 旧：「按钮是『发布』+ 状态『草稿』→ 可以安全再点。」
  ✅ 补：可以点（确实不产生副本），但**撞到这堵墙时重点也没用**——实测连点两次，行为完全一致。
  重点一次确认即可，别耗回合。

**排程含义（重要）**：不要再按「百家号发几篇，知乎就同步几篇」执行 ——
**当日超过约 2 篇之后写的知乎稿是白写**。建议每天知乎只排 2 篇：
1 篇与当日百家号同话题、1 篇积压清库，把有限配额用在最该占的话题上。
（阈值是本次单日观测，是否恰好为 2、是否随等级/创作分变化，需再观测几天确认。）

**🔄 2026-08-18 19:35 复测修正阈值：当日公开天花板实测是 5 篇，不是 2 篇。**
同日 19:35 用创作中心**双向**核对（比早些时候只看一侧更硬）：
- `/creator/manage/creation/article` 已发布列表，今日只有 5 条（11 小时前 ×3、8 小时前 ×2），
  id = 2072946830464250638 / 2072947819858622112 / 2072948844942443328 /
  2072995757611921868 / 2072997167141335724，其余全是 08-14 的。
- `/creator/manage/creation/draft?type=article` 草稿箱(9)、文章草稿 9 条，
  id 与当日 11:40 之后提交的 9 篇**一一对应**，且摘要显示**正文完整在库**。
→ 所以 14:50 那次记的「约 2 篇」是**观测时点太早**造成的低估（当时后面 3 篇还没落地）。
  **当日公开配额按 5 篇用**，但仍远低于百家号的 10 篇。
→ **排程含义不变且更明确**：知乎每天只排 2 篇（1 篇同话题 + 1 篇积压清库）仍是对的，
  因为 5 是天花板不是目标，贴着天花板发＝把后面的稿子推进草稿箱白写。
→ **判定当日还能不能发，别数 PUBLISH-LOG，直接读创作中心两个页面**：
  已发布列表今日条数 ≥5 就停手，写好的稿留到次日。


**好消息**：卡住的稿子完整躺在草稿箱，`[data-block]` 数与提交时一致，重发不用重灌正文。

### 🚨 2026-08-18 修正：三条旧结论被推翻

**① 浏览器归属（此前一直漏记，害我今天绕了半小时）**
Claude 的 Browser pane（`mcp__Claude_Browser__*`）是**全新 profile，没有知乎 session**，
点「写回答」只弹登录框、`contenteditable` 恒 0，看起来像「五连派发失效」其实是没登录。
**知乎必须走 `claude-in-chrome`（Jack 真实 Chrome，已登录）。**

**② 「已提交但不可见」是知乎的一个真实状态**
2026-08-17 Q366531183 那篇点发布后卡「发布中…」，08-18 早上查：问题页 12 个回答、
个人主页回答数 3，**据此判「服务端没收到」→ 重发**。
结果发完查 API：该问题下我们**只有 1 条**，id=2073003881316074829，
**内容是 08-17 的旧稿**，created_time≈08-18 11:10。
→ 08-17 那篇**提交成功了**，只是一直未公开未计数，**今天才转正**，created 记的是转正时间。

| 想判断 | 能用 | 不能用 |
|---|---|---|
| 已公开入库 | 个人主页回答数↑、问题页回答数↑ | —— |
| **是否提交过** | **只能等 ≥48h 再看** | ❌ 计数 ❌ 创作中心 ❌ 问题页 |

**重发前提改成：距上次发布 ≥48 小时且仍不可见。** 计数没涨 ≠ 没提交。

**③ `/api/v4/questions/{qid}/answers` 会限流**
同一参数第一次返回 `total: 13`，40 秒后再调返回 `total: 0`。**别拿它做轮询判据。**

**④ CSP 挡 localhost**：想起本地 http server 喂正文给页面 fetch，会被知乎 CSP 挂住，
并触发 CDP `Runtime.evaluate` 45s 超时。正文只能**内联注入**（中文原文比 base64 省一半 context）。
`pbcopy` 也不通——Bash 沙箱访问不到系统剪贴板。

### 回答区发布链路（2026-08-17 打通，与文章区共用 Draft.js）

**战术定位**：文章区是「自己开话题」，回答区是「接住已有搜索流量」。
知乎问题页本身在百度有排名，43 万浏览的老问题＝现成的流量池，比新开文章快得多。

```
navigate https://www.zhihu.com/question/{qid}
  → ⚠️ 物理 left_click「写回答」不生效（实测点两个位置都没反应，contenteditable 恒 0）
     破法＝五连事件派发：
     ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t=>
       btn.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window})))
  → 等 9s，编辑器出现（class = public-DraftEditor-content，与文章区同一个 Draft.js）
  → 回答区**没有标题栏**，只灌正文：paste 注入法（见上「破法」段），完全复用
  → 验 [data-block="true"] 数 == 源段数
  → 「发布回答」按钮同样用五连派发（物理点击同样不生效）
  → 成功判据：URL 变成 /question/{qid}/answer/{aid} 且 contenteditable 归零
```

### 选题：怎么挑问题

```
navigate https://www.zhihu.com/search?q=<词>&type=content
  → 抓 a[href*="/question/"] 去重，得候选 qid
  → 逐个开问题页读「关注者 N 被浏览 M」和回答数
  → 优先级 = 浏览量大 × 现有回答质量低（都在列清单/复制粘贴 = 有空位）
```

**已建候选池（2026-08-17 实测数据）**：

| qid | 问题 | 关注 | 浏览 | 回答 | 状态 |
|---|---|---|---|---|---|
| 32261544 | 有哪些好用的法律案例检索工具？ | 475 | **435,801** | 31 | ✅ 已答 |
| 309992362 | 法律案例裁判文书查询检索系统哪个最强最方便？ | — | — | — | ⬜ |
| 274245873 | 有什么好的法律检索工具？ | — | — | — | ⬜ |
| 533808857 | 律师怎么样进行类案检索呢？收费的方式除外？ | — | — | — | ⬜ |
| 656206850 | 刚做实习律师，带教律师让我做类案检索…推荐吗？ | 9 | 1,978 | 5 | ⬜ |
| 661022657 | 给法官提供类似判例，法官不参考怎么办？ | — | — | — | ⬜ 我们有对口百家号文 |
| 50301460 | 有哪些检索中国法律条例的网络工具/网址/app？ | — | — | — | ⬜ |
| 410923439 | 什么叫类案检索？ | — | — | — | ⬜ |

### ⚠️ 「发布中…」卡住 ≠ 失败（2026-08-17 误判，08-18 更正）

实测：Q32261544 发布成功后 6 分钟发第二个回答，「发布回答」按钮变成「**发布中…**」
并卡住超 90 秒、无报错。我去创作中心查显示「共 1 条」，**据此误判为限速失败**。

**08-18 在个人主页复核：两条回答都在，第二条其实发成功了。**

**正确判据（按可靠性排序）**：
1. ✅✅ **个人主页** `zhihu.com/people/{id}/answers` —— 最硬，所见即所得
2. ✅ 直接打开 `/question/{qid}/answer/{aid}` 看内容在不在
3. ❌ **创作中心的「共 N 条」计数有延迟，不能当判据** —— 就是它骗了我一次

### ⏳ 已观察到的模式：第一条秒发，后续进队列延迟入库（2026-08-17/18 两次复现）

| 序 | 问题 | 发布时表现 | 最终结果 |
|---|---|---|---|
| 1 | Q32261544 | 秒发，URL 立刻跳 /answer/{aid} | ✅ 立即成功 |
| 2 | Q309992362 | 卡「发布中…」90s 无报错 | ✅ **延迟成功**（次日复核已在） |
| 3 | Q656206850 | 卡「发布中…」40s+ | ⏳ 观察中 |

**判读：这不是失败，是延迟入库。** 新号当次会话里第一条能秒发，后续的进审核/写入队列。

**所以规则是：**
1. 按钮卡在「发布中…」→ **绝不重试**（重试会产生重复回答，比延迟难收拾得多）
2. 当场不确认结果，**次日去个人主页 `zhihu.com/people/{id}/answers` 复核**
3. 判据优先级：个人主页 ✅✅ > 直接开 /question/{qid}/answer/{aid} ✅ >
   创作中心「共 N 条」❌（有延迟，2026-08-17 就是它骗了我一次）
4. 排程任务里：发完记一行 `⏳待复核`，第二天开工时先回头确认，确认了再改成 ✅

### ⚠️ 回答区不自动存草稿

文章区（zhuanlan）会自动存草稿，**回答区不会**。发布卡住后重载页面，编辑器全空，
32 段内容全丢。

**所以纪律是：稿子必须先写成 md 落盘，再灌进编辑器。** 绝不在编辑器里直接创作。
落盘的稿子用 `scripts/zhihu_extract.py` 解析成段落数组，用 `===BODY===` 或
`<!--BODY-START-->` 界标包住正文。

### 🚨 回答区的红线（比文章区严，知乎对软广零容忍）

1. **开头必须写利益披露**（「我自己在做这行（文书查）」），不披露＝被当软广举报
2. **不做排名、不点名说谁不好** —— 只给用户能自己跑的验证方法
3. **必须真正回答问题**，我们的产品信息只能作为「可被同一套方法验证的对象之一」出现
4. **末尾必须有「我做不到的部分」** —— 这是知乎调性，也是我们一贯的诚实红线
5. 前面答主已经写全的内容不重复，**找他们没覆盖的角度**（32261544 的空位就是「怎么判断」）

---

### 发布链路

```
navigate https://zhuanlan.zhihu.com/write        → 自动建草稿，URL 变 /p/<id>/edit
  → textarea 写标题（native setter + input/change）
  → paste 注入正文（上面那段）
  → 等 4s，读 [data-block] 数自验
  → 重载 /edit，复核 block 数与「字数」
  → 点「发布」(右下角) → 面板展开，需向下滚 15 格才看得到
  → 「文章话题」知乎会自动推荐填好（本次自动填了「检察院」），不用手动加
  → 封面可选，跳过
  → 再点一次「发布」→ URL 去掉 /edit = 已发布
  → 打开 /p/<id> 复核 .Post-RichTextContainer 的 p 数
```

### 🚨 「发布」按钮要点两次，且两次之间必须留间隔（2026-08-18 实测，踩了两次）

第一次点击**永远不生效**（推测是先把编辑器 blur / 触发一次保存），按钮文字不变、仍是「草稿」。
第二次点击才会变成「**发布中...**」。

⚠️ 但**两次点击不能连着发**——连点两下（中间无停顿）会互相抵消，按钮闪一下又变回「发布」，
2026-08-18 这样连点，两篇各白丢一轮。**正确节奏 = 点一次 → 截图确认 → 再点一次 → 截图看到「发布中...」**。

**判据只认线上页**：`/p/<id>` 打开后 `.Post-RichTextContainer` 的 p 数对得上才算发出去。
未发布的草稿访问 `/p/<id>` 会**跳到 zhihu.com 首页**（不是 404），这是最快的失败判据。
点完后 URL 仍停在 `/edit` 属正常，别拿它当成功或失败的依据。

- 已发布的文章再编辑，按钮文字变「**更新**」，流程相同
- 无需封面、无需实名认证、无需付费

---

### 知乎写作规范（吃百度 + AI 引用，问答体）
| 项 | 规则 |
|---|---|
| 标题 | **用户真会打出来的问句** |
| 开头 | **前 50 字直接给结论** |
| 风格 | 分点、有判断标准、**必须承认局限** —— 知乎读者最反感把话说满 |
| 禁忌 | 硬广、「我们的产品」、新号抢热门问题下的回答 |
| 形式 | 养号期先发「文章」，两周后再进回答区 |

### 搜狐号（AI 引用权重最高，⏸ 待实名认证解锁）
| 项 | 规则 |
|---|---|
| 标题 | 资讯体 |
| 重点 | **优先铺原创数据报告** —— 白杨：原创调研数据是 AI 最想引用的形态 |
| 状态 | 实名认证未完成，暂不能发文 |

---

## 四、发布链路（2026-07-22 实测确认）

### 发布节奏守门（2026-08-14 纠偏）

- 新号每天最多 **3 篇**，只做裁判文书检索／法律 AI 的产品邻近高意图词；没有合格词宁可少发。
- 两篇之间至少 3 小时。每日自动任务只运行一次时，第 1 篇立即发布，第 2、3 篇只有在能验证
  百家号「定时发布」状态时才排到后续黄金时段；否则存草稿，禁止同一轮连发。
- 停止「每天多发 1 篇撞配额墙」。过审只说明平台没拦，不代表搜索分发，更不代表获客。
- 从 3 篇扩到 4 篇必须同时满足：最近 7 天至少一半新文在 48 小时内获得可验证百度展现或
  自然阅读 ≥20，信用分无下降、未通过为 0；每周最多调整一次。

### ✅ 百家号：可全自动到【发布】（2026-07-22 实测跑通一整篇）

**关键突破：封面不必上传。** 「选择封面」点开是**页内弹框**，三个标签页：
```
正文/本地上传   ← ⛔ 这个才是系统选档窗口,驱动不了,别在这死磕
AI封图         ← ✅ 有「根据全文智能生成封面」,纯页内,自动出 4 张候选
免费正版图库    ← 页内,但法律类关键词常无结果
```
**走 AI封图,全程不碰文件系统。** 之前误判「封面必须上传」害得只能停在草稿,
剪贴板粘贴/工具栏图片按钮/一键填写全试过全撞墙——因为都在「上传」这条路上。

**完整链路：**
```
1. navigate https://baijiahao.baidu.com/builder/rc/edit?type=news
2. 点标题区(约 560,217) 输标题
3. 点正文区(约 560,349) 输正文 —— ⚠️ 标题超一行会换行,正文区被顶到 y≈349;
   写死 310 会落回标题区、正文静默丢失(字数仍 0)。先打两字探针 + 截图确认再灌全文
4. 点「存草稿」(约 615,757) → URL 出 article_id=xxx,记下
5. 滚到「设置封面」,点「选择封面」(用 JS 定位:文本==='选择封面' 的元素,
   scrollIntoView 后取坐标 —— 页面很长,写死坐标会点空)
   ⚠️ **坐标要换算,但系数不固定**:截图尺寸 ÷ viewport 尺寸 = 换算系数,
      **每次都要用 JS 现读 `window.innerWidth/innerHeight` 算**,别照抄旧值。
      实测过 1.05(1512×791 / 1440×753)和 1.167(1400×844 / 1200×723)两种,随窗口大小变。
   ⚠️ 点「选择封面」四个字本身会落空,要点**封面框内的图片图标**
      (2026-07-29 实测:文字上方约 32px 才生效;只上移 17px 到框几何中心那次点空了)
6. 弹框首次打开是收起态,wait 6 秒展开后再点「AI封图」标签
   ⚠️ **收起态下点「根据全文智能生成封面」是无效的**(2026-08-18 实测):收起态那行链接在
      截图上看得见、点下去没反应,要等弹框长到全屏尺寸(约 1000×680)后**重新用 JS 取一次坐标**
      再点,才会真正触发生成。别照抄收起态时算出来的坐标。
7. 点「根据全文智能生成封面」→ 等 20 秒左右(生成慢,wait 上限 10 秒,分两次等)
8. 生成 3-4 张后默认选中第 1 张,点右下「确定 (N)」
   ⚠️ **若弹出「封面裁剪处理中,请稍后再点击"确定"」→ 别重复点确定**(2026-07-31 实测:
      等 6s/8s/20s 重点三次全被同一提示拦住,提示还从灰色信息态变红色错误态,
      说明是那张的裁剪任务卡死,不是没好)。**判据:主区有没有出现带裁剪框的编辑视图** ——
      没有就是没跑起来。**破法:直接点另一张候选**,主区立刻出裁剪框、右侧预览同步更新,
      再点「确定」一次通过。候选格里偶有空白占位(该张生成失败)属常见,不影响其他张。
9. 跑完三道闸门 → 点「发布」(约 922,757)
10. 出现「文章发布成功 / 提交成功,正在审核中」即完成
```
**注意：** 弹框有淡入淡出动画,点太快会落空。每步之间 wait 5-8 秒。
**⚠️ 别用一张截图就判「点空」(2026-07-30 教训):** 点封面框后 wait 7 秒截图仍显示弹框未开,
差点重点一遍;用 JS 查 DOM 发现「AI封图」「免费正版图库」标签已存在——弹框其实开了,
只是截图拍在淡入动画完成前。**判定弹框开没开一律查 DOM 文本,不看截图**(重点一次可能反而关掉它)。
另:第 5 步「封面框图片图标在文字上方约 32px」已两次复现(07-29 / 07-30),可当稳定规律用;
但第 3 步的正文区 y 值随标题行数变(07-29 是 349、07-30 两行标题时是 388),仍必须探针确认。
**字数：** 起稿直接按 3500 字目标写。写到 4800 再回头砍要多花三轮,且容易砍出逻辑断口。

**🔴 2026-08-21 封面链路两处大改(旧步骤 5-8 已部分作废,先读这段再照旧文走):**

**A. 根因新形态:tab 不可见 → 弹框动画永不启动 → 卡死在 opacity 0。**
点开「选择封面」后 `.cheetah-modal` 已存在、尺寸已是 980×671(展开态),但 class 停在
`cheetah-zoom-appear-prepare`、`opacity` **恒为 0 达 17 秒不变**,且「AI封面」等标签文本
**根本不在 DOM 里**(内容未渲染)。旧手册教的「等 opacity==='1'」在这种情况下会等到天荒地老。
**判据**:`document.visibilityState === 'hidden'`。Chrome 对隐藏 tab 节流 rAF,
CSS 进入动画**不是在跑而是压根没开始**。关掉其他 tab 让它变前台**不一定管用**
(2026-08-21 实测关掉后 visibilityState 仍是 hidden —— 整个 Chrome 窗口在后台)。
**破法(实测一次通过):**
```js
const m=document.querySelector('.cheetah-modal');
m.classList.remove('cheetah-zoom-appear-prepare','cheetah-zoom-appear');
m.classList.add('cheetah-zoom-appear-active');
m.style.opacity='1';
document.querySelectorAll('.cheetah-modal-mask').forEach(x=>{x.style.opacity='1';
  x.classList.remove('cheetah-fade-appear-prepare','cheetah-fade-appear');});
```
强制推进后弹框内容立刻渲染。**后续每开一个新弹框/新面板都要再推一次**,通用写法:
```js
document.querySelectorAll('[class*="-appear-prepare"],[class*="-enter-prepare"]').forEach(x=>{
  x.className=x.className.replace(/-appear-prepare|-enter-prepare/g,'-appear-active'); x.style.opacity='1';});
```
**⚠️ 代价:强制改 class 后截图里弹框是空的**(合成层没绘制),但 DOM 完全是活的。
所以这条路上**一切判据只能读 DOM,截图彻底失效**;点击也要用 JS `click()` 或派发
pointerdown/mousedown/pointerup/mouseup/click 五连,不能用坐标点。

**B. 标签叫「AI封面」不叫「AI封图」,且生成流程已改版。**
旧手册的 `includes('AI封图')` 永远返 false —— 平台文案是「**AI封面**」。
「根据全文智能生成封面」那个单链接**已不存在**,现在是三段式:
```
点「AI封面」标签
 → 点「从正文总结」(自动填好「封面描述」长文本 + 「封面文字」≤15字,2026-08-21 实测填得很切题)
 → 点「生成」
 → 等待,文案依次是「整理封面信息中...」→「生成封面中...」→ 出现「重新生成」即完成(实测约 20-25 秒)
 → ⚠️ **不再默认选中第 1 张!** 必须自己点一张候选
 → 点「确定 (1)」
```
⚠️ **等待循环的判据别写漏**:文案是「生成封面**中**...」,只 `includes('生成中')` 匹配不上,
会误判成已完成而提前退出(08-21 踩过)。正则用 `/整理封面信息中|生成封面中|生成中/`。
⚠️ **「选中了没有」的判据**:候选容器 class 从 `wrap selectBorder autoSize` 变成
`wrap **selected** selectBorder autoSize`,同时标签页文字变「AI封面**(1)**」、封面预览区 img 数 0→1。
`selectBorder` 只是可选边框样式类,**光看它会误判成已选中**。
生成图的辨认法:modal 内 `img` 宽度 >200px 的才是候选大图(336×252),70×52 的是「热门模板」缩略图。

**⚠️ 2026-08-03 两条硬判据(都栽过,别再踩):**
1. **正文在 iframe 里,`document.body` 读不到。** 探针打进去了、截图明明看得见,但
   `document.body.innerText.includes('探针')` 返回 false、底栏「字数」也还显示 0
   ——**这不是输入丢失**。正确查法:
   `document.querySelectorAll('iframe')[0].contentDocument.body.innerText`
   (共 3 个 iframe,正文是第 0 个)。灌完全文也用它验长度/首尾/有无链接。
2. **判弹框开没开,「文本存在」还不够硬。** 手册原说"查 DOM 文本不看截图",但 08-03 实测:
   `AI封图`/`免费正版图库` 文本都已在 DOM,弹框却还没画出来(截图全空、rect 还在跳)。
   **真判据**:`document.querySelector('.cheetah-modal')` 的 class 含
   `cheetah-zoom-appear-active` 且 `opacity<1` = 进入动画还在跑;等 `opacity==='1'`
   且元素 rect 两次读数稳定,再点。别在动画中途点(会点空,或反而关掉弹框)。

**⚠️ 2026-08-04 新坑(耗了 3 个回合):弹框永远 opacity:0,不是点空,是分页在后台被节流。**
判据:`document.visibilityState === 'hidden'`(claude-in-chrome 驱动时分页常不在前台)。
此时 rc-motion 的入场动画靠 rAF 推进,后台分页 rAF 被暂停 → 弹框 DOM 挂上了、rect 正常、
`AI封图` 文本也在,但 class 卡在 `cheetah-zoom-appear-active`、`opacity` 恒为 `0`,截图全空。
**⛔ 别重点封面框**(会把弹框关掉)。**破法 = 手动补派发一次 animationend 让 rc-motion 落定:**
```js
document.querySelector('.cheetah-modal')
  .dispatchEvent(new AnimationEvent('animationend',{bubbles:true}))
```
派发完 `opacity` 立刻变 `1`,截图能看见,后续「AI封图」标签 / 生成 / 确定全部照常一次通过。
→ 于是 08-03 那条「真判据是等 opacity==='1'」要补一句:**等不到就是被节流了,派发事件,别干等**。

**✅ 2026-08-05 通用破法(比派发事件更根本,今后首选,进编辑器就先打):**
08-04 的「派发 animationend」这次**不管用**——弹框卡在更早一级的 `cheetah-zoom-appear-prepare`
(不是 `-active`),补派发 animationstart / animationend 都不推进,`opacity` 恒为 `0`。
硬确诊:`await new Promise(r=>requestAnimationFrame(r))` **直接 45 秒 CDP 超时**,即渲染帧完全不推进。
**破法 = 一进编辑器就把 rAF 打补丁成 setTimeout**,rc-motion 的 prepare→active 就能自己跑完:
```js
window.requestAnimationFrame = cb => setTimeout(() => cb(performance.now()), 16)
window.cancelAnimationFrame = id => clearTimeout(id)
```
打完补丁后弹框自行 `opacity → 1`,「AI封图」/ 生成 / 确定全部一次通过。
**顺序建议**:navigate 之后立刻打补丁,别等卡住了再救——省 2-3 个回合。

**⚠️ 2026-08-20 新坑：AI 封图卡「图片生成中…」不动，根因是轮询 URL 变 undefined（破法＝刷新页）：**

点完「根据全文智能生成封面」后 UI 卡在「图片生成中…」**超 125 秒不动**。排查顺序与结论：
1. 弹框展开本身正常（派发 animationend 后 196×134 → 980×671，opacity=1），rAF 补丁已打；
2. 覆盖 `visibilityState` → visible 解除后台节流：**无效**；
3. **开网络追踪后 15 秒内零请求** ⇒ 轮询根本没在跑；
4. 请求列表里抓到真因：`https://baijiahao.baidu.com/builder/rc/undefined`（GET 200）
   —— **前端没拿到生成任务 id，轮询打到 undefined，永远等不到结果。不是生成慢、不是节流。**

⛔ **关弹框重开无效**：重开后状态仍是「图片生成中」，且「根据全文智能生成封面」按钮 rect 为 0×0 不可点。

✅ **破法＝存草稿 → 整页刷新**（`/builder/rc/edit?type=news&article_id=<id>`）。
重载后僵死状态清空，重走一遍封面流程：20 秒内 4 张候选全出图、「确定 (1)」一次通过。
⏱ **判据先后顺序（别硬等）**：生成超 **40 秒** 就开网络追踪看有没有轮询；零请求或看到 `/rc/undefined` → **直接刷页**，别再等、也别反复重开弹框。

**✅ 同日顺带验证（可当稳定手法用）**：在正文 iframe 里直接 `p.remove()` 删段落，
**会被 ueditor 持久化**——存草稿 + 重载后段数/字数与删后一致（本例 34段/2051字 → 33段/1956字）。
可以放心用它做发布前的字数微调（例如把 >2000 压回引擎偏好的 1500-2000 区间）。

**⚠️ 字数校准更正**：编辑器底栏「字数」与「去掉空白后的纯正文字符数」**完全一致**（实测 2051 对 2051、
1956 对 1956）。之前从日志反推出的「编辑器比本地算法少 6%」不成立，**别再按比例换算**，
写稿时直接拿纯字符数当编辑器字数用。


**🔴 2026-08-21 封面链路大改版（旧第 5-8 步部分失效，法律类选题请直接跳到「破法」）：**

百家号把封面弹框换了新版：
- 标签「AI封图」→ **「AI封面」**；
- 面板从「根据全文智能生成封面」一个链接，换成 **热门模板 + 封面描述 + 封面文字 + 生成**，
  另有居中大按钮 **「AI一键生成封面」**——它是个 `div`，**文字是背景图、`innerText` 为空**，
  文本选择器一律找不到，只能靠 rect 定位（本次 `524,304,192,44`，中心 620,326）。

**🔴 AI 封面对法律类选题会直接失败，且 UI 不报错、只是永远转圈。**
真判据是查生成任务：
```js
await (await fetch('/writebrain/aicover_v2/generate/query?task_id=<id>',{credentials:'include'})).json()
// {"errno":0,"data":{"status":3,"images":[],"fail_reason":"text_audit"},...}
```
本篇两次全败：第一次描述写「法院天平与合同文件」，第二次换成完全中性的
「安静的办公桌面，一叠文件与一支笔」、封面文字清空，**仍是 `text_audit`**
⇒ **触发审核的不是你填的描述，是标题/正文本身**（含「违约金」「法院」这类词）。
**别再改描述重试，改不出来。**

**✅ 破法＝走「免费正版图库」标签页**（SKILL 只禁「正文/本地上传」，图库是页内允许的，
手册旧说「法律类关键词常无结果」——那是因为搜的是法律词，**搜中性物件词就有结果**）：
```js
const m=document.querySelector('.cheetah-modal');
window.__fire([...m.querySelectorAll('.cheetah-tabs-tab')].find(e=>e.innerText.trim()==='免费正版图库'));
// 搜索框：native value setter + input 事件 + 派发 Enter keydown/keyup
// 搜「合同」出 30 张；图片 rect 例 452,180,160,240 → 选择圈在右上角（x+140, y+18）
// elementFromPoint(592,198) 拿到圈再派发五连事件 → 按钮变「确定 (1)」+ 右侧预览换图
```
判据：`[...m.querySelectorAll('button')]` 里出现 **`确定 (1)`**，且右侧预览 img 的 src 换成
带 `wm_1,k_cGljX2JqaHdhdGVyLmpwZw==` 水印参数的那张。点可见的那个「确定」即完成，一次通过。
⏱ 法律类选题今后**直接走图库，别在 AI 封面上耗回合**（本次白耗 4 轮 ≈ 60 秒等待 ×2）。

**🔴 同日复验：点击/轮询完全不动的真因仍是 `document.visibilityState === 'hidden'`。**
fire 事件派发到「AI一键生成封面」，12 秒内**零网络请求**；覆盖 visibilityState 后**同一次 fire
立刻打出 `/writebrain/aicover_v2/generate`**。→ **进编辑器的第一动作应该是 rAF 补丁 + 解 hidden 一起打：**
```js
window.requestAnimationFrame = cb => setTimeout(() => cb(performance.now()), 16);
window.cancelAnimationFrame = id => clearTimeout(id);
Object.defineProperty(document,'visibilityState',{get:()=>'visible',configurable:true});
Object.defineProperty(document,'hidden',{get:()=>false,configurable:true});
document.dispatchEvent(new Event('visibilitychange'));
```

**✅ 存草稿会改写 URL（08-06 那条「不再改写」本次不成立）**：存完 URL 就是
`edit?type=news&article_id=1874086204811118254`，不必再去 `/rc/content` 首行捞 id。

**⚠️ PUBLISH-LOG 行首格式是硬约束（今天差点又漏记）：百家号行必须写成 `YYYY-MM-DD | 百家号 | ...`，
不带时间**——SKILL 的计数命令是 `grep -c "^$(date +%Y-%m-%d) | 百家号"`，grep 里 `|` 是字面量，
写成 `2026-08-21 07:26 | 百家号` 会**一条都数不到**，下一轮就会把已发的当没发、多发一篇。
时间要记就记在行内（`| 07:26 发布 |`），别放行首。知乎行带时间不受影响（它不参与这个计数）。

**⚠️ 2026-08-18 两条新坑（标题吞字母 + 正文点不进，都有现成破法，建议直接当默认流程）：**

1. **标题区用 `computer type` 打字会静默吞掉 ASCII 字母。** 打「律师用AI会不会泄露客户信息？…」
   进去变成「律师用会不会…」（29字→27字），AI 两个字母凭空消失，没有任何报错。
   **正文 iframe 里同样的字符全部保留**（AI×8 / wenshucha.com / 1.6亿一个没丢），所以这是标题区独有的。
   **破法 = 用 execCommand 写标题，别用 type：**
   ```js
   const t=document.querySelector('[contenteditable=true]');t.focus();
   const r=document.createRange();r.selectNodeContents(t);      // ⚠️ 不要 collapse
   const s=getSelection();s.removeAllRanges();s.addRange(r);
   document.execCommand('insertText',false,标题);                // 直接替换整个选区
   ```
   ⚠️ 配套坑：`execCommand('delete')` 在标题区**无效**（选中全文 delete 不删，紧接着的
   insertText 会插到开头，造成标题重复成两份）。**别先 delete 再 insert，一步 insertText 替换选区。**

2. **正文区 `left_click` 可能完全打不进去**（点 iframe 内 y=345 后 type，字全跑进标题栏）。
   与其反复探针试坐标，**直接在 iframe 内用 execCommand 逐段灌**，一次成，且不吞 ASCII：
   ```js
   const f=document.getElementById('ueditor_0'), doc=f.contentDocument, win=f.contentWindow;
   doc.body.innerHTML='<p><br></p>'; doc.body.focus();
   const r=doc.createRange(); r.selectNodeContents(doc.body);
   const s=win.getSelection(); s.removeAllRanges(); s.addRange(r);
   doc.execCommand('insertText',false,P[0]);
   for(let i=1;i<P.length;i++){ doc.execCommand('insertParagraph'); doc.execCommand('insertText',false,P[i]); }
   ```
   实测 29/29 段一次通过，自动生成带 `data-diagnose-id` 的 `<p>`。
   **验收查 `doc.body.querySelectorAll('p').length` 和 `doc.body.innerText` 长度，别看底栏字数。**
   → 这条比旧手册第 3 步「点正文区+两字探针+截图确认」更稳更快，**建议以后首选**。

**✅ 2026-08-19 封面弹框第三级破法（前两招都失效时用这个，实测一次解开）:**
本次弹框卡在 `cheetah-zoom-appear-start`（**比 08-05 的 -prepare、08-04 的 -active 更早一级**），
且 navigate 后立刻打了 rAF 补丁仍 `opacity:0`，补派发 animationstart+animationend 也不推进。
**破法 = 直接把入场动画的 class 全摘掉并硬设 opacity：**
```js
const m=document.querySelector('.cheetah-modal');
m.classList.remove('cheetah-zoom-appear','cheetah-zoom-appear-start',
                   'cheetah-zoom-appear-prepare','cheetah-zoom-appear-active');
m.style.opacity='1'; m.style.transform='none';
const wrap=m.closest('.cheetah-modal-wrap'); if(wrap) wrap.style.opacity='1';
```
摘完 `opacity` 立刻为 1、弹框 980×671，后续「AI封图」→「根据全文智能生成封面」→「确定(1)」全部一次通过。
→ **顺序固定为：① 进编辑器先打 rAF 补丁 → ② 卡住就派发 animationend → ③ 还卡就摘 class 硬设 opacity。**
别在 ② 上反复试，直接上 ③ 省两个回合。

**⚠️ 2026-08-06 三条新坑(和坐标/点击有关,比动画那批更根本):**
1. **`computer` 工具的坐标 = CSS/viewport 空间,不是截图像素空间。** 本次窗口 1400×844 截图 / 1200×723 viewport,
   系数 1.1667。**做法:一律用 JS `getBoundingClientRect()` 拿到的值直接喂给 `computer`,不要乘系数、也不要从截图上量。**
   (旧手册第 5 步那句「坐标要换算」指的是反过来:把截图上量到的像素换回 CSS 才能用。)
2. **标题区:`left_click` 落进去了,`type` 却什么都不写入。** 坐标经 rect 核对无误、`activeElement` 却是外层 `edit-mode`。
   **破法 = 用 JS 建光标再打字:**
   ```js
   const t=document.querySelector('[contenteditable]');t.focus();
   const r=document.createRange();r.selectNodeContents(t);r.collapse(true);
   const s=getSelection();s.removeAllRanges();s.addRange(r);
   ```
   验 `document.activeElement===t` 为 true 后再 `computer type`,一次通过。正文(iframe)不受影响,照常点+打。
3. **封面弹框内的一切按钮,物理 `left_click` 100% 落空**(AI封图标签连点两次、间隔 5s,DOM 文本纹丝不动)。
   **破法 = JS 派发完整事件序列**,React 的委托监听才认:
   ```js
   for(const e of ['pointerdown','mousedown','pointerup','mouseup','click'])
     el.dispatchEvent(new MouseEvent(e,{bubbles:true,cancelable:true,composed:true,clientX:cx,clientY:cy,view:window}))
   ```
   「AI封图」标签 / 「根据全文智能生成封面」/「确定 (N)」/ 页面底部「发布」全用此法,**四处全部一次通过**。
   注意标签要取 `.cheetah-tabs-tab`(外层)而非 `-tab-btn`。
4. **存草稿不再改写 URL** —— URL 恒为 `edit?type=news`,拿不到 article_id(旧手册第 4 步已失效)。
   **改法:发布后开 `/builder/rc/content`,首行即本篇,`a[href*="s?id="]` 里的 19 位数字就是 article_id。**
   顺带这一步还能直接读到「已发布 / 审核中」状态,比停在编辑页猜要准。
5. 弹框仍卡 `zoom-appear-active` + `opacity:0`(`visibilityState=hidden`)。**08-05 的 rAF 补丁在 navigate 后立刻打了,
   仍不足以单独解开;补派发一次 `animationend`(08-04 破法)后 `opacity` 立刻变 1。→ 两招都要留着,先打补丁,不行再派发。**

**🔴 2026-08-07 最严重的一条:`computer type` 会静默丢弃全部 ASCII 字符和全部换行符。**
不是「首字丢失」,是**所有非 CJK 字符被吞**,且一个字的报错都没有:
- 标题打 `AI合同审查靠谱吗？…` → 落地 `合同审查靠谱吗？…`,「AI」凭空消失。
- 正文灌 1300 字 → `AI接过去`变`接过去`、`交给AI反而`变`交给反而`、`第3.2条`的数字也没了,
  **56 个换行全丢,整篇挤成 1 个 `<p>`**。历史手册记的「标题区点了 type 不写入」多半就是这个的表现。
**✅ 破法(08-07 全程使用,标题+正文各一次通过,今后首选):改用 `execCommand`,别用 `computer type`。**
```js
// 标题(主文档)
const t=document.querySelector('[contenteditable]'); t.focus();
const r=document.createRange(); r.selectNodeContents(t); r.collapse(true);
const s=getSelection(); s.removeAllRanges(); s.addRange(r);
document.execCommand('insertText', false, '标题文字');   // ← Latin 字符能进来了
// 正文(iframe[0]),分段灌
const f=document.querySelectorAll('iframe')[0], w=f.contentWindow, d=f.contentDocument;
w.focus(); d.body.focus();
let rr=d.createRange(); rr.selectNodeContents(d.body); rr.collapse(false);
const ss=w.getSelection(); ss.removeAllRanges(); ss.addRange(rr);
TEXT.split('\n').forEach((p,i)=>{ if(i) d.execCommand('insertParagraph');
                                  d.execCommand('insertText', false, p); });
```
灌完验 `d.body.innerText.length` 和 `d.querySelectorAll('p').length` 与源文一致(08-07 实测 56/56 段、`AI` 保留 38 处)。
清理写错的字用 Range 精确选中 + `execCommand('delete')`,别用退格键。

**⚠️ 2026-08-07 另三条:**
1. **正文点不中时,键盘事件会回落到标题区。** 在 iframe 坐标点击后打的探针「探针AI测试」**跑进了标题**,
   正文 iframe 一个字没有。→ **打完探针必须同时读标题和 iframe 两处**,只查 iframe 会误判成「输入丢失」而重打,
   越重打标题越脏(最后标题成了 `AI探针测试合同审查靠谱吗？…`)。
2. **底栏「字数」在 execCommand 灌文期间恒为 0,直到封面「确定」后才跳到真实值。** 这是第三次踩,
   **字数 0 永远不能当输入失败的判据**,真判据只有 `iframe[0].contentDocument.body.innerText` 的长度和段数。
3. **存草稿本次又会改写 URL 了**(`?article_id=…`),与 08-06 记的「已失效」相反。→ **两条路都留着**:
   先看 URL,没有再去 `/builder/rc/content` 首行取。
4. 弹框仍卡 `zoom-appear-active`+`opacity:0`;navigate 后立刻打 rAF 补丁**不足以单独解开**,
   补派发一次 `animationend` 立刻变 1。与 08-06 一致 → **这套组合拳(补丁 + 派发)可当固定动作。**

**🔴 2026-08-10 最贵的一条:标题区是 Lexical,`execCommand` 已经生效了,但 `innerText` 当场读回是旧值。**
`document.execCommand('insertText',...)` 返回 true、文字其实已经进去了,可紧接着读
`titleEl.innerText` 拿到的还是 `"\n"`(len 1)——照此判「没写进去」再打一遍,标题就变成**两遍**
(本次实测落地 47 字 = 35 字标题 + 12 字重复)。
**判据改法**:插入后 `await` 一下再读,或直接读 `innerHTML`(能看到 `<span data-lexical-text>` 里的真值)。
**写错了怎么删**(别用退格):
```js
const s=getSelection(); for(let i=0;i<N;i++) s.modify('extend','backward','character');
document.execCommand('delete');
```
**另一条**:标题第一次 `execCommand` 之前需要一次**真实 `left_click`** 让 Lexical 自己建选区——
纯 JS `focus()`+Range 那次没进去(`activeElement` 是对的也没用)。点一次之后 `execCommand` 就一次通过。
正文 iframe 不受影响,08-07 那套(w.focus + d.body.focus + Range + 逐段 insertText/insertParagraph)
本次 53/53 段、ASCII 全保留,一次通过。
**其余照旧**:①「字数 0」第四次出现仍是假信号,旁边的「已保存」才是真信号;②弹框仍卡
`zoom-appear-active`+`opacity:0`,**rAF 补丁 + 补派发 `animationend` 组合拳**照常解开;
③封面框图片图标 = 「选择封面」文字上方 **25px(CSS 空间)** 命中 `-icon`;
④存草稿本次**不改写 URL**(与 08-06 同、与 08-07 反)→ article_id 去 `/builder/rc/content` 首行取。

**✅ 2026-08-11 全程零返工的固定动作(照这个顺序跑,本次 10 步一次通过):**
navigate → 立刻打 rAF 补丁 → 标题**先一次真实 `left_click`** 再 `execCommand('insertText')` →
插入后 `await` 800ms 再读 `innerHTML` 验(避开 08-10 的 Lexical 读回旧值坑) → 正文 iframe[0] 走
`w.focus + d.body.focus + Range + 逐段 insertText/insertParagraph`(本次 51/51 段、ASCII 全保留) →
存草稿(**不改写 URL**,与 08-10 同) → 「选择封面」文字**上方 25px**(CSS 空间)命中 `-icon`,JS 派发五连点击 →
弹框卡 `zoom-appear-active`+`opacity:0`,**补派发 `animationend`** 立刻变 1 → AI封图 / 生成 / 确定全用五连派发 →
底栏「发布」同法。

**🆕 本次唯一新坑:点「发布」那一次 `javascript_tool` 的返回会被工具层拦成
`[BLOCKED: Cookie/query string data]`,读不到任何回执。** 别据此判「没点到」而重点一次——
判据看 **tab 的 URL 是否已跳到 `/builder/rc/clue?...&from=news&firstPublish=...`**,跳了就是发布成功。
最终一律以 `/builder/rc/content` 首行的「已发布」+ article_id 为准。
另:「字数 0」第五次出现,仍是假信号。

**已四次复现的稳定规律**(07-29 / 07-30 / 08-03 / 08-04 / 08-07 共五次):封面框的图片图标 = 「选择封面」文字**上方 32px**(截图像素)。
08-07 换算到 CSS 空间实测:文字 rect 上方 25px 处 `elementFromPoint` 即命中 `…-icon` 元素,直接 JS 派发五连点击即开框。
**平台行为**:用了 AI封图后,平台会自动勾上创作声明「采用AI生成内容」——保留即可,合规。

**⚠️ 2026-08-18（16:2x 复核）知乎「当日约 2 篇硬墙」再次证实，队列理论第二次被否**
14:5x 那次发现 9 篇卡草稿箱之后，**过了约 1.5 小时再查创作中心：已发布仍是 9 条、草稿箱仍是 9 条，一条都没自行落地**。
→ 「进队列、晚点会自己发出去」彻底不成立。当日超过约 2 篇之后写的稿子是白写，必须次日手动重发。
→ **排程执行口径：知乎每天只排 2 篇（1 篇同话题 + 1 篇积压），当日额度用完就不要再写知乎版**，
   把回合省给百家号。判断额度有没有用完，看 /creator/manage/creation/article 的「共 N 条内容」有没有涨。

**⚠️ 2026-08-18（第7篇）新坑：用 DOM `p.remove()` 改正文，底栏「字数」不会重算。**
灌完全文字数显示 2001（想压进 1500-2000 格），于是换短末段并 remove 掉重复的旧 `<p>`，
iframe innerText 从 2073 降到 2057、段数 36 正确，**但底栏字数纹丝不动仍显示 2001**；
补插一个字符再 `execCommand('delete')` 触发 input 事件也没让它重算。
→ 「字数」计数器不可信这条又添一种新形态（此前是「恒为 0」，这次是「改了不更新」）。
   **真判据仍只有 `iframe[0].contentDocument.body.innerText` 的长度和 `p` 段数。**
⚠️ 配套：想替换某一段时，`selectNodeContents(p)` + `insertText` **不会替换该段，而是新起一段**
   （本次一下变成 37 段）。要替换整段，只能 insertText 后再把旧段 `remove()`，然后逐条验段数与首尾。


**🔴🔴 2026-08-21 推翻 08-06 第 1 条：`computer` 的坐标是【截图像素空间】，不是 CSS/viewport 空间。**
旧手册写「一律用 `getBoundingClientRect()` 的值直接喂给 computer，不要乘系数」——**这条是错的，照它做点击会静默落空**。
本轮实测（截图 1560×784 / viewport 1492×750，k = 1560/1492 = 1.0456）：
- 直接喂 rect 值点 (500,290) → `document.activeElement` 是 **body**，没进编辑器；
- 同一个点乘 k 变 (320,344) → `activeElement` 立刻是编辑器，一次进去。
**固定写法：**
```js
const k = 1560 / window.innerWidth;   // 1560 = 最近一次截图的宽度，每轮现读
const shot = [Math.round(vpX * k), Math.round(vpY * k)];   // 喂给 computer 的才是这个
```
（08-06 那条之所以「看起来成立」，多半是当时窗口 k 接近 1；k 越偏离 1，落空越明显。）

**🔴 落空之后最严重的连锁后果：整篇正文会被一个字符替换掉，而且三个指标里两个会骗你。**
真实点击没落进编辑器时，选区仍停在 paste 前用 JS 设的「全选」状态，接着那一次真实打字就把全文换成了那一个字符。
当时的读数是：**fiber 的 `memoizedProps.editorState` 仍报 43 blocks（渲染快照，滞后）**、
**底栏字数仍显示 2998（假高）**、**只有 DOM `[data-block="true"]` 报的 1 是真的**。
→ **新纪律两条：**
① 真实打字前必须验 `activeElement` 在编辑器内 **且** `getSelection().isCollapsed === true`，一条不成立就别打；
② 判模型状态优先看 **DOM `[data-block]` 计数**；fiber 的 editorState 只在刚 paste 完那一刻可信。

**✅ 知乎（文章区/回答区通用）注入六步，本轮第三次才跑通，照此固化：**
```
① 按 k 换算坐标真实点击编辑器 → 验 activeElement 在编辑器内
② 真实 cmd+a → 真实 Delete → 验 DOM blocks==1 且 innerText 去空白后 length==0
   （跳过这步直接 paste = 追加不是替换，实测 1 + 43 → 85 blocks 整篇重复，这是第二次踩）
③ JS focus + selectNodeContents + 派发 selectionchange + ClipboardEvent 注入 BODY.slice(0,-1)
④ 验 DOM blocks == 源段数
⑤ 滚到末段、按 k 换算真实点击 → 验 activeElement + isCollapsed → cmd+Right → 真实打回最后一个字符
⑥ 与源文逐段 diff，要求 diffCount == 0
```

**⚠️ 文章区开着「Markdown 语法输入中」**：行首 `1. ` 会被解析成有序列表。注入前先把 `^(\d)\.\s+` 替换成 `$1、`。
注入后验 `.public-DraftStyleDefault-orderedListItem` 计数为 0。**旧积压稿凡有数字编号行首的都要先做这个替换。**

**⚠️ 文章区「发布」按钮初始 `disabled=true` 不是缺话题/封面，是草稿还在保存中**，等约 12 秒自行 enable
（同时底栏字数从假 0 跳到真值）。别去点「添加话题」凑条件。

**⚠️ 文章区「发布中...」同样会卡住不动（>60 秒），成功判据是 `/api/v4/members/{token}/articles`**
里出现该 id、账号文章数 +1。**不要盯按钮文案，也不要重复点。**

**⚠️ `members/{token}/answers` 与 `questions/{qid}/answers` 在【问题页上下文】会返 `10003 请求参数异常`，
换到 `/people/{token}/answers` 上下文同一请求立刻正常。** 这不是风控，是上下文相关的接口行为
——08-20 记的那次「限流苗头」至少有一部分是同一现象。**判发布成败一律在个人主页上下文调 API。**

**⚠️ 扫止损线关键词必须看上下文**：本轮 `innerText` 里三处「失败」全部来自正文（"这种失败不报错"…），
百家号侧「未通过」则是筛选 tab 名。**只数命中次数会天天误报。**


### 🔴 2026-08-21 · 百家号正文注入链路大改（推翻本手册两条旧结论）

**旧结论一「正文在 iframe 内，JS 够不着，只能点正文区 + type + 截图确认落点」——已作废。**
`document.getElementById('ueditor_0').contentDocument` 现在可以直接访问（同源），
于是正文可以走：清空 → 逐段 `d.execCommand('insertText')` + `insertParagraph` → 读回
`[...d.body.querySelectorAll('p')]` 与源文**逐段 diff**。40 段 2002 字实测 diffCount=0、零返工，
**全程不需要截图**。这一条在本轮救了命：CDP 截图中途断连（"Claude in Chrome is not connected"），
若还依赖「打两字探针+截图确认」的老链路，整轮会卡死。

**旧结论二「字数计数器是防抖的，探针刚打完显示 0 属正常」——不完整，会害死人。**
真相是：JS 注入后 **DOM 满、UEditor 自身 model 也满**（`getContent()` 2714 字符），
但**外层 React 壳完全不知情**，所以底栏「字数」恒为 0。后果不只是显示问题——
**「AI一键生成封面」会据此报「标题或正文内容过短，多输入一些内容吧~」而拒绝生成**，
等多久都没用（本轮等了 20 秒＋重试才发现根因）。

**破法（一句话）**：
```js
const ed = window.UE_V2.instants.ueditorInstant0;   // 不是 window.UE，是 UE_V2
ed.fireEvent('contentchange');                       // 字数 0 → 2252，AI 封面立刻可用
```
注入完正文后**必须**补这一句，再去点封面/发布。顺带：`window.UE`、`UE.instants` 都不存在，
实例挂在 `window.UE_V2.instants.ueditorInstant0`；`getEditorContent()` 这个全局返回 undefined，别用它判空。

**封面**：AI 生成一次给 2 张，**必须逐张看文案错别字再选**。本轮左图把
「查不到不等于是假的」渲染成「查不到不等**到**于假的」，选了会把错别字印在封面上；右图正确。

### ⚠️ 知乎：SPA 难驱动
页面长期不进 document_idle，截图工具超时，程序点击不落到 React handler。
`ProfileHeader-name` 是纯 span 无编辑控件。
**结论：知乎稿子生成后交由 Jack 手动贴。** 不要在这上面耗回合。

### ⛔ 本地文件上传（头像、正文插图）
点击时才动态生成 file input，弹 **macOS 系统选档窗口** —— 浏览器外，驱动不了。
**但封面已不受此限：走 AI封图。** 头像这类一次性设置仍需 Jack 手动传。

---

## 五、每次产出的交付物

```
~/wenshucha-seo/content/drafts/YYYY-MM-DD/
  ├─ baijiahao-<slug>.md    # 附 article_id + 发布状态(已发布/仅草稿+原因)
  ├─ zhihu-<slug>.md        # 待 Jack 手动贴
  └─ INDEX.md               # 当日清单 + 状态 + 下一步

另追加一行到 ../PUBLISH-LOG.md 作为发布台账（可回溯、可撤稿）。
```

每篇稿末尾必须带**自查块**：
- [ ] 全文无链接/电话/邮箱（养号期）
- [ ] 数据口径与官网一致（当前：**1.6 亿**）
- [ ] 未编造案号、统计、案例
- [ ] 定位是办案人视角，不是 IT 视角

---

## 六、口径红线（违反一次毁品牌）

- **数据规模对外统一 1.6 亿**（Jack 2026-07-22 定案）。海外站 = 160M。
- **劳动争议数据样本仅含获赔判决**，禁称胜诉率、禁做逐年趋势。
- **禁引用第三方数据时篡改**（143M=裁判文书网累计公开量、10.979M=最高法年度公开量，这些不是我们的数）。
- **不编造案号、金额、定罪率。**
- 竞品对比不做贬低式表格，改「选型该问的 12 个问题」。

---

## 📌 白杨SEO 百家号方法论（2026-08-12 从知识星球原帖调取，此前只留了标题）

来源：星球「白杨SEO玩赚流量」topic 412412455488248（2022-12-27）+ 181541215585452（2023-02-11）

### ⛔ 先破一个幻想：百家号没有快排

白杨原话：「百家号没有快排！如果单靠刷点击排名也上不去。**百家号排名，主要是看文章标题匹配。
文章优质，被百度收录了，然后排名就会不错。**」

→ 这条与我们 2026-08-12 的乾净真搜实测完全吻合：进百度首页的 5 条全是标题精确匹配搜索词的长尾，
大词一条没进。**选词和标题匹配是唯一杠杆，没有捷径。**

### ★ 卡位排名（我们此前完全不知道的东西）★

「百家号卡位排名」= 关键词在百度移动端/PC端的百家号**大卡位**。

- 某个关键词**只有一家**百家号排名卡位时 → 占大位置，**可以显示绑定电话、绑定网址等菜单栏目**
- 2-3 家时 → 聚合展现，每个关键词只出一个百家号卡位
- PC 端大卡位：最后发布的几篇会以 **3 篇超大位置**展现
- 注：一般手机端已卡位的词，才能在 PC 端大卡位展现

→ **这是平台给的官方引流位**，不是违规夹带。我们此前一直在纠结「养号期不能放联系方式」，
卡位是合规拿到电话+网址曝光的正路。

### 卡位优化三条（白杨原文）

1. **账号命名**：`（地域词）+ 行业词 +（修饰词）+ 品牌词/公司名`，不宜过长，包含关键词。
   ⚠️ **我们现在叫「文书查」——纯品牌词，零行业词，不符合这个公式。**
   按公式应为「裁判文书检索 文书查」这类。改名前需确认百家号改名冷却期与历史影响。
2. **内容优质原创**提升账号整体权重。
3. **企业百家号蓝V认证** —— 白杨：「对于进行过百家号蓝V认证的，**百度会给予卡位和排名**」
   「有蓝V认证的企业号在百度会有**优先推荐引流**，一般企业做过蓝V认证之后，多发几条作品，
   踩中相关关键词，搜索排名自然排名上升。」
   ⚠️ **我们没做蓝V。这是目前最大的一个空缺。** 蓝V认证收费，需 Jack 批准后才能动。

### 文章排名六条（白杨原文精简）

1. 标题加相关关键词（行业词、产品词）
2. 内容必须与标题关键词匹配，**文不对题＝低质，百度不收录不给排名**
3. 坚持原创优质、**稳定持续输出**
4. 通俗易懂，不堆砌
5. **内容垂直度要高**——平台按内容打标签再推给同标签用户，垂直度高才有展现和权重
6. 蓝V企业号有优先推荐引流

### ⏰ 发文黄金时间（我们踩错了）

白杨原文：「较晚较早发布都会容易错过流量高峰期……黄金时间一般是
**早上7—8点，11—13点，15—16点，19点—20点**。要结合自己的内容领域去选择时间节点。
例如：**知识型干货性内容最好是早上和下午**，娱乐或生活分享就中午或晚上。」

→ 我们是**知识型干货**，应走早上和下午。分发任务时间已据此调整。

---

## 🚨 用自建 ES 出数时的红线（2026-08-18 差点踩，务必先读）

数据源：本机 `es-search2` (v216, 127.0.0.1:3201，线上 /wscx2 同源)，
ES 索引 `judgments`，`160,291,678` 篇 / 413.5GB。

### ✅ 可以直接引用的

| 来源 | 为什么可靠 |
|---|---|
| `/search` 的 `total`（结构化筛选下） | 精确计数 |
| `/agg2` 的 term 聚合：year / recent / province / cause / court / caseType / procedure / courtLevel / docType / industry | 都是字段级 term 聚合，不涉语义猜测 |
| 结果里的 `case_no` / `court` | 真实案号，可回中国裁判文书网核对 |

### ❌ 绝对不能拿来做统计的

**`q2`（在结果中搜索）对正文用的是 `match` 而非 `match_phrase`** ——
即分词后 OR 匹配，不是精确短语。

实测证据（2026-08-18，同一基准 1,350,049）：
```
q2=予以支持   → 1,186,303
q2=不予支持   → 1,157,143    ← 两者几乎相同
q2=已过仲裁时效 → 1,157,256
```
「不予支持」匹配到的是含「不」或「予」或「支持」的文书，几乎是全集。

**所以 q2 只能用于「加一个词还剩多少条」的收窄演示，
绝不能解释成「多少案子是这么判的」。** 拿它写「支持率/败诉率」就是编数据。

### 判决倾向类结论怎么办

目前的检索接口**给不出**「多少案子支持了诉求」——那需要对判项做结构化抽取，我们没有这个字段。
所以：
- 可以说：这类案子有多少件、分布在哪些法院/年份/审级/文书类型
- **不能说**：多少胜诉、多少支持、判赔多少（除非另有实算数据，如 /data/labor-report/
  那份基于 8 万份获赔判决的报告，而它自带「样本仅含获赔判决，不代表胜诉率」的口径限制）

### 🔗 链接口径（2026-08-17 实测定案）

| 想贴的东西 | 能不能 | 说明 |
|---|---|---|
| 中国裁判文书网原文直链 | ❌ **做不到** | 2021 年后需登录+验证码，深链失效。我们自己的产品页也写明「原文直链目前系统性为空」。**绝不能承诺「点击直达原文」** |
| 案号（文字） | ✅ | 写「可到中国裁判文书网自行核对」 |
| 我们的检索深链 | ✅ | `https://tob.wenshucha.com/cases?q=…&cause=…&province=…`，**前端只吃这三个参数**，其余传了不生效 |

**百家号 vs 知乎的关键差别**：百家号养号期红线是全文零链接，wenshucha.com 只能纯文本出现，
实测从百家号点到官网 **0 次**；**知乎可以放链接**，这是目前唯一通着的转化路径，要用好但别滥用
（一篇一条，且必须在「让你自己验证我上面那些数」的语境里）。

⚠️ 另记：`https://www.wenshucha.com/wscx2/` 与 `/wscx/` 线上实测 **25 秒超时回 000**，
那条反代是坏的，别往外贴。真正能用的检索应用入口是 **`https://tob.wenshucha.com/cases`**。

### 🔗 深链红线：URL 里绝不能有空格（2026-08-18 实测踩坑）

**现象**：知乎回答里贴 `https://tob.wenshucha.com/cases?q=借条 未约定利息 逾期利息&cause=民间借贷`，
发布后知乎的自动识链**在第一个空格处截断**：

- `<a>` 的 href 只剩 `...?q=借条` —— 三个关键词丢了两个，点进去是另一批结果
- 剩下的 ` 未约定利息 逾期利息&cause=民间借贷` 被甩在链接后面变成一行裸文字垃圾

**根因**：不是工具的错。`wsc_query.py` 输出的 `深链：` 那一行用 `urllib.parse.urlencode`，
空格已经是 `+`，本来是对的。是我为了「好看」手工把 `+` 改回空格，自己把它写坏的。

**规矩**：
1. 深链**原样复制** `wsc_query.py` 输出的 `深链：` 那一整行，**禁止手工美化 URL**。
2. 贴进正文前自查：`grep -n 'tob.wenshucha.*?.* ' 草稿.md` —— 命中就是有空格，必须改回 `+`。
3. 发布后复核 `document.querySelector('a').href` 的参数个数，别只看有没有 `<a>`。

**顺带一个好消息**：知乎会把裸 URL 自动转成**卡片式链接**，锚文本直接取目标页 `<title>`，
实测显示成「类案检索 · 近 1.6 亿裁判文书全文检索 | 文书查」。
→ 所以 `tob.wenshucha.com/cases` 的 `<title>` 就是我们在知乎的免费品牌位，别乱改。

### ✅ 知乎 Draft.js「清空重写」正确姿势（2026-08-18 打通）

之前只在**空编辑器**上验证过 paste 注入，误以为「全选＋粘贴」也能替换。实测：**不能**。

| 做法 | 结果 |
|---|---|
| `execCommand('selectAll')` + paste 事件 | ❌ 选区 DOM 上是对的（`selection.toString()` 有 4061 字），但 Draft.js **不认程序设置的 DOM 选区**，内容被**追加**到光标处 → 41 段变 82 段 |
| `computer.key('cmd+a')`（没先点进编辑器） | ❌ 键盘事件没落到编辑器，纹丝不动 |
| **先 `computer.left_click` 真点进正文区，再 `cmd+a` → `Delete`** | ✅ 瞬间清空到 `blocks:1 / chars:1`（剩一个零宽空格） |

**所以改稿流程固定为**：
1. `computer.screenshot` 拿到编辑器正文区的真实坐标（**别用 `getBoundingClientRect`** —— 知乎有内层滚动容器，算出来的 y 可能是 -2067 这种废值）
2. `left_click` 点进正文 → `key cmd+a` → `key Delete` → 断言 `blocks===1`
3. JS 派 paste 事件注入新正文 → 断言 `blocks === 段落数`
4. 按钮用**五连事件**派发，不要用坐标点（坐标点了没反应，五连一次就中）

### ⚠️ 两个把我骗过去的「验证假阳性」（2026-08-18）

改完之后我连着两次误判「没生效」，都是**验证代码写错**，不是发布失败：

1. **`nParam` 数错了**：知乎会把外链包成 `link.zhihu.com/?target=<整条URL做了URL编码>`。
   直接 `href.split('?')[1].split('&').length` 永远等于 1。
   正确写法：
   ```js
   const u = new URL(a.href);
   const tgt = u.searchParams.get('target') || a.href;
   const q = new URL(tgt);           // 再解一层
   [...q.searchParams.keys()]        // ← 这才是真参数
   ```
2. **关键词自查串味**：用 `/未约定利息 逾期利息/` 判断「有没有残留裸文字」，
   结果命中的是正文里那句「关键词填「借条 未约定利息 逾期利息」」—— 永远 true。
   → **自查正则必须挑正文里不会出现的特征**，比如直接量那一段的**段落字数**（坏的 73 字，好的 28 字）。

**通则：说「没生效」之前，先怀疑自己的断言写错了。**

### 🧱 已焊死的发布前闸门（2026-08-18）

`zhihu_extract.py` 现在带 `lint()`，命中就 **exit 3**，拒绝输出正文：

| 检查 | 为什么 |
|---|---|
| URL 后面紧跟空格 | 知乎在第一个空格处截断识链，参数会丢、后半段变裸文字 |
| 残留 `**` 或 `[]()` | paste 注入是纯文本，markdown 记号会原样显示 |

反向测过：故意写一条带空格的 URL → `exit=3` 并打印命中行。**先跑 extract 再注入，别跳。**

### 📐 案由轮换（2026-08-18 起）

同一案由连答会让数据高度雷同，读者和平台都看得出来。目前已建立可横向对比的三组基线：

| 案由 | 二审占比 | 判决书:裁定书 | 调解书占比 | 地域 top3 | 纯度 |
|---|---|---|---|---|---|
| **刑事**（取保候审口径） | **6.7%** 最低 | 4.8 : 1 | ~0 | 广东/河南/浙江 | — |
| 民间借贷 | 8.1% | **11.3 : 1** 最高 | 0.8% | 浙江/广东/河南 | 99.7% |
| 婚约财产（彩礼） | 12.2% | **1.5 : 1** 最低 | 2.1% | 河南/山东/甘肃 | 90.8% |
| 劳动争议（工伤口径） | **39.7%** 最高 | 9.0 : 1 | **0.15%** | 北京/广东/辽宁 | 78.8% |

**这张表就是内容资产**，每答一个新案由加一行，横向对比是别人给不出的（他们只有法条，没有分布）。
用法举例：答工伤时说「二审 39.7%，是民间借贷的五倍，你得按打两轮做预算」——
单看 39.7% 没感觉，横着比才有杀伤力。

⚠️ 纯度那一列必须一起报。78.8% 的批次只能说「劳动争议类的上界」，不能说「工伤案有多少件」。

**这张表本身就是内容资产**：每答一个新案由就多一行，横向对比是别人给不出的东西
（他们只有法条，没有分布）。下一篇优先补空格：劳动争议的判决书:裁定书、交通事故、房屋买卖合同。

### 📌 2026-08-18 17:25 补测：知乎当日公开阈值这次是 5，不是 2

同日 14:50 记的「当日公开约 2 篇」偏低。17:25 复查 `/creator/manage/creation/article`：
今日实际公开 **5 篇**（3 篇「发布于 9 小时前」≈08:2x，2 篇「发布于 6 小时前」≈11:2x），
草稿箱 **9 篇**全部卡住，且 11:25 之后再无一篇转正。

→ 结论方向不变（**存在当日硬墙、撞墙后提交是白写**），但**阈值不是固定 2**，
本次观测落在 5。所以排程上不要写死篇数，改成**行为判据**：
**开 `/creator/manage/creation/article`，若「草稿箱(N)」的 N 在涨而今日「发布于」条数不涨 → 已撞墙，
当轮直接跳过知乎，别写稿也别重点发布**（同日重点实测无效）。

**📌 2026-08-18 18:2x 第三次复核知乎当日墙：确认「撞墙后不会自行转正」**
`/creator/manage/creation/article`：今日公开仍是 **5 篇**（3 篇「10 小时前」≈08:2x、2 篇「7 小时前」≈11:2x），
**草稿箱仍是 9 条，一条未动**。距 11:25 最后一次转正已过 7 小时。
→ 14:50 记的「队列会自行落地」第三次被否，可以当定论了。**当日阈值本次仍是 5**（与 17:25 观测一致，非固定 2）。
→ 排程口径不变：**撞墙后当轮直接跳过知乎，把回合全给百家号**，不写稿也不重试发布。

**🆕 2026-08-20 两条新坑（标题区换引擎 + 后台标签页点击失效，都有破法）：**

1. **百家号标题区已换成 Lexical 编辑器**，不再是旧的裸 contenteditable。
   DOM 现在长这样：`<p dir="auto"><span data-lexical-text="true">标题</span></p>`。
   ✅ **旧破法（execCommand insertText 替换选区）仍然有效，一次通过，不用改。**
   ⛔ **但验收方法必须改**：写完立刻读 `t.innerText` 会返回 `"\n"`（Lexical 还没 re-render），
      **会把成功误判成失败**，然后你就会去重写标题、写成两份。
   ✅ **正确验收 = 读镜像 textarea**：
   ```js
   document.querySelector('textarea[class*="-simulator"]').value   // 精确等于标题
   ```
   （本次实测：simulator 读到 24 字精确匹配，而同一时刻 innerText 还是 "\n"。）

2. **tab 在后台时（`document.visibilityState==='hidden'`），物理 `left_click` 对封面框完全无效**
   —— 不是点偏，是 modal 根本不挂载（点完 `document.querySelector('.cheetah-modal')` 返 null）。
   坐标是用 `getBoundingClientRect()` 现算的、`elementFromPoint` 也确认命中了图标 div，照样没反应。
   ✅ **破法：后台标签页下一律直接用 JS 派发五连事件序列，别浪费一个回合先试物理点击。**
   ```js
   for(const ev of ['pointerdown','mousedown','pointerup','mouseup','click'])
     el.dispatchEvent(new MouseEvent(ev,{bubbles:true,cancelable:true,composed:true,clientX:cx,clientY:cy,view:window}))
   ```
   → 这条把 08-06 那条「封面弹框**内**的按钮物理点击 100% 落空」的射程**扩大到封面框本身**：
     后台分页下，编辑页上的一切点击都该走 JS 派发。

3. **封面弹框节流第四次复现**（`cheetah-zoom-appear-active` + `opacity:0`，rect 仅 196×134）。
   08-19 记的省步走法**再次一次成功，现正式固化为默认流程**：
   **① navigate 后立刻打 rAF 补丁 → ②【跳过】派发 animationend → ③ 直接摘 class + 硬设 opacity。**
   摘完立刻 980×671、opacity=1，后续 AI封图 → 智能生成 → 确定(N) 全部一次通过。别再在 ② 上试。

**⚠️ 2026-08-20 发文前置检查（新增，因本日踩到）：正文要放深链前，先确认检索后端活着。**
`curl -s -m20 -o /dev/null -w "%{http_code}" "https://www.wenshucha.com/wscx/search?q=借款&size=1"`
返 502 / 或 `wsc_query.py` 裸查返 0 ⇒ **ES 不可达**（多半是 mini 192.168.31.241 掉出局域网，
见记忆 `reference_wscx_tunnel_outage_stale_listener`，只能物理上机唤醒）。
此时：**照发文（测量不阻塞发文），但① 全篇不许引任何数据库数字 ② 删掉导流深链** ——
把读者导去一个搜出来是空的页面，比不导更伤。⚠️ `wscx2/health` 返 200 是**假绿**，健康检查不碰 ES。

### 🚨 2026-08-20 止损线①的假阳性：别用 innerText 关键词扫「未通过」

本轮开工体检时用 `document.body.innerText.includes('未通过')` 扫止损线，**命中了**，
差点按「有文章未通过审核 → 当天停发」把整天停掉。

真相：`/builder/rc/content` 的**筛选标签栏本身就是**「全部 / 已发布 / 待发布 / **未通过** / 已撤回 / 草稿」，
这六个字永远在 DOM 里。同理「限流」「违规」这类词也可能来自帮助入口或规则中心链接。

**正确判据（唯一）**：点「未通过」标签（URL 变成 `collection=rejected`），读列表的「共 N 篇」。
本轮实测 `共0篇` ＝ 无未通过文章，止损线未触发。

```js
// 切到 rejected 后
document.body.innerText.match(/共\d+篇/)[0]   // '共0篇' = 干净
```

⚠️ 这条比看起来重要：**止损线是「停发一整天」的开关，假阳性的代价是当天产能归零**，
和 2026-08-17 那次「测量阻塞发文」的断更是同一类事故——**体检本身把主线掐了**。
凡是会导致停发的判据，一律要求「能点进去看到计数」，不接受关键词命中。

### 🔒 2026-08-20（11:30 轮）选词封口线：含「类案检索」四字的词整体废弃

本轮乾净真搜连毙 5 词，其中两个死于同一个结构，可以立规律了：

**规律一：凡搜索词里含「类案检索」四个字，一律被最高法《关于统一法律适用加强类案检索的
指导意见》的各级法院/检察院转载页占死。** 实测「执行案件怎么做类案检索」首页 6 条官方
（人民法院案例库帮助页、鄂伦春法院带「官方」标记、海门区检察院、开鲁县法院、鸡西中院、最高检），
加上我们自己 2 条已在首页 ⇒ **官方压顶＋自我竞争双杀**。
→ 挖检索场景词时**避开这四个字**，改用不带它的具体动作描述。

**规律二：我们自己已占首页 ≥2 条的语义簇＝写满，别再加篇。**
「类案检索报告要不要写不利判决」首页我们独占 4 条（2天前不利判决篇／3天前筛选篇／
7-22 报告篇／7天前仲裁篇）。类案检索报告线确认封口。
⚠️ 但**只占 1 条且答的是不同子问题时不算自我竞争** —— 本轮选中的「最近的判决为什么检索不到」
首页有我们 3 天前那篇（答检索式写法），本篇答时间分布与上网机制，判可做；
48h 后若阅读偏低，优先归因于此并把阈值收严到「自家在首页即毙」。

**规律三（复核 8/19 阈值，本轮再中一次）：顶部百度 AI 直答框/百科摘要把流程答完＝空位为零。**
「尽职调查怎么查企业的诉讼风险」顶部一整块百科来源 AI 摘要已答完全流程，
再加百度百科＋百度知道＋法行宝 ⇒ 百度自家 ≥4 条，命中 8/19 立的毙词阈值。**该阈值确认可用。**

**规律四：主结果 8 条无一在答本问题 ＝ 意图劫持，不是空位。**
「对方律师提交的判例怎么反驳」首页 8 条全在讲「法庭辩论话术怎么怼」，相关搜索全是
找律师/律师事务所/律师起诉流程。与 8/19 毙的「不同数据库检索结果不一样」同型死法。
⚠️ 与之相反的**可做**形态：主结果确实在答这件事、只是**视角是当事人**（本轮选中的词就是这种）——
那是真空位，因为办案人视角没人写。**「没人答」和「答了但视角不对」要分开判，前者毙后者做。**

## 🔴 回填阅读量的致命坑（2026-08-21 13:4x 实测发现）

**把 `pageSize` 调大以求一次读完，会让作品管理列表的六个统计数字全部渲染成 0。**

复现：`/builder/rc/content?pageSize=50` 读到的 08-18 那批全是 `0/0/0/0/0/0`；
同一批文章用默认 `pageSize=10` 逐页读，是 `8/14/1/2...`，**与 metrics.jsonl 里早先存的值完全一致**。
即大分页只渲染占位、不加载统计数据，**外观上完全看不出异常**。

后果：如果照着大分页的结果回填，会把整批文章写成 0 阅读，被引擎当成真实观测，
直接得出「内容没人看」的错误结论——和 2026-08-14 那次「回填跑早了」是同一种事故的不同成因。

**纪律：回填一律用默认 `pageSize=10` 逐页翻（currentPage=1,2,3...），不许图快改 pageSize。**
读完先拿一批已回填过的旧文对账，对得上才继续填新的。

## 正文改单句：innerHTML 替换会失效，必须整段 textContent 重设（2026-08-21）

UEditor 里 `p.innerHTML.replace(old,new)` 经常 `replaced=0`——文字在 innerHTML 里被标签和
零宽字符拆散，匹配不到。改法：
```js
const p=[...ed.document.querySelectorAll('p')].find(p=>p.innerText.includes('锚点句'));
p.textContent = 整段新文本;
ed.fireEvent('contentchange');
```
改完必须重跑逐段 diff 确认回到 diffCount=0。

## 选词：除「法条型答案」外，另有两类必毙词型（2026-08-21 连毙 5 词归纳）

1. **近期有新闻事件的概念** —— 「判决书上网哪些信息会被隐去」被「法官姓名隐去」事件劫持，
   光明网/南方都市报/上观/南方+/最高法官网把整个 SERP 吃干净。凡是行业里最近吵过的概念，
   官媒的报道会长期压制所有长尾内容，直接换词。
2. **动词用「统计 / 分析」** —— 百度会把它理解成「计算」，把专业检索意图劫持成当事人算钱意图。
   「判决书里的赔偿金额怎么统计」返回的全是「赔偿金怎么算」的律图/律临/法行宝。
   要表达数据分析的意思，改用「怎么筛」「怎么核」「怎么读」这类动作词。

---

## 2026-08-24 百家号编辑器：两条实测更正（省时间，优先照这条走）

**⚠️「正文在 iframe 内，JS 够不着，只能靠截图判落点」——部分作废。**
实测 `document.querySelector('iframe').contentDocument` **同源可直读**
（body `contenteditable=true`，class `view news-editor-pc`）。
⇒ 探针落点、逐段长度 diff、字数核验**全部可以用 JS 精确判**，
不必再依赖会骗人的「字数」计数器和会返回缓存旧帧的截图。
本轮据此做到 **34/34 段长度与源文逐段全等**后才点发布。

推荐核验片段：
```js
const d=document.querySelector('iframe').contentDocument;
const ps=d.body.innerText.split('\n').map(s=>s.trim()).filter(Boolean);
JSON.stringify({n:ps.length, lens:ps.map(p=>p.length)})   // 拿去和源文逐段比
```

**⚠️ 标题区：execCommand 会双写，且 selectNodeContents+delete 完全无效。**
`insertText` 之后再 `dispatchEvent(InputEvent)` 会让标题变成两遍；
`execCommand('delete')` 对这个 React 受控标题**连删三次纹丝不动**（反而累积到三遍）。
**唯一有效清空法＝真实键盘 cmd+a → Delete**（立刻回到 placeholder），然后**真实 type**，一次到位。

**⚠️ 探针残字：**「探针」两字用 cmd+a+Delete 清不干净，会残一个「针」被推到全文末尾。
处置＝**shift+Right 选中再 Delete**（单按 `Delete` 是退格，删不掉光标后面的字）。

**⚠️ hidden-tab（`document.hidden===true`）：**
截图会**长时间返回旧缓存帧**（点完发布看到的还是一分钟前的画面）；
伪造 `visibilityState/hidden=visible` **无效**。
但：**图库搜索必须用真实键盘 Enter 才会发请求**——合成 KeyboardEvent / 点搜索图标全部返回 0 结果，
换真实 click+type+Enter 后立刻返回 20 张图。
另：**模态框开着若干秒后截图会自行恢复实时**，所以遇 hidden-tab 先用 JS 读 DOM 顶住，隔一会儿再截图。

**⚠️ 封面是必填**：不设封面点发布只会弹「请添加封面」，不会提交。
AI 封面失败时的合规兜底＝**「免费正版图库」搜通用词选图**（本轮搜「办公」），
**不要碰被禁的「正文/本地上传」**。
判 AI 封面真失败的硬判据＝modal 内 fresh img 恒 0 张 + tab 无「AI封面(N)」计数 + 「生成失败」toast；
若 DOM 里其实已有图且 tab 变成 (1)，那是**假失败**，重开弹框即见图。

## 🎯 渠道归因（2026-08-24 建，Jack：「百度统计每天二三十访客，想知道从哪来」）

**为什么之前分不出来**：百家号正文**不允许放任何链接**，读者只能手打域名，
到站时 **referer 为空**，跟直接访问、书签、微信内打开完全混在一起。光看 referer 永远无解。

**三条通道，各用各的认法：**

| 渠道 | 能放链接？ | 认法 | 正文里写什么 |
|---|---|---|---|
| 知乎 | ✅ | 深链自带 `utm_source=zhihu`（`wsc_query.py` 已自动加） | 直接贴 `tob.wenshucha.com/cases?...&utm_source=zhihu` |
| **百家号** | ❌ | **专属短链** `/bjh` → 302 到 `/?utm_source=baijiahao` | 文末写「打开 wenshucha.com/bjh」 |
| 微信公众号 | 部分 | 短链 `/wx` | 同上 |

短链在 nginx `html_wenshucha.com.conf` 里，三条 `location =` 规则，不占页面不占部署。

**两个必须一起改的地方**（少一个就白设）：
1. 像素原来只记 `location.pathname`，302 之后的 utm 参数**记不到**。已改成 `pathname+search`。
2. `wsc_query.py` 输出的深链现在自动带 `utm_source`/`utm_medium`，**别再手工删**。

**看数**：百度统计「来源分析 → 全部来源」直接分渠道；我们自己的像素日志里
`p=` 参数带 utm，`traffic_report.py` 会拆出来。两套交叉验证。
