"""Read local hardware without installing drivers or requiring administrator access."""

import csv
import io
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

import psutil

from director.system.schemas import CPUInfo, GPUInfo, HardwareProfile, RAMInfo, StorageInfo

GIB = 1024**3

# Fixed script: user input is never interpolated into a shell command.
WINDOWS_QUERY = """
$ErrorActionPreference = 'Stop'
$cpu = @(Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name)
$gpus = @(Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM)
@{ cpu_names = $cpu; gpus = $gpus } | ConvertTo-Json -Depth 4 -Compress
"""


def _run_command(arguments: list[str]) -> str:
    result = subprocess.run(
        arguments,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    return result.stdout


def _vendor(name: str) -> str:
    lowered = name.lower()
    if "nvidia" in lowered:
        return "nvidia"
    if "amd" in lowered or "radeon" in lowered or "advanced micro devices" in lowered:
        return "amd"
    if "intel" in lowered:
        return "intel"
    return "unknown"


def _windows_hardware() -> tuple[str | None, list[GPUInfo]]:
    output = _run_command([
        "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; " + WINDOWS_QUERY,
    ])
    data = json.loads(output.lstrip("\ufeff"))
    names = data.get("cpu_names", [])
    gpus = []
    for item in data.get("gpus", []):
        name = item.get("Name") or "Unknown display adapter"
        adapter_ram = item.get("AdapterRAM")
        # AdapterRAM is a 32-bit Windows field; it can truncate modern VRAM.
        # Expose it only as an estimate, never as proof of compatibility.
        estimate = float(adapter_ram) / GIB if adapter_ram and float(adapter_ram) > 0 else None
        gpus.append(GPUInfo(
            name=name, vendor=_vendor(name), vram_gb=estimate,
            vram_is_estimate=estimate is not None, source="windows_cim",
        ))
    return "; ".join(names) or None, gpus


def _nvidia_hardware() -> list[GPUInfo]:
    output = _run_command([
        "nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits",
    ])
    gpus = []
    for row in csv.reader(io.StringIO(output)):
        if len(row) != 2:
            raise ValueError("Unexpected nvidia-smi output")
        gpus.append(GPUInfo(
            name=row[0].strip(), vendor="nvidia", vram_gb=float(row[1].strip()) / 1024,
            source="nvidia_smi",
        ))
    return gpus


def detect_hardware(storage_path: Path) -> HardwareProfile:
    warnings: list[str] = []
    cpu = CPUInfo(name=platform.processor() or None)
    ram = RAMInfo()
    storage = StorageInfo(path=str(storage_path.resolve()))
    gpus: list[GPUInfo] = []
    complete = False

    try:
        cpu.physical_cores = psutil.cpu_count(logical=False) or None
        cpu.logical_cores = psutil.cpu_count(logical=True) or None
    except (OSError, RuntimeError):
        warnings.append("CPU core counts could not be read.")
    try:
        memory = psutil.virtual_memory()
        ram = RAMInfo(total_gb=memory.total / GIB, available_gb=memory.available / GIB)
    except (OSError, RuntimeError):
        warnings.append("RAM information could not be read.")
    try:
        disk = shutil.disk_usage(storage_path)
        storage = StorageInfo(path=storage.path, total_gb=disk.total / GIB, free_gb=disk.free / GIB)
    except OSError:
        warnings.append("Storage information could not be read for the configured path.")

    if platform.system() == "Windows":
        try:
            name, gpus = _windows_hardware()
            cpu.name = name or cpu.name
            complete = True
        except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
            warnings.append("Windows CPU/GPU query failed; GPU detection may be incomplete.")
    else:
        warnings.append("Windows GPU detection is unavailable on this operating system.")

    # NVIDIA is optional. AMD/Intel adapters remain visible when this tool is absent.
    if shutil.which("nvidia-smi"):
        try:
            nvidia_gpus = _nvidia_hardware()
            if nvidia_gpus:
                gpus = [gpu for gpu in gpus if gpu.vendor != "nvidia"] + nvidia_gpus
        except (OSError, subprocess.SubprocessError, ValueError):
            warnings.append("nvidia-smi failed; NVIDIA VRAM may be unknown or estimated.")
    if any(gpu.vram_is_estimate for gpu in gpus):
        warnings.append("Windows AdapterRAM values are estimates and are not used to confirm VRAM requirements.")
    if not cpu.name:
        warnings.append("CPU name could not be read.")
    return HardwareProfile(
        platform=platform.system(), cpu=cpu, ram=ram, gpus=gpus,
        gpu_detection_complete=complete, storage=storage, warnings=warnings,
    )
