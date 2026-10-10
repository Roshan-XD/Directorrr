import hashlib
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from director.main import create_app
from director.installations.schemas import ManagerError
from director.runtimes.fixtures import FixtureProvider, PAYLOADS, fixture_profile
from director.runtimes.manager import RuntimeProvisioningManager
from director.runtimes.schemas import RuntimeProfile, profile_digest
from director.runtimes.storage import RuntimeStorageManager

KEY = "offline-runtime-test-key-" * 2


def wait(manager, job):
    for _ in range(200):
        current = manager.get(job.id)
        if current.state in {"installed_unvalidated", "not_installed", "failed", "cancelled", "corrupted", "interrupted"}:
            return current
        time.sleep(0.01)
    pytest.fail("Fixture job did not finish")


@pytest.fixture
def manager(tmp_path):
    item = RuntimeProvisioningManager(RuntimeStorageManager(tmp_path / "runtimes"), enabled=True)
    yield item
    item.close()


def install(manager):
    profile = fixture_profile()
    return wait(manager, manager.start(profile, "provision", profile_digest(profile)))


def test_fixture_never_executes_or_downloads(manager, monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", lambda *_a, **_k: pytest.fail("No process may execute"))
    profile = fixture_profile()
    assert manager.plan(profile)["total_expected_bytes"] == sum(map(len, PAYLOADS.values()))
    assert not manager.storage.base.exists()  # Planning creates nothing.
    job = install(manager)
    assert job.state == "installed_unvalidated"
    assert not job.execution_validated and not job.generation_ready
    assert all(item.valid for item in job.verification)
    verified = wait(manager, manager.start(profile, "verify"))
    assert verified.state == "installed_unvalidated"
    status = manager.status(profile)
    assert status["structurally_verified"] and not status["execution_validated"]


@pytest.mark.parametrize("change", [
    {"schema_version": 99}, {"comfyui_commit": "main"}, {"python_version": "garbage"},
    {"execution_validated": True}, {"status": "validated"}, {"unexpected": "command"},
])
def test_invalid_profiles(change):
    data = fixture_profile().model_dump()
    data.update(change)
    with pytest.raises(ValidationError):
        RuntimeProfile.model_validate(data)


@pytest.mark.parametrize("destination", ["../outside", "C:/outside", "a\\b", "env/con.txt", "receipt.json", "env/file:stream"])
def test_unsafe_profile_destinations(destination):
    data = fixture_profile().model_dump()
    data["artifacts"][0]["destination"] = destination
    with pytest.raises(ValidationError):
        RuntimeProfile.model_validate(data)


def test_duplicate_and_ancestor_destinations():
    for path in ("PYTHON/fixture.TXT", "python/FIXTURE.txt/nested"):
        data = fixture_profile().model_dump()
        data["artifacts"][1]["destination"] = path
        with pytest.raises(ValidationError):
            RuntimeProfile.model_validate(data)


@pytest.mark.parametrize("field,value", [("url", "https://token@host/file"), ("expected_size_bytes", True), ("expected_size_bytes", -1), ("sha256", "bad")])
def test_invalid_artifact_metadata(field, value):
    data = fixture_profile().model_dump()
    data["artifacts"][0][field] = value
    with pytest.raises(ValidationError):
        RuntimeProfile.model_validate(data)


def test_real_candidate_is_partial_and_blocked(manager):
    profile = RuntimeProfile.model_validate_json(Path("runtime_profiles/wan-windows-candidate.json").read_text())
    assert profile.python_version == "3.13.16" and not profile.execution_validated
    plan = manager.plan(profile)
    assert plan["total_expected_bytes"] is None and not plan["provisionable"]
    assert plan["blockers"][0]["code"] == "real_runtime_disabled"
    with pytest.raises(ManagerError, match="not implemented"):
        manager.start(profile, "provision", profile_digest(profile))


def test_missing_metadata_and_unknowns_preserved():
    profile = RuntimeProfile(id="unknown", name="Unknown candidate")
    assert profile.python_version is None and profile.comfyui_commit is None and not profile.artifacts


@pytest.mark.parametrize("corruption,code", [("missing", "missing"), ("short", "size_mismatch"), ("hash", "checksum_mismatch")])
def test_structural_verification_detects_corruption(manager, corruption, code):
    job = install(manager)
    profile = fixture_profile()
    path = manager.storage.installed(profile.id, job.id) / profile.artifacts[0].destination
    if corruption == "missing":
        path.unlink()
    elif corruption == "short":
        path.write_bytes(b"short")
    else:
        path.write_bytes(b"X" * profile.artifacts[0].expected_size_bytes)
    assert manager.status(profile)["state"] == "corrupted"
    verified = wait(manager, manager.start(profile, "verify"))
    assert verified.state == "corrupted" and verified.verification[0].code == code
    assert not manager.status(profile)["structurally_verified"]
    # Removal is safe even when allowlisted files are missing/corrupted.
    assert wait(manager, manager.start(profile, "remove")).state == "not_installed"


class BlockingProvider(FixtureProvider):
    def __init__(self):
        self.entered, self.release = threading.Event(), threading.Event()
    def payload(self, artifact):
        self.entered.set()
        assert self.release.wait(3)
        return super().payload(artifact)


def test_cancellation_concurrency_and_safe_staging_cleanup(manager):
    provider = BlockingProvider()
    manager.provider = provider
    profile = fixture_profile()
    job = manager.start(profile, "provision", profile_digest(profile))
    try:
        assert provider.entered.wait(2)
        with pytest.raises(ManagerError, match="active"):
            manager.start(profile, "provision", profile_digest(profile))
        with pytest.raises(ManagerError, match="stopped"):
            manager.cleanup_staging(job.id)
        manager.cancel(job.id)
    finally:
        provider.release.set()
    assert wait(manager, job).state == "cancelled"
    assert manager.storage.active(profile.id) is None
    assert manager.cleanup_staging(job.id)["staging_removed"]
    assert not manager.storage.staging(job.id).exists()


def test_wrong_bytes_fail_before_activation(manager):
    manager.provider = SimpleNamespace(payload=lambda artifact: b"X" * artifact.expected_size_bytes)
    job = install(manager)
    assert job.state == "failed" and job.error["code"] == "artifact_integrity_failed"
    assert manager.storage.active(fixture_profile().id) is None


def test_space_rechecked(manager, monkeypatch):
    calls = []
    original = manager.storage.check_space
    def check(size):
        calls.append(size)
        if len(calls) > 1:
            raise ManagerError("insufficient_disk_space", "Fixture disk space insufficient")
        original(size)
    monkeypatch.setattr(manager.storage, "check_space", check)
    assert install(manager).error["code"] == "insufficient_disk_space"
    assert manager.storage.active(fixture_profile().id) is None


def test_safe_removal_refuses_user_additions(manager):
    job = install(manager)
    profile = fixture_profile()
    bundle = manager.storage.installed(profile.id, job.id)
    user_file = bundle / "user.txt"
    user_file.write_text("user-owned data")
    failed = wait(manager, manager.start(profile, "remove"))
    assert failed.state == "failed" and user_file.read_text() == "user-owned data"
    assert manager.storage.active(profile.id) is not None


def test_receipt_identity_and_owner_corruption(manager):
    job = install(manager)
    profile = fixture_profile()
    receipt_path = manager.storage.installed(profile.id, job.id) / "receipt.json"
    receipt = manager.storage.read_json(receipt_path)
    receipt["profile_digest"] = "f" * 64
    manager.storage.write_json(receipt_path, receipt)
    assert manager.status(profile)["state"] == "corrupted"
    with pytest.raises(ManagerError):
        manager.start(profile, "remove")


def test_recovery_never_resumes(tmp_path):
    storage = RuntimeStorageManager(tmp_path / "runtime")
    manager = RuntimeProvisioningManager(storage, enabled=True)
    job = install(manager)
    path = storage.path("jobs", job.id + ".json")
    record = storage.read_json(path)
    record["state"] = "activating"
    storage.write_json(path, record)
    manager.close()
    recovered = RuntimeProvisioningManager(RuntimeStorageManager(storage.root), enabled=True,
                                          provider=SimpleNamespace(payload=lambda _: pytest.fail("No auto resume")))
    try:
        assert recovered.get(job.id).state == "interrupted"
        assert recovered.status(fixture_profile())["state"] == "interrupted"
        assert wait(recovered, recovered.start(fixture_profile(), "verify")).state == "installed_unvalidated"
    finally:
        recovered.close()


def test_existing_incomplete_stage_recovered_and_cleaned(tmp_path):
    manager = RuntimeProvisioningManager(RuntimeStorageManager(tmp_path / "runtime"), enabled=True)
    manager.provider = SimpleNamespace(payload=lambda _: (_ for _ in ()).throw(OSError("fixture failure")))
    job = install(manager)
    path = manager.storage.path("jobs", job.id + ".json")
    record = manager.storage.read_json(path)
    record["state"] = "staging"
    manager.storage.write_json(path, record)
    manager.close()
    recovered = RuntimeProvisioningManager(RuntimeStorageManager(tmp_path / "runtime"), enabled=True)
    try:
        assert recovered.get(job.id).state == "interrupted"
        assert recovered.cleanup_staging(job.id)["staging_removed"]
    finally:
        recovered.close()


def test_root_lock_and_unowned_namespace(tmp_path, manager):
    install(manager)
    with pytest.raises(ManagerError, match="owns"):
        RuntimeProvisioningManager(RuntimeStorageManager(manager.storage.root), enabled=True)
    root = tmp_path / "unowned"
    (root / ".director-runtime").mkdir(parents=True)
    with pytest.raises(ManagerError, match="not owned"):
        RuntimeProvisioningManager(RuntimeStorageManager(root))


@pytest.mark.parametrize("root", [Path("relative"), Path(sys.prefix) / "runtime", Path(sys.base_prefix) / "runtime"])
def test_protected_roots(root):
    with pytest.raises(ManagerError):
        RuntimeStorageManager(root)


def test_reparse_escape_without_privileges(tmp_path, monkeypatch):
    from director.installations import verifier
    original = verifier.is_link
    monkeypatch.setattr(verifier, "is_link", lambda path: path == tmp_path or original(path))
    with pytest.raises(ManagerError):
        RuntimeStorageManager(tmp_path / "nested")


def test_symlink_escape_where_supported(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Windows symlink privilege unavailable")
    with pytest.raises(ManagerError):
        RuntimeStorageManager(link / "runtime")


def test_windows_runtime_junction_escape(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows-specific junction test")
    from director.installations.verifier import is_link
    external = tmp_path / "outside"
    external.mkdir()
    sentinel = external / "user.txt"
    sentinel.write_text("User-owned file", encoding="utf-8")
    junction = tmp_path / "junction"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(external)],
                            capture_output=True, timeout=5)
    assert result.returncode == 0
    try:
        assert is_link(junction)
        with pytest.raises(ManagerError):
            RuntimeStorageManager(junction / "runtime")
    finally:
        assert junction.parent == tmp_path and is_link(junction)
        os.rmdir(junction)  # Removes the checked junction, never its external target.
    assert sentinel.read_text(encoding="utf-8") == "User-owned file"


@pytest.fixture
def client(tmp_path):
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtimes",
                     enable_runtime_fixtures=True, manager_key=KEY)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        yield client


def test_api_complete_flow(client):
    profiles = client.get("/api/runtime/profiles").json()
    assert profiles["real_provisioning_enabled"] is False
    profile_id = "runtime-fixture-tiny"
    base = f"/api/runtime/profiles/{profile_id}"
    plan = client.get(base + "/installation-plan").json()
    assert plan["provisionable"] and not plan["generation_ready"]
    headers = {"X-Director-Key": KEY, "Origin": "http://127.0.0.1"}
    response = client.post(base + "/provision", json={"profile_digest": plan["profile_digest"], "confirmed": True}, headers=headers)
    assert response.status_code == 202
    job = response.json()
    manager = client.app.state.runtimes
    assert wait(manager, SimpleNamespace(id=job["id"])).state == "installed_unvalidated"
    assert client.get("/api/runtime/jobs/" + job["id"]).json()["execution_validated"] is False
    assert client.get(base + "/installation").json()["structurally_verified"]
    verify = client.post(base + "/installation/verify", headers=headers)
    assert wait(manager, SimpleNamespace(id=verify.json()["id"])).state == "installed_unvalidated"
    remove = client.delete(base + "/installation", headers=headers)
    assert wait(manager, SimpleNamespace(id=remove.json()["id"])).state == "not_installed"


@pytest.mark.parametrize("headers", [{}, {"X-Director-Key": "wrong"}, {"X-Director-Key": KEY, "Origin": "https://evil.example"}])
def test_mutation_auth_and_origin(client, headers):
    response = client.post("/api/runtime/profiles/runtime-fixture-tiny/provision", json={"profile_digest": "a" * 64, "confirmed": True}, headers=headers)
    assert response.status_code == 403
    assert not client.app.state.runtimes.storage.base.exists()


def test_api_stale_confirmation_and_invalid_ids(client):
    base = "/api/runtime/profiles/runtime-fixture-tiny"
    headers = {"X-Director-Key": KEY}
    assert client.post(base + "/provision", json={"profile_digest": "f" * 64, "confirmed": True}, headers=headers).status_code == 409
    for acceptance in (False, "true", 1):
        assert client.post(base + "/provision", json={"profile_digest": "f" * 64, "confirmed": acceptance}, headers=headers).status_code == 422
    assert client.get("/api/runtime/profiles/unknown/installation-plan").status_code == 404
    assert client.get("/api/runtime/jobs/invalid").status_code == 404
    assert client.post("/api/runtime/profiles/wan-windows-candidate/provision", json={"profile_digest": "f" * 64, "confirmed": True}, headers=headers).status_code == 412


def test_disabled_default_and_manager_key_required(tmp_path):
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", enable_runtime_fixtures=False)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert not any(item["is_fixture"] for item in client.get("/api/runtime/profiles").json()["profiles"])
        assert client.post("/api/runtime/profiles/wan-windows-candidate/provision", json={"profile_digest": "a" * 64, "confirmed": True}).status_code == 503


def test_runtime_ownership_tampering_is_not_verified(manager):
    install(manager)
    owner_path = manager.storage.path("owner.json")
    owner = manager.storage.read_json(owner_path)
    owner["id"] = "f" * 32
    manager.storage.write_json(owner_path, owner)
    assert manager.status(fixture_profile())["state"] == "corrupted"
    with pytest.raises(ManagerError):
        manager.start(fixture_profile(), "remove")


def test_terminal_job_cannot_be_cancelled_or_staging_cleaned(manager):
    job = install(manager)
    with pytest.raises(ManagerError) as error:
        manager.cancel(job.id)
    assert error.value.status_code == 409
    with pytest.raises(ManagerError):
        manager.cleanup_staging(job.id)


def test_runtime_mutation_rejects_untrusted_host(client):
    response = client.post("/api/runtime/profiles/runtime-fixture-tiny/provision",
                           headers={"Host": "evil.example", "X-Director-Key": KEY},
                           json={"confirmed": True, "profile_digest": "a" * 64})
    assert response.status_code in {400, 403}
    assert not client.app.state.runtimes.storage.base.exists()
