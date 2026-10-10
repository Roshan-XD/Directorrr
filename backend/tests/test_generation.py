import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from director.generation.service import ComfyUIClient, DevelopmentGeneration, GenerationRequest, build_workflow
from director.installations.schemas import ManagerError
from director.main import create_app

PROMPT_ID = "12345678-1234-1234-1234-123456789abc"
KEY = "g" * 32


class FakeComfy:
    def __init__(self):
        self.history = {}
        self.queue = {"queue_running": [], "queue_pending": []}
        self.submissions = []

    def request(self, path, body=None):
        if path == "/prompt":
            self.submissions.append(body)
            return {"prompt_id": PROMPT_ID, "node_errors": {}}
        if path == "/queue":
            return self.queue
        return self.history

    def close(self):
        pass


@pytest.fixture
def manager(tmp_path):
    return DevelopmentGeneration(FakeComfy(), tmp_path)


def finish(manager, job, filename=None):
    filename = filename or f"Director_Stage8_{job.id}_00001_.webm"
    manager.client.history = {PROMPT_ID: {"status": {"status_str": "success", "completed": True},
        "outputs": {"47": {"images": [{"filename": filename, "subfolder": "", "type": "output"}]}}}}
    return filename


def test_fixed_workflow_prompt_and_seed():
    first = build_workflow("ocean", 9, "a" * 32)
    second = build_workflow("mountain", 10, "a" * 32)
    first["6"]["inputs"]["text"] = "mountain"
    first["3"]["inputs"]["seed"] = 10
    assert first == second
    assert second["40"]["inputs"] == {"width": 320, "height": 192, "length": 17, "batch_size": 1}
    assert second["3"]["inputs"]["steps"] == 8
    second["40"]["inputs"]["width"] = 999
    assert build_workflow("x", 1, "a" * 32)["40"]["inputs"]["width"] == 320


@pytest.mark.parametrize("body", [{"prompt": " "}, {"prompt": "x", "steps": 1}, {"prompt": "x", "seed": -1},
    {"prompt": "x", "seed": True}, {"prompt": "x", "seed": 9007199254740992}, {"prompt": "x", "workflow": {}}])
def test_fixed_request_protection(body):
    with pytest.raises(ValidationError):
        GenerationRequest(**body)


def test_submission_progress_and_success(manager):
    job = manager.start(GenerationRequest(prompt="ocean"))
    assert job.state == "queued" and job.comfy_prompt_id == PROMPT_ID
    manager.client.queue["queue_running"] = [[0, PROMPT_ID]]
    assert manager.get(job.id).state == "running"
    assert manager.get(job.id).progress is None
    filename = finish(manager, job)
    (manager.output_root / filename).write_bytes(b"\x1a\x45\xdf\xa3fixture")
    assert manager.get(job.id).state == "completed"
    assert manager.output(job.id)[0] == filename


def test_execution_failure(manager):
    job = manager.start(GenerationRequest(prompt="x"))
    manager.client.history = {PROMPT_ID: {"status": {"status_str": "error"}}}
    assert manager.get(job.id).state == "failed"


@pytest.mark.parametrize("filename", ["../elsewhere.webm", "C:\\file.webm", "wrong.webm", "/absolute.webm"])
def test_unsafe_output(manager, filename):
    job = manager.start(GenerationRequest(prompt="x"))
    finish(manager, job, filename)
    assert manager.get(job.id).state == "failed"
    with pytest.raises(ValueError):
        manager._read_output(filename)


def test_missing_output_and_bad_header(manager):
    job = manager.start(GenerationRequest(prompt="x"))
    finish(manager, job)
    assert manager.get(job.id).state == "failed"
    p = manager.output_root / f"Director_Stage8_{job.id}_1_.webm"
    p.write_bytes(b"not video")
    with pytest.raises(ValueError):
        manager._read_output(p.name)


def test_duplicate_and_busy(manager):
    manager.start(GenerationRequest(prompt="x"))
    with pytest.raises(ManagerError, match="already active"):
        manager.start(GenerationRequest(prompt="x"))
    assert len(manager.client.submissions) == 1


def test_symlink_output(manager, tmp_path):
    job = manager.start(GenerationRequest(prompt="x"))
    filename = finish(manager, job)
    outside = tmp_path / "unrelated.webm"
    outside.write_bytes(b"\x1a\x45\xdf\xa3fixture")
    try:
        (tmp_path / filename).symlink_to(outside)
    except OSError:
        pytest.skip("Symlink privilege unavailable")
    assert manager.get(job.id).state == "failed"
    assert outside.exists()


@pytest.mark.parametrize("url", ["http://evil.example:8188", "http://localhost:8188", "https://127.0.0.1:8188", "http://127.0.0.1:8188/path", "http://user@127.0.0.1:8188"])
def test_endpoint_restrictions(url):
    with pytest.raises(ValueError):
        ComfyUIClient(url)


def test_unavailable_and_redirect():
    client = ComfyUIClient("http://127.0.0.1:8188")
    client.http.close()
    def offline(request):
        raise httpx.ConnectError("offline", request=request)
    client.http = httpx.Client(transport=httpx.MockTransport(offline))
    with pytest.raises(ManagerError):
        client.request("/queue")
    client.http.close()
    client.http = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(302, headers={"Location": "http://evil.example"})))
    with pytest.raises(ManagerError):
        client.request("/queue")
    client.close()


def test_api_security_and_output(manager, tmp_path):
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key=KEY, development_generation=manager)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/api/dev/generation/config").json()["enabled"]
        assert client.post("/api/dev/generation/jobs", json={"prompt": "x"}).status_code == 403
        headers = {"X-Director-Key": KEY}
        for extra in [{"Origin": "http://evil.example"}, {"Host": "evil.example"}]:
            assert client.post("/api/dev/generation/jobs", headers={**headers, **extra}, json={"prompt": "x"}).status_code == 403
        assert client.post("/api/dev/generation/jobs", headers=headers, json={"prompt": "x", "steps": 1}).status_code == 422
        response = client.post("/api/dev/generation/jobs", headers=headers, json={"prompt": "x"})
        assert response.status_code == 202
        job = manager.jobs[response.json()["id"]]
        assert client.get(f"/api/dev/generation/jobs/{job.id}").status_code == 403
        filename = finish(manager, job)
        (tmp_path / filename).write_bytes(b"\x1a\x45\xdf\xa3fixture")
        assert client.get(f"/api/dev/generation/jobs/{job.id}", headers=headers).json()["state"] == "completed"
        video = client.get(f"/api/dev/generation/jobs/{job.id}/output", headers=headers)
        assert video.status_code == 200 and video.headers["content-type"] == "video/webm"
        assert video.headers["x-director-job"] == job.id
        assert client.get("/api/dev/generation/jobs/unknown", headers=headers).status_code == 404


def test_disabled_default(tmp_path, monkeypatch):
    monkeypatch.delenv("DIRECTOR_ENABLE_DEV_GENERATION", raising=False)
    with TestClient(create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key=KEY), base_url="http://127.0.0.1") as client:
        assert client.get("/api/dev/generation/config").json()["enabled"] is False
        assert client.post("/api/dev/generation/jobs", headers={"X-Director-Key": KEY}, json={"prompt": "x"}).status_code == 404
