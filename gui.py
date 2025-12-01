# gui.py
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import time
from monitors.system_monitor import check_system
from notifier import send_alert, ALERT_LOG
import yaml
import os

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

REFRESH = cfg['gui']['refresh_interval']

class HIDS_GUI:

    def __init__(self, root):
        self.root = root
        self.root.title("HIDS Dashboard - Kali Linux")
        self.root.geometry("700x500")

        self.event_queue = queue.Queue()

        # Labels
        self.cpu_label = tk.Label(root, text="CPU: 0%", font=("Arial", 12))
        self.cpu_label.pack(anchor='w', padx=10, pady=(10,0))

        self.ram_label = tk.Label(root, text="RAM: 0%", font=("Arial", 12))
        self.ram_label.pack(anchor='w', padx=10)

        # Log area
        self.log_area = scrolledtext.ScrolledText(root, width=90, height=22)
        self.log_area.pack(padx=10, pady=10)

        # Track last read position of alerts.log
        self.log_path = ALERT_LOG
        self.last_log_size = 0
        if os.path.exists(self.log_path):
            self.last_log_size = os.path.getsize(self.log_path)

        # Start threads
        threading.Thread(target=self.process_monitor_thread, daemon=True).start()
        # Schedule GUI updates
        self.root.after(1000, self.update_gui)

    def process_monitor_thread(self):
        while True:
            cpu, ram, alerts = check_system()
            self.event_queue.put((cpu, ram, alerts))
            time.sleep(1)

    def read_new_alerts_file(self):
        """Read only new lines appended to alerts.log and return them."""
        if not os.path.exists(self.log_path):
            return []
        try:
            current_size = os.path.getsize(self.log_path)
            if current_size < self.last_log_size:
                # rotated or truncated file: read from start
                self.last_log_size = 0
            if current_size == self.last_log_size:
                return []
            with open(self.log_path, "r") as f:
                f.seek(self.last_log_size)
                new = f.read()
                self.last_log_size = f.tell()
            lines = [l for l in new.splitlines() if l.strip()]
            return lines
        except Exception as e:
            return [f"[GUI ERROR] Failed to read alerts.log: {e}"]

    def update_gui(self):
        # Process queued CPU/RAM alerts
        try:
            while True:
                cpu, ram, alerts = self.event_queue.get_nowait()
                self.cpu_label.config(text=f"CPU Usage: {cpu}%")
                self.ram_label.config(text=f"RAM Usage: {ram}%")
                for alert in alerts:
                    self.log_area.insert(tk.END, alert + "\n")
                    self.log_area.yview(tk.END)
        except queue.Empty:
            pass

        # Read any new alerts from alert log file (login monitor and notifier write here)
        new_lines = self.read_new_alerts_file()
        for l in new_lines:
            self.log_area.insert(tk.END, l + "\n")
            self.log_area.yview(tk.END)

        # Schedule next update
        self.root.after(REFRESH, self.update_gui)

def start_gui():
    root = tk.Tk()
    app = HIDS_GUI(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()

