#!/usr/bin/env python3
"""从知乎草稿 md 抽出 {title, body[]} 供自动发布用

为什么要这个(2026-08-14):
  19 篇积压稿是七月至今不同批次写的,标题位置有两种写法:
    A) `## 标题（…）` 段落下第一个 **加粗行** = 真标题
    B) 文件首行 `# 真标题`（08-10 之后的新格式）
  正文一律从 `## 正文` 之后开始;没有 `## 正文` 的,从标题行之后开始。
  自查块/发布前确认/备选标题/元信息(> 引用行、**平台**、**台账词**)全部剔除。

  ⚠️ 知乎是 Draft.js,正文靠 paste 事件注入,段落用 \n 分隔 —— 所以这里输出的是
     纯文本段落数组,不能带 markdown 标记(** 会原样显示)。

用法: python3 zhihu_extract.py <draft.md>   → stdout 输出 JSON
"""
import json
import re
import sys
from pathlib import Path

# 这些整行直接丢弃(元信息,不是正文)
DROP_LINE = re.compile(
    r"^\s*[-*+]?\s*"                                   # 允许列表符前缀
    r"(>|\||---+\s*$|===+\s*$|<!--"
    r"|\*{0,2}(平台|台账词?|状态|建议投递形式?|投递形式|发布状态|落点|同话题不同角度)\*{0,2}\s*[:：]"
    r"|\*{0,2}待\s*Jack|\*{0,2}待手动贴|手动贴到)"
)
# 少数新格式草稿带显式界标,优先用它(最干净)
BODY_MARK_START = re.compile(r"<!--\s*BODY-START\s*-->")
BODY_MARK_END = re.compile(r"<!--\s*BODY-END\s*-->")
# 这些小节标题出现后,整节丢到下一个同级/更高级标题为止
DROP_SECTION = re.compile(r"^#{2,4}\s*(备选标题|自查|发布前|交付|⚠️)")
# 正文起点
BODY_START = re.compile(r"^#{1,3}\s*正文\s*$|^=+\s*BODY\s*=+\s*$")
TITLE_SECTION = re.compile(r"^#{1,3}\s*标题\s*$|^#{1,3}\s*标题（")


def strip_md(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)          # 去粗体
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", s)  # 去斜体
    s = re.sub(r"`(.+?)`", r"\1", s)                 # 去行内代码
    s = re.sub(r"\[(.+?)\]\([^)]*\)", r"\1", s)      # 去链接,只留文字
    s = re.sub(r"^\s*[-*+]\s+", "", s)               # 去无序列表符
    s = re.sub(r"^\s*\d+[.、]\s+", "", s)            # 去有序列表符
    return s.strip()


def parse(path: Path):
    raw_text = path.read_text(encoding="utf-8")
    lines = raw_text.split("\n")
    title, body = None, []
    in_title_sec = False
    in_body = False
    skipping = False

    # 有显式界标就只吃界标之间的内容
    has_marks = bool(BODY_MARK_START.search(raw_text))
    if has_marks:
        seen_start = False
        for raw in lines:
            s = raw.strip()
            if BODY_MARK_END.search(s):
                break
            if BODY_MARK_START.search(s):
                seen_start = True
                continue
            if title is None and re.match(r"^#\s+", s):
                t = strip_md(re.sub(r"^#\s+", "", s))
                if not re.match(r"^【?知乎", t):
                    title = t
                continue
            if not seen_start or not s or DROP_LINE.match(s):
                continue
            out = strip_md(re.sub(r"^#{1,6}\s*", "", s))
            if out:
                body.append(out)
        return {"title": title, "body": body}

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()

        if DROP_SECTION.match(s):
            skipping = True
            continue
        if skipping:
            # 遇到下一个 ## 级标题就退出丢弃模式
            if re.match(r"^##\s", s) and not DROP_SECTION.match(s):
                skipping = False
            else:
                continue

        if BODY_START.match(s):
            in_body, in_title_sec = True, False
            continue
        if TITLE_SECTION.match(s):
            in_title_sec = True
            continue

        if not s or DROP_LINE.match(s):
            continue

        # 标题：优先取 ## 标题 段里的第一个加粗行
        if in_title_sec and title is None:
            m = re.match(r"^\*\*(.+?)\*\*$", s)
            if m:
                title = m.group(1).strip()
                continue
            if not s.startswith("#"):
                title = strip_md(s)
                continue

        # 文件首行 # 真标题（新格式）
        if title is None and re.match(r"^#\s+", s):
            t = strip_md(re.sub(r"^#\s+", "", s))
            if not re.match(r"^【?知乎", t):     # 排除 "【知乎 · date】slug" 这种文件头
                title, in_body = t, True
            else:
                # 2026-09-01 修:文件头行只是「不当标题」,不该顺带把正文闸门关死。
                # 旧版这里直接 continue,in_body 永远 False,后面每一行都被
                # `if not in_body: continue` 丢掉 => body=[] => product_gate 报
                # 「大数 0 个」把好稿判成废稿(08-27 zhihu-xingzheng-anli-nazhao
                # 实际有 13 个大数/4 个筛选项,被误杀 5 天)。
                # 括号里通常是真标题,能取就取。
                mt = re.search(r"[（(]([^（()）]{4,60})[）)]\s*$", t)
                if mt:
                    title = mt.group(1).strip()
                in_body = True
            continue

        if not in_body:
            continue
        if re.match(r"^#{1,6}\s", s):            # 正文里的小节标题 → 变成普通段落
            body.append(strip_md(re.sub(r"^#{1,6}\s*", "", s)))
            continue

        out = strip_md(s)
        if out:
            body.append(out)

    return {"title": title, "body": body}


# 只写给我们自己看的运维词 —— 出现在正文里就是穿帮,见 lint() 第 ③ 条
OPS_NOTE_RE = re.compile(
    r"⏳|✅\s*(已|08-|09-|1[0-2]-)|runner|PUBLISH-LOG|wsc_query\.py|"
    r"未入库|已入库|两头落空|重灌重发|本轮跳过|待复核|投递(成功|失败|中)|"
    r"纯度体检(脚本|已)|草稿箱"
)


def lint(body):
    """发布前硬校验 —— 命中就 exit 3,绝不带病发布

    ① URL 里有空格:2026-08-18 实测,知乎自动识链在第一个空格处截断,
       href 只剩第一个关键词,后半段变成裸文字垃圾。深链必须原样复制
       wsc_query.py 输出的那一行(urlencode 过,空格是 +)。
    ② 残留 markdown 记号:paste 注入是纯文本,** 会原样显示出来。
    ③ 运维注记混进正文:2026-08-21 实测,.md 文件尾部那行
       「⏳ 08-21 两次投递…至 10:37 仍未入库」被当成正文抽了出来,
       lint 照样 exit 0,差点连这句一起发到知乎上。凡是只写给我们自己看的
       状态/排期/runner 字眼,一律不许进正文。
    """
    errs = []
    for i, b in enumerate(body):
        if OPS_NOTE_RE.search(b):
            errs.append(f"[{i}] 运维注记混进正文,只写给我们自己看的话不许发: {b[:60]}")
        for m in re.finditer(r"https?://\S*", b):
            # \S* 本身不会跨空格,所以要看 URL 后面紧跟的是不是「空格+非中文标点」
            tail = b[m.end():m.end() + 2]
            if tail.startswith(" ") and tail[1:2] not in ("", "。", "，", "、"):
                errs.append(f"[{i}] URL 后接空格,知乎会截断: {b[:60]}")
        if "**" in b or re.search(r"\[[^\]]+\]\(", b):
            errs.append(f"[{i}] 残留 markdown 记号: {b[:60]}")
    return errs


def product_gate(body):
    """产品演示硬闸门 —— 2026-08-18 Jack 三次强调:「一定要体现我们的数据跟类案检索，
    要不然跟普通 AI 回答没区别」。冲量的时候最容易掉的就是这条,所以做成 exit 4,绕不过去。

    批量的正确切法是分两层:
      · **案由基线可复用**(二审占比/判决书:裁定书/地域分布)—— 同案由答多题时不必重跑,
        而且横向对比表本身就是资产
      · **每题的收窄链和案号必须当场跑** —— 这是"把产品操作一遍"的实质,不能复用

    所以闸门只查后者:有没有真的逐层收窄、有没有新鲜案号、有没有可点深链。
    """
    txt = "\n".join(body)
    errs = []

    # ① 逐层收窄:至少 3 个带千分位的大数(把筛选面板一项项按下去的证据)
    nums = re.findall(r"\b\d{1,3}(?:,\d{3})+\b", txt)
    if len(nums) < 3:
        errs.append(f"只有 {len(nums)} 个带千分位的数 —— 没有逐层收窄的痕迹,"
                    f"这就是「普通 AI 回答」。必须写清每加一个筛选项还剩多少条")

    # ② 筛选项名字:证明是在操作产品,不是在背法条
    filters = [w for w in ("案由", "案件类型", "近三年", "近三", "隐藏公告",
                           "审理程序", "地域", "省份", "聚合") if w in txt]
    if len(filters) < 3:
        errs.append(f"只提到 {len(filters)} 个筛选项{filters} —— 至少 3 个,"
                    f"否则看不出是在用类案检索")

    # ③ 真实案号:(2024)闽0505民初41号 这种
    cases = re.findall(r"[（(]\s*20\d{2}\s*[)）]\s*[\u4e00-\u9fa5]{0,3}\d{2,4}[\u4e00-\u9fa5]{1,4}\d+\s*号", txt)
    if not cases:
        errs.append("没有一个真实案号 —— 案号是「数据是真的」最硬的证据,必须带")

    # ④ 可点深链
    if "tob.wenshucha.com/cases?" not in txt:
        errs.append("没有深链 —— 读者没法自己复现,产品演示不闭环")

    # ⑤ 数据边界(唯一不轮换的结构):不许把分布说成胜诉率
    # 边界声明:2026-08-19 放宽 —— 原来只认「不是胜诉率/上界/给不出」几个词,
    # 把一篇真写了边界段的稿子误判成没写。改成「命中 ≥2 个边界语汇」,
    # 既不误伤,也拦得住真的没写的。
    BOUND = ("不是胜诉率", "不是支持率", "上界", "做不到", "给不出", "数据边界",
             "不完全等于", "查不到不等于", "分母", "不是法律意见", "只有已公开",
             "公开率", "不等于现实", "观察不是统计")
    hit = [w for w in BOUND if w in txt]
    if len(hit) < 2:
        errs.append(f"边界声明不足(只命中 {hit}) —— 每篇必须说清这些数不能证明什么,"
                    f"这是我们和「张口就来」的唯一区别")

    return errs, {"nums": len(nums), "filters": filters, "cases": len(cases)}


if __name__ == "__main__":
    r = parse(Path(sys.argv[1]))
    # 2026-09-01 加:解析拿到空正文 = 格式没被识别,不是「稿子没数据」。
    # 必须在这里断掉,否则 product_gate 会把它报成「大数 0 个/筛选项 0 个」,
    # 读起来跟「这稿真的没数据」一模一样,直接导致误杀。
    if not r["body"]:
        print("❌ 解析失败(exit 5):正文为空,说明这份 md 的格式没被 parse 识别,"
              "**不是**稿子没数据。", file=sys.stderr)
        print("   排查:首行是否为 `# 真标题`(以「知乎」开头的会被当文件头)、"
              "有没有 `## 正文` 或 <!-- BODY-START --> 界标。", file=sys.stderr)
        sys.exit(5)
    errs = lint(r["body"])
    if "--no-gate" not in sys.argv:
        gerrs, stat = product_gate(r["body"])
        if gerrs:
            print("❌ 产品演示闸门不通过(exit 4),这篇跟普通 AI 回答没区别:", file=sys.stderr)
            for e in gerrs:
                print("   · " + e, file=sys.stderr)
            print(f"   实测: 大数 {stat['nums']} 个 / 筛选项 {stat['filters']} / 案号 {stat['cases']} 个",
                  file=sys.stderr)
            sys.exit(4)
    if errs:
        print("❌ 发布前校验不通过,禁止注入:", file=sys.stderr)
        for e in errs:
            print("   " + e, file=sys.stderr)
        sys.exit(3)
    r["n"] = len(r["body"])
    r["chars"] = sum(len(x) for x in r["body"])
    print(json.dumps(r, ensure_ascii=False))
