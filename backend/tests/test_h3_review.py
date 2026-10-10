"""No weights, package installation, GPU load, or model deletion."""
import json
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from director.main import PROJECT_ROOT, create_app, get_hardware
from director.product.h3 import H3Recipe, build_h3_review, REPOSITORY, REVISION

KEY = "h3-review-test-" * 4


@pytest.fixture
def recipe():
    return H3Recipe.model_validate_json((PROJECT_ROOT / "model_registry/plans/minimax-h3-official-t2va.json").read_text())


def test_official_exact_workflow_subset(recipe):
    assert recipe.repository == REPOSITORY and recipe.revision == REVISION
    assert len(recipe.files) == 54 and recipe.download_bytes == 144039659327
    assert recipe.download_bytes == sum(f.expected_size_bytes for f in recipe.files)
    assert not any(f.filename.startswith(("transformer_ref/", "h3-base/", "loras/")) for f in recipe.files)
    assert len([f for f in recipe.files if f.filename.startswith("transformer/") and f.filename.endswith(".safetensors")]) == 14
    assert len([f for f in recipe.files if f.filename.startswith("text_encoder/") and f.filename.endswith(".safetensors")]) == 14
    assert any(f.filename.startswith("audio_vae/") for f in recipe.files)
    assert all(f.sha256 for f in recipe.files if f.filename.endswith(".safetensors"))


@pytest.mark.parametrize("mutation", ["repository", "revision", "runtime", "duplicate", "missing", "bytes", "url", "path", "hash", "ready", "license", "unreviewed_file"])
def test_invalid_h3_recipe(recipe, mutation):
    data = deepcopy(recipe.model_dump())
    if mutation in {"repository", "revision", "runtime"}: data[mutation] = "unexpected"
    elif mutation == "duplicate": data["files"].append(data["files"][0])
    elif mutation == "missing":
        data["files"] = [f for f in data["files"] if not f["filename"].startswith("audio_vae/")]
        data["download_bytes"] = sum(f["expected_size_bytes"] for f in data["files"])
    elif mutation == "bytes": data["download_bytes"] += 1
    elif mutation == "url": data["files"][0]["url"] = "https://attacker.invalid/model"
    elif mutation == "path": data["files"][0]["destination"] = "../Wan"
    elif mutation == "hash": data["files"][0]["sha256"] = "x"
    elif mutation == "ready": data["execution_validated"] = True
    elif mutation == "license": data["license_sha256"] = "f" * 64
    elif mutation == "unreviewed_file":
        file = data["files"][0]
        file.update(filename="tokenizer/unreviewed.json", destination="tokenizer/unreviewed.json",
                    url=f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/tokenizer/unreviewed.json")
    with pytest.raises(ValidationError): H3Recipe.model_validate(data)


def test_realistic_laptop_is_blocked(recipe, hardware):
    plan = build_h3_review(recipe, hardware)
    assert not plan["can_install"] and not plan["ready"]
    assert any("Host RAM is below" in b for b in plan["blockers"])
    assert any("Insufficient disk" in b for b in plan["blockers"])
    assert plan["required_free_bytes"] == 442856396221


def test_more_memory_never_authorizes_install(recipe, hardware):
    hardware.ram.total_gb = 128
    hardware.storage.free_gb = 1000
    plan = build_h3_review(recipe, hardware)
    assert not any("Host RAM is below" in b for b in plan["blockers"])
    assert not any("Insufficient disk" in b for b in plan["blockers"])
    assert any("execution adapter" in b for b in plan["blockers"])
    assert not plan["can_install"] and not plan["ready"]


def test_unknown_and_estimated_hardware(recipe, hardware):
    hardware.ram.total_gb = None
    hardware.storage.free_gb = None
    hardware.gpus[0].vram_is_estimate = True
    plan = build_h3_review(recipe, hardware)
    assert plan["free_bytes"] is None
    assert len(plan["blockers"]) >= 5


def test_review_api_auth_and_no_transfer(tmp_path, hardware):
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key=KEY)
    app.dependency_overrides[get_hardware] = lambda: hardware
    with TestClient(app, base_url="http://127.0.0.1") as client:
        endpoint = "/api/product/h3/installation-plan"
        assert client.get(endpoint).status_code == 403
        assert client.get(endpoint, headers={"X-Director-Key": "wrong"}).status_code == 403
        assert client.get(endpoint, headers={"X-Director-Key": KEY, "Origin": "http://evil.invalid"}).status_code == 403
        headers = {"X-Director-Key": KEY}
        plan = client.get(endpoint, headers=headers).json()
        assert plan["repository"] == REPOSITORY and not plan["ready"]
        start = "/api/product/h3/installations"
        approval = {"digest": plan["digest"], "confirmed": True, "accepted_license": True, "eligible_territory": True}
        assert client.post(start, headers=headers, json={**approval, "confirmed": False}).status_code == 422
        assert client.post(start, headers=headers, json={**approval, "eligible_territory": False}).status_code == 422
        assert client.post(start, headers=headers, json={**approval, "digest": "f" * 64}).json()["detail"]["code"] == "plan_changed"
        response = client.post(start, headers=headers, json=approval)
        assert response.status_code == 409 and response.json()["detail"]["code"] == "h3_installation_blocked"
        assert not app.state.product.downloads.jobs
        assert not app.state.installations._jobs
