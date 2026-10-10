"""One reviewed native H3 recipe; explicit UI consent, never repository code."""
import hashlib
import json
import os
import shutil
from pathlib import Path

from director.generation.service import ComfyUIClient
from director.installations.downloader import HuggingFaceDownloader
from director.installations.schemas import Cancelled, ManagerError
from director.installations.verifier import ArtifactVerifier, assert_no_links
from director.models.schemas import ModelComponent
from director.product.assets import Asset
from director.product.downloads import DownloadManager

MODEL_ID = "minimax-h3-optimized"
RECIPE_HASH = "6fe0cccbf7f1a2278a73bdfce5ef9cc052e660dc4f21a369d5575ea13e828d40"
ENCODER_LICENSE_HASH = "1701d973c2230600dd7b796150165f3b5360371804c5d5779849d223dae45874"
COMFY_REVISION = "b0b743566f65daafc423b4fea8a2fbda94b3384a"


def recipe(root):
    path = root / "model_registry/plans/minimax-h3-optimized.json"
    assert_no_links(path)
    if path.stat().st_size > 256 * 1024:
        raise ManagerError("unreviewed_recipe", "Oversized H3 inventory", 409)
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != RECIPE_HASH:
        raise ManagerError("unreviewed_recipe", "H3 inventory differs from the reviewed recipe", 409)
    result = json.loads(data)
    notice_path = root / "model_registry/plans/minimax-h3-optimized-qwen-license.json"
    assert_no_links(notice_path)
    if notice_path.stat().st_size > 128 * 1024:
        raise ManagerError("unreviewed_notice", "Oversized encoder notice", 409)
    notice = notice_path.read_bytes()
    if hashlib.sha256(notice).hexdigest() != ENCODER_LICENSE_HASH:
        raise ManagerError("unreviewed_notice", "Encoder license document differs from the reviewed text", 409)
    result["encoder_license"] = json.loads(notice)
    result["components"] = [ModelComponent.model_validate(c).model_dump(mode="json") for c in result["components"]]
    return result


def owned_native(native):
    marker = native / "owner.json"
    source = native / "receipts/comfy-source.json"
    for path in (marker, source):
        assert_no_links(path)
        if path.stat().st_size > 16384:
            raise ValueError("Oversized runtime receipt")
    if json.loads(marker.read_text())["owner"] != "Director Stage 12 private development":
        raise ValueError("Unowned runtime")
    if json.loads(source.read_text())["revision"] != COMFY_REVISION:
        raise ValueError("Unreviewed ComfyUI revision")
    cuda = native / "receipts/cuda-smoke.json"
    assert_no_links(cuda)
    if cuda.stat().st_size > 16384:
        raise ValueError("Oversized CUDA receipt")
    evidence = json.loads(cuda.read_text())
    if evidence.get("available") is not True or evidence.get("capability", [0])[0] < 12 or evidence.get("torch") != "2.12.1+cu130":
        raise ValueError("Reviewed Blackwell CUDA runtime is required")


def registered_assets(root, native):
    """Registration is usable only while every recorded file identity is unchanged."""
    try:
        owned_native(native)
        r = recipe(root)
        record = native / "receipts/h3-optimized.json"
        assert_no_links(record)
        if record.stat().st_size > 16384:
            return []
        receipt = json.loads(record.read_text())
        if receipt["recipe_sha256"] != RECIPE_HASH or receipt["execution_validated"] is not False:
            return []
        acknowledgement = receipt["license_acknowledgement"]
        if acknowledgement.get("accepted") is not True or acknowledgement.get("sha256") != r["license_sha256"] or acknowledgement.get("revision") != r["revision"]:
            return []
        assets = []
        for c in r["components"]:
            p = native / "models" / c["destination"]
            assert_no_links(p)
            stat = p.stat()
            item = receipt["files"][c["destination"]]
            if stat.st_nlink != 1 or not p.is_file() or (stat.st_size, stat.st_mtime_ns, stat.st_ino) != tuple(item["identity"]):
                return []
            if item["sha256"] != c["sha256"]:
                return []
            assets.append(Asset(path=c["destination"], size=c["expected_size_bytes"], sha256=c["sha256"], models=[MODEL_ID]))
        return assets
    except (OSError, ValueError, KeyError, TypeError):
        return []


class OptimizedH3Downloads(DownloadManager):
    def __init__(self, root, discovery, project, native, refresh, **kwargs):
        self.project, self.native, self.refresh = project, native, refresh
        self.h3_transport = kwargs.pop("h3_transport", None) or HuggingFaceDownloader(enabled=True)
        super().__init__(root, discovery, **kwargs)

    def plan(self, selection):
        r = recipe(self.project)
        if selection.repository != r["repository"]:
            return super().plan(selection)
        if sorted(selection.files) != sorted(c["filename"] for c in r["components"]):
            raise ManagerError("unreviewed_selection", "Install only the exact four optimized H3 components", 422)
        blockers = []
        try:
            owned_native(self.native)
        except (OSError, ValueError, KeyError):
            blockers.append("The reviewed Director-owned Windows runtime is unavailable.")
        # No location inference: eligibility is an explicit user acknowledgement.
        try:
            license_text = self.discovery.fetch(f"/{r['repository']}/raw/{r['revision']}/LICENSE")
        except Exception:
            license_text = None
        if not isinstance(license_text, str) or hashlib.sha256(license_text.encode()).hexdigest() != r["license_sha256"]:
            blockers.append("Pinned accompanying license changed or is unavailable.")
        total = r["total_bytes"]
        required = total * 2 + 2 * 1024**3
        free = shutil.disk_usage(self.project).free
        if free < required:
            blockers.append("Insufficient free disk for staging, cache and safety reserve.")
        for c in r["components"]:
            p = self.native / "models" / c["destination"]
            assert_no_links(p)
            if p.exists():
                blockers.append("H3 destination already exists; existing files will never be overwritten.")
        result = {**r, "required_free_bytes": required, "free_bytes": free,
                  "destination": str(self.native / "models"), "license": "MiniMax H3 Community License (2026-08-02); Qwen Apache-2.0",
                  "blockers": blockers, "runnable": False,
                  "warnings": ["16 GB Blackwell target: CPU offload required. 32 GB RAM is experimental; full pipeline memory has not been measured for this variant.",
                               "NVFP4 transformer is 10.86 GiB; text encoder and VAEs cannot all reside on the GPU together.",
                               "Ready means verified files and native workflow configured, not a completed inference test."],
                  "license_conditions": ["I am outside the EU, UK, Republic of Korea and USA, and my use/outputs remain within the Applicable Territory.",
                                         "I accept the complete MiniMax H3 agreement and Exhibit A acceptable-use policy; no training other AI models with H3 works/outputs.",
                                         "Public outputs require clear AI disclosure; retain applicable notices. Commercial and downstream-access conditions still apply."]}
        # Free-space changes do not change the reviewed artifact/terms identity.
        result["digest"] = hashlib.sha256(json.dumps({k:v for k,v in result.items() if k != "free_bytes"}, sort_keys=True).encode()).hexdigest()
        return result

    def _transport_for(self, job):
        # Generic transfers retain their separate disabled-by-default gate.
        return self.h3_transport if job["plan"].get("model_id") == MODEL_ID else self.transport

    def start(self, body):
        # Serialize runtime activation with generation/removal review operations.
        with self.lock:
            if body.repository == recipe(self.project)["repository"] and registered_assets(self.project, self.native):
                raise ManagerError("already_installed", "H3 Optimized is already installed", 409)
            return super().start(body)

    def _activate(self, job, components, stage, cancel):
        if job["plan"].get("model_id") != MODEL_ID:
            return
        self._update(job, state="installing", message="Registering verified H3 files in the private Windows runtime")
        owned_native(self.native)
        self.storage.check_space(16 * 1024**2)
        moved = []
        try:
            for index, component in enumerate(components):
                if cancel.is_set():
                    raise Cancelled()
                source = stage / f"file-{index}.data"
                destination = self.native / "models" / component.destination
                assert_no_links(source); assert_no_links(destination)
                if destination.exists() or not destination.resolve().is_relative_to((self.native / "models").resolve()):
                    raise ManagerError("destination_conflict", "H3 destination is occupied or unsafe", 409)
                if not ArtifactVerifier().verify(source, component, cancel).valid:
                    raise ManagerError("integrity_failed", "Staged H3 artifact changed", 409)
                destination.parent.mkdir(parents=True, exist_ok=True)
                assert_no_links(destination)
                # Same-drive rename avoids a third full-size copy and cannot overwrite.
                source.rename(destination)
                moved.append((source, destination))
            self.validate_nodes(components)
            if cancel.is_set():
                raise Cancelled()
            files = {}
            for component in components:
                p = self.native / "models" / component.destination
                stat = p.stat()
                files[component.destination] = {"identity": [stat.st_size, stat.st_mtime_ns, stat.st_ino], "sha256": component.sha256}
            record = self.native / "receipts/h3-optimized.json"
            temporary = record.with_suffix(".pending")
            assert_no_links(record); assert_no_links(temporary)
            with temporary.open("x", encoding="utf-8") as stream:
                json.dump({"recipe_sha256": RECIPE_HASH, "execution_validated": False, "files": files,
                           "license_acknowledgement": job["license_acknowledgement"]}, stream)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, record)
            self.refresh()
        except Exception:
            for source, destination in reversed(moved):
                assert_no_links(destination); assert_no_links(source)
                if destination.exists() and not source.exists():
                    destination.rename(source)
            raise

    def validate_nodes(self, components):
        client = ComfyUIClient(os.environ.get("DIRECTOR_DEV_COMFY_URL", "http://127.0.0.1:8188"))
        try:
            from director.generation.h3_workflow import build_h3_workflow
            graph = build_h3_workflow("installation schema check", 0, "0" * 32, {"width": 960, "height": 544, "frames": 124, "steps": 20})
            for node_type in {n["class_type"] for n in graph.values()}:
                info = client.request("/object_info/" + node_type)
                if node_type not in info:
                    raise ManagerError("missing_node", "Required native H3 node is unavailable; restart Director and retry", 409)
            for c, loader, field in ((components[0], "UNETLoader", "unet_name"), (components[1], "CLIPLoader", "clip_name"),
                                     (components[2], "VAELoader", "vae_name"), (components[3], "VAELoader", "vae_name")):
                info = client.request("/object_info/" + loader)[loader]
                name = Path(c.destination).name
                if name not in info["input"]["required"][field][0]:
                    raise ManagerError("registration_failed", "ComfyUI did not discover a required H3 component", 409)
        finally:
            client.close()
