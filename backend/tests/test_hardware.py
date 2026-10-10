import json
import subprocess
from types import SimpleNamespace

import pytest

from director.system import hardware as detector


@pytest.fixture(autouse=True)
def system_probes(monkeypatch):
    # Unit tests never inspect the developer's actual GPU or launch PowerShell.
    monkeypatch.setattr(detector.platform, "system", lambda: "Windows")
    monkeypatch.setattr(detector.platform, "processor", lambda: "Fallback CPU")
    monkeypatch.setattr(detector.psutil, "cpu_count", lambda logical: 16 if logical else 8)
    monkeypatch.setattr(detector.psutil, "virtual_memory", lambda: SimpleNamespace(total=32 * detector.GIB, available=20 * detector.GIB))
    monkeypatch.setattr(detector.shutil, "disk_usage", lambda path: SimpleNamespace(total=500 * detector.GIB, free=100 * detector.GIB))
    monkeypatch.setattr(detector.shutil, "which", lambda name: None)
    monkeypatch.setattr(detector, "_run_command", lambda args: json.dumps({"cpu_names": ["CIM CPU"], "gpus": []}))


def test_windows_cpu_ram_storage(tmp_path):
    profile = detector.detect_hardware(tmp_path)
    assert profile.cpu.name == "CIM CPU"
    assert profile.cpu.physical_cores == 8
    assert profile.cpu.logical_cores == 16
    assert profile.ram.total_gb == 32
    assert profile.ram.available_gb == 20
    assert profile.storage.free_gb == 100
    assert profile.storage.path == str(tmp_path.resolve())
    assert profile.gpu_detection_complete


@pytest.mark.parametrize("name, vendor", [("AMD Radeon", "amd"), ("Intel Graphics", "intel"), ("Other adapter", "unknown")])
def test_non_nvidia_gpu_and_estimated_vram(monkeypatch, tmp_path, name, vendor):
    monkeypatch.setattr(detector, "_run_command", lambda args: json.dumps({"cpu_names": [], "gpus": [{"Name": name, "AdapterRAM": 2 * detector.GIB}]}))
    profile = detector.detect_hardware(tmp_path)
    assert profile.gpus[0].vendor == vendor
    assert profile.gpus[0].vram_gb == 2
    assert profile.gpus[0].vram_is_estimate
    assert profile.warnings


def test_nvidia_smi_replaces_estimate_preserves_intel(monkeypatch, tmp_path):
    monkeypatch.setattr(detector.shutil, "which", lambda name: "nvidia-smi.exe")

    def command(args):
        if args[0] == "nvidia-smi":
            return "NVIDIA Test GPU, 12288\n"
        return json.dumps({"cpu_names": ["CPU"], "gpus": [
            {"Name": "NVIDIA Test GPU", "AdapterRAM": 1 * detector.GIB},
            {"Name": "Intel Graphics", "AdapterRAM": None},
        ]})

    monkeypatch.setattr(detector, "_run_command", command)
    profile = detector.detect_hardware(tmp_path)
    assert len(profile.gpus) == 2
    nvidia = next(gpu for gpu in profile.gpus if gpu.vendor == "nvidia")
    assert nvidia.vram_gb == 12
    assert not nvidia.vram_is_estimate
    assert nvidia.source == "nvidia_smi"


@pytest.mark.parametrize("error", [FileNotFoundError(), subprocess.TimeoutExpired("query", 10), ValueError("bad output")])
def test_gpu_query_failures_are_graceful(monkeypatch, tmp_path, error):
    def fail(args):
        raise error

    monkeypatch.setattr(detector, "_run_command", fail)
    profile = detector.detect_hardware(tmp_path)
    assert profile.cpu.name == "Fallback CPU"
    assert not profile.gpu_detection_complete
    assert profile.gpus == []
    assert profile.warnings


def test_ram_cpu_storage_failures_are_graceful(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise OSError("Unavailable")

    monkeypatch.setattr(detector.psutil, "cpu_count", fail)
    monkeypatch.setattr(detector.psutil, "virtual_memory", fail)
    monkeypatch.setattr(detector.shutil, "disk_usage", fail)
    profile = detector.detect_hardware(tmp_path)
    assert profile.cpu.logical_cores is None
    assert profile.ram.total_gb is None
    assert profile.storage.free_gb is None
    assert len(profile.warnings) == 3


def test_non_windows_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(detector.platform, "system", lambda: "Linux")

    def forbidden(args):
        pytest.fail("Must not call Windows probes on Linux")

    monkeypatch.setattr(detector, "_run_command", forbidden)
    profile = detector.detect_hardware(tmp_path)
    assert profile.ram.total_gb == 32
    assert not profile.gpu_detection_complete
    assert profile.warnings


@pytest.mark.parametrize("output", ["NVIDIA GPU, N/A", "unexpected"])
def test_malformed_nvidia_output_does_not_break_api(monkeypatch, tmp_path, output):
    monkeypatch.setattr(detector.shutil, "which", lambda name: "nvidia-smi.exe")
    monkeypatch.setattr(detector, "_run_command", lambda args: output if args[0] == "nvidia-smi" else '{"cpu_names": [], "gpus": []}')
    profile = detector.detect_hardware(tmp_path)
    assert any("nvidia-smi failed" in warning for warning in profile.warnings)
