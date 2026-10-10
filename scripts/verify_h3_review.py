"""Read-only launcher-session HTTP review; no credentials/weights in receipts."""
import json
from pathlib import Path

import httpx


def main():
    with httpx.Client(base_url="http://127.0.0.1:5173", timeout=30, trust_env=False) as client:
        path = "/api/product/h3/installation-plan"
        headers = {"Origin": "http://127.0.0.1:5173", "X-Director-Session": "launcher"}
        response = client.get(path, headers=headers)
        response.raise_for_status()
        plan = response.json()
        result = {"status": response.status_code, "repository": plan["repository"],
                  "revision": plan["revision"], "files": len(plan["files"]),
                  "download_bytes": plan["download_bytes"], "required_free_bytes": plan["required_free_bytes"],
                  "free_bytes": plan["free_bytes"], "hardware": plan["hardware"],
                  "can_install": plan["can_install"], "ready": plan["ready"], "blockers": plan["blockers"],
                  "missing_auth_status": client.get(path).status_code,
                  "untrusted_origin_status": client.get(path, headers={**headers, "Origin": "http://evil.invalid"}).status_code,
                  "weights_transferred": 0, "inference_started": 0}
        assert result["missing_auth_status"] == result["untrusted_origin_status"] == 403
        assert not plan["can_install"] and not plan["ready"]
        (Path(__file__).resolve().parents[1] / "docs/h3-live-review.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))


if __name__ == "__main__":
    main()
