import streamlit as st
import psutil
import time
import threading
import yaml
import os
from notifier import ALERT_LOG, send_alert
from monitors.system_monitor import check_system
from monitors.file_monitor import start_file_monitor
from monitors.login_monitor import start_login_monitor

# Load config
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

REFRESH = cfg['gui']['refresh_interval'] / 1000  # convert ms → seconds

# Start monitors in background (runs only once)
if "monitors_started" not in st.session_state:
    threading.Thread(target=start_file_monitor, daemon=True).start()
    st.session_state["login_event"] = start_login_monitor()
    st.session_state["monitors_started"] = True

# Streamlit Page Settings
st.set_page_config(page_title="HIDS Dashboard", layout="wide")
st.title("🔐 Host Intrusion Detection System (HIDS) – Streamlit Dashboard")

# System monitor section
st.subheader("📊 System Status")
cpu = psutil.cpu_percent()
ram = psutil.virtual_memory().percent
disk = psutil.disk_usage('/').percent

col1, col2, col3 = st.columns(3)
col1.metric("CPU Usage", f"{cpu}%")
col2.metric("RAM Usage", f"{ram}%")
col3.metric("Disk Usage", f"{disk}%")

# Log display
st.subheader("📜 Real-Time Alert Logs")
log_box = st.empty()

def read_logs():
    if not os.path.exists(ALERT_LOG):
        return "No alerts yet."
    with open(ALERT_LOG, "r") as f:
        return f.read()

log_box.text(read_logs())

# Check for new alerts from system monitor
cpu_now, ram_now, alerts = check_system()
for alert in alerts:
    send_alert(alert)

# Auto-refresh
time.sleep(REFRESH)
st.rerun()
