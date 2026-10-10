"""Tiny offline files only. Never transfer real weights or initialize CUDA."""
import copy
import hashlib
import json
import threading
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from director.main import PROJECT_ROOT, create_app
from director.installations.downloader import FixtureDownloader
from director.installations.schemas import ManagerError
from director.product.downloads import Selection, StartDownload
from director.product import optimized_h3 as h3
from director.product.capabilities import CreativeRequest, load_capabilities
from director.generation.h3_workflow import build_h3_workflow
from director.generation.service import DevelopmentGeneration, GenerationRequest


def test_frozen_four_file_recipe():
    r = h3.recipe(PROJECT_ROOT)
    assert len(r["components"]) == 4
    assert r["total_bytes"] == 33163649303 < 50_000_000_000
    assert all(c["sha256"] and len(c["pinned_revision"]) == 40 for c in r["components"])
    assert "Exhibit A" in r["license_text"]


@pytest.fixture
def manager(tmp_path, monkeypatch):
    r = copy.deepcopy(h3.recipe(PROJECT_ROOT))
    payloads = {}
    for i, c in enumerate(r["components"]):
        data = b"inert tiny artifact " + bytes([i])
        c.update(expected_size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        payloads[(c["repository_id"], c["pinned_revision"], c["filename"])] = data
    r["total_bytes"] = sum(c["expected_size_bytes"] for c in r["components"])
    monkeypatch.setattr(h3, "recipe", lambda root: copy.deepcopy(r))
    native = tmp_path / "native"
    (native / "receipts").mkdir(parents=True)
    (native / "models").mkdir()
    (native / "owner.json").write_text(json.dumps({"owner": "Director Stage 12 private development"}))
    (native / "receipts/comfy-source.json").write_text(json.dumps({"revision": h3.COMFY_REVISION}))
    (native / "receipts/cuda-smoke.json").write_text(json.dumps({"available": True, "capability": [12, 0], "torch": "2.12.1+cu130"}))
    d = Mock(); d.fetch.return_value = r["license_text"]
    refresh = Mock()
    value = h3.OptimizedH3Downloads(tmp_path / "downloads", d, tmp_path, native, refresh,
                                   h3_transport=FixtureDownloader(payloads), transport=FixtureDownloader({}))
    monkeypatch.setattr(value, "validate_nodes", Mock())
    yield value, r, refresh
    value.close()


def selection(r):
    return Selection(repository=r["repository"], files=[c["filename"] for c in r["components"]])


def confirmed(r, plan, **changes):
    return StartDownload(**selection(r).model_dump(), digest=plan["digest"], confirmed=True, accepted_license=True, **changes)


def test_plan_and_successful_registration(manager):
    m, r, refresh = manager
    plan = m.plan(selection(r))
    assert not plan["blockers"] and plan["free_bytes"] > plan["required_free_bytes"]
    assert "territory" in " ".join(plan["license_conditions"]).lower()
    # Merely viewing the plan creates no files or transfers.
    assert not m.storage.base.exists()
    job = m.start(confirmed(r, plan))
    m.threads[-1].join(5)
    assert m.jobs[job["id"]]["state"] == "completed"
    assert len(h3.registered_assets(m.project, m.native)) == 4
    from director.product.api import ProductServices
    from director.product.assets import AssetInventory
    product = ProductServices.__new__(ProductServices)
    product.root, product.native = m.project, m.native
    product.capabilities = load_capabilities(PROJECT_ROOT / "model_registry/capabilities")
    product.assets = AssetInventory(m.native / "models", h3.registered_assets(m.project, m.native), m.native / "owner.json")
    assert next(c for c in product.catalog(True)["models"] if c["id"] == h3.MODEL_ID)["runnable"]
    assert refresh.call_count == 1
    assert all((m.native / "models" / c["destination"]).read_bytes().startswith(b"inert") for c in r["components"])
    assert not (m.native / "models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors").exists()
    with pytest.raises(ManagerError, match="already installed"):
        m.start(confirmed(r, plan))
    p = m.native / "models" / r["components"][0]["destination"]
    p.write_bytes(b"changed")
    assert not h3.registered_assets(m.project, m.native)
    assert not next(c for c in product.catalog(True)["models"] if c["id"] == h3.MODEL_ID)["runnable"]


def test_reject_unreviewed_files_and_missing_consent(manager):
    m, r, _ = manager
    with pytest.raises(ManagerError):
        m.plan(Selection(repository=r["repository"], files=["../bad"]))
    plan = m.plan(selection(r))
    body = confirmed(r, plan).model_copy(update={"accepted_license": False})
    with pytest.raises(ManagerError):
        m.start(body)
    assert not m.jobs


def test_changed_license_and_insufficient_disk(manager, monkeypatch):
    m, r, _ = manager
    m.discovery.fetch.return_value = "Changed terms"
    assert m.plan(selection(r))["blockers"]
    m.discovery.fetch.return_value = r["license_text"]
    monkeypatch.setattr(h3.shutil, "disk_usage", lambda root: Mock(free=1))
    plan = m.plan(selection(r))
    assert "disk" in " ".join(plan["blockers"])
    with pytest.raises(ManagerError):
        m.start(confirmed(r, plan))


def test_activation_failure_rolls_back_and_preserves_wan(manager):
    m, r, refresh = manager
    wan = m.native / "models" / "wan-existing.bin"
    wan.write_bytes(b"original Wan")
    m.validate_nodes.side_effect = ManagerError("missing_node", "Node unavailable", 409)
    job = m.start(confirmed(r, m.plan(selection(r))))
    m.threads[-1].join(5)
    assert m.jobs[job["id"]]["state"] == "failed"
    assert wan.read_bytes() == b"original Wan"
    assert not h3.registered_assets(m.project, m.native)
    assert not refresh.called
    assert all(not (m.native / "models" / c["destination"]).exists() for c in r["components"])


def test_corruption_never_registers(manager):
    m, r, refresh = manager
    m.h3_transport = FixtureDownloader({(c["repository_id"],c["pinned_revision"],c["filename"]):b"bad" for c in r["components"]})
    job = m.start(confirmed(r, m.plan(selection(r))))
    m.threads[-1].join(5)
    assert m.jobs[job["id"]]["state"] == "failed"
    assert not refresh.called


def test_fixed_native_audio_workflow_and_mp4(tmp_path):
    cap = next(c for c in load_capabilities(PROJECT_ROOT / "model_registry/capabilities") if c.id == h3.MODEL_ID)
    body = CreativeRequest(model_id=h3.MODEL_ID, prompt="Ocean with waves sound", resolution="development", duration=5, quality="Native", seed=7, export_fps=24)
    settings = body.resolve(cap)
    graph = build_h3_workflow(settings["prompt"], 7, "a" * 32, settings)
    assert graph["38"]["inputs"]["type"] == "minimax"
    assert graph["56"]["inputs"]["audio"] == ["55", 0]
    assert graph["47"]["inputs"]["format"] == "mp4"
    with pytest.raises(ValueError):
        build_h3_workflow("a", 0, "a"*32, {**settings,"width":1344})
    client = Mock()
    client.request.side_effect = [{"queue_running":[],"queue_pending":[]}, {"prompt_id":"12345678-1234-1234-1234-123456789abc"}]
    engine = DevelopmentGeneration(client, tmp_path)
    job = engine.start(GenerationRequest(prompt=settings["prompt"],seed=7), settings=settings, creative=body.model_dump())
    assert client.request.call_args.args[1]["prompt"]["37"]["inputs"]["unet_name"] == "MiniMax-H3_FL2VA-NVFP4.safetensors"
    filename = "Director_Stage8_" + job.id + "_00001_.mp4"
    (tmp_path / filename).write_bytes(b"\x00\x00\x00\x18ftypmp42inert")
    client.request.side_effect = None
    client.request.return_value = {job.comfy_prompt_id:{"status":{"status_str":"success"}, "outputs":{"47":{"images":[{"filename":filename,"type":"output","subfolder":""}]}}}}
    assert engine.get(job.id).state == "completed"
    assert engine.output(job.id)[0] == filename


def test_install_api_authentication_and_origin(tmp_path, monkeypatch):
    monkeypatch.setenv("DIRECTOR_STUDIO_ROOT", str(tmp_path / "studio"))
    key = "h3-focused-manager-key-" * 3
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtimes", manager_key=key)
    body = selection(h3.recipe(PROJECT_ROOT)).model_dump()
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        for headers in ({}, {"X-Director-Key":"wrong"}, {"X-Director-Key":key,"Origin":"https://untrusted.example"}):
            assert client.post("/api/product/downloads/plan",json=body,headers=headers).status_code == 403
        app.state.product.downloads.plan = Mock(return_value={"review":"authenticated only"})
        response = client.post("/api/product/downloads/plan",json=body,headers={"X-Director-Key":key})
        assert response.status_code == 200
