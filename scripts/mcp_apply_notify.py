#!/usr/bin/env python3
"""拉走 MCP 申请表单的新提交,发邮件给 Jack + Telegram。

为什么在 Mac 侧而不是服务器上发信:
  公司邮箱 SMTP 密码在 Jack 的 Mac 钥匙串(security -s wenshucha-smtp)。
  生产机是公网机、每天被扫(ipset 黑名单 8003 条),把公司邮箱密码放上去,
  一旦被拿下就能以公司名义对外发信 —— 不值这个风险。
  所以服务器只落 JSONL,这个脚本按排程拉走再发。

⚠️ 这封信是【发给 Jack 本人的内部通知】,不是对外邮件,所以直接 send。
   对外邮件仍然一律只存草稿,见记忆 feedback_email_draft_not_send。

用法: python3 mcp_apply_notify.py        # 排程每 15 分钟跑
      python3 mcp_apply_notify.py --dry  # 只看不发不标记
"""
import json, subprocess, sys, smtplib, ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate

SRV = "root@114.132.74.235"
LEDGER = "/opt/mcp-applications/applications.jsonl"
ACCOUNT = "chenjiaxin@wenshucha.com"
TO = "jack.jiaxin.chen@gmail.com"
DRY = "--dry" in sys.argv


def ssh(cmd, timeout=40):
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=25", SRV, cmd],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout


def smtp_pass():
    r = subprocess.run(["security", "find-generic-password", "-s", "wenshucha-smtp", "-w"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def fetch_new():
    out = ssh(f"cat {LEDGER} 2>/dev/null")
    rows = []
    for i, line in enumerate(out.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        d["_line"] = i
        if not d.get("notified"):
            rows.append(d)
    return rows


def mark_notified(idxs):
    if not idxs:
        return
    ids = ",".join(str(i) for i in idxs)
    ssh(f"""python3 - <<'PY'
import json
p="{LEDGER}"
mark=set([{ids}])
out=[]
for i,l in enumerate(open(p,encoding='utf-8')):
    l=l.strip()
    if not l: continue
    d=json.loads(l)
    if i in mark: d["notified"]=True
    out.append(json.dumps(d,ensure_ascii=False))
open(p,'w',encoding='utf-8').write("\\n".join(out)+"\\n")
print("marked",len(mark))
PY""")


def render(rows):
    L = []
    for d in rows:
        L.append(f"""【{d.get('industry','?')}】{d.get('company','?')}   {d.get('scale','?')}
  联系人：{d.get('name','')}（{d.get('title','')}）
  邮箱：  {d.get('email','')}      电话：{d.get('phone','') or '未留'}
  预计量：{d.get('volume','') or '未填'}
  用途：  {d.get('usecase','')}
  提交于：{d.get('ts','')}   IP {d.get('ip','')}""")
    return "\n\n" + ("\n\n" + "-" * 56 + "\n\n").join(L) + "\n"


def send(rows):
    body = f"""收到 {len(rows)} 条 MCP 机构接入申请。
（这个表单已挡掉个人邮箱与个人/小团队，能走到你这里的都填了机构信息。）
{render(rows)}
—— 表单页 https://www.wenshucha.com/mcp/apply/
"""
    m = EmailMessage()
    m["Subject"] = f"[文书查] {len(rows)} 条 MCP 机构接入申请 · {rows[0].get('company','')}" + ("等" if len(rows) > 1 else "")
    m["From"] = formataddr(("文书查表单", ACCOUNT))
    m["To"] = TO
    m["Date"] = formatdate(localtime=True)
    m.set_content(body)
    if DRY:
        print("[dry] 不发信。正文预览：\n" + body[:1200])
        return True
    pw = smtp_pass()
    if not pw:
        print("❌ 钥匙串取不到 SMTP 密码"); return False
    with smtplib.SMTP_SSL("smtp.exmail.qq.com", 465, context=ssl.create_default_context()) as s:
        s.login(ACCOUNT, pw)
        s.send_message(m)
    print(f"✅ 已发邮件到 {TO}")
    return True


def telegram(rows):
    try:
        import pathlib
        sh = pathlib.Path.home() / ".claude/bin/notify-telegram.sh"
        if not sh.exists():
            return
        txt = f"📋 {len(rows)} 条 MCP 机构接入申请\n" + "\n".join(
            f"· {d.get('company','?')}（{d.get('industry','?')}·{d.get('scale','?')}）{d.get('name','')} {d.get('title','')}"
            for d in rows)
        if DRY:
            print("[dry] Telegram:\n" + txt); return
        subprocess.run([str(sh), txt], timeout=20)
    except Exception as e:
        print("Telegram 推送失败(不影响主流程):", e)


if __name__ == "__main__":
    rows = fetch_new()
    if not rows:
        print("没有新申请")
        sys.exit(0)
    print(f"发现 {len(rows)} 条新申请")
    if send(rows):
        telegram(rows)
        if not DRY:
            mark_notified([d["_line"] for d in rows])
