"""Private Windows development launcher; no installers, downloads or WSL."""
import json
import os
import secrets
import shutil
import socket
import subprocess
import time
import urllib.request
import uuid
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "runtime/windows-dev-001"


def check_path(path):
    for parent in (path, *path.parents):
        if parent.exists() and (parent.is_symlink() or parent.stat().st_file_attributes & 0x400):
            raise RuntimeError("Linked launcher path")


def health(url):
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url, timeout=2) as reply:
            return reply.status == 200
    except OSError:
        return False


class Session:
    def __init__(self, key=None, status=lambda text: None):
        key = key if key is not None else secrets.token_urlsafe(48)
        if len(key) < 32:
            raise ValueError("Manager key requires at least 32 characters")
        self.key, self.status = key, status
        self.children, self.logs = [], []
        self.identity = uuid.uuid4().hex
        self.quit = NATIVE / "receipts" / ("stop-" + self.identity)
        self.comfy_quit = NATIVE / "receipts" / ("comfy-stop-" + self.identity)

    def spawn(self, args, cwd, env, label):
        log = (NATIVE / "receipts" / (self.identity + "-" + label + ".log")).open("ab")
        self.logs.append(log)
        p = subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        self.children.append(p)
        return p

    def wait(self, url, process, label, timeout=150):
        self.status("Starting " + label + "…")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(label + " exited; see runtime receipts/logs")
            if health(url):
                return
            time.sleep(0.5)
        raise RuntimeError(label + " startup timed out; see runtime receipts/logs")

    def start(self, packaged=False):
        for path in (NATIVE, ROOT / ".venv", ROOT / "frontend"):
            check_path(path)
        configured = (ROOT / "setup/state/installed.json").is_file()
        packaged = packaged or configured
        if configured:
            from teammate_setup import validate_installed
            validate_installed()
        else:
            receipt = json.loads((NATIVE / "receipts/native-inference.json").read_text())
            if receipt["state"] != "PASS":
                raise RuntimeError("Windows native inference validation is required")
        node = shutil.which("node.exe")
        if not node and not packaged:
            raise RuntimeError("Existing Node.js is required; launcher installs nothing")
        for port in (8188, 8000, 5173):
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    raise RuntimeError(f"Port {port} is occupied. Stop the existing services first.")
        env = os.environ.copy()
        env.pop("DIRECTOR_MANAGER_TOKEN", None)
        env.pop("DIRECTOR_LAUNCHER_TOKEN", None)
        env.update(TEMP=str(NATIVE / "temp"), TMP=str(NATIVE / "temp"),
                   CUDA_CACHE_PATH=str(NATIVE / "cache"), HF_HUB_OFFLINE="1")
        comfy = self.spawn([str(NATIVE / "venv/Scripts/python.exe"), "-s",
            str(ROOT / "scripts/comfy_windows_runner.py"), str(self.comfy_quit),
            "--listen", "127.0.0.1", "--port", "8188", "--offline", "--disable-all-custom-nodes",
            "--disable-auto-launch", "--disable-dynamic-vram", "--use-pytorch-cross-attention",
            "--base-directory", str(NATIVE / "data"), "--user-directory", str(NATIVE / "data/user"),
            "--models-directory", str(NATIVE / "models"), "--temp-directory", str(NATIVE / "data/temp")],
            NATIVE / "ComfyUI", env, "comfy")
        self.wait("http://127.0.0.1:8188/system_stats", comfy, "Windows ComfyUI")
        backend_env = env.copy()
        if packaged:
            backend_env["PYTHONPATH"] = str(ROOT / "backend")
        backend_env.update(DIRECTOR_MANAGER_TOKEN=self.key, DIRECTOR_ENABLE_DEV_GENERATION="1",
                           DIRECTOR_ENABLE_DEV_RESOLVE="1", DIRECTOR_DEV_WINDOWS_RUNTIME="1",
                           DIRECTOR_DEV_COMFY_URL="http://127.0.0.1:8188",
                           DIRECTOR_DEV_GENERATION_OUTPUT=str(NATIVE / "data/output"))
        backend = self.spawn([str(ROOT / ".venv/Scripts/python.exe"), "-m", "uvicorn",
                              "director.main:app", "--host", "127.0.0.1", "--port", "8000", "--no-access-log"],
                             ROOT, backend_env, "backend")
        self.wait("http://127.0.0.1:8000/api/dev/generation/config", backend, "Director backend")
        ui_env = env.copy()
        # Server-only variable: never VITE_, a URL, file or subprocess argument.
        ui_env.update(VITE_PRODUCT_WORKSPACE="1", VITE_DEV_GENERATION="1", VITE_LAUNCHER_SESSION="1", DIRECTOR_BACKEND_URL="http://127.0.0.1:8000",
                      DIRECTOR_LAUNCHER_TOKEN=self.key)
        if packaged:
            ui_env["DIRECTOR_PACKAGED_SESSION"] = "1"
            ui = self.spawn([str(ROOT / ".venv/Scripts/python.exe"), str(ROOT / "scripts/packaged_ui.py")],
                            ROOT, ui_env, "Director UI")
        else:
            ui = self.spawn([node, str(ROOT / "frontend/node_modules/vite/bin/vite.js"),
                             "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
                            ROOT / "frontend", ui_env, "Director UI")
        self.wait("http://127.0.0.1:5173", ui, "Director UI")
        # This record contains process ownership information, never the manager key.
        (NATIVE / "receipts/launcher-session.json").write_text(json.dumps({
            "identity": self.identity, "controller_pid": os.getpid(),
            "pids": [p.pid for p in self.children], "stop_file": str(self.quit),
            "windows_only": True}, indent=2))
        self.status("Director is ready. Local authorization is automatic for this session.")

    def stop(self):
        import ctypes
        self.comfy_quit.touch(exist_ok=True)
        for index, child in reversed(list(enumerate(self.children))):
            if child.poll() is None:
                if index != 0:
                    kernel = ctypes.windll.kernel32
                    kernel.FreeConsole()
                    if kernel.AttachConsole(child.pid):
                        kernel.SetConsoleCtrlHandler(None, True)
                        kernel.GenerateConsoleCtrlEvent(0, 0)
                        kernel.FreeConsole()
                try:
                    child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    self.status("A service has not stopped; inspect its owned process/log before retrying.")
        for log in self.logs:
            log.close()
        self.key = ""
        if all(child.poll() is not None for child in self.children):
            record = NATIVE / "receipts/launcher-session.json"
            if record.exists() and json.loads(record.read_text()).get("identity") == self.identity:
                record.unlink()
            self.quit.unlink(missing_ok=True)
            self.comfy_quit.unlink(missing_ok=True)


def main():
    import tkinter as tk
    from tkinter import messagebox
    window = tk.Tk()
    session = None
    try:
        window.deiconify()
        window.title("Director — Windows development")
        label = tk.Label(window, text="Starting Director…", padx=24, pady=20)
        label.pack()
        def status(text):
            label.configure(text=text)
            window.update()
        session = Session(status=status)
        session.start()
        webbrowser.open("http://127.0.0.1:5173")
        def shutdown():
            session.stop()
            window.destroy()
        tk.Button(window, text="Stop Director", command=shutdown).pack(pady=10)
        window.protocol("WM_DELETE_WINDOW", shutdown)
        def check_stop():
            if session.quit.exists(): shutdown()
            else: window.after(500, check_stop)
        window.after(500, check_stop)
        window.mainloop()
    except Exception as exc:
        if session: session.stop()
        messagebox.showerror("Director startup", str(exc), parent=window)
        window.destroy()


if __name__ == "__main__": main()
