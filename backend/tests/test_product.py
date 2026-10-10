"""Offline product behavior and safety; never models, GPU work or real deletion."""
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from director.product.capabilities import Capability, CreativeRequest, Shot, load_capabilities
from director.product.assets import Asset, AssetInventory, directory_size
from director.product.console import ActivityConsole
from director.product.discovery import Discovery
from director.generation.service import DevelopmentGeneration, GenerationRequest
from director.installations.schemas import ManagerError
from director.main import create_app, PROJECT_ROOT

KEY="product-test-key-"*3
PID="12345678-1234-1234-1234-123456789abc"
@pytest.fixture
def wan(): return next(c for c in load_capabilities(PROJECT_ROOT/"model_registry/capabilities") if c.id=="wan21-t2v-13b")
class Fake:
    def __init__(self): self.queue={"queue_running":[],"queue_pending":[]}; self.history={}; self.calls=[]
    def request(self,path,body=None):
        self.calls.append((path,body))
        if path=="/prompt": return {"prompt_id":PID}
        if path=="/queue":
            if body: self.queue["queue_pending"]=[item for item in self.queue["queue_pending"] if item[1] not in body["delete"]]
            return self.queue
        if path=="/interrupt": return {}
        return self.history
    def close(self): pass
@pytest.fixture
def engine(tmp_path): return DevelopmentGeneration(Fake(),tmp_path)

def test_manifest_and_defaults(wan):
    s=CreativeRequest(prompt="Ocean",seed=1).resolve(wan)
    assert (s["frames"],s["width"],s["height"],s["steps"],s["fps"])==(17,320,192,8,16)
    for c in load_capabilities(PROJECT_ROOT/"model_registry/capabilities"): assert Capability.model_validate(c.model_dump())==c
@pytest.mark.parametrize("change",[{"workspace":"magic"},{"default_resolution":"bad"},{"durations":[{"seconds":1,"frames":18}]},{"qualities":{"Fast":999}},{"unknown":True}])
def test_invalid_manifest(wan,change):
    raw=wan.model_dump()
    if "workspace" in change: raw["workspaces"]=[change["workspace"]]
    else: raw.update(change)
    with pytest.raises(ValidationError): Capability.model_validate(raw)
@pytest.mark.parametrize("change",[{"workspace":"image-to-video"},{"resolution":"1080p"},{"duration":3},{"quality":"Ultra"},{"export_fps":60},{"prompt":" "}])
def test_invalid_combinations(wan,change):
    with pytest.raises(ValueError): CreativeRequest(**{"prompt":"Ocean",**change}).resolve(wan)
@pytest.mark.parametrize("change",[{"width":1024},{"workflow":{}},{"seed":True},{"duration":True},{"steps":100},{"cfg":100}])
def test_request_protection(change):
    with pytest.raises(ValidationError): CreativeRequest(**{"prompt":"Ocean",**change})
def test_duration_resolution_quality_seed_camera(wan):
    value=CreativeRequest(prompt="Ocean",duration=4,resolution="portrait",quality="High",seed=55,camera="pan-left").resolve(wan)
    assert (value["frames"],value["width"],value["height"],value["steps"],value["seed"])==(65,288,512,24,55)
    assert value["prompt"].endswith("Slow camera pan left.")
    assert len({CreativeRequest(prompt="Ocean").resolve(wan)["seed"] for _ in range(10)})==10
    assert CreativeRequest(prompt="Ocean",seed=0).resolve(wan)["seed"]==0

def test_fixed_adapter_settings_protection(wan,engine):
    body=CreativeRequest(prompt="Ocean",seed=10,resolution="square",duration=2,quality="Balanced",camera="push-in")
    settings=body.resolve(wan)
    job=engine.start(GenerationRequest(prompt=settings["prompt"],seed=10),settings=settings,creative=body.model_dump())
    workflow=engine.client.calls[-1][1]["prompt"]
    assert workflow["40"]["inputs"]=={"width":384,"height":384,"length":33,"batch_size":1}
    assert workflow["3"]["inputs"]["steps"]==16
    assert job.creative["prompt"]=="Ocean"
    assert workflow["37"]["inputs"]["unet_name"]=="wan2.1_t2v_1.3B_fp16.safetensors"
    engine.jobs.clear()
    with pytest.raises(ValueError): engine.start(GenerationRequest(prompt=settings["prompt"],seed=10),settings={**settings,"width":999},creative=body.model_dump())
def test_pending_and_running_cancellation(engine):
    j=engine.start(GenerationRequest(prompt="Ocean")); engine.client.queue["queue_pending"]=[[0,PID]]
    assert engine.cancel(j.id).state=="cancelled"
    j=engine.start(GenerationRequest(prompt="Ocean")); engine.client.queue["queue_running"]=[[0,PID]]
    assert engine.cancel(j.id).state=="running" # Not prematurely reported stopped
    engine.client.history={PID:{"status":{"status_str":"error","messages":[["execution_interrupted",{}]]}}}
    assert engine.get(j.id).state=="cancelled"
def test_cancellation_preserves_other_work(engine):
    j=engine.start(GenerationRequest(prompt="Ocean")); engine.client.queue["queue_running"]=[[0,"other"]]
    with pytest.raises(ManagerError): engine.cancel(j.id)
    assert not any(p=="/interrupt" for p,_ in engine.client.calls)
def test_history_no_active_forget(engine):
    j=engine.start(GenerationRequest(prompt="Ocean"))
    with pytest.raises(ManagerError): engine.forget(j.id)
    engine.jobs[j.id].state="failed"; engine.forget(j.id)
    assert not engine.jobs

def inventory(tmp_path):
    marker=tmp_path/"owner.json"; marker.write_text("owned")
    root=tmp_path/"models";root.mkdir()
    def item(name,models,kind="model"):
        path=root/name;path.write_bytes(name.encode())
        return Asset(path=name,size=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),models=models,kind=kind)
    assets=[item("diffusion.bin",["wan"]),item("encoder.bin",["wan","next"]),item("unused.bin",[],"cache")]
    (root/"unrelated.bin").write_text("user owned")
    return AssetInventory(root,assets,marker)
def test_removal_shared_media_and_unrelated_preserved(tmp_path):
    store=inventory(tmp_path); video=tmp_path/"video.mp4";video.write_text("user media")
    plan=store.plan("wan"); assert plan["files"]==["diffusion.bin"] and plan["shared_files"]==["encoder.bin"]
    with pytest.raises(ValueError): store.remove("wan",plan["digest"],False)
    result=store.remove("wan",plan["digest"],True)
    assert result["reclaimed_bytes"]==len("diffusion.bin")
    assert not (store.root/"diffusion.bin").exists()
    assert (store.root/"encoder.bin").exists() and store.assets[0].models==["next"]
    assert (store.root/"unrelated.bin").read_text()=="user owned" and video.read_text()=="user media"
def test_changed_hash_and_digest_block_removal(tmp_path):
    store=inventory(tmp_path);plan=store.plan("wan")
    (store.root/"diffusion.bin").write_bytes(b"X"*len("diffusion.bin"))
    with pytest.raises(ValueError): store.remove("wan",plan["digest"],True)
    assert (store.root/"encoder.bin").exists()
def test_cache_only_unreferenced_registered_files(tmp_path):
    store=inventory(tmp_path);plan=store.cleanup_plan()
    assert plan["files"]==["unused.bin"]
    store.cleanup(plan["digest"],True)
    assert not (store.root/"unused.bin").exists() and (store.root/"encoder.bin").exists() and (store.root/"unrelated.bin").exists()
@pytest.mark.parametrize("path",["../escape","C:/x","/abs","a\\b","a//b","a/./b","a/../../b"])
def test_unsafe_asset_paths(path):
    with pytest.raises(ValidationError): Asset(path=path,size=1,sha256="a"*64,models=["wan"])
def test_duplicate_asset_destinations(tmp_path):
    asset=Asset(path="A.bin",size=1,sha256="a"*64,models=["one"])
    with pytest.raises(ValueError): AssetInventory(tmp_path,[asset,asset.model_copy(update={"path":"a.bin"})],tmp_path/"owner")
def test_removal_rename_failure_rolls_back(tmp_path,monkeypatch):
    store=inventory(tmp_path);extra=Asset(path="second.bin",size=1,sha256=hashlib.sha256(b"s").hexdigest(),models=["wan"])
    (store.root/extra.path).write_bytes(b"s");store.assets.append(extra)
    original=Path.rename
    def rename(path,target):
        if path.name=="second.bin": raise OSError("fixture failure")
        return original(path,target)
    monkeypatch.setattr(Path,"rename",rename)
    with pytest.raises(OSError): store.remove("wan",store.plan("wan")["digest"],True)
    assert (store.root/"diffusion.bin").exists()
def test_size_inventory(tmp_path):
    (tmp_path/"file").write_bytes(b"123")
    assert directory_size(tmp_path)["bytes"]==3
    assert directory_size(tmp_path,limit=0)["complete"] is False

def test_discovery_offline_no_fake_success():
    fetch=Mock(return_value=[{"id":"a/model","sha":"a"*40,"cardData":{"license":"<script>"},"pipeline_tag":"text-to-video"}])
    discovery=Discovery(fetch);data=discovery.search("video")
    assert data["items"][0]["status"]=="discovered_not_runnable" and not data["cached"]
    fetch.side_effect=ValueError("offline")
    assert discovery.search("video")["cached"]
    with pytest.raises(ManagerError): discovery.search("uncached")
def test_discovery_never_follows_untrusted_repository_urls():
    discovery=Discovery(Mock(return_value=[{"id":"../../escape"},{"id":"http://evil"}]))
    assert discovery.search("video")["items"]==[]
    with pytest.raises(ManagerError): discovery.details("../escape")
def test_card_plain_text_pinned():
    fetch=Mock(side_effect=[{"sha":"a"*40},{"sha":"a"*40},"<script>bad()</script>"])
    result=Discovery(fetch).details("a/model")
    assert result["runnable"] is False and result["card_text"]=="<script>bad()</script>"
    assert fetch.call_args_list[-1].args[0].endswith("/"+"a"*40+"/README.md")

def test_card_inventory_is_pinned_metadata_and_offline_cached():
    metadata={"sha":"a"*40,"siblings":[{"rfilename":"weights.safetensors","size":4,"lfs":{"sha256":"b"*64}}],
              "tags":["video"],"cardData":{"license":"apache-2.0"}}
    fetch=Mock(side_effect=[{"sha":"a"*40},metadata,"Published card",ValueError("offline")])
    discovery=Discovery(fetch)
    card=discovery.details("a/model")
    assert card["repository_bytes"]==4 and card["files"][0]["sha256"]=="b"*64
    assert fetch.call_args_list[1].args[0].endswith("/revision/"+"a"*40)
    assert card["runnable"] is False
    cached=discovery.details("a/model")
    assert cached["cached"] is True and cached["revision"]==card["revision"]

def test_card_unknown_file_size_not_invented():
    fetch=Mock(side_effect=[{"sha":"a"*40},{"sha":"a"*40,"siblings":[{"rfilename":"model"}]},"card"])
    card=Discovery(fetch).details("a/model")
    assert card["repository_bytes"] is None and card["files"][0]["size"] is None

@pytest.mark.parametrize("pinned",[
    {"sha":"b"*40},
    {"sha":"a"*40,"siblings":[{"rfilename":"model","size":-1}]},
    {"sha":"a"*40,"siblings":[{"rfilename":"model","lfs":{"sha256":"invented"}}]},
    {"sha":"a"*40,"siblings":[{"rfilename":"a"}]*1001},
])
def test_card_rejects_unverified_or_unbounded_inventory(pinned):
    with pytest.raises(ManagerError):
        Discovery(Mock(side_effect=[{"sha":"a"*40},pinned,"card"])).details("a/model")
def test_secret_redaction_and_bound():
    console=ActivityConsole([KEY]);console.add("generation",KEY+" token=abc hf_secret1234 Bearer secrettoken")
    text=json.dumps(console.read());assert KEY not in text and "secrettoken" not in text and "hf_secret1234" not in text
    for i in range(310): console.add("test",str(i))
    assert len(console.read()["events"])==300;console.clear();assert not console.read()["events"]
def test_sequence_and_audio_capability_gate(wan):
    Shot(id="shot1",prompt="Ocean").validate_for(wan)
    with pytest.raises(ValueError): Shot(id="shot2",prompt="Ocean",audio="native").validate_for(wan)
    with pytest.raises(ValueError): Shot(id="shot2",prompt="Ocean",continuation="reference",previous_job_id="a"*32).validate_for(wan)
    with pytest.raises(ValidationError): Shot(id="shot2",prompt="Ocean",previous_job_id="C:/video")

def test_product_api_security_jobs_discovery_and_gates(engine,tmp_path):
    app=create_app(model_root=tmp_path/"storage",runtime_root=tmp_path/"runtime",manager_key=KEY,development_generation=engine)
    with TestClient(app,base_url="http://127.0.0.1:8000") as client:
        for path in ["/api/product/models","/api/product/jobs","/api/product/console","/api/product/storage"]:
            assert client.get(path).status_code==403
            assert client.get(path,headers={"X-Director-Key":"wrong"}).status_code==403
            assert client.get(path,headers={"X-Director-Key":KEY,"Origin":"http://evil.test"}).status_code==403
        headers={"X-Director-Key":KEY}
        assert client.get("/api/product/models",headers=headers).json()["production_ready"] is False
        result=client.get("/api/product/jobs",headers=headers).json();assert result=={"jobs":[],"session_only":True}
        j=engine.start(GenerationRequest(prompt="Ocean"))
        result=client.get("/api/product/jobs",headers=headers).json();assert result["jobs"][0]["id"]==j.id
        assert result["jobs"][0]["progress"] is None
        assert client.post("/api/product/generation",headers=headers,json={"model_id":"minimax-h3","prompt":"x"}).status_code==409
        assert client.post("/api/product/generation",headers=headers,json={"prompt":"x","workflow":{}}).status_code==422
        assert client.post("/api/product/jobs/invalid/forget",headers=headers).status_code==404
        app.state.product.discovery=Discovery(Mock(return_value=[]))
        assert client.get("/api/product/discovery?q=video",headers=headers).json()["items"]==[]
        assert KEY not in json.dumps(client.get("/api/product/console",headers=headers).json())


def test_sequence_reference_ownership_and_audio_preservation(wan):
    from director.product.scene import SequencePlan, SceneOutput, AudioTrack
    plan=SequencePlan(model_id=wan.id,shots=[Shot(id="one",prompt="Ocean",previous_job_id="a"*32)])
    with pytest.raises(ValueError):plan.validate_for(wan,set())
    plan.validate_for(wan,{"a"*32})
    with pytest.raises(ValidationError):SequencePlan(model_id=wan.id,shots=[Shot(id="one",prompt="a"),Shot(id="one",prompt="b")])
    audio=AudioTrack(origin="native",present=True,codec="aac",sample_rate=32000,channels=2)
    with pytest.raises(ValidationError):SceneOutput(job_id="a"*32,width=320,height=192,frames=17,fps=16,audio=audio,decoded_video=True,decoded_audio=False,resolve_compatible=True)
    output=SceneOutput(job_id="a"*32,width=320,height=192,frames=17,fps=16,audio=audio,decoded_video=True,decoded_audio=True,resolve_compatible=True)
    assert output.audio.present
@pytest.mark.parametrize("change",[{"license_source":"javascript:bad()"},{"repository":"../bad"},{"required_assets":["../model"]},{"required_assets":[]}])
def test_catalog_source_and_allowlist_validation(wan,change):
    with pytest.raises(ValidationError):Capability.model_validate({**wan.model_dump(),**change})
def test_model_state_requires_complete_inventory(tmp_path,wan):
    from director.product.api import ProductServices
    services=ProductServices(PROJECT_ROOT,KEY,studio_root=tmp_path/"studio_data")
    store=inventory(tmp_path)
    # Even a valid owned file alone cannot mark the full Wan adapter installed.
    store.assets[0].models=[wan.id]
    services.assets=store
    assert not next(m for m in services.catalog(True)["models"] if m["id"]==wan.id)["runnable"]
def test_product_successful_submission_and_dynamic_api(engine,tmp_path,wan):
    app=create_app(model_root=tmp_path/"storage",runtime_root=tmp_path/"runtime",manager_key=KEY,development_generation=engine)
    with TestClient(app,base_url="http://127.0.0.1:8000") as client:
        owner=tmp_path/"owned.json";owner.write_text("owned");assets=[]
        for filename in wan.required_assets:
            f=tmp_path/"models"/filename;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b"tiny")
            assets.append(Asset(path=filename,size=4,sha256=hashlib.sha256(b"tiny").hexdigest(),models=[wan.id]))
        app.state.product.assets=AssetInventory(tmp_path/"models",assets,owner)
        h={"X-Director-Key":KEY}
        response=client.post("/api/product/generation",headers=h,json={"prompt":"Ocean","seed":9,"duration":2,"resolution":"portrait"})
        assert response.status_code==202
        assert response.json()["creative"]["frames"]==33
        assert engine.client.calls[-1][1]["prompt"]["40"]["inputs"]["width"]==288
        assert client.get("/api/product/jobs",headers=h).json()["jobs"][0]["id"]==response.json()["id"]


@pytest.mark.parametrize("path",["CON","nul.bin","folder/lpt1.dll","trailing.","folder./file.bin"])
def test_asset_windows_device_names_and_aliases(path):
    with pytest.raises(ValidationError):Asset(path=path,size=1,sha256="a"*64,models=["wan"])
def test_linked_inventory_blocks_removal(tmp_path,monkeypatch):
    store=inventory(tmp_path)
    def reject(path):raise ValueError("synthetic reparse escape")
    monkeypatch.setattr("director.product.assets.assert_no_links",reject)
    assert store.plan("wan")["blockers"]
    assert (store.root/"diffusion.bin").exists()
