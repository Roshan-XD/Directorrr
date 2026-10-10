import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from director.generation.service import GenerationJob
from director.installations.schemas import ManagerError
from director.main import create_app
from director.resolve.jobs import GenerationResolveJobs
from director.resolve.service import DevelopmentResolve, PlacementRequest

ID = "c" * 32


@pytest.fixture
def jobs(tmp_path):
    generation = MagicMock()
    generation.get.return_value = GenerationJob(id=ID, state="completed")
    generation.output.return_value = (f"Director_Stage8_{ID}_00001_.webm", b"\x1a\x45\xdf\xa3tiny")
    pool = MagicMock()
    inventory = []
    pool.GetRootFolder.return_value.GetClipList.side_effect = lambda: inventory[:]
    pool.GetRootFolder.return_value.GetSubFolderList.return_value = []
    project = MagicMock()
    project.GetName.return_value = "Director Development"
    project.GetMediaPool.return_value = pool
    project.GetTimelineCount.return_value = 1
    timeline = MagicMock()
    timeline.GetName.return_value = "Development"
    timeline.GetUniqueId.return_value = "timeline"
    timeline.GetSetting.return_value = "24"
    timeline.GetTrackCount.side_effect = lambda kind: 1 if kind == "video" else 0
    entries = []
    timeline.GetItemListInTrack.side_effect = lambda *args: entries[:]
    project.GetTimelineByIndex.return_value = timeline
    project.GetCurrentTimeline.return_value = timeline
    connector = MagicMock()
    connector.GetProjectManager.return_value.GetCurrentProject.return_value = project
    resolve = DevelopmentResolve(tmp_path, lambda: connector)
    def convert(source, output):
        assert source.read_bytes() == generation.output.return_value[1]
        output.write_bytes(b"\x00\x00\x00\x20ftyp" + b"tiny converted fixture")
        return {"codec": "h264", "container": "mp4", "pixel_format": "yuv420p", "width": 320, "height": 192,
                "frames": 17, "fps": 16, "duration_seconds": 1.0625, "size_bytes": output.stat().st_size,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "decoded_all_frames": True}
    def imported(paths):
        clip = MagicMock()
        clip.GetMediaId.return_value = "new-media"
        clip.GetClipProperty.side_effect = lambda key: paths[0] if key == "File Path" else "Online"
        inventory.append(clip)
        return [clip]
    pool.ImportMedia.side_effect = imported
    def append(clips):
        item = MagicMock()
        item.GetUniqueId.return_value = "new-timeline-item"
        item.GetMediaPoolItem.return_value = clips[0]
        item.GetDuration.return_value = 25
        entries.append(item)
        return [item]
    pool.AppendToTimeline.side_effect = append
    return GenerationResolveJobs(generation, resolve, tmp_path, convert), generation, pool


def test_new_job_full_mock_flow_and_idempotent_import(jobs):
    manager, _, pool = jobs
    assert manager.status(ID)["state"] == "generated"
    result = manager.import_job(ID)
    assert result["job_id"] == ID and result["state"] == "imported"
    assert result["media_id"] == "new-media"
    manager.import_job(ID)
    pool.ImportMedia.assert_called_once()
    filename, data = manager.output(ID)
    assert filename == f"Director_{ID}.mp4" and data[4:8] == b"ftyp"
    placed = manager.place(ID, PlacementRequest(confirmed=True, timeline_id="timeline", timeline_name="Development"))
    assert placed["state"] == "placed" and placed["placement"]["media_id"] == "new-media"
    pool.AppendToTimeline.assert_called_once()
    with pytest.raises(ManagerError):
        manager.place(ID, PlacementRequest(confirmed=True))
    pool.AppendToTimeline.assert_called_once()


@pytest.mark.parametrize("state", ["queued", "running", "failed"])
def test_incomplete_generation_rejected(jobs, state):
    manager, generation, pool = jobs
    generation.get.return_value.state = state
    with pytest.raises(ManagerError): manager.import_job(ID)
    pool.ImportMedia.assert_not_called()


@pytest.mark.parametrize("job_id", ["../secret", "C:/secret", "nope"])
def test_arbitrary_paths_rejected(jobs, job_id):
    with pytest.raises(ManagerError): jobs[0].import_job(job_id)


def test_conversion_failure_no_import_or_retry(jobs):
    manager, _, pool = jobs
    manager.converter = MagicMock(side_effect=ValueError("conversion failed"))
    with pytest.raises(ManagerError, match="Conversion failed"): manager.import_job(ID)
    assert manager.status(ID)["state"] == "failed"
    with pytest.raises(ManagerError): manager.import_job(ID)
    pool.ImportMedia.assert_not_called()


def test_import_failure_no_retry(jobs):
    manager, _, pool = jobs
    pool.ImportMedia.side_effect = None
    pool.ImportMedia.return_value = []
    with pytest.raises(ManagerError, match="Media Pool import failed"): manager.import_job(ID)
    with pytest.raises(ManagerError): manager.import_job(ID)
    pool.ImportMedia.assert_called_once()


def test_unavailable_resolve_prevents_conversion(jobs):
    manager, _, pool = jobs
    manager.resolve.connector = lambda: None
    with pytest.raises(ManagerError, match="unavailable"): manager.import_job(ID)
    assert not manager.root.exists()
    pool.ImportMedia.assert_not_called()


def test_corruption_prevents_output_and_placement(jobs):
    manager, _, pool = jobs
    manager.import_job(ID)
    output = manager.root / ID / f"Director_{ID}.mp4"
    output.write_bytes(b"corrupted")
    with pytest.raises(ManagerError): manager.output(ID)
    with pytest.raises(ManagerError): manager.place(ID, PlacementRequest(confirmed=True))
    pool.AppendToTimeline.assert_not_called()


def test_declined_or_missing_target_has_no_timeline_mutation(jobs):
    manager, _, pool = jobs
    manager.import_job(ID)
    for body in [PlacementRequest(confirmed=False), PlacementRequest(confirmed=True)]:
        with pytest.raises(ManagerError): manager.place(ID, body)
    assert manager.status(ID)["state"] == "imported"
    pool.AppendToTimeline.assert_not_called()


def test_insufficient_disk(jobs, monkeypatch):
    manager, _, pool = jobs
    monkeypatch.setattr("director.resolve.jobs.shutil.disk_usage", lambda _: MagicMock(free=1))
    with pytest.raises(ManagerError, match="free space"): manager.import_job(ID)
    pool.ImportMedia.assert_not_called()


def test_authenticated_job_api(jobs, tmp_path):
    manager, _, pool = jobs
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key="k" * 32,
                     development_resolve_jobs=manager)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        path = f"/api/dev/resolve/jobs/{ID}"
        assert client.get(path).status_code == 403
        headers = {"X-Director-Key": "k" * 32}
        assert client.post(path + "/import", headers={**headers, "Origin": "https://evil.example"}).status_code == 403
        assert client.post(path + "/import", headers=headers).json()["state"] == "imported"
        video = client.get(path + "/output", headers=headers)
        assert video.status_code == 200 and video.headers["content-type"] == "video/mp4"
        assert client.get(path + "/output").status_code == 403
    pool.ImportMedia.assert_called_once()


def test_product_geometry_resolve_regression(jobs):
    manager,generation,pool=jobs
    generation.get.return_value.creative={"width":288,"height":512,"frames":33,"fps":16}
    convert=manager.converter
    def dynamic(source,output):
        metadata=convert(source,output)
        metadata.update(width=288,height=512,frames=33,duration_seconds=33/16)
        return metadata
    manager.converter=dynamic
    result=manager.import_job(ID)
    assert result["video"]["frames"]==33
    assert pool.ImportMedia.call_count==1

def test_product_geometry_mismatch_blocks_import(jobs):
    manager,generation,pool=jobs
    generation.get.return_value.creative={"width":288,"height":512,"frames":33,"fps":16}
    with pytest.raises(ManagerError):manager.import_job(ID)
    pool.ImportMedia.assert_not_called()
