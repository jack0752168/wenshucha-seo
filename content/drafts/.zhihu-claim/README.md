# 知乎回答区抢占锁（2026-09-04 建）

## 为什么存在
answers API 只反映**已入库**状态，而撞车发生在**入库之前那 15-30 分钟的写稿窗口**里。
- 2026-08-19：主控手写一篇，发现引擎 20 分钟前已答同题，整篇白写。
- 2026-09-04 10:1x：本引擎 10:12 拉清单判 ems-songda 可留后，另一 runner 10:17:25 就把它发了。
  零损失纯属两边挑了不同题，不是机制起作用。

## 用法
动笔前：`touch .zhihu-claim/<qid>`（写入时间戳），发布成功后 `rm`。
开工时：扫本目录，**30 分钟内被占的 qid 直接跳过**（30 分钟＝一篇稿的写作耗时上界）。
过期锁（>2h）视为死锁，可清理。

```bash
# 开工扫描
find ~/wenshucha-seo/content/drafts/.zhihu-claim -type f -name '[0-9]*' -mmin -30
# 清死锁
find ~/wenshucha-seo/content/drafts/.zhihu-claim -type f -name '[0-9]*' -mmin +120 -delete
```

## 边界
本机制**不改任何投递闸门**（CAP、滚动 7×24h 窗口、30 答闸门一律不动），
只防两个 runner 同时写同一题。零副作用，不认它的 runner 直接忽略即可。

## 两种锁（2026-09-04 补）
- **写稿锁** `state` 缺省：动笔时 touch，**30 分钟未转 banked 视为死锁**可清理。
- **银行锁** `state=banked`：稿子已成型待发，**不过期**，直到发布成功才删。
  09-04 的 ems 撞车正发生在银行队列上——成稿到发布之间可能隔一整天，写稿锁的 30 分钟盖不住。

```bash
# 开工扫（写稿锁 30 分钟内 + 全部银行锁）
grep -L 'state=banked' ~/wenshucha-seo/content/drafts/.zhihu-claim/[0-9]* 2>/dev/null | xargs -I{} find {} -mmin -30
grep -l 'state=banked' ~/wenshucha-seo/content/drafts/.zhihu-claim/[0-9]* 2>/dev/null
```
