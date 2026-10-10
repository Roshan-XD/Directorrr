import pytest

from director.models.compatibility import evaluate_compatibility
from director.models.schemas import RuntimeState
from director.system.schemas import GPUInfo


def test_unverified_wan_is_only_potential(manifests, hardware):
    result = evaluate_compatibility(manifests["wan-2-1-t2v-1-3b"], hardware)
    assert result.status == "unknown"
    assert result.assessment == "potentially_compatible"
    assert any(check.resource == "runtime" and check.status == "unknown" for check in result.profile_checks)
    hardware.gpus = []
    hardware.gpu_detection_complete = False
    assert evaluate_compatibility(manifests["wan-2-1-t2v-1-3b"], hardware).assessment == "unknown"


def test_verified_requires_full_observations(complete_model, hardware, ready_runtime):
    hardware.gpus[0].architecture = "test-architecture"
    result = evaluate_compatibility(complete_model, hardware, ready_runtime)
    assert result.assessment == "verified_compatible"
    hardware.gpus[0].architecture = None
    assert evaluate_compatibility(complete_model, hardware, ready_runtime).assessment == "potentially_compatible"


@pytest.mark.parametrize("change", ["ram", "vram", "storage", "architecture", "vendor", "platform", "runtime", "dependency", "revision"])
def test_known_failed_requirement_is_unsupported(complete_model, hardware, ready_runtime, change):
    hardware.gpus[0].architecture = "test-architecture"
    if change == "ram":
        hardware.ram.total_gb = 4
    elif change == "vram":
        hardware.gpus[0].vram_gb = 4
    elif change == "storage":
        complete_model.requirements.min_free_storage_gb = 200
    elif change == "architecture":
        hardware.gpus[0].architecture = "other"
    elif change == "vendor":
        hardware.gpus[0].vendor = "amd"
    elif change == "platform":
        hardware.platform = "Darwin"
    elif change == "runtime":
        ready_runtime.status = "missing"
    elif change == "dependency":
        ready_runtime.dependency_versions["torch"] = "1.0"
    elif change == "revision":
        ready_runtime.pinned_revision = "d" * 40
    assert evaluate_compatibility(complete_model, hardware, ready_runtime).assessment == "unsupported"


def test_unverified_capacity_cannot_certify_or_reject(complete_model, hardware, ready_runtime):
    hardware.gpus[0].architecture = "test-architecture"
    hardware.gpus[0].vram_gb = 1
    complete_model.requirements_quality = "estimate"
    result = evaluate_compatibility(complete_model, hardware, ready_runtime)
    assert result.status == "incompatible"  # Legacy declared-capacity result is preserved.
    assert result.assessment == "potentially_compatible"


def test_architecture_and_vram_must_belong_to_same_gpu(complete_model, hardware, ready_runtime):
    hardware.gpus = [
        GPUInfo(name="Architecture only", vendor="nvidia", architecture="test-architecture", vram_gb=4, source="nvidia_smi"),
        GPUInfo(name="Memory only", vendor="nvidia", architecture="other", vram_gb=24, source="nvidia_smi"),
    ]
    result = evaluate_compatibility(complete_model, hardware, ready_runtime)
    assert result.status == "compatible"  # Legacy status checks capacity only.
    assert result.assessment == "unsupported"


def test_custom_node_and_version_unknowns(complete_model, hardware, ready_runtime):
    from director.models.schemas import CustomNode
    hardware.gpus[0].architecture = "test-architecture"
    complete_model.execution_profile.custom_nodes = [CustomNode(name="test", source="https://example.com/node", pinned_revision="a" * 40)]
    result = evaluate_compatibility(complete_model, hardware, ready_runtime)
    assert result.assessment == "potentially_compatible"
    ready_runtime.custom_node_revisions["test"] = "b" * 40
    assert evaluate_compatibility(complete_model, hardware, ready_runtime).assessment == "unsupported"
    assert evaluate_compatibility(complete_model, hardware, RuntimeState()).assessment != "verified_compatible"
