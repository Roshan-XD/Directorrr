import re
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from director.installations.downloader import FixtureDownloader, HuggingFaceDownloader
from director.installations.licenses import LicenseAcknowledgementStore
from director.installations.schemas import (
    Cancelled, Job, ManagerError, Receipt, TERMINAL, manifest_digest, now,
)
from director.installations.storage import ModelStorageManager
from director.installations.verifier import ArtifactVerifier, assert_no_links
from director.models.schemas import ModelManifest
from director.models.planning import ArtifactReview, PlanIssue

TRANSITIONS = {
    "checking": {"downloading", "verifying", "installing", "failed", "cancelled"},
    "downloading": {"verifying", "failed", "cancelled"},
    "verifying": {"installing", "ready", "failed", "cancelled", "corrupted"},
    "installing": {"ready", "not_installed", "failed"},
}


class InstallationJobManager:
    def __init__(self, storage: ModelStorageManager, downloader=None, fixture_downloader=None):
        self.storage = storage
        self.downloader = downloader or HuggingFaceDownloader()
        self.fixture_downloader = fixture_downloader
        self.licenses = LicenseAcknowledgementStore(storage)
        self.verifier = ArtifactVerifier()
        self._mutex = threading.RLock()
        self._jobs: dict[str, Job] = {}
        self._cancels: dict[str, threading.Event] = {}
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="director-installation")
        self._closed = False
        if storage.base.exists():
            try:
                storage.ensure_owned()
                self.recover()
            except Exception:
                storage.close()
                self._executor.shutdown(wait=False)
                raise

    def _save(self, job: Job) -> None:
        job.updated_at = now()
        self.storage.write_json(self.storage.path("jobs", job.id + ".json"), job.model_dump(mode="json"))

    def _transition(self, job: Job, state: str) -> None:
        if state not in TRANSITIONS.get(job.state, set()):
            raise ManagerError("invalid_transition", f"Cannot transition {job.state} to {state}")
        job.state = state
        self._save(job)

    def get(self, job_id: str) -> Job:
        with self._mutex:
            if not re.fullmatch(r"[0-9a-f]{32}", job_id) or job_id not in self._jobs:
                raise ManagerError("job_not_found", "Installation job not found", 404)
            return self._jobs[job_id].model_copy(deep=True)

    def cancel(self, job_id: str) -> Job:
        with self._mutex:
            job = self._jobs.get(self.get(job_id).id)
            if job.state == "cancelled":
                return job.model_copy(deep=True)
            if job.state in TERMINAL or job.state == "installing":
                raise ManagerError("cancellation_too_late", "Job is complete or in its commit section", 409)
            job.cancel_requested = True
            self._cancels[job.id].set()
            self._save(job)
            return job.model_copy(deep=True)

    def _artifact_metadata_preflight(self, model: ModelManifest) -> None:
        if model.is_mock and not model.is_fixture:
            raise ManagerError("not_installable", "Legacy mocks have no installable files")
        if model.is_fixture:
            if self.fixture_downloader is None:
                raise ManagerError("fixtures_disabled", "Offline fixture mode is disabled")
        elif isinstance(self.downloader, HuggingFaceDownloader) and not self.downloader.enabled:
            raise ManagerError("real_downloads_disabled", "Real model downloads are disabled by default")
        if model.support_status == "unsupported" or not model.artifact_installation_reviewed or not model.components:
            raise ManagerError("unreviewed_artifacts", "Artifact/license inventory has not been approved for installation")
        if any(c.pinned_revision is None or c.expected_size_bytes is None or not c.sha256 for c in model.components):
            raise ManagerError("missing_integrity_metadata", "Every file needs a revision, exact size and SHA-256")
        self.licenses.requirements(model)

    def _artifact_preflight(self, model: ModelManifest, acknowledgement_id: str) -> None:
        self._artifact_metadata_preflight(model)
        self.licenses.check(model, acknowledgement_id)

    def artifact_review(self, model: ModelManifest, manager_key_configured: bool) -> ArtifactReview:
        """Read-only snapshot using the same gates as start; never records consent."""
        model = ModelManifest.model_validate(model.model_dump())
        total = (sum(c.expected_size_bytes for c in model.components)
                 if model.components and all(c.expected_size_bytes is not None for c in model.components) else None)
        blockers = []
        with self._mutex:
            try:
                self._artifact_metadata_preflight(model)
                if not manager_key_configured:
                    raise ManagerError("manager_key_missing", "Configure a local manager key before installing", 503)
                if self._closed:
                    raise ManagerError("manager_closed", "Installation manager is shutting down", 503)
                if any(job.state not in TERMINAL for job in self._jobs.values()):
                    raise ManagerError("installation_busy", "Another operation is active", 409)
                if self.storage.active(model.id) is not None:
                    raise ManagerError("already_installed", "Artifacts already exist; verify or remove them first", 409)
                self.storage.check_space((total or 0) * 3)
            except ManagerError as error:
                blockers.append(PlanIssue(code=error.code, message=error.message))
        return ArtifactReview(can_review=not blockers, blockers=blockers,
            expected_download_bytes=total,
            required_storage_bytes=None if total is None else total * 3 + self.storage.margin,
            destination_template=str(self.storage.base / "installed" / model.id / "<job-id>"))

    def start(self, model: ModelManifest, operation: str, expected_digest: str | None = None,
              acknowledgement_id: str | None = None) -> Job:
        model = ModelManifest.model_validate(model.model_dump())
        with self._mutex:
            if self._closed:
                raise ManagerError("manager_closed", "Installation manager is shutting down", 503)
            if any(job.state not in TERMINAL for job in self._jobs.values()):
                raise ManagerError("installation_busy", "Another operation is active; retry after it completes", 409)
            if operation == "install":
                if expected_digest != manifest_digest(model):
                    raise ManagerError("stale_manifest", "Manifest changed; inspect it again", 409)
                self._artifact_preflight(model, acknowledgement_id or "")
                if self.storage.active(model.id) is not None:
                    raise ManagerError("already_installed", "Installation already exists; verify or remove it first", 409)
                self.storage.check_space(sum(c.expected_size_bytes for c in model.components) * 3)
            elif operation in {"verify", "remove"}:
                receipt = self.storage.active(model.id)
                if receipt is None:
                    raise ManagerError("not_installed", "No active installation exists", 404)
                model = receipt.manifest
            else:
                raise ManagerError("unsupported_operation", "Operation is not implemented", 422)
            self.storage.ensure_owned()
            job = Job(id=uuid4().hex, model_id=model.id, operation=operation, manifest=model,
                      manifest_digest=manifest_digest(model), acknowledgement_id=acknowledgement_id,
                      total_expected_bytes=sum(c.expected_size_bytes or 0 for c in model.components))
            self._jobs[job.id] = job
            self._cancels[job.id] = threading.Event()
            self._save(job)
            self._executor.submit(self._run, job.id)
            return job.model_copy(deep=True)

    def _run(self, job_id: str) -> None:
        job, cancel = self._jobs[job_id], self._cancels[job_id]
        try:
            if cancel.is_set():
                raise Cancelled()
            if job.operation == "install":
                self._install(job, cancel)
            else:
                receipt = self.storage.active(job.model_id)
                if receipt is None:
                    raise ManagerError("not_installed", "Installation disappeared")
                if job.operation == "remove":
                    with self._mutex:
                        if cancel.is_set():
                            raise Cancelled()
                        self._transition(job, "installing")
                    self.storage.remove(receipt)
                    with self._mutex:
                        self._transition(job, "not_installed")
                else:
                    with self._mutex:
                        self._transition(job, "verifying")
                    results = self._verify_bundle(self.storage.installed(receipt.model_id, receipt.job_id), receipt.manifest, cancel)
                    with self._mutex:
                        job.verification = results
                        job.verified_bytes = sum(result.actual_size or 0 for result in results if result.valid)
                        if any(result.code in {"unreadable", "unsafe_file"} for result in results):
                            raise ManagerError("verification_unavailable", "Artifacts could not be safely inspected")
                        self._transition(job, "ready" if all(result.valid for result in results) else "corrupted")
            # A journal records intent; terminal job + active pointer are still rechecked on restart.
        except Cancelled:
            with self._mutex:
                self._transition(job, "cancelled")
        except Exception as error:
            with self._mutex:
                if job.state not in TERMINAL:
                    job.error = {"code": error.code if isinstance(error, ManagerError) else "operation_failed",
                                 "message": error.message if isinstance(error, ManagerError) else "Operation failed; inspect storage and retry"}
                    self._transition(job, "failed")
        finally:
            cancel.clear()

    def _verify_bundle(self, bundle: Path, model: ModelManifest, cancel: threading.Event):
        return [self.verifier.verify(self.storage.component_path(bundle, c.destination), c, cancel) for c in model.components]

    def _install(self, job: Job, cancel: threading.Event) -> None:
        model = job.manifest
        stage = self.storage.staging(job.id)
        cache = self.storage.path("hf-cache")
        stage.mkdir(parents=True, exist_ok=False)
        cache.mkdir(parents=True, exist_ok=True)
        allowlist = {(c.repository_id, c.pinned_revision, c.filename) for c in model.components}
        downloader = self.fixture_downloader if model.is_fixture else self.downloader
        completed = 0
        with self._mutex:
            self._transition(job, "downloading")
        for component in model.components:
            if cancel.is_set():
                raise Cancelled()
            remaining = job.total_expected_bytes - completed
            self.storage.check_space(remaining * 3)
            def progress(count):
                self.storage.check_space(remaining * 2)
                with self._mutex:
                    job.current_component = component.id
                    job.candidate_bytes = completed + min(count, component.expected_size_bytes)
                    self._save(job)
            source = downloader.fetch(component, cache, cancel, progress, allowlist)
            source = source.resolve()
            if not source.is_relative_to(cache.resolve()):
                raise ManagerError("unsafe_cache", "Transfer result is outside private cache")
            candidate_result = self.verifier.verify(source, component, cancel)
            if not candidate_result.valid:
                raise ManagerError("artifact_integrity_failed", "Transferred file failed size/hash verification")
            target = self.storage.component_path(stage, component.destination)
            target.parent.mkdir(parents=True, exist_ok=True)
            self.storage.check_space(remaining)
            assert_no_links(target)
            with source.open("rb") as incoming, target.open("xb") as outgoing:
                while chunk := incoming.read(1024 * 1024):
                    if cancel.is_set():
                        raise Cancelled()
                    self.storage.check_space(remaining)
                    outgoing.write(chunk)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            completed += component.expected_size_bytes
        with self._mutex:
            self._transition(job, "verifying")
        job.verification = self._verify_bundle(stage, model, cancel)
        if not all(result.valid for result in job.verification):
            raise ManagerError("artifact_integrity_failed", "Staged bundle failed full verification")
        job.verified_bytes = sum(result.actual_size for result in job.verification)
        licenses = stage / "licenses"
        licenses.mkdir()
        for document in model.license_documents:
            assert_no_links(licenses)
            (licenses / (document.id + ".txt")).write_bytes(document.text.encode("utf-8"))
        self.storage.check_space(0)
        with self._mutex:
            if cancel.is_set():
                raise Cancelled()
            self._transition(job, "installing")
        receipt = Receipt(job_id=job.id, model_id=model.id, manifest=model, manifest_digest=job.manifest_digest,
                          acknowledgement_id=job.acknowledgement_id, verification=job.verification)
        self.storage.activate(receipt)
        # Never rely on transfer progress or a successful rename alone.
        self.storage.active(model.id)
        with self._mutex:
            job.candidate_bytes = job.total_expected_bytes
            self._transition(job, "ready")

    def status(self, model: ModelManifest) -> dict:
        with self._mutex:
            receipt = self.storage.active(model.id)
            jobs = [job for job in self._jobs.values() if job.model_id == model.id]
            latest = max(jobs, key=lambda job: job.created_at) if jobs else None
            state = "not_installed"
            report = []
            if receipt:
                report = self._verify_bundle(self.storage.installed(model.id, receipt.job_id), receipt.manifest, threading.Event())
                state = "ready" if report and all(result.valid for result in report) else "corrupted"
                if any(result.code in {"unsafe_file", "unreadable"} for result in report):
                    state = "checking"
            elif latest and latest.state != "ready":
                state = latest.state
            return {"model_id": model.id, "state": state, "artifact_ready": state == "ready",
                    "generation_ready": False, "job_id": latest.id if latest else None,
                    "verification": [result.model_dump() for result in report],
                    "incomplete_bundles": [p.parent.name for p in self.storage.path("staging").glob("*/bundle")]
                    if self.storage.path("staging").exists() else []}

    def recover(self) -> None:
        """Reconcile local receipts; never resumes a network transfer at startup."""
        jobs_dir = self.storage.path("jobs")
        if not jobs_dir.exists():
            return
        for path in sorted(jobs_dir.glob("*.json")):
            job = Job.model_validate(self.storage.read_json(path))
            if path.stem != job.id or not re.fullmatch(r"[0-9a-f]{32}", job.id) or job.manifest_digest != manifest_digest(job.manifest):
                raise ManagerError("invalid_job_record", "Invalid persisted job; manual recovery required")
            self._jobs[job.id] = job
            self._cancels[job.id] = threading.Event()
            if job.state not in TERMINAL:
                receipt = self.storage.active(job.model_id)
                if job.operation == "install" and receipt and receipt.job_id == job.id:
                    results = self._verify_bundle(self.storage.installed(receipt.model_id, receipt.job_id), receipt.manifest, threading.Event())
                    job.verification = results
                    job.state = "ready" if all(result.valid for result in results) else "corrupted"
                elif job.operation == "remove" and receipt is None:
                    job.state = "not_installed"
                    job.error = {"code": "cleanup_pending", "message": "Removal was interrupted; retained owned files may need manual cleanup"}
                else:
                    job.state = "failed"
                    job.error = {"code": "interrupted", "message": "Interrupted job; no automatic transfer resumed. Start a new attempt."}
                self._save(job)

    def close(self) -> None:
        with self._mutex:
            self._closed = True
            for job_id, event in self._cancels.items():
                if self._jobs[job_id].state not in TERMINAL and self._jobs[job_id].state != "installing":
                    event.set()
        self._executor.shutdown(wait=True)
        self.storage.close()
