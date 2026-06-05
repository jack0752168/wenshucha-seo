#!/usr/bin/env python3
"""推送内容到飞书自定义机器人(免费 + 无限频次)

配置:
  1. 在飞书群组里:右上角 ⚙ → 群机器人 → 添加机器人 → 自定义机器人
  2. 起名(例:wenshucha-seo-bot)
  3. 拷贝 webhook URL(形如 https://open.feishu.cn/open-apis/bot/v2/hook/xxx)
  4. 写到 /opt/wenshucha-seo/secrets/feishu_webhook(chmod 600)

用法:
  python3 notify_feishu.py "标题" path/to/report.md
  python3 notify_feishu.py "标题"  < some.md
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEBHOOK_FILE = ROOT / "secrets" / "feishu_webhook"

# 飞书 lark_md 内容长度上限约 30000 字符
MAX_CONTENT_LEN = 28000


def push_card(title: str, content: str, template: str = "blue") -> int:
    """推送富文本卡片(支持 markdown)"""
    if not WEBHOOK_FILE.exists():
        print("⏭️  飞书推送跳过:secrets/feishu_webhook 不存在(Jack 还没配 webhook URL)")
        return 0

    webhook_url = WEBHOOK_FILE.read_text().strip()
    if not webhook_url.startswith("https://open.feishu.cn/"):
        print(f"⚠️  飞书 webhook URL 格式异常: {webhook_url[:60]}")
        return 1

    if len(content) > MAX_CONTENT_LEN:
        content = content[:MAX_CONTENT_LEN] + "\n\n... (内容过长,已截断,完整版见 Lighthouse `/opt/wenshucha-seo/reports/weekly/`)"

    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": template,  # blue / green / orange / red
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content}},
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "lark_md",
                            "content": "🤖 wenshucha-seo · 自动生成 · 部署在腾讯云 Lighthouse",
                        }
                    ],
                },
            ],
        },
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8", errors="replace"))
            # 飞书成功返回 {"code": 0, "msg": "success"} 或 {"StatusCode": 0}
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print(f"✓ 飞书推送 OK: {title[:40]}")
                return 0
            print(f"✗ 飞书推送返回非成功: {result}")
            return 1
    except urllib.error.HTTPError as e:
        print(f"✗ 飞书推送 HTTP {e.code}: {e.read()[:200]}")
        return 1
    except Exception as e:
        print(f"✗ 飞书推送异常: {e}")
        return 1


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    title = sys.argv[1]
    if len(sys.argv) >= 3:
        content_path = Path(sys.argv[2])
        if not content_path.exists():
            print(f"内容文件不存在: {content_path}")
            return 1
        content = content_path.read_text(encoding="utf-8", errors="replace")
    else:
        content = sys.stdin.read()

    # 根据 title 关键词自动选模板色
    template = "blue"
    title_low = title.lower()
    if any(w in title_low for w in ("告警", "critical", "🔥", "异常", "fail")):
        template = "red"
    elif any(w in title_low for w in ("warn", "⚠️", "提醒")):
        template = "orange"
    elif any(w in title_low for w in ("ok", "✓", "成功", "周报", "📊")):
        template = "green"

    return push_card(title, content, template)


if __name__ == "__main__":
    sys.exit(main())
