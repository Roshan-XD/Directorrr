import os
import re
import stat
import threading
import time
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

from director.installations.schemas import ManagerError
from director.installations.verifier import assert_no_links


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    prompt: str = Field(min_length=1, max_length=2000)
    # JavaScript can represent these seed values exactly.
    seed: int = Field(default=20261009, ge=0, le=9007199254740991)

    @field_validator("prompt")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Prompt cannot be blank")
        return value


class GenerationJob(BaseModel):
    id: str
    state: Literal["queued", "running", "completed", "failed", "cancelled"] = "queued"
    comfy_prompt_id: str | None = None
    progress: float | None = None
    message: str = "Waiting for ComfyUI"
    output_filename: str | None = None
    output_url: str | None = None
    development_only: bool = True
    creative: dict | None = None


def build_workflow(prompt: str, seed: int, job_id: str) -> dict:
    """Stage 7's successful workflow; callers cannot supply nodes or settings."""
    body = GenerationRequest(prompt=prompt, seed=seed)
    if not body.prompt.strip() or not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ValueError("Invalid prompt or job identity")
    return {
        "37": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.1_t2v_1.3B_fp16.safetensors", "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "39": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["38", 0], "text": body.prompt}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["38", 0], "text": "low quality, blurry, static, distorted, watermark, subtitles"}},
        "40": {"class_type": "EmptyHunyuanLatentVideo", "inputs": {"width": 320, "height": 192, "length": 17, "batch_size": 1}},
        "48": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["37", 0], "shift": 8.0}},
        "3": {"class_type": "KSampler", "inputs": {"model": ["48", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["40", 0], "seed": body.seed, "steps": 8, "cfg": 6.0, "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["39", 0]}},
        "47": {"class_type": "SaveWEBM", "inputs": {"images": ["8", 0], "filename_prefix": "Director_Stage8_" + job_id, "codec": "vp9", "fps": 16.0, "crf": 32.0}},
    }


class ComfyUIClient:
    def __init__(self, endpoint: str):
        url = urlsplit(endpoint)
        if (url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port
                or url.path not in {"", "/"} or url.query or url.fragment or url.username or url.password):
            raise ValueError("Development ComfyUI must be an explicit http://127.0.0.1:PORT origin")
        self.http = httpx.Client(base_url=endpoint.rstrip("/"), timeout=10, trust_env=False, follow_redirects=False)

    def request(self, path: str, body=None):
        try:
            with self.http.stream("POST" if body is not None else "GET", path, json=body) as response:
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 2 * 1024 * 1024:
                        raise ValueError("Response too large")
                import json
                result = json.loads(data)
                if not isinstance(result, dict):
                    raise ValueError("Expected object")
                return result
        except (httpx.HTTPError, ValueError) as error:
            # Never expose configured paths, request bodies or credentials in API errors.
            raise ManagerError("comfy_unavailable", "ComfyUI is unavailable or returned an invalid response", 502) from error

    def close(self):
        self.http.close()


class DevelopmentGeneration:
    """Small in-memory job adapter; model installation jobs remain independent."""
    def __init__(self, client, output_root: Path):
        if not output_root.is_absolute():
            raise ValueError("Configure an absolute approved development output directory")
        self.client = client
        self.output_root = output_root
        self.jobs: dict[str, GenerationJob] = {}
        self._lock = threading.RLock()
        self._submitted: dict[str, float] = {}
        self._uncertain = False
        self._cancel_requested: set[str] = set()

    def _queue(self):
        queue = self.client.request("/queue")
        if not all(isinstance(queue.get(key), list) for key in ("queue_running", "queue_pending")):
            raise ManagerError("invalid_queue", "ComfyUI returned an invalid queue", 502)
        return queue

    def start(self, body: GenerationRequest, *, settings: dict | None = None, creative: dict | None = None) -> GenerationJob:
        with self._lock:
            if self._uncertain:
                raise ManagerError("submission_uncertain", "Previous submission outcome is unknown. Inspect ComfyUI before restarting Director", 409)
            if any(j.state in {"queued", "running"} for j in self.jobs.values()):
                raise ManagerError("generation_active", "A development generation is already active", 409)
            queue = self._queue()
            if queue.get("queue_running") or queue.get("queue_pending"):
                raise ManagerError("comfy_busy", "ComfyUI already has queued work", 409)
            job = GenerationJob(id=uuid4().hex)
            workflow = build_workflow(body.prompt, body.seed, job.id)
            if settings is not None:
                from director.product.capabilities import CreativeRequest, load_capabilities
                approved = load_capabilities(Path(__file__).resolve().parents[3] / "model_registry/capabilities")
                parsed = CreativeRequest.model_validate(creative)
                expected = parsed.model_copy(update={"seed":body.seed}).resolve(next(c for c in approved if c.id == parsed.model_id))
                if settings != expected or body.prompt != expected["prompt"]:
                    raise ValueError("Unvalidated adapter settings")
                if parsed.model_id == "minimax-h3-optimized":
                    from director.generation.h3_workflow import build_h3_workflow
                    workflow = build_h3_workflow(body.prompt, body.seed, job.id, settings)
                else:
                    workflow["40"]["inputs"].update(width=settings["width"], height=settings["height"], length=settings["frames"])
                    workflow["3"]["inputs"].update(steps=settings["steps"], cfg=settings["cfg"])
                    workflow["48"]["inputs"]["shift"] = settings["shift"]
                    workflow["7"]["inputs"]["text"] = settings["negative_prompt"]
                job.creative = {**creative, **settings, "prompt":creative["prompt"]}
            # Retain only a bounded session history; never resubmit after restart.
            if len(self.jobs) >= 12:
                oldest = next(iter(self.jobs))
                self.jobs.pop(oldest)
                self._submitted.pop(oldest, None)
                self._cancel_requested.discard(oldest)
            self.jobs[job.id] = job
            try:
                result = self.client.request("/prompt", {"prompt": workflow, "client_id": "Director-stage8-dev"})
                if result.get("node_errors") or not re.fullmatch(r"[0-9a-f-]{36}", str(result.get("prompt_id", ""))):
                    raise ManagerError("workflow_rejected", "ComfyUI rejected the fixed development workflow", 502)
                job.comfy_prompt_id = result["prompt_id"]
                self._submitted[job.id] = time.monotonic()
            except ManagerError:
                job.state = "failed"
                job.message = "Submission failed; outcome may be unknown. Inspect ComfyUI before retrying."
                self._uncertain = True
                raise
            return job.model_copy(deep=True)

    def get(self, job_id: str) -> GenerationJob:
        with self._lock:
            if not re.fullmatch(r"[0-9a-f]{32}", job_id) or job_id not in self.jobs:
                raise ManagerError("generation_not_found", "Generation job not found", 404)
            job = self.jobs[job_id]
            if job.state not in {"queued", "running"}:
                return job.model_copy(deep=True)
            history = self.client.request("/history/" + job.comfy_prompt_id)
            entry = history.get(job.comfy_prompt_id)
            if entry is not None:
                if not isinstance(entry, dict) or not isinstance(entry.get("status"), dict):
                    raise ManagerError("invalid_history", "Invalid ComfyUI job history", 502)
                if entry["status"].get("status_str") != "success":
                    if job.id in self._cancel_requested and any(isinstance(m,list) and m and m[0]=="execution_interrupted" for m in entry["status"].get("messages",[])):
                        job.state, job.message = "cancelled", "Generation cancelled by ComfyUI"
                    else:
                        job.state, job.message = "failed", "ComfyUI execution failed; inspect the development server log"
                else:
                    try:
                        outputs = entry.get("outputs", {}).get("47", {})
                        files = outputs.get("images", []) + outputs.get("videos", [])
                        if len(files) != 1 or files[0].get("type") != "output" or files[0].get("subfolder", "") != "":
                            raise ValueError("Unexpected output inventory")
                        filename = files[0]["filename"]
                        extension = "mp4" if (job.creative or {}).get("model_id") == "minimax-h3-optimized" else "webm"
                        if not re.fullmatch(r"Director_Stage8_" + job.id + r"_\d+_\." + extension, filename):
                            raise ValueError("Unexpected output name")
                        self._read_output(filename)
                        job.output_filename = filename
                        job.output_url = f"/api/dev/generation/jobs/{job.id}/output"
                        job.state, job.message = "completed", "Video completed"
                    except (KeyError, TypeError, ValueError, OSError):
                        job.state, job.message = "failed", "Generated output is missing or unsafe"
            else:
                queue = self._queue()
                running = queue.get("queue_running", [])
                if any(isinstance(item, list) and len(item) > 1 and item[1] == job.comfy_prompt_id for item in running):
                    job.state, job.message = "running", "Generating video; step progress is not available"
                if time.monotonic() - self._submitted[job.id] > 1800:
                    job.state, job.message = "failed", "Tracking timed out; inspect ComfyUI before another submission"
                    self._uncertain = True
            return job.model_copy(deep=True)

    def cancel(self, job_id: str):
        """Delete only our pending item; interrupt only an exclusively owned active queue."""
        with self._lock:
            job = self.get(job_id)
            if job.state not in {"queued", "running"}:
                raise ManagerError("not_active", "This job is no longer active", 409)
            queue = self._queue()
            running = queue["queue_running"]
            owned = lambda item: isinstance(item, list) and len(item)>1 and item[1]==job.comfy_prompt_id
            if running:
                if len(running)!=1 or not owned(running[0]) or queue["queue_pending"]:
                    raise ManagerError("cancel_unsafe", "Cannot interrupt unrelated ComfyUI work", 409)
                self.client.request("/interrupt", {})
                self._cancel_requested.add(job_id)
                self.jobs[job_id].message = "Cancellation requested; waiting for ComfyUI to stop"
                # Do not claim cancellation, or permit a new submission, before history confirms it.
            else:
                if not any(owned(item) for item in queue["queue_pending"]):
                    raise ManagerError("cancel_uncertain", "Job state changed; refresh before cancelling", 409)
                self.client.request("/queue", {"delete":[job.comfy_prompt_id]})
                remaining = self._queue()
                if any(owned(item) for item in remaining["queue_pending"]+remaining["queue_running"]):
                    raise ManagerError("cancel_uncertain", "Cancellation has not been confirmed", 409)
                self.jobs[job_id].state = "cancelled"
                self.jobs[job_id].message = "Pending generation cancelled"
            return self.jobs[job_id].model_copy(deep=True)

    def forget(self, job_id: str):
        with self._lock:
            job = self.get(job_id)
            if job.state in {"queued", "running"}:
                raise ManagerError("generation_active", "Cannot remove an active job from history", 409)
            del self.jobs[job_id]
            self._submitted.pop(job_id, None)

    def _read_output(self, filename: str) -> bytes:
        if not re.fullmatch(r"Director_Stage8_[0-9a-f]{32}_\d+_\.(?:webm|mp4)", filename):
            raise ValueError("Unsafe filename")
        path = self.output_root / filename
        assert_no_links(path)
        if not path.resolve().is_relative_to(self.output_root.resolve()):
            raise ValueError("Outside approved output root")
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= 32 * 1024 * 1024:
            raise ValueError("Unsafe output file")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ValueError("Output changed")
            data = stream.read(32 * 1024 * 1024 + 1)
        assert_no_links(path)
        after = path.stat()
        identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
        container_valid = data[4:8] == b"ftyp" if filename.endswith(".mp4") else data.startswith(b"\x1a\x45\xdf\xa3")
        if identity(before) != identity(after) or len(data) != before.st_size or not container_valid:
            raise ValueError("Output changed or is not WebM")
        return data

    def output(self, job_id: str) -> tuple[str, bytes]:
        job = self.get(job_id)
        if job.state != "completed":
            raise ManagerError("output_not_ready", "Video is not completed", 409)
        try:
            return job.output_filename, self._read_output(job.output_filename)
        except (ValueError, OSError) as error:
            raise ManagerError("output_unavailable", "Video is missing or unsafe", 404) from error

    def close(self):
        self.client.close()
