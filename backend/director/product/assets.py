"""Exact inventory removal. Unregistered files and user media are never cleanup targets."""
import hashlib
import json
import os
import re
import shutil
import stat
import threading
from typing import Literal
from pathlib import Path
from pydantic import Field, field_validator
from director.product.capabilities import StrictModel
from director.installations.verifier import assert_no_links
from director.models.validation import relative_file_path

class Asset(StrictModel):
    path: str
    size: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    models: list[str]
    kind: Literal["model", "cache"] = "model"
    @field_validator("path")
    @classmethod
    def safe(cls, value):
        if not re.fullmatch(r"[a-zA-Z0-9_./-]{1,220}", value) or any(part in {"", ".", ".."} for part in value.split("/")) or value.startswith("/"):
            raise ValueError("Unsafe inventory path")
        return relative_file_path(value)

class AssetInventory:
    def __init__(self, root: Path, assets: list[Asset], ownership_file: Path):
        self.root, self.assets, self.owner = root, assets, ownership_file
        self.lock = threading.RLock()
        paths = [a.path.casefold() for a in assets]
        if len(paths)!=len(set(paths)): raise ValueError("Conflicting destinations")
    def path(self, asset):
        assert_no_links(self.owner)
        if not self.owner.is_file(): raise ValueError("Missing ownership evidence")
        path = self.root / asset.path
        assert_no_links(path)
        if not path.resolve().is_relative_to(self.root.resolve()): raise ValueError("Outside owned root")
        return path
    def available(self, asset):
        try:
            info = self.path(asset).stat()
            return stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size==asset.size
        except (ValueError, OSError): return False
    def plan(self, model_id):
        related = [a for a in self.assets if model_id in a.models]
        if not related: raise ValueError("No owned inventory for model")
        exclusive = [a for a in related if a.models==[model_id]]
        missing = [a.path for a in related if not self.available(a)]
        detail = {"model_id":model_id, "files":[a.path for a in exclusive],
                  "shared_files":[a.path for a in related if a not in exclusive],
                  "reclaim_bytes":sum(a.size for a in exclusive if self.available(a)),
                  "blockers":["Inventory missing, changed or unsafe"] if missing else [],
                  "preserves":["Generated videos", "Runtime software", "Unrelated files", "Referenced shared assets"]}
        detail["digest"] = hashlib.sha256(json.dumps(detail,sort_keys=True).encode()).hexdigest()
        return detail
    def remove(self, model_id, digest, confirmed):
        with self.lock:
            plan = self.plan(model_id)
            if not confirmed or plan["blockers"] or digest!=plan["digest"]: raise ValueError("Fresh explicit removal review required")
            exclusive = [a for a in self.assets if a.models==[model_id]]
            # Verify all hashes before any mutation. This never follows links or accepts request paths.
            identities = {}
            for asset in exclusive:
                path = self.path(asset); before=path.stat(); checksum=hashlib.sha256()
                with path.open("rb") as stream:
                    opened=os.fstat(stream.fileno())
                    if (opened.st_ino,opened.st_dev)!=(before.st_ino,before.st_dev): raise ValueError("Asset changed")
                    while chunk:=stream.read(1024*1024): checksum.update(chunk)
                after=path.stat()
                identity=lambda i:(i.st_ino,i.st_dev,i.st_size,i.st_mtime_ns)
                if identity(before)!=identity(after) or checksum.hexdigest()!=asset.sha256: raise ValueError("Asset integrity changed")
                identities[asset.path]=identity(after)
            staged=[]
            try:
                for asset in exclusive:
                    path=self.path(asset)
                    info=path.stat()
                    if (info.st_ino,info.st_dev,info.st_size,info.st_mtime_ns)!=identities[asset.path]: raise ValueError("Asset changed")
                    target=path.with_name(path.name+".director-removing")
                    if target.exists(): raise ValueError("Existing removal transaction needs inspection")
                    path.rename(target); staged.append((path,target))
            except Exception:
                for path,target in reversed(staged):
                    if not path.exists(): target.rename(path)
                raise
            # Shared assets lose only this model reference. Files with other references survive.
            for asset in self.assets:
                if model_id in asset.models: asset.models.remove(model_id)
            for _,target in staged: target.unlink()
            self.assets=[a for a in self.assets if a not in exclusive]
            return {"removed":True, "reclaimed_bytes":plan["reclaim_bytes"], "shared_preserved":plan["shared_files"]}
    def cleanup_plan(self):
        eligible=[a for a in self.assets if a.kind=="cache" and not a.models]
        detail={"files":[a.path for a in eligible],"reclaim_bytes":sum(a.size for a in eligible if self.available(a)),
                "blockers":["Registered cache integrity/ownership changed"] if any(not self.available(a) for a in eligible) else [],
                "shared_preserved":[a.path for a in self.assets if a.models],
                "unknown_files_preserved":True}
        detail["digest"]=hashlib.sha256(json.dumps(detail,sort_keys=True).encode()).hexdigest()
        return detail
    def cleanup(self,digest,confirmed):
        with self.lock:
            plan=self.cleanup_plan()
            if not confirmed or digest!=plan["digest"] or plan["blockers"]: raise ValueError("Fresh cache review required")
            eligible=[a for a in self.assets if a.kind=="cache" and not a.models]
            if not eligible: return {"removed":True,"reclaimed_bytes":0,"shared_preserved":plan["shared_preserved"]}
            for asset in eligible: asset.models=["__unused_cache__"]
            try: return self.remove("__unused_cache__",self.plan("__unused_cache__")["digest"],True)
            finally:
                for asset in eligible:
                    if asset.models==["__unused_cache__"]: asset.models=[]


def directory_size(path: Path, limit=100000):
    total=0; count=0; warnings=[]
    if not path.exists(): return {"bytes":0,"complete":True,"warnings":[]}
    stack=[path]
    while stack:
        folder=stack.pop()
        try:
            assert_no_links(folder)
            with os.scandir(folder) as entries:
                for item in entries:
                    count+=1
                    if count>limit: return {"bytes":total,"complete":False,"warnings":["Inventory limit reached"]}
                    info=item.stat(follow_symlinks=False)
                    if item.is_symlink() or getattr(info,"st_file_attributes",0)&0x400:
                        warnings.append("Linked item excluded"); continue
                    if stat.S_ISDIR(info.st_mode): stack.append(Path(item.path))
                    elif stat.S_ISREG(info.st_mode): total+=info.st_size
        except (ValueError,OSError): warnings.append("Unreadable item excluded")
    return {"bytes":total,"complete":not warnings,"warnings":list(set(warnings))}
