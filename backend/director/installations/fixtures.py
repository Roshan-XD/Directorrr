"""Opt-in offline demonstration metadata, not an AI model or generation claim."""

import hashlib

from director.models.schemas import ModelManifest

PAYLOAD = b"Director offline installation fixture. This is not a model.\n"
REVISION = "0" * 40  # Deliberately fictional fixture identity, never sent to Hugging Face.


def fixture_manifest() -> ModelManifest:
    text = "Director fixture license v1: this tiny synthetic text is provided for installation testing only. No AI weights or generation capabilities."
    license_info = {"identifier": "Director-Fixture-Only", "source": "https://example.invalid/director-fixture-license-v1",
                    "acknowledgement_requirements": ["Acknowledge that this is a test fixture, not an AI model."]}
    return ModelManifest.model_validate({
        "schema_version": 2, "id": "fixture-tiny", "name": "MOCK installation fixture (not an AI model)",
        "description": "Synthetic offline byte fixture. Never usable for generation; repositories/revisions are fictional.",
        "is_mock": True, "is_fixture": True, "tasks": ["text-to-video"], "runtime": "comfyui", "license": "Director-Fixture-Only",
        "huggingface_repo_id": None, "pinned_revision": None,
        "requirements": {"min_ram_gb": None, "min_free_storage_gb": None, "gpu_required": False, "min_vram_gb": 0},
        "execution_profile": {"backend": "cpu", "width": 1, "height": 1, "frames": 1},
        "evidence": [{"subject": "offline fixture", "quality": "unverified", "detail": "Fictional test metadata only."}],
        "license_info": license_info, "artifact_installation_reviewed": True,
        "license_documents": [{"id": "fixture-license", "version": "1", "text": text,
                               "sha256": hashlib.sha256(text.encode()).hexdigest()}],
        "components": [{"id": "tiny", "role": "config", "repository_id": "Director-Fixtures/tiny",
                        "pinned_revision": REVISION, "filename": "tiny.txt", "destination": "checkpoints/tiny.txt",
                        "expected_size_bytes": len(PAYLOAD), "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
                        "license_info": license_info}],
        "unresolved_assumptions": ["Offline installation fixture has no inference implementation."],
    })


def fixture_payloads() -> dict[tuple, bytes]:
    return {("Director-Fixtures/tiny", REVISION, "tiny.txt"): PAYLOAD}
