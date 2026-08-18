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


def lint(body):
    """发布前硬校验 —— 命中就 exit 3,绝不带病发布

    ① URL 里有空格:2026-08-18 实测,知乎自动识链在第一个空格处截断,
       href 只剩第一个关键词,后半段变成裸文字垃圾。深链必须原样复制
       wsc_query.py 输出的那一行(urlencode 过,空格是 +)。
    ② 残留 markdown 记号:paste 注入是纯文本,** 会原样显示出来。
    """
    errs = []
    for i, b in enumerate(body):
        for m in re.finditer(r"https?://\S*", b):
            # \S* 本身不会跨空格,所以要看 URL 后面紧跟的是不是「空格+非中文标点」
            tail = b[m.end():m.end() + 2]
            if tail.startswith(" ") and tail[1:2] not in ("", "。", "，", "、"):
                errs.append(f"[{i}] URL 后接空格,知乎会截断: {b[:60]}")
        if "**" in b or re.search(r"\[[^\]]+\]\(", b):
            errs.append(f"[{i}] 残留 markdown 记号: {b[:60]}")
    return errs


if __name__ == "__main__":
    r = parse(Path(sys.argv[1]))
    errs = lint(r["body"])
    if errs:
        print("❌ 发布前校验不通过,禁止注入:", file=sys.stderr)
        for e in errs:
            print("   " + e, file=sys.stderr)
        sys.exit(3)
    r["n"] = len(r["body"])
    r["chars"] = sum(len(x) for x in r["body"])
    print(json.dumps(r, ensure_ascii=False))
