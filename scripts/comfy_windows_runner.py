"""Owned development server runner with cooperative file-signalled shutdown."""
import runpy
import signal
import sys
import threading
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
stop = Path(sys.argv[1])
if stop.parent != root / "runtime/windows-dev-001/receipts":
    raise ValueError("Invalid shutdown signal directory")


def watch():
    while not stop.exists():
        time.sleep(0.5)
    signal.raise_signal(signal.SIGINT)


threading.Thread(target=watch, daemon=True).start()
source = root / "runtime/windows-dev-001/ComfyUI"
sys.path.insert(0, str(source))
sys.argv = [str(source / "main.py"), *sys.argv[2:]]
try:
    runpy.run_path(str(source / "main.py"), run_name="__main__")
except KeyboardInterrupt:
    pass
