import json
import subprocess
import io
from types import SimpleNamespace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from director.main import create_app, get_runtime_report
from director.system import runtime as r


@pytest.fixture
def passive(monkeypatch):
    monkeypatch.setattr(r, "driver_inventory", lambda: ([], r.Observation(source="test", detail="Unknown"), []))


def environment(tmp_path):
    root = tmp_path / "env"
    (root / "Scripts").mkdir(parents=True)
    (root / "Scripts/python.exe").write_bytes(b"never execute")
    (root / "pyvenv.cfg").write_text("version = 3.13.1\n", encoding="utf-8")
    (root / "Lib/site-packages").mkdir(parents=True)
    return root


def test_configured_environment_metadata_without_execution(tmp_path, monkeypatch):
    root = environment(tmp_path)
    package = root / "Lib/site-packages/torch-2.7.0.dist-info"
    package.mkdir()
    (package / "METADATA").write_bytes(b"Name: torch\r\nVersion: 2.7.0+cu128\r\n")
    monkeypatch.setattr(r, "run_diagnostic", lambda *_: pytest.fail("No interpreter execution"))
    python, torch = r.inspect_environment(root)
    assert python.version == "3.13.1"
    assert torch.status == "installed"
    assert torch.version == "2.7.0+cu128"
    assert "not tested" in torch.detail


def test_missing_python_and_torch(tmp_path):
    root = environment(tmp_path)
    (root / "Scripts/python.exe").unlink()
    python, torch = r.inspect_environment(root)
    assert python.status == torch.status == "not_detected"


@pytest.mark.parametrize("text", ["Name: torch\n", "Name: other\nVersion: 1\n", "x" * (r.LIMIT + 1), "Name: torch\nVersion: garbage\n"], ids=["missing-version", "wrong-package", "oversized", "invalid-version"])
def test_bad_torch_metadata_unknown(tmp_path, text):
    root = environment(tmp_path)
    package = root / "Lib/site-packages/torch-1.dist-info"
    package.mkdir()
    (package / "METADATA").write_text(text, encoding="utf-8")
    assert r.inspect_environment(root)[1].status == "unknown"


def test_ambiguous_torch_unknown(tmp_path):
    root = environment(tmp_path)
    for version in ("1", "2"):
        (root / f"Lib/site-packages/torch-{version}.dist-info").mkdir()
    assert r.inspect_environment(root)[1].status == "unknown"


@pytest.mark.parametrize("path", ["relative", "C:/safe/../outside"])
def test_unsafe_configuration(path):
    assert r.inspect_comfyui(Path(path)).status == "unknown"
    assert r.inspect_environment(Path(path))[0].status == "unknown"


def test_comfy_unconfigured_missing_and_incomplete(tmp_path):
    assert r.inspect_comfyui(None).status == "not_configured"
    assert r.inspect_comfyui(tmp_path / "absent").status == "not_detected"
    assert r.inspect_comfyui(tmp_path).status == "not_detected"


def test_comfy_metadata_not_execution(tmp_path):
    for name in ("main.py", "nodes.py", "requirements.txt"):
        (tmp_path / name).write_text("raise Exception('never execute')", encoding="utf-8")
    (tmp_path / "comfy").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.3.1"\n', encoding="utf-8")
    observed = r.inspect_comfyui(tmp_path)
    assert observed.status == "installed"
    assert observed.version == "0.3.1"
    (tmp_path / "pyproject.toml").write_text("[invalid", encoding="utf-8")
    assert r.inspect_comfyui(tmp_path).status == "unknown"


def test_symlink_refused(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Creating links requires Windows privileges")
    assert r.inspect_comfyui(link).status == "unknown"
    assert r.inspect_comfyui(link / "nested").status == "unknown"


def test_junction_attributes_refused_without_privileges(tmp_path, monkeypatch):
    original = Path.lstat
    def attributes(path):
        return SimpleNamespace(st_file_attributes=0x400, st_mode=original(path).st_mode) if path == tmp_path else original(path)
    monkeypatch.setattr(Path, "lstat", attributes)
    assert r.inspect_comfyui(tmp_path).status == "unknown"


@pytest.mark.parametrize("oversized", [False, True])
def test_process_bounds(monkeypatch, oversized):
    class Process:
        stdout = io.BytesIO(b"x" * (r.LIMIT + 1) if oversized else b"result")
        returncode = None
        killed = False
        def wait(self, timeout=None):
            if timeout == 5 and not oversized:
                raise subprocess.TimeoutExpired("fixed tool", 5)
            self.returncode = 0
        def kill(self):
            self.killed = True
        def poll(self):
            return self.returncode
    process = Process()
    monkeypatch.setattr(r.subprocess, "Popen", lambda *_args, **_kwargs: process)
    with pytest.raises((ValueError, subprocess.TimeoutExpired)):
        r.run_diagnostic(["fixed-test-tool"])
    assert process.killed


def windows(monkeypatch, tmp_path, output):
    monkeypatch.setattr(r.platform, "system", lambda: "Windows")
    monkeypatch.setenv("SystemRoot", str(tmp_path))
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    tool = tmp_path / "System32/nvidia-smi.exe"
    tool.parent.mkdir(exist_ok=True)
    tool.write_bytes(b"fixture only")
    monkeypatch.setattr(r, "run_diagnostic", output)
    return tool


@pytest.mark.parametrize("label", ["CUDA Version", "CUDA UMD Version"])
def test_nvidia_driver_cuda_distinction(monkeypatch, tmp_path, label):
    def output(args):
        if "-Command" in args:
            return json.dumps([{"Name": "Intel Graphics", "DriverVersion": "31.0.1"}])
        if len(args) > 1:
            return "NVIDIA Test GPU, 580.88\n"
        return f"{label}: 13.0"
    windows(monkeypatch, tmp_path, output)
    gpus, cuda, warnings = r.driver_inventory()
    assert [gpu.vendor for gpu in gpus] == ["intel", "nvidia"]
    assert cuda.version == "13.0"
    assert "not an installed toolkit" in cuda.detail
    assert not warnings


@pytest.mark.parametrize("vendor,name", [("amd", "AMD Radeon"), ("intel", "Intel Graphics")])
def test_non_nvidia_and_missing_tools(monkeypatch, tmp_path, vendor, name):
    tool = windows(monkeypatch, tmp_path, lambda args: json.dumps([{"Name": name, "DriverVersion": "1.2"}]))
    tool.unlink()
    gpus, cuda, warnings = r.driver_inventory()
    assert gpus[0].vendor == vendor
    assert cuda.status == "unknown"
    assert warnings


@pytest.mark.parametrize("failure", ["bad json", "{}", '[{"Name": 12}]'])
def test_malformed_driver_output(monkeypatch, tmp_path, failure):
    windows(monkeypatch, tmp_path, lambda args: failure)
    gpus, cuda, warnings = r.driver_inventory()
    assert not gpus
    assert cuda.status == "unknown"
    assert warnings


def test_diagnostic_timeout_is_unknown(monkeypatch, tmp_path):
    def timeout(args):
        raise subprocess.TimeoutExpired(args, 5)
    windows(monkeypatch, tmp_path, timeout)
    assert r.driver_inventory()[2]


def test_readiness_cannot_verify_execution(tmp_path, passive):
    report = r.detect_runtime(environment(tmp_path))
    assert report.readiness == "incomplete"
    assert report.gpu_execution == "not_tested"
    assert report.generation_ready is False
    assert report.missing_prerequisites
    installed = r.Observation(status="installed", source="test", detail="Metadata")
    report.python = report.pytorch = report.comfyui = installed
    assert r.evaluate_readiness(report).readiness == "unknown"
    assert not report.generation_ready


def test_runtime_endpoint_contract(tmp_path, passive):
    report = r.detect_runtime(environment(tmp_path))
    app = create_app(model_root=tmp_path / "models")
    app.dependency_overrides[get_runtime_report] = lambda: report
    with TestClient(app) as client:
        response = client.get("/api/system/runtime")
        assert response.status_code == 200
        assert r.RuntimeReport.model_validate(response.json()) == report
        assert str(tmp_path) not in response.text
