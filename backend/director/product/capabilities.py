"""Declarative capabilities and bounded adapter controls, independent of installers."""
import secrets
import re
from urllib.parse import urlsplit
from pathlib import Path
from typing import Literal
from director.models.validation import repository_id, destination_path
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Workspace = Literal["text-to-video", "image-to-video", "reference-to-video", "first-last-frame", "sequence", "video-to-video", "text-to-image", "image-to-image", "reference-image", "inpainting", "audio-conditioned-video"]
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
class Resolution(StrictModel):
    id: str
    width: int = Field(ge=64, le=4096, multiple_of=16)
    height: int = Field(ge=64, le=4096, multiple_of=16)
    aspect: str
class Duration(StrictModel):
    seconds: int = Field(ge=1, le=30)
    frames: int = Field(ge=1, le=1000)
class Capability(StrictModel):
    schema_version: Literal[1] = 1
    id: str
    name: str
    repository: str
    manifest_id: str | None = Field(default=None,pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    license_source: str
    required_assets: list[str] = []
    adapter: str | None
    workspaces: list[Workspace]
    native_audio: bool = False
    continuation: Literal["none", "reference", "first-last", "native"] = "none"
    fps: int = Field(ge=1, le=60)
    frame_multiple: int = Field(ge=1)
    frame_offset: int = Field(ge=0)
    durations: list[Duration]
    resolutions: list[Resolution]
    qualities: dict[str, int]
    default_resolution: str
    default_duration: int
    evidence: list[str]
    blockers: list[str] = []
    @field_validator("repository")
    @classmethod
    def valid_repository(cls,value):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}",value):
            raise ValueError("Invalid repository identifier")
        return repository_id(value)
    @field_validator("license_source")
    @classmethod
    def authoritative_link(cls,value):
        source=urlsplit(value)
        if source.scheme!="https" or source.hostname not in {"huggingface.co","github.com","docs.comfy.org"} or source.username or source.password or source.port not in {None,443}:
            raise ValueError("License must be an authoritative HTTPS reference")
        return value
    @model_validator(mode="after")
    def consistent(self):
        if self.adapter and not self.required_assets:
            raise ValueError("An enabled adapter needs an exact component allowlist")
        if len(set(self.required_assets))!=len(self.required_assets) or any(not re.fullmatch(r"[A-Za-z0-9_./-]+",p) or any(v in {"", ".", ".."} for v in p.split("/")) for p in self.required_assets):
            raise ValueError("Invalid component allowlist")
        for component in self.required_assets: destination_path(component)
        if not self.workspaces or len(set(self.workspaces)) != len(self.workspaces):
            raise ValueError("Unique supported workspaces required")
        ids = [r.id for r in self.resolutions]
        if len(ids) != len(set(ids)) or self.default_resolution not in ids:
            raise ValueError("Invalid resolution defaults")
        seconds = [d.seconds for d in self.durations]
        if len(seconds) != len(set(seconds)) or self.default_duration not in seconds:
            raise ValueError("Invalid duration defaults")
        if any((d.frames-self.frame_offset) % self.frame_multiple for d in self.durations):
            raise ValueError("Invalid temporal grid")
        if not self.qualities or any(not 1 <= s <= 50 for s in self.qualities.values()):
            raise ValueError("Invalid quality steps")
        return self

class CreativeRequest(StrictModel):
    model_id: str = "wan21-t2v-13b"
    workspace: Workspace = "text-to-video"
    prompt: str = Field(min_length=1, max_length=1800)
    resolution: str = "preview"
    duration: int = Field(default=1, strict=True)
    quality: str = "Fast"
    seed: int | None = Field(default=None, ge=0, le=9007199254740991, strict=True)
    camera: Literal["none", "static", "pan-left", "pan-right", "push-in", "pull-out", "orbit"] = "none"
    steps: int | None = Field(default=None, ge=1, le=32, strict=True)
    cfg: float = Field(default=6, ge=1, le=10)
    shift: float = Field(default=8, ge=1, le=12)
    negative_prompt: str = Field(default="low quality, blurry, static, distorted, watermark, subtitles", max_length=2000)
    export_fps: int = Field(default=16, strict=True)
    def resolve(self, capability: Capability):
        if not capability.adapter or capability.blockers:
            raise ValueError("This model has no enabled Director adapter")
        if self.model_id != capability.id or self.workspace not in capability.workspaces:
            raise ValueError("Unsupported model/workspace combination")
        if not self.prompt.strip() or self.export_fps != capability.fps:
            raise ValueError("Blank prompt or unsupported export frame rate")
        resolution = next((r for r in capability.resolutions if r.id == self.resolution), None)
        duration = next((d for d in capability.durations if d.seconds == self.duration), None)
        if not resolution or not duration or self.quality not in capability.qualities:
            raise ValueError("Unsupported resolution, duration or quality")
        if capability.id == "minimax-h3-optimized" and self.steps not in {None, 20}:
            raise ValueError("The reviewed H3 recipe uses exactly 20 steps")
        camera = {"none":"", "static":"Static camera.", "pan-left":"Slow camera pan left.", "pan-right":"Slow camera pan right.", "push-in":"Gentle camera push in.", "pull-out":"Gentle camera pull out.", "orbit":"Slow camera orbit around the subject."}[self.camera]
        return {"width":resolution.width, "height":resolution.height, "frames":duration.frames,
                "fps":capability.fps, "steps":self.steps or capability.qualities[self.quality],
                "cfg":self.cfg, "shift":self.shift, "negative_prompt":self.negative_prompt,
                "prompt":self.prompt + ("\n" + camera if camera else ""),
                "seed":self.seed if self.seed is not None else secrets.randbelow(9007199254740992)}

class Shot(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,48}$")
    prompt: str = Field(min_length=1, max_length=1800)
    notes: str = Field(default="", max_length=2000)
    previous_job_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    continuation: Literal["none", "reference", "first-last", "native"] = "none"
    audio: Literal["none", "native", "separate-track"] = "none"
    def validate_for(self, capability: Capability):
        if self.continuation != "none" and self.continuation != capability.continuation:
            raise ValueError("Unsupported continuation")
        if self.audio == "native" and not capability.native_audio:
            raise ValueError("Native audio unavailable")
        if self.continuation != "none" and not self.previous_job_id:
            raise ValueError("Continuation requires an owned previous job")

def load_capabilities(root: Path) -> list[Capability]:
    values = [Capability.model_validate_json(p.read_text(encoding="utf-8")) for p in sorted(root.glob("*.json"))]
    if len({v.id for v in values}) != len(values):
        raise ValueError("Duplicate capability identity")
    return values
