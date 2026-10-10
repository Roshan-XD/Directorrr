"""Explicit small LICENSE transfer check; never model weights or activation."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from director.installations.downloader import HuggingFaceDownloader
from director.models.schemas import ModelComponent
from director.product.discovery import Discovery
from director.product.downloads import DownloadManager, StartDownload
from director.product.optimized_h3 import recipe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inherited-offline", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    r = recipe(root)
    metadata = Discovery().fetch(f"/api/models/{r['repository']}/revision/{r['revision']}", {"blobs": "true"})
    file = next(f for f in metadata["siblings"] if f["rfilename"] == "LICENSE")
    data = r["license_text"].encode()
    assert len(data) == file["size"] < 128 * 1024
    assert hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() == file["blobId"]
    c = ModelComponent(id="license-check", role="config", repository_id=r["repository"],
        pinned_revision=r["revision"], filename="LICENSE", destination="checkpoints/license.data",
        expected_size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    plan = {"repository":r["repository"], "revision":r["revision"], "components":[c.model_dump(mode="json")],
            "total_bytes":len(data), "required_free_bytes":len(data)*2+16*1024**2,
            "license_sha256":c.sha256, "blockers":[], "digest":"a"*64}
    class SmallCheck(DownloadManager):
        def plan(self, body):
            return plan
    # Match the launcher backend environment, not an unrelated manual shell.
    if args.inherited_offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
    mode = "offline-reproduction" if args.inherited_offline else "fixed-transfer"
    manager = SmallCheck(root/".verification"/"h3-transfer-check"/mode, None,
                         transport=HuggingFaceDownloader(enabled=True, timeout_seconds=90))
    try:
        job = manager.start(StartDownload(repository=r["repository"],files=["LICENSE"],
            digest=plan["digest"],confirmed=True,accepted_license=True))
        manager.threads[-1].join(100)
        result = manager.jobs[job["id"]]
        print(json.dumps({k:result.get(k) for k in ("state","message","technical_details","verified_bytes")}))
        if result["state"] == "completed":
            final = manager.storage.path("downloads",job["id"],"file-0.data")
            assert final.read_bytes() == data
            final.unlink()  # Exact small test artifact only; no model/user files.
            print("PASS: spawned SDK worker -> owned cache -> size/SHA-256 verification -> managed final file; test artifact removed")
    finally:
        manager.close()


if __name__ == "__main__":
    main()
