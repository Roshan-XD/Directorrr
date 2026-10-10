"""Explicit inspection of already registered native assets; no replacement/install."""
import json
import re
from fastapi import APIRouter, Depends, Request
from director.installations.api import require_manager_key
from director.installations.schemas import ManagerError
from director.installations.verifier import ArtifactVerifier, assert_no_links
from director.models.schemas import ModelManifest, ModelComponent

def model_tools_router():
    router=APIRouter(prefix="/api/product/models",dependencies=[Depends(require_manager_key)])
    def registered(request,model_id):
        product=request.app.state.product
        cap=next((c for c in product.capabilities if c.id==model_id),None)
        if not cap:raise ManagerError("model_not_found","Model not found",404)
        return product,cap
    @router.get("/{model_id}/files")
    def files(model_id:str,request:Request):
        product,cap=registered(request,model_id)
        assets=[a for a in product.assets.assets if model_id in a.models]
        return {"model_id":model_id,"location":"runtime/windows-dev-001/models (Director-owned)",
            "files":[{"path":a.path,"bytes":a.size,"sha256":a.sha256,"present":product.assets.available(a),"shared_with":[m for m in a.models if m!=model_id]} for a in assets],
            "expected_assets":cap.required_assets,"last_used":next((j.get("created") for j in product.studio.state["history"] if (j.get("creative") or {}).get("model_id")==model_id),None),
            "integrity":"Metadata presence only; use explicit verification for current hashes."}
    @router.post("/{model_id}/verify")
    def verify(model_id:str,request:Request):
        product,cap=registered(request,model_id)
        engine=request.app.state.development_generation
        if engine and any(j.state in {"queued","running"} for j in engine.jobs.values()):raise ManagerError("generation_active","Wait for generation before verifying large files",409)
        manifest=next((ModelManifest.model_validate_json(p.read_text()) for p in (product.root/"model_registry").glob("*.json") if json.loads(p.read_text()).get("id")== (cap.manifest_id or model_id)),None)
        if not manifest and model_id == "minimax-h3-optimized":
            from director.product.optimized_h3 import recipe
            from types import SimpleNamespace
            manifest=SimpleNamespace(components=[ModelComponent.model_validate(c) for c in recipe(product.root)["components"]])
        if not manifest:raise ManagerError("manifest_missing","No exact artifact manifest for this candidate",409)
        registered_paths={a.path for a in product.assets.assets if model_id in a.models}
        if set(cap.required_assets)!=registered_paths:raise ManagerError("inventory_missing","Registered native inventory is incomplete",409)
        verifier=ArtifactVerifier();reports=[]
        for c in manifest.components:
            if c.destination not in registered_paths:raise ManagerError("unregistered_file","Unregistered manifest component",409)
            path=product.assets.root/c.destination;assert_no_links(path)
            reports.append(verifier.verify(path,c).model_dump())
        return {"model_id":model_id,"valid":bool(reports) and all(r["valid"] for r in reports),"reports":reports,"generation_validated":False}
    @router.get("/{model_id}/update-check")
    def update(model_id:str,request:Request):
        product,cap=registered(request,model_id)
        manifest=next((json.loads(p.read_text()) for p in (product.root/"model_registry").glob("*.json") if json.loads(p.read_text()).get("id")== (cap.manifest_id or model_id)),None)
        if not manifest:raise ManagerError("manifest_missing","No pinned installation manifest",409)
        results=[]
        for c in manifest.get("components",[]):
            try:
                metadata=product.discovery.fetch("/api/models/"+c["repository_id"])
                latest=metadata.get("sha")
                if not re.fullmatch(r"[0-9a-f]{40}",str(latest)):raise ValueError()
                results.append({"repository":c["repository_id"],"installed_revision":c["pinned_revision"],"current_revision":latest,"different":latest!=c["pinned_revision"]})
            except Exception:results.append({"repository":c["repository_id"],"current_revision":None,"different":None})
        return {"components":results,"replacement_allowed":False,"message":"A newer repository commit is not an approved model upgrade. No files changed."}
    return router
