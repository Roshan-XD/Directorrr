from typing import Literal

from pydantic import BaseModel, Field


class CPUInfo(BaseModel):
    name: str | None = None
    physical_cores: int | None = Field(default=None, ge=1)
    logical_cores: int | None = Field(default=None, ge=1)


class RAMInfo(BaseModel):
    total_gb: float | None = Field(default=None, ge=0)
    available_gb: float | None = Field(default=None, ge=0)


class GPUInfo(BaseModel):
    name: str
    vendor: Literal["nvidia", "amd", "intel", "unknown"]
    vram_gb: float | None = Field(default=None, ge=0)
    vram_is_estimate: bool = False
    source: Literal["windows_cim", "nvidia_smi"]
    # Unknown until a reliable probe is available; do not guess from the GPU name.
    architecture: str | None = None


class StorageInfo(BaseModel):
    path: str
    total_gb: float | None = Field(default=None, ge=0)
    free_gb: float | None = Field(default=None, ge=0)


class HardwareProfile(BaseModel):
    platform: str
    cpu: CPUInfo
    ram: RAMInfo
    gpus: list[GPUInfo] = Field(default_factory=list)
    # An empty list after failed detection does not prove that no GPU exists.
    gpu_detection_complete: bool = False
    storage: StorageInfo
    warnings: list[str] = Field(default_factory=list)
