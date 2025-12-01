# main.py

import threading
from gui import start_gui
from monitors.file_monitor import start_file_monitor
from monitors.login_monitor import start_login_monitor

if __name__ == "__main__":
    # Start file monitor in background
    t_files = threading.Thread(target=start_file_monitor, daemon=True)
    t_files.start()

    # Start login monitor (returns stop event)
    login_stop_event = start_login_monitor()

    # Start GUI
    start_gui()

    # When GUI closes, stop login monitor
    if login_stop_event:
        login_stop_event.set()
