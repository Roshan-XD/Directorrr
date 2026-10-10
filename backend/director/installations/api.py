import secrets
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request

from director.installations.schemas import AcknowledgeRequest, InstallRequest, ManagerError
from director.models.schemas import ModelManifest


def require_manager_key(request: Request) -> None:
    key = request.app.state.manager_key
    if not key:
        raise HTTPException(503, detail={"code": "manager_key_missing", "message": "Configure DIRECTOR_MANAGER_TOKEN to enable mutations"})
    if request.url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise HTTPException(403, detail="Local host required")
    origin = request.headers.get("origin")
    if origin:
        parsed = urlsplit(origin)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != request.url.netloc:
            raise HTTPException(403, detail="Untrusted origin")
    if not secrets.compare_digest(request.headers.get("X-Director-Key", "").encode("utf-8"), key.encode("utf-8")):
        raise HTTPException(403, detail="Model Manager authorization required")


def installation_router(get_model) -> APIRouter:
    router = APIRouter()
    mutations = [Depends(require_manager_key)]

    @router.get("/api/models/{model_id}/license-requirements")
    def requirements(request: Request, model: ModelManifest = Depends(get_model)):
        from director.installations.schemas import manifest_digest
        return {**request.app.state.installations.licenses.requirements(model), "manifest_digest": manifest_digest(model)}

    @router.post("/api/models/{model_id}/license-acknowledgements", dependencies=mutations, status_code=201)
    def acknowledge(body: AcknowledgeRequest, request: Request, model: ModelManifest = Depends(get_model)):
        return request.app.state.installations.licenses.record(model, body.document_set_digest, accepted=body.accepted)

    @router.post("/api/models/{model_id}/installations", dependencies=mutations, status_code=202)
    def install(body: InstallRequest, request: Request, model: ModelManifest = Depends(get_model)):
        return request.app.state.installations.start(model, "install", body.manifest_digest, body.acknowledgement_id)

    @router.get("/api/installation-jobs/{job_id}")
    def job(job_id: str, request: Request):
        return request.app.state.installations.get(job_id)

    @router.post("/api/installation-jobs/{job_id}/cancel", dependencies=mutations, status_code=202)
    def cancel(job_id: str, request: Request):
        return request.app.state.installations.cancel(job_id)

    @router.get("/api/models/{model_id}/installation")
    def status(request: Request, model: ModelManifest = Depends(get_model)):
        return request.app.state.installations.status(model)

    @router.post("/api/models/{model_id}/installation/verify", dependencies=mutations, status_code=202)
    def verify(request: Request, model: ModelManifest = Depends(get_model)):
        return request.app.state.installations.start(model, "verify")

    @router.delete("/api/models/{model_id}/installation", dependencies=mutations, status_code=202)
    def remove(request: Request, model: ModelManifest = Depends(get_model)):
        return request.app.state.installations.start(model, "remove")

    return router
