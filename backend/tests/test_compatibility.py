import pytest

from director.models.compatibility import evaluate_compatibility
from director.system.schemas import GPUInfo


def test_cpu_model_needs_no_gpu(hardware, manifests):
    hardware.gpus = []
    hardware.gpu_detection_complete = False
    assert evaluate_compatibility(manifests["mock-cpu-video"], hardware).status == "compatible"


@pytest.mark.parametrize("vendor", ["nvidia", "amd", "intel"])
def test_mock_gpu_accepts_each_declared_vendor(hardware, manifests, vendor):
    hardware.gpus[0].vendor = vendor
    assert evaluate_compatibility(manifests["mock-gpu-video"], hardware).status == "compatible"


@pytest.mark.parametrize("resource", ["ram", "storage", "gpu"])
def test_insufficient_capacity(hardware, manifests, resource):
    if resource == "ram":
        hardware.ram.total_gb = 4
    elif resource == "storage":
        hardware.storage.free_gb = 1
    else:
        hardware.gpus[0].vram_gb = 2
    result = evaluate_compatibility(manifests["mock-gpu-video"], hardware)
    assert result.status == "incompatible"
    assert next(check for check in result.checks if check.resource == resource).status == "incompatible"


@pytest.mark.parametrize("resource", ["ram", "storage", "gpu", "estimated_vram"])
def test_unknown_capacity_is_not_compatible(hardware, manifests, resource):
    if resource == "ram":
        hardware.ram.total_gb = None
    elif resource == "storage":
        hardware.storage.free_gb = None
    elif resource == "gpu":
        hardware.gpus[0].vram_gb = None
    else:
        hardware.gpus[0].vram_is_estimate = True
    assert evaluate_compatibility(manifests["mock-gpu-video"], hardware).status == "unknown"


@pytest.mark.parametrize("complete, expected", [(True, "incompatible"), (False, "unknown")])
def test_absent_gpu_differs_from_failed_detection(hardware, manifests, complete, expected):
    hardware.gpus = []
    hardware.gpu_detection_complete = complete
    assert evaluate_compatibility(manifests["mock-gpu-video"], hardware).status == expected


def test_unknown_vendor_is_uncertain(hardware, manifests):
    hardware.gpus[0].vendor = "unknown"
    assert evaluate_compatibility(manifests["mock-gpu-video"], hardware).status == "unknown"


def test_vram_is_not_added_across_gpus(hardware, manifests):
    hardware.gpus = [GPUInfo(name=f"GPU {i}", vendor="nvidia", vram_gb=4, source="nvidia_smi") for i in range(2)]
    assert evaluate_compatibility(manifests["mock-gpu-video"], hardware).status == "incompatible"
    hardware.gpus.append(GPUInfo(name="Large GPU", vendor="nvidia", vram_gb=8, source="nvidia_smi"))
    assert evaluate_compatibility(manifests["mock-gpu-video"], hardware).status == "compatible"


def test_exact_thresholds_and_mock_notice(hardware, manifests):
    hardware.ram.total_gb = 16
    hardware.storage.free_gb = 30
    hardware.gpus[0].vram_gb = 8
    result = evaluate_compatibility(manifests["mock-gpu-video"], hardware)
    assert result.status == "compatible"
    assert any("MOCK" in note for note in result.notes)


def test_known_failure_wins_over_unknown(hardware, manifests):
    hardware.ram.total_gb = 1
    hardware.gpus[0].vram_gb = None
    assert evaluate_compatibility(manifests["mock-gpu-video"], hardware).status == "incompatible"
