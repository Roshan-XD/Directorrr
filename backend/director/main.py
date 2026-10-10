import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from director.installations.api import installation_router
from director.installations.downloader import FixtureDownloader, HuggingFaceDownloader
from director.installations.fixtures import fixture_manifest, fixture_payloads
from director.installations.jobs import InstallationJobManager
from director.installations.schemas import ManagerError
from director.installations.storage import ModelStorageManager

from director.models.compatibility import evaluate_compatibility
from director.models.registry import ModelRegistry
from director.models.schemas import ModelManifest, ModelsResponse, RegisteredModel, RuntimeState
from director.models.planning import InstallationPlan, build_installation_plan
from director.system.hardware import detect_hardware
from director.system.schemas import HardwareProfile
from director.system.runtime import RuntimeReport, detect_runtime
from director.runtimes.api import runtime_router
from director.runtimes.fixtures import fixture_profile
from director.runtimes.manager import RuntimeProvisioningManager
from director.runtimes.schemas import RuntimeProfile
from director.runtimes.storage import RuntimeStorageManager
from director.runtimes.preflight import RuntimePreflight
from director.product.api import product_router, ProductServices
from director.generation.api import generation_router
from director.generation.service import ComfyUIClient, DevelopmentGeneration
from director.resolve.api import resolve_router
from director.resolve.service import DevelopmentResolve
from director.resolve.jobs import GenerationResolveJobs
from director.resolve.conversion import WindowsVideoConverter

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_hardware(request: Request) -> HardwareProfile:
    return detect_hardware(request.app.state.storage_path)


def get_runtime_state() -> RuntimeState:
    # Runtime inspection belongs to a future adapter, not backend package detection.
    return RuntimeState()


def get_runtime_report(request: Request) -> RuntimeReport:
    return detect_runtime(request.app.state.runtime_environment, request.app.state.comfyui_directory)


def get_registered_model(model_id: str, request: Request) -> ModelManifest:
    # IDs are looked up in memory, never interpolated into filesystem paths.
    model = next((item for item in request.app.state.manifests if item.id == model_id), None)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


def create_app(
    registry_dir: Path | None = None, storage_path: Path | None = None, model_root: Path | None = None,
    enable_fixtures: bool | None = None, allow_real_downloads: bool | None = None,
    manager_key: str | None = None, downloader=None,
    runtime_root: Path | None = None, enable_runtime_fixtures: bool | None = None,
    development_generation=None,
    development_resolve=None,
    development_resolve_jobs=None,
    studio_root: Path | None = None,
) -> FastAPI:
    if registry_dir is None:
        registry_dir = Path(os.environ.get("DIRECTOR_REGISTRY_DIR", PROJECT_ROOT / "model_registry"))
    if storage_path is None:
        storage_path = Path(os.environ.get("DIRECTOR_STORAGE_PATH", PROJECT_ROOT))
    if model_root is None:
        model_root = Path(os.environ.get("DIRECTOR_MODEL_ROOT", storage_path / "model_weights"))
    if enable_fixtures is None:
        enable_fixtures = os.environ.get("DIRECTOR_ENABLE_FIXTURES") == "1"
    if allow_real_downloads is None:
        allow_real_downloads = os.environ.get("DIRECTOR_ALLOW_REAL_DOWNLOADS") == "1"
    manager_key = manager_key or os.environ.get("DIRECTOR_MANAGER_TOKEN")
    runtime_root = runtime_root or Path(os.environ.get("DIRECTOR_RUNTIME_ROOT", PROJECT_ROOT / "runtime_storage"))
    if enable_runtime_fixtures is None:
        enable_runtime_fixtures = os.environ.get("DIRECTOR_ENABLE_RUNTIME_FIXTURES") == "1"
    studio_root=studio_root or Path(os.environ.get("DIRECTOR_STUDIO_ROOT",model_root.parent/"studio_data"))
    if manager_key is not None and len(manager_key) < 32:
        raise ValueError("DIRECTOR_MANAGER_TOKEN must have at least 32 characters")

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        # Bad metadata should be fixed explicitly, not silently omitted from recommendations.
        application.state.manifests = ModelRegistry(registry_dir).load()
        if enable_fixtures:
            if any(item.id == "fixture-tiny" for item in application.state.manifests):
                raise ValueError("fixture-tiny is reserved for Director's built-in offline fixture")
            application.state.manifests.append(fixture_manifest())
        application.state.product = ProductServices(PROJECT_ROOT, manager_key,studio_root=studio_root)
        application.state.storage_path = storage_path
        application.state.model_root = model_root
        application.state.manager_key = manager_key
        application.state.development_generation = development_generation
        application.state.development_resolve = development_resolve
        if development_resolve is None and os.environ.get("DIRECTOR_ENABLE_DEV_RESOLVE") == "1":
            application.state.development_resolve = DevelopmentResolve(PROJECT_ROOT)
        if development_generation is None and os.environ.get("DIRECTOR_ENABLE_DEV_GENERATION") == "1":
            application.state.development_generation = DevelopmentGeneration(
                ComfyUIClient(os.environ.get("DIRECTOR_DEV_COMFY_URL", "http://127.0.0.1:8188")),
                Path(os.environ.get("DIRECTOR_DEV_GENERATION_OUTPUT", r"\\wsl.localhost\Director-GPU-Dev\opt\director-gpu-dev\stage7\data\output")),
            )
        application.state.development_resolve_jobs = development_resolve_jobs
        if (development_resolve_jobs is None and application.state.development_resolve is not None
                and application.state.development_generation is not None):
            application.state.development_resolve_jobs = GenerationResolveJobs(
                application.state.development_generation, application.state.development_resolve, PROJECT_ROOT,
                converter=WindowsVideoConverter(PROJECT_ROOT)
                if os.environ.get("DIRECTOR_DEV_WINDOWS_RUNTIME") == "1" else None)
        application.state.runtime_environment = Path(os.environ["DIRECTOR_RUNTIME_ENV"]) if os.environ.get("DIRECTOR_RUNTIME_ENV") else None
        application.state.comfyui_directory = Path(os.environ["DIRECTOR_COMFYUI_DIR"]) if os.environ.get("DIRECTOR_COMFYUI_DIR") else None
        application.state.installations = InstallationJobManager(
            ModelStorageManager(model_root),
            downloader=downloader or HuggingFaceDownloader(enabled=allow_real_downloads,
                use_login=os.environ.get("DIRECTOR_HF_AUTH") == "login"),
            fixture_downloader=FixtureDownloader(fixture_payloads()) if enable_fixtures else None,
        )
        # Runtime profiles are separate metadata, never model manifests or executable commands.
        try:
            application.state.runtime_profiles = [RuntimeProfile.model_validate_json(path.read_text(encoding="utf-8"))
                                                 for path in sorted((PROJECT_ROOT / "runtime_profiles").glob("*.json"))]
            if any(profile.is_fixture for profile in application.state.runtime_profiles):
                raise ValueError("Fixture runtime profiles must use the built-in offline allowlist")
            profile_ids = [profile.id.casefold() for profile in application.state.runtime_profiles]
            if len(profile_ids) != len(set(profile_ids)) or "runtime-fixture-tiny" in profile_ids:
                raise ValueError("Runtime profile IDs must be unique; runtime-fixture-tiny is reserved")
            if enable_runtime_fixtures:
                application.state.runtime_profiles.append(fixture_profile())
            application.state.runtimes = RuntimeProvisioningManager(RuntimeStorageManager(runtime_root), enabled=enable_runtime_fixtures)
            application.state.runtime_preflight = RuntimePreflight(PROJECT_ROOT, application.state.runtimes)
            yield
        finally:
            if application.state.development_generation is not None:
                application.state.development_generation.close()
            if hasattr(application.state, "runtimes"):
                application.state.runtimes.close()
            application.state.installations.close()
            application.state.product.studio.close()
            application.state.product.downloads.close()

    application = FastAPI(title="Director", version="0.1.0", lifespan=lifespan)

    @application.middleware("http")
    async def product_activity(request: Request, call_next):
        response = await call_next(request)
        product = getattr(request.app.state,"product",None)
        route = request.scope.get("route")
        template = getattr(route,"path","")
        if product and request.method != "GET" and template.startswith(("/api/dev/resolve/","/api/models/","/api/installation-jobs/")):
            stage="resolve" if "/dev/resolve/" in template else "installation"
            product.console.add(stage,"Explicit operation " + template + " returned HTTP " + str(response.status_code),"info" if response.status_code<400 else "warning")
        return response

    @application.exception_handler(ManagerError)
    async def manager_error(request: Request, error: ManagerError):
        return JSONResponse(status_code=error.status_code, content={"detail": {"code": error.code, "message": error.message}})

    application.include_router(installation_router(get_registered_model))
    application.include_router(runtime_router())
    application.include_router(generation_router())
    application.include_router(product_router(PROJECT_ROOT))
    from director.product.studio_api import studio_router
    application.include_router(studio_router())
    from director.product.model_tools import model_tools_router
    application.include_router(model_tools_router())
    from director.product.h3 import h3_router
    application.include_router(h3_router(PROJECT_ROOT, get_hardware))
    application.include_router(resolve_router())

    @application.get("/api/system/hardware", response_model=HardwareProfile)
    def hardware(profile: HardwareProfile = Depends(get_hardware)) -> HardwareProfile:
        return profile

    @application.get("/api/system/runtime", response_model=RuntimeReport)
    def runtime_diagnostics(report: RuntimeReport = Depends(get_runtime_report)) -> RuntimeReport:
        return report

    @application.get("/api/models", response_model=ModelsResponse)
    def models(request: Request, profile: HardwareProfile = Depends(get_hardware),
               runtime: RuntimeState = Depends(get_runtime_state)) -> ModelsResponse:
        return ModelsResponse(
            models=[
                RegisteredModel(
                    manifest=manifest,
                    compatibility=evaluate_compatibility(manifest, profile, runtime),
                )
                for manifest in request.app.state.manifests
            ],
            hardware_warnings=profile.warnings,
        )

    @application.get("/api/models/{model_id}/installation-plan", response_model=InstallationPlan)
    def installation_plan(
        request: Request, manifest: ModelManifest = Depends(get_registered_model),
        profile: HardwareProfile = Depends(get_hardware), runtime: RuntimeState = Depends(get_runtime_state),
    ) -> InstallationPlan:
        plan = build_installation_plan(manifest, profile, request.app.state.model_root, runtime)
        plan.artifact_review = request.app.state.installations.artifact_review(
            manifest, bool(request.app.state.manager_key))
        return plan

    return application


app = create_app()
