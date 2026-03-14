"""
SOC Accountability Tracker — Desktop Launcher
Double-click this file (or a shortcut to it) to open the app
in a native desktop window instead of a browser tab.
"""

import subprocess
import sys
import time
import socket
import webview

APP_TITLE = "SOC Accountability Cockpit"
PORT = 8501
URL = f"http://localhost:{PORT}"


def _port_open(port: int, timeout: float = 0.3) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    # Start Streamlit in the background (hidden console)
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false",
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    # Wait for Streamlit to be ready
    for _ in range(40):
        if _port_open(PORT):
            break
        time.sleep(0.5)

    # Open native desktop window
    window = webview.create_window(APP_TITLE, URL, width=1400, height=900)
    webview.start()

    # When window closes, kill Streamlit
    proc.terminate()


if __name__ == "__main__":
    main()
