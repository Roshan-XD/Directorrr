import pytest
from pydantic import ValidationError

from director.models.schemas import ModelManifest


def test_legacy_json_remains_valid():
    model = ModelManifest.model_validate({
        "id": "legacy", "name": "MOCK legacy", "description": "Old manifest",
        "is_mock": True, "tasks": ["text-to-video"], "runtime": "comfyui", "license": "MOCK",
        "requirements": {"min_ram_gb": 8, "min_free_storage_gb": 10, "gpu_required": False},
    })
    assert model.schema_version == 1
    assert model.components == []
    assert model.execution_profile is None


def test_real_manifest_records_unknowns_honestly(manifests):
    model = manifests["wan-2-1-t2v-1-3b"]
    assert model.schema_version == 2 and not model.is_mock
    assert model.support_status == "researched"
    assert model.pinned_revision == "37ec512624d61f7aa208f7ea8140a131f93afc9a"
    assert model.requirements.min_vram_gb is None
    assert model.requirements.min_ram_gb is None
    assert len(model.components) == 3
    assert all(component.estimated_size_bytes is None for component in model.components)
    assert sum(component.expected_size_bytes for component in model.components) == 9_828_025_775
    assert model.execution_profile.custom_nodes == []
    assert model.tasks == ["text-to-video"]


@pytest.mark.parametrize("component_id,size,digest", [
    ("diffusion", 2_838_303_560, "be531024cd9018cb5b48c40cfbb6a6191645b1c792eb8bf4f8c1c6e10f924dc5"),
    ("text-encoder", 6_735_906_897, "c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68"),
    ("vae", 253_815_318, "2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b"),
])
def test_wan_pinned_artifact_metadata(manifests, component_id, size, digest):
    model = manifests["wan-2-1-t2v-1-3b"]
    component = next(item for item in model.components if item.id == component_id)
    assert component.repository_id == "Comfy-Org/Wan_2.1_ComfyUI_repackaged"
    assert component.pinned_revision == "123acf1cc74bccbb9bfff8ac1ee72edc08c2341d"
    assert component.expected_size_bytes == size and component.sha256 == digest
    assert component.license_info.identifier == "Apache-2.0"
    assert component.evidence[0].quality == "verified_metadata"
    assert component.filename == "split_files/" + component.destination


def test_artifact_verification_does_not_certify_runtime(manifests):
    model = manifests["wan-2-1-t2v-1-3b"]
    assert model.execution_profile.workflow.pinned_revision == "cb13911e7d83e4f61ca12e29629cab85a6c08856"
    assert model.execution_profile.runtime_version_constraint is None
    assert model.execution_profile.runtime_pinned_revision is None
    assert model.requirements_quality == "unverified"
    assert model.support_status == "researched" and model.unresolved_assumptions


@pytest.mark.parametrize("path", [
    "../bad", "/vae/model", "C:/vae/model", "vae/../model", "vae//model", "vae\\model",
    "vae/file:stream", "vae/%2e%2e/file", "vae/CON.safetensors", "vae/model.", "vae/model ",
    "other/model", "vae", "//server/share/model", "vae/LPT9.safetensors", "vae/a?b",
])
def test_unsafe_destination_rejected(manifests, path):
    data = manifests["wan-2-1-t2v-1-3b"].model_dump()
    data["components"][0]["destination"] = path
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(data)


@pytest.mark.parametrize("repo", ["owner", "https://huggingface.co/o/m", "../model", "owner/../model", "o/m?ref=x", "o/m--bad", "o/m."])
def test_repository_ids_are_not_urls_or_paths(manifests, repo):
    data = manifests["wan-2-1-t2v-1-3b"].model_dump()
    data["components"][0]["repository_id"] = repo
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(data)


@pytest.mark.parametrize("field,value", [
    ("filename", "../model.safetensors"), ("filename", "vae\\model"),
    ("pinned_revision", "main"), ("pinned_revision", "abc1234"),
    ("sha256", "not-a-checksum"), ("expected_size_bytes", 0), ("expected_size_bytes", -1),
    ("expected_size_bytes", True), ("expected_size_bytes", 10.5), ("unexpected", 1),
])
def test_component_metadata_validation(manifests, field, value):
    data = manifests["wan-2-1-t2v-1-3b"].model_dump()
    data["components"][0][field] = value
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(data)


@pytest.mark.parametrize("destinations", [
    ["vae/a", "vae/A", "vae/b"],
    ["vae/a", "vae/a.b", "vae/a/child"],
])
def test_duplicate_and_file_directory_conflicts(manifests, destinations):
    data = manifests["wan-2-1-t2v-1-3b"].model_dump()
    for item, destination in zip(data["components"], destinations):
        item["destination"] = destination
    with pytest.raises(ValidationError, match="conflicting"):
        ModelManifest.model_validate(data)


def test_invalid_version_constraints_and_evidence(manifests):
    data = manifests["wan-2-1-t2v-1-3b"].model_dump()
    data["execution_profile"]["runtime_version_constraint"] = "latest please"
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(data)
    data["execution_profile"]["runtime_version_constraint"] = ">=0.3,<1"
    data["support_status"] = "validated"
    with pytest.raises(ValidationError, match="local measurement"):
        ModelManifest.model_validate(data)


def test_nonfinite_hardware_requirements_rejected(manifests):
    data = manifests["wan-2-1-t2v-1-3b"].model_dump()
    data["requirements"]["min_ram_gb"] = float("inf")
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(data)
