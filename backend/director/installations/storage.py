"""An isolated Director-owned namespace; never manages external ComfyUI files."""

import json
import os
import re
import shutil
from pathlib import Path
from uuid import uuid4

from director.installations.schemas import ManagerError, Receipt, manifest_digest
from director.installations.verifier import assert_no_links
from director.models.validation import destination_path, relative_file_path


def inspect_owned_inventory(bundle: Path, expected: set[Path]) -> tuple[set[Path], list[Path]]:
    """Shared fail-closed inventory check for model and runtime removal/verification."""
    files: set[Path] = set()
    directories: list[Path] = []
    allowed_dirs = {p for file in expected for p in file.parents if p.is_relative_to(bundle)}
    def inspect(directory: Path) -> None:
        assert_no_links(directory)
        for child in directory.iterdir():
            assert_no_links(child)
            if child.is_dir():
                if child not in allowed_dirs:
                    raise ManagerError("unowned_files", "Unexpected files/directories exist; operation refused")
                inspect(child)
                directories.append(child)
            elif child.is_file() and child.stat().st_nlink == 1:
                files.add(child)
            else:
                raise ManagerError("unsafe_removal", "Unsafe entry in installation")
    inspect(bundle)
    if files - expected or set(directories) - allowed_dirs:
        raise ManagerError("unowned_files", "Unexpected files/directories exist; operation refused")
    return files, directories


class ModelStorageManager:
    def __init__(self, root: Path, safety_margin_bytes: int = 16 * 1024 * 1024, *,
                 namespace: str = ".director", owner_format: str = "director-model-storage-v1"):
        if (namespace, owner_format) not in {
            (".director", "director-model-storage-v1"),
            (".director-runtime", "director-runtime-storage-v1"),
        }:
            raise ValueError("Unsupported owned storage namespace")
        self.root = root.absolute()
        self.base = self.root / namespace
        self.owner_format = owner_format
        self.margin = safety_margin_bytes
        self._lock_file = None
        self.validate_root()

    def validate_root(self) -> None:
        try:
            assert_no_links(self.root)
            if self.root.parent == self.root or str(self.root).startswith("\\\\"):
                raise ValueError("Use a dedicated local storage directory, not a drive/network root")
            for parent in [self.root, *self.root.parents]:
                if parent.name.casefold() == "comfyui" or (parent / "folder_paths.py").is_file():
                    raise ValueError("External ComfyUI directories cannot be managed")
            if self.root.exists() and not self.root.is_dir():
                raise ValueError("Storage root must be a directory")
        except (OSError, ValueError) as error:
            raise ManagerError("unsafe_storage", str(error)) from error

    def path(self, *parts: str) -> Path:
        self.validate_root()
        path = self.base.joinpath(*parts)
        try:
            for part in parts:
                relative_file_path(part)
                if "/" in part:
                    raise ValueError("Internal path segments cannot contain separators")
            assert_no_links(path)
            if not path.resolve().is_relative_to(self.base.resolve()):
                raise ValueError("Path escapes owned storage")
        except (OSError, ValueError) as error:
            raise ManagerError("unsafe_path", "Unsafe path or filesystem link") from error
        return path

    def component_path(self, bundle: Path, relative: str) -> Path:
        self.validate_root()
        path = bundle.joinpath(*relative.split("/"))
        try:
            destination_path(relative)
            assert_no_links(path)
            if not path.resolve().is_relative_to(self.base.resolve()):
                raise ValueError("Path escapes owned storage")
        except (ValueError, OSError) as error:
            raise ManagerError("unsafe_path", "Unsafe component destination") from error
        return path

    def read_json(self, path: Path) -> dict:
        assert_no_links(path)
        if not path.resolve().is_relative_to(self.base.resolve()) or path.stat().st_nlink != 1:
            raise ManagerError("unsafe_record", "Record is not an owned regular file")
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ManagerError("invalid_record", "Record exceeds size limit")
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, data: dict) -> None:
        self.validate_root()
        assert_no_links(path)
        if not path.resolve().is_relative_to(self.base.resolve()):
            raise ManagerError("unsafe_path", "Record escapes owned storage")
        path.parent.mkdir(parents=True, exist_ok=True)
        assert_no_links(path.parent)
        if path.exists() and path.stat().st_nlink != 1:
            raise ManagerError("unsafe_record", "Hardlinked records cannot be replaced")
        temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(data, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        assert_no_links(path)
        os.replace(temporary, path)

    def ensure_owned(self) -> None:
        if self._lock_file is not None:
            self.path("owner.json")
            return
        self.validate_root()
        self.root.mkdir(parents=True, exist_ok=True)
        marker = self.path("owner.json")
        if self.base.exists():
            try:
                owner = self.read_json(marker)
                if owner.get("format") != self.owner_format or not re.fullmatch(r"[0-9a-f]{32}", owner.get("id", "")):
                    raise ValueError()
            except (OSError, ValueError):
                raise ManagerError("unowned_storage", "Existing namespace is not owned; choose another root")
        else:
            self.base.mkdir()
            self.write_json(marker, {"format": self.owner_format, "id": uuid4().hex})
        lock_path = self.path("manager.lock")
        stream = lock_path.open("a+b")
        try:
            if lock_path.stat().st_nlink != 1:
                raise OSError()
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                if lock_path.stat().st_size == 0:
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            stream.close()
            raise ManagerError("storage_busy", "Another manager owns this storage root", 409)
        self._lock_file = stream

    def close(self) -> None:
        if self._lock_file is not None:
            self._lock_file.close()
            self._lock_file = None

    def check_space(self, required_bytes: int) -> None:
        self.validate_root()
        ancestor = self.root
        while not ancestor.exists():
            ancestor = ancestor.parent
        try:
            free = shutil.disk_usage(ancestor).free
        except OSError:
            raise ManagerError("unknown_disk_space", "Storage free space could not be measured")
        if free < required_bytes + self.margin:
            raise ManagerError("insufficient_disk_space", "Insufficient space for remaining writes and safety margin")

    def staging(self, job_id: str) -> Path:
        return self.path("staging", job_id, "bundle")

    def installed(self, model_id: str, job_id: str) -> Path:
        return self.path("installed", model_id, job_id)

    def active(self, model_id: str) -> Receipt | None:
        pointer = self.path("installations", model_id + ".json")
        if not pointer.exists():
            return None
        try:
            record = self.read_json(pointer)
            job_id = record["job_id"]
            if not re.fullmatch(r"[0-9a-f]{32}", job_id):
                raise ValueError()
            receipt = Receipt.model_validate(self.read_json(self.installed(model_id, job_id) / "receipt.json"))
            if (receipt.model_id != model_id or receipt.job_id != job_id
                    or receipt.manifest.id != model_id
                    or receipt.manifest_digest != manifest_digest(receipt.manifest)
                    or len(receipt.verification) != len(receipt.manifest.components)
                    or not receipt.manifest.components
                    or any(not result.valid for result in receipt.verification)):
                raise ValueError()
            for component, result in zip(receipt.manifest.components, receipt.verification):
                if (result.component_id != component.id or result.actual_size != component.expected_size_bytes
                        or result.actual_sha256 != component.sha256):
                    raise ValueError()
            return receipt
        except (KeyError, OSError, ValueError):
            raise ManagerError("invalid_receipt", "Installation receipt is missing or invalid; manual recovery required")

    def activate(self, receipt: Receipt) -> None:
        stage = self.staging(receipt.job_id)
        installed = self.installed(receipt.model_id, receipt.job_id)
        self.write_json(stage / "receipt.json", receipt.model_dump(mode="json"))
        journal = self.path("journals", receipt.job_id + ".json")
        self.write_json(journal, {"operation": "install", "model_id": receipt.model_id, "job_id": receipt.job_id})
        installed.parent.mkdir(parents=True, exist_ok=True)
        assert_no_links(stage)
        assert_no_links(installed)
        if installed.exists() or stage.stat().st_dev != installed.parent.stat().st_dev:
            raise ManagerError("activation_failed", "Activation requires a new destination on the same volume")
        stage.rename(installed)
        self.write_json(self.path("installations", receipt.model_id + ".json"), {"job_id": receipt.job_id})

    def remove(self, receipt: Receipt) -> None:
        """Delete only the exact receipt inventory; unknown additions block removal."""
        bundle = self.installed(receipt.model_id, receipt.job_id)
        expected = {self.component_path(bundle, c.destination) for c in receipt.manifest.components}
        expected |= {bundle / "receipt.json"}
        expected |= {bundle / "licenses" / (document.id + ".txt") for document in receipt.manifest.license_documents}
        files, directories = inspect_owned_inventory(bundle, expected)
        self.write_json(self.path("journals", receipt.job_id + ".json"), {
            "operation": "remove", "model_id": receipt.model_id, "job_id": receipt.job_id,
        })
        pointer = self.path("installations", receipt.model_id + ".json")
        if pointer.exists():
            pointer.unlink()
        # All final targets were validated above; recheck before each deletion.
        for file in files:
            assert_no_links(file)
            if not file.resolve().is_relative_to(bundle.resolve()) or file.stat().st_nlink != 1:
                raise ManagerError("unsafe_removal", "Installation changed during removal")
            file.unlink()
        for directory in directories:
            assert_no_links(directory)
            directory.rmdir()
        bundle.rmdir()
