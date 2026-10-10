"""The new artifact snapshot never changes the legacy generation plan contract."""
import pytest
from fastapi.testclient import TestClient
from director.main import create_app, get_hardware

KEY = "offline-test-manager-key-1234567890"

def app_client(root, hardware, **kwargs):
    app = create_app(model_root=root, enable_fixtures=True, allow_real_downloads=False, **kwargs)
    app.dependency_overrides[get_hardware] = lambda: hardware
    return TestClient(app, base_url="http://127.0.0.1")

def test_fixture_artifact_review_is_read_only(tmp_path, hardware):
    root = tmp_path / "models"
    with app_client(root, hardware, manager_key=KEY) as client:
        result = client.get("/api/models/fixture-tiny/installation-plan").json()
        assert result["ready_for_installation"] is False
        assert result["status"] == "blocked" and result["blockers"]
        review = result["artifact_review"]
        assert review["can_review"] and not review["blockers"]
        assert review["expected_download_bytes"] == 60
        assert review["required_storage_bytes"] == 180 + 16 * 1024 * 1024
        assert review["requires_acknowledgement"] and review["requires_manager_key"]
        assert review["generation_ready"] is False
        assert ".director" in review["destination_template"]
        assert not root.exists()

def test_review_blocks_missing_server_key(tmp_path, hardware):
    with app_client(tmp_path / "models", hardware) as client:
        review = client.get("/api/models/fixture-tiny/installation-plan").json()["artifact_review"]
        assert not review["can_review"]
        assert review["blockers"][0]["code"] == "manager_key_missing"

def test_review_blocks_real_model(tmp_path, hardware):
    with app_client(tmp_path / "models", hardware, manager_key=KEY) as client:
        review = client.get("/api/models/wan-2-1-t2v-1-3b/installation-plan").json()["artifact_review"]
        assert not review["can_review"]
        assert review["blockers"][0]["code"] == "real_downloads_disabled"

def test_review_rechecks_disk_space(tmp_path, hardware, monkeypatch):
    from director.installations.schemas import ManagerError
    from director.installations.storage import ModelStorageManager
    def no_space(self, size):
        raise ManagerError("insufficient_disk_space", "Insufficient space")
    monkeypatch.setattr(ModelStorageManager, "check_space", no_space)
    root = tmp_path / "models"
    with app_client(root, hardware, manager_key=KEY) as client:
        review = client.get("/api/models/fixture-tiny/installation-plan").json()["artifact_review"]
        assert not review["can_review"] and review["blockers"][0]["code"] == "insufficient_disk_space"
        assert not root.exists()

def test_review_blocks_existing_installation(tmp_path, hardware):
    from test_installation_api import wait
    with app_client(tmp_path / "models", hardware, manager_key=KEY) as client:
        client.headers["X-Director-Key"] = KEY
        base = "/api/models/fixture-tiny"
        docs = client.get(base + "/license-requirements").json()
        ack = client.post(base + "/license-acknowledgements", json={"accepted": True,
            "document_set_digest": docs["document_set_digest"]}).json()
        assert wait(client, client.post(base + "/installations", json={
            "manifest_digest": docs["manifest_digest"], "acknowledgement_id": ack["id"]}))["state"] == "ready"
        review = client.get(base + "/installation-plan").json()["artifact_review"]
        assert not review["can_review"] and review["blockers"][0]["code"] == "already_installed"
