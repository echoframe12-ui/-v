from __future__ import annotations

import gc
import os
import time


def safe_remove(path: str | None) -> None:
    """Safely remove a temporary file on Windows or POSIX, handling open handles gracefully."""
    if not path or not os.path.exists(path):
        return
    gc.collect()
    for _ in range(5):
        try:
            os.remove(path)
            return
        except PermissionError:
            gc.collect()
            time.sleep(0.02)
