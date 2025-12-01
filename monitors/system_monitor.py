import psutil
from notifier import send_alert
import yaml

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

#IGNORE_PROC = [p.lower() for p in cfg["ignore"]["processes"]] 

CPU_THRESHOLD = cfg['alerts']['cpu_threshold']
RAM_THRESHOLD = cfg['alerts']['ram_threshold']

def check_system():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    alerts = []

    if cpu > CPU_THRESHOLD:
        alerts.append(send_alert(f"High CPU usage detected: {cpu}%"))

    if ram > RAM_THRESHOLD:
        alerts.append(send_alert(f"High RAM usage detected: {ram}%"))

    return cpu, ram, alerts
