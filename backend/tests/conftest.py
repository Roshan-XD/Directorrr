from pathlib import Path

import pytest

from director.models.registry import ModelRegistry
from director.models.schemas import ModelManifest, RuntimeState
from director.system.schemas import CPUInfo, GPUInfo, HardwareProfile, RAMInfo, StorageInfo

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(autouse=True)
def isolated_creative_storage(tmp_path, monkeypatch):
    # Even default create_app tests must not lock or change a user's Library/cache.
    monkeypatch.setenv("DIRECTOR_STUDIO_ROOT",str(tmp_path/"studio_data"))
    monkeypatch.delenv("DIRECTOR_ENABLE_REPOSITORY_DOWNLOADS",raising=False)


@pytest.fixture
def manifests():
    return {model.id: model for model in ModelRegistry(ROOT / "model_registry").load()}


@pytest.fixture
def hardware():
    return HardwareProfile(
        platform="Windows", cpu=CPUInfo(name="Test CPU", physical_cores=8, logical_cores=16),
        ram=RAMInfo(total_gb=32, available_gb=20),
        gpus=[GPUInfo(name="Test GPU", vendor="nvidia", vram_gb=12, source="nvidia_smi")],
        gpu_detection_complete=True,
        storage=StorageInfo(path="D:/test", total_gb=500, free_gb=100),
    )


@pytest.fixture
def complete_model(manifests):
    """Synthetic metadata for tests, not evidence about real Wan execution."""
    data = manifests["wan-2-1-t2v-1-3b"].model_dump()
    data.update(id="test-profile", name="Synthetic test profile", pinned_revision="a" * 40,
                support_status="validated", requirements_quality="locally_measured",
                unresolved_assumptions=[], installation_overhead_bytes=100)
    data["evidence"].append({"subject": "test fixture", "quality": "locally_measured",
                             "detail": "Synthetic test data only"})
    data["requirements"].update(min_ram_gb=16, min_vram_gb=8, min_free_storage_gb=0,
                                gpu_architectures=["test-architecture"])
    profile = data["execution_profile"]
    profile.update(runtime_version_constraint=">=0.3,<1", runtime_pinned_revision="b" * 40)
    profile["workflow"]["pinned_revision"] = "c" * 40
    for dependency in profile["dependencies"]:
        dependency["version_constraint"] = ">=2,<3"
    for index, component in enumerate(data["components"]):
        component.update(pinned_revision="a" * 40, expected_size_bytes=(index + 1) * 100,
                         estimated_size_bytes=None, license_info=data["license_info"])
    return ModelManifest.model_validate(data)


@pytest.fixture
def ready_runtime():
    return RuntimeState(status="available", version="0.4", pinned_revision="b" * 40,
                        dependency_versions={"torch": "2.5", "nvidia-driver": "2.1"})
