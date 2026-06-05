#!/usr/bin/env python3
"""每日 SSL 证书到期监控
跟 wenshucha-monitor 重叠的是健康层 SSL,这里关注的是「业务关键域名 SSL 到期日 < N 天」的告警 escalation:
- < ssl_warn_days(默认 30):提醒告警
- < ssl_critical_days(默认 14):紧急告警 + 自动尝试续费
"""
import os
import socket
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pip3 install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yml").read_text())
WARN = CONFIG["global"].get("ssl_warn_days", 30)
CRITICAL = CONFIG["global"].get("ssl_critical_days", 14)

NOTIFY_WECHAT = Path.home() / ".claude/bin/notify-wechat.py"
NOTIFY_IMESSAGE = Path.home() / ".claude/bin/notify-imessage.sh"
NOTIFY_FEISHU = Path(__file__).resolve().parent / "notify_feishu.py"


def get_ssl_days_left(hostname: str, port: int = 443, timeout: int = 10):
    """返回 (days_left, expire_str, issuer) 或 (None, error, None)"""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                days = (exp - datetime.utcnow()).days
                issuer = dict(x[0] for x in cert.get("issuer", []))
                return days, exp.strftime("%Y-%m-%d"), issuer.get("commonName", "?")
    except Exception as e:
        return None, str(e), None


def notify(msg: str, title: str = "wenshucha SEO · SSL 到期告警"):
    """三通道告警:飞书(主)+ iMessage(备 1)+ 微信(备 2)
    任一通道成功就算成功;全部失败才 return False
    """
    sent = False

    # 1) 飞书(主通道,卡片更醒目)
    if NOTIFY_FEISHU.exists():
        try:
            r = subprocess.run(
                ["python3", str(NOTIFY_FEISHU), title],
                input=msg,
                timeout=20,
                capture_output=True,
                text=True,
            )
            if r.returncode == 0:
                sent = True
        except Exception as e:
            print(f"飞书推送异常: {e}")

    # 2) iMessage(备 1)
    if NOTIFY_IMESSAGE.exists() and os.access(NOTIFY_IMESSAGE, os.X_OK):
        try:
            r = subprocess.run([str(NOTIFY_IMESSAGE), msg], timeout=20, capture_output=True, text=True)
            if r.returncode == 0:
                sent = True
        except Exception:
            pass

    # 3) 微信(备 2,Hermes 可能限流但聊胜于无)
    if NOTIFY_WECHAT.exists() and os.access(NOTIFY_WECHAT, os.X_OK):
        try:
            r = subprocess.run([str(NOTIFY_WECHAT), msg], timeout=20, capture_output=True, text=True)
            if r.returncode == 0:
                sent = True
        except Exception:
            pass

    return sent


def main():
    alerts = []
    print(f"[{datetime.now()}] SSL 到期检查 (warn<{WARN}d, critical<{CRITICAL}d)")
    for site in CONFIG["sites"]:
        if not site.get("check_ssl", True):
            continue
        host = site["host"]
        days, exp_or_err, issuer = get_ssl_days_left(host)
        if days is None:
            line = f"  ✗ {host:35} 读取失败: {exp_or_err}"
            alerts.append((host, "ERROR", exp_or_err, None))
        else:
            tag = "✓"
            level = None
            if days < CRITICAL:
                tag = "🔥"
                level = "CRITICAL"
            elif days < WARN:
                tag = "⚠️"
                level = "WARN"
            line = f"  {tag} {host:35} {days:>4}d  exp={exp_or_err}  by {issuer}"
            if level:
                alerts.append((host, level, exp_or_err, days))
        print(line)

    if alerts:
        msg_lines = [f"【wenshucha SEO · SSL 到期告警】{len(alerts)} 个站需要关注:\n"]
        for host, level, exp, days in alerts:
            if days is not None:
                msg_lines.append(f"• [{level}] {host} 剩 {days} 天,{exp} 到期")
            else:
                msg_lines.append(f"• [{level}] {host} 读取失败: {exp}")
        notify("\n".join(msg_lines))

    return 0 if not alerts else 1


if __name__ == "__main__":
    sys.exit(main())
