"""Upload the setup ZIP to the exact repository; credentials stay in memory."""
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

repo = os.environ.get("GITHUB_REPOSITORY", "Roshan-XD/Directorrr")
tag = os.environ.get("GITHUB_REF_NAME", "v1.1.0-setup-preview.1")
if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not re.fullmatch(r"v[0-9A-Za-z_.-]+", tag):
    raise SystemExit("Unexpected release destination")
token = os.environ.pop("GH_TOKEN", "")
if not token:
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\npath=" + repo + ".git\n\n",
                            text=True, capture_output=True, check=True)
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    token = fields.get("password", "")
    if not token:
        raise SystemExit("GitHub sign-in is required")
base = "https://api.github.com/repos/" + repo


def request(url, data, content_type):
    req = urllib.request.Request(url, data=data, method="POST", headers={"Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json", "Content-Type": content_type, "X-GitHub-Api-Version": "2022-11-28"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *_args, **_kwargs):
            raise ValueError("Authenticated release requests cannot redirect")
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=90) as reply:
        return json.load(reply)


release = request(base + "/releases", json.dumps({"tag_name": tag, "name": "Director Windows Setup (Preview)",
    "prerelease": True, "body": "Download Director-Windows-Setup.zip, extract it to a short writable local folder, and open Setup Director.exe. Read docs/install-director.md. The ZIP includes Director code/UI, not third-party runtimes or model weights. Setup separately requests terms and download approval. This installer has offline fixture tests; fresh-PC runtime installation still needs validation. Production binary redistribution remains uncleared."}).encode(), "application/json")
for name in ("Director-Windows-Setup.zip", "SHA256SUMS.txt"):
    artifact = Path("releases") / name
    request("https://uploads.github.com/repos/" + repo + "/releases/" + str(release["id"]) + "/assets?name=" + name,
            artifact.read_bytes(), "application/zip" if name.endswith(".zip") else "text/plain")
print("Published setup preview: " + release["html_url"])
