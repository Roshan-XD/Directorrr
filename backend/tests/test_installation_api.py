import time

import pytest
from fastapi.testclient import TestClient

from director.main import create_app, get_hardware

KEY = "offline-test-manager-key-1234567890"


@pytest.fixture
def client(tmp_path, hardware):
    app = create_app(model_root=tmp_path / "models", enable_fixtures=True,
                     allow_real_downloads=False, manager_key=KEY)
    app.dependency_overrides[get_hardware] = lambda: hardware
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Director-Key": KEY}) as client:
        yield client


def wait(client, response):
    assert response.status_code == 202, response.text
    job_id = response.json()["id"]
    for _ in range(300):
        result = client.get(f"/api/installation-jobs/{job_id}")
        assert result.status_code == 200
        if result.json()["state"] in {"ready", "failed", "cancelled", "corrupted", "not_installed"}:
            return result.json()
        time.sleep(0.01)
    pytest.fail("API job timeout")


def test_full_offline_api_flow(client):
    base = "/api/models/fixture-tiny"
    requirements = client.get(base + "/license-requirements").json()
    ack = client.post(base + "/license-acknowledgements",json={"accepted":True,
        "document_set_digest":requirements["document_set_digest"]})
    assert ack.status_code == 201
    job = wait(client,client.post(base + "/installations",json={
        "manifest_digest":requirements["manifest_digest"],"acknowledgement_id":ack.json()["id"]}))
    assert job["state"] == "ready" and job["generation_ready"] is False
    status = client.get(base + "/installation").json()
    assert status["artifact_ready"] and not status["generation_ready"]
    assert wait(client,client.post(base + "/installation/verify"))["state"] == "ready"
    assert client.post(f"/api/installation-jobs/{job['id']}/cancel").status_code == 409
    assert wait(client,client.delete(base + "/installation"))["state"] == "not_installed"
    assert not client.get(base + "/installation").json()["artifact_ready"]


@pytest.mark.parametrize("accepted", [False,1,"true",None])
def test_explicit_license_boolean(client,accepted):
    response = client.post("/api/models/fixture-tiny/license-acknowledgements",json={
        "accepted":accepted,"document_set_digest":"0" * 64})
    assert response.status_code == 422


def test_missing_ack_and_disabled_wan(client):
    base = "/api/models/fixture-tiny"
    requirement = client.get(base + "/license-requirements").json()
    response = client.post(base + "/installations",json={
        "manifest_digest":requirement["manifest_digest"],"acknowledgement_id":"0" * 32})
    assert response.status_code == 412 and response.json()["detail"]["code"] == "acknowledgement_missing"
    manifests = client.app.state.manifests
    from director.installations.schemas import manifest_digest
    wan = next(model for model in manifests if model.id == "wan-2-1-t2v-1-3b")
    response = client.post("/api/models/wan-2-1-t2v-1-3b/installations",json={
        "manifest_digest":manifest_digest(wan),"acknowledgement_id":"0" * 32})
    assert response.status_code == 412 and response.json()["detail"]["code"] == "real_downloads_disabled"


@pytest.mark.parametrize("suffix,method", [("installation","get"),("installation","delete"),
    ("installation/verify","post"),("license-requirements","get"),
    ("license-acknowledgements","post"),("installations","post")])
def test_unknown_model_id(client,suffix,method):
    assert getattr(client,method)(f"/api/models/unknown-model/{suffix}").status_code == 404


def test_bad_job_and_request(client):
    assert client.get("/api/installation-jobs/bad-id").status_code == 404
    assert client.post("/api/installation-jobs/bad-id/cancel").status_code == 404
    assert client.post("/api/models/fixture-tiny/installations",json={"manifest_digest":"bad"}).status_code == 422
    assert client.post("/api/models/fixture-tiny/installation/verify").status_code == 404


@pytest.mark.parametrize("headers", [{"X-Director-Key":"wrong"},
    {"Origin":"https://malicious.example"},{"Host":"malicious.example"}])
def test_local_mutation_authorization(client,headers):
    assert client.delete("/api/models/fixture-tiny/installation",headers=headers).status_code == 403


def test_default_no_mutations_or_storage_creation(tmp_path,monkeypatch):
    monkeypatch.delenv("DIRECTOR_MANAGER_TOKEN",raising=False)
    root = tmp_path / "models"
    with TestClient(create_app(model_root=root,enable_fixtures=False,allow_real_downloads=False),base_url="http://127.0.0.1") as client:
        assert client.delete("/api/models/wan-2-1-t2v-1-3b/installation").status_code == 503
        assert client.get("/api/models/fixture-tiny/installation").status_code == 404
    assert not root.exists()


def test_cancel_active_job_api(client):
    import threading
    from director.installations.schemas import Cancelled
    entered=threading.Event()
    def blocked(component,cache,cancel,progress,allowlist):
        entered.set()
        assert cancel.wait(3)
        raise Cancelled()
    client.app.state.installations.fixture_downloader.fetch=blocked
    base="/api/models/fixture-tiny"
    terms=client.get(base+"/license-requirements").json()
    ack=client.post(base+"/license-acknowledgements",json={"accepted":True,"document_set_digest":terms["document_set_digest"]}).json()
    response=client.post(base+"/installations",json={"manifest_digest":terms["manifest_digest"],"acknowledgement_id":ack["id"]})
    assert response.status_code==202 and entered.wait(2)
    assert client.post("/api/installation-jobs/"+response.json()["id"]+"/cancel").status_code==202
    assert wait(client,response)["state"]=="cancelled"
