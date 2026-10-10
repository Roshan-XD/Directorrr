"""Pinned single-file SDK transfers. Network is opt-in and isolated in a worker."""

import logging
import multiprocessing
import os
import queue
import re
import time
from pathlib import Path
from threading import Event
from threading import Thread

from director.installations.schemas import Cancelled, ManagerError
from director.models.schemas import ModelComponent
from director.installations.verifier import assert_no_links, is_link


def transfer_details(error: Exception) -> str:
    """Keep actionable exception evidence, without tokens or signed URL queries."""
    secrets = [value for key, value in os.environ.items()
               if any(word in key.upper() for word in ("TOKEN", "PASSWORD", "SECRET", "KEY")) and len(value) >= 8]
    def redact(text):
        for value in secrets:
            text = text.replace(value, "[redacted]")
        text = re.sub(r"https?://[^\s\"'<>]+", lambda m: m.group(0).split("?")[0].split("#")[0] if "@" not in m.group(0) else "[redacted URL]", text)
        text = re.sub(r"\bhf_[A-Za-z0-9]+\b|(?i:Bearer|Basic)\s+[A-Za-z0-9+/=_-]+", "[redacted]", text)
        return text[:1500]
    parts = []
    seen = set()
    while error is not None and id(error) not in seen and len(parts) < 4:
        seen.add(id(error))
        parts.append(type(error).__name__ + ": " + redact(str(error)))
        error = error.__cause__ or error.__context__
    return "\nCaused by: ".join(parts)


def validate_private_cache(cache: Path) -> None:
    """Reject redirected directories/hardlinks before letting the SDK write.

    Hugging Face snapshot file symlinks are allowed only into this private cache.
    """
    assert_no_links(cache)
    if not cache.exists():
        return
    for directory, directories, files in os.walk(cache, followlinks=False):
        for name in directories:
            if is_link(Path(directory) / name):
                raise ManagerError("unsafe_cache", "Cache directory links are forbidden")
        for name in files:
            path = Path(directory) / name
            if is_link(path):
                if not path.is_symlink() or not path.resolve().is_relative_to(cache.resolve()):
                    raise ManagerError("unsafe_cache", "Cache file link escapes private storage")
            elif not path.is_file() or path.stat().st_nlink != 1:
                raise ManagerError("unsafe_cache", "Unsafe cache file")


def _sdk_fetch(component: ModelComponent, cache: Path, send, use_login: bool) -> str:
    # Imported only for a real transfer, never needed by fixture tests.
    from huggingface_hub import hf_hub_download
    # SDK 1.0.0 has no public progress callback. Observe private partial files;
    # these bytes are approximate transfer progress, never integrity evidence.
    transfer_cache = cache / component.sha256
    validate_private_cache(cache)
    assert_no_links(transfer_cache)
    stopped = Event()
    def monitor():
        while not stopped.wait(0.25):
            try:
                sizes = [p.stat().st_size for p in transfer_cache.rglob("*.incomplete")
                         if not p.is_symlink() and p.resolve().is_relative_to(transfer_cache.resolve())]
                if sizes:
                    send({"kind": "progress", "bytes": min(sum(sizes), component.expected_size_bytes)})
            except OSError:
                pass  # Transfer verification will report inaccessible files.
    observer = Thread(target=monitor, daemon=True)
    observer.start()
    try:
        path = hf_hub_download(
            repo_id=component.repository_id, filename=component.filename,
            revision=component.pinned_revision, cache_dir=transfer_cache,
            token=True if use_login else False, endpoint="https://huggingface.co", etag_timeout=10,
        )
        send({"kind": "progress", "bytes": component.expected_size_bytes})
        return path
    finally:
        stopped.set()
        observer.join(timeout=1)


def _worker(component_data: dict, cache: str, messages, use_login: bool) -> None:
    # SDK may log signed locations/exception details; none enter Director's logs.
    os.environ.pop("HF_DEBUG", None)
    os.environ.pop("DIRECTOR_MANAGER_TOKEN", None)
    os.environ.pop("DIRECTOR_LAUNCHER_TOKEN", None)
    # ComfyUI stays offline; explicitly authorized transfers use a separate child.
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ["HF_ENDPOINT"] = "https://huggingface.co"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "20"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    logging.disable(logging.CRITICAL)
    with open(os.devnull, "w") as sink:
        import contextlib
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            try:
                component = ModelComponent.model_validate(component_data)
                # Spawn entry-point imports may already have cached SDK constants.
                # This changes only the transfer child, never the parent/runtime.
                from huggingface_hub import constants
                constants.HF_HUB_OFFLINE = False
                path = _sdk_fetch(component, Path(cache), messages.put, use_login)
                messages.put({"kind": "complete", "path": path})
            except Exception as error:
                # Friendly categories plus bounded, redacted causal evidence.
                name = type(error).__name__
                code = "sdk_missing" if isinstance(error, ImportError) else (
                    "access_denied" if name in {"GatedRepoError", "RepositoryNotFoundError"} else
                    "artifact_not_found" if name in {"RevisionNotFoundError", "RemoteEntryNotFoundError", "EntryNotFoundError"}
                    else "network_failure"
                )
                messages.put({"kind": "error", "code": code, "technical_details": transfer_details(error)})


class HuggingFaceDownloader:
    is_real = True

    def __init__(self, *, enabled: bool = False, use_login: bool = False, timeout_seconds: float = 3600):
        self.enabled, self.use_login, self.timeout = enabled, use_login, timeout_seconds

    def fetch(self, component: ModelComponent, cache: Path, cancel: Event, progress, allowlist: set[tuple]) -> Path:
        if not self.enabled:
            raise ManagerError("real_downloads_disabled", "Real downloads are disabled")
        key = (component.repository_id, component.pinned_revision, component.filename)
        if key not in allowlist or component.pinned_revision is None or component.expected_size_bytes is None or not component.sha256:
            raise ManagerError("invalid_artifact", "A pinned allowlisted artifact with exact integrity metadata is required")
        if cancel.is_set():
            raise Cancelled()
        validate_private_cache(cache)
        context = multiprocessing.get_context("spawn")
        messages = context.Queue(maxsize=256)
        process = context.Process(target=_worker, args=(component.model_dump(mode="json"), str(cache), messages, self.use_login))
        process.start()
        deadline = time.monotonic() + self.timeout
        try:
            while True:
                if cancel.is_set():
                    raise Cancelled()
                if time.monotonic() >= deadline:
                    raise ManagerError("transfer_timeout", "Transfer exceeded its time budget")
                try:
                    message = messages.get(timeout=0.1)
                except queue.Empty:
                    if not process.is_alive():
                        raise ManagerError("worker_failed", "Transfer worker stopped without a completion record")
                    continue
                if message["kind"] == "progress":
                    progress(min(message["bytes"], component.expected_size_bytes))
                elif message["kind"] == "error":
                    error = ManagerError(message["code"], "Transfer failed; check access, connection and SDK setup")
                    error.technical_details = message.get("technical_details", "Worker returned no additional details")
                    raise error
                else:
                    path = Path(message["path"])
                    if not path.resolve().is_relative_to(cache.resolve()):
                        raise ManagerError("unsafe_cache", "SDK result escapes the private cache")
                    return path
        finally:
            process.join(timeout=1)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()
            messages.close()


class FixtureDownloader:
    """Explicit tiny allowlist: never contacts any network or arbitrary source path."""
    is_real = False

    def __init__(self, payloads: dict[tuple, bytes]):
        if sum(map(len, payloads.values())) > 1024 * 1024:
            raise ValueError("Fixture data must be tiny")
        self.payloads = payloads

    def fetch(self, component: ModelComponent, cache: Path, cancel: Event, progress, allowlist: set[tuple]) -> Path:
        key = (component.repository_id, component.pinned_revision, component.filename)
        if key not in allowlist or key not in self.payloads:
            raise ManagerError("fixture_not_allowed", "Artifact is not an approved offline fixture")
        if cancel.is_set():
            raise Cancelled()
        target = cache / (component.sha256 + ".fixture")
        from director.installations.verifier import assert_no_links
        assert_no_links(target)
        cache.mkdir(parents=True, exist_ok=True)
        if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
            raise ManagerError("unsafe_cache", "Fixture cache must be an unlinked regular file")
        with target.open("wb") as stream:
            stream.write(self.payloads[key])
        progress(len(self.payloads[key]))
        return target
