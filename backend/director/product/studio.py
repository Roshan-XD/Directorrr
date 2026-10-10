"""Owned creative metadata and media copies; never executes uploaded/model code."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import Field, field_validator
from director.product.capabilities import StrictModel, CreativeRequest, Shot
from director.installations.schemas import ManagerError, now
from director.installations.storage import ModelStorageManager
from director.installations.verifier import assert_no_links

MAX_MEDIA = 64 * 1024 * 1024
MEDIA_TYPES = {".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg",
               ".webm":"video/webm", ".mp4":"video/mp4", ".wav":"audio/wav"}

class Project(StrictModel):
    id: str = Field(pattern=r"^[0-9a-f]{32}$")
    name: str = Field(default="Untitled project", min_length=1, max_length=80)
    updated: str = Field(default_factory=now)
    draft: dict = {}
    shots: list[dict] = Field(default_factory=list, max_length=12)
    favorites: list[str] = Field(default_factory=list, max_length=100)
    presets: list[dict] = Field(default_factory=list, max_length=40)
    references: list[str] = Field(default_factory=list, max_length=12)
    @field_validator("favorites", "references")
    @classmethod
    def bounded_identities(cls,value,info):
        if any(not 0<len(v)<=193 or any(ord(c)<32 for c in v) for v in value):raise ValueError("Invalid saved identity")
        if info.field_name=="references" and any(not re.fullmatch(r"[0-9a-f]{32}",v) for v in value):raise ValueError("Invalid asset reference")
        if len(set(value))!=len(value):raise ValueError("Duplicate saved identity")
        return value
    @field_validator("draft", "shots", "presets")
    @classmethod
    def bounded_settings(cls, value):
        if len(json.dumps(value).encode()) > 64*1024:
            raise ValueError("Project settings exceed the limit")
        return value
    @field_validator("draft")
    @classmethod
    def validate_draft(cls,value):
        if value:
            # Empty prompts are valid unfinished drafts; only CreativeRequest fields persist.
            CreativeRequest.model_validate({**value,"prompt":value.get("prompt") or "Draft"})
        return value
    @field_validator("presets")
    @classmethod
    def validate_presets(cls,value):
        for preset in value:
            if set(preset)!={"name","settings"} or not isinstance(preset["name"],str) or not 0<len(preset["name"])<=80: raise ValueError("Invalid preset")
            CreativeRequest.model_validate({**preset["settings"],"prompt":preset["settings"].get("prompt") or "Draft"})
        return value
    @field_validator("shots")
    @classmethod
    def validate_shots(cls,value):
        for shot in value:
            if set(shot)!={"id","settings","notes","previousJob"} or type(shot["id"]) is not int or not isinstance(shot["notes"],str) or len(shot["notes"])>2000:
                raise ValueError("Invalid planned shot")
            if shot["previousJob"] and not re.fullmatch(r"[0-9a-f]{32}",str(shot["previousJob"])):raise ValueError("Invalid previous job")
            CreativeRequest.model_validate({**shot["settings"],"prompt":shot["settings"].get("prompt") or "Draft"})
        return value

class Media(StrictModel):
    id: str = Field(pattern=r"^[0-9a-f]{32}$")
    title: str = Field(min_length=1, max_length=160)
    filename: str
    type: Literal["image", "video", "audio"]
    origin: Literal["input", "output"]
    created: str = Field(default_factory=now)
    bytes: int = Field(gt=0, le=MAX_MEDIA)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    extension: Literal[".png", ".jpg", ".jpeg", ".webm", ".mp4", ".wav"]
    project_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    job_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    model_id: str | None = None
    favorite: bool = False
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    codec: str | None = None
    thumbnail: bool = False

PROBE = r'''
import av,json,sys
from pathlib import Path
p,t=map(Path,sys.argv[1:])
with av.open(str(p)) as c:
 v=next(iter(c.streams.video),None)
 a=next(iter(c.streams.audio),None)
 s=v or a
 if not s: raise ValueError('No media stream')
 suffix=p.suffix.lower()
 if suffix in ('.png','.jpg','.jpeg') and (not v or v.codec_context.name not in ('png','mjpeg')): raise ValueError('Wrong image format')
 if suffix=='.wav' and (v or not a or 'wav' not in c.format.name): raise ValueError('Wrong audio format')
 if suffix=='.mp4' and (not v or 'mov' not in c.format.name): raise ValueError('Wrong video container')
 if suffix=='.webm' and (not v or 'webm' not in c.format.name): raise ValueError('Wrong video container')
 result={'width':v.width if v else None,'height':v.height if v else None,
 'duration':float(c.duration/av.time_base) if c.duration else None,
 'codec':s.codec_context.name,'thumbnail':False}
 if v:
  if not 0<v.width<=4096 or not 0<v.height<=4096: raise ValueError('Unsafe geometry')
  frame=next(c.decode(video=0))
  image=frame.to_image(); image.thumbnail((480,270)); image.save(str(t),'JPEG')
  result['thumbnail']=True
 else: next(c.decode(audio=0))
 print(json.dumps(result))
'''

class StudioStore:
    def __init__(self, root: Path, project_root: Path, probe=None):
        self.storage=ModelStorageManager(root)
        self.root=project_root
        self.lock=threading.RLock()
        self.probe=probe or self._probe
        self.state={"version":1,"current":"0"*32,"projects":[Project(id="0"*32).model_dump()],"media":[],"history":[]}
        path=self.storage.path("studio.json")
        if path.exists():
            self.storage.ensure_owned()
            data=self.storage.read_json(path)
            if data.get("version")!=1 or len(data.get("projects",[]))>50 or len(data.get("media",[]))>500 or len(data.get("history",[]))>500:
                raise ManagerError("studio_corrupted","Studio metadata requires recovery; existing media preserved",409)
            data["projects"]=[Project.model_validate(p).model_dump() for p in data["projects"]]
            data["media"]=[Media.model_validate(p).model_dump() for p in data["media"]]
            if len({p["id"] for p in data["projects"]})!=len(data["projects"]) or len({a["id"] for a in data["media"]})!=len(data["media"]):
                raise ManagerError("studio_corrupted","Duplicate metadata identities",409)
            if not any(p["id"]==data.get("current") for p in data["projects"]):
                raise ManagerError("studio_corrupted","Current project is missing",409)
            self.state=data
            for job in self.state["history"]:
                if job.get("state") in {"queued","running"}:
                    job.update(state="failed",tracking_warning="Interrupted prior session; no automatic retry or submission.")

    def close(self): self.storage.close()
    def _save(self):
        if len(json.dumps(self.state).encode())>2*1024*1024:
            raise ManagerError("studio_full","Project metadata limit reached",409)
        self.storage.ensure_owned()
        current=self.storage.path("studio.json")
        if current.exists(): self.storage.write_json(self.storage.path("studio.previous.json"),self.storage.read_json(current))
        self.storage.write_json(self.storage.path("studio.json"),self.state)
    def snapshot(self):
        with self.lock: return json.loads(json.dumps(self.state))
    def save_project(self, project: Project, select=True):
        with self.lock:
            if any(ref not in {a["id"] for a in self.state["media"]} for ref in project.references):
                raise ManagerError("invalid_reference","Reference is not in the Library",422)
            projects=[p for p in self.state["projects"] if p["id"]!=project.id]
            if len(projects)>=50: raise ManagerError("project_limit","Archive a project before creating another",409)
            project.updated=now(); self.state["projects"]=[project.model_dump(),*projects]
            if select: self.state["current"]=project.id
            self._save();return self.snapshot()
    def media(self, asset_id):
        item=next((a for a in self.state["media"] if a["id"]==asset_id),None)
        if not item: raise ManagerError("asset_not_found","Asset not found",404)
        return Media.model_validate(item)
    def path(self, asset_id, thumbnail=False):
        asset=self.media(asset_id)
        path=self.storage.path("media",asset.id,"thumbnail.jpg" if thumbnail else "original"+asset.extension)
        assert_no_links(path)
        if not path.is_file() or path.stat().st_nlink!=1:
            raise ManagerError("asset_missing","Library file is missing or unsafe",409)
        if not thumbnail and path.stat().st_size!=asset.bytes:
            raise ManagerError("asset_changed","Library file size changed",409)
        if not thumbnail:
            digest=hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b""):digest.update(chunk)
            if digest.hexdigest()!=asset.sha256:raise ManagerError("asset_changed","Library integrity changed",409)
        return path
    def _probe(self,path,thumbnail):
        python=self.root/"runtime/windows-dev-001/venv/Scripts/python.exe"
        assert_no_links(python)
        if not python.is_file(): raise ManagerError("media_probe_unavailable","Private media decoder is unavailable",503)
        try:
            env={k:v for k,v in os.environ.items() if k not in {"DIRECTOR_MANAGER_TOKEN","DIRECTOR_LAUNCHER_TOKEN"}}
            result=subprocess.run([str(python),"-I","-c",PROBE,str(path),str(thumbnail)],capture_output=True,text=True,timeout=20,shell=False,env=env)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ManagerError("media_probe_failed","Media inspection timed out or was unavailable",422) from exc
        if result.returncode: raise ManagerError("invalid_media","This file could not be safely decoded",422)
        try: return json.loads(result.stdout)
        except ValueError as exc: raise ManagerError("invalid_media","Invalid media inspection report",422) from exc
    def add(self, data: bytes, filename: str, *, origin="input", job_id=None, model_id=None, project_id=None):
        # No incoming paths: filenames are display-only and storage is ID-associated.
        suffix=Path(filename).suffix.lower()
        if suffix not in MEDIA_TYPES or len(filename)>160 or any(c in filename for c in "/\\:\x00") or not data or len(data)>MAX_MEDIA:
            raise ManagerError("invalid_media","Use a supported image, video or WAV file under 64 MiB",422)
        with self.lock:
            if len(self.state["media"])>=500: raise ManagerError("library_full","Library limit reached",409)
            self.storage.ensure_owned();self.storage.check_space(len(data)*2)
            asset_id=uuid4().hex
            folder=self.storage.path("media",asset_id);folder.mkdir(parents=True)
            target=folder/("original"+suffix);target.write_bytes(data)
            try:
                metadata=self.probe(target,folder/"thumbnail.jpg")
                asset=Media(id=asset_id,title=filename,filename=filename,type=MEDIA_TYPES[suffix].split("/")[0],origin=origin,
                            bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),extension=suffix,
                            project_id=project_id or self.state["current"],job_id=job_id,model_id=model_id,**metadata)
                self.state["media"].insert(0,asset.model_dump());self._save()
                return asset
            except Exception:
                self.state["media"]=[a for a in self.state["media"] if a["id"]!=asset_id]
                # Remove only our two exact newly created files; never recursively delete unknown additions.
                for name in ("original"+suffix,"thumbnail.jpg"):
                    path=folder/name;assert_no_links(path)
                    if path.exists(): path.unlink()
                if not any(folder.iterdir()): folder.rmdir()
                raise
    def record_job(self, job, source=None):
        with self.lock:
            value=job.model_dump(mode="json")
            value["input_references"]=[] # Current validated Wan adapter is text-only.
            value["artifact_revisions"]=None
            if (job.creative or {}).get("model_id") == "minimax-h3-optimized":
                from director.product.optimized_h3 import recipe
                value["artifact_revisions"]=[{k:c[k] for k in ("repository_id","pinned_revision","filename","sha256")} for c in recipe(self.root)["components"]]
            if (job.creative or {}).get("model_id","wan21-t2v-13b")=="wan21-t2v-13b":
                for manifest in (self.root/"model_registry").glob("wan*.json"):
                    if manifest.stat().st_size>512*1024:continue
                    data=json.loads(manifest.read_text())
                    value["artifact_revisions"]=[{k:c.get(k) for k in ("repository_id","pinned_revision","filename","sha256")} for c in data.get("components",[])]
                    break
            prior=next((j for j in self.state["history"] if j["id"]==job.id),None)
            if prior and prior.get("state")==job.state and (not source or any(a.get("job_id")==job.id for a in self.state["media"])): return
            value["project_id"]=prior.get("project_id") if prior else self.state["current"]
            value["updated"]=now();value["created"]=prior.get("created") if prior else now()
            self.state["history"]=[value,*[j for j in self.state["history"] if j["id"]!=job.id]][:500]
            if source and not any(a.get("job_id")==job.id for a in self.state["media"]):
                if isinstance(source,tuple):
                    filename,data=source
                    self.add(data,filename,origin="output",job_id=job.id,model_id=(job.creative or {}).get("model_id","wan21-t2v-13b"),project_id=value["project_id"])
                    self._save()
                    return
                assert_no_links(source)
                before=source.stat()
                if before.st_nlink!=1 or not 0<before.st_size<=MAX_MEDIA: raise ManagerError("unsafe_output","Unsafe generated asset",409)
                data=source.read_bytes()
                after=source.stat()
                if (after.st_ino,after.st_dev,after.st_size,after.st_mtime_ns)!=(before.st_ino,before.st_dev,before.st_size,before.st_mtime_ns):
                    raise ManagerError("output_changed","Generated output changed",409)
                self.add(data,source.name,origin="output",job_id=job.id,model_id=(job.creative or {}).get("model_id","wan21-t2v-13b"),project_id=value["project_id"])
            self._save()
    def edit(self, asset_id, *, title=None, favorite=None):
        with self.lock:
            asset=self.media(asset_id)
            if title is not None: asset.title=title
            if favorite is not None: asset.favorite=favorite
            asset=Media.model_validate(asset.model_dump())
            self.state["media"]=[asset.model_dump() if a["id"]==asset_id else a for a in self.state["media"]]
            self._save();return asset
    def delete(self, asset_id, confirmed=False):
        if confirmed is not True: raise ManagerError("confirmation_required","Confirm Library copy deletion",422)
        with self.lock:
            if any(asset_id in p["references"] for p in self.state["projects"]):
                raise ManagerError("asset_in_use","This asset is referenced by a project",409)
            asset=self.media(asset_id);path=self.path(asset_id)
            if hashlib.sha256(path.read_bytes()).hexdigest()!=asset.sha256:
                raise ManagerError("asset_changed","Library integrity changed; deletion blocked",409)
            folder=path.parent
            allowed={path.name,"thumbnail.jpg"}
            if any(p.name not in allowed or p.is_symlink() or p.stat().st_nlink!=1 for p in folder.iterdir()):
                raise ManagerError("unowned_files","Unknown Library files; deletion blocked",409)
            for file in folder.iterdir(): assert_no_links(file)
            for file in folder.iterdir(): file.unlink()
            folder.rmdir()
            self.state["media"]=[a for a in self.state["media"] if a["id"]!=asset_id]
            self._save();return {"deleted":True,"original_generation_preserved":True}

