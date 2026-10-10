"""Explicit private Windows setup wizard. Not Director's production provisioner."""
import hashlib
import json
import os
import queue
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
import webbrowser
import zipfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "runtime/windows-dev-001"
STATE = ROOT / "setup/state"
ALLOWED_HOSTS = {"www.python.org", "files.pythonhosted.org", "download.pytorch.org", "github.com", "codeload.github.com"}


def safe(path):
    path = Path(path)
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Setup path escapes Director")
    for parent in (path, *path.parents):
        if parent.exists() and (parent.is_symlink() or getattr(parent.stat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Setup paths cannot contain links or junctions")
    if path.is_file() and path.stat().st_nlink != 1:
        raise ValueError("Setup file has shared hard links")
    return path


def sha(path):
    safe(path)
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_manifest():
    data = json.loads(safe(ROOT / "setup/manifest.json").read_text())
    identities = {"runtime_lock_sha256": ROOT / "runtime_profiles/locks/wan-windows-cp313-cu130.lock.json",
                  "backend_lock_sha256": ROOT / "setup/backend-lock.json",
                  "source_inventory_sha256": ROOT / "runtime_profiles/sources/wan-comfyui.inventory.json",
                  "model_manifest_sha256": ROOT / "model_registry/wan-2-1-t2v-1-3b.json"}
    for key, path in identities.items():
        if sha(path) != data[key]:
            raise ValueError("Setup inventory changed: " + key)
    for item in data["agreement_sources"]:
        if "document" in item and sha(ROOT / "setup" / item["document"]) != item["sha256"]:
            raise ValueError("Review document changed")
    return data


def plan(manifest):
    runtime = json.loads((ROOT / "runtime_profiles/locks/wan-windows-cp313-cu130.lock.json").read_text())
    backend = json.loads((ROOT / "setup/backend-lock.json").read_text())
    models = json.loads((ROOT / "model_registry/wan-2-1-t2v-1-3b.json").read_text())["components"]
    if runtime["status"] != "COMPLETE" or len(runtime["packages"]) != 84:
        raise ValueError("Complete reviewed runtime lock required")
    return {"runtime": runtime, "backend": backend, "models": models,
            "known_download_bytes": manifest["python"]["size_bytes"] + manifest["backend_python"]["size_bytes"] + sum(p["size_bytes"] for p in runtime["packages"] + backend["packages"]),
            "model_bytes": sum(c["expected_size_bytes"] for c in models),
            "source_max_bytes": manifest["source_transfer_limit_bytes"]}


def validate_installed():
    """Setup configuration is not a generation PASS or production clearance."""
    manifest = load_manifest()
    receipt = json.loads(safe(NATIVE / "receipts/teammate-setup.json").read_text())
    owner = json.loads(safe(NATIVE / "owner.json").read_text())
    if (owner.get("owner") != "Director Stage 12 private development" or owner.get("production_ready") is not False
            or receipt.get("state") != "configured" or receipt.get("manifest_sha256") != sha(ROOT / "setup/manifest.json")
            or receipt.get("comfyui_revision") != manifest["comfyui_revision"] or receipt.get("cuda_smoke_pass") is not True):
        raise ValueError("Private setup ownership/profile validation failed")
    for relative in ("python/python.exe", "venv/Scripts/python.exe", "ComfyUI/main.py", "receipts/cuda-smoke.json"):
        if not safe(NATIVE / relative).is_file():
            raise ValueError("Required private runtime file is missing")
    cuda = json.loads((NATIVE / "receipts/cuda-smoke.json").read_text())
    if cuda.get("available") is not True or cuda.get("tensor_pass") is not True or cuda.get("torch") != "2.12.1+cu130":
        raise ValueError("Private setup CUDA validation is missing")
    for item in plan(manifest)["models"]:
        path = safe(NATIVE / "models" / item["destination"])
        if not path.is_file() or path.stat().st_size != item["expected_size_bytes"]:
            raise ValueError("Required Wan model is missing or truncated")
    ui = json.loads(safe(ROOT / "setup/ui-manifest.json").read_text())
    if not ui or any(sha(ROOT / "frontend/dist" / name) != value for name, value in ui.items()):
        raise ValueError("Packaged frontend integrity failed")


class Cancelled(Exception):
    pass


class Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


def checked_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise ValueError("Artifact origin is not approved")


def space(required):
    safe(ROOT)
    if shutil.disk_usage(ROOT).free < required:
        raise ValueError("Insufficient free disk space; existing installations are preserved")


def download(item, folder, cancel, report):
    """Exact artifact URL, exclusive quarantine file, bounded streaming hash."""
    checked_url(item["artifact_url"])
    name = item["wheel_filename"]
    if not re.fullmatch(r"[A-Za-z0-9_.+%-]+", name) or unquote(urlsplit(item["artifact_url"]).path.split("/")[-1]) != name:
        raise ValueError("Artifact filename does not match its approved URL")
    folder = safe(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = safe(folder / name)
    maximum = item.get("size_bytes") or item["maximum_bytes"]
    expected = item.get("sha256")
    if target.exists():
        if expected and (target.stat().st_size != maximum or sha(target) != expected) or not expected and not 0 < target.stat().st_size <= maximum:
            raise ValueError("Existing quarantine artifact failed integrity; preserved for review")
        return target
    partial = safe(folder / (name + ".partial-" + uuid.uuid4().hex))
    checksum = hashlib.sha256()
    total = 0
    try:
        opener = urllib.request.build_opener(Redirects())
        with opener.open(item["artifact_url"], timeout=30) as response, partial.open("xb") as output:
            declared = response.headers.get("Content-Length")
            if declared and (int(declared) > maximum or item.get("size_bytes") and int(declared) != maximum):
                raise ValueError("Published artifact size changed")
            last = 0
            while chunk := response.read(1024 * 1024):
                if cancel.is_set():
                    raise Cancelled()
                total += len(chunk)
                if total > maximum:
                    raise ValueError("Artifact exceeded approved transfer size")
                space(len(chunk) + 1024**3)
                checksum.update(chunk)
                output.write(chunk)
                if time.monotonic() - last > 0.5:
                    report(f"Downloading {name}: {total:,} / {maximum:,} bytes")
                    last = time.monotonic()
        if total == 0 or item.get("size_bytes") and total != maximum or expected and checksum.hexdigest() != expected:
            raise ValueError("Artifact size/SHA-256 mismatch; nothing installed")
        safe(target)
        if target.exists():
            raise ValueError("Quarantine target appeared during transfer")
        partial.rename(target)
        return target
    except Exception:
        if partial.exists():
            safe(partial).unlink()  # Only the exact partial file created by this call.
        raise


def atomic_json(path, value):
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = safe(path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp"))
    with temp.open("x") as output:
        json.dump(value, output, indent=2)
    os.replace(temp, path)


@contextmanager
def setup_lock():
    import msvcrt
    STATE.mkdir(parents=True, exist_ok=True)
    with safe(STATE / "setup.lock").open("a+b") as stream:
        stream.seek(0)
        if not stream.read(1):
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise RuntimeError("Another Director setup is already active")
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def process_environment():
    """Do not pass Director sessions or Hub credentials into setup children."""
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(("DIRECTOR_", "HF_")) or key in {"PYTHONPATH", "PYTHONHOME", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL"}:
            env.pop(key, None)
    env.update(PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONNOUSERSITE="1",
               PIP_CACHE_DIR=str(STATE / "pip-cache"))
    safe(STATE / "temp").mkdir(parents=True, exist_ok=True)
    safe(NATIVE / "cache").mkdir(parents=True, exist_ok=True)
    env.update(TEMP=str(STATE / "temp"), TMP=str(STATE / "temp"), CUDA_CACHE_PATH=str(NATIVE / "cache"))
    return env


def command(args, log_name, report, cancel, timeout=1200):
    if cancel.is_set():
        raise Cancelled()
    report("Installing/checking " + log_name)
    STATE.mkdir(parents=True, exist_ok=True)
    env = process_environment()
    with safe(STATE / (log_name + ".log")).open("ab") as output:
        process = subprocess.Popen([str(a) for a in args], cwd=ROOT, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            if cancel.is_set() or time.monotonic() > deadline:
                process.terminate()
                process.wait(timeout=20)
                raise Cancelled() if cancel.is_set() else RuntimeError(log_name + " timed out")
            time.sleep(0.2)
        if process.returncode:
            raise RuntimeError(log_name + " failed; see setup/state/" + log_name + ".log")


def install_wheels(python, packages, label, cancel, report, review=None):
    cache = STATE / label
    artifacts = [download(item, cache, cancel, report) for item in packages]
    requirements = safe(STATE / (label + ".txt"))
    requirements.write_text("\n".join(f"{p['name']}=={p['version']} --hash=sha256:{p['sha256']}" for p in packages) + "\n")
    if label == "runtime-wheels":
        manifest = load_manifest()
        by_name = {p.name: p for p in artifacts}
        for notice in manifest["wheel_notices"]:
            with zipfile.ZipFile(by_name[notice["wheel"]]) as archive:
                matches = [i for i in archive.infolist() if i.filename == notice["member"]]
                if len(matches) != 1 or matches[0].file_size != notice["size"] or matches[0].file_size > 2 * 1024**2:
                    raise ValueError("Bundled runtime notice inventory changed")
                text = archive.read(matches[0])
                if hashlib.sha256(text).hexdigest() != notice["sha256"]:
                    raise ValueError("Bundled runtime notice checksum changed")
    elif review is not None:
        documents = []
        total = 0
        for artifact in artifacts:
            with zipfile.ZipFile(artifact) as archive:
                members = [i for i in archive.infolist() if not i.is_dir() and
                           (i.filename.endswith(".dist-info/METADATA") or
                            re.search(r"(?i)(license|licence|notice|copying)", i.filename))]
                if not members or len(members) > 100:
                    raise ValueError("Backend package license evidence needs manual review")
                for member in members:
                    total += member.file_size
                    if member.file_size > 2 * 1024**2 or total > 20 * 1024**2:
                        raise ValueError("Backend document inspection limit exceeded")
                    data = archive.read(member)
                    identity = hashlib.sha256(data).hexdigest()
                    notices = safe(STATE / "backend-notices")
                    notices.mkdir(exist_ok=True)
                    captured = notices / (identity + ".txt")
                    if not captured.exists():
                        captured.write_bytes(data)
                    documents.append(artifact.name + " / " + member.filename + "\nSHA-256: " + identity + "\n" + data.decode("utf-8", errors="replace"))
        text = "\n\n".join(documents)
        if not review("Exact backend package notices and metadata", text):
            raise ValueError("Backend package terms were not accepted; no packages installed")
        atomic_json(STATE / "backend-notices-consent.json", {"accepted": True, "document_sha256": hashlib.sha256(text.encode()).hexdigest()})
    command([python, "-I", "-m", "pip", "--isolated", "install", "--no-index", "--find-links", cache,
             "--only-binary=:all:", "--require-hashes", "--no-deps", "--no-cache-dir", "-r", requirements], label, report, cancel)


def extract_python(archive, destination, cancel):
    """Full, hashed CPython ZIP only; not an embeddable pip workaround."""
    destination = safe(destination)
    if destination.exists():
        raise ValueError("Unknown/incomplete backend Python exists; it will not be overwritten")
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        names, total = set(), 0
        if len(entries) > 10000:
            raise ValueError("Python ZIP entry limit exceeded")
        for entry in entries:
            name = entry.orig_filename.rstrip("/")
            if "\\" in name or ":" in name or name.startswith("/") or name.casefold() in names:
                raise ValueError("Unsafe/duplicate Python ZIP path")
            names.add(name.casefold())
            for part in name.split("/"):
                if (part in {"", ".", ".."} or part.endswith((" ", ".")) or re.search(r'[<>"|?*\x00]', part)
                        or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", part.split(".")[0])):
                    raise ValueError("Unsafe Python ZIP member")
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if entry.flag_bits & 1 or entry.external_attr & 0x400 or kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise ValueError("Special Python ZIP member")
            total += entry.file_size
            if entry.file_size > 64 * 1024**2 or total > 256 * 1024**2:
                raise ValueError("Python extraction limit exceeded")
        destination.mkdir(parents=True)
        for entry in entries:
            if cancel.is_set():
                raise Cancelled()
            path = safe(destination / entry.filename)
            if entry.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            count = 0
            with source.open(entry) as incoming, path.open("xb") as outgoing:
                while chunk := incoming.read(64 * 1024):
                    count += len(chunk)
                    if count > entry.file_size:
                        raise ValueError("Python member exceeded declared length")
                    outgoing.write(chunk)
            if count != entry.file_size:
                raise ValueError("Python extraction size mismatch")


def prepare_backend(cancel, report, review):
    manifest = load_manifest()
    spec = manifest["backend_python"]
    base = safe(ROOT / "runtime/backend-python")
    proof = STATE / "backend-python.json"
    if not base.exists():
        archive = download({"artifact_url": spec["url"], "wheel_filename": spec["filename"],
                            "size_bytes": spec["size_bytes"], "sha256": spec["sha256"]}, STATE / "bootstrap", cancel, report)
        extract_python(archive, base, cancel)
        atomic_json(proof, {"sha256": spec["sha256"], "version": spec["version"]})
    elif not proof.is_file() or json.loads(safe(proof).read_text()).get("sha256") != spec["sha256"]:
        raise ValueError("Backend Python ownership/integrity receipt is missing")
    for needed in ("python.exe", "pythonw.exe", "Lib/venv/__init__.py", "Lib/ensurepip/__init__.py", "LICENSE.txt"):
        if not safe(base / needed).is_file():
            raise ValueError("Full backend Python inventory is incomplete")
    document = (base / "LICENSE.txt").read_text()
    if len(document) > 2 * 1024**2 or not review("Exact bundled Python " + spec["version"] + " license and notices", document):
        raise ValueError("Bundled backend Python terms were not accepted; no interpreter executed")
    atomic_json(STATE / "backend-python-consent.json", {"accepted": True, "version": spec["version"], "document_sha256": sha(base / "LICENSE.txt")})
    python = safe(base / "python.exe")
    safe(ROOT / ".venv")
    backend = ROOT / ".venv/Scripts/python.exe"
    if backend.exists():
        config = safe(ROOT / ".venv/pyvenv.cfg").read_text()
        if str(base).lower() not in config.lower() or "include-system-site-packages = false" not in config.lower():
            raise ValueError("Existing backend environment is not setup-owned; it will not be changed")
    if not backend.exists():
        command([python, "-I", "-m", "venv", "--copies", ROOT / ".venv"], "backend-environment", report, cancel)
    install_wheels(backend, plan(manifest)["backend"]["packages"], "backend-wheels", cancel, report, review)
    command([backend, "-I", "-m", "pip", "check"], "backend-check", report, cancel)
    return backend


def provision_process(backend, cancel, report, identity):
    """Assign an OS job before allowing the worker to create any descendants."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from setup_process import OwnedJob
    signal = safe(STATE / ("provision-ready-" + identity))
    process = subprocess.Popen([str(backend), "-I", str(ROOT / "scripts/teammate_setup.py"), "--provision", "--ready", identity],
        cwd=ROOT, env=process_environment(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    job = None
    reader = None
    try:
        job = OwnedJob(process)
        signal.touch(exist_ok=False)
        def output():
            with safe(STATE / "provision.log").open("a", encoding="utf-8") as log:
                for line in process.stdout:
                    log.write(line[:4096])
                    log.flush()
                    report(line.strip()[:1500])
        reader = threading.Thread(target=output, daemon=True)
        reader.start()
        while process.poll() is None:
            if cancel.wait(0.25):
                job.close()  # Stops this worker and only its SDK/pip descendants.
                process.wait(timeout=20)
                raise Cancelled()
        reader.join(timeout=5)
        if process.returncode:
            raise RuntimeError("Runtime setup stopped; see setup/state/provision.log")
    finally:
        if job:
            job.close()
        elif process.poll() is None:
            process.terminate()
        process.wait(timeout=20)
        if reader:
            reader.join(timeout=5)
        signal.unlink(missing_ok=True)


def provision(cancel, report, download_models):
    """Runs in the new backend environment; reuses existing verifiers/transports."""
    sys.path.insert(0, str(ROOT / "backend"))
    from director.installations.downloader import HuggingFaceDownloader
    from director.installations.verifier import ArtifactVerifier
    from director.installations.schemas import digest
    from director.models.schemas import ModelComponent
    from director.runtimes.schemas import RuntimeProfile
    from director.runtimes.lock_validation import validate_lock
    from director.runtimes.source import SourceInventory, SourceVerifier
    from director.runtimes.storage import RuntimeStorageManager
    manifest = load_manifest()
    items = plan(manifest)
    profile = RuntimeProfile.model_validate_json((ROOT / "runtime_profiles/wan-windows-candidate.json").read_text())
    requirements = (ROOT / "runtime_profiles/locks/wan-windows-comfyui-requirements.txt").read_text()
    audit = validate_lock(items["runtime"], profile, requirements, (ROOT / "runtime_profiles/wan-windows-candidate.json").read_bytes())
    if not audit["complete"]:
        raise ValueError("Independent runtime lock verification failed")
    python = safe(NATIVE / "python/python.exe")
    runtime_python = safe(NATIVE / "venv/Scripts/python.exe")
    if runtime_python.exists():
        config = safe(NATIVE / "venv/pyvenv.cfg").read_text()
        if str(NATIVE / "python").lower() not in config.lower() or "include-system-site-packages = false" not in config.lower():
            raise ValueError("Existing runtime environment is not setup-owned")
    if not runtime_python.exists():
        command([python, "-I", "-m", "venv", "--copies", NATIVE / "venv"], "runtime-environment", report, cancel)
    install_wheels(runtime_python, items["runtime"]["packages"], "runtime-wheels", cancel, report)
    command([runtime_python, "-I", "-m", "pip", "check"], "runtime-check", report, cancel)
    inventory = SourceInventory.model_validate_json((ROOT / "runtime_profiles/sources/wan-comfyui.inventory.json").read_text())
    destination = safe(NATIVE / "ComfyUI")
    if destination.exists():
        # Recover only exact verified source, never overwrite an unknown tree.
        from director.installations.storage import inspect_owned_inventory
        expected = {safe(destination / item.path) for item in inventory.files}
        inspect_owned_inventory(destination, expected)
        for item in inventory.files:
            if cancel.is_set():
                raise Cancelled()
            file = safe(destination / item.path)
            if file.stat().st_size != item.size_bytes:
                raise ValueError("Existing ComfyUI source size changed")
            content = file.read_bytes()
            if hashlib.sha1(f"blob {item.size_bytes}\0".encode() + content).hexdigest() != item.git_blob_sha1:
                raise ValueError("Existing ComfyUI source hash changed")
        source_hash = None
    else:
        source = download({"artifact_url": manifest["source_url"], "wheel_filename": manifest["comfyui_revision"] + ".zip",
                           "maximum_bytes": manifest["source_transfer_limit_bytes"]}, STATE / "source", cancel, report)
        storage = RuntimeStorageManager((ROOT / "runtime/setup-staging").absolute())
        verifier = SourceVerifier(inventory, approved_digest=digest(inventory.model_dump()), revision=manifest["comfyui_revision"])
        job_id = uuid.uuid4().hex
        report("Checking every ComfyUI source file against the frozen Git tree")
        verifier.extract(storage, source, job_id=job_id, archive_sha256=sha(source), archive_size=source.stat().st_size, cancel=cancel)
        storage.staging(job_id).rename(destination)
        source_hash = sha(source)
    for directory in ("receipts", "models", "data/output", "data/user", "data/temp", "cache", "temp"):
        safe(NATIVE / directory).mkdir(parents=True, exist_ok=True)
    atomic_json(NATIVE / "receipts/comfy-source.json", {"revision": inventory.revision, "tree": inventory.tree,
                "files_verified": len(inventory.files), "archive_sha256": source_hash})
    components = [ModelComponent.model_validate(c) for c in items["models"]]
    allowlist = {(c.repository_id, c.pinned_revision, c.filename) for c in components}
    transport = HuggingFaceDownloader(enabled=download_models, timeout_seconds=7200)
    for component in components:
        target = safe(NATIVE / "models" / component.destination)
        if target.exists():
            if not ArtifactVerifier().verify(target, component).valid:
                raise ValueError("Existing model failed verification; preserved")
            continue
        if not download_models:
            raise ValueError("Missing Wan model: " + component.destination + ". Setup needs explicit model-download approval.")
        report("Downloading verified Wan component: " + component.id)
        candidate = transport.fetch(component, STATE / "model-cache", cancel,
            lambda count: report(f"Wan {component.id}: {count:,} / {component.expected_size_bytes:,} bytes"), allowlist)
        if candidate.is_symlink():
            if not candidate.resolve().is_relative_to((STATE / "model-cache").resolve()):
                raise ValueError("Model snapshot link escapes private cache")
            candidate = candidate.resolve()
        if not ArtifactVerifier().verify(candidate, component).valid:
            raise ValueError("Downloaded model failed exact verification")
        target.parent.mkdir(parents=True, exist_ok=True)
        # Snapshot links are never activated; copy into an exclusive owned file.
        partial = safe(target.with_name(target.name + "." + uuid.uuid4().hex + ".partial"))
        space(component.expected_size_bytes + 1024**3)
        try:
            with candidate.open("rb") as incoming, partial.open("xb") as outgoing:
                while chunk := incoming.read(1024 * 1024):
                    if cancel.is_set():
                        raise Cancelled()
                    outgoing.write(chunk)
            if not ArtifactVerifier().verify(partial, component).valid:
                raise ValueError("Model handoff verification failed")
            if target.exists():
                raise ValueError("Model destination appeared during installation")
            partial.rename(target)
        finally:
            if partial.exists():
                safe(partial).unlink()
    smoke = NATIVE / "receipts/setup-smoke.json"
    command([runtime_python, "-I", ROOT / "scripts/setup_cuda_check.py", smoke], "cuda-check", report, cancel, 120)
    evidence = json.loads(smoke.read_text())
    if evidence["torch"] != "2.12.1+cu130" or not evidence["available"] or not evidence["tensor_pass"]:
        raise ValueError("CUDA check failed. No driver/toolkit is installed by Director.")
    atomic_json(NATIVE / "receipts/cuda-smoke.json", evidence)
    atomic_json(NATIVE / "receipts/teammate-setup.json", {"state": "configured", "scope": "private development",
                "manifest_sha256": sha(ROOT / "setup/manifest.json"), "comfyui_revision": inventory.revision,
                "cuda_smoke_pass": True, "generation_validated": False})
    atomic_json(STATE / "installed.json", {"packaged_ui": True, "generation_validated": False})
    report("Setup finished. Start Director is ready; generation must still be tested on this PC.")


def wizard():
    import tkinter as tk
    from tkinter import messagebox
    if os.name != "nt" or os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() != "AMD64":
        raise RuntimeError("This setup targets Windows AMD64")
    manifest = load_manifest()
    items = plan(manifest)
    if (NATIVE / "receipts/teammate-setup.json").exists():
        validate_installed()
        messagebox.showinfo("Director", "Director is already configured. Use Start Director. Existing runtime and user media were preserved.")
        return
    if (NATIVE / "receipts/native-inference.json").exists():
        messagebox.showinfo("Director", "Director is already configured. Use Start Director. Existing runtime and user media were preserved.")
        return
    window = tk.Tk()
    window.title("Director — Private Windows Setup")
    window.geometry("820x700")
    text = tk.Text(window, wrap="word", height=23)
    text.pack(fill="both", expand=True, padx=16, pady=12)
    text.insert("end", "PRIVATE LOCAL DEVELOPMENT SETUP\n\n"
        f"Destination: {ROOT}\nKnown software transfers: {items['known_download_bytes']:,} bytes (including Python bootstrap).\n"
        f"ComfyUI source: up to {items['source_max_bytes']:,} additional bytes; each file checked against the pinned tree.\n"
        f"Optional Wan model transfers: {items['model_bytes']:,} bytes. Require 32 GiB free.\n\n"
        "Windows x64, a compatible NVIDIA driver/GPU and enough available RAM/VRAM are required. Drivers and Resolve are not installed or modified. "
        "A similar GPU does not guarantee generation; this setup runs a bounded CUDA check, not video inference.\n\n"
        "READ THE COMPLETE TERMS before accepting. These are private-use agreements, not permission to redistribute binaries. "
        "No acceptance belonging to the author is reused. WAN repackaging/FP8 provenance limits and production review blockers remain documented in model-research.md.\n\n")
    for agreement in manifest["agreement_sources"]:
        text.insert("end", agreement["name"] + "\n" + agreement["source"] + "\n")
        if "document" in agreement:
            text.insert("end", "Captured text: setup/" + agreement["document"] + "; SHA-256 " + agreement["sha256"] + "\n")
    text.insert("end", "\nAll captured bundled notices are under setup/notices. They are preserved and checked against the exact downloaded wheels before installation. Additional/changed terms stop setup.\n")
    text.configure(state="disabled")
    def documents():
        os.startfile(str(ROOT / "setup/notices"))
        for agreement in manifest["agreement_sources"]:
            webbrowser.open(agreement["source"])
    tk.Button(window, text="Open full agreements and notices", command=documents).pack()
    accepted = tk.BooleanVar(value=False)
    models = tk.BooleanVar(value=False)
    tk.Checkbutton(window, text="I have reviewed and accept the applicable terms, have the required age/authority,\nand authorize this private installation and the bounded CUDA check.", variable=accepted).pack(pady=8)
    tk.Checkbutton(window, text=f"Also download the three Wan files ({items['model_bytes']:,} bytes) under their reviewed terms.", variable=models).pack()
    status = tk.StringVar(value="No further downloads start before you click Install.")
    tk.Label(window, textvariable=status, wraplength=780).pack(pady=8)
    events = queue.Queue()
    cancel = threading.Event()
    running = False
    def report(value):
        events.put(("status", value))
    def review(name, document):
        response = {"accepted": False, "event": threading.Event()}
        events.put(("review", (name, document, response)))
        while not response["event"].wait(0.25):
            if cancel.is_set():
                return False
        return response["accepted"]
    def work():
        try:
            space(manifest["first_setup_free_bytes"])
            if not (ROOT / "frontend/dist/index.html").exists():
                raise ValueError("Use the complete release ZIP, which includes the built UI")
            with setup_lock():
                identity = uuid.uuid4().hex
                atomic_json(STATE / "consent.json", {"accepted": True, "scope": "private local development", "manifest_sha256": sha(ROOT / "setup/manifest.json"), "model_download": True, "cuda_check": True, "session": identity})
                backend = prepare_backend(cancel, report, review)
                provision_process(backend, cancel, report, identity)
            report("Director is installed. Use Start Director. See setup/state for progress and receipts.")
            events.put(("done", "Setup finished"))
        except Exception as error:
            detail = getattr(error, "technical_details", None)
            events.put(("error", (str(error) + ("\n" + detail if detail else "")) if not cancel.is_set() else "Cancelled. Owned staging remains; user media was preserved."))
    def start():
        nonlocal running
        if not accepted.get():
            return messagebox.showwarning("Review needed", "Explicit acknowledgement is required.")
        if not models.get():
            return messagebox.showwarning("Model confirmation", "Select the Wan download confirmation for first setup.")
        running = True
        install.configure(state="disabled")
        threading.Thread(target=work, daemon=True).start()
    def stop():
        if running:
            cancel.set()
            status.set("Cancelling after the current bounded operation…")
        else:
            window.destroy()
    def poll():
        nonlocal running
        while not events.empty():
            kind, value = events.get()
            if kind == "review":
                name, document, response = value
                panel = tk.Toplevel(window)
                panel.title(name)
                panel.geometry("780x600")
                contents = tk.Text(panel, wrap="word")
                contents.insert("end", document)
                contents.configure(state="disabled")
                contents.pack(fill="both", expand=True)
                checkbox = tk.BooleanVar(value=False)
                tk.Checkbutton(panel, text="I reviewed and accept this complete bundled document.", variable=checkbox).pack()
                def answer(accepted, response=response, panel=panel, checkbox=checkbox):
                    response["accepted"] = accepted and checkbox.get()
                    response["event"].set()
                    panel.destroy()
                tk.Button(panel, text="Accept / Continue", command=lambda: answer(True)).pack()
                panel.protocol("WM_DELETE_WINDOW", lambda: answer(False))
                continue
            status.set(value)
            if kind in {"done", "error"}:
                running = False
                if kind == "error":
                    messagebox.showerror("Setup stopped", value)
        window.after(250, poll)
    install = tk.Button(window, text="Confirm / Install Director", command=start)
    install.pack(side="left", padx=30, pady=15)
    tk.Button(window, text="Cancel / Close", command=stop).pack(side="right", padx=30, pady=15)
    window.protocol("WM_DELETE_WINDOW", stop)
    window.after(250, poll)
    window.mainloop()


if __name__ == "__main__":
    if "--provision" in sys.argv:
        import multiprocessing
        multiprocessing.freeze_support()
        consent = json.loads(safe(STATE / "consent.json").read_text())
        if consent.get("accepted") is not True or consent.get("manifest_sha256") != sha(ROOT / "setup/manifest.json") or consent.get("cuda_check") is not True:
            raise SystemExit("Fresh setup acknowledgement is required")
        identity = sys.argv[sys.argv.index("--ready") + 1] if "--ready" in sys.argv else ""
        if not re.fullmatch(r"[0-9a-f]{32}", identity) or consent.get("session") != identity:
            raise SystemExit("Invalid setup process session")
        ready = safe(STATE / ("provision-ready-" + identity))
        deadline = time.monotonic() + 30
        while not ready.exists():
            if time.monotonic() > deadline:
                raise SystemExit("Setup owner did not establish cancellation")
            time.sleep(.1)
        try:
            provision(threading.Event(), lambda message: print(message, flush=True), consent.get("model_download") is True)
        except Exception as error:
            sys.path.insert(0, str(ROOT / "backend"))
            from director.installations.downloader import transfer_details
            print(transfer_details(error), flush=True)
            raise SystemExit(1)
    else:
        wizard()
