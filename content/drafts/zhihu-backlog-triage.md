# 知乎积压三堆分类表（2026-09-04 14:1x 首次落盘 / 17:1x 判据修订 / **18:2x 线上核对定稿**）

> ⚠️ **2026-09-04 18:2x 全量线上核对已完成，本表以此版为准。**
> 核对方式（可复现）：`/api/v4/creators/creations/v2/answer` 与 `.../v2/article` 各翻完全部 offset，
> 拿到线上 **回答 83 篇（qid 全集）+ 专栏 78 篇（标题全集）**，再与本地稿件的 qid / 标题（标点归一化 + 6-gram 模糊）逐条比。
> 结果：**17:1x 版的「真实可发池 ≈ 28 篇」高估了**，真实可发 **19 篇**；而且——
> 🔴 **其中回答区能用的只有 2 篇**，另外 17 篇全是专栏稿。**「不缺稿」这个说法只对专栏成立，对回答区不成立。**

## 结论（2026-09-04 18:2x 线上核对定稿）

| 堆 | 数量 | 处置 |
|---|---|---|
| 已回填 URL（确认已发） | 133 | 不动 |
| ③a 确认已发·已回填 | 21 | 不动，禁重发 |
| **本轮新查出的「假待发·实为已发」** | **8**（③b 里 6 ＋ ① 队列里 2） | 已回填落点 + 标禁重发 |
| **永久判死（同 qid 已被自己的 v2 占位 / lint 废稿 / 养号期老稿）** | **4** | 从积压计数永久剔除 |
| **① 真·待发（全部专栏型）** | **9** | 专栏通道清，不占回答区 CAP |
| **③b 真·待发** | **10**（专栏 8 ＋ **回答 2**） | 已逐篇标 🟢 可发 |
| **⇒ 真实可发池** | **19**（专栏 **17** ／ **回答区 2**） | — |

### 🔴 本轮最重要的一条：回答区稿件银行只剩 2 篇

- `2026-09-01/zhihu-shumingquan-fanxiang.md` — qid 2076663408166966037（署名权反向侵权）🟢 已核对未答
- `2026-09-02/zhihu-yiqi-xingshi-vs-jicheng.md` — qid 2078443662854330253（遗弃：判刑 vs 分遗产）🟢 已核对未答

明日 CAP=5 ⇒ **现成稿只够 2 篇，另外 3 篇必须当天现写**。
17:1x 版写的「下周不会缺稿；『没稿可发』这个理由从现在起不成立」——**在回答区口径下不成立，须按本节修正**。

## 本轮查实的「假待发·实为已发」8 篇（已全部回填落点并标禁重发）

| 稿件 | qid | 线上 aid | 入库时刻(UTC+8) |
|---|---|---|---|
| 2026-08-23/zhihu-answer-2042244409325008348 | 2042244409325008348 | 2075617224887363413 | 08-25 16:15:09 |
| 2026-08-27/zhihu-qisuzhuang-panli | 447673785 | 2076345933902759567 | 08-27 16:30:47 |
| 2026-08-27/zhihu-tinghou-buchong-zhizheng | 2602752341 | 2076330605806208839 | 08-27 15:29:52 |
| 2026-08-28/zhihu-lvshi-leian-jiansuo-mianfei | 533808857 | 2076623269608929060 | 08-28 10:52:49 |
| 2026-09-01/zhihu-xingzheng-anli-nazhao-v2 | 326881877 | 2078081102254716556 | 09-01 11:25:43 |
| 2026-09-02/zhihu-jiansuo-xingjiabi-v2 | 509090966 | 2078410489198129579 | 09-02 09:14:35 |
| **① 队列第10位** 2026-08-29/zhihu-answer-2066810497647769273 | 2066810497647769273 | 2076979093875201610 | 08-29 10:26:44 |
| **① 队列第11位** 2026-08-29/zhihu-answer-2075543153524879693 | 2075543153524879693 | 2076986241057407470 | 08-29 10:55:08 |

> ⚠️ 最后两条是本轮的**真实避损**：它们被 17:1x 版排在 ①「真·待发」队列第 10、11 位，
> 而且稿件头部还写着「⚠️发前须重探题目热度与是否已答」——按队列顺序取稿就会重投，
> 而知乎一人一题只能一条，重投＝覆盖自己 08-29 已入库的回答，是净损失。
> ⇒ **教训固化：① 队列同样不可信，任何回答型稿件投递前都必须用 qid 打一次线上 qid 全集比对。**

## 永久判死 4 篇（从积压计数剔除）

- `2026-08-27/zhihu-jiansuo-xingjiabi.md` — qid 509090966 已被自己的 **v2**（09-02 09:14 入库）占位
- `2026-08-27/zhihu-xingzheng-anli-nazhao.md` — qid 326881877 已被自己的 **v2**（09-01 11:25 入库）占位
- `2026-09-01/zhihu-noncompete-penalty.md` — lint **exit 4** 废稿
- `batch01/zhihu-01-hallucination.md` — 养号期老模板，且选题已在实测打不动词表

## ① 真·待发队列（**线上核对后剩 9 篇，全部专栏型**，按最早优先）

2. ~~2026-08-24/zhihu-db-account-sharing.md~~ — ✅ **09-04 15:28:34 已清** → https://zhuanlan.zhihu.com/p/2079229014946866968
3. 2026-08-24/zhihu-expert-opinion-cross-exam.md — 质证意见判决书一字不提
4. 2026-08-25/zhihu-zhongcai-buggongkai.md — 仲裁裁决查不到，制度上为什么不给看
5. 2026-08-26/zhihu-judge-past-rulings.md — 查了法官过往判决仍猜不到结果
6. 2026-08-26/zhihu-judge-questions-in-court.md — 法官庭上会问什么
7. 2026-08-27/zhihu-jianshe-gongcheng-jine.md — 建设工程金额三条计价路径
8. 2026-08-27/zhihu-labor-arbitration-survivorship.md — 劳动争议调解结案的幸存者偏差
9. 2026-08-27/zhihu-leian-baogao-wu-huiying.md — 检索报告法官不回应
10. ~~2026-08-29/zhihu-answer-2066810497647769273.md~~ — ⛔ **实为已发**（aid 2076979093875201610，08-29 10:26:44），2026-09-04 18:2x 线上核对查出，已移出队列
11. ~~2026-08-29/zhihu-answer-2075543153524879693.md~~ — ⛔ **实为已发**（aid 2076986241057407470，08-29 10:55:08），同上，已移出队列
12. 2026-09-01/zhihu-mingyuquan-yangben.md — 名誉权案件池子长得不一样
13. 2026-09-03/zhihu-caichan-xiansuo.md — 赢了拿不到钱，问题不在执行阶段

全部为完整成稿，主题均可拿干净数，**没有一篇属于管辖/程序性不可净化族**（09-02 判死的 `2026-08-18/zhihu-jurisdiction-objection.md` 已不在无 URL 列表内，无需再处理）。

## ② 判死剔除（1 篇）

- `batch01/zhihu-01-hallucination.md` — 养号期（8/5 前）老草稿模板，且「法律AI幻觉怎么防」已列入 SKILL 的实测打不动词表。**永久剔除，不再计入积压。**

## ③ 原「已发未回填 40 篇」—— 2026-09-04 17:1x **判据被推翻，已重跑**

⛔ **旧版这一节的结论「这 40 篇一律不许重发」是错的，别再照它行事。**
旧判据＝「文件名在 PUBLISH-LOG 出现过就算已发」。但日志里提到文件名的场合还包括
「⏸️未投递」「CAP 打满入银行队列」「积压清单」「lint 否决」——于是把大量**从未发出**的成稿
误判成已发并冻结。实锤三例：
- `2026-09-03/ems-songda-gonggao` 旧版判「已发不许重发」，实际 09-03 日志写的是「未投递·抢首答仍在」
- `2026-09-01/noncompete-penalty` 旧版判「已发」，实际是 lint **exit 4** 的废稿（该进②不是③）
- `2026-09-03/gongshang-siliao` 反向：文件名匹配不到发布行（发布行只写标题＋qid），靠 qid 才认出 09-04 08:15 已发

**新判据（可复现，别再用文件名 grep）**：
1. PUBLISH-LOG 结构化发布行 = 行首日期 `|` (可选状态) `|` 知乎专栏/回答 `|` **19位id**，第三列是 `—` 的一律不算发布；
2. 文件名匹配不到时，用稿件头部的 **qid** 去发布行第三列命中；
3. 两条都不中 → **不能判已发**，进下面的「待线上核对」。

### ③a 确认已发（21 篇）—— 已把 id 与链接回填进稿件头部「✅ 已发布落点」，禁重发
bangxin-yinhangka、beijichengren-zhaiwu、xukai-jieshao、qitacaichan-guinvfang、
fahuichongshen-tongantongpan、renshenshanghai-yiliaofei、wangke-zhuanmai-banquan、
jiabanfei-jishu-shijia、tiaodian-shanghai、yiwai-shoushang-tanpan、gongzhonghao-toushu-shanwen、
loupan-zhengyijiaodian、zangkuan-zhuihui-disanren、ems-songda-gonggao、fuqi-gongtong-caichan、
fuyangfei-zhixing、shiyongqi-buzhuanzheng、wugongfei-linggong、gongshang-qiye-bufu、
zhuangsi-shengchu-anyou-cuowei、gongshang-siliao

### ③b 原「无任何发布行证据 19 篇」—— 2026-09-04 18:2x 线上核对已拆完

**✅ 实为已发（6 篇）**：answer-2042244409325008348、qisuzhuang-panli、tinghou-buchong-zhizheng、
lvshi-leian-jiansuo-mianfei、xingzheng-anli-nazhao-v2、jiansuo-xingjiabi-v2 —— 见上表，已回填、禁重发。

**⛔ 判死（3 篇）**：jiansuo-xingjiabi(v1)、xingzheng-anli-nazhao(v1)、noncompete-penalty。

**🟢 真·待发（10 篇，已逐篇在稿件头部标记）**：
- **回答型 2 篇（回答区唯一存货）**：2026-09-01/shumingquan-fanxiang（qid 2076663408166966037）、
  2026-09-02/yiqi-xingshi-vs-jicheng（qid 2078443662854330253）
- **专栏型 8 篇**（标题已与线上 78 篇全集精确 + 6-gram 模糊双比，零命中）：
  2026-08-21/jiansuo-tisu-zhenxiang、2026-08-24/ai-legal-search-prompt、2026-08-24/db-result-mismatch、
  2026-08-25/conflict-check-search、2026-08-25/precedent-into-brief、2026-08-25/wuzui-shaojian、
  2026-08-25/xingshi-yuejuan、2026-09-01/minjian-jiedai-duandai

⚠️ 语义近题提醒（不是重复，但选题时别撞车）：`db-result-mismatch`（「为什么爱比收录量」）
与线上已发《厂商说数据库收录了上亿篇判决，这个数字对办案到底有多大意义？》主题高度重叠，
发之前先改角度或直接降优先级。

## 维护规则

- 每轮从 ① 顶部取 2 篇发；① 取空后从 ③b 取，取前先做线上核对。
- 发完把该行移到「已清」区并回填 URL 到稿件头部。
- **禁止再用文件名 grep 判定发布状态**，一律走上面的新判据。
- 🔴 **任何回答型稿件投递前，必须先拉线上 qid 全集比对**（① 队列也不例外，本轮就是在 ① 队列里查出 2 篇已发的）。
  端点：`/api/v4/creators/creations/v2/answer?offset=N&limit=20&sort_field=created&order_field=DESC`，
  取 `data[].data.question_id`（注意是嵌套的 `.data`，直接取 `x.question_id` 会全 undefined）；
  专栏用同路径的 `.../v2/article`，取 `data[].data.title`。

## 已清

- 2026-09-04 14:5x｜`2026-08-24/zhihu-ai-win-rate-denominator.md`｜《法律AI给出的「胜诉率72%」，这个数到底是怎么算出来的？》｜https://zhuanlan.zhihu.com/p/2079215679132137225
- 2026-09-04 15:28｜`2026-08-24/zhihu-db-account-sharing.md`｜https://zhuanlan.zhihu.com/p/2079229014946866968

---

## 🔵 09-05 回答区银行队列（2026-09-04 20:3x 复核后定稿，覆盖 18:1x 版的「只够 2 篇」）

18:1x 那轮写的「回答区真实可发仅 2 篇 ⇒ 明日 CAP=5 有 3 篇要当天现写」**已过时**，
原因是它只核到 09-03 及以前的积压，**没算 09-04 当天新写的两篇回答区稿**（它们不在积压队列里，
是当天 CAP 打满后预写落盘的银行稿）。本轮把 `.zhihu-claim/` 的银行锁和 `2026-09-04/` 目录逐个对上后，
真实队列是 **5 篇，正好够 CAP=5**：

| # | qid | 题 | 稿件 | 状态 |
|---|---|---|---|---|
| 1 | 2078488303683252960 | 社保补缴导致的税后工资差额追索，是否属于法院受理范围？ | `2026-09-04/zhihu-shebao-shuihou-gongzi.md` | 🟢 成稿+inject，锁 state=banked |
| 2 | 2057905728803828497 | 一审判决后公司换法人，如何追讨欠款？ | `2026-09-04/zhihu-zhuijia-gudong-zhixing.md` | 🟢 成稿，锁**本轮补标 state=banked** |
| 3 | 2076663408166966037 | 署名权反向侵权 | `2026-09-01/zhihu-shumingquan-fanxiang.md` | 🟢 已核对未答 |
| 4 | 2078443662854330253 | 遗弃：判刑 vs 分遗产 | `2026-09-02/zhihu-yiqi-xingshi-vs-jicheng.md` | 🟢 已核对未答 |
| 5 | 2078767506643339017 | 诈骗罪为什么这么难立案？ | `2026-09-04/zhihu-zhapian-lian.md` | 🟢 **本轮新写**，92段/3,219字，SHA-1 `c4cdf397…`，锁 state=banked |

⚠️ 五篇**发布前仍须逐篇重探回答数（过 30 闸门）+ 拉 answers API 撞车核对**——
本轮就实测到题库把一篇已答的标成「🟢 待答」（qid 2076317353931957552），
🟢 标记本身不能当发布许可。

### 🔧 本轮修掉的一个锁机制 BUG

`.zhihu-claim/2057905728803828497` 稿子 12:16 就成型了，锁却一直没有 `state=banked`。
按 README 的「写稿锁 30 分钟未转 banked 视为死锁可清理」，它在 12:46 之后就是可被清理的死锁——
**成稿会失去撞车保护，另一 runner 可以合法地重写同一题**。已补标 banked。
⇒ **规则补充：稿子一落盘就必须立刻把锁转 banked，不能等到发布日。**
