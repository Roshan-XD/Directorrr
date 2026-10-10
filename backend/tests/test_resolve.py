from unittest.mock import MagicMock
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from director.installations.schemas import ManagerError
from director.main import create_app
from director.resolve.service import DevelopmentResolve, JOB_ID, MEDIA_ID, PlacementRequest


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    output = tmp_path / "generated_videos/stage9" / f"Director_Stage8_{JOB_ID}.mp4"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"x" * 125769)
    # Scope the synthetic clip hash to Resolve. Patching hashlib.sha256 itself
    # changes the shared module and corrupts independent recipe verification.
    monkeypatch.setattr("director.resolve.service.hashlib", SimpleNamespace(sha256=lambda _: MagicMock(
        hexdigest=lambda: "ebfeda18308703be8c8bb0446d2a44fe4209b3e7d68b20393ab9fdbe4a7f6410")))
    clip = MagicMock()
    clip.GetMediaId.return_value = MEDIA_ID
    clip.GetClipProperty.side_effect = lambda key: str(output) if key == "File Path" else "Online"
    pool = MagicMock()
    pool.GetRootFolder.return_value.GetClipList.return_value = [clip]
    pool.GetRootFolder.return_value.GetSubFolderList.return_value = []
    project = MagicMock()
    project.GetName.return_value = "Director Development"
    project.GetMediaPool.return_value = pool
    project.GetTimelineCount.return_value = 0
    project.GetCurrentTimeline.return_value = None
    timeline = MagicMock()
    timeline.GetName.return_value = "Director AI Test"
    timeline.GetUniqueId.return_value = "timeline-1"
    timeline.GetSetting.return_value = "24"
    timeline.GetTrackCount.side_effect = lambda kind: 1 if kind == "video" else 0
    item = MagicMock()
    item.GetUniqueId.return_value = "item-1"
    item.GetMediaPoolItem.return_value = clip
    item.GetDuration.return_value = 26
    timeline.GetItemListInTrack.side_effect = [[], [item]]
    pool.CreateEmptyTimeline.return_value = timeline
    pool.AppendToTimeline.return_value = [item]
    resolve = MagicMock()
    resolve.GetProjectManager.return_value.GetCurrentProject.return_value = project
    service = DevelopmentResolve(tmp_path, lambda: resolve)
    return service, project, pool, timeline


def approval(**changes):
    return PlacementRequest(**{"confirmed": True, "create_new": True, "timeline_name": "Director AI Test", **changes})


def test_empty_timelines(adapter):
    service, _, pool, _ = adapter
    assert service.inspect()["timelines"] == []
    pool.CreateEmptyTimeline.assert_not_called()
    pool.AppendToTimeline.assert_not_called()


def test_successful_new_placement_and_retry_prevention(adapter):
    service, _, pool, _ = adapter
    result = service.place(approval())
    assert result["state"] == "placed"
    assert result["duration_seconds"] == pytest.approx(26 / 24)
    assert result["created_timeline"] is True
    pool.AppendToTimeline.assert_called_once()
    with pytest.raises(ManagerError):
        service.place(approval())
    pool.AppendToTimeline.assert_called_once()


def test_selected_existing_timeline(adapter):
    service, project, pool, timeline = adapter
    project.GetTimelineCount.return_value = 1
    project.GetTimelineByIndex.return_value = timeline
    project.GetCurrentTimeline.return_value = timeline
    timeline.GetItemListInTrack.side_effect = [[], [], [pool.AppendToTimeline.return_value[0]]]
    report = service.inspect()
    assert report["current_timeline_id"] == "timeline-1"
    result = service.place(approval(create_new=False, timeline_id="timeline-1"))
    assert result["created_timeline"] is False
    pool.CreateEmptyTimeline.assert_not_called()
    project.SetCurrentTimeline.assert_called_once_with(timeline)


@pytest.mark.parametrize("changes", [{"confirmed": False}, {"create_new": False, "timeline_id": "missing"}, {"timeline_name": "Other"}])
def test_confirmation_selection_guard(adapter, changes):
    service, _, pool, _ = adapter
    with pytest.raises(ManagerError):
        service.place(approval(**changes))
    pool.AppendToTimeline.assert_not_called()
    pool.CreateEmptyTimeline.assert_not_called()


def test_existing_timeline_prevents_implicit_creation(adapter):
    service, project, pool, timeline = adapter
    project.GetTimelineCount.return_value = 1
    project.GetTimelineByIndex.return_value = timeline
    with pytest.raises(ManagerError):
        service.place(approval())
    pool.CreateEmptyTimeline.assert_not_called()


def test_failure_receipt_blocks_retry(adapter):
    service, _, pool, _ = adapter
    pool.AppendToTimeline.return_value = []
    with pytest.raises(ManagerError, match="placement failed"):
        service.place(approval())
    with pytest.raises(ManagerError, match="already attempted"):
        service.place(approval())
    pool.AppendToTimeline.assert_called_once()


def test_unavailable_wrong_project_and_missing_media(adapter):
    service, project, pool, _ = adapter
    service.connector = lambda: None
    with pytest.raises(ManagerError, match="unavailable"):
        service.inspect()
    service.connector = lambda: MagicMock(GetProjectManager=lambda: MagicMock(GetCurrentProject=lambda: project))
    project.GetName.return_value = "Other"
    with pytest.raises(ManagerError, match="Director Development"):
        service.inspect()
    project.GetName.return_value = "Director Development"
    pool.GetRootFolder.return_value.GetClipList.return_value = []
    with pytest.raises(ManagerError, match="clip is unavailable"):
        service.place(approval())


def test_no_arbitrary_paths_or_media():
    with pytest.raises(ValidationError):
        PlacementRequest(confirmed=True, path="C:/secret.mp4")


def test_authenticated_api_and_origin(adapter, tmp_path):
    service, _, _, _ = adapter
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key="k" * 32,
                     development_resolve=service)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/api/dev/resolve/timelines").status_code == 403
        headers = {"X-Director-Key": "k" * 32}
        assert client.get("/api/dev/resolve/timelines", headers=headers).status_code == 200
        assert client.post("/api/dev/resolve/placement", headers={**headers, "Origin": "https://evil.example"},
                           json=approval().model_dump()).status_code == 403
        assert client.post("/api/dev/resolve/placement", headers=headers, json=approval().model_dump()).status_code == 200
