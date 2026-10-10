from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from director.installations.api import require_manager_key
from director.installations.schemas import ManagerError
from director.resolve.service import PlacementRequest


def resolve_router():
    router = APIRouter(prefix="/api/dev/resolve", dependencies=[Depends(require_manager_key)])

    def service(request: Request):
        adapter = request.app.state.development_resolve
        if adapter is None:
            raise ManagerError("resolve_disabled", "Development Resolve integration is disabled", 404)
        return adapter

    def jobs(request: Request):
        adapter = request.app.state.development_resolve_jobs
        if adapter is None:
            raise ManagerError("resolve_disabled", "Enable both development generation and Resolve adapters", 404)
        return adapter

    @router.get("/timelines")
    def timelines(adapter=Depends(service)):
        return adapter.inspect()

    @router.post("/placement")
    def place(body: PlacementRequest, adapter=Depends(service)):
        return adapter.place(body)

    @router.get("/jobs/{job_id}")
    def result(job_id: str, adapter=Depends(jobs)):
        return adapter.status(job_id)

    @router.post("/jobs/{job_id}/import")
    def import_result(job_id: str, adapter=Depends(jobs)):
        return adapter.import_job(job_id)

    @router.post("/jobs/{job_id}/placement")
    def place_result(job_id: str, body: PlacementRequest, adapter=Depends(jobs)):
        return adapter.place(job_id, body)

    @router.get("/jobs/{job_id}/output")
    def output(job_id: str, adapter=Depends(jobs)):
        filename, data = adapter.output(job_id)
        return Response(data, media_type="video/mp4", headers={
            "Content-Disposition": f'inline; filename="{filename}"', "X-Director-Job": job_id,
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    return router
