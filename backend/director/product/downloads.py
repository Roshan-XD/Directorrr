"""Data-only repository downloads. A completed download never becomes runnable."""
import hashlib
import json
import shutil
import threading
import os
import time
from uuid import uuid4
from pathlib import Path
from pydantic import Field
from director.product.capabilities import StrictModel
from director.models.schemas import ModelComponent
from director.installations.schemas import ManagerError, Cancelled, now
from director.installations.storage import ModelStorageManager
from director.installations.downloader import HuggingFaceDownloader
from director.installations.verifier import ArtifactVerifier, assert_no_links

class Selection(StrictModel):
    repository: str = Field(max_length=193)
    files: list[str] = Field(min_length=1, max_length=32)

class StartDownload(Selection):
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirmed: bool
    accepted_license: bool

class DownloadManager:
    def __init__(self, root, discovery, transport=None, events=None):
        self.storage=ModelStorageManager(root)
        self.discovery=discovery
        self.events=events or (lambda *args:None)
        self.transport=transport or HuggingFaceDownloader(enabled=os.environ.get("DIRECTOR_ENABLE_REPOSITORY_DOWNLOADS")=="1")
        self.lock=threading.RLock(); self.jobs={}; self.cancel_flags={}; self.threads=[];self.samples={}
        record=self.storage.path("downloads.json")
        if record.exists():
            self.storage.ensure_owned()
            values=self.storage.read_json(record)
            if not isinstance(values,list) or len(values)>100: raise ValueError("Invalid download history")
            for job in values:
                if not isinstance(job,dict) or not __import__('re').fullmatch(r"[0-9a-f]{32}",str(job.get("id"))):
                    raise ValueError("Invalid download job")
                if job["state"] in {"queued","downloading","verifying","installing"}:
                    job.update(state="failed",message="Interrupted; retry requires a new review. No automatic resume.")
                self.jobs[job["id"]]=job
    def _save(self):
        if len(json.dumps(list(self.jobs.values())).encode())>3*1024*1024:raise ManagerError("history_full","Download metadata limit reached",409)
        self.storage.ensure_owned()
        self.storage.write_json(self.storage.path("downloads.json"),list(self.jobs.values()))
    def snapshot(self):
        with self.lock: return {"jobs":json.loads(json.dumps(list(self.jobs.values()))),"real_downloads_enabled":self.transport.is_real and self.transport.enabled}
    def plan(self, selection):
        card=self.discovery.details(selection.repository)
        blockers=[]; components=[]
        if card.get("gated"): blockers.append("Gated repositories require a separately reviewed authenticated access route.")
        if card.get("cached"): blockers.append("Offline metadata cannot authorize a new transfer.")
        if card.get("license_state")!="known_permissive_declaration": blockers.append("License grant requires review; declaration is not download permission.")
        if len(set(selection.files))!=len(selection.files): raise ManagerError("duplicate_file","Select each file once",422)
        available={f["name"]:f for f in card["files"]}
        for index,name in enumerate(selection.files):
            f=available.get(name)
            if not f: raise ManagerError("file_not_found","Selected file is not in the pinned inventory",422)
            try:
                c=ModelComponent(id=f"file-{index}",role="config",repository_id=selection.repository,
                    pinned_revision=card["revision"],filename=name,destination=f"checkpoints/file-{index}.data",
                    expected_size_bytes=f["size"],sha256=f["sha256"])
            except ValueError as exc: raise ManagerError("unsafe_artifact","Invalid selected artifact path or metadata",422) from exc
            if not c.sha256 or not c.expected_size_bytes: blockers.append(f"Missing exact size/published SHA-256: {name}")
            components.append(c.model_dump(mode="json"))
        # A license declaration alone is insufficient. Capture the pinned accompanying text.
        license_text=None; license_file=next((f["name"] for f in card["files"] if f["name"] in {"LICENSE","LICENSE.txt","LICENSE.md"}),None)
        if license_file:
            try:
                license_text=self.discovery.fetch(f"/{selection.repository}/raw/{card['revision']}/{license_file}")
                if not isinstance(license_text,str) or not 0<len(license_text.encode())<=128*1024: license_text=None
            except Exception: license_text=None
        if not license_text: blockers.append("Pinned accompanying license text is unavailable.")
        total=sum(c["expected_size_bytes"] or 0 for c in components)
        if self.transport.is_real and not self.transport.enabled: blockers.append("Real repository downloads are disabled; separate weight approval is required.")
        result={"repository":selection.repository,"revision":card["revision"],"components":components,
            "total_bytes":total,"required_free_bytes":total*2+16*1024*1024,"destination":"Director-owned repository data; never a runtime model directory",
            "license":card["license"],"license_text":license_text,"license_sha256":hashlib.sha256(license_text.encode()).hexdigest() if license_text else None,
            "blockers":blockers,"warnings":["No adapter is installed. Repository code is never executed.","Published license declaration is not an independent legal opinion."],"runnable":False}
        result["digest"]=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
        return result
    def start(self, body):
        with self.lock:
            if not body.confirmed or not body.accepted_license: raise ManagerError("confirmation_required","Review and explicitly acknowledge the exact plan/license",422)
            plan=self.plan(body)
            if plan["digest"]!=body.digest: raise ManagerError("plan_changed","Plan changed; review again",409)
            if plan["blockers"]: raise ManagerError("download_blocked",plan["blockers"][0],409)
            if any(j["state"] in {"queued","downloading","verifying","installing"} for j in self.jobs.values()): raise ManagerError("download_active","Another download is active",409)
            if len(self.jobs)>=100: raise ManagerError("history_full","Download history limit reached",409)
            self.storage.ensure_owned(); self.storage.check_space(plan["required_free_bytes"])
            job={"id":uuid4().hex,"repository":body.repository,"revision":plan["revision"],"state":"queued","message":"Explicitly confirmed data download", "candidate_bytes":0,"verified_bytes":0,"total_bytes":plan["total_bytes"],"created":now(),"plan":plan,"runnable":False,"speed_bytes_per_second":None,"eta_seconds":None}
            job["license_acknowledgement"]={"accepted":True,"sha256":plan["license_sha256"],"revision":plan["revision"],"at":now()}
            if len(json.dumps([*self.jobs.values(),job]).encode())>3*1024*1024:raise ManagerError("history_full","Download metadata limit reached",409)
            self.jobs[job["id"]]=job; self.cancel_flags[job["id"]]=threading.Event()
            try:self._save()
            except Exception:
                self.jobs.pop(job["id"]);self.cancel_flags.pop(job["id"]);raise
            thread=threading.Thread(target=self._run,args=(job["id"],),daemon=True);self.threads.append(thread);thread.start()
            return json.loads(json.dumps(job))
    def _update(self, job, **values):
        with self.lock:
            if values.get("state") and values["state"]!=job["state"]:
                self.events("download",values.get("message",values["state"]),"error" if values["state"]=="failed" else "info")
            if "candidate_bytes" in values:
                timestamp=time.monotonic();previous=self.samples.get(job["id"])
                if previous and timestamp-previous[0]>=.5 and values["candidate_bytes"]>previous[1]:
                    speed=(values["candidate_bytes"]-previous[1])/(timestamp-previous[0])
                    values.update(speed_bytes_per_second=speed,eta_seconds=max(0,job["total_bytes"]-values["candidate_bytes"])/speed)
                if previous is None or timestamp-previous[0]>=.5:self.samples[job["id"]]=(timestamp,values["candidate_bytes"])
            if values.get("state") in {"verifying","completed","failed","cancelled"}: values.update(speed_bytes_per_second=None,eta_seconds=None)
            job.update(values);self._save()
    def _run(self, job_id):
        job=self.jobs[job_id]; cancel=self.cancel_flags[job_id]
        try:
            stage=self.storage.path("downloads",job_id);stage.mkdir(parents=True)
            cache=self.storage.path("cache",job_id);cache.mkdir(parents=True)
            components=[ModelComponent.model_validate(c) for c in job["plan"]["components"]]
            allowlist={(c.repository_id,c.pinned_revision,c.filename) for c in components}
            verifier=ArtifactVerifier();verified=0
            for index,c in enumerate(components):
                self.storage.check_space(c.expected_size_bytes*2)
                self._update(job,state="downloading",message=f"Downloading {index+1}/{len(components)}")
                source=self._transport_for(job).fetch(c,cache,cancel,lambda n:self._update(job,candidate_bytes=verified+n),allowlist)
                # SDK snapshots can be private-cache links; verify the contained regular blob.
                if source.is_symlink():
                    if not source.resolve().is_relative_to(cache.resolve()): raise ManagerError("unsafe_cache","Snapshot escapes owned cache",409)
                    source=source.resolve()
                self._update(job,state="verifying",message="Verifying exact bytes and SHA-256")
                if not verifier.verify(source,c,cancel).valid: raise ManagerError("integrity_failed","Artifact verification failed",409)
                target=stage/f"file-{index}.data";assert_no_links(target)
                with source.open("rb") as incoming, target.open("xb") as outgoing: shutil.copyfileobj(incoming,outgoing)
                if not verifier.verify(target,c,cancel).valid: raise ManagerError("copy_failed","Stored copy failed verification",409)
                verified+=c.expected_size_bytes; self._update(job,verified_bytes=verified)
            if cancel.is_set(): raise Cancelled()
            self._activate(job, components, stage, cancel)
            self._update(job,state="completed",message="Ready — verified H3 files registered; first generation remains experimental" if job["plan"].get("model_id") else "Data verified; no generation adapter or runtime installed")
        except Cancelled: self._update(job,state="cancelled",message="Cancelled; partial data remains isolated")
        except Exception as exc:
            from director.installations.downloader import transfer_details
            detail=getattr(exc,"technical_details",None) or transfer_details(exc)
            self._update(job,state="failed",message=exc.message if isinstance(exc,ManagerError) else "Download failed; isolated partial data preserved",technical_details=detail)
            self.events("download",detail,"error")
    def _activate(self, job, components, stage, cancel):
        """Generic repository data stays inert. Reviewed adapters may activate it."""
    def _transport_for(self, job):
        return self.transport
    def cancel(self, job_id):
        with self.lock:
            if job_id not in self.jobs: raise ManagerError("job_not_found","Download job not found",404)
            if job_id in self.cancel_flags: self.cancel_flags[job_id].set()
            return self.jobs[job_id]
    def removal_plan(self, job_id):
        with self.lock:
            job=self.jobs.get(job_id)
            if not job: raise ManagerError("job_not_found","Download job not found",404)
            if job["state"] not in {"completed","failed","cancelled"}: raise ManagerError("download_active","Stop the download before removal",409)
            folder=self.storage.path("downloads",job_id)
            files=[]
            if folder.exists():
                expected={f"file-{i}.data" for i in range(len(job["plan"]["components"]))}
                for path in folder.iterdir():
                    assert_no_links(path)
                    if path.name not in expected or not path.is_file() or path.stat().st_nlink!=1: raise ManagerError("unowned_files","Unknown download data blocks removal",409)
                    digest=hashlib.sha256()
                    with path.open("rb") as stream:
                        for chunk in iter(lambda:stream.read(1024*1024),b""):digest.update(chunk)
                    files.append({"name":path.name,"bytes":path.stat().st_size,"sha256":digest.hexdigest()})
            result={"job_id":job_id,"files":files,"reclaim_bytes":sum(f["bytes"] for f in files),"preserves":["Installed models","Generated media","Private SDK cache (separate review)"]}
            result["digest"]=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest();return result
    def remove(self, job_id, digest):
        with self.lock:
            plan=self.removal_plan(job_id)
            if plan["digest"]!=digest:raise ManagerError("plan_changed","Download data changed; review again",409)
            folder=self.storage.path("downloads",job_id)
            for file in plan["files"]:(folder/file["name"]).unlink()
            if folder.exists():folder.rmdir()
            self.jobs[job_id].update(state="cancelled",message="Data removed explicitly; model and media preserved")
            self._save();return {"removed":True,"reclaimed_bytes":plan["reclaim_bytes"],"shared_preserved":plan["preserves"]}
    def close(self):
        for flag in self.cancel_flags.values(): flag.set()
        for thread in self.threads: thread.join(timeout=15)
        self.storage.close()
