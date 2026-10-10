# Windows runtime dependency lock — Milestones 4E and 4F

## Milestone 4F — Current result

Reviewed **9 October 2026**. The target wheel dependency lock is now **COMPLETE**, with **84 packages**, **84 published wheel SHA-256 values**, and exact selected-wheel dependency metadata for **84/84** selections. An independent offline dependency walk passes with **136 distinct active requirement relationships**, no missing dependency and no unsatisfied version constraint. `installation_eligible`, `authorized_real_installation`, execution validation and generation readiness remain **false**. The complete wheel lock does not include the full Python/bootstrap/ComfyUI-source installation inventory.

### Metadata gaps closed

| Selected wheel | Exact wheel bytes | Sidecar bytes | Result |
| --- | ---: | ---: | --- |
| `torch-2.12.1+cu130-cp313-cp313-win_amd64.whl` | 1,926,432,963 | 31,962 | Exact CUDA-wheel declarations and Python >=3.10 verified |
| `torchvision-0.27.1+cu130-cp313-cp313-win_amd64.whl` | 9,155,394 | 5,610 | Exact CUDA-wheel declarations and Python >=3.10, !=3.14.1 verified |
| `pydantic-2.14.0-py3-none-any.whl` | 487,109 (reused 4E evidence) | 131,572 | Exact selected-wheel declarations and Python >=3.10 verified |

The official [torch cu130 index](https://download.pytorch.org/whl/cu130/torch/) and [TorchVision cu130 index](https://download.pytorch.org/whl/cu130/torchvision/) publish both artifact hashes and metadata-sidecar hashes. Requests to the recorded `download-r2.pytorch.org` origin returned 403. The same exact filenames on official `download.pytorch.org` returned successful HEAD size headers and small metadata bodies. The lock now uses those accessible official URLs; versions, CUDA builds, filenames and published wheel hashes are unchanged.

Sources: [torch sidecar](https://download.pytorch.org/whl/cu130/torch-2.12.1%2Bcu130-cp313-cp313-win_amd64.whl.metadata), [vision sidecar](https://download.pytorch.org/whl/cu130/torchvision-0.27.1%2Bcu130-cp313-cp313-win_amd64.whl.metadata), and [Pydantic sidecar](https://files.pythonhosted.org/packages/2d/eb/9146591cc819d040475bf7f2be786710c7f7eb8083693bf859728da2ca9c/pydantic-2.14.0-py3-none-any.whl.metadata). Only metadata GETs and wheel HEAD requests were made; no wheel body was requested. This follows [PyPA's distribution metadata sidecar mechanism](https://packaging.python.org/en/latest/specifications/simple-repository-api/#serve-distribution-metadata-in-the-simple-repository-api). Redirects were restricted to approved official origins, with ten-second timeouts and an explicit 512 KiB metadata ceiling. Pydantic exceeded the former 128 KiB ceiling by only 500 bytes.

| Metadata snapshot | Observed SHA-256 | Independently published sidecar hash |
| --- | --- | --- |
| torch | `4ad71ae45aa42b90af7e4a937b850dd412104184096f26d31654cbfecf76da8c` | Matches official index |
| torchvision | `9e4576749e2ee4b1e38d14490f6601b2599b72ef02d9fc8579a567c3618d4d76` | Matches official index |
| pydantic | `11c8967cbcd622677943be38b48a3931cc524250acd9d8c7a6386408099c4cf9` | Not independently established in 4F; observed HTTPS metadata digest only |

Torch's required dependencies match the former source-based provisional list: filelock, typing-extensions >=4.10.0, setuptools <82, sympy >=1.13.3, networkx >=2.5.1, jinja2 and fsspec >=0.8.5. Its opt-einsum, optree and pyyaml extras are not requested. TorchVision requires numpy, torch ==2.12.1 and pillow !=8.3.*, >=5.3.0; gdown/scipy extras are not requested. PEP 440 permits the approved local `2.12.1+cu130` version for the public-version constraint `==2.12.1`. Pydantic confirms its four required dependencies and inactive email/timezone extras. No new package or core-pin substitution was necessary.

All 84 recorded name/version identities, Python declarations and dependency lists were also compared against their exact, previously hashed sidecar snapshots, using a separate source-check pass. The pinned requirements snapshot matches the previously hashed official ComfyUI response. PyOpenGL has no `Requires-Python` declaration; mpmath's former empty declaration was normalized to `null`. With exact sidecar evidence, an absent optional header means no declared Python constraint, not a fabricated version floor or execution guarantee.

### Independent verification and safe completion gate

The new [offline validator](../backend/director/runtimes/lock_validation.py) validates the audit schema, normalized package uniqueness, exact versions/wheel identities, CPython/ABI/platform tags, SHA-256 formats, official artifact/index origins, exact URL filenames, recorded sidecar evidence, Python constraints, CUDA pins and candidate-profile consistency. It rejects duplicate JSON keys and bounded input files exceeding 4 MiB. It independently walks the [pinned requirements snapshot](../runtime_profiles/locks/wan-windows-comfyui-requirements.txt), profile pins and package declarations, propagating extras and evaluating markers against the explicit Windows/Python target. It rejects unsupported direct requirements, unresolved OS-release markers, missing dependencies, orphan selections and conflicting requirements. It never trusts resolver relationship or incoming-constraint records to prove closure. The old `relationships` array retains 4E expansion history; the independent result records a fresh distinct relationship count.

Complete means internally consistent, closed **recorded wheel metadata**, with every selected artifact size/hash/source known. The checker does not authenticate remote publishers offline, verify untransferred wheel bytes, prove global optimal resolution, validate DLLs/imports, or test ComfyUI APIs. It uses the existing `packaging` parser for standards rather than the old resolver's selection algorithm. Research-sidecar caches remain ignored; the normal CLI checks the recorded evidence and supplied root snapshot without needing that cache. Published wheel hashes must still be checked against actual bytes during a separately authorized transfer.

From the repository root, run this read-only audit with the existing backend interpreter:

```powershell
.\.venv\Scripts\python.exe -m director.runtimes.lock_validation --lock runtime_profiles/locks/wan-windows-cp313-cu130.lock.json --profile runtime_profiles/wan-windows-candidate.json --requirements runtime_profiles/locks/wan-windows-comfyui-requirements.txt
```

Exit 0 means complete metadata; exit 2 means valid but incomplete; exit 1 means invalid inputs/checks. No result writes files, invokes a package manager, authorizes installation or changes provisioning controls. The API, frontend, runtime profile pins and fixture-only provisioning implementation are unchanged.

### Size, tests and remaining blockers

Exact wheel artifact inventory: **2,677,041,805 bytes (2.49319 GiB)** across all 84 selections. This is published PyPI size metadata plus official torch/vision HEAD headers, **not measured binary downloads or installed size**. The full-runtime size remains unknown until Python/bootstrap/source artifacts are inventoried. Temporary cache, staging, expanded files and rollback need separate space calculations.

Focused validator tests cover valid data, missing dependencies, duplicates, invalid hashes, wrong platform tags, conflicts, wrong CUDA wheels, missing metadata/sizes/evidence, markers/extras, unsafe URLs, false completion and authorization claims, root/profile identity, and the real lock's offline regression. See [verification history](verification.md) for final counts and commands.

**No remaining dependency-metadata blocker was found for this wheel lock. Real installation remains blocked** by the private full-Python/bootstrap mechanism and artifacts, exact ComfyUI source integrity inventory, runtime package/binary license and notice review, isolated installer/rollback implementation, disk checks and explicit authorization. Broad newest-version selections (including transformers 5.19.0) remain execution-untested; metadata consistency does not prove ComfyUI API compatibility. Wan license-document and conversion-provenance blockers remain separate and unresolved.

Recommended **Milestone 4G — Bootstrap/source inventory and runtime license review**: freeze the isolated Python mechanism, bootstrap and ComfyUI-source URLs/sizes/hashes, review software/binary notices and consent requirements, and produce a complete software-only installation plan with staging/rollback/disk gates. Keep real provisioning disabled until a later explicitly authorized implementation and execution-validation phase. No model download is authorized by this lock.

## Historical Milestone 4E report

The remainder records the original incomplete 4E result. The current lock, sizes and completion status are given above; the historical gaps below have been closed by 4F.

Reviewed **9 October 2026**. Result: **INCOMPLETE, installation-ineligible**. The lock selects **84 package artifacts**, all with published SHA-256 values, but cannot certify the complete dependency closure of the approved CUDA wheels. No packages, wheels, ComfyUI archives or weights were downloaded or installed. No CUDA or ComfyUI execution occurred.

## 1. Resolution method

The research used bounded read-only official JSON and wheel metadata, with the existing backend Python/`packaging` library as a text parser. It did not run pip, build hooks, package imports, installers or a runtime interpreter. A local ignored research helper rejects binary GETs and unapproved origins, checks redirected URLs and uses ten-second HTTP timeouts. JSON responses are limited to 2 MiB and wheel `.metadata` files to 128 KiB. Large PyPI release histories were not fetched in full: a bounded 128 KiB prefix supplied the current project `info`, followed by smaller version-specific JSON. Cached metadata avoided re-fetching successful responses.

The resolver started with all **34 direct requirements** at the pinned ComfyUI commit, including the six labelled nonessential upstream. It added exact torch/vision constraints, normalized names, selected non-yanked stable wheels published by the audit date, matched standard Windows CPython 3.13 tags and `Requires-Python`, and expanded applicable dependency markers/extras. Target values were supplied explicitly rather than inherited from the Python 3.11 research host.

Selection generally chooses the newest eligible version inside all known constraints, while preserving upstream exact pins, the 4D audited template branch and the approved CUDA core. This is bounded fixed-point constraint selection with a reviewed multidict history choice, **not a general backtracking SAT resolver**. Six passes converged, and final checks found every recorded active requirement satisfied by the selected version. Such a check proves consistency of the observed graph only; it cannot discover dependencies hidden by unavailable metadata or establish package API/runtime compatibility.

Official metadata behavior and tag meanings follow [PyPI's JSON API](https://docs.pypi.org/api/json/), [PyPA core metadata](https://packaging.python.org/en/latest/specifications/core-metadata/) and [platform compatibility tags](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/). Distribution-specific metadata can differ between artifacts. Published release JSON is not silently treated as exact selected-wheel metadata.

## 2. Exact target environment

| Property | Frozen target |
| --- | --- |
| OS / machine | Windows, AMD64 / x86-64; `os_name=nt`, `sys_platform=win32` |
| Interpreter | Standard CPython **3.13.16**, interpreter/ABI `cp313-cp313`; no free-threaded variant |
| Wheel platform | `win_amd64`; compatible CPython stable-ABI and pure-Python tags allowed |
| Torch | **2.12.1+cu130**, exact official Windows CPython 3.13 wheel |
| TorchVision | **0.27.1+cu130**, exact official Windows CPython 3.13 wheel |
| ComfyUI | **v0.39.0**, commit `b0b743566f65daafc423b4fea8a2fbda94b3384a` |
| Root input | [Immutable requirements](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/requirements.txt) plus Director's two approved core constraints |

Unknown Windows release/version are explicitly `UNKNOWN`. No observed requirement needed those marker fields; a future requirement that does would block evaluation rather than borrowing the host's values. Python 3.13.16 was used for marker/floor evaluation, not installed or executed. AMD/Intel and other platforms are outside this selected CUDA lock, not declared universally unsupported by Director.

## 3. Lock artifact, count and completeness

Lock: [wan-windows-cp313-cu130.lock.json](../runtime_profiles/locks/wan-windows-cp313-cu130.lock.json).

It is stored under `runtime_profiles/locks/`, **not beside the top-level profile JSON files**. Existing application startup loads only `runtime_profiles/*.json` as RuntimeProfile objects. This separate audit format is neither imported as a runtime profile nor consumed by an installer, preserving startup behavior without changing application code.

The lock includes:

- Exact name/version, official source index, artifact URL and wheel filename/tags for 84 selected packages.
- Published artifact SHA-256, published byte size where known, Python floor, requested extras and incoming constraints.
- Raw dependency declarations, target-evaluated relationships (including inactive markers), and per-package evidence scope.
- Source URLs and observed hashes of bounded metadata responses. Prefix hashes explicitly identify only the bounded prefix, not the complete JSON response.
- Candidate profile file SHA-256, immutable ComfyUI input, missing metadata/issues, and false installation/authorization/execution flags.

**84 packages are selected; the full dependency count remains unknown.** The recorded graph has 134 active relationship records and 1,022 total records including inactive markers and repeated expansion paths. These are record counts, not unique dependency-edge counts. All active targets currently have selected artifacts. The 34 roots and the previously audited eight template subpackages are covered.

Selected-wheel sidecar metadata supplied dependency declarations for **81 packages**. Pydantic uses version-specific release JSON only because its selected wheel sidecar exceeds the 128 KiB ceiling. Torch's provisional edges reuse the pinned source packaging declarations; TorchVision's provisional edges use version-specific PyPI metadata for the public release, not exact cu130 Windows-wheel metadata. The lock puts those two lists in `provisional_requires_dist`, keeps exact `requires_dist: null`, and labels their outgoing relationships as inferred. Its graph is therefore **not complete or installation eligible**, despite a converged known graph and complete artifact-hash coverage for those 84 selections.

All selected versions and sources appear in the JSON; the table below is a navigable summary, not a second independent lock.

| Package | Exact selection | Wheel tags | Dependency evidence |
| --- | --- | --- | --- |
| [aiohappyeyeballs](https://pypi.org/simple/aiohappyeyeballs/) | 2.7.1 | py3-none-any | wheel sidecar |
| [aiohttp](https://pypi.org/simple/aiohttp/) | 3.14.4 | cp313-cp313-win_amd64 | wheel sidecar |
| [aiosignal](https://pypi.org/simple/aiosignal/) | 1.4.0 | py3-none-any | wheel sidecar |
| [alembic](https://pypi.org/simple/alembic/) | 1.20.0 | py3-none-any | wheel sidecar |
| [annotated-doc](https://pypi.org/simple/annotated-doc/) | 0.0.5 | py3-none-any | wheel sidecar |
| [annotated-types](https://pypi.org/simple/annotated-types/) | 0.8.0 | py3-none-any | wheel sidecar |
| [anyio](https://pypi.org/simple/anyio/) | 4.15.1 | py3-none-any | wheel sidecar |
| [attrs](https://pypi.org/simple/attrs/) | 26.1.0 | py3-none-any | wheel sidecar |
| [av](https://pypi.org/simple/av/) | 19.0.1 | cp312-abi3-win_amd64 | wheel sidecar |
| [blake3](https://pypi.org/simple/blake3/) | 1.0.11 | cp313-cp313-win_amd64 | wheel sidecar |
| [certifi](https://pypi.org/simple/certifi/) | 2026.7.22 | py3-none-any | wheel sidecar |
| [charset-normalizer](https://pypi.org/simple/charset-normalizer/) | 3.5.2 | cp313-cp313-win_amd64 | wheel sidecar |
| [click](https://pypi.org/simple/click/) | 8.5.0 | py3-none-any | wheel sidecar |
| [colorama](https://pypi.org/simple/colorama/) | 0.4.6 | py2-none-any, py3-none-any | wheel sidecar |
| [comfy-aimdo](https://pypi.org/simple/comfy-aimdo/) | 0.5.5 | cp39-abi3-win_amd64 | wheel sidecar |
| [comfy-angle](https://pypi.org/simple/comfy-angle/) | 0.1.1 | py3-none-win_amd64 | wheel sidecar |
| [comfy-kitchen](https://pypi.org/simple/comfy-kitchen/) | 0.2.37 | cp312-abi3-win_amd64 | wheel sidecar |
| [comfyui-embedded-docs](https://pypi.org/simple/comfyui-embedded-docs/) | 0.5.13 | py3-none-any | wheel sidecar |
| [comfyui-frontend-package](https://pypi.org/simple/comfyui-frontend-package/) | 1.53.10 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates](https://pypi.org/simple/comfyui-workflow-templates/) | 0.11.76 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-core](https://pypi.org/simple/comfyui-workflow-templates-core/) | 0.3.367 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-json](https://pypi.org/simple/comfyui-workflow-templates-json/) | 0.1.102 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-media-api](https://pypi.org/simple/comfyui-workflow-templates-media-api/) | 0.3.84 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-media-assets-01](https://pypi.org/simple/comfyui-workflow-templates-media-assets-01/) | 0.1.48 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-media-assets-02](https://pypi.org/simple/comfyui-workflow-templates-media-assets-02/) | 0.1.9 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-media-image](https://pypi.org/simple/comfyui-workflow-templates-media-image/) | 0.3.160 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-media-other](https://pypi.org/simple/comfyui-workflow-templates-media-other/) | 0.3.229 | py3-none-any | wheel sidecar |
| [comfyui-workflow-templates-media-video](https://pypi.org/simple/comfyui-workflow-templates-media-video/) | 0.3.101 | py3-none-any | wheel sidecar |
| [einops](https://pypi.org/simple/einops/) | 0.8.2 | py3-none-any | wheel sidecar |
| [filelock](https://pypi.org/simple/filelock/) | 4.0.12 | py3-none-any | wheel sidecar |
| [frozenlist](https://pypi.org/simple/frozenlist/) | 1.8.0 | cp313-cp313-win_amd64 | wheel sidecar |
| [fsspec](https://pypi.org/simple/fsspec/) | 2026.9.0 | py3-none-any | wheel sidecar |
| [h11](https://pypi.org/simple/h11/) | 0.16.0 | py3-none-any | wheel sidecar |
| [hf-xet](https://pypi.org/simple/hf-xet/) | 1.7.0 | cp38-abi3-win_amd64 | wheel sidecar |
| [httpcore](https://pypi.org/simple/httpcore/) | 1.0.9 | py3-none-any | wheel sidecar |
| [httpx](https://pypi.org/simple/httpx/) | 0.28.1 | py3-none-any | wheel sidecar |
| [huggingface-hub](https://pypi.org/simple/huggingface-hub/) | 1.33.0 | py3-none-any | wheel sidecar |
| [idna](https://pypi.org/simple/idna/) | 3.20 | py3-none-any | wheel sidecar |
| [jinja2](https://pypi.org/simple/jinja2/) | 3.1.6 | py3-none-any | wheel sidecar |
| [kornia](https://pypi.org/simple/kornia/) | 0.8.3 | py3-none-any | wheel sidecar |
| [kornia-rs](https://pypi.org/simple/kornia-rs/) | 0.2.0 | cp313-cp313-win_amd64 | wheel sidecar |
| [mako](https://pypi.org/simple/mako/) | 1.4.3 | py3-none-any | wheel sidecar |
| [markdown-it-py](https://pypi.org/simple/markdown-it-py/) | 4.2.0 | py3-none-any | wheel sidecar |
| [markupsafe](https://pypi.org/simple/markupsafe/) | 3.0.4 | cp313-cp313-win_amd64 | wheel sidecar |
| [mdurl](https://pypi.org/simple/mdurl/) | 0.1.2 | py3-none-any | wheel sidecar |
| [mpmath](https://pypi.org/simple/mpmath/) | 1.3.0 | py3-none-any | wheel sidecar |
| [multidict](https://pypi.org/simple/multidict/) | 6.9.1 | cp313-cp313-win_amd64 | wheel sidecar |
| [networkx](https://pypi.org/simple/networkx/) | 3.7 | py3-none-any | wheel sidecar |
| [numpy](https://pypi.org/simple/numpy/) | 2.5.3 | cp313-cp313-win_amd64 | wheel sidecar |
| [packaging](https://pypi.org/simple/packaging/) | 26.3 | py3-none-any | wheel sidecar |
| [pillow](https://pypi.org/simple/pillow/) | 12.3.0 | cp313-cp313-win_amd64 | wheel sidecar |
| [propcache](https://pypi.org/simple/propcache/) | 0.5.4 | cp313-cp313-win_amd64 | wheel sidecar |
| [psutil](https://pypi.org/simple/psutil/) | 7.2.2 | cp37-abi3-win_amd64 | wheel sidecar |
| [pydantic](https://pypi.org/simple/pydantic/) | 2.14.0 | py3-none-any | release JSON only |
| [pydantic-core](https://pypi.org/simple/pydantic-core/) | 2.50.0 | cp313-cp313-win_amd64 | wheel sidecar |
| [pydantic-settings](https://pypi.org/simple/pydantic-settings/) | 2.15.0 | py3-none-any | wheel sidecar |
| [pygments](https://pypi.org/simple/pygments/) | 2.21.0 | py3-none-any | wheel sidecar |
| [pyopengl](https://pypi.org/simple/pyopengl/) | 3.1.10 | py3-none-any | wheel sidecar |
| [python-dotenv](https://pypi.org/simple/python-dotenv/) | 1.2.4 | py3-none-any | wheel sidecar |
| [pyyaml](https://pypi.org/simple/pyyaml/) | 6.0.3 | cp313-cp313-win_amd64 | wheel sidecar |
| [regex](https://pypi.org/simple/regex/) | 2026.9.29 | cp313-cp313-win_amd64 | wheel sidecar |
| [requests](https://pypi.org/simple/requests/) | 2.34.2 | py3-none-any | wheel sidecar |
| [rich](https://pypi.org/simple/rich/) | 15.0.0 | py3-none-any | wheel sidecar |
| [safetensors](https://pypi.org/simple/safetensors/) | 0.8.0 | cp310-abi3-win_amd64 | wheel sidecar |
| [scipy](https://pypi.org/simple/scipy/) | 1.18.1 | cp313-cp313-win_amd64 | wheel sidecar |
| [sentencepiece](https://pypi.org/simple/sentencepiece/) | 0.2.2 | cp313-cp313-win_amd64 | wheel sidecar |
| [setuptools](https://pypi.org/simple/setuptools/) | 81.0.0 | py3-none-any | wheel sidecar |
| [shellingham](https://pypi.org/simple/shellingham/) | 1.5.4 | py2-none-any, py3-none-any | wheel sidecar |
| [simpleeval](https://pypi.org/simple/simpleeval/) | 1.0.8 | py3-none-any | wheel sidecar |
| [spandrel](https://pypi.org/simple/spandrel/) | 0.4.2 | py3-none-any | wheel sidecar |
| [sqlalchemy](https://pypi.org/simple/sqlalchemy/) | 2.1.4 | cp313-cp313-win_amd64 | wheel sidecar |
| [sympy](https://pypi.org/simple/sympy/) | 1.14.0 | py3-none-any | wheel sidecar |
| [tokenizers](https://pypi.org/simple/tokenizers/) | 0.23.2 | cp310-abi3-win_amd64 | wheel sidecar |
| [torch](https://download.pytorch.org/whl/cu130/torch/) | 2.12.1+cu130 | cp313-cp313-win_amd64 | inferred; exact wheel unknown |
| [torchsde](https://pypi.org/simple/torchsde/) | 0.2.6 | py3-none-any | wheel sidecar |
| [torchvision](https://download.pytorch.org/whl/cu130/torchvision/) | 0.27.1+cu130 | cp313-cp313-win_amd64 | inferred; exact wheel unknown |
| [tqdm](https://pypi.org/simple/tqdm/) | 4.70.1 | py3-none-any | wheel sidecar |
| [trampoline](https://pypi.org/simple/trampoline/) | 0.1.2 | py3-none-any | wheel sidecar |
| [transformers](https://pypi.org/simple/transformers/) | 5.19.0 | py3-none-any | wheel sidecar |
| [typer](https://pypi.org/simple/typer/) | 0.27.3 | py3-none-any | wheel sidecar |
| [typing-extensions](https://pypi.org/simple/typing-extensions/) | 4.16.0 | py3-none-any | wheel sidecar |
| [typing-inspection](https://pypi.org/simple/typing-inspection/) | 0.4.4 | py3-none-any | wheel sidecar |
| [urllib3](https://pypi.org/simple/urllib3/) | 2.8.0 | py3-none-any | wheel sidecar |
| [yarl](https://pypi.org/simple/yarl/) | 1.25.1 | cp313-cp313-win_amd64 | wheel sidecar |

## 4. Official sources and evidence boundaries

- [Torch CUDA 13.0 index](https://download.pytorch.org/whl/cu130/torch/) and [TorchVision index](https://download.pytorch.org/whl/cu130/torchvision/): exact `cp313-cp313-win_amd64` filenames and published hashes reused from 4D. No CPU index or alternate CUDA build was selected.
- Versioned `https://pypi.org/pypi/<name>/<version>/json` responses: exact filenames, publisher digests, sizes, Python floors, declared dependency/license metadata and yanked status. PyPI's matching `files.pythonhosted.org` URLs identify binary artifacts; **only their `.metadata` sidecars were read**, never the wheel URL body.
- [Torch source packaging at v2.12.1](https://raw.githubusercontent.com/pytorch/pytorch/v2.12.1/setup.py): provisional torch closure only. Build-injected requirements remain unknown for the approved wheel.
- [TorchVision 0.27.1 release JSON](https://pypi.org/pypi/torchvision/0.27.1/json): provisional release-level edges only; no claim that every build has identical metadata.
- The [4D audit](runtime-artifact-audit.md) supplies the exact previously verified Python/core/template provenance and licensing boundaries. These were reused rather than downloading artifacts to repeat verification.

Observed metadata SHA-256 is a research snapshot identifier computed from metadata text. It is distinct from the **published wheel SHA-256** and is not a claim to have measured or verified a wheel's bytes. The local `.verification/4e-research/` cache/helper is ignored research material, not installed runtime software or an application resolver.

## 5. Conflicts, exclusions and missing artifacts

| Check | Finding | Disposition |
| --- | --- | --- |
| Python floors and ABI | Every selected file matches the target's CPython/abi3/pure tags and its published Python floor | Known metadata checks pass; imports/DLL behavior untested |
| Torch/Vision pairing | Exact versions retained; inferred torchvision `torch==2.12.1` accepts the approved local `+cu130` version under PEP 440 | No core substitution; exact CUDA-wheel edges still missing |
| Windows artifacts | All 84 selections have eligible published wheel filenames; x86/ARM/Linux-only files excluded | No missing wheel in the known closure; unknown closure may add one |
| multidict | Current 7.0.0 fails aiohttp's `<7.0,>=4.5` requirement | [Official release history](https://pypi.org/project/multidict/#history) and version-specific metadata establish **6.9.1**, satisfying recorded constraints; 7.0.0 was not selected |
| Transitive version constraints | Every recorded active incoming specifier is satisfied after convergence | No unresolved known version conflict; no global backtracking proof or API compatibility claim |
| Environment markers/extras | Explicit Windows/CPython target and requested parent extras used; inactive dependencies retained as evidence | No unresolved observed marker; OS release/version stay unknown |
| Torch selected-wheel metadata and size | Not established by 4D; no binary fallback permitted in 4E | Block complete audited lock; source declarations remain provisional |
| TorchVision selected-wheel metadata and size | Not established; generic release metadata is build-ambiguous | Block complete audited lock; no full wheel request attempted |
| Pydantic 2.14.0 sidecar | Advertised metadata exceeds the 128 KiB ceiling; no oversized body read | Release JSON remains provisional; exact wheel metadata review deferred |

Several broad upstream ranges permit newer major packages (for example transformers 5.19.0). They are **metadata-consistent candidates**, not evidence that ComfyUI's runtime API interactions were tested. The lock makes these exact selections visible rather than claiming that broad range satisfaction proves runtime support. Review these choices before authorizing an installation; changes require a fresh lock and constraint checks.

No source distribution, source build, package installation, Windows VC++ installer, standalone CUDA toolkit, custom node or model-weight transfer was selected by this research. Runtime bootstrap tooling and bundled binary notices are not fully captured by this dependency graph.

## 6. Hash coverage

**84/84 selected artifacts (100%) have published SHA-256 values.** Each is paired with an exact filename/source; no missing wheel hash was invented. Hash-format/name/version/tag checks passed, and approved torch/vision identities were explicitly checked. No downloaded wheel was hashed because no wheel was downloaded.

This is 100% of **known selections**, not 100% of an established full installation inventory. Unknown CUDA-wheel dependencies, private Python/bootstrap/source artifacts, Windows runtime libraries and archive contents are not made complete by this percentage. Licenses, notices, package authenticity and actual byte verification remain separate checks.

## 7. Download volume

The 82 selected artifacts with published byte sizes total **741,453,448 bytes (0.69053 GiB)**. The torch/vision sizes remain `null`; exact total download bytes is also `null`. The subtotal is publisher metadata, not transferred binary volume.

The 4D **5–10 GiB complete-runtime download/cache allowance** remains a provisional estimate. It is not a resolved total and excludes weights; it must be replaced by actual approved artifact sizes before installation. Expanded-runtime, temp and rollback overhead remain the [4D disk estimates](runtime-artifact-audit.md#7-hardware-and-disk-considerations), not measurements derived from this lock. No package download or GPU capacity claim follows from these numbers.

## 8. Conservative installation-readiness gate

| Stage | Meaning | Current status |
| --- | --- | --- |
| Candidate profile | Proposed core pins and target; not an installed or verified runtime | Present; untested |
| Partially resolved lock | Exact known artifacts and provisional dependency graph with explicit gaps | **Current stage** |
| Complete audited lock | Every root/transitive/marker decision closed with exact selected-wheel dependency metadata, artifacts, hashes and required size inventory; independently rechecked | Blocked by three metadata gaps; future unknown edges may change selections |
| Authorized real installation | Separate user scope, reviewed software documents/consent, complete plan, isolation/rollback/security implementation and fresh disk checks | **Not authorized or implemented** |
| Execution-validated runtime | Explicitly authorized, bounded import/GPU/startup tests passed on the local device | **Not performed**; not Wan generation validation |

The lock fixes `status: INCOMPLETE`, `graph_complete: false`, `installation_eligible: false`, `authorized_real_installation: false` and `execution_validated: false`. Graph convergence and hashes never toggle these flags. A future complete lock still does not authorize installation. The existing runtime manager continues rejecting every non-fixture profile with `real_runtime_disabled`; no application or security change was made.

Remaining gates also include the isolated full-Python method and rollback, exact ComfyUI source integrity, bootstrap/tooling inventory, binary libraries/licenses/notice review, consent boundary, current disk/library prerequisites and the real installer implementation. Wan license documents and diffusion/VAE/UMT5 conversion provenance remain separately blocked. The recorded RTX 5080 Laptop VRAM does not validate CUDA or Wan execution.

## 9. Performed checks and next milestone

Performed metadata-only resolution and independent final data checks: selected names/versions match wheel filenames, all hashes have valid SHA-256 format, all tags/Python floors match the target, every known incoming constraint is satisfied, torch/vision remain exactly `+cu130`, and the known graph converged. No pip, binary GET, runtime modification or execution occurred. Application code and top-level candidate JSON are unchanged; full automated tests were not run. The 4C **274 passes / 3 skips / 1 warning** result remains historical.

Recommend **Milestone 4F — selected-wheel metadata closure and lock verification**: obtain official dependency metadata and exact byte sizes for the approved torch/vision artifacts, explicitly review whether a modest larger metadata-only limit is justified for Pydantic, then recompute and independently verify the closure. Do not fetch full wheels just to satisfy a resolver; if official small metadata cannot be obtained, stop and seek separately defined scope. Continue the bootstrap/source-integrity/license inventory before a later installer milestone. No installation, GPU test or next milestone is automatically authorized.
