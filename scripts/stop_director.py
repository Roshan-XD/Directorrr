"""Signal only a recorded Director launcher; never kill processes by port/name."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "runtime/windows-dev-001/receipts"
try:
    data = json.loads((root / "launcher-session.json").read_text())
    path = Path(data["stop_file"])
    if path.parent != root or path.name != "stop-" + data["identity"]:
        raise ValueError("Invalid launcher signal")
    for parent in (path, *path.parents):
        if parent.exists() and (parent.is_symlink() or parent.stat().st_file_attributes & 0x400):
            raise ValueError("Linked launcher path")
    path.touch(exist_ok=True)
    print("Stop requested for the recorded Director session. User media and runtime files are preserved.")
except (OSError, ValueError, KeyError):
    raise SystemExit("No valid Director launcher session was found.")
