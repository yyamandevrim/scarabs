"""Optional Linux LED brightness hook. The default is a no-op everywhere."""
from pathlib import Path
import logging

class LedHook:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.failed = False

    def set_alarm(self, enabled):
        if self.path and not self.failed:
            try:
                self.path.write_text("1" if enabled else "0")
            except OSError as exc:
                logging.warning("LED hook unavailable; continuing without LED: %s", exc)
                self.failed = True
