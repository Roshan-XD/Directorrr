"""Small owned-media/data fixtures only; no network, model weights or inference."""
import hashlib
import threading
from unittest.mock import Mock
import pytest
import httpx
from pydantic import ValidationError
from fastapi.testclient import TestClient
from director.product.studio import StudioStore, Project
from director.product.downloads import DownloadManager, Selection, StartDownload
from director.product.discovery import Discovery
from director.product.adapters import classify, family
from director.product.capabilities import load_capabilities
from director.installations.downloader import FixtureDownloader
from director.installations.schemas import ManagerError
from director.main import create_app,PROJECT_ROOT

KEY="studio-manager-key-"*3
REV="a"*40
PAYLOAD=b"small inert fixture"
def probe(path,thumbnail):
    thumbnail.write_bytes(b"fixture thumbnail")
    return {"width":320,"height":192,"duration":1.0625,"codec":"fixture","thumbnail":True}
@pytest.fixture
def store(tmp_path):
    value=StudioStore(tmp_path/"studio",tmp_path,probe=probe)
    yield value
    value.close()

def test_asset_metadata_persistence_and_original_preservation(store):
    asset=store.add(PAYLOAD,"scene.webm")
    assert asset.bytes==len(PAYLOAD) and asset.sha256==hashlib.sha256(PAYLOAD).hexdigest()
    assert store.path(asset.id).read_bytes()==PAYLOAD
    store.edit(asset.id,title="Sunset",favorite=True)
    root=store.storage.root; project_root=store.root;store.close()
    reopened=StudioStore(root,project_root,probe=probe)
    assert reopened.media(asset.id).title=="Sunset" and reopened.media(asset.id).favorite
    with pytest.raises(ManagerError):reopened.delete(asset.id,False)
    assert reopened.delete(asset.id,True)["original_generation_preserved"]
    reopened.close()

@pytest.mark.parametrize("filename",["../scene.webm","C:scene.mp4","bad.exe","scene\\bad.png","x\x00.jpg"])
def test_invalid_media_paths(store,filename):
    with pytest.raises(ManagerError): store.add(PAYLOAD,filename)
    assert not store.snapshot()["media"]

def test_probe_failure_cleans_only_new_files(store):
    store.probe=Mock(side_effect=ManagerError("invalid_media","Cannot decode",422))
    with pytest.raises(ManagerError):store.add(PAYLOAD,"invalid.png")
    assert not store.snapshot()["media"]
    assert not list(store.storage.path("media").iterdir())

def test_corruption_and_unknown_files_block_deletion(store):
    asset=store.add(PAYLOAD,"scene.webm");path=store.path(asset.id)
    path.write_bytes(b"x"*len(PAYLOAD))
    with pytest.raises(ManagerError):store.delete(asset.id,True)
    path.write_bytes(PAYLOAD);(path.parent/"user.txt").write_text("preserve")
    with pytest.raises(ManagerError):store.delete(asset.id,True)
    assert path.exists()

def test_project_reference_protection_and_autosave(store):
    asset=store.add(PAYLOAD,"reference.png")
    project=Project(id="b"*32,name="Storyboard",draft={"prompt":"Ocean"},references=[asset.id])
    store.save_project(project)
    assert store.snapshot()["current"]==project.id
    with pytest.raises(ManagerError):store.delete(asset.id,True)
    with pytest.raises(ManagerError):store.save_project(Project(id="c"*32,references=["f"*32]))
    assert store.storage.path("studio.previous.json").is_file()

def test_project_no_credentials_or_unbounded_settings():
    with pytest.raises(ValidationError):Project(id="a"*32,draft={"manager_key":"secret"})
    with pytest.raises(ValidationError):Project(id="a"*32,presets=[{"name":"x","settings":{"command":"execute"}}])

def catalog():
    return {"repository":"example/fixture","revision":REV,"files":[{"name":"sample.bin","size":len(PAYLOAD),"sha256":hashlib.sha256(PAYLOAD).hexdigest()},{"name":"LICENSE","size":5,"sha256":None}],"license":"apache-2.0","license_state":"known_permissive_declaration","gated":False,"cached":False}
def manager(tmp_path,transport=None,card=None):
    discovery=Mock();discovery.details.return_value=card or catalog();discovery.fetch.return_value="Apache License, Version 2.0 fixture"
    return DownloadManager(tmp_path/"data",discovery,transport)
def selection():return Selection(repository="example/fixture",files=["sample.bin"])
def confirmed(plan):return StartDownload(repository=plan["repository"],files=["sample.bin"],digest=plan["digest"],confirmed=True,accepted_license=True)
def test_download_plan_default_disabled(tmp_path):
    manager_=manager(tmp_path);plan=manager_.plan(selection())
    assert plan["total_bytes"]==len(PAYLOAD) and plan["runnable"] is False
    assert any("disabled" in b for b in plan["blockers"])
    with pytest.raises(ManagerError):manager_.start(confirmed(plan))
    assert not manager_.jobs
    manager_.close()
def test_successful_persistent_data_download(tmp_path):
    transport=FixtureDownloader({("example/fixture",REV,"sample.bin"):PAYLOAD})
    value=manager(tmp_path,transport);plan=value.plan(selection())
    job=value.start(confirmed(plan));value.threads[-1].join(5)
    assert value.jobs[job["id"]]["state"]=="completed"
    assert value.jobs[job["id"]]["verified_bytes"]==len(PAYLOAD)
    assert value.jobs[job["id"]]["runnable"] is False
    value.close();reopened=manager(tmp_path,transport)
    assert reopened.jobs[job["id"]]["state"]=="completed";reopened.close()
@pytest.mark.parametrize("change",[{"gated":True},{"cached":True},{"license_state":"unknown"},{"files":[{"name":"sample.bin","size":None,"sha256":None}]}])
def test_missing_license_gated_offline_integrity_metadata(tmp_path,change):
    value=manager(tmp_path,FixtureDownloader({}),{**catalog(),**change});plan=value.plan(selection())
    assert plan["blockers"]
    with pytest.raises(ManagerError):value.start(confirmed(plan))
    value.close()
def test_missing_license_document(tmp_path):
    value=manager(tmp_path,FixtureDownloader({}));value.discovery.fetch.side_effect=ValueError("unavailable")
    assert any("license text" in b for b in value.plan(selection())["blockers"]);value.close()
def test_duplicate_and_unsafe_selection(tmp_path):
    value=manager(tmp_path)
    with pytest.raises(ManagerError):value.plan(Selection(repository="example/fixture",files=["sample.bin"]*2))
    value.discovery.details.return_value={**catalog(),"files":[{"name":"../sample.bin","size":1,"sha256":"a"*64}]}
    with pytest.raises(ManagerError):value.plan(Selection(repository="example/fixture",files=["../sample.bin"]))
    value.close()
def test_download_failure_and_cancellation(tmp_path):
    class Blocked:
        is_real=False
        def fetch(self,component,cache,cancel,progress,allowlist):
            cancel.wait(2)
            from director.installations.schemas import Cancelled
            raise Cancelled()
    value=manager(tmp_path,Blocked());job=value.start(confirmed(value.plan(selection())))
    with pytest.raises(ManagerError):value.start(confirmed(value.plan(selection())))
    value.cancel(job["id"]);value.threads[-1].join(5)
    assert value.jobs[job["id"]]["state"]=="cancelled";value.close()
def test_integrity_failure_never_ready(tmp_path):
    value=manager(tmp_path,FixtureDownloader({("example/fixture",REV,"sample.bin"):b"bad"}))
    job=value.start(confirmed(value.plan(selection())));value.threads[-1].join(5)
    assert value.jobs[job["id"]]["state"]=="failed" and not value.jobs[job["id"]]["runnable"];value.close()
def test_discovery_filters_pagination_offline():
    value=Discovery()
    calls=[]
    def fetch(path,params):
        calls.append(params);value.next_link="https://huggingface.co/api/models?cursor=abc"
        return [{"id":"arbitrary/new-model","sha":REV,"cardData":{"license":"mit"},"gated":"auto"}]
    value.fetch=fetch
    first=value.search("new",author="arbitrary",task="text-to-image",sort="likes")
    assert first["next_cursor"] and first["items"][0]["gated"]
    value.search("new",author="arbitrary",task="text-to-image",sort="likes",cursor=first["next_cursor"])
    assert calls[-1]["cursor"]=="abc" and calls[-1]["pipeline_tag"]=="text-to-image"
    with pytest.raises(ManagerError):value.search("different",cursor=first["next_cursor"])
    value.fetch=Mock(side_effect=httpx.ConnectError("offline"))
    assert value.search("new",author="arbitrary",task="text-to-image",sort="likes")["cached"]
def test_no_unreviewed_family_matches():
    cap=next(c for c in load_capabilities(PROJECT_ROOT/"model_registry/capabilities") if c.adapter=="wan-native-v1")
    assert family(cap).workflow=="wan-stage7-native-v1"
    assert classify("arbitrary/Wan-lookalike",{"models":[]})["state"]=="adapter_required"
def test_studio_and_download_api_authentication(tmp_path):
    app=create_app(model_root=tmp_path/"models",runtime_root=tmp_path/"runtime",manager_key=KEY)
    with TestClient(app,base_url="http://127.0.0.1:8000") as client:
        h={"X-Director-Key":KEY}
        for path in ["/api/product/studio","/api/product/downloads","/api/product/adapters"]:
            assert client.get(path).status_code==403
            assert client.get(path,headers={**h,"Origin":"http://evil.test"}).status_code==403
            assert client.get(path,headers=h).status_code==200
        app.state.product.studio.probe=probe
        response=client.post("/api/product/library/upload?filename=scene.webm",headers=h,content=PAYLOAD)
        assert response.status_code==201;asset=response.json()
        assert client.get(f"/api/product/library/{asset['id']}/file",headers=h).content==PAYLOAD
        assert client.get(f"/api/product/library/{asset['id']}/handoffs",headers=h).json()["actions"]==[]
        assert client.post(f"/api/product/library/{asset['id']}/delete",headers=h,json={"confirmed":False}).status_code==422
        assert client.get("/api/product/library/../../file",headers=h).status_code in {404,422}

def test_download_removal_preserves_unrelated_data(tmp_path):
    value=manager(tmp_path,FixtureDownloader({("example/fixture",REV,"sample.bin"):PAYLOAD}))
    job=value.start(confirmed(value.plan(selection())));value.threads[-1].join(5)
    folder=value.storage.path("downloads",job["id"]);extra=folder/"user.txt";extra.write_text("preserve")
    with pytest.raises(ManagerError):value.removal_plan(job["id"])
    extra.unlink();plan=value.removal_plan(job["id"])
    with pytest.raises(ManagerError):value.remove(job["id"],"f"*64)
    assert value.remove(job["id"],plan["digest"])["reclaimed_bytes"]==len(PAYLOAD)
    assert value.storage.path("cache",job["id"]).is_dir();value.close()

def test_interrupted_download_recovery(tmp_path):
    value=manager(tmp_path,FixtureDownloader({}));value.jobs={"a"*32:{"id":"a"*32,"state":"downloading","message":"old"}};value._save();value.close()
    reopened=manager(tmp_path,FixtureDownloader({}));assert reopened.jobs["a"*32]["state"]=="failed";assert "Interrupted" in reopened.jobs["a"*32]["message"];reopened.close()

def test_download_disk_preflight_blocks_before_transfer(tmp_path,monkeypatch):
    value=manager(tmp_path,FixtureDownloader({}));monkeypatch.setattr(value.storage,"check_space",Mock(side_effect=ManagerError("insufficient_space","Not enough disk",409)))
    with pytest.raises(ManagerError):value.start(confirmed(value.plan(selection())))
    assert not value.jobs;value.close()

def test_discovery_cache_survives_restart(store):
    value=Discovery(Mock(return_value=[{"id":"new/publisher","sha":REV}]))
    value.attach_cache(store.storage);value.search("publisher")
    reopened=Discovery(Mock(side_effect=httpx.ConnectError("offline")));reopened.attach_cache(store.storage)
    assert reopened.search("publisher")["cached"]

def test_model_tools_no_mutation_and_unknown_ids(tmp_path):
    app=create_app(model_root=tmp_path/"models",runtime_root=tmp_path/"runtime",manager_key=KEY)
    with TestClient(app,base_url="http://127.0.0.1:8000") as client:
        h={"X-Director-Key":KEY}
        assert client.get("/api/product/models/unknown/files",headers=h).status_code==404
        files=client.get("/api/product/models/wan21-t2v-13b/files",headers=h)
        assert files.status_code==200 and "Metadata presence only" in files.json()["integrity"]
        assert client.post("/api/product/models/minimax-h3/verify",headers=h).status_code==409

def test_console_collapses_identical_events():
    from director.product.console import ActivityConsole
    value=ActivityConsole([KEY]);value.add("download",KEY);value.add("download",KEY)
    assert len(value.read()["events"])==1 and value.read()["events"][0]["count"]==2
    assert KEY not in str(value.read())

def test_completed_output_stays_with_originating_project(store):
    from director.generation.service import GenerationJob
    job=GenerationJob(id="d"*32,state="queued",message="queued")
    store.record_job(job)
    original=store.state["current"]
    store.save_project(Project(id="b"*32,name="Other project"))
    store.record_job(job.model_copy(update={"state":"completed"}),("scene.webm",PAYLOAD))
    assert store.state["media"][0]["project_id"]==original
    assert store.state["history"][0]["project_id"]==original
