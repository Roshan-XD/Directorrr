import hashlib
import importlib
import json
import sys
import threading
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from director.installations.schemas import ManagerError
from director.installations.verifier import assert_no_links

MEDIA_ID = "e9c970ca-b631-4071-9012-d82cc71fcc1a"
JOB_ID = "a2147a96924045caae576e1f4e5c1fff"
PROJECT = "Director Development"
NEW_TIMELINE = "Director AI Test"


class PlacementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    confirmed: bool
    create_new: bool = False
    timeline_id: str | None = Field(default=None, min_length=1, max_length=128)
    timeline_name: str | None = Field(default=None, min_length=1, max_length=256)


def connect_resolve():
    # Load only Blackmagic's installed module, never a module supplied by a request.
    directory = Path(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
    if not (directory / "DaVinciResolveScript.py").is_file():
        raise ManagerError("resolve_unavailable", "Official Resolve scripting module is unavailable", 503)
    sys.path.insert(0, str(directory))
    try:
        return importlib.import_module("DaVinciResolveScript").scriptapp("Resolve")
    except Exception as exc:
        raise ManagerError("resolve_unavailable", "Resolve scripting connection failed; check local scripting access", 503) from exc
    finally:
        sys.path.remove(str(directory))


def pool_items(folder):
    items = list(folder.GetClipList() or [])
    for child in folder.GetSubFolderList() or []:
        items.extend(pool_items(child))
    return items


def timeline_items(timeline):
    return [item for kind in ("video", "audio")
            for index in range(1, timeline.GetTrackCount(kind) + 1)
            for item in timeline.GetItemListInTrack(kind, index) or []]


class DevelopmentResolve:
    """One-shot placement of the verified Stage 9 clip; no arbitrary media imports."""
    def __init__(self, root: Path, connector=connect_resolve):
        self.root = root
        self.connector = connector
        self.lock = threading.Lock()

    def context(self):
        resolve = self.connector()
        if resolve is None:
            raise ManagerError("resolve_unavailable", "Resolve is unavailable; open it and enable local scripting access", 503)
        manager = resolve.GetProjectManager()
        project = manager.GetCurrentProject() if manager else None
        if project is None or project.GetName() != PROJECT:
            raise ManagerError("resolve_project", "Open the Director Development project", 409)
        pool = project.GetMediaPool()
        if pool is None:
            raise ManagerError("resolve_pool", "Media Pool is unavailable", 409)
        return project, pool

    def inspect(self):
        project, _ = self.context()
        current = project.GetCurrentTimeline()
        return {"development_only": True, "project": PROJECT, "media_id": MEDIA_ID,
                "current_timeline_id": current.GetUniqueId() if current else None,
                "timelines": [{"id": t.GetUniqueId(), "name": t.GetName()}
                              for t in [project.GetTimelineByIndex(i)
                                        for i in range(1, project.GetTimelineCount() + 1)]]}

    def place(self, body: PlacementRequest):
        if body.confirmed is not True:
            raise ManagerError("confirmation_required", "Explicit timeline placement confirmation is required", 409)
        if not self.lock.acquire(blocking=False):
            raise ManagerError("placement_active", "A placement is already in progress", 409)
        try:
            return self._place(body)
        finally:
            self.lock.release()

    def _place(self, body):
        project, pool = self.context()
        path = self.root / "generated_videos" / "stage9" / f"Director_Stage8_{JOB_ID}.mp4"
        try:
            assert_no_links(path)
        except ValueError as exc:
            raise ManagerError("output_invalid", "Linked output paths are not permitted", 409) from exc
        if (not path.is_file() or path.stat().st_size != 125769
                or hashlib.sha256(path.read_bytes()).hexdigest() != "ebfeda18308703be8c8bb0446d2a44fe4209b3e7d68b20393ab9fdbe4a7f6410"):
            raise ManagerError("output_invalid", "The verified Stage 9 output is missing or changed", 409)
        return self.place_media(body, path, MEDIA_ID, self.root / ".verification" / "stage10" / "placement.json")

    def place_media(self, body, path, media_id, receipt):
        """Shared placement and verification for legacy and new job-associated media."""
        if body.confirmed is not True:
            raise ManagerError("confirmation_required", "Explicit timeline placement confirmation is required", 409)
        project, pool = self.context()
        clips = [item for item in pool_items(pool.GetRootFolder()) if item.GetMediaId() == media_id]
        if (len(clips) != 1 or Path(clips[0].GetClipProperty("File Path")) != path
                or clips[0].GetClipProperty("Online Status") != "Online"):
            raise ManagerError("media_missing", "The known Stage 9 Media Pool clip is unavailable or offline", 409)
        timelines = [project.GetTimelineByIndex(i) for i in range(1, project.GetTimelineCount() + 1)]
        if body.create_new:
            if timelines or body.timeline_id is not None or body.timeline_name != NEW_TIMELINE:
                raise ManagerError("timeline_changed", "New timeline creation requires no existing timelines and the approved name", 409)
            timeline = None
        else:
            matches = [t for t in timelines if t.GetUniqueId() == body.timeline_id and t.GetName() == body.timeline_name]
            if len(matches) != 1:
                raise ManagerError("timeline_changed", "Selected timeline is missing or renamed; review again", 409)
            timeline = matches[0]
        if any(item.GetMediaPoolItem() and item.GetMediaPoolItem().GetMediaId() == media_id
               for t in timelines for item in timeline_items(t)):
            raise ManagerError("already_placed", "This clip is already on a timeline; refusing duplicate placement", 409)
        assert_no_links(receipt)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        # Durable attempt marker prevents a retry after an ambiguous API failure/restart.
        try:
            with receipt.open("x", encoding="utf-8") as file:
                json.dump({"state": "attempting", "request": body.model_dump()}, file)
        except FileExistsError as exc:
            raise ManagerError("placement_attempted", "Placement was already attempted; inspect Resolve and the receipt before further action", 409) from exc
        result = {"development_only": True, "project": PROJECT, "media_id": media_id,
                  "created_timeline": body.create_new, "state": "failed"}
        try:
            if timeline is None:
                timeline = pool.CreateEmptyTimeline(NEW_TIMELINE)
            if timeline is None or not project.SetCurrentTimeline(timeline):
                raise RuntimeError("Timeline creation or selection failed")
            before = {item.GetUniqueId() for item in timeline_items(timeline)}
            appended = pool.AppendToTimeline([clips[0]])
            if not appended or len(appended) != 1:
                raise RuntimeError("AppendToTimeline did not return exactly one item")
            item = appended[0]
            after = {entry.GetUniqueId() for entry in timeline_items(timeline)}
            fps = float(timeline.GetSetting("timelineFrameRate"))
            duration = float(item.GetDuration()) / fps
            if (item.GetMediaPoolItem().GetMediaId() != media_id
                    or after != before | {item.GetUniqueId()}
                    or abs(duration - 17 / 16) > 1 / fps + 0.0001):
                raise RuntimeError("Inserted media identity, inventory or duration verification failed")
            result.update(state="placed", timeline=timeline.GetName(), timeline_id=timeline.GetUniqueId(),
                          item_id=item.GetUniqueId(), duration_seconds=duration, timeline_fps=fps)
        except Exception as exc:
            result["message"] = str(exc)
            receipt.write_text(json.dumps(result, indent=2), encoding="utf-8")
            raise ManagerError("placement_failed", "Resolve placement failed or could not be verified; inspect the timeline before retrying", 502) from exc
        receipt.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
