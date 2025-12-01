from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from notifier import send_alert
import yaml
import time

# Load config
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

WATCH_PATHS = cfg["files"]["watch_paths"]
IGNORE_PATHS = cfg.get("ignore", {}).get("paths", [])

class FileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Ignore unwanted paths
        #if event.src_path.startswith(p):
            #return

       
        send_alert(f"File modified: {event.src_path}")

    def on_created(self, event):
        # Ignore unwanted paths
        #if event.src_path.startswith(p):
            #return

        
        send_alert(f"New file created: {event.src_path}")

def start_file_monitor():
    observer = Observer()

    for path in WATCH_PATHS:
        observer.schedule(FileHandler(), path, recursive=True)

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
