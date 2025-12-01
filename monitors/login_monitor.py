# login_monitor.py
import time
import os
import threading
from notifier import send_alert
import yaml
import re

# load config
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

AUTH_LOG = cfg.get('login', {}).get('auth_log_path', '/var/log/auth.log')
WATCH_FAILED = cfg.get('login', {}).get('watch_failed', True)
WATCH_SUCCESS = cfg.get('login', {}).get('watch_success', True)
SUSPICIOUS_THRESHOLD = cfg.get('login', {}).get('suspicious_threshold', 5)

# simple counters for suspicious detection (resets on program restart)
failed_counts = {}

# regex patterns (Debian/Ubuntu auth.log format)
FAILED_PATTERNS = [
    re.compile(r'Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>\S+)'),
    re.compile(r'authentication failure; .* rhost=(?P<ip>\S+)')
]
SUCCESS_PATTERNS = [
    re.compile(r'Accepted password for (?P<user>\S+) from (?P<ip>\S+)'),
    re.compile(r'Accepted publickey for (?P<user>\S+) from (?P<ip>\S+)')
]

def process_line(line):
    # check failed patterns
    if WATCH_FAILED:
        for p in FAILED_PATTERNS:
            m = p.search(line)
            if m:
                user = m.groupdict().get('user', 'unknown')
                ip = m.groupdict().get('ip', 'unknown')
                send_alert(f"Failed login attempt for user='{user}' from {ip}", subject_prefix="HIDS Login FAIL")
                # increment counter for IP
                failed_counts[ip] = failed_counts.get(ip, 0) + 1
                if failed_counts[ip] >= SUSPICIOUS_THRESHOLD:
                    send_alert(f"Suspicious activity: {failed_counts[ip]} failed attempts from {ip}", subject_prefix="HIDS Suspicious")
                return

    if WATCH_SUCCESS:
        for p in SUCCESS_PATTERNS:
            m = p.search(line)
            if m:
                user = m.groupdict().get('user', 'unknown')
                ip = m.groupdict().get('ip', 'unknown')
                send_alert(f"Successful login for user='{user}' from {ip}", subject_prefix="HIDS Login SUCCESS")
                # Reset failed counter for the IP if needed
                if ip in failed_counts:
                    failed_counts[ip] = 0
                return

def tail_f(filepath, stop_event):
    """
    Tail file for new lines and process them.
    Uses polling to be robust across filesystems.
    """
    try:
        with open(filepath, "r") as f:
            # Go to the end of file
            f.seek(0, os.SEEK_END)
            while not stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                process_line(line)
    except FileNotFoundError:
        send_alert(f"Auth log not found: {filepath}. Login detection disabled.", subject_prefix="HIDS Login")
    except PermissionError:
        send_alert(f"Permission denied reading auth log: {filepath}. Run with sudo.", subject_prefix="HIDS Login")
    except Exception as e:
        send_alert(f"Login monitor error: {e}", subject_prefix="HIDS Login")

def start_login_monitor(stop_event=None):
    """
    Start monitoring auth log. If stop_event provided, loop will exit when set.
    """
    if stop_event is None:
        stop_event = threading.Event()

    t = threading.Thread(target=tail_f, args=(AUTH_LOG, stop_event), daemon=True)
    t.start()
    return stop_event
