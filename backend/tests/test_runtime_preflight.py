"""Tiny offline archives, synthetic consent text and fake failure injection."""
import hashlib
import io
import json
import stat
import threading
import zipfile
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from director.installations.schemas import Cancelled, ManagerError, digest
from director.main import PROJECT_ROOT, create_app
from director.models.validation import relative_file_path
from director.runtimes.preflight import RuntimePreflight
from director.runtimes.review import RuntimeConsentStore, RuntimeReview
from director.runtimes.schemas import RuntimeProfile, RuntimeReceipt, profile_digest
from director.runtimes.source import ExtractionLimits, SourceFile, SourceInventory, SourceVerifier, source_path, git_tree_digest
from director.runtimes.storage import RuntimeStorageManager
from director.runtimes.manager import RuntimeProvisioningManager
from director.runtimes.fixtures import fixture_profile, PAYLOADS

KEY = "runtime-review-offline-test-" * 2
DATA = {".github/test.txt": b"inert fixture", "lib/__init__.py": b"# text only\n",
        "blueprints/First & Last (fixture).json": b"{}"}


def inventory(data=DATA):
    files = [SourceFile(path=path, size_bytes=len(payload),
                        git_blob_sha1=hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest(),
                        sha256=hashlib.sha256(payload).hexdigest()) for path, payload in data.items()]
    return SourceInventory(revision="a" * 40, tree=git_tree_digest(files), archive_root="ComfyUI-" + "a" * 40,
                           evidence_source="offline synthetic fixture", files=files)


def make_archive(tmp_path, entries=None, *, data=DATA, compress=zipfile.ZIP_STORED):
    path = tmp_path / (uuid4().hex + ".zip")
    with zipfile.ZipFile(path, "w", compression=compress) as archive:
        for name, payload in entries if entries is not None else [(inventory().archive_root + "/" + p, b) for p, b in data.items()]:
            archive.writestr(name, payload)
    return path


@pytest.fixture
def source(tmp_path):
    storage = RuntimeStorageManager(tmp_path / "owned-runtime")
    spec = inventory()
    verifier = SourceVerifier(spec, approved_digest=digest(spec.model_dump()), revision=spec.revision)
    yield storage, spec, verifier
    storage.close()


def extract(source, archive, **kwargs):
    storage, _, verifier = source
    return verifier.extract(storage, archive, job_id=kwargs.pop("job_id", "c" * 32),
                            archive_size=archive.stat().st_size,
                            archive_sha256=kwargs.pop("archive_sha256", hashlib.sha256(archive.read_bytes()).hexdigest()), **kwargs)


def test_legitimate_source_extract_and_scoped_cleanup(source, tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", lambda *_a, **_k: pytest.fail("No process execution"))
    archive = make_archive(tmp_path)
    result = extract(source, archive)
    assert result["structurally_verified"] and not result["activated"] and not result["execution_validated"]
    for path, data in DATA.items():
        assert (source[0].staging("c" * 32) / path).read_bytes() == data
    with pytest.raises(ValueError):
        relative_file_path("lib/__init__.py")  # Original policy remains unchanged.
    with pytest.raises(ManagerError, match="overwrite"):
        extract(source, archive)
    source[2].cleanup(source[0], "c" * 32)
    assert not source[0].staging("c" * 32).exists()


@pytest.mark.parametrize("path", ["/absolute", "../escape", "C:/file", "a\\b", "//server/file", "a//b",
                                   "a/./b", "a/../b", "NUL.txt", "aux/file", "file:stream", "file.", "file ", "a\0b"])
def test_source_path_rejects_unsafe_names(path):
    with pytest.raises(ValueError):
        source_path(path)


@pytest.mark.parametrize("name", ["../escape", "/outside", "C:/outside", "root\\escape", "wrong/file"])
def test_malicious_archive_rejected_before_writes(source, tmp_path, name):
    with pytest.raises(ManagerError):
        extract(source, make_archive(tmp_path, [(name, b"bad")]))
    assert not source[0].staging("c" * 32).exists()


def test_duplicate_archive(source, tmp_path):
    name = source[1].archive_root + "/.github/test.txt"
    with pytest.warns(UserWarning, match="Duplicate"):
        archive = make_archive(tmp_path, [(name, DATA[".github/test.txt"])] * 2)
    with pytest.raises(ManagerError) as error:
        extract(source, archive)
    assert error.value.code == "duplicate_archive_entry"


@pytest.mark.parametrize("kind", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFSOCK])
def test_archive_special_types(source, tmp_path, kind):
    item = zipfile.ZipInfo(source[1].archive_root + "/.github/test.txt")
    item.create_system = 3
    item.external_attr = (kind | 0o600) << 16
    with pytest.raises(ManagerError) as error:
        extract(source, make_archive(tmp_path, [(item, b"link target")]))
    assert error.value.code == "unsafe_archive_type"


def test_missing_unexpected_and_corrupt_source(source, tmp_path):
    root = source[1].archive_root + "/"
    for entries, code in [([(root + ".github/test.txt", DATA[".github/test.txt"])], "source_files_missing"),
                          ([(root + "extra", b"x")], "unexpected_archive_entry")]:
        with pytest.raises(ManagerError) as error:
            extract(source, make_archive(tmp_path, entries), job_id=uuid4().hex)
        assert error.value.code == code
    altered = {**DATA, "lib/__init__.py": b"x" * len(DATA["lib/__init__.py"])}
    with pytest.raises(ManagerError) as error:
        extract(source, make_archive(tmp_path, data=altered))
    assert error.value.code == "source_hash"
    record = source[0].read_json(source[0].path("source-jobs", "c" * 32 + ".json"))
    assert record["state"] == "failed" and record["error"] == "source_hash"
    source[2].cleanup(source[0], "c" * 32)


@pytest.mark.parametrize("limits", [dict(max_entries=1), dict(max_file_bytes=1), dict(max_total_bytes=1), dict(max_archive_bytes=1)])
def test_extraction_limits(source, tmp_path, limits):
    source[2].limits = ExtractionLimits(**limits)
    with pytest.raises(ManagerError) as error:
        extract(source, make_archive(tmp_path))
    assert error.value.code == "source_limits"


def test_compression_ratio_bomb(source, tmp_path):
    spec = inventory({"text.txt": b"0" * 10000})
    verifier = SourceVerifier(spec, approved_digest=digest(spec.model_dump()), revision=spec.revision,
                              limits=ExtractionLimits(max_ratio=2))
    archive = make_archive(tmp_path, [(spec.archive_root + "/text.txt", b"0" * 10000)], compress=zipfile.ZIP_DEFLATED)
    with pytest.raises(ManagerError) as error:
        extract((source[0], spec, verifier), archive)
    assert error.value.code == "source_limits"


def test_archive_hash_inventory_and_revision(source, tmp_path):
    with pytest.raises(ManagerError):
        extract(source, make_archive(tmp_path), archive_sha256="f" * 64)
    for args in [dict(approved_digest="f" * 64, revision=source[1].revision),
                 dict(approved_digest=digest(source[1].model_dump()), revision="f" * 40)]:
        with pytest.raises(ManagerError):
            SourceVerifier(source[1], **args)


def test_cancel_recover_and_partial_cleanup(source, tmp_path, monkeypatch):
    archive = make_archive(tmp_path)
    event = threading.Event()
    original = source[2].target
    def interrupt(*args):
        target = original(*args)
        event.set()
        return target
    monkeypatch.setattr(source[2], "target", interrupt)
    with pytest.raises(Cancelled):
        extract(source, archive, cancel=event)
    record_path = source[0].path("source-jobs", "c" * 32 + ".json")
    record = source[0].read_json(record_path)
    assert record["state"] == "cancelled"
    record["state"] = "extracting"
    source[0].write_json(record_path, record)
    source[2].recover(source[0])
    assert source[0].read_json(record_path)["state"] == "interrupted"
    source[2].cleanup(source[0], "c" * 32)
    assert not source[0].staging("c" * 32).exists()


def test_cleanup_refuses_user_additions(source, tmp_path):
    extract(source, make_archive(tmp_path))
    extra = source[0].staging("c" * 32) / "user.txt"
    extra.write_text("user file")
    with pytest.raises(ManagerError):
        source[2].cleanup(source[0], "c" * 32)
    assert extra.read_text() == "user file"


def synthetic_review():
    review = RuntimeReview.model_validate_json((PROJECT_ROOT / "runtime_profiles/reviews/wan-windows-candidate.json").read_text())
    text = "MOCK runtime document. Synthetic test text only."
    review.required_document_ids = ["fixture-license"]
    review.notice_classifications = []
    from director.models.schemas import LicenseDocument
    review.documents = [LicenseDocument(id="fixture-license", version="1", text=text, sha256=hashlib.sha256(text.encode()).hexdigest())]
    review.license_review_complete = True
    review.unresolved_requirements = []
    return review


def test_consent_explicit_missing_changed_documents(source):
    consent = RuntimeConsentStore(source[0])
    review = synthetic_review()
    current = consent.requirements(review)["document_set_digest"]
    for value in [False, 1, "true", None]:
        with pytest.raises(ManagerError):
            consent.record(review, current, accepted=value)
    record = consent.record(review, current, accepted=True)
    consent.check(review, record.id)
    assert "runtime-acknowledgements" in str(source[0].path("runtime-acknowledgements", record.id + ".json"))
    review.documents[0].version = "2"
    with pytest.raises(ManagerError) as error:
        consent.check(review, record.id)
    assert error.value.code == "stale_runtime_acknowledgement"
    with pytest.raises(ManagerError):
        consent.record(review, current, accepted=True)
    review.documents = []
    with pytest.raises(ManagerError):
        consent.record(review, consent.requirements(review)["document_set_digest"], accepted=True)


def test_preflight_read_only_lock_inventory_disk_and_gates(source):
    manager = SimpleNamespace(storage=source[0], has_active_jobs=lambda: False)
    service = RuntimePreflight(PROJECT_ROOT, manager, disk_usage=lambda _: SimpleNamespace(free=100 * 1024**3))
    profile = RuntimeProfile.model_validate_json((PROJECT_ROOT / "runtime_profiles/wan-windows-candidate.json").read_text())
    report = service.report(profile)
    assert not source[0].base.exists()
    assert report["verified_wheel_download_bytes"] == 2677041805
    assert not report["provisionable"] and not report["installation_authorized"]
    assert {e["subject"] for e in report["evidence"]} >= {"dependency_lock", "python_bootstrap", "comfyui_inventory"}
    assert {b["code"] for b in report["blockers"]} >= {"runtime_documents_missing", "installation_not_authorized", "real_runtime_disabled", "runtime_root_not_owned"}
    source[0].ensure_owned()
    service.disk_usage = lambda _: SimpleNamespace(free=1)
    assert "insufficient_disk_space" in {b["code"] for b in service.report(profile)["blockers"]}


def test_real_source_inventory_paths():
    value = SourceInventory.model_validate_json((PROJECT_ROOT / "runtime_profiles/sources/wan-comfyui.inventory.json").read_text())
    assert len(value.files) == 1248
    assert sum(f.size_bytes for f in value.files) == 48552928
    assert any("__init__.py" in f.path for f in value.files)


def test_runtime_api_authorization_and_missing_review(tmp_path):
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key=KEY)
    base = "/api/runtime/profiles/wan-windows-candidate"
    headers = {"X-Director-Key": KEY}
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get(base + "/preflight").status_code == 403
        assert client.get(base + "/preflight", headers={**headers, "Origin": "https://evil.example"}).status_code == 403
        assert client.get(base + "/preflight", headers={**headers, "Host": "evil.example"}).status_code == 403
        report = client.get(base + "/preflight", headers=headers)
        assert report.status_code == 200 and report.json()["provisionable"] is False
        review = client.get(base + "/runtime-review", headers=headers).json()
        assert review["review_complete"] is False and review["missing_document_ids"]
        body = {"document_set_digest": review["document_set_digest"], "accepted": True}
        assert client.post(base + "/runtime-acknowledgements", json=body, headers=headers).status_code == 412
        assert client.post(base + "/runtime-acknowledgements", json=body).status_code == 403
        body["accepted"] = "true"
        assert client.post(base + "/runtime-acknowledgements", json=body, headers=headers).status_code == 422
        assert client.get("/api/runtime/profiles/missing/preflight", headers=headers).status_code == 404


def test_review_api_success_is_consent_not_installation(tmp_path, monkeypatch):
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key=KEY)
    base = "/api/runtime/profiles/wan-windows-candidate"
    headers = {"X-Director-Key": KEY, "Origin": "http://127.0.0.1"}
    with TestClient(app, base_url="http://127.0.0.1") as client:
        review = synthetic_review()
        monkeypatch.setattr(app.state.runtime_preflight, "review", lambda _: review)
        packet = client.get(base + "/runtime-review", headers=headers).json()
        record = client.post(base + "/runtime-acknowledgements", headers=headers,
                             json={"document_set_digest": packet["document_set_digest"], "accepted": True})
        assert record.status_code == 201
        result = client.get(base + "/preflight?acknowledgement_id=" + record.json()["id"], headers=headers).json()
        assert not result["provisionable"] and not result["installation_authorized"]
        assert "runtime_acknowledgement_missing" not in {b["code"] for b in result["blockers"]}
        review.documents[0].version = "2"
        result = client.get(base + "/preflight?acknowledgement_id=" + record.json()["id"], headers=headers).json()
        assert "stale_runtime_acknowledgement" in {b["code"] for b in result["blockers"]}


def test_api_requires_configured_manager_key(tmp_path, monkeypatch):
    monkeypatch.delenv("DIRECTOR_MANAGER_TOKEN", raising=False)
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime")
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/api/runtime/profiles/wan-windows-candidate/preflight").status_code == 503


def test_inventory_tree_and_duplicate_names_rejected():
    value = inventory().model_dump()
    value["files"][0]["git_blob_sha1"] = "f" * 40
    with pytest.raises(ValidationError, match="Git tree"):
        SourceInventory.model_validate(value)
    value = inventory().model_dump()
    value["files"].append(value["files"][0])
    with pytest.raises(ValidationError, match="Duplicate"):
        SourceInventory.model_validate(value)


def test_source_symlink_and_junction_escape(source, tmp_path):
    import subprocess, os
    outside = tmp_path / "outside"
    outside.mkdir()
    source[0].ensure_owned()
    bundle = source[0].staging("c" * 32)
    bundle.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # A junction creation command is a test fixture, never a source process.
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(bundle), str(outside)], capture_output=True, timeout=5)
        assert result.returncode == 0
    else:
        bundle.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises((ManagerError, ValueError)):
            extract(source, make_archive(tmp_path))
        assert not list(outside.iterdir())
    finally:
        os.rmdir(bundle) if os.name == "nt" else bundle.unlink()


def test_failed_activation_job_cleanup(tmp_path, monkeypatch):
    import time
    manager = RuntimeProvisioningManager(RuntimeStorageManager(tmp_path / "runtime"), enabled=True)
    original = manager.storage.write_json
    def fail(path, data):
        if path.parent.name == "installations":
            raise OSError("fake publish failure")
        original(path, data)
    monkeypatch.setattr(manager.storage, "write_json", fail)
    try:
        profile = fixture_profile()
        job = manager.start(profile, "provision", profile_digest(profile))
        for _ in range(200):
            result = manager.get(job.id)
            if result.state == "failed":
                break
            time.sleep(.01)
        assert result.state == "failed"
        assert manager.storage.active(profile.id) is None
        assert manager.storage.staging(job.id).exists()
        assert manager.cleanup_staging(job.id)["staging_removed"]
    finally:
        manager.close()


def test_preflight_missing_inventory_changed_lock_and_storage_conflicts(source, tmp_path):
    import shutil
    for relative in ["runtime_profiles/wan-windows-candidate.json", "runtime_profiles/reviews/wan-windows-candidate.json",
                     "runtime_profiles/locks/wan-windows-cp313-cu130.lock.json", "runtime_profiles/locks/wan-windows-comfyui-requirements.txt"]:
        dest = tmp_path / "project" / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, dest)
    profile = RuntimeProfile.model_validate_json((PROJECT_ROOT / "runtime_profiles/wan-windows-candidate.json").read_text())
    service = RuntimePreflight(tmp_path / "project", SimpleNamespace(storage=source[0], has_active_jobs=lambda: True),
                               disk_usage=lambda _: SimpleNamespace(free=100 * 1024**3))
    result = service.report(profile)
    assert "source_inventory_missing" in {b["code"] for b in result["blockers"]}
    lock = tmp_path / "project/runtime_profiles/locks/wan-windows-cp313-cu130.lock.json"
    lock.write_text(lock.read_text() + "\n")
    result = service.report(profile)
    assert "runtime_lock_invalid" in {b["code"] for b in result["blockers"]}
    assert "runtime_busy" in {b["code"] for b in result["blockers"]}


@pytest.mark.parametrize("when", ["before", "after"])
def test_fixture_failed_activation_returns_to_staging_and_preserves_old_pointer(source, monkeypatch, when):
    storage = source[0]
    storage.ensure_owned()
    profile = fixture_profile()
    def receipt(job_id):
        stage = storage.staging(job_id)
        for artifact in profile.artifacts:
            path = storage.component_path(stage, artifact.destination)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(PAYLOADS[artifact.destination])
        manager = RuntimeProvisioningManager(storage, enabled=True)
        results = manager.verify_bundle(stage, profile, receipt=False)
        manager._executor.shutdown()
        return RuntimeReceipt(job_id=job_id, owner_id=storage.owner_id(), profile=profile,
                              profile_digest=profile_digest(profile), verification=results)
    old = receipt("d" * 32)
    storage.activate(old)
    new = receipt("e" * 32)
    original = storage.write_json
    def fail(path, data):
        if path.parent.name == "installations" and data.get("job_id") == new.job_id:
            if when == "after":
                original(path, data)
            raise OSError("fake atomic publish failure")
        original(path, data)
    monkeypatch.setattr(storage, "write_json", fail)
    with pytest.raises(OSError):
        storage.activate(new)
    assert storage.active(profile.id) == old
    assert storage.staging(new.job_id).exists()
    assert not storage.installed(profile.id, new.job_id).exists()
