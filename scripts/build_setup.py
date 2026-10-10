"""Build a small source/UI/bootstrap release; never bundle private runtimes."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "releases"
    output.mkdir(exist_ok=True)
    compiler = Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    if not compiler.is_file():
        raise RuntimeError("The Windows .NET Framework C# compiler is required by the release builder")
    exe = output / "Setup Director.exe"
    subprocess.run([str(compiler), "/nologo", "/target:winexe", "/platform:x64", "/out:" + str(exe),
                    "/r:System.Windows.Forms.dll", "/r:System.IO.Compression.dll",
                    "/r:System.IO.Compression.FileSystem.dll", str(ROOT / "setup/Bootstrap.cs")], check=True, cwd=ROOT)
    assets = ROOT / "frontend/dist"
    if not (assets / "index.html").is_file():
        raise RuntimeError("Build the packaged frontend first")
    ui = {p.relative_to(assets).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in assets.rglob("*") if p.is_file()}
    ui_manifest = output / "ui-manifest.json"
    ui_manifest.write_text(json.dumps(ui, indent=2) + "\n")
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    archive = output / "Director-Windows-Setup.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as release:
        for name in sorted(filter(None, files)):
            if name.startswith(("runtime/", ".venv/", "generated_videos/", "docs/final-evidence/", "setup/state/", "releases/", ".verification/")) or "/node_modules/" in name:
                raise ValueError("Private file in release inventory")
            p = ROOT / name
            if p.is_symlink() or p.stat().st_size > 10 * 1024**2 or p.suffix in {".dll", ".whl", ".safetensors", ".gguf"}:
                raise ValueError("Unexpected binary or oversized release file")
            if name.startswith(".github/"):
                continue
            release.write(p, "Director/" + name)
        release.write(exe, "Director/Setup Director.exe")
        release.write(ui_manifest, "Director/setup/ui-manifest.json")
        for name in ui:
            release.write(assets / name, "Director/frontend/dist/" + name)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(checksum + "  Director-Windows-Setup.zip\n")
    print(json.dumps({"archive": str(archive), "size_bytes": archive.stat().st_size, "sha256": checksum,
                      "bundled_runtime_or_models": False}))


if __name__ == "__main__":
    main()
