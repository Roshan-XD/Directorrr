"""Offline setup/proxy regressions; no installers, packages, models or CUDA run."""
import hashlib
import http.client
import importlib.util
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest


def script(name):
    path = Path(__file__).resolve().parents[2] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_setup_metadata_identity_and_exact_budget():
    setup = script("teammate_setup")
    manifest = setup.load_manifest()
    plan = setup.plan(manifest)
    assert len(plan["runtime"]["packages"]) == 84
    assert len(plan["backend"]["packages"]) == 33
    assert plan["known_download_bytes"] == 2751945221
    assert plan["model_bytes"] == 9828025775
    assert plan["runtime"]["installation_eligible"] is False
    assert plan["runtime"]["authorized_real_installation"] is False


@pytest.mark.parametrize("url", ["http://files.pythonhosted.org/a.whl", "https://evil.example/a.whl", "https://user:secret@files.pythonhosted.org/a.whl"])
def test_setup_rejects_unapproved_origins(url):
    with pytest.raises(ValueError):
        script("teammate_setup").checked_url(url)


def test_setup_rejects_paths_outside_owned_root(tmp_path, monkeypatch):
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path / "owned")
    with pytest.raises(ValueError):
        setup.safe(tmp_path / "user-file")


@pytest.mark.parametrize("outcome", ["success", "corrupt", "cancel"])
def test_exact_small_transfer_integrity_and_partial_cleanup(tmp_path, monkeypatch, outcome):
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "space", lambda _: None)
    payload = b"tiny offline fixture"
    item = {"artifact_url": "https://files.pythonhosted.org/tiny.whl", "wheel_filename": "tiny.whl",
            "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    class Response:
        headers = {"Content-Length": str(len(payload))}
        sent = False
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def read(self, _):
            if self.sent: return b""
            self.sent = True
            return b"x" * len(payload) if outcome == "corrupt" else payload
    monkeypatch.setattr(setup.urllib.request, "build_opener", lambda *_: SimpleNamespace(open=lambda *_args, **_kw: Response()))
    cancel = threading.Event()
    if outcome == "cancel": cancel.set()
    folder = tmp_path / "quarantine"
    if outcome == "success":
        result = setup.download(item, folder, cancel, lambda _: None)
        assert result.read_bytes() == payload
        result.write_bytes(b"x" * len(payload))
        with pytest.raises(ValueError, match="integrity"):
            setup.download(item, folder, cancel, lambda _: None)
        assert result.exists()  # Never remove an existing corrupt/user file.
    else:
        with pytest.raises((ValueError, setup.Cancelled)):
            setup.download(item, folder, cancel, lambda _: None)
        assert list(folder.iterdir()) == []


def test_setup_disk_preflight_fails_without_mutation(tmp_path, monkeypatch):
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup.shutil, "disk_usage", lambda _: SimpleNamespace(free=1))
    with pytest.raises(ValueError, match="Insufficient"):
        setup.space(100)
    assert list(tmp_path.iterdir()) == []


def test_setup_review_hash_change_is_rejected(tmp_path, monkeypatch):
    setup = script("teammate_setup")
    manifest = setup.load_manifest()
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    (tmp_path / "setup").mkdir()
    (tmp_path / "setup/manifest.json").write_text(json.dumps(manifest))
    with pytest.raises((ValueError, FileNotFoundError)):
        setup.load_manifest()


@pytest.mark.parametrize("headers,expected", [
    ({"Host": "127.0.0.1:5173", "Origin": "http://127.0.0.1:5173"}, True),
    ({"Host": "127.0.0.1:5173", "Sec-Fetch-Site": "same-origin", "Referer": "http://127.0.0.1:5173/"}, True),
    ({"Host": "127.0.0.1:5173", "Origin": "https://evil.example"}, False),
    ({"Host": "evil.example:5173", "Origin": "http://127.0.0.1:5173"}, False),
    ({"Host": "127.0.0.1:5173"}, False),
    ({"Host": "127.0.0.1:5173", "Sec-Fetch-Site": "same-origin", "Referer": "http://127.0.0.1:5173.evil.example/"}, False),
])
def test_packaged_proxy_origin_proof(headers, expected):
    assert script("packaged_ui").trusted_session(headers) is expected


def test_packaged_proxy_only_authenticates_marked_trusted_requests(tmp_path, monkeypatch):
    ui = script("packaged_ui")
    monkeypatch.setattr(ui, "ROOT", tmp_path)
    assets = tmp_path / "frontend/dist"
    assets.mkdir(parents=True)
    (assets / "index.html").write_text("Director")
    key = "session-private-" + "x" * 64
    forwarded = []
    class Backend:
        def __init__(self, *_args, **_kw): pass
        def request(self, method, path, body, headers):
            forwarded.append(headers)
            self.ok = headers.get("X-Director-Key") == key
        def getresponse(self):
            data = [b'{"ok":true}' if self.ok else b'{"detail":"Forbidden"}', b""]
            return SimpleNamespace(status=200 if self.ok else 403, getheaders=lambda: [], read=lambda _: data.pop(0))
        def close(self): pass
    monkeypatch.setattr(ui, "http", SimpleNamespace(client=SimpleNamespace(HTTPConnection=Backend, HTTPException=http.client.HTTPException)))
    from functools import partial
    server = ui.ThreadingHTTPServer(("127.0.0.1", 0), partial(ui.Handler, directory=str(assets)))
    server.session_key = key
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def get(headers, path="/api/private"):
        client = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        client.request("GET", path, headers={"Host": "127.0.0.1:5173", **headers})
        response = client.getresponse()
        result = response.status, response.read()
        client.close()
        return result
    trusted = {"Origin": "http://127.0.0.1:5173", "X-Director-Session": "launcher"}
    try:
        assert get({})[0] == 403
        assert get(trusted | {"X-Director-Key": "wrong"})[0] == 403
        assert get(trusted)[0] == 200
        assert forwarded[-1]["X-Director-Key"] == key
        assert "X-Director-Session" not in forwarded[-1]
        assert get(trusted | {"Origin": "https://evil.example"})[0] == 403
        status, body = get(trusted, "/api/launcher-session")
        assert status == 200 and key.encode() not in body
        assert get({}, "/../user-secret")[0] == 403
        assert key.encode() not in get({}, "/")[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_setup_never_fabricates_inference_or_production_authorization():
    setup = script("teammate_setup")
    source = Path(setup.__file__).read_text()
    assert '"generation_validated": False' in source
    assert 'atomic_json(NATIVE / "receipts/native-inference.json"' not in source
    assert 'DIRECTOR_ENABLE_REPOSITORY_DOWNLOADS="1"' not in source


@pytest.mark.parametrize("member", ["../escape", "C:/escape", "folder\\escape", "CON.txt"])
def test_python_archive_rejects_unsafe_members_before_extraction(tmp_path, monkeypatch, member):
    import zipfile
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    archive = tmp_path / "tiny.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr(member.replace("\\", "/"), b"inert")
    if "\\" in member:
        # Windows ZipInfo normalizes separators when writing. Restore the raw
        # hostile member in both headers to exercise the incoming ZIP policy.
        archive.write_bytes(archive.read_bytes().replace(member.replace("\\", "/").encode(), member.encode()))
    destination = tmp_path / "python"
    with pytest.raises(ValueError):
        setup.extract_python(archive, destination, threading.Event())
    assert not destination.exists()


def test_python_archive_preserves_existing_directory(tmp_path, monkeypatch):
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    destination = tmp_path / "python"
    destination.mkdir()
    (destination / "user.txt").write_text("preserve")
    with pytest.raises(ValueError, match="overwritten"):
        setup.extract_python(tmp_path / "missing.zip", destination, threading.Event())
    assert (destination / "user.txt").read_text() == "preserve"


def test_setup_children_do_not_inherit_manager_or_hub_credentials(tmp_path, monkeypatch):
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "STATE", tmp_path / "state")
    monkeypatch.setattr(setup, "NATIVE", tmp_path / "runtime")
    monkeypatch.setenv("DIRECTOR_MANAGER_KEY", "private")
    monkeypatch.setenv("HF_TOKEN", "private")
    monkeypatch.setenv("PYTHONPATH", "external")
    env = setup.process_environment()
    assert not {"DIRECTOR_MANAGER_KEY", "HF_TOKEN", "PYTHONPATH"} & env.keys()
    assert env["TEMP"] == str(tmp_path / "state/temp")


def test_cancelled_provisioning_closes_owned_job_and_removes_signal(tmp_path, monkeypatch):
    import sys
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "STATE", tmp_path / "state")
    monkeypatch.setattr(setup, "NATIVE", tmp_path / "runtime")
    identity = "a" * 32
    process = SimpleNamespace(stdout=iter([]), returncode=None, poll=lambda: None, wait=lambda **_: 0)
    monkeypatch.setattr(setup.subprocess, "Popen", lambda *_, **__: process)
    closed = []
    monkeypatch.setitem(sys.modules, "setup_process", SimpleNamespace(OwnedJob=lambda _: SimpleNamespace(close=lambda: closed.append(True))))
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(setup.Cancelled):
        setup.provision_process(tmp_path / "python.exe", cancel, lambda _: None, identity)
    assert closed
    assert not (tmp_path / "state" / ("provision-ready-" + identity)).exists()


def test_backend_notices_require_acceptance_before_pip(tmp_path, monkeypatch):
    import zipfile
    setup = script("teammate_setup")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "STATE", tmp_path / "state")
    (tmp_path / "state").mkdir()
    wheel = tmp_path / "tiny.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("tiny.dist-info/licenses/LICENSE", "Fixture terms")
    monkeypatch.setattr(setup, "download", lambda *_, **__: wheel)
    invoked = []
    monkeypatch.setattr(setup, "command", lambda *_, **__: invoked.append(True))
    package = {"name": "tiny", "version": "1", "sha256": "a" * 64}
    with pytest.raises(ValueError, match="not accepted"):
        setup.install_wheels(tmp_path / "python.exe", [package], "backend-wheels", threading.Event(), lambda _: None, lambda *_: False)
    assert not invoked
    setup.install_wheels(tmp_path / "python.exe", [package], "backend-wheels", threading.Event(), lambda _: None, lambda title, text: "Fixture terms" in text)
    assert invoked == [True]
