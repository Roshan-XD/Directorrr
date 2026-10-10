from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from director.installations.api import require_manager_key
from director.installations.schemas import ManagerError
from director.generation.service import GenerationJob, GenerationRequest


def generation_router():
    router = APIRouter(prefix="/api/dev/generation")

    def manager(request: Request):
        service = request.app.state.development_generation
        if service is None:
            raise ManagerError("development_generation_disabled", "Development generation is disabled", 404)
        return service

    @router.get("/config")
    def config(request: Request):
        return {"enabled": request.app.state.development_generation is not None, "development_only": True}

    @router.post("/jobs", response_model=GenerationJob, status_code=202, dependencies=[Depends(require_manager_key)])
    def create(body: GenerationRequest, service=Depends(manager)):
        return service.start(body)

    @router.get("/jobs/{job_id}", response_model=GenerationJob, dependencies=[Depends(require_manager_key)])
    def status(job_id: str, service=Depends(manager)):
        return service.get(job_id)

    @router.get("/jobs/{job_id}/output", dependencies=[Depends(require_manager_key)])
    def output(job_id: str, service=Depends(manager)):
        filename, content = service.output(job_id)
        return Response(content, media_type="video/mp4" if filename.endswith(".mp4") else "video/webm", headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Director-Job": job_id,
        })

    return router
