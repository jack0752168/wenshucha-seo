#!/usr/bin/env python3
"""MCP API Key 申请表单后端 —— 只落库,不发信。

为什么不在这台机上发邮件:
  公司邮箱 SMTP 密码在 Jack 的 Mac 钥匙串里,这台是公网机(每天被扫,ipset 黑名单已 8003 条)。
  把公司邮箱密码放上来,一旦机器被拿下就能以公司名义发信 —— 不值。
  所以这里只写 JSONL,由 Mac 侧的排程任务拉走再发邮件/Telegram。

为什么要这个表单(2026-09-05 Jack):
  「时不时有人发邮件申请 MCP API Key,但我只想对接企业性质的,尤其中大型的,像律所这些。」
  ⇒ 表单的作用不是收集,是【筛选】。真正挡掉噪音的是:
    ① 页面上把话说死:个人/小团队直接用免费额度,不必申请
    ② 免费邮箱一律拒收(qq/163/gmail/126/outlook…)—— 机构申请不会用私人邮箱
    ③ 必填机构规模与用途,填不出来的自己会走
"""
import json, os, re, time, html
import fcntl, uuid
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STORE = "/opt/mcp-applications"
LEDGER = os.path.join(STORE, "applications.jsonl")

def funnel_context(value):
    if not isinstance(value, dict): return None
    try: sid = str(uuid.UUID(value.get("sid", "")))
    except (ValueError, TypeError, AttributeError): return None
    source = value.get("source")
    medium = value.get("medium")
    campaign = value.get("campaign", "")
    if source not in {"bing", "google", "baidu", "zhihu", "baijiahao", "weixin", "chatgpt", "copilot", "sogou", "360", "quark", "duckduckgo", "direct", "other"}: return None
    if medium not in {"organic", "referral", "campaign", "direct"} or not isinstance(campaign, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{0,80}", campaign): return None
    return {"sid": sid, "source": source, "medium": medium, "campaign": campaign, "qa": value.get("qa") is True}

def persist_application(data):
    os.makedirs(STORE, exist_ok=True)
    ledger = os.path.join(STORE, "qa-applications.jsonl") if (data.get("funnel") or {}).get("qa") else LEDGER
    with open(os.path.join(STORE, "ledger.lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if os.path.exists(ledger):
            for line in open(ledger, encoding="utf8"):
                try: previous = json.loads(line)
                except ValueError: continue
                if previous.get("id") == data["id"]:
                    return previous.get("email") == data.get("email") and previous.get("company") == data.get("company")
        with open(ledger, "a", encoding="utf8") as stream:
            stream.write(json.dumps(data, ensure_ascii=False) + "\n")
        os.chmod(ledger, 0o600)
    return True
RATE = {}                      # ip -> [timestamps]
RATE_MAX, RATE_WIN = 3, 3600   # 每 IP 每小时最多 3 次

FREE_MAIL = {"qq.com","163.com","126.com","gmail.com","outlook.com","hotmail.com",
             "foxmail.com","sina.com","sohu.com","yeah.net","139.com","189.cn",
             "live.com","icloud.com","yahoo.com","aliyun.com","tom.com","21cn.com"}
FIELDS = ["company","industry","scale","name","title","email","phone","usecase","volume"]
REQUIRED = ["company","industry","scale","name","title","email","usecase"]
MAXLEN = {"company":120,"industry":40,"scale":40,"name":40,"title":60,
          "email":120,"phone":40,"usecase":1000,"volume":60}
CST = timezone(timedelta(hours=8))


def clean(s, n):
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(s or "")).strip()
    return s[:n]


def validate(d):
    errs = []
    for f in REQUIRED:
        if not d.get(f):
            errs.append(f"{f} 必填")
    em = (d.get("email") or "").lower()
    if em:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", em):
            errs.append("邮箱格式不对")
        else:
            dom = em.split("@")[-1]
            if dom in FREE_MAIL:
                errs.append("请使用企业邮箱（个人邮箱恕不受理）")
    if len(d.get("usecase") or "") < 20:
        errs.append("用途场景请写具体一些（至少 20 字）")
    return errs


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "https://www.wenshucha.com")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_POST(self):
        if self.path.rstrip("/") != "/api/mcp-apply":
            return self._send(404, {"ok": False, "error": "not found"})
        ip = self.headers.get("X-Real-IP") or self.client_address[0]
        now = time.time()
        hits = [t for t in RATE.get(ip, []) if now - t < RATE_WIN]
        if len(hits) >= RATE_MAX:
            return self._send(429, {"ok": False, "error": "提交过于频繁，请稍后再试"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 20000:
                return self._send(413, {"ok": False, "error": "内容过长"})
            raw = json.loads(self.rfile.read(n).decode("utf-8", "replace"))
        except Exception:
            return self._send(400, {"ok": False, "error": "请求格式不对"})
        if raw.get("website"):          # 蜜罐:真人看不见这个字段
            return self._send(200, {"ok": True})
        d = {f: clean(raw.get(f), MAXLEN[f]) for f in FIELDS}
        errs = validate(d)
        if errs:
            return self._send(422, {"ok": False, "error": "；".join(errs)})
        d["ts"] = datetime.now(CST).isoformat(timespec="seconds")
        d["ip"] = ip
        d["ua"] = clean(self.headers.get("User-Agent"), 200)
        d["notified"] = False
        try: d["id"] = str(uuid.UUID(raw.get("request_id", "")))
        except (ValueError, TypeError, AttributeError): d["id"] = str(uuid.uuid4())
        d["funnel"] = funnel_context(raw.get("funnel"))
        d["bot"] = bool(re.search(r"bot|spider|crawler|headless|curl|python|wget", d["ua"], re.I))
        d["self"] = bool(re.match(r"^(202\.68\.|114\.132\.)", ip)) or ip in {"163.125.249.3", "163.125.144.23"}
        if not persist_application(d):
            return self._send(409, {"ok": False, "error": "提交编号冲突，请刷新后重试"})
        RATE[ip] = hits + [now]
        self._send(200, {"ok": True, "id": d["id"]})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    os.makedirs(STORE, exist_ok=True)
    ThreadingHTTPServer(("127.0.0.1", 8787), H).serve_forever()
