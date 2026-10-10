import hashlib
import json
import os
import re
import shutil
import stat
import threading
from pathlib import Path

from director.installations.schemas import ManagerError
from director.installations.verifier import assert_no_links
from director.resolve.conversion import WslVideoConverter
from director.resolve.service import pool_items


def verified_bytes(path, size=None, checksum=None):
    assert_no_links(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= 32 * 1024 * 1024:
        raise ValueError("Unsafe video")
    with path.open("rb") as file:
        opened = os.fstat(file.fileno())
        data = file.read(32 * 1024 * 1024 + 1)
    assert_no_links(path)
    after = path.stat()
    identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    if identity(before) != identity(opened) or identity(before) != identity(after):
        raise ValueError("Video changed")
    if len(data) != before.st_size or (size is not None and len(data) != size):
        raise ValueError("Wrong size")
    if checksum is not None and hashlib.sha256(data).hexdigest() != checksum:
        raise ValueError("Wrong hash")
    return data


class GenerationResolveJobs:
    """Conversion/import state for completed jobs; never accept user filesystem paths."""
    def __init__(self, generation, resolve, root: Path, converter=None):
        self.generation, self.resolve = generation, resolve
        self.root = root / "generated_videos" / "development"
        self.converter = converter or WslVideoConverter()
        self.lock = threading.RLock()

    def folder(self, job_id):
        if not re.fullmatch(r"[0-9a-f]{32}", job_id):
            raise ManagerError("invalid_job", "Invalid generation job ID", 404)
        if self.generation.get(job_id).state != "completed":
            raise ManagerError("output_not_ready", "Wait for generation to complete", 409)
        path = self.root / job_id
        try:
            assert_no_links(path)
        except ValueError as exc:
            raise ManagerError("output_invalid", "Linked development output paths are prohibited", 409) from exc
        return path

    def read(self, folder):
        record = folder / "result.json"
        assert_no_links(record)
        if not record.exists():
            return {"state": "generated", "development_only": True, "job_id": folder.name}
        if record.stat().st_size > 16384:
            raise ManagerError("result_invalid", "Invalid result receipt", 409)
        return json.loads(record.read_text(encoding="utf-8"))

    def save(self, folder, result):
        path = folder / "result.json"
        temporary = folder / "result.pending.json"
        assert_no_links(path); assert_no_links(temporary)
        with temporary.open("x", encoding="utf-8") as file:
            json.dump(result, file, indent=2)
        os.replace(temporary, path)

    def status(self, job_id):
        with self.lock:
            return self.read(self.folder(job_id))

    def output_path(self, folder, result):
        path = folder / ("Director_" + folder.name + ".mp4")
        metadata = result["video"]
        data = verified_bytes(path, metadata["size_bytes"], metadata["sha256"])
        if data[4:8] != b"ftyp":
            raise ValueError("Not MP4")
        return path

    def import_job(self, job_id):
        with self.lock:
            folder = self.folder(job_id)
            result = self.read(folder)
            if result["state"] in {"imported", "placed"}:
                self.output_path(folder, result)
                return result  # Idempotent; never issue another ImportMedia call.
            if result["state"] != "generated":
                raise ManagerError("import_attempted", "Import/conversion was already attempted; inspect the result before retrying", 409)
            project, pool = self.resolve.context()
            filename, source = self.generation.output(job_id)
            if filename.endswith(".mp4"):
                raise ManagerError("audio_handoff_unvalidated", "H3 audio/video preview is available. Resolve handoff remains limited to the validated Wan conversion.", 409)
            assert filename.startswith("Director_Stage8_" + job_id + "_")
            if shutil.disk_usage(self.root.parent if self.root.parent.exists() else self.resolve.root).free < 128 * 1024 * 1024:
                raise ManagerError("disk_space", "At least 128 MiB free space is required for the tiny development conversion", 409)
            folder.mkdir(parents=True, exist_ok=False)
            result.update(state="converting", source_sha256=hashlib.sha256(source).hexdigest())
            self.save(folder, result)
            try:
                webm = folder / ("Director_" + job_id + ".webm")
                with webm.open("xb") as file: file.write(source)
                output = folder / ("Director_" + job_id + ".mp4")
                metadata = self.converter(webm, output)
                creative = getattr(self.generation.get(job_id), "creative", None) or {}
                expected = (creative.get("width",320), creative.get("height",192), creative.get("frames",17), creative.get("fps",16))
                if (metadata.get("codec"), metadata.get("pixel_format"), metadata.get("width"), metadata.get("height"),
                    metadata.get("frames"), metadata.get("fps"), metadata.get("duration_seconds"), metadata.get("decoded_all_frames")) != ("h264", "yuv420p", *expected, expected[2]/expected[3], True):
                    raise ValueError("Conversion metadata mismatch")
                result.update(video=metadata, filename=output.name, state="converted")
                self.output_path(folder, result)
                self.save(folder, result)
            except Exception as exc:
                result.update(state="failed", message="Conversion failed; original WebM retained. Inspect the development result before retrying.")
                self.save(folder, result)
                raise ManagerError("conversion_failed", result["message"], 502) from exc
            # Recheck active project immediately before the external mutation.
            project, pool = self.resolve.context()
            result.update(state="importing")
            self.save(folder, result)
            try:
                if any(Path(item.GetClipProperty("File Path") or "") == output for item in pool_items(pool.GetRootFolder())):
                    raise ValueError("Unexpected existing import")
                imported = pool.ImportMedia([str(output)])
                if not imported or len(imported) != 1:
                    raise ValueError("Import did not return one item")
                item = imported[0]
                media_id = item.GetMediaId()
                if (not media_id or item.GetClipProperty("Online Status") != "Online"
                        or Path(item.GetClipProperty("File Path")) != output
                        or not any(clip.GetMediaId() == media_id for clip in pool_items(pool.GetRootFolder()))):
                    raise ValueError("Imported media verification failed")
                result.update(state="imported", media_id=media_id, project=project.GetName(), message="Imported to Resolve; ready for timeline review")
                self.save(folder, result)
                return result
            except Exception as exc:
                result.update(state="failed", message="Media Pool import failed or is uncertain; inspect Resolve before retrying")
                self.save(folder, result)
                raise ManagerError("import_failed", result["message"], 502) from exc

    def place(self, job_id, body):
        with self.lock, self.resolve.lock:
            folder = self.folder(job_id)
            result = self.read(folder)
            if result["state"] != "imported":
                raise ManagerError("not_imported", "Import this completed job before timeline placement; duplicate placement is prohibited", 409)
            try:
                output = self.output_path(folder, result)
            except (OSError, ValueError) as exc:
                raise ManagerError("output_invalid", "Converted output is missing or changed", 409) from exc
            placement = self.resolve.place_media(body, output, result["media_id"], folder / "placement.json")
            result.update(state="placed", placement=placement, message="Placed on timeline")
            self.save(folder, result)
            return result

    def output(self, job_id):
        with self.lock:
            folder = self.folder(job_id)
            result = self.read(folder)
            if result["state"] not in {"converted", "imported", "placed"}:
                raise ManagerError("output_not_ready", "Resolve-compatible output is not ready", 409)
            try:
                path = self.output_path(folder, result)
                return path.name, verified_bytes(path, result["video"]["size_bytes"], result["video"]["sha256"])
            except (ValueError, OSError) as exc:
                raise ManagerError("output_invalid", "Converted output is missing or changed", 409) from exc
