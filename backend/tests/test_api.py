import pytest
from fastapi.testclient import TestClient

from director.main import PROJECT_ROOT, create_app, get_hardware
from director.models.registry import RegistryError
from director.models.schemas import ModelsResponse
from director.system.schemas import HardwareProfile


def test_endpoints_use_same_injected_hardware(hardware):
    application = create_app()
    application.dependency_overrides[get_hardware] = lambda: hardware
    with TestClient(application) as client:
        response = client.get("/api/system/hardware")
        assert response.status_code == 200
        assert HardwareProfile.model_validate(response.json()) == hardware
        response = client.get("/api/models")
        assert response.status_code == 200
        result = ModelsResponse.model_validate(response.json())
        assert len(result.models) == 3
        mocks = [model for model in result.models if model.manifest.is_mock]
        assert len(mocks) == 2
        assert all(model.compatibility.status == "compatible" for model in mocks)
        real = next(model for model in result.models if not model.manifest.is_mock)
        assert real.compatibility.status == "unknown"
        assert real.compatibility.assessment == "potentially_compatible"
        assert client.get("/openapi.json").status_code == 200


def test_partial_hardware_is_returned_with_warnings(hardware):
    hardware.gpus = []
    hardware.gpu_detection_complete = False
    hardware.warnings = ["GPU query failed"]
    application = create_app()
    application.dependency_overrides[get_hardware] = lambda: hardware
    with TestClient(application) as client:
        response = client.get("/api/models")
        assert response.status_code == 200
        result = response.json()
        assert result["hardware_warnings"] == hardware.warnings
        statuses = {item["manifest"]["id"]: item["compatibility"]["status"] for item in result["models"]}
        assert statuses == {"mock-cpu-video": "compatible", "mock-gpu-video": "unknown", "wan-2-1-t2v-1-3b": "unknown"}


def test_invalid_registry_prevents_startup(tmp_path):
    (tmp_path / "bad.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RegistryError, match="bad.json"):
        with TestClient(create_app(registry_dir=tmp_path)):
            pass


def test_paths_do_not_depend_on_working_directory(monkeypatch, tmp_path, hardware):
    monkeypatch.chdir(tmp_path)
    application = create_app()
    application.dependency_overrides[get_hardware] = lambda: hardware
    with TestClient(application) as client:
        assert application.state.storage_path == PROJECT_ROOT
        assert len(client.get("/api/models").json()["models"]) == 3


def test_environment_can_select_empty_registry(monkeypatch, tmp_path, hardware):
    monkeypatch.setenv("DIRECTOR_REGISTRY_DIR", str(tmp_path))
    monkeypatch.setenv("DIRECTOR_STORAGE_PATH", str(tmp_path))
    application = create_app()
    application.dependency_overrides[get_hardware] = lambda: hardware
    with TestClient(application) as client:
        assert client.get("/api/models").json()["models"] == []
        assert application.state.storage_path == tmp_path
