"""Passive runtime inventory. Never imports torch or executes configured runtimes."""

import csv
import io
import json
import os
import platform
import re
import subprocess
import sysconfig
import threading
import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from packaging.version import Version

Status = Literal["installed", "not_detected", "unknown", "not_tested", "not_configured"]
LIMIT = 65536


class Observation(BaseModel):
    status: Status = "unknown"
    version: str | None = None
    source: str
    detail: str


class DriverObservation(BaseModel):
    name: str
    vendor: Literal["nvidia", "amd", "intel", "unknown"]
    driver: Observation


class RuntimeReport(BaseModel):
    operating_system: str
    architecture: str
    python: Observation
    pytorch: Observation
    comfyui: Observation
    cuda_toolkit: Observation
    driver_cuda: Observation
    gpu_drivers: list[DriverObservation] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    readiness: Literal["incomplete", "unknown"] = "unknown"
    gpu_execution: Literal["not_tested"] = "not_tested"
    generation_ready: Literal[False] = False


def safe_path(path: Path) -> Path:
    """Refuse links/reparse points, including intermediate Windows junctions."""
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Absolute, non-traversing configuration required")
    for part in [*reversed(path.parents), path]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if part.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Linked configuration refused")
    return path


def read_metadata(path: Path) -> str:
    safe_path(path)
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("Metadata exceeds limit")
    return data.decode("utf-8")


def run_diagnostic(arguments: list[str]) -> str:
    """Fixed callers only; cap both process time and captured output."""
    process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    output: list[bytes] = []

    def read():
        output.append(process.stdout.read(LIMIT + 1))
        if len(output[0]) > LIMIT:
            process.kill()

    worker = threading.Thread(target=read, daemon=True)
    worker.start()
    try:
        process.wait(timeout=5)
        worker.join(timeout=1)
        if worker.is_alive() or not output or len(output[0]) > LIMIT or process.returncode:
            raise ValueError("Diagnostic failed or exceeded output limit")
        return output[0].decode("utf-8-sig")
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        worker.join(timeout=1)
        if not worker.is_alive():
            process.stdout.close()


def vendor(name: str) -> str:
    lower = name.lower()
    if "nvidia" in lower:
        return "nvidia"
    if any(value in lower for value in ("amd", "radeon", "advanced micro devices")):
        return "amd"
    return "intel" if "intel" in lower else "unknown"


def driver_inventory() -> tuple[list[DriverObservation], Observation, list[str]]:
    gpus = []
    warnings = []
    cuda = Observation(source="nvidia_smi", detail="Driver CUDA capability was not observed.")
    if platform.system() != "Windows":
        return gpus, cuda, ["Windows driver inventory is unavailable on this OS."]
    # Trusted OS/vendor locations only: never execute a tool from the working directory.
    system = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32"
    try:
        powershell = safe_path(system / "WindowsPowerShell/v1.0/powershell.exe")
        script = "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; @(Get-CimInstance Win32_VideoController -ErrorAction Stop | Select-Object Name,DriverVersion) | ConvertTo-Json -Compress"
        data = json.loads(run_diagnostic([str(powershell), "-NoProfile", "-NonInteractive", "-Command", script]))
        if not isinstance(data, list) or len(data) > 64:
            raise ValueError("Invalid driver inventory")
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("Name"), str):
                raise ValueError("Invalid adapter")
            version = item.get("DriverVersion")
            if version is not None and (not isinstance(version, str) or len(version) > 80):
                raise ValueError("Invalid driver version")
            gpus.append(DriverObservation(name=item["Name"][:200], vendor=vendor(item["Name"]),
                driver=Observation(status="installed" if version else "unknown", version=version,
                                   source="windows_cim", detail="Windows display-driver metadata; execution not tested.")))
    except (OSError, ValueError, subprocess.SubprocessError):
        gpus = []
        warnings.append("Windows driver inventory failed or timed out; GPU absence is not established.")
    candidates = [system / "nvidia-smi.exe", Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "NVIDIA Corporation/NVSMI/nvidia-smi.exe"]
    try:
        tool = next((safe_path(p) for p in candidates if p.is_file()), None)
        if tool is None:
            warnings.append("nvidia-smi was not found in trusted locations; NVIDIA metadata is unknown.")
        else:
            rows = list(csv.reader(io.StringIO(run_diagnostic([str(tool), "--query-gpu=name,driver_version", "--format=csv,noheader"]))))
            detected = []
            if not rows or len(rows) > 64:
                raise ValueError("Invalid NVIDIA inventory")
            for row in rows:
                if len(row) != 2 or not re.fullmatch(r"\d+(?:\.\d+)+", row[1].strip()) or not row[0].strip():
                    raise ValueError("Invalid NVIDIA row")
                detected.append(DriverObservation(name=row[0].strip()[:200], vendor="nvidia", driver=Observation(
                    status="installed", version=row[1].strip(), source="nvidia_smi", detail="NVIDIA driver report; GPU execution not tested.")))
            gpus = [gpu for gpu in gpus if gpu.vendor != "nvidia"] + detected
            try:
                summary = run_diagnostic([str(tool)])
                match = re.search(r"CUDA (?:UMD )?Version:\s*(\d+\.\d+)", summary)
                if match:
                    cuda = Observation(status="installed", version=match[1], source="nvidia_smi",
                        detail="Driver-supported CUDA ceiling, not an installed toolkit or PyTorch CUDA build.")
                else:
                    warnings.append("Driver CUDA capability was not present in diagnostic output.")
            except (OSError, ValueError, subprocess.SubprocessError):
                warnings.append("Driver CUDA capability query failed or timed out.")
    except (OSError, ValueError, subprocess.SubprocessError):
        warnings.append("NVIDIA diagnostic failed or timed out; CUDA metadata remains unknown.")
    return gpus, cuda, warnings


def inspect_environment(root: Path | None) -> tuple[Observation, Observation]:
    source = "configured_environment_metadata" if root is not None else "backend_environment_metadata"
    python = Observation(status="installed", version=platform.python_version(), source="backend_process",
                         detail="Running backend interpreter; not proof of a separate AI runtime.")
    torch = Observation(source=source, detail="PyTorch metadata could not be inspected; no package was imported.")
    environment_checked = root is None
    try:
        if root is not None:
            safe_path(root)
            if not root.is_dir():
                return (Observation(status="not_detected", source=source, detail="Configured environment directory is absent."), torch)
            executable = safe_path(root / "Scripts/python.exe")
            python = Observation(status="installed" if executable.is_file() else "not_detected", source=source,
                                 detail="Configured Windows environment interpreter file; execution not tested.")
            if (root / "pyvenv.cfg").is_file():
                match = re.search(r"(?m)^version\s*=\s*(\d+\.\d+\.\d+)\s*$", read_metadata(root / "pyvenv.cfg"))
                python.version = match[1] if match else None
            site = root / "Lib/site-packages"
        else:
            site = Path(sysconfig.get_path("purelib"))
        environment_checked = True
        safe_path(site)
        if not site.is_dir():
            return python, torch
        # Bound discovery to one site-packages directory; do not recursively scan.
        matches = []
        with os.scandir(site) as entries:
            for index, item in enumerate(entries):
                if index >= 2048:
                    raise ValueError("Environment inventory too large")
                if item.name.lower().startswith("torch-") and item.name.lower().endswith(".dist-info"):
                    matches.append(Path(item.path))
        if not matches:
            torch = Observation(status="not_detected", source=source, detail="No torch distribution metadata in the inspected environment.")
        elif len(matches) == 1:
            metadata = read_metadata(matches[0] / "METADATA")
            name = re.search(r"(?m)^Name: (.+)$", metadata)
            version = re.search(r"(?m)^Version: ([^\r\n]{1,80})\r?$", metadata)
            if not name or name[1].strip().lower() != "torch" or not version:
                raise ValueError("Invalid distribution metadata")
            Version(version[1].strip())
            torch = Observation(status="installed", version=version[1].strip(), source=source,
                                detail="Distribution metadata only; import, DLLs and CUDA build not tested.")
    except (OSError, ValueError, UnicodeError):
        if not environment_checked:
            python = Observation(source=source, detail="Configured environment metadata is unsafe or unreadable.")
    return python, torch


def inspect_comfyui(root: Path | None) -> Observation:
    source = "configured_comfyui_metadata"
    if root is None:
        return Observation(status="not_configured", source=source, detail="No ComfyUI directory configured; no search was performed.")
    try:
        safe_path(root)
        if not root.is_dir():
            return Observation(status="not_detected", source=source, detail="Configured ComfyUI directory is absent.")
        for filename in ("main.py", "nodes.py", "requirements.txt"):
            if not safe_path(root / filename).is_file():
                return Observation(status="not_detected", source=source, detail="Configured directory lacks expected ComfyUI files.")
        if not safe_path(root / "comfy").is_dir():
            return Observation(status="not_detected", source=source, detail="Configured directory lacks the comfy package directory.")
        version = None
        if (root / "pyproject.toml").is_file():
            metadata = tomllib.loads(read_metadata(root / "pyproject.toml"))
            value = metadata.get("project", {}).get("version")
            if isinstance(value, str) and len(value) <= 80:
                version = value
        return Observation(status="installed", version=version, source=source,
                           detail="Appears to be ComfyUI from expected files; source integrity, dependencies and execution not tested.")
    except (OSError, ValueError, UnicodeError):
        return Observation(source=source, detail="Configured ComfyUI path or metadata is unsafe, invalid or unreadable.")


def evaluate_readiness(report: RuntimeReport) -> RuntimeReport:
    """Pure, conservative summary; package presence never becomes execution proof."""
    report.missing_prerequisites = []
    for label, observation in (("Python", report.python), ("PyTorch", report.pytorch), ("ComfyUI", report.comfyui)):
        if observation.status in ("not_detected", "not_configured"):
            report.missing_prerequisites.append(f"{label}: {observation.detail}")
    report.unresolved_questions = [
        "A pinned ComfyUI/Python/PyTorch/driver configuration has not been validated.",
        "GPU architecture, CUDA execution and runtime imports have not been tested.",
        "Wan peak memory, workflow execution, encoding and licensing review remain unresolved.",
    ]
    report.warnings.extend(f"{label}: {item.detail}" for label, item in
                           (("Python", report.python), ("PyTorch", report.pytorch), ("ComfyUI", report.comfyui))
                           if item.status == "unknown")
    report.readiness = "incomplete" if report.missing_prerequisites else "unknown"
    return report


def detect_runtime(environment: Path | None = None, comfyui: Path | None = None) -> RuntimeReport:
    python, torch = inspect_environment(environment)
    drivers, cuda, warnings = driver_inventory()
    return evaluate_readiness(RuntimeReport(
        operating_system=platform.system(), architecture=platform.machine(), python=python, pytorch=torch,
        comfyui=inspect_comfyui(comfyui), driver_cuda=cuda, gpu_drivers=drivers, warnings=warnings,
        cuda_toolkit=Observation(status="not_tested", source="not_probed", detail="Toolkit discovery is deferred; driver CUDA does not prove a toolkit installation."),
    ))
