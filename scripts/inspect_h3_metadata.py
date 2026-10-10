"""Explicit metadata-only H3 audit. Never fetch weight files or repository code."""
import hashlib
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "MiniMaxAI/MiniMax-H3"


def fetch(client, path):
    with client.stream("GET", "https://huggingface.co" + path) as response:
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > 2 * 1024 * 1024:
                raise ValueError("Metadata exceeded audit limit")
        return bytes(content)


def main():
    with httpx.Client(timeout=20, trust_env=False, follow_redirects=False) as client:
        head = json.loads(fetch(client, f"/api/models/{REPOSITORY}?blobs=true"))
        revision = head["sha"]
        metadata = json.loads(fetch(client, f"/api/models/{REPOSITORY}/revision/{revision}?blobs=true"))
        if metadata["sha"] != revision:
            raise ValueError("Pinned metadata mismatch")
        index = json.loads(fetch(client, f"/{REPOSITORY}/raw/{revision}/modular_model_index.json"))
        license_text = fetch(client, f"/{REPOSITORY}/raw/{revision}/LICENSE").decode()
        result = {"repository": REPOSITORY, "revision": revision, "metadata_only": True,
                  "index": index, "siblings": metadata["siblings"],
                  "license_text": license_text, "license_sha256": hashlib.sha256(license_text.encode()).hexdigest(),
                  "license_source": f"https://huggingface.co/{REPOSITORY}/blob/{revision}/LICENSE"}
        destination = ROOT / "docs/h3-official-metadata.json"
        destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        # Pin only the T2VA transformer and common component inventory. Never
        # select original checkpoints, the reference transformer or Turbo LoRA.
        folders = {"transformer", "text_encoder", "tokenizer", "processor", "vae", "audio_vae", "scheduler", "audio_scheduler"}
        selected = []
        indexes = {}
        for folder in ("transformer", "text_encoder", "vae"):
            filename = "model.safetensors.index.json" if folder == "text_encoder" else "diffusion_pytorch_model.safetensors.index.json"
            indexes[folder] = json.loads(fetch(client, f"/{REPOSITORY}/raw/{revision}/{folder}/{filename}"))
        for item in metadata["siblings"]:
            name = item["rfilename"]
            folder = name.split("/")[0]
            if folder not in folders and name not in {"LICENSE", "modular_model_index.json"}:
                continue
            if folder in indexes:
                basename = name.split("/")[-1]
                if basename not in {"config.json", "model.safetensors.index.json", "diffusion_pytorch_model.safetensors.index.json", *indexes[folder]["weight_map"].values()}:
                    continue
            lfs = item.get("lfs") or {}
            selected.append({"filename": name, "expected_size_bytes": item["size"],
                             "sha256": lfs.get("sha256"), "git_blob_sha1": item.get("blobId"),
                             "hash_evidence": "published_lfs_sha256" if lfs else "pinned_git_blob_sha1",
                             "url": f"https://huggingface.co/{REPOSITORY}/resolve/{revision}/{name}",
                             "destination": name})
        recipe = {"schema_version": 1, "family_id": "minimax-h3-official-t2va", "repository": REPOSITORY,
                  "revision": revision, "workflow": "t2va", "runtime": "diffusers-modular",
                  "runtime_version": "0.41.0", "status": "review_only", "execution_validated": False,
                  "files": selected, "excluded_folders": ["transformer_ref", "h3-base", "h3-base-ref", "docs"],
                  "license_source": result["license_source"], "license_sha256": result["license_sha256"],
                  "download_bytes": sum(f["expected_size_bytes"] for f in selected),
                  "source": "https://huggingface.co/docs/diffusers/v0.41.0/api/pipelines/minimax_h3"}
        (ROOT / "model_registry/plans/minimax-h3-official-t2va.json").write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"revision": revision, "files": len(metadata["siblings"]), "index": index}))
        print(json.dumps({"selected_files": len(selected), "download_bytes": recipe["download_bytes"]}))


if __name__ == "__main__":
    main()
