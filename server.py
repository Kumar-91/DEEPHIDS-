from flask import Flask, jsonify, send_from_directory
import os, socket, time
import psutil
import yaml
from datetime import datetime

app = Flask(__name__, static_folder="web")

ALERT_LOG = "logs/alerts.log"

# ---------- API: system stats ----------
@app.route("/api/stats")
def stats():
    total_alerts = 0
    recent = 0

    if os.path.exists(ALERT_LOG):
        with open(ALERT_LOG) as f:
            lines = f.readlines()
            total_alerts = len(lines)
            recent = len(lines[-10:]) if len(lines) > 10 else len(lines)

    return jsonify({
        "total_alerts": total_alerts,
        "recent_activities": recent,
        "system_time": time.time() * 1000,
        "hostname": socket.gethostname()
    })

# ---------- API: alerts list ----------
@app.route("/api/alerts")
def alerts():
    final = []
    if os.path.exists(ALERT_LOG):
        with open(ALERT_LOG) as f:
            for line in f.readlines():
                ts = line[1:20]  # timestamp
                msg = line[22:].strip()
                final.append({
                    "timestamp": ts,
                    "alerts": [msg]
                })
    return jsonify(final)

# ---------- API: CPU, RAM, Disk ----------
@app.route("/api/system_info")
def system_info():
    return jsonify({
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    })

# ---------- Serve Dashboard ----------
@app.route("/")
def dashboard():
    return send_from_directory("web", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
