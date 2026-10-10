"""Maintainer utility: freeze small official metadata, never wheel bodies."""
import hashlib
import importlib.metadata
import json
import urllib.request
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import canonicalize_name, parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]


def metadata(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        body = response.read(8 * 1024 * 1024 + 1)
    if len(body) > 8 * 1024 * 1024:
        raise ValueError("Metadata limit exceeded")
    return body


def main():
    env = default_environment() | {"python_version": "3.11", "python_full_version": "3.11.9", "extra": ""}
    tags = set(cpython_tags((3, 11), ["cp311"], ["win_amd64"])) | set(compatible_tags((3, 11), "cp311", ["win_amd64"]))
    todo = ["fastapi", "pydantic", "uvicorn", "psutil", "packaging", "httpx", "huggingface-hub"]
    packages = {}
    while todo:
        name = canonicalize_name(todo.pop())
        if name in packages:
            continue
        dist = importlib.metadata.distribution(name)
        version = dist.version
        data = json.loads(metadata(f"https://pypi.org/pypi/{name}/{version}/json"))
        candidates = [f for f in data["urls"] if f["filename"].endswith(".whl") and
                      parse_wheel_filename(f["filename"])[3] & tags]
        if not candidates:
            raise ValueError(f"No approved target wheel: {name} {version}")
        file = sorted(candidates, key=lambda f: f["filename"])[0]
        requirements = dist.requires or []
        for text in requirements:
            requirement = Requirement(text)
            if requirement.marker and not requirement.marker.evaluate(env):
                continue
            selected = importlib.metadata.version(requirement.name)
            if selected not in requirement.specifier:
                raise ValueError(f"Existing backend dependency conflict: {requirement.name}")
            todo.append(requirement.name)
        packages[name] = {"name": name, "version": version, "wheel_filename": file["filename"],
                          "artifact_url": file["url"], "size_bytes": file["size"],
                          "sha256": file["digests"]["sha256"], "requires_dist": requirements}
    output = ROOT / "setup"
    output.mkdir(exist_ok=True)
    (output / "backend-lock.json").write_text(json.dumps({"target": "CPython 3.11 / Windows AMD64",
        "packages": sorted(packages.values(), key=lambda p: p["name"])}, indent=2) + "\n")
    print(f"Frozen {len(packages)} backend wheels; metadata requests only")


if __name__ == "__main__":
    main()
