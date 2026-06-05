#!/usr/bin/env python3
"""推送内容到 Telegram bot(免费、可靠、全球可达)

配置:
  /opt/wenshucha-seo/secrets/telegram_bot_token   # bot token(从 @BotFather 拿)
  /opt/wenshucha-seo/secrets/telegram_chat_id     # 接收者 chat_id(Jack 个人 ID)

用法:
  python3 notify_telegram.py "标题" path/to/report.md
  echo "内容" | python3 notify_telegram.py "标题"
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / "secrets" / "telegram_bot_token"
CHAT_FILE = ROOT / "secrets" / "telegram_chat_id"

# Telegram 单条消息最长 4096 字符
MAX_LEN = 4000


def send(title: str, body: str) -> int:
    if not TOKEN_FILE.exists() or not CHAT_FILE.exists():
        print("⏭️  Telegram 跳过:secrets/telegram_bot_token 或 telegram_chat_id 未配置")
        return 0

    token = TOKEN_FILE.read_text().strip()
    chat_id = CHAT_FILE.read_text().strip()

    # 拼标题 + 正文(MarkdownV2 转义麻烦,这里用普通 Markdown 模式,可读性更好)
    text = f"*{title}*\n\n{body}"
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN] + "\n\n_…内容过长已截断,完整版见 Lighthouse `/opt/wenshucha-seo/reports/`_"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8", errors="replace"))
            if result.get("ok"):
                print(f"✓ Telegram OK: {title[:50]}")
                return 0
            print(f"✗ Telegram 返回非 ok: {result}")
            return 1
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")[:300]
        print(f"✗ Telegram HTTP {e.code}: {body_err}")
        # Markdown 解析失败时回退成纯文本重试一次
        if "can't parse" in body_err.lower() or "bad request" in body_err.lower():
            print("  → 回退纯文本重试")
            payload.pop("parse_mode", None)
            req2 = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req2, timeout=20) as resp:
                    if json.loads(resp.read()).get("ok"):
                        print("✓ Telegram 纯文本回退 OK")
                        return 0
            except Exception as e2:
                print(f"✗ 回退也失败: {e2}")
        return 1
    except Exception as e:
        print(f"✗ Telegram 异常: {e}")
        return 1


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    title = sys.argv[1]
    if len(sys.argv) >= 3:
        p = Path(sys.argv[2])
        if not p.exists():
            print(f"文件不存在: {p}")
            return 1
        body = p.read_text(encoding="utf-8", errors="replace")
    else:
        body = sys.stdin.read()

    return send(title, body)


if __name__ == "__main__":
    sys.exit(main())
