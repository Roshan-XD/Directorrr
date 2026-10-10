"""All transfers here use synthetic bytes. No network or model weights."""
import hashlib
import os
import threading
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from director.installations.downloader import FixtureDownloader, HuggingFaceDownloader, _sdk_fetch
from director.installations.fixtures import PAYLOAD, fixture_manifest, fixture_payloads
from director.installations.jobs import InstallationJobManager
from director.installations.schemas import Cancelled, Job, ManagerError, TERMINAL, manifest_digest
from director.installations.storage import ModelStorageManager
from director.installations.verifier import ArtifactVerifier, is_link


def wait(manager, job):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = manager.get(job.id)
        if result.state in TERMINAL:
            return result
        time.sleep(0.01)
    pytest.fail("Job did not finish")


@pytest.fixture
def manager(tmp_path):
    instance = InstallationJobManager(ModelStorageManager(tmp_path / "models", safety_margin_bytes=0),
        fixture_downloader=FixtureDownloader(fixture_payloads()))
    yield instance
    instance.close()


def acknowledge(manager, model):
    requirement = manager.licenses.requirements(model)
    return manager.licenses.record(model, requirement["document_set_digest"], accepted=True).id


def install(manager, model=None):
    model = model or fixture_manifest()
    ack = acknowledge(manager, model)
    return manager.start(model, "install", manifest_digest(model), ack)


def test_success_verification_removal_and_restart(manager):
    model = fixture_manifest()
    job = wait(manager, install(manager, model))
    assert job.state == "ready" and job.verified_bytes == len(PAYLOAD)
    assert job.generation_ready is False
    receipt = manager.storage.active(model.id)
    bundle = manager.storage.installed(model.id, receipt.job_id)
    assert (bundle / "checkpoints/tiny.txt").read_bytes() == PAYLOAD
    assert (bundle / "licenses/fixture-license.txt").read_text() == model.license_documents[0].text
    assert manager.status(model)["artifact_ready"]
    assert wait(manager, manager.start(model, "verify")).state == "ready"
    manager.close()
    recovered = InstallationJobManager(ModelStorageManager(manager.storage.root))
    try:
        assert recovered.get(job.id).state == "ready"
        assert recovered.status(model)["artifact_ready"]
        assert wait(recovered, recovered.start(model, "remove")).state == "not_installed"
        assert not bundle.exists()
        assert recovered.storage.active(model.id) is None
    finally:
        recovered.close()


@pytest.mark.parametrize("payload,code", [(None,"missing"),(b"short","size_mismatch"),
    (b"x" * len(PAYLOAD),"checksum_mismatch"),(PAYLOAD,"verified")])
def test_streaming_verifier(tmp_path, payload, code):
    path = tmp_path / "tiny"
    if payload is not None:
        path.write_bytes(payload)
    report = ArtifactVerifier().verify(path, fixture_manifest().components[0])
    assert report.code == code
    assert report.valid == (code == "verified")


def test_verifier_unknown_metadata_and_cancel(tmp_path):
    component = fixture_manifest().components[0].model_copy(update={"sha256": None})
    assert ArtifactVerifier().verify(tmp_path / "missing", component).code == "missing_integrity_metadata"
    path = tmp_path / "tiny"
    path.write_bytes(PAYLOAD)
    cancel = threading.Event(); cancel.set()
    with pytest.raises(Cancelled):
        ArtifactVerifier().verify(path, fixture_manifest().components[0], cancel)


@pytest.mark.parametrize("destination", ["../tiny", "C:/tiny", "/tiny", "vae/../tiny", "vae/CON.txt", "vae/a:b"])
def test_bad_component_paths(destination):
    data = fixture_manifest().model_dump()
    data["components"][0]["destination"] = destination
    with pytest.raises(ValidationError):
        type(fixture_manifest()).model_validate(data)


def test_symlink_escape_and_hardlinks(tmp_path):
    external = tmp_path / "external"; external.mkdir()
    link = tmp_path / "linked"
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("Windows symlink privilege unavailable; junction test covers reparse points")
    with pytest.raises(ManagerError):
        ModelStorageManager(link / "models")


def test_windows_junction_escape(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows-specific junction test")
    import subprocess
    external = tmp_path / "outside"; external.mkdir()
    junction = tmp_path / "junction"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(external)], capture_output=True)
    assert result.returncode == 0
    try:
        assert is_link(junction)
        with pytest.raises(ManagerError):
            ModelStorageManager(junction / "models")
    finally:
        # rmdir removes this exact verified junction, never its target contents.
        assert junction.parent == tmp_path and is_link(junction)
        os.rmdir(junction)
    assert external.exists()


def test_hardlinked_artifact_rejected(tmp_path):
    original = tmp_path / "original"; original.write_bytes(PAYLOAD)
    linked = tmp_path / "linked"; os.link(original, linked)
    assert ArtifactVerifier().verify(linked, fixture_manifest().components[0]).code == "unsafe_file"


def test_storage_unowned_external_and_lock(manager, tmp_path):
    root = tmp_path / "unowned"; (root / ".director").mkdir(parents=True)
    sentinel = root / ".director/user.txt"; sentinel.write_text("user")
    with pytest.raises(ManagerError, match="not owned"):
        ModelStorageManager(root).ensure_owned()
    assert sentinel.read_text() == "user"
    with pytest.raises(ManagerError):
        ModelStorageManager(tmp_path / "ComfyUI/models")
    manager.storage.ensure_owned()
    other = ModelStorageManager(manager.storage.root)
    with pytest.raises(ManagerError) as error:
        other.ensure_owned()
    assert error.value.code == "storage_busy"
    other.close()


def test_insufficient_and_unknown_disk_space(manager, monkeypatch):
    monkeypatch.setattr("director.installations.storage.shutil.disk_usage", lambda _: SimpleNamespace(free=0))
    with pytest.raises(ManagerError) as error:
        install(manager)
    assert error.value.code == "insufficient_disk_space"
    monkeypatch.setattr("director.installations.storage.shutil.disk_usage", lambda _: (_ for _ in ()).throw(OSError()))
    with pytest.raises(ManagerError) as error:
        manager.storage.check_space(0)
    assert error.value.code == "unknown_disk_space"


def test_disk_recheck_during_transfer(manager, monkeypatch):
    original = manager.fixture_downloader.fetch
    def transfer(*args):
        monkeypatch.setattr("director.installations.storage.shutil.disk_usage", lambda _: SimpleNamespace(free=0))
        return original(*args)
    manager.fixture_downloader.fetch = transfer
    result = wait(manager, install(manager))
    assert result.state == "failed" and result.error["code"] == "insufficient_disk_space"
    assert manager.storage.active("fixture-tiny") is None


def test_acknowledgement_and_stale_manifest(manager):
    model = fixture_manifest()
    with pytest.raises(ManagerError) as error:
        manager.start(model, "install", manifest_digest(model), "0" * 32)
    assert error.value.code == "acknowledgement_missing"
    with pytest.raises(ManagerError):
        manager.licenses.record(model, manager.licenses.requirements(model)["document_set_digest"], accepted=False)
    ack = acknowledge(manager, model)
    changed = model.model_copy(deep=True)
    changed.license_documents[0].version = "2"
    with pytest.raises(ManagerError) as error:
        manager.start(changed, "install", manifest_digest(changed), ack)
    assert error.value.code == "stale_acknowledgement"
    with pytest.raises(ManagerError) as error:
        manager.start(model, "install", "0" * 64, ack)
    assert error.value.code == "stale_manifest"


@pytest.mark.parametrize("field,value,code", [("sha256",None,"missing_integrity_metadata"),
    ("expected_size_bytes",None,"missing_integrity_metadata"),("pinned_revision",None,"missing_integrity_metadata")])
def test_missing_metadata(manager, field, value, code):
    model = fixture_manifest(); setattr(model.components[0], field, value)
    with pytest.raises(ManagerError) as error:
        manager.start(model,"install",manifest_digest(model),"0" * 32)
    assert error.value.code == code


def test_real_downloads_disabled_and_wan_unreviewed(manager, manifests):
    model = manifests["wan-2-1-t2v-1-3b"]
    with pytest.raises(ManagerError) as error:
        manager.start(model,"install",manifest_digest(model),"0" * 32)
    assert error.value.code == "real_downloads_disabled"
    manager.downloader = HuggingFaceDownloader(enabled=True)
    with pytest.raises(ManagerError) as error:
        manager.start(model,"install",manifest_digest(model),"0" * 32)
    assert error.value.code == "unreviewed_artifacts"


@pytest.mark.parametrize("mode", ["network", "corruption", "outside"])
def test_failed_transfer_never_ready(manager, tmp_path, mode):
    def fetch(component, cache, cancel, progress, allowlist):
        if mode == "network":
            raise ManagerError("network_failure", "Connection failed")
        path = (tmp_path if mode == "outside" else cache) / "bad"
        path.write_bytes(b"x" * len(PAYLOAD))
        return path
    manager.fixture_downloader.fetch = fetch
    job = wait(manager, install(manager))
    assert job.state == "failed"
    assert job.error["code"] == {"network":"network_failure","corruption":"artifact_integrity_failed","outside":"unsafe_cache"}[mode]
    assert not manager.status(fixture_manifest())["artifact_ready"]


def test_cancellation_and_concurrent_install(manager):
    entered = threading.Event()
    def blocked(component, cache, cancel, progress, allowlist):
        entered.set()
        assert cancel.wait(3)
        raise Cancelled()
    manager.fixture_downloader.fetch = blocked
    model = fixture_manifest(); job = install(manager, model)
    assert entered.wait(2)
    with pytest.raises(ManagerError) as error:
        manager.start(model,"install",manifest_digest(model), acknowledge(manager, model))
    assert error.value.code == "installation_busy"
    manager.cancel(job.id)
    assert wait(manager, job).state == "cancelled"
    assert manager.cancel(job.id).state == "cancelled"
    assert manager.storage.active(model.id) is None


def test_duplicate_install_and_safe_removal(manager):
    model = fixture_manifest(); job = wait(manager, install(manager))
    with pytest.raises(ManagerError) as error:
        install(manager)
    assert error.value.code == "already_installed"
    bundle = manager.storage.installed(model.id, job.id)
    extra = bundle / "user.txt"; extra.write_text("keep")
    removal = wait(manager, manager.start(model, "remove"))
    assert removal.state == "failed" and removal.error["code"] == "unowned_files"
    assert extra.read_text() == "keep" and manager.storage.active(model.id)


@pytest.mark.parametrize("change", ["missing", "corrupted"])
def test_installed_corruption(manager, change):
    model = fixture_manifest(); job = wait(manager, install(manager))
    path = manager.storage.installed(model.id, job.id) / "checkpoints/tiny.txt"
    if change == "missing":
        path.unlink()
    else:
        path.write_bytes(b"x" * len(PAYLOAD))
    assert manager.status(model)["state"] == "corrupted"
    assert wait(manager, manager.start(model,"verify")).state == "corrupted"
    assert wait(manager, manager.start(model,"remove")).state == "not_installed"


def test_recovery_interrupted_and_committed(manager):
    model = fixture_manifest(); finished = wait(manager, install(manager))
    committed = manager.get(finished.id); committed.state = "installing"; manager._save(committed)
    interrupted = Job(id=uuid4().hex, model_id="fixture-tiny", operation="verify", manifest=model,
                      manifest_digest=manifest_digest(model), state="verifying")
    manager._save(interrupted)
    manager.close()
    recovered = InstallationJobManager(ModelStorageManager(manager.storage.root))
    try:
        assert recovered.get(committed.id).state == "ready"
        assert recovered.get(interrupted.id).state == "failed"
        assert recovered.get(interrupted.id).error["code"] == "interrupted"
    finally:
        recovered.close()


def test_invalid_receipt_fails_closed(manager):
    model = fixture_manifest(); job = wait(manager, install(manager))
    path = manager.storage.installed(model.id, job.id) / "receipt.json"
    data = manager.storage.read_json(path); data["manifest_digest"] = "0" * 64
    manager.storage.write_json(path,data)
    with pytest.raises(ManagerError) as error:
        manager.status(model)
    assert error.value.code == "invalid_receipt"


@pytest.mark.parametrize("use_login", [True,False])
def test_official_sdk_arguments_are_pinned_and_no_token_value(tmp_path, monkeypatch, use_login):
    import sys
    calls = []
    monkeypatch.setitem(sys.modules,"huggingface_hub",SimpleNamespace(hf_hub_download=lambda **kwargs: calls.append(kwargs) or str(tmp_path / "fake")))
    component = fixture_manifest().components[0]
    messages = []
    _sdk_fetch(component,tmp_path,messages.append,use_login)
    assert calls[0]["revision"] == component.pinned_revision
    assert calls[0]["filename"] == component.filename
    assert calls[0]["token"] is use_login
    assert calls[0]["endpoint"] == "https://huggingface.co"
    assert "tqdm_class" not in calls[0]
    assert messages[-1]["bytes"] == len(PAYLOAD)


def test_downloader_allowlist_disabled_and_precancel(tmp_path):
    component = fixture_manifest().components[0]; cancel = threading.Event()
    with pytest.raises(ManagerError) as error:
        HuggingFaceDownloader().fetch(component,tmp_path,cancel,lambda _: None,set())
    assert error.value.code == "real_downloads_disabled"
    downloader = HuggingFaceDownloader(enabled=True)
    with pytest.raises(ManagerError) as error:
        downloader.fetch(component,tmp_path,cancel,lambda _: None,set())
    assert error.value.code == "invalid_artifact"
    cancel.set()
    with pytest.raises(Cancelled):
        downloader.fetch(component,tmp_path,cancel,lambda _: None,set(fixture_payloads()))


def test_license_document_hash_validation():
    data = fixture_manifest().model_dump(); data["license_documents"][0]["text"] += "changed"
    with pytest.raises(ValidationError):
        type(fixture_manifest()).model_validate(data)


@pytest.mark.parametrize("part", ["..", "../outside", "C:/outside", "CON", "a/b", "a\\b"])
def test_storage_path_validation(manager, part):
    with pytest.raises(ManagerError) as error:
        manager.storage.path(part)
    assert error.value.code == "unsafe_path"


def test_staging_link_escape(manager, tmp_path):
    if os.name != "nt":
        pytest.skip("Windows junction test")
    import subprocess
    manager.storage.ensure_owned()
    outside = tmp_path / "outside"; outside.mkdir()
    sentinel = outside / "user.txt"; sentinel.write_text("keep")
    junction = manager.storage.base / "staging"
    assert subprocess.run(["cmd","/c","mklink","/J",str(junction),str(outside)],capture_output=True).returncode == 0
    try:
        job = wait(manager,install(manager))
        assert job.state == "failed" and job.error["code"] == "unsafe_path"
        assert sentinel.read_text() == "keep"
    finally:
        assert is_link(junction) and junction.parent == manager.storage.base
        os.rmdir(junction)


def test_legacy_mock_and_disabled_fixture(manager, manifests):
    legacy = next(model for model in manifests.values() if model.is_mock)
    with pytest.raises(ManagerError) as error:
        manager.start(legacy,"install",manifest_digest(legacy),"0" * 32)
    assert error.value.code == "not_installable"
    manager.fixture_downloader = None
    with pytest.raises(ManagerError) as error:
        install(manager)
    assert error.value.code == "fixtures_disabled"


@pytest.mark.parametrize("event", ["cancel", "timeout", "network", "complete", "outside"])
def test_sdk_worker_supervisor_offline(tmp_path,monkeypatch,event):
    import queue
    component = fixture_manifest().components[0]
    cancel = threading.Event(); progress = []
    candidate = tmp_path / "candidate"; candidate.write_bytes(PAYLOAD)
    class Process:
        alive = True
        stopped = False
        def start(self):
            if event == "cancel":
                cancel.set()
        def is_alive(self): return self.alive
        def join(self,timeout=None): pass
        def terminate(self): self.alive=False; self.stopped=True
        def kill(self): self.terminate()
    process = Process()
    class Messages:
        closed = False
        def get(self,timeout):
            if event == "network": return {"kind":"error","code":"network_failure"}
            if event == "outside": return {"kind":"complete","path":str(tmp_path.parent / "outside")}
            if event == "complete": return {"kind":"complete","path":str(candidate)}
            raise queue.Empty()
        def close(self): self.closed=True
    messages = Messages()
    monkeypatch.setattr("director.installations.downloader.multiprocessing.get_context",
        lambda _: SimpleNamespace(Queue=lambda **_:messages,Process=lambda **_:process))
    downloader = HuggingFaceDownloader(enabled=True,timeout_seconds=0 if event == "timeout" else 3)
    if event == "complete":
        assert downloader.fetch(component,tmp_path,cancel,progress.append,set(fixture_payloads())) == candidate
    elif event == "cancel":
        with pytest.raises(Cancelled):
            downloader.fetch(component,tmp_path,cancel,progress.append,set(fixture_payloads()))
    else:
        with pytest.raises(ManagerError) as error:
            downloader.fetch(component,tmp_path,cancel,progress.append,set(fixture_payloads()))
        assert error.value.code == {"timeout":"transfer_timeout","network":"network_failure","outside":"unsafe_cache"}[event]
    assert process.stopped and messages.closed


def test_network_error_details_redacted(manager):
    def fetch(*args):
        raise RuntimeError("private-token-secret and signed URL")
    manager.fixture_downloader.fetch = fetch
    result = wait(manager,install(manager))
    assert result.state == "failed"
    assert "private-token-secret" not in result.model_dump_json()
    assert "private-token-secret" not in manager.storage.path("jobs",result.id + ".json").read_text()


def test_activation_failure_never_ready(manager,monkeypatch):
    monkeypatch.setattr(manager.storage,"activate",lambda _: (_ for _ in ()).throw(OSError("locked")))
    result = wait(manager,install(manager))
    assert result.state == "failed" and manager.storage.active("fixture-tiny") is None


def test_missing_and_unsafe_files_block_ready_but_user_root_retained(manager):
    user = manager.storage.root / "user.txt"
    user.parent.mkdir(parents=True); user.write_text("keep")
    job = wait(manager,install(manager))
    assert wait(manager,manager.start(fixture_manifest(),"remove")).state == "not_installed"
    assert user.read_text() == "keep"
    assert manager.storage.path("acknowledgements").exists()


def test_fixture_hardlink_cache_not_overwritten(manager,tmp_path):
    manager.storage.ensure_owned()
    cache = manager.storage.path("hf-cache"); cache.mkdir()
    original = tmp_path / "user.txt"; original.write_bytes(PAYLOAD)
    target = cache / (fixture_manifest().components[0].sha256 + ".fixture")
    os.link(original,target)
    result = wait(manager,install(manager))
    assert result.state == "failed" and original.read_bytes() == PAYLOAD


def test_sdk_cache_hardlink_rejected_without_network(tmp_path):
    from director.installations.downloader import validate_private_cache
    outside = tmp_path / "user"; outside.write_bytes(PAYLOAD)
    cache = tmp_path / "cache"; cache.mkdir()
    os.link(outside,cache / "blob")
    with pytest.raises(ManagerError) as error:
        validate_private_cache(cache)
    assert error.value.code == "unsafe_cache"


def test_sdk_observed_partial_progress_and_cache_reuse(tmp_path,monkeypatch):
    import sys
    seen = []
    def download(**kwargs):
        cache = kwargs["cache_dir"]; seen.append(cache)
        cache.mkdir(exist_ok=True)
        (cache / "tiny.incomplete").write_bytes(b"x" * 10)
        time.sleep(.35)
        return str(cache / "candidate")
    monkeypatch.setitem(sys.modules,"huggingface_hub",SimpleNamespace(hf_hub_download=download))
    messages=[]; component=fixture_manifest().components[0]
    _sdk_fetch(component,tmp_path,messages.append,False)
    _sdk_fetch(component,tmp_path,messages.append,False)
    assert seen[0] == seen[1] == tmp_path / component.sha256
    assert any(message["bytes"] == 10 for message in messages)
    # Reusing the same pinned cache is verified here, not real HTTP resume.


def test_fixture_rejected_without_explicit_acceptance_cli(tmp_path,capsys):
    import sys
    from director.installations.demo import main
    from unittest.mock import patch
    root = tmp_path / "demo"
    with patch.object(sys,"argv",["demo","--root",str(root)]):
        assert main() == 2
    assert not root.exists()
    assert "pass --acknowledge-fixture-license" in capsys.readouterr().out


def test_authorized_worker_clears_inherited_offline_mode(tmp_path, monkeypatch):
    import sys
    from director.installations import downloader
    constants = SimpleNamespace(HF_HUB_OFFLINE=True)
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(constants=constants))
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setattr(downloader.logging, "disable", lambda _: None)
    def fetch(*args):
        assert "HF_HUB_OFFLINE" not in os.environ
        assert constants.HF_HUB_OFFLINE is False
        return str(tmp_path / "candidate")
    monkeypatch.setattr(downloader, "_sdk_fetch", fetch)
    # Restore all process environment changes made by this in-process worker test.
    from unittest.mock import patch
    messages = []
    with patch.dict(os.environ):
        downloader._worker(fixture_manifest().components[0].model_dump(), str(tmp_path),
                           SimpleNamespace(put=messages.append), False)
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert messages[-1]["kind"] == "complete"


def test_transfer_exception_preserves_cause_without_credentials(monkeypatch):
    from director.installations.downloader import transfer_details
    monkeypatch.setenv("HF_TOKEN", "private-token-value")
    cause = RuntimeError("HF_HUB_OFFLINE=1 blocks network access")
    error = ValueError("private-token-value https://example.com/file?signature=secret hf_abc123 Bearer credential")
    error.__cause__ = cause
    details = transfer_details(error)
    assert "HF_HUB_OFFLINE=1" in details and "ValueError" in details
    for secret in ("private-token-value", "signature=secret", "hf_abc123", "credential"):
        assert secret not in details
