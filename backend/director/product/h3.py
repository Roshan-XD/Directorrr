"""Official H3 subset review. No weights, environment changes or execution.

The current laptop cannot meet the documented host-memory recipe. A review
button must therefore explain the blockers, not disguise a data download as a
working model installation.
"""
import hashlib
import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import Field, model_validator

from director.installations.api import require_manager_key
from director.installations.schemas import ManagerError
from director.models.validation import relative_file_path
from director.product.capabilities import StrictModel
from director.system.schemas import HardwareProfile

REPOSITORY = "MiniMaxAI/MiniMax-H3"
REVISION = "42ed227ee7df40d41602854ae760620d6eb651fe"
# Locally frozen reviewed metadata digest, not an upstream signature.
INVENTORY_SHA256 = "26352cf6375cdaa11e654aec1604825ba070c50618d5920eab5a845e5d042f19"
LICENSE_SHA256 = "59b99642b95ea21630e311198ddbfffbfe05aadba0c2f5d884cbdf4efcc90f44"
FOLDERS = {"transformer", "text_encoder", "tokenizer", "processor", "vae", "audio_vae", "scheduler", "audio_scheduler"}
MEMORY_SOURCE = "https://huggingface.co/docs/diffusers/v0.41.0/api/pipelines/minimax_h3#memory"


class H3File(StrictModel):
    filename: str
    expected_size_bytes: int = Field(gt=0)
    sha256: str | None = Field(pattern=r"^[0-9a-f]{64}$")
    git_blob_sha1: str = Field(pattern=r"^[0-9a-f]{40}$")
    hash_evidence: Literal["published_lfs_sha256", "pinned_git_blob_sha1"]
    url: str
    destination: str

    @model_validator(mode="after")
    def exact(self):
        # Diffusers has a separate, reviewed folder allowlist. Do not expand
        # the existing ComfyUI destination policy to accommodate this recipe.
        relative_file_path(self.filename)
        if self.destination != self.filename:
            raise ValueError("H3 destination must match the reviewed relative file")
        if self.filename.split("/")[0] not in FOLDERS and self.filename not in {"LICENSE", "modular_model_index.json"}:
            raise ValueError("File outside the T2VA component allowlist")
        if self.url != f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{self.filename}":
            raise ValueError("H3 requires the reviewed official immutable URL")
        if bool(self.sha256) != (self.hash_evidence == "published_lfs_sha256"):
            raise ValueError("Integrity evidence mismatch")
        return self


class H3Recipe(StrictModel):
    schema_version: Literal[1]
    family_id: Literal["minimax-h3-official-t2va"]
    repository: Literal["MiniMaxAI/MiniMax-H3"]
    revision: Literal["42ed227ee7df40d41602854ae760620d6eb651fe"]
    workflow: Literal["t2va"]
    runtime: Literal["diffusers-modular"]
    runtime_version: Literal["0.41.0"]
    status: Literal["review_only"]
    execution_validated: Literal[False]
    files: list[H3File] = Field(min_length=1, max_length=100)
    excluded_folders: list[str]
    license_source: str
    license_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    download_bytes: int = Field(gt=0)
    source: str

    @model_validator(mode="after")
    def complete_inventory(self):
        paths = [f.filename for f in self.files]
        if len(set(paths)) != len(paths) or sum(f.expected_size_bytes for f in self.files) != self.download_bytes:
            raise ValueError("Duplicate or inconsistent H3 inventory")
        if {p.split("/")[0] for p in paths if "/" in p} != FOLDERS:
            raise ValueError("Missing common H3 component")
        if self.license_source != f"https://huggingface.co/{REPOSITORY}/blob/{REVISION}/LICENSE":
            raise ValueError("Unpinned H3 license")
        if self.source != "https://huggingface.co/docs/diffusers/v0.41.0/api/pipelines/minimax_h3":
            raise ValueError("Unreviewed runtime recipe")
        inventory = [f.model_dump() for f in self.files]
        if hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest() != INVENTORY_SHA256:
            raise ValueError("Inventory differs from the reviewed frozen subset")
        if self.license_sha256 != LICENSE_SHA256:
            raise ValueError("License differs from the captured pinned agreement")
        return self


def build_h3_review(recipe: H3Recipe, hardware: HardwareProfile):
    # Decimal GB is what the publisher documents. This is guidance, not a
    # measured minimum or a guarantee that a larger machine will execute H3.
    required = recipe.download_bytes * 3 + 10 * 1024**3
    free = int(hardware.storage.free_gb * 1024**3) if hardware.storage.free_gb is not None else None
    ram = int(hardware.ram.total_gb * 1024**3) if hardware.ram.total_gb is not None else None
    blockers = []
    if ram is None:
        blockers.append("Host RAM is unknown; the documented INT8 offload recipe needs about 75 GB of host memory.")
    elif ram < 75_000_000_000:
        blockers.append("Host RAM is below the documented ~75 GB INT8 offload working set. Smaller frames do not remove weight residency.")
    if free is None:
        blockers.append("Free disk space could not be measured.")
    elif free < required:
        blockers.append("Insufficient disk for the current verified staging/cache/rollback budget.")
    if not any(g.vendor == "nvidia" and g.vram_gb is not None and not g.vram_is_estimate for g in hardware.gpus):
        blockers.append("A reliable NVIDIA VRAM measurement is missing; runtime compatibility is unverified.")
    missing_sha = [f.filename for f in recipe.files if f.sha256 is None]
    blockers.extend([
        "No isolated H3 Diffusers execution adapter or reviewed dependency lock is installed. The Wan-only ComfyUI adapter cannot run this recipe.",
        "Explicit exact-file download authorization and current territorial/license acknowledgement have not been recorded.",
    ])
    if missing_sha:
        blockers.append("Small configuration/tokenizer files have pinned Git blob identities, but the SHA-256-only installer needs reviewed SHA-256 metadata before activation.")
    result = {
        "repository": recipe.repository, "revision": recipe.revision, "workflow": recipe.workflow,
        "runtime": recipe.runtime, "runtime_version": recipe.runtime_version,
        "files": [f.model_dump() for f in recipe.files], "download_bytes": recipe.download_bytes,
        "installed_payload_bytes": recipe.download_bytes, "required_free_bytes": required,
        "free_bytes": free, "hardware": {"ram_bytes": ram, "available_ram_gb": hardware.ram.available_gb,
            "gpus": [{"name": g.name, "vendor": g.vendor, "vram_gb": g.vram_gb, "is_estimate": g.vram_is_estimate} for g in hardware.gpus]},
        "memory_guidance_bytes": 75_000_000_000, "memory_evidence": "publisher_estimate_not_measured_minimum",
        "memory_source": MEMORY_SOURCE,
        "destination": "Director-owned isolated H3 candidate (not the active Wan model directory)",
        "license_source": recipe.license_source, "license_sha256": recipe.license_sha256,
        "license": "MiniMax H3 Community License Agreement, August 2, 2026",
        "license_conditions": ["Territorial grant excludes EU, UK, South Korea and USA; do not infer the user's eligibility.",
            "Acceptable Use Policy and applicable laws apply to private use.",
            "Do not use H3 outputs to improve other AI models; disclose AI generation for public outputs.",
            "Commercial/redistribution obligations are separate; Qwen encoder has Apache-2.0 terms."],
        "blockers": blockers, "warnings": [*hardware.warnings,
            "Native stereo audio is inseparable from T2VA and must be preserved by a future adapter.",
            "No speed, fit or execution success is promised. INT8 group offload would require transformer, encoder and video VAE offloading.",
            "This official 54-file plan is different from the older Comfy-Org converted 5-file plan; no precision substitution was made."],
        "state": "not_installed", "can_install": False, "ready": False,
        "proposed_test": {"width": 960, "height": 544, "frames": 124, "fps": 24,
                          "steps": 20, "audio_sample_rate": 32000, "audio_channels": 2,
                          "execution_validated": False},
    }
    result["digest"] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


class H3Approval(StrictModel):
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirmed: bool
    accepted_license: bool
    eligible_territory: bool


def h3_router(root: Path, get_hardware):
    router = APIRouter(prefix="/api/product/h3", dependencies=[Depends(require_manager_key)])
    recipe = H3Recipe.model_validate_json((root / "model_registry/plans/minimax-h3-official-t2va.json").read_text(encoding="utf-8"))

    @router.get("/installation-plan")
    def plan(hardware: HardwareProfile = Depends(get_hardware)):
        return build_h3_review(recipe, hardware)

    @router.post("/installations")
    def install(body: H3Approval, hardware: HardwareProfile = Depends(get_hardware)):
        review = build_h3_review(recipe, hardware)
        if not body.confirmed or not body.accepted_license or not body.eligible_territory:
            raise ManagerError("confirmation_required", "Exact plan, license and territory require explicit review", 422)
        if review["digest"] != body.digest:
            raise ManagerError("plan_changed", "Hardware/storage review changed; review the plan again", 409)
        # No flag or UI acknowledgement can bypass unavailable execution support.
        raise ManagerError("h3_installation_blocked", review["blockers"][0], 409)

    return router
