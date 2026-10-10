"""Additive development product APIs. Existing installer/security contracts remain intact."""
import json
import os
import shutil
import threading
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from pydantic import Field
from director.installations.api import require_manager_key
from director.installations.schemas import ManagerError
from director.installations.verifier import assert_no_links
from director.generation.service import GenerationRequest
from director.product.capabilities import CreativeRequest, StrictModel, load_capabilities
from director.product.assets import Asset, AssetInventory, directory_size
from director.product.console import ActivityConsole
from director.product.discovery import Discovery
from director.product.studio import StudioStore
from director.product.downloads import DownloadManager
from director.product.optimized_h3 import OptimizedH3Downloads, registered_assets, recipe, MODEL_ID

class RemovalRequest(StrictModel):
    confirmed: bool
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")

class ProductServices:
    def __init__(self,root,key,studio_root=None):
        self.root=root
        self.capabilities=load_capabilities(root/"model_registry/capabilities")
        self.console=ActivityConsole([key]); self.discovery=Discovery()
        self.lock=threading.RLock()
        self.native=root/"runtime/windows-dev-001"
        self.assets=self._assets()
        self.storage_cache=None
        self.studio=StudioStore(studio_root or root/"studio_data",root)
        self.discovery.attach_cache(self.studio.storage)
        self.downloads=OptimizedH3Downloads((studio_root or root/"studio_data").parent/"repository_data",self.discovery,
                                          root,self.native,self.refresh_assets,events=self.console.add)
        self.console.add("session","Product workspace connected. Production provisioning remains disabled.")
    def _assets(self):
        manifest=json.loads(next((self.root/"model_registry").glob("wan*.json")).read_text())
        assets=[Asset(path=c["destination"],size=c["expected_size_bytes"],sha256=c["sha256"],models=["wan21-t2v-13b"])
                for c in manifest["components"]]
        # Only the Stage 12 ownership marker and signed-off copy receipt register native model assets.
        marker=self.native/"owner.json"; receipt=self.native/"receipts/model-copies.json"
        try:
            assert_no_links(marker); assert_no_links(receipt)
            if marker.stat().st_size>4096 or receipt.stat().st_size>16384: raise ValueError("Oversized receipt")
            if json.loads(marker.read_text()).get("owner")!="Director Stage 12 private development": raise ValueError("Ownership mismatch")
            records=json.loads(receipt.read_text())
            for asset in assets:
                expected=self.native/"models"/asset.path
                if not any(Path(r["file"])==expected and r["bytes"]==asset.size and r["sha256"]==asset.sha256 for r in records):
                    raise ValueError("Unregistered native asset")
        except (OSError,ValueError,KeyError,TypeError): assets=[]
        assets.extend(registered_assets(self.root,self.native))
        inventory=AssetInventory(self.native/"models",assets,marker)
        state=self.native/"receipts/product-assets.json"
        if state.exists():
            assert_no_links(state)
            if state.stat().st_size>32768: raise ValueError("Oversized asset state")
            retained=[Asset.model_validate(a) for a in json.loads(state.read_text())]
            # Persisted references cannot introduce new files or alter reviewed integrity/ownership.
            for asset in retained:
                reviewed_h3 = [(c["destination"], c["expected_size_bytes"], c["sha256"]) for c in recipe(self.root)["components"]] if asset.models == [MODEL_ID] else []
                if (asset.path,asset.size,asset.sha256) not in reviewed_h3 and not any((a.path,a.size,a.sha256)==(asset.path,asset.size,asset.sha256) for a in assets):
                    raise ValueError("Unreviewed asset registration")
            retained.extend(a for a in assets if MODEL_ID in a.models and not any(a.path==v.path for v in retained))
            inventory=AssetInventory(self.native/"models",retained,marker)
        return inventory
    def refresh_assets(self):
        with self.lock:
            self.assets=self._assets()
            self.storage_cache=None
    def save_assets(self):
        path=self.native/"receipts/product-assets.json"; temporary=path.with_suffix(".pending")
        assert_no_links(path); assert_no_links(temporary)
        if temporary.exists(): raise ValueError("Interrupted inventory update requires inspection")
        with temporary.open("x",encoding="utf-8") as stream:
            json.dump([a.model_dump() for a in self.assets.assets],stream); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,path)
    def catalog(self,enabled):
        values=[]
        for c in self.capabilities:
            assets=[a for a in self.assets.assets if c.id in a.models]
            installed=bool(c.required_assets) and {a.path for a in assets}==set(c.required_assets) and all(self.assets.available(a) for a in assets)
            values.append({**c.model_dump(),"installed":installed,
                 "runnable":c.adapter in {"wan-native-v1","minimax-h3-native-v1"} and installed and enabled and (c.id != MODEL_ID or bool(registered_assets(self.root,self.native))),
                 "model_bytes":sum(a.size for a in assets),
                 "installation_status":"installed_development" if installed else "not_installed",
                 "compatibility":"experimental_nvfp4_offload" if c.id==MODEL_ID else "validated_baseline" if installed and c.adapter else "unknown"})
        return {"models":values,"production_ready":False}

def product_router(root: Path):
    router=APIRouter(prefix="/api/product",dependencies=[Depends(require_manager_key)])
    def services(request: Request): return request.app.state.product
    def generation(request: Request):
        service=request.app.state.development_generation
        if service is None: raise ManagerError("generation_disabled","Development generation is disabled",404)
        return service
    @router.get("/models")
    def catalog(request: Request, service=Depends(services)):
        return service.catalog(request.app.state.development_generation is not None)
    @router.post("/generation",status_code=202)
    def generate(body:CreativeRequest, request:Request, service=Depends(services), engine=Depends(generation)):
        c=next((c for c in service.capabilities if c.id==body.model_id),None)
        if not c: raise ManagerError("model_not_found","Model not found",404)
        with service.lock:
            if not next(item for item in service.catalog(True)["models"] if item["id"]==c.id)["runnable"]:
                raise ManagerError("model_unavailable","Install and validate an approved Director adapter first",409)
            try: settings=body.resolve(c)
            except ValueError as exc: raise ManagerError("unsupported_settings",str(exc),422) from exc
            request_data=body.model_dump(); request_data["seed"]=settings["seed"]
            job=engine.start(GenerationRequest(prompt=settings["prompt"],seed=settings["seed"]),settings=settings,creative=request_data)
            service.studio.record_job(job)
            service.console.add("generation","Generation queued; native settings validated.")
            return job
    @router.get("/jobs")
    def jobs(service=Depends(services),engine=Depends(generation)):
        items=[]
        # The adapter owns a bounded 12-job session history. No automatic restart/retry.
        with engine._lock:
            for job_id in reversed(list(engine.jobs)):
                try:
                    old=engine.jobs[job_id].state; job=engine.get(job_id)
                    if old!=job.state: service.console.add("generation","Job state: "+job.state)
                    items.append(job.model_dump())
                    try:
                        needs_copy=job.state=="completed" and not any(a.get("job_id")==job.id for a in service.studio.state["media"])
                        service.studio.record_job(job,engine.output(job.id) if needs_copy else None)
                    except (ManagerError,OSError,ValueError):
                        service.console.add("library","Output registration needs attention; the original video is preserved.","warning")
                except ManagerError:
                    items.append({**engine.jobs[job_id].model_dump(),"tracking_warning":"ComfyUI is unavailable; last observed state retained."})
        return {"jobs":items,"session_only":True}
    @router.post("/jobs/{job_id}/cancel")
    def cancel(job_id:str,service=Depends(services),engine=Depends(generation)):
        job=engine.cancel(job_id); service.console.add("generation",job.message); return job
    @router.post("/jobs/{job_id}/forget")
    def forget(job_id:str,engine=Depends(generation)):
        engine.forget(job_id); return {"forgotten":True,"output_deleted":False}
    @router.get("/discovery")
    def discover(q:str="",author:str="",task:str="",sort:str="downloads",cursor:str|None=None,service=Depends(services)):
        return service.discovery.search(q,author=author,task=task,sort=sort,cursor=cursor)
    @router.get("/discovery/details")
    def discovery_details(repository:str,service=Depends(services)): return service.discovery.details(repository)
    @router.get("/storage")
    def storage(service=Depends(services)):
        import time
        if service.storage_cache and time.monotonic()-service.storage_cache[0]<60: return service.storage_cache[1]
        categories={name:directory_size(path) for name,path in {
            "models":service.native/"models", "python":service.native/"python", "packages":service.native/"venv",
            "comfyui":service.native/"ComfyUI", "generated_videos":root/"generated_videos",
            "native_outputs":service.native/"data/output", "cache":service.native/"cache",
            "temporary":service.native/"data/temp", "library":service.studio.storage.root,
            "repository_downloads":service.downloads.storage.root}.items()}
        free=shutil.disk_usage(root).free
        result={"categories":categories,"free_bytes":free,"low_disk":free<10*1024**3,
                "cleanup_policy":"Only reviewed owned assets can be removed. Unknown cache/orphan files require review.",
                "cache_cleanup_enabled":False,"unknown_files_are_not_deletion_targets":True}
        service.storage_cache=(time.monotonic(),result); return result
    @router.get("/models/{model_id}/removal-plan")
    def removal_plan(model_id:str,service=Depends(services)):
        try: return service.assets.plan(model_id)
        except ValueError as exc: raise ManagerError("removal_blocked",str(exc),409) from exc
    @router.post("/models/{model_id}/remove")
    def remove(model_id:str,body:RemovalRequest,service=Depends(services),engine=Depends(generation)):
        with service.lock,engine._lock:
            if any(j.state in {"queued","running"} for j in engine.jobs.values()):
                raise ManagerError("generation_active","Wait for all generation work to stop before removing assets",409)
            queue=engine._queue()
            if queue["queue_running"] or queue["queue_pending"]:
                raise ManagerError("comfy_busy","ComfyUI has active work",409)
            try:
                result=service.assets.remove(model_id,body.digest,body.confirmed); service.save_assets()
            except (ValueError,OSError) as exc:
                raise ManagerError("removal_blocked","Removal blocked by ownership, integrity or filesystem checks. Inspect the asset inventory.",409) from exc
            service.storage_cache=None; service.console.add("storage","Explicit model removal finished; user media preserved.")
            return result
    @router.get("/cache/removal-plan")
    def cache_plan(service=Depends(services)): return service.assets.cleanup_plan()
    @router.post("/cache/remove")
    def cache_remove(body:RemovalRequest,service=Depends(services),engine=Depends(generation)):
        with service.lock,engine._lock:
            if any(j.state in {"queued","running"} for j in engine.jobs.values()):
                raise ManagerError("generation_active","Wait for active work before cache removal",409)
            try:
                result=service.assets.cleanup(body.digest,body.confirmed);service.save_assets()
            except (ValueError,OSError) as exc: raise ManagerError("cleanup_blocked","Cache review or ownership changed",409) from exc
            service.storage_cache=None;return result
    @router.get("/installation-jobs")
    def installation_jobs(request:Request):
        manager=request.app.state.installations
        with manager._mutex:
            return {"jobs":[job.model_dump(mode="json") for job in list(manager._jobs.values())[-12:]],"session_only":False}
    @router.get("/console")
    def console(service=Depends(services)): return service.console.read()
    @router.post("/console/clear")
    def clear(service=Depends(services)): service.console.clear(); return {"cleared":True}
    return router
