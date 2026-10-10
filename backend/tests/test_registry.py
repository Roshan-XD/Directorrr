import json

import pytest
from pydantic import ValidationError

from director.models.registry import ModelRegistry, RegistryError
from director.models.schemas import ModelManifest


def test_shipped_models_are_clearly_mock(manifests):
    mocks = {key: model for key, model in manifests.items() if model.is_mock}
    assert set(mocks) == {"mock-cpu-video", "mock-gpu-video"}
    for model in mocks.values():
        assert model.is_mock
        assert "MOCK" in model.name
        assert model.huggingface_repo_id is None


def test_empty_registry(tmp_path):
    assert ModelRegistry(tmp_path).load() == []


def test_missing_directory(tmp_path):
    with pytest.raises(RegistryError, match="does not exist"):
        ModelRegistry(tmp_path / "missing").load()


@pytest.mark.parametrize("contents", ["{bad json", '{"id": "incomplete"}'])
def test_bad_manifest_reports_filename(tmp_path, contents):
    (tmp_path / "broken.json").write_text(contents, encoding="utf-8")
    with pytest.raises(RegistryError, match="broken.json"):
        ModelRegistry(tmp_path).load()


def test_duplicate_ids(tmp_path, manifests):
    model = manifests["mock-cpu-video"]
    for filename in ("a.json", "b.json"):
        (tmp_path / filename).write_text(model.model_dump_json(), encoding="utf-8")
    with pytest.raises(RegistryError, match="Duplicate model id"):
        ModelRegistry(tmp_path).load()


@pytest.mark.parametrize("mutation", [
    {"is_mock": True, "name": "Unlabeled example"},
    {"huggingface_repo_id": "fake/model"},
    {"unexpected_field": 1},
    {"schema_version": 2},
    {"tasks": []},
    {"requirements": {"min_ram_gb": -1, "min_free_storage_gb": 0, "gpu_required": False}},
    {"requirements": {"min_ram_gb": 8, "min_free_storage_gb": 0, "gpu_required": True}},
    {"requirements": {"min_ram_gb": 8, "min_free_storage_gb": 0, "gpu_required": False, "min_vram_gb": 1}},
])
def test_manifest_rejects_invalid_metadata(manifests, mutation):
    data = json.loads(manifests["mock-cpu-video"].model_dump_json())
    data.update(mutation)
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(data)
