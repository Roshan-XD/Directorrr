# Milestone 4K — Experimental GPU validation plan

## Phase A follow-up

The [4L Phase A report](experimental-gpu-phase-a.md) records separately authorized acquisition of exactly the 11 artifacts, successful exact size/hash checks and non-executing ZIP/notice inspection. No installation or execution was authorized or performed; unresolved vendor evidence is recorded. The plan below remains a historical proposal for stages B/C, not permission to run them.

Reviewed 9 October 2026. **Plan only: no transfers, installations or GPU execution authorized or performed.** This is a disposable developer experiment, not Director's production installer. Production remains **NO-GO**, `installation_eligible: false`, and real provisioning disabled. No application, profile, lock, consent or security behavior changes.

## 1. Question and evidence

Can the pinned Windows PyTorch build import, recognize the RTX 5080 Laptop and execute one tiny CUDA tensor operation? Prefer **standard CPython 3.13.16 x64 / torch 2.12.1+cu130**, retaining approved pins. The [official PyTorch version table](https://pytorch.org/get-started/previous-versions/) documents 2.12.1 with the CUDA 13.0 index for Windows; the [complete lock](../runtime_profiles/locks/wan-windows-cp313-cu130.lock.json) records its exact `cp313-cp313-win_amd64` wheel metadata. This documents artifact availability and ABI selection, not operation on this computer.

NVIDIA's [GPU capability table](https://developer.nvidia.com/cuda/gpus) lists RTX 5080 at compute capability 12.0. Applying that to the Laptop variant is a family-based expectation, **not a measured capability**. [CUDA driver compatibility documentation](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html) places CUDA 13.x in the driver >=580 branch; the historical detected 616.92 is plausible. Its driver-reported CUDA 13.4 is neither an installed toolkit nor PyTorch's build version. Recheck observations before execution. A driver version alone cannot establish CUDA availability, kernel support or DLL compatibility.

Existing read-only observations: Windows AMD64, RTX 5080 Laptop, **15.9208984375 GiB total VRAM**, approximately 31.42 GiB RAM. These are historical measurements, not fresh free-memory/free-space checks. Backend Python 3.11.5 is excluded from this experiment. Torch has not been execution-tested. No fallback or changed CUDA build is authorized.

Only ten wheels are needed: torch's seven mandatory dependencies plus mpmath (sympy) and MarkupSafe (Jinja2). Reuse exact selections and selected-wheel metadata from the complete lock; do not resolve again. Do not request extras. **TorchVision, TorchAudio, NumPy, ComfyUI, PyOpenGL, model weights and a standalone CUDA toolkit are excluded.** An optional NumPy warning during torch import must be recorded; it is not permission to install NumPy. This is the minimal mandatory dependency closure for this pinned tensor-only test, not a claim of the smallest possible PyTorch distribution.

## 2. Acquisition and bootstrap gates

Appendix A specifies every allowed artifact, URL, expected size and published hash. They are expected publisher metadata; no binary was acquired or hashed in 4K. Total: **11 artifacts / 1,968,154,400 bytes (1.83299 GiB)**. Ten wheels alone: **1,937,000,993 bytes**. One artifact, torch, is 1,926,432,963 bytes; authorization must explicitly cover this large transfer. No previous bounded PyOpenGL authorization applies here.

Use the official **full** `python-3.13.16-amd64.zip`, not embeddable Python, free-threaded Python, a registered installer or the system interpreter. The [release manifest](https://www.python.org/ftp/python/3.13.16/windows-3.13.16.json) supplies its SHA-256; its 31,153,407-byte HEAD observation is reused from [4G](runtime-installation-readiness.md#1-preferred-isolated-python-bootstrap). [Official extraction guidance](https://docs.python.org/3.14/using/windows.html#offline-installs) permits unregistered full-ZIP use. Guidance does not change the Python version. Version-specific [layout](https://raw.githubusercontent.com/python/cpython/v3.13.16/PC/layout/support/options.py) and [ensurepip source](https://raw.githubusercontent.com/python/cpython/v3.13.16/Lib/ensurepip/__init__.py) support venv and bundled pip 26.2.1. Actual ZIP contents, bundled pip bytes, notices and operation remain untested; internal pip size/hash is unknown and is not a separate transfer.

Future acquisition must use bounded HTTPS transfers of this exact allowlist only, reject unexpected redirects/origins, stream into quarantine, enforce exact byte limits and verify SHA-256 before extraction. Partial files are never executable or accepted. No package-index resolution, automatic retries with different artifacts or unbounded download command is proposed. On interruption retain clearly incomplete quarantine or remove exact owned partial files. Recheck official identity if upstream evidence changes; never silently refresh pins/hashes.

Inspect ZIP entries without executing them: reject traversal, absolute/drive paths, links/reparse points, duplicates, collisions and special files; enforce declared and observed expansion limits. Verify bootstrap contents (`python.exe`, standard library, venv/ensurepip and bundled pip), applicable notices and wheel inventories. Keep reviewed license text with the experiment. Hashes bind bytes to publisher evidence; they are not a signature or independent supply-chain guarantee.

**Authorization stages:** (A) exact artifact acquisition and inert integrity/notice inspection; (B) only after applicable local-use/copy-retention terms are established and explicitly reviewed, private bootstrap extraction, venv and offline wheel installation; (C) explicitly authorized interpreter/torch/CUDA test. Overall approval cannot fill a missing license document or accept terms silently. If acquired evidence leaves local-use obligations uncertain, stop before installation/execution and present that evidence. No production acknowledgement is reused or bypassed.

## 3. Isolated layout and disk budget

Proposed root: **`D:\Director-GPU-Experiment\run-001`**, outside the repository, backend environment and production runtime roots. This directory has **not been created**. Refuse an existing run root. Validate the parent, volume and every created path against reparse/junction/link escapes; create an experiment ownership marker before writes and an exact inventory afterward. Do not point Director's runtime configuration at it.

```text
run-001/
  owner.json                 # experiment identity and approved scope
  artifacts/                # exactly the 11 approved files
  python/                   # private full Python, never registered
  env/                      # final-path venv; never moved
  temp/                     # child-process temporary data
  cache/cuda/               # requested CUDA cache location
  notices/                  # retained reviewed license/notice texts
  logs/                     # bounded redacted output and receipts
  gpu-requirements.txt       # Appendix B, reviewed before execution
  gpu_smoke.py               # listing below, copied only after approval
```

Provisional minimum **20 GiB free on the target volume**, an engineering estimate, not a measured installation minimum: 1.833 GiB retained compressed downloads + 8 GiB expanded Python/venv/wheels + 4 GiB temporary overhead + 4 GiB failure/cleanup reserve = about 17.833 GiB, rounded upward. There is no previous runtime to retain. Installed wheel sizes, filesystem allocation and bootstrap expansion are unknown. After authorized acquisition, use declared archive inventories to refine this budget **before extraction**, then check space before each write/install. If limits are exceeded, stop and request a revised budget. No current disk reprobe occurred in 4K; old 149.197 GiB free-space evidence is not a fresh preflight.

Use child-only TEMP/TMP and CUDA_CACHE_PATH under this root. Never modify persistent environment variables, registry, PATH, drivers, system Python, existing venvs or ComfyUI. Do not use administrator rights. If a missing Visual C++ DLL/runtime or another prerequisite is found, stop: installing it is outside this approval. Windows/driver code may write system/user caches despite requested cache settings; this procedure is isolation by convention, **not an OS sandbox**.

## 4. Future commands — do not run in 4K

First approve scope, acquire/verify artifacts and notices, safely extract the full ZIP, and materialize the reviewed requirements/script. The commands below do not acquire files and are not a ready-to-run installer. Each command executes real software and belongs only to an authorized later milestone.

```powershell
$experimentRoot = 'D:\Director-GPU-Experiment\run-001'
& "$experimentRoot\python\python.exe" -I -B -m venv --copies "$experimentRoot\env"
& "$experimentRoot\env\Scripts\python.exe" -I -B -m pip --isolated --disable-pip-version-check install --no-index --find-links "$experimentRoot\artifacts" --require-hashes --only-binary=:all: --no-deps --no-cache-dir --no-compile -r "$experimentRoot\gpu-requirements.txt"
& "$experimentRoot\env\Scripts\python.exe" -I -B -m pip --isolated --disable-pip-version-check check
& "$experimentRoot\env\Scripts\python.exe" -I -B "$experimentRoot\gpu_smoke.py" --authorize-cuda-test
```

`venv --copies` uses the private base and bundled offline pip; no activation or dependency upgrade. Offline pip accepts only the complete reviewed local set, enforces hashes, forbids source builds and dependency selection; `pip check` checks installed declared requirements. `-I` isolates Python from user site/import environment; it does not sandbox native code. Audit effective pip configuration before installation; unexpected global settings must block the command, not alter the approved destinations or sources. Disable network access during install/test where practical and validate installed distributions and their paths afterward. A future bounded process runner must use fixed executable/argument arrays, no shell interpolation, controlled child environment, bounded output, exit-code checking and **120-second timeout per command**. Stop on the first failure; do not continue to GPU execution after a failed integrity, license, dependency or identity check.

## 5. Minimal smoke-test listing — not an executable deliverable

This listing has not been run, including torch import. A later milestone must review/materialize it and test its reporting with fake torch before GPU execution. CPU/GPU work is deliberately tiny; CUDA context/allocator overhead is larger than the 16-element tensor. It checks one device rather than summing GPUs or selecting a different GPU silently.

```python
import argparse
import json
import platform
import struct
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-cuda-test", action="store_true")
    args = parser.parse_args()
    report = {"gpu_smoke_passed": False, "production_runtime_ready": False,
              "generation_ready": False, "stage": "authorization"}
    if not args.authorize_cuda_test:
        print(json.dumps(report))
        return 2
    try:
        report["stage"] = "interpreter_identity"
        if (sys.version_info[:3] != (3, 13, 16)
                or platform.system() != "Windows"
                or platform.machine().upper() not in {"AMD64", "X86_64"}
                or struct.calcsize("P") != 8):
            raise RuntimeError("Unexpected Python version or platform")
        report["python"] = platform.python_version()
        report["stage"] = "torch_import"
        import torch  # Explicitly executes native code in the future experiment.

        report.update(torch=str(torch.__version__), cuda_build=torch.version.cuda)
        if str(torch.__version__) != "2.12.1+cu130" or torch.version.cuda != "13.0":
            raise RuntimeError("Unexpected torch/CUDA build; no substitution allowed")
        report["stage"] = "cuda_detection"
        report["cuda_available"] = torch.cuda.is_available()
        if not report["cuda_available"]:
            raise RuntimeError("CUDA unavailable; inspect captured diagnostics")
        devices = [(i, torch.cuda.get_device_name(i))
                   for i in range(torch.cuda.device_count())]
        report["devices"] = devices
        matches = [i for i, name in devices
                   if name == "NVIDIA GeForce RTX 5080 Laptop GPU"]
        if len(matches) != 1:
            raise RuntimeError("Expected GPU identity absent or ambiguous; stop for review")
        index = matches[0]
        capability = torch.cuda.get_device_capability(index)
        report["compute_capability"] = list(capability)
        report["compiled_arches"] = torch.cuda.get_arch_list()
        report["total_vram_bytes"] = torch.cuda.get_device_properties(index).total_memory
        if capability != (12, 0):
            raise RuntimeError("Observed capability differs from proposed family expectation")
        report["stage"] = "tiny_tensor"
        device = torch.device("cuda", index)
        values = torch.arange(16, dtype=torch.float32, device=device)
        result = values * 2 + 1
        torch.cuda.synchronize(device)
        actual = result.cpu().tolist()
        if actual != [float(i * 2 + 1) for i in range(16)]:
            raise RuntimeError("GPU tensor result mismatch")
        report.update(stage="complete", gpu_smoke_passed=True)
        print(json.dumps(report))
        return 0
    except Exception as error:
        # Avoid absolute paths, environment dumps or unsanitized exception messages.
        report["error_type"] = type(error).__name__
        report["error"] = "Stage failed; review bounded, redacted process diagnostics"
        print(json.dumps(report))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Record stdout JSON, exit code, stage, approved artifact/installed receipts and redacted bounded stderr. A future runner should sanitize paths/credentials before retaining output; native loader stderr may contain paths. Keyboard interruption, timeout and process crash need distinct runner results. Report compiled architectures as build metadata; successful execution is stronger evidence for this operation, not a guarantee for all kernels. One float32 elementwise operation does not validate cuDNN, cuBLAS, attention, VRAM sufficiency, performance, ComfyUI or Wan. A failure must not trigger downloads, package substitutions, driver changes or model tests.

## 6. Host effects, cleanup and rollback

Approval covers download bandwidth and disk occupancy, execution of the private Python/pip and third-party native torch/CUDA libraries as the current user, GPU initialization and a tiny kernel. Expect a CUDA context, driver activity, possible cache writes, fan/power changes and contention with active applications. A hung GPU operation may not be promptly cancellable; a timeout can stop the owned process but cannot promise immediate driver recovery. No administrator action, reboot or driver reset is proposed. Close GPU-intensive work voluntarily before the test; never terminate unrelated applications.

No production pointer is touched, so failure rollback means stopping only owned child processes, preserving a selected redacted report and removing the disposable owned run. Cleanup must validate ownership and inventory, resolved containment, reparse/link/hard-link safety and unknown additions before deletion. Remove exact validated files then empty directories; do not issue blind recursive deletion, uninstall system Python, clear shared driver caches or kill all Python processes. If user files, unknown additions, locks or links are present, refuse automatic cleanup and report retained files. Restore only experiment-scoped process environment; do not edit persistent host settings. Removal of the venv alone leaves artifacts/base/logs, so the reviewed run inventory must cover all of them.

## 7. Licensing and approval checklist

Production still has **68 unresolved document identities** and 26 captured texts. This narrower experiment excludes ComfyUI/vision/media packages; excluding them is not closing or downgrading production blockers. Python PSF/copy-retention and incorporated OpenSSL/libffi/Expat/Tcl-Tk/Microsoft terms, bundled pip/vendor notices, torch LICENSE/NOTICE plus exact CUDA/vendor binary correspondence, and the nine dependency notices must be reviewed for the acquired bytes. See [4J evidence and uncertainties](runtime-installation-readiness.md#milestone-4j--notice-classification-and-bounded-inspection), [Python terms](https://docs.python.org/3.13/license.html), and [CUDA 13.0 EULA](https://docs.nvidia.com/cuda/archive/13.0.0/eula/index.html). Generic source licenses are not proof of every binary's terms. Private use does not remove all copy-retention or vendor use restrictions. This document is not legal clearance or license acceptance. Redistribution/packaging is out of scope; retain notices and investigate redistribution obligations before a future release. Wan licensing and model download authorization remain completely separate.

- [ ] Approve only the 11 immutable, hash-bound artifact selections below and 1,968,154,400-byte expected transfer; no additional packages or builds.
- [ ] Approve the new disposable root and its bounded cache/temp/log/notices files; require fresh disk and path checks.
- [ ] Acquire and inspect integrity/notices first; stop if applicable terms remain uncertain or require unrecorded acknowledgement.
- [ ] Explicitly review applicable document identities/checksums and acknowledgement requirements before installation; never preselect acceptance.
- [ ] Approve only private extraction, venv/offline pip/dependency verification and the listed GPU smoke command, with bounded process controls.
- [ ] Understand current-user native execution and driver/cache effects; no OS sandbox or universal rollback guarantee.
- [ ] Approve exact-inventory cleanup, with refusal on unknown files/links; preserve a chosen redacted result.
- [ ] Keep production provisioning, generation and model transfers disabled regardless of result.

**Decision: CONDITIONAL experiment proposal; no execution authorization. Production remains NO-GO.** Recommended next milestone: **4L — Separately authorized disposable PyTorch GPU experiment**, staged acquisition/notice inspection first; proceed to installation and CUDA only if the explicit scope and applicable terms are resolved. Stop at the tensor result and cleanup, with no ComfyUI integration.

## 8. Checks performed in 4K

Reviewed relevant existing profiles, complete lock, preflight/license evidence and official compatibility documentation. Computed the ten-wheel subset and transfer totals from existing lock metadata. No executable application/test files changed. The smoke code is a documentation listing only. No artifact transfer, package installation, CUDA execution or automated tests occurred. The last reported backend result remains historical: **369 passed, 3 privilege-related skips, one existing warning**.

## Appendix A — Exact acquisition allowlist

Python bootstrap: [`python-3.13.16-amd64.zip`](https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.zip), **31,153,407 bytes**, published SHA-256 `bbf675bb5e763c1efbb09a3a461b259d81598a63c30c4b0d7ea11b9f063df159`.

The following wheel entries are reproduced from the existing lock, including publisher hashes and exact artifact URLs. They are not new binary inspections.

| Package / exact wheel | Expected bytes | Official artifact / published SHA-256 |
| --- | ---: | --- |
| torch 2.12.1+cu130<br>`torch-2.12.1+cu130-cp313-cp313-win_amd64.whl` | 1926432963 | [Artifact](https://download.pytorch.org/whl/cu130/torch-2.12.1%2Bcu130-cp313-cp313-win_amd64.whl)<br>`76dd848312a40d29499614b714a4318841734ff309ad922f2365868395b6b054` |
| filelock 4.0.12<br>`filelock-4.0.12-py3-none-any.whl` | 111732 | [Artifact](https://files.pythonhosted.org/packages/da/a1/b047e1c486a2c66283633b7dbb73872ca16ca1ce6a426f70d4d037fc8e1c/filelock-4.0.12-py3-none-any.whl)<br>`5f17ee83ecee8a6f3e389c75822fb70a1c2f0506b99438a6dffa1d56793588c8` |
| typing-extensions 4.16.0<br>`typing_extensions-4.16.0-py3-none-any.whl` | 45571 | [Artifact](https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl)<br>`481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` |
| setuptools 81.0.0<br>`setuptools-81.0.0-py3-none-any.whl` | 1062021 | [Artifact](https://files.pythonhosted.org/packages/e1/e3/c164c88b2e5ce7b24d667b9bd83589cf4f3520d97cad01534cd3c4f55fdb/setuptools-81.0.0-py3-none-any.whl)<br>`fdd925d5c5d9f62e4b74b30d6dd7828ce236fd6ed998a08d81de62ce5a6310d6` |
| sympy 1.14.0<br>`sympy-1.14.0-py3-none-any.whl` | 6299353 | [Artifact](https://files.pythonhosted.org/packages/a2/09/77d55d46fd61b4a135c444fc97158ef34a095e5681d0a6c10b75bf356191/sympy-1.14.0-py3-none-any.whl)<br>`e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5` |
| networkx 3.7<br>`networkx-3.7-py3-none-any.whl` | 2142205 | [Artifact](https://files.pythonhosted.org/packages/7e/cd/fe58041e9011f307c490e3e17dd48cc516448f7c698a3f2d9d9d65d7e6a8/networkx-3.7-py3-none-any.whl)<br>`e3fd2c13a7814cee3746340d8d7f8598a67f16a58bf47fb7f8793fab6efca1b0` |
| jinja2 3.1.6<br>`jinja2-3.1.6-py3-none-any.whl` | 134899 | [Artifact](https://files.pythonhosted.org/packages/62/a1/3d680cbfd5f4b8f15abc1d571870c5fc3e594bb582bc3b64ea099db13e56/jinja2-3.1.6-py3-none-any.whl)<br>`85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` |
| fsspec 2026.9.0<br>`fsspec-2026.9.0-py3-none-any.whl` | 221738 | [Artifact](https://files.pythonhosted.org/packages/6c/c0/a98505f18594f1bce828bb159cec0fcf9860562f1a2c85913409fc8f3d9e/fsspec-2026.9.0-py3-none-any.whl)<br>`8dd6e646e99ea382bd85f97a45e6b526a442d79423a7dc673f1e2756d05fcb5f` |
| mpmath 1.3.0<br>`mpmath-1.3.0-py3-none-any.whl` | 536198 | [Artifact](https://files.pythonhosted.org/packages/43/e3/7d92a15f894aa0c9c4b49b8ee9ac9850d6e63b03c9c32c0367a13ae62209/mpmath-1.3.0-py3-none-any.whl)<br>`a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c` |
| markupsafe 3.0.4<br>`markupsafe-3.0.4-cp313-cp313-win_amd64.whl` | 14313 | [Artifact](https://files.pythonhosted.org/packages/6f/36/163da64de88a13db79214ef75fa041be7fa13bdb42261cf5b7484de14bfb/markupsafe-3.0.4-cp313-cp313-win_amd64.whl)<br>`1f1f9477e174582b0a1b583d60b66e1f2cf5d3fe12cee985e4aedf44766600e5` |

## Appendix B — Future hashed requirements file

Save only after separate approval. Every transitive package is explicit; no extras or online resolution.

```text
torch==2.12.1+cu130 --hash=sha256:76dd848312a40d29499614b714a4318841734ff309ad922f2365868395b6b054
filelock==4.0.12 --hash=sha256:5f17ee83ecee8a6f3e389c75822fb70a1c2f0506b99438a6dffa1d56793588c8
typing-extensions==4.16.0 --hash=sha256:481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8
setuptools==81.0.0 --hash=sha256:fdd925d5c5d9f62e4b74b30d6dd7828ce236fd6ed998a08d81de62ce5a6310d6
sympy==1.14.0 --hash=sha256:e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5
networkx==3.7 --hash=sha256:e3fd2c13a7814cee3746340d8d7f8598a67f16a58bf47fb7f8793fab6efca1b0
jinja2==3.1.6 --hash=sha256:85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67
fsspec==2026.9.0 --hash=sha256:8dd6e646e99ea382bd85f97a45e6b526a442d79423a7dc673f1e2756d05fcb5f
mpmath==1.3.0 --hash=sha256:a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c
markupsafe==3.0.4 --hash=sha256:1f1f9477e174582b0a1b583d60b66e1f2cf5d3fe12cee985e4aedf44766600e5
```
