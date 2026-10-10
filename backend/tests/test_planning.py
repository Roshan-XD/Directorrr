from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from director.main import create_app, get_hardware
from director.models.planning import PlanStorage, build_installation_plan, inspect_storage


def snapshot(root, free=10**11):
    return PlanStorage(root=str(root), measured_path=str(root.parent), free_bytes=free, total_bytes=10**12)


def test_unknown_metadata_blocks_wan_plan(manifests, hardware, tmp_path):
    root = tmp_path / "not-created"
    before = list(tmp_path.rglob("*"))
    plan = build_installation_plan(manifests["wan-2-1-t2v-1-3b"], hardware, root)
    assert plan.read_only and not plan.ready_for_installation and plan.status == "blocked"
    assert plan.total_expected_download_bytes == 9_828_025_775
    assert plan.known_download_bytes == 9_828_025_775
    assert plan.total_estimated_download_bytes == 9_828_025_775
    assert plan.required_storage_bytes is None
    assert "components.diffusion.expected_size_bytes" not in plan.missing_metadata
    assert "pinned_revision" not in plan.missing_metadata
    assert "requirements.min_ram_gb" in plan.missing_metadata
    assert "missing_metadata" in {item.code for item in plan.blockers}
    assert len(plan.components) == 3
    assert Path(plan.components[0].destination_path).is_relative_to(root)
    assert plan.runtime_observation.status == "unknown"
    assert list(tmp_path.rglob("*")) == before
    assert not root.exists()


@pytest.mark.parametrize("free,blocked", [(700, False), (699, True), (0, True)])
def test_exact_storage_budget(complete_model, hardware, ready_runtime, tmp_path, free, blocked):
    hardware.gpus[0].architecture = "test-architecture"
    plan = build_installation_plan(complete_model, hardware, tmp_path, ready_runtime, snapshot(tmp_path, free))
    assert plan.known_download_bytes == plan.total_expected_download_bytes == 600
    assert plan.total_estimated_download_bytes == 600
    assert plan.required_storage_bytes == 700
    assert ("insufficient_disk_space" in {item.code for item in plan.blockers}) == blocked
    assert plan.status == ("blocked" if blocked else "reviewable")
    assert not plan.ready_for_installation


def test_partial_size_total_is_not_a_complete_total(complete_model, hardware, tmp_path):
    complete_model.components[1].expected_size_bytes = None
    plan = build_installation_plan(complete_model, hardware, tmp_path, storage=snapshot(tmp_path, 399))
    assert plan.known_download_bytes == 400
    assert plan.total_expected_download_bytes is None
    assert plan.total_estimated_download_bytes is None
    assert "insufficient_disk_space" in {item.code for item in plan.blockers}


def test_estimated_budget_can_warn_about_insufficient_space(manifests, hardware, tmp_path):
    model = manifests["wan-2-1-t2v-1-3b"]
    # Keep the estimate-only regression independent of newly verified production metadata.
    for component in model.components:
        component.estimated_size_bytes = component.expected_size_bytes
        component.expected_size_bytes = None
    plan = build_installation_plan(model, hardware, tmp_path, storage=snapshot(tmp_path, 100))
    assert plan.total_expected_download_bytes is None
    assert "insufficient_disk_space" in {item.code for item in plan.blockers}


def test_disk_failure_is_unknown(monkeypatch, tmp_path):
    def failed(_):
        raise OSError("offline drive")
    monkeypatch.setattr("director.models.planning.shutil.disk_usage", failed)
    result = inspect_storage(tmp_path / "new" / "models")
    assert result.free_bytes is None and result.measured_path is None
    assert not (tmp_path / "new").exists()


def test_existing_ancestor_measured_without_creating_folders(monkeypatch, tmp_path):
    observed = []
    def disk_usage(path):
        observed.append(path)
        return type("Usage", (), {"free": 123, "total": 456})()
    monkeypatch.setattr("director.models.planning.shutil.disk_usage", disk_usage)
    root = tmp_path / "new" / "models"
    result = inspect_storage(root)
    assert observed == [tmp_path]
    assert result.free_bytes == 123 and result.measured_path == str(tmp_path)
    assert not root.exists()


def test_unknown_space_blocks_plan(complete_model, hardware, tmp_path):
    plan = build_installation_plan(complete_model, hardware, tmp_path, storage=PlanStorage(root=str(tmp_path)))
    assert "unknown_disk_space" in {item.code for item in plan.blockers}


def test_mock_has_no_installation(manifests, hardware, tmp_path):
    plan = build_installation_plan(manifests["mock-cpu-video"], hardware, tmp_path)
    assert not plan.components and plan.total_expected_download_bytes is None
    assert "no_installable_components" in {item.code for item in plan.blockers}


def test_existing_file_and_parent_file_are_blocked(complete_model, hardware, tmp_path):
    (tmp_path / "diffusion_models").mkdir()
    destination = tmp_path / complete_model.components[0].destination
    destination.write_text("do not overwrite", encoding="utf-8")
    (tmp_path / "vae").write_text("not a directory", encoding="utf-8")
    plan = build_installation_plan(complete_model, hardware, tmp_path)
    assert {"destination_exists", "unsafe_destination"} <= {item.code for item in plan.blockers}
    assert destination.read_text(encoding="utf-8") == "do not overwrite"


def test_link_escape_is_blocked(monkeypatch, complete_model, hardware, tmp_path):
    original = Path.resolve
    outside = tmp_path.parent / "outside" / "weights"
    def linked_resolve(path, *args, **kwargs):
        if "diffusion_models" in path.parts:
            return outside
        return original(path, *args, **kwargs)
    # Simulate a Windows junction without requiring privileges to create links.
    monkeypatch.setattr(Path, "resolve", linked_resolve)
    plan = build_installation_plan(complete_model, hardware, tmp_path, storage=snapshot(tmp_path))
    assert plan.components[0].destination_path is None
    assert "unsafe_destination" in {item.code for item in plan.blockers}


@pytest.mark.parametrize("child", [False, True])
def test_resolved_link_conflicts_are_blocked(monkeypatch, complete_model, hardware, tmp_path, child):
    original = Path.resolve
    shared = tmp_path / "vae" / "shared"
    def linked_resolve(path, *args, **kwargs):
        if "diffusion_models" in path.parts:
            return shared
        if "text_encoders" in path.parts:
            return shared / "child" if child else shared
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", linked_resolve)
    plan = build_installation_plan(complete_model, hardware, tmp_path, storage=snapshot(tmp_path))
    assert "conflicting_destination" in {item.code for item in plan.blockers}


def test_hardware_storage_is_replaced_by_destination_drive(complete_model, hardware, ready_runtime, tmp_path):
    hardware.gpus[0].architecture = "test-architecture"
    complete_model.requirements.min_free_storage_gb = 1
    assert hardware.storage.free_gb == 100
    plan = build_installation_plan(complete_model, hardware, tmp_path, ready_runtime, snapshot(tmp_path, 700))
    assert plan.compatibility.assessment == "unsupported"
    assert "unsupported_profile" in {item.code for item in plan.blockers}


def test_invalid_mutated_manifest_is_revalidated(complete_model, hardware, tmp_path):
    from pydantic import ValidationError
    complete_model.components[0].destination = "../escape"
    with pytest.raises(ValidationError):
        build_installation_plan(complete_model, hardware, tmp_path)


def test_plan_endpoint_and_model_root_environment(monkeypatch, tmp_path, hardware):
    root = tmp_path / "weights"
    monkeypatch.setenv("DIRECTOR_MODEL_ROOT", str(root))
    application = create_app()
    application.dependency_overrides[get_hardware] = lambda: hardware
    with TestClient(application) as client:
        response = client.get("/api/models/wan-2-1-t2v-1-3b/installation-plan")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked" and data["ready_for_installation"] is False
        assert data["total_expected_download_bytes"] == 9_828_025_775
        assert data["total_estimated_download_bytes"] == 9_828_025_775
        assert data["runtime_requirements"]["workflow"]["format"] == "ui"
        assert len(data["components"]) == 3 and data["blockers"]
        assert Path(data["storage"]["root"]) == root
        assert client.get("/api/models/mock-cpu-video/installation-plan").json()["status"] == "blocked"
    assert not root.exists()


@pytest.mark.parametrize("model_id", ["missing", "INVALID_ID", "..", "C%3Aevil", "%2E%2E%5Csecret"])
def test_invalid_id_returns_404_before_hardware_probe(model_id):
    application = create_app()
    def unexpected_probe():
        raise AssertionError("Unknown IDs should not probe hardware")
    application.dependency_overrides[get_hardware] = unexpected_probe
    with TestClient(application) as client:
        response = client.get(f"/api/models/{model_id}/installation-plan")
        assert response.status_code == 404
        # HTTP clients normalize literal '..' before routing; both forms are a safe 404.
        assert response.json()["detail"] in {"Model not found", "Not Found"}
