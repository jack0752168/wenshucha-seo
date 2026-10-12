#!/usr/bin/env python3
"""Notify Jack about durable research demands; never read QA receipts or email applicants."""
import fcntl
import json
from pathlib import Path
import smtplib
import ssl
import subprocess
import urllib.parse
import urllib.request
from email.message import EmailMessage

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state/report-demand-notified.json"
REMOTE = """import pathlib,json
out=[]
for p in pathlib.Path('/opt/wenshucha-leads/report').glob('*.json'):
 try:
  d=json.loads(p.read_text())
  if not (d.get('funnel') or {}).get('qa'):out.append(d)
 except ValueError:pass
print(json.dumps(out))"""

def send_telegram(text):
    try:
        auto = Path.home() / ".claude/automation"
        token = next((line.partition("=")[2].strip().strip("'\"") for line in (auto / "telegram.env").read_text().splitlines() if line.startswith("TELEGRAM_BRIDGE_TOKEN=")), "")
        chat = json.loads((auto / "telegram-bridge-state.json").read_text()).get("authorized_chat_id")
        if not token or not chat: return False
        body = urllib.parse.urlencode({"chat_id": chat, "text": text[:3800]}).encode()
        req = urllib.request.Request("https://api.telegram.org/bot" + token + "/sendMessage", data=body)
        reply = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return reply.get("ok") is True and bool((reply.get("result") or {}).get("message_id"))
    except Exception:
        # Exceptions can contain a token-bearing URL; never print them.
        return False

def send_email(receipt):
    try:
        import mcp_apply_notify as existing
        password = existing.smtp_pass()
        if not password: return False
        msg = EmailMessage(); msg["From"] = existing.ACCOUNT; msg["To"] = existing.TO
        msg["Subject"] = "[文書查] 新研究報告需求 · " + " ".join(receipt["topic"].split())[:90]
        msg.set_content("研究主題：" + receipt["topic"] + "\n身份：" + receipt["role"] + "\n學校／機構：" + receipt.get("institution", "") + "\n回覆郵箱：" + receipt["email"] + "\n需求：" + receipt["purpose"] + "\n時間範圍：" + receipt.get("timeframe", "") + "\n需求編號：" + receipt["id"])
        with smtplib.SMTP_SSL("smtp.exmail.qq.com", 465, context=ssl.create_default_context()) as client:
            client.login(existing.ACCOUNT, password); client.send_message(msg)
        # SMTP acceptance is not a recipient-delivery receipt.
        return True
    except Exception: return False

def process_new_report_demands(dry=False):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with (STATE.parent / "report-demand-notify.lock").open("a") as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return
        result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "root@114.132.74.235", "python3 -"], input=REMOTE, capture_output=True, text=True, timeout=45)
        if result.returncode: raise RuntimeError("report receipt queue unavailable")
        receipts = json.loads(result.stdout)
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        pending = [r for r in receipts if not state.get(r["id"], {}).get("telegram_confirmed")]
        if dry: print("研究需求通知預檢：待通知 " + str(len(pending)) + " 筆；測試佇列不讀取。"); return
        for receipt in receipts:
            status = state.setdefault(receipt["id"], {})
            if not status.get("telegram_confirmed"):
                text = "📄 文書查研究報告需求\n主題：" + receipt["topic"] + "\n身份：" + receipt["role"] + "\n學校／機構：" + receipt.get("institution", "") + "\n回覆郵箱：" + receipt["email"] + "\n需求編號：" + receipt["id"]
                status["telegram_confirmed"] = send_telegram(text)
            if not status.get("smtp_accepted"): status["smtp_accepted"] = send_email(receipt)
        temp = STATE.with_suffix(".tmp"); temp.write_text(json.dumps(state) + "\n"); temp.chmod(0o600); temp.replace(STATE)
        if pending: print("研究需求通知：" + str(sum(bool(state[r["id"]].get("telegram_confirmed")) for r in pending)) + "/" + str(len(pending)) + " 筆 Telegram 回執已核；SMTP 僅記受理，不當作送達。")
        if any(not state[r['id']].get('telegram_confirmed') or not state[r['id']].get('smtp_accepted') for r in receipts):
            raise RuntimeError("report notification incomplete; durable queue retained")

if __name__ == "__main__":
    import sys
    try: process_new_report_demands(dry="--dry" in sys.argv)
    except Exception:
        print("研究需求通知資料讀取失敗，未標記送達。")
        raise SystemExit(1)
