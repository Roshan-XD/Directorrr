import hashlib
import os
import stat
from pathlib import Path
from threading import Event

from director.installations.schemas import Cancelled, VerificationResult
from director.models.schemas import ModelComponent


def is_link(path: Path) -> bool:
    """Include Windows junctions/reparse points and broken symlinks."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def assert_no_links(path: Path) -> None:
    for item in [path, *path.parents]:
        if is_link(item):
            raise ValueError("Symlinks and reparse points are not permitted")


class ArtifactVerifier:
    def verify(self, path: Path, component: ModelComponent, cancel: Event | None = None) -> VerificationResult:
        result = VerificationResult(component_id=component.id, valid=False, code="missing",
                                    expected_size=component.expected_size_bytes, expected_sha256=component.sha256)
        if component.expected_size_bytes is None or component.sha256 is None:
            result.code = "missing_integrity_metadata"
            return result
        try:
            assert_no_links(path)
            if not path.exists():
                return result
            before = path.stat()
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                result.code = "unsafe_file"
                return result
            result.actual_size = before.st_size
            if before.st_size != component.expected_size_bytes:
                result.code = "size_mismatch"
                return result
            checksum = hashlib.sha256()
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                    result.code = "changed_during_verification"
                    return result
                while chunk := stream.read(1024 * 1024):
                    if cancel is not None and cancel.is_set():
                        raise Cancelled()
                    checksum.update(chunk)
            assert_no_links(path)
            after = path.stat()
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
            ):
                result.code = "changed_during_verification"
                return result
            result.actual_sha256 = checksum.hexdigest()
            result.valid = result.actual_sha256 == component.sha256
            result.code = "verified" if result.valid else "checksum_mismatch"
        except ValueError:
            result.code = "unsafe_file"
        except OSError:
            result.code = "unreadable"
        return result
