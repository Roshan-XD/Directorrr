import re
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from pydantic import Field
from director.installations.api import require_manager_key
from director.installations.schemas import ManagerError
from director.installations.verifier import assert_no_links
from director.product.capabilities import StrictModel
from director.product.studio import Project, MAX_MEDIA, MEDIA_TYPES
from director.product.downloads import Selection, StartDownload
from director.product.adapters import family, classify
class RemoveDownload(StrictModel):
    confirmed: bool
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")

class AssetEdit(StrictModel):
    title: str | None = Field(default=None,min_length=1,max_length=160)
    favorite: bool | None = None
class DeleteAsset(StrictModel):
    confirmed: bool

def studio_router():
    router=APIRouter(prefix="/api/product",dependencies=[Depends(require_manager_key)])
    def store(request:Request): return request.app.state.product.studio
    @router.get("/adapters")
    def adapters(request:Request): return {"families":[family(c).model_dump() for c in request.app.state.product.capabilities]}
    @router.get("/discovery/compatibility")
    def compatibility(repository:str,request:Request):
        return classify(repository,request.app.state.product.catalog(request.app.state.development_generation is not None))
    @router.get("/downloads")
    def downloads(request:Request): return request.app.state.product.downloads.snapshot()
    @router.post("/downloads/plan")
    def plan(body:Selection,request:Request): return request.app.state.product.downloads.plan(body)
    @router.post("/downloads",status_code=202)
    def start(body:StartDownload,request:Request): return request.app.state.product.downloads.start(body)
    @router.post("/downloads/{job_id}/cancel")
    def cancel(job_id:str,request:Request): return request.app.state.product.downloads.cancel(job_id)
    @router.get("/downloads/{job_id}/removal-plan")
    def removal(job_id:str,request:Request):return request.app.state.product.downloads.removal_plan(job_id)
    @router.post("/downloads/{job_id}/remove")
    def remove(job_id:str,body:RemoveDownload,request:Request):
        if not body.confirmed:raise ManagerError("confirmation_required","Explicit confirmation required",422)
        return request.app.state.product.downloads.remove(job_id,body.digest)
    @router.get("/studio")
    def state(studio=Depends(store)): return studio.snapshot()
    @router.post("/studio/projects")
    def save(body:Project,studio=Depends(store)): return studio.save_project(body)
    @router.post("/library/upload",status_code=201)
    async def upload(request:Request,filename:str,studio=Depends(store)):
        size=request.headers.get("content-length")
        if size and (not size.isdigit() or int(size)>MAX_MEDIA):
            raise ManagerError("media_too_large","Media must be under 64 MiB",413)
        data=bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data)>MAX_MEDIA: raise ManagerError("media_too_large","Media must be under 64 MiB",413)
        # CPU decode/probing runs in the existing bounded private media process.
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(studio.add,bytes(data),filename)
    @router.get("/library/{asset_id}/file")
    def file(asset_id:str,thumbnail:bool=False,studio=Depends(store)):
        asset=studio.media(asset_id)
        return FileResponse(studio.path(asset_id,thumbnail),media_type="image/jpeg" if thumbnail else MEDIA_TYPES[asset.extension],
                            filename=None if thumbnail else asset.filename,headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"})
    @router.post("/library/{asset_id}/edit")
    def edit(asset_id:str,body:AssetEdit,studio=Depends(store)): return studio.edit(asset_id,**body.model_dump())
    @router.post("/library/{asset_id}/delete")
    def delete(asset_id:str,body:DeleteAsset,studio=Depends(store)): return studio.delete(asset_id,body.confirmed)
    @router.post("/library/{asset_id}/reveal")
    def reveal(asset_id:str,studio=Depends(store)):
        path=studio.path(asset_id)
        import os,subprocess
        if os.name!="nt": raise ManagerError("reveal_unavailable","Explorer reveal is Windows-only",409)
        explorer=Path(os.environ.get("SystemRoot",r"C:\Windows"))/"explorer.exe"
        subprocess.Popen([str(explorer),"/select,",str(path)],shell=False)
        return {"revealed":True}
    @router.get("/library/{asset_id}/handoffs")
    def handoffs(asset_id:str,request:Request,studio=Depends(store)):
        asset=studio.media(asset_id);catalog=request.app.state.product.catalog(request.app.state.development_generation is not None)
        modes={"image":{"image-to-video","reference-to-video","image-to-image","reference-image","inpainting"},
               "video":{"video-to-video"},"audio":{"audio-conditioned-video"}}[asset.type]
        return {"asset_id":asset_id,"actions":[{"model_id":m["id"],"model_name":m["name"],"workspace":mode}
                for m in catalog["models"] if m["runnable"] for mode in m["workspaces"] if mode in modes],
                "message":"Only installed, execution-enabled adapters are offered. Wan T2V cannot accept a reference."}
    @router.post("/library/import-outputs")
    def import_outputs(request:Request,studio=Depends(store)):
        engine=request.app.state.development_generation
        if engine is None: raise ManagerError("generation_disabled","No owned output directory configured",409)
        root=engine.output_root
        # Historical scanning is explicit and limited to the proven native output directory.
        native=request.app.state.product.native
        assert_no_links(native/"owner.json");assert_no_links(root)
        if not root.resolve().is_relative_to(native.resolve()) or not (native/"owner.json").is_file():
            raise ManagerError("unowned_output","Only Director-owned native output can be indexed",409)
        import json
        marker=native/"owner.json"
        if marker.stat().st_size>4096 or json.loads(marker.read_text()).get("owner")!="Director Stage 12 private development":
            raise ManagerError("unowned_output","Native ownership identity differs",409)
        from director.generation.service import GenerationJob
        count=0
        for path in list(root.glob("Director_Stage8_*.webm"))[:100]:
            match=re.fullmatch(r"Director_Stage8_([0-9a-f]{32})_[0-9]+_\.webm",path.name)
            if not match: continue
            if any(a.get("job_id")==match[1] for a in studio.state["media"]): continue
            assert_no_links(path)
            if not path.is_file() or path.stat().st_nlink!=1 or not 0<path.stat().st_size<=MAX_MEDIA: continue
            with path.open("rb") as stream:
                if stream.read(4)!=b"\x1aE\xdf\xa3": continue
            job=GenerationJob(id=match[1],state="completed",output_filename=path.name,message="Recovered owned output; original generation settings unknown")
            studio.record_job(job,path);count+=1
        return {"imported":count,"original_files_preserved":True}
    return router
