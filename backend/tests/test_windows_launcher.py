import importlib.util
from pathlib import Path

import pytest


def launcher():
    path = Path(__file__).resolve().parents[2] / "scripts/windows_launcher.py"
    spec = importlib.util.spec_from_file_location("director_windows_launcher_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_launcher_rejects_short_key():
    with pytest.raises(ValueError, match="32"):
        launcher().Session("short")


def test_launcher_signals_are_distinct_and_owned():
    module = launcher()
    a, b = module.Session("x" * 32), module.Session("y" * 32)
    assert a.quit != b.quit
    assert a.quit.parent == module.NATIVE / "receipts"
    assert a.comfy_quit != a.quit


def test_launcher_stop_empty_session_clears_key(tmp_path, monkeypatch):
    module = launcher()
    monkeypatch.setattr(module, "NATIVE", tmp_path)
    (tmp_path / "receipts").mkdir()
    session = module.Session("x" * 32)
    session.stop()
    assert session.key == ""
    assert not session.comfy_quit.exists()


def test_automatic_key_is_fresh_and_strong():
    module = launcher()
    a, b = module.Session(), module.Session()
    assert len(a.key) == 64 and a.key != b.key
    assert not any(c.isspace() for c in a.key)


def test_start_transfers_same_secret_only_in_process_environments(tmp_path, monkeypatch, capsys):
    import json
    module = launcher()
    monkeypatch.setattr(module, "NATIVE", tmp_path)
    (tmp_path / "receipts").mkdir()
    (tmp_path / "receipts/native-inference.json").write_text('{"state":"PASS"}')
    monkeypatch.setattr(module, "check_path", lambda _: None)
    monkeypatch.setattr(module.shutil, "which", lambda _: "node.exe")
    class Socket:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def connect_ex(self, *_): return 1
    monkeypatch.setattr(module.socket, "socket", Socket)
    session = module.Session()
    calls = []
    class Child:
        pid = 123
        def poll(self): return 0
    def spawn(args, cwd, env, label):
        calls.append((args, env, label))
        session.children.append(Child())
        return session.children[-1]
    monkeypatch.setattr(session, "spawn", spawn)
    monkeypatch.setattr(session, "wait", lambda *_: None)
    session.start()
    secret = session.key
    assert calls[1][1]["DIRECTOR_MANAGER_TOKEN"] == secret
    assert calls[2][1]["DIRECTOR_LAUNCHER_TOKEN"] == secret
    assert secret not in str(calls[0])
    assert all(secret not in str(args) for args, _, _ in calls)
    assert secret not in (tmp_path / "receipts/launcher-session.json").read_text()
    assert secret not in capsys.readouterr().out
    session.quit.touch()
    session.stop()
    assert session.key == ""
    assert not (tmp_path / "receipts/launcher-session.json").exists()
    assert not session.quit.exists() and not session.comfy_quit.exists()
    assert all(secret not in file.read_text() for file in (tmp_path / "receipts").iterdir() if file.is_file())


def test_launcher_never_prompts_or_places_secret_in_browser_url():
    source = (Path(__file__).resolve().parents[2] / "scripts/windows_launcher.py").read_text()
    assert "simpledialog" not in source
    assert 'webbrowser.open("http://127.0.0.1:5173")' in source
    assert "VITE_DIRECTOR_MANAGER" not in source


def test_generated_key_keeps_backend_authentication_and_origin_checks():
    from fastapi import FastAPI, Depends
    from fastapi.testclient import TestClient
    from director.installations.api import require_manager_key
    key = launcher().Session().key
    app = FastAPI()
    app.state.manager_key = key
    @app.get("/privileged", dependencies=[Depends(require_manager_key)])
    def privileged(): return {"ok": True}
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        assert client.get("/privileged", headers={"X-Director-Key": key, "Origin":"http://127.0.0.1:8000"}).status_code == 200
        assert client.get("/privileged").status_code == 403
        assert client.get("/privileged", headers={"X-Director-Key":"wrong"}).status_code == 403
        assert client.get("/privileged", headers={"X-Director-Key":key,"Origin":"https://evil.example"}).status_code == 403
