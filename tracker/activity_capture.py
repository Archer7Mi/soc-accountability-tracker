from __future__ import annotations

import ctypes
import sys
import threading
import time
from datetime import datetime
from typing import Any

from tracker.db import add_auto_activity_segment, init_db

_POLL_SECONDS = 5
_COLLECTOR_LOCK = threading.Lock()
_COLLECTOR: "AutoActivityCollector | None" = None


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _active_window_title_windows() -> str:
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def _active_window_title() -> str:
    if sys.platform != "win32":
        return ""
    try:
        return _active_window_title_windows()
    except Exception:
        return ""


def _infer_app_name(window_title: str) -> str:
    if " - " in window_title:
        return window_title.split(" - ")[-1].strip()[:80] or "Unknown"
    if "|" in window_title:
        return window_title.split("|")[-1].strip()[:80] or "Unknown"
    return (window_title[:80] or "Unknown").strip()


class AutoActivityCollector:
    def __init__(self, poll_seconds: int = _POLL_SECONDS) -> None:
        self.poll_seconds = poll_seconds
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._last_title = ""
        self._segment_started: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._thread = threading.Thread(target=self._run, name="auto-activity-capture", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._running.is_set():
            return
        self._running.clear()
        self._flush_segment(_now_str())

    def is_running(self) -> bool:
        return self._running.is_set()

    def current_title(self) -> str:
        return self._last_title

    def _flush_segment(self, ended_at: str) -> None:
        if not self._segment_started or not self._last_title:
            return
        start = datetime.strptime(self._segment_started, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(ended_at, "%Y-%m-%d %H:%M:%S")
        duration = int((end - start).total_seconds())
        if duration < 5:
            self._segment_started = None
            return

        add_auto_activity_segment(
            work_date=start.date().isoformat(),
            app_name=_infer_app_name(self._last_title),
            window_title=self._last_title[:240],
            started_at=self._segment_started,
            ended_at=ended_at,
            duration_seconds=duration,
            source="auto",
        )
        self._segment_started = None

    def _run(self) -> None:
        while self._running.is_set():
            now = _now_str()
            title = _active_window_title()
            if title != self._last_title:
                self._flush_segment(now)
                self._last_title = title
                if title:
                    self._segment_started = now
            time.sleep(self.poll_seconds)


def start_auto_capture() -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Auto capture currently supports Windows only."

    init_db()

    global _COLLECTOR
    with _COLLECTOR_LOCK:
        if _COLLECTOR and _COLLECTOR.is_running():
            return True, "Auto capture is already running."
        if _COLLECTOR is None:
            _COLLECTOR = AutoActivityCollector()
        _COLLECTOR.start()
    return True, "Auto capture started."


def stop_auto_capture() -> tuple[bool, str]:
    global _COLLECTOR
    with _COLLECTOR_LOCK:
        if not _COLLECTOR or not _COLLECTOR.is_running():
            return True, "Auto capture is not running."
        _COLLECTOR.stop()
    return True, "Auto capture stopped and current segment saved."


def get_auto_capture_status() -> dict[str, Any]:
    running = bool(_COLLECTOR and _COLLECTOR.is_running())
    title = _COLLECTOR.current_title() if _COLLECTOR else ""
    return {
        "supported": sys.platform == "win32",
        "running": running,
        "poll_seconds": _POLL_SECONDS,
        "current_title": title,
    }
