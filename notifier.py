# notifier.py
import datetime
import yaml
import os
import smtplib
from email.message import EmailMessage
import ssl

# Load config once
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

EMAIL_ENABLED = cfg.get('alerts', {}).get('email_alerts', False)
SMTP_CFG = cfg.get('alerts', {}).get('smtp', {})

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

ALERT_LOG = os.path.join(LOG_DIR, "alerts.log")

def write_log(text):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {text}"
    print(line)
    with open(ALERT_LOG, "a") as f:
        f.write(line + "\n")
    return line

def send_email(subject, body):
    if not EMAIL_ENABLED:
        return False, "Email disabled in config"

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_CFG.get('from_addr') or SMTP_CFG.get('username')
        msg['To'] = ", ".join(SMTP_CFG.get('to_addrs', []))
        msg.set_content(body)

        host = SMTP_CFG.get('host')
        port = SMTP_CFG.get('port', 587)
        username = SMTP_CFG.get('username')
        password = SMTP_CFG.get('password')
        use_tls = SMTP_CFG.get('use_tls', True)

        if use_tls:
            # Start TLS connection
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if username and password:
                    server.login(username, password)
                server.send_message(msg)

        return True, "Email sent"
    except Exception as e:
        return False, f"Email error: {e}"

def send_alert(message, subject_prefix="HIDS Alert"):
    """
    Central alert function: writes to alerts.log, prints, and optionally emails.
    Returns the composed alert string (timestamped).
    """
    line = write_log(message)

    # Send email asynchronously is possible, but here we send synchronously for simplicity
    if EMAIL_ENABLED:
        subj = f"{subject_prefix}: {message[:80]}"
        ok, info = send_email(subj, line)
        if not ok:
            # record email send failure
            write_log(f"[EMAIL FAIL] {info}")

    return line
