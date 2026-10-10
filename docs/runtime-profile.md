# Milestone 4B — Pinned runtime profile and licensing review

## Milestone 4K — Separate experimental GPU proposal

The [experimental GPU validation plan](experimental-gpu-validation.md) proposes the same Python 3.13.16 / torch 2.12.1+cu130 pins in a disposable developer environment outside Director's runtime roots. It includes only ten required wheels and the full Python ZIP, exact expected transfer metadata, staged license/authorization gates and an unrun tensor-test listing. No software was acquired, installed or executed in 4K. This experiment does not change the candidate profile, production preflight, consent requirements or NO-GO decision; even a future successful tensor test cannot validate ComfyUI or Wan.

## Milestone 4H safety infrastructure

The [installation-readiness report](runtime-installation-readiness.md#milestone-4h-implementation-result) now documents a frozen, reconstructed ComfyUI Git inventory, bounded offline extraction, read-only preflight, and checksum/version-bound runtime review. These additions do not change the approved candidate pins or enable provisioning. Exact runtime license documents and binary notices, unsigned-source trust policy, real installation/rollback implementation and explicit authorization remain blockers. Fixture structural verification is not runtime execution validation. The new conservative preflight disk estimate is approximately 63.1 GiB; earlier estimates below are historical.

## Milestone 4G bootstrap and installation-readiness update

The [installation-readiness review](runtime-installation-readiness.md) selects the official **full** `python-3.13.16-amd64.zip` (31,153,407 bytes, publisher SHA-256 in the official Windows manifest) as the preferred future private bootstrap. It is distinct from embedded Python and avoids a registered installer. Official extraction guidance and the version-specific pip/venv packaging preset support the method; exact binary contents and execution remain untested. Approved core pins and candidate JSON are unchanged.

ComfyUI's immutable Git tree is identified, but its ZIP has no established published SHA-256 or size. A reviewed Git-content verification policy and hostile-archive tests are required. Runtime binary notices, PyOpenGL exact-release licensing evidence, consent, disk checks and real installer/rollback implementation remain unresolved. **NO-GO for real installation**; see the new review for the 28–43 GiB first-install planning budget and proposed offline Milestone 4H. No model/runtime transfer or authorization is implied.

## Milestone 4F dependency metadata closure

The [dependency lock report](runtime-dependency-lock.md#milestone-4f--current-result) now establishes a **COMPLETE wheel metadata lock**: 84 exact selections, 84 published artifact hashes, exact sidecars for all selections, and 2,677,041,805 bytes (2.49319 GiB) of expected wheel artifacts. Independent offline root/marker/constraint validation passes. Approved Python/torch/cu130/vision/ComfyUI pins are unchanged and untested. The earlier 4E gaps below are historical and closed.

The candidate JSON and real provisioning gate are unchanged. `installation_eligible` remains false; full Python/bootstrap/source inventory, binary license/notice review, isolated installer/rollback and explicit authorization remain unresolved. The complete dependency metadata lock does not make the entire runtime inventory complete or authorize installation, CUDA execution or Wan downloads.

## Milestone 4E dependency lock update

The [dependency lock report](runtime-dependency-lock.md) now records 84 exact target wheel selections with 84 published SHA-256 values. The [separate lock artifact](../runtime_profiles/locks/wan-windows-cp313-cu130.lock.json) is **INCOMPLETE and installation-ineligible**: 81 packages have selected-wheel sidecar metadata, Pydantic uses release JSON only, and the approved torch/vision CUDA-wheel dependency metadata and sizes remain unknown. The 82 known sizes total 741,453,448 bytes; the complete download volume is unknown. All recorded target constraints pass, including multidict 6.9.1 selected below aiohttp's <7 ceiling. This does not establish a complete graph or runtime execution compatibility.

The lock is under a subdirectory so existing top-level RuntimeProfile loading remains unchanged. The candidate JSON, provisioning gate and real-installation authorization remain unchanged. Newest range-compatible transitive pins are provisional and require review; no Python, wheel or runtime installation took place. Next proposed scope is metadata gap closure and independent lock verification, not real provisioning.

## Milestone 4D independent artifact audit

The [runtime artifact audit](runtime-artifact-audit.md) independently rechecked the proposed core versions on **9 October 2026**. CPython 3.13.16 x64, torch 2.12.1/cu130 and torchvision 0.27.1 Windows CPython 3.13 wheels, and ComfyUI v0.39.0/full commit are officially listed. No unavailable core version or justified replacement was found. This confirms availability, not execution compatibility or installation readiness.

New evidence includes published Python installer/embedded ZIP SHA-256 values, official torch/vision index SHA-256 values, and exact bytes/hashes for 13 pinned PyPI wheels. The templates meta-package also requires eight exact subordinate packages without extra markers, making the audited PyPI subset 599,514,961 bytes. These are partial publisher metadata totals, not an installed-size measurement or a complete lock. Torch/vision binary HEAD and metadata-sidecar requests failed; exact sizes and selected-wheel dependency metadata remain unknown.

**Controlled real installation remains BLOCKED.** The complete target dependency lock, source/archive integrity inventory, binary notice/license review and isolated full-Python bootstrap/rollback method are unresolved. Python's embedded distribution is not a supported normal pip-dependency shortcut. Runtime JSON stays proposed with no real artifact inventory and provisioning remains fixture-only. The historical recommendation and 4C fixture evidence below do not override the audit's no-go criteria. Recommended next step: explicitly scope target dependency resolution and audited lock generation; no real provisioning, GPU execution or Wan download is authorized by this document.

## Milestone 4C implementation status

The proposal below now has a validated schema-v1 metadata representation at `runtime_profiles/wan-windows-candidate.json`. It preserves the documented Python, torch/cu130, optional TorchVision and ComfyUI commit. Required dependency pins are a partial inventory, **not a complete transitive lock**. The real artifact list is empty: exact binary URLs, hashes and sizes are still unresolved and have not been invented. Unknown package versions remain `null`. The profile is `proposed`, never execution validated and never provisionable in 4C.

`backend/director/runtimes/schemas.py` validates versions, commit/hash formats, HTTPS artifact metadata, relative directories and conflicting artifact destinations. Profiles separate evidence sources, unresolved requirements and proposed validation stages. Listing a stage does not run it. Real runtime provisioning has no implementation or enable switch.

The explicitly enabled built-in `runtime-fixture-tiny` uses three inert UTF-8 text files (149 bytes total), exact sizes and SHA-256 values, and a clearly fictional zero commit. It contains no interpreter, wheels, ComfyUI source or executable dependency. It passes the shared storage and verification flow and finishes `installed_unvalidated`; inventory verification is recorded separately from execution validation. It grants no software license acceptance and resolves none of the Wan or runtime licensing blockers.

The 4C lifecycle supports cancellation, durable interrupted-job recovery, corruption reports, scoped removal and explicit staging cleanup. Future real environments must use final-path candidates and pointer activation: a virtual environment cannot safely reuse the fixture's directory relocation strategy. Real software installers, archive extraction, network transfer, complete wheel locking, reviewed runtime license documents, execution probes and automatic repair remain future work.

For an exact offline demo, see [README](../README.md#milestone-4c-offline-runtime-fixture). The next practical milestone is a **read-only artifact/lock and license audit**: freeze the complete Windows dependency inventory and verify official installer/wheel provenance, sizes, hashes and license documents before separately authorizing real provisioning. No installation or CUDA execution is implied by that recommendation.

Reviewed **9 October 2026**. This proposes one runtime candidate for Windows AMD64 and Director's first native Wan 2.1 T2V-1.3B experiment. It is **not execution-validated**, an installation authorization, or a completed dependency lock. No Python, PyTorch, ComfyUI or weights were installed/downloaded; no CUDA tests or ComfyUI startup were performed.

## Decision and evidence labels

Prefer **CPython 3.13.16 x64 + PyTorch 2.12.1/cu130 + TorchVision 0.27.1/cu130 + ComfyUI v0.39.0 at `b0b743566f65daafc423b4fea8a2fbda94b3384a`**. Use standard CPython, not its free-threaded variant. This selects a stable release with documented Blackwell wheel guidance and a fixed ComfyUI source snapshot rather than tracking `master` or nightly packages.

- **Documented:** an official source explicitly supplies a release, requirement, wheel or architectural statement.
- **Inferred:** those statements make a proposed combination plausible, but do not certify the complete combination.
- **Untested:** Director has not executed the relevant check on this machine.

Every proposed combination remains untested locally. No fallback is recommended now: Windows CPython 3.13 wheels exist for the selected torch/vision pair, and no measured failure justifies maintaining a second stack. If dependency locking fails, stop and review the failing package; do not silently downgrade Python, switch CUDA builds or enable a nightly.

## Machine observations, not inferred capacities

A temporary Director backend served **`GET /api/system/hardware` on 127.0.0.1:8011** for this review and was stopped afterward. The response reported:

| Measurement | Observation and scope |
| --- | --- |
| NVIDIA device | NVIDIA GeForce RTX 5080 Laptop GPU |
| NVIDIA total VRAM | **15.9208984375 GiB**, `source=nvidia_smi`, `vram_is_estimate=false` |
| Intel adapter | Intel Graphics; its approximately 2 GiB CIM estimate is not used as compatibility proof |
| Total system RAM | 31.420948028564453 GiB |
| Project-volume free storage | Approximately 149.197 GiB at the observation time |

VRAM was read from the endpoint, not assumed from a product name. This is total memory, not currently free VRAM. RAM/storage are snapshots and do not prove peak inference capacity. The supplied 4A runtime observation records Windows AMD64, backend Python 3.11.5, NVIDIA driver 616.92 and driver-reported CUDA 13.4. These runtime observations were not reprobed in 4B. No torch metadata was found in the inspected backend environment; that does not establish absence in other environments.

## Preferred core pins

| Item | Proposed exact selection | Authoritative evidence | Interpretation |
| --- | --- | --- | --- |
| GPU architecture | Blackwell; expected compute capability 12.0, to be measured later | NVIDIA's [RTX 50 laptop page](https://www.nvidia.com/en-us/geforce/laptops/50-series/) identifies the laptop family as Blackwell. Its [CUDA table](https://developer.nvidia.com/cuda/gpus) lists RTX 5080 under 12.0. | Family is documented; the table does not separately name the laptop variant. Applying 12.0 to this device is an inference, not a local capability measurement. |
| Runtime Python | **CPython 3.13.16**, standard Windows x64 | [Official release and Windows distribution](https://www.python.org/downloads/release/python-31316/); [pinned ComfyUI README](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/README.md) recommends 3.13; [package declaration](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/pyproject.toml) permits >=3.10. | Release availability and Python branch support documented. Exact combined dependency compatibility untested. Backend 3.11.5 stays separate. |
| PyTorch | **`torch==2.12.1+cu130`**, `cp313-cp313-win_amd64` | [Official version pairing](https://pytorch.org/get-started/previous-versions/) lists 2.12.1 with CUDA 13.0; [official wheel index](https://download.pytorch.org/whl/cu130/torch/) lists that platform/build. | Pair/platform documented. No wheel downloaded or imported. |
| TorchVision | **`torchvision==0.27.1+cu130`**, `cp313-cp313-win_amd64` | Same official version pairing; [vision wheel index](https://download.pytorch.org/whl/cu130/torchvision/) lists the Windows CPython 3.13 wheel. | Documented torch/vision pair; required by the selected ComfyUI requirements. Import/kernel behavior untested. |
| CUDA build | **cu130 (CUDA 13.0)** inside the selected wheel distribution | [PyTorch 2.12 release guidance](https://pytorch.org/blog/pytorch-2-12-release-blog/) recommends CUDA 13.0+ for Blackwell. | Documented family guidance. Applying it to the 2.12.1 patch and this workflow is an inference awaiting tests. It does not require changing the driver-reported 13.4 to 13.0. |
| NVIDIA driver | Retain observed **616.92**; no update action | The same release guidance names **580.88 Windows** for its CUDA 13.0+ Blackwell recommendation. | Observed driver numerically exceeds that threshold; this is a preliminary version check, not execution proof. |
| ComfyUI | **v0.39.0**, commit **`b0b743566f65daafc423b4fea8a2fbda94b3384a`** | [Official release](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.39.0) links to the [full commit](https://github.com/Comfy-Org/ComfyUI/commit/b0b743566f65daafc423b4fea8a2fbda94b3384a). | Release/pin verified; native support exists in source, but no startup/workflow test was run. This is a selected candidate, not a claim about Wan's minimum version. |

TorchAudio is **not selected**: it is absent from this commit's requirements and the selected T2V graph has no audio nodes. Do not install a mismatched audio package just because a generic setup command lists it. If a later feature needs audio, research and lock that feature's compatible release separately. No standalone CUDA Toolkit, compiler, FlashAttention, xformers or third-party custom node is proposed for this first profile. Source-built extensions would require a separate tooling review.

## Required ComfyUI dependencies and reproducibility gap

The authoritative input is the [requirements file at the selected commit](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/requirements.txt). Its exact upstream package pins, in addition to Director's proposed torch/vision constraints, are:

| Package | Upstream pin | Evidence quality |
| --- | --- | --- |
| comfyui-frontend-package | 1.53.10 | Documented requirement, installation untested |
| comfyui-workflow-templates | 0.11.76 | Documented requirement, installation untested |
| comfyui-embedded-docs | 0.5.13 | Documented requirement, installation untested |
| comfy-kitchen | 0.2.37 | Documented requirement; [PyPI metadata](https://pypi.org/pypi/comfy-kitchen/0.2.37/json) supplies a `cp312-abi3-win_amd64` wheel and Python >=3.10. Stable-ABI suitability for CPython 3.13 is inferred; DLL/kernel loading remains untested. |
| comfy-aimdo | 0.5.5 | Documented requirement; [PyPI metadata](https://pypi.org/pypi/comfy-aimdo/0.5.5/json) supplies a `cp39-abi3-win_amd64` wheel and Python >=3.9. Stable-ABI suitability is inferred; loading remains untested. |

The source also requires torchsde, numpy>=1.25.0, einops, transformers>=4.50.3, tokenizers>=0.13.3, sentencepiece, safetensors>=0.4.2, aiohttp>=3.11.8, yarl>=1.18.0, pyyaml, Pillow, scipy, tqdm, psutil, alembic, SQLAlchemy>=2.0.0, filelock, av>=17.0.0, requests, simpleeval>=1.0.0 and blake3. Its nonessential section contains kornia>=0.7.1, spandrel, pydantic~=2.0, pydantic-settings~=2.0, PyOpenGL>=3.1.8 and comfy-angle. Keep the upstream inventory as the initial resolution input; do not omit packages before establishing which imports the selected startup requires.

**These ranges are not a reproducible lock.** Exact versions, transitive dependencies, binary sizes/hashes, package licenses and the installer/bootstrap tooling remain unresolved. In 4C, resolve against this commit with exact torch/vision constraints and Windows CPython 3.13 tags, then review/freeze every selected artifact. Require binary wheels; fail rather than compiling an unexpected source distribution. Do not add kitchen's optional development/build/cuBLAS extras without justification. Do not allow `pip install -r requirements.txt` to replace the chosen CUDA wheel with a different build.

The core candidate is pinned; **installation must remain blocked until the full dependency and integrity lock is complete**. No executable lock or runtime profile was added to the live registry in 4B. The Wan manifest's runtime constraints remain unchanged because a proposed stack is not validated model support.

## Native Wan workflow evidence

Reuse the [existing artifact/workflow research](model-research.md): three pinned diffusion/FP8 UMT5/VAE files, total **9,828,025,775 bytes**, and example commit `cb13911e7d83e4f61ca12e29629cab85a6c08856`. The [official tutorial](https://docs.comfy.org/tutorials/video/wan/wan-video) documents the native T2V path. At the proposed ComfyUI commit, [core loaders](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/nodes.py) include UNETLoader and CLIPLoader's `wan` type, and [the latent module](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/comfy_extras/nodes_hunyuan.py) registers EmptyHunyuanLatentVideo. Static evidence establishes native building blocks, not successful registration/execution of every node or compatibility of an older UI graph with this release.

Use the existing 832×480, 33-frame, batch-1, 30-step graph as the later bounded experiment. Verify all declared nodes and inputs at runtime. No CLIP Vision, I2V model or prompt-enhancement model is required for this selection. The graph is UI-format and has active animated WEBP output; WEBM is disabled. API conversion and a tested video container/encoder remain later tasks. Do not claim Resolve-ready output.

## Exact licensing gates before a real Wan download

Reuse the [3C license/provenance inventory](runtime-readiness.md); hashes/file identities were already verified in 2C and do not need binary downloads to revisit them. The upstream Wan snapshot has an authoritative Apache-2.0 license, and the converted publisher README declares Apache-2.0. Those declarations do not close the following gates:

1. Map **diffusion and VAE** artifacts to exact upstream checkpoint files/revisions, documenting conversion/modification history and applicable attribution/notices.
2. Map **scaled FP8 UMT5** to its exact source checkpoint/revision and quantization/scaling recipe. Google UMT5-XXL's license is candidate lineage; it is not proof of the selected converted bytes' lineage.
3. Inventory the applicable license and NOTICE texts and model-card usage expectations. Preserve existing notices if applicable; do not invent a NOTICE because none appeared at the publisher root. Separate card expectations from license terms. If provenance cannot be resolved, keep the gate blocked rather than silently accepting uncertainty.
4. Create reviewed exact document/version/source/text/SHA-256 entries, then set `artifact_installation_reviewed=true` only after review. Until then the existing empty document set produces `license_documents_missing`.
5. Obtain explicit acknowledgement of the current document-set digest and a separate confirmed installation plan. Source/pin/document changes invalidate the acknowledgement. Director's acceptance policy is separate from any publisher gating; earlier public/ungated observations must be rechecked before an authorized transfer.
6. Independently pass existing immutable pin/hash/size, ownership and disk-space preflight. Keep real downloads off until explicitly authorized. No runtime candidate or successful GPU test bypasses these artifact gates.

ComfyUI's [license at the selected commit](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/LICENSE) is GPL-3.0. Runtime source, Python, dependencies, NVIDIA libraries, multimedia components and any bundled workflow need their own license/notice inventory. Local use and redistributing a packaged runtime raise different review questions; weight acknowledgement does not cover software distribution obligations. Full runtime license closure and the unresolved converted-artifact lineage remain blockers, not completed approvals.

## Isolated Director-owned layout — proposal only

Use a dedicated runtime root, separate from the model manager's existing namespace:

```text
<DIRECTOR_RUNTIME_ROOT>/.director-runtime/
  owner.json
  staging/<job-id>/
  runtimes/<profile-id>/<bundle-id>/
    python/              reviewed private full CPython, if provisioned later
    env/                 dedicated runtime environment
    ComfyUI/             exact reviewed source inventory
    locks/               profile, package hashes and license inventory
    receipt.json
  active.json
  cache/                 owned package/source cache
  jobs/                  recovery records
  runs/<run-id>/         configuration, input/output/temp/user/cache/log files
```

No directory was created by this proposal. Reject drive/network roots, traversal, symlinks/junctions, unowned collisions and external ComfyUI roots. Never reuse or change Director's backend `.venv`, system Python, global PATH, driver installation or another ComfyUI directory.

A base interpreter acquisition mechanism is **not yet approved**. Prefer an explicitly selected existing compatible interpreter to create an isolated environment for an initial developer test, without altering that interpreter. Automated private Python provisioning needs a separate review of the official full-distribution installer and any registry side effects. Do not improvise pip support in the embeddable ZIP: [Python's Windows guidance](https://docs.python.org/3.13/using/windows.html) does not support treating that package as a regular pip-managed installation. If neither approved mechanism is available, report a missing base interpreter and stop.

Windows virtual environments are not safely relocatable by assumption. Build each environment at its final, inactive bundle path; use staging for downloaded inputs and source checks. Activate by replacing a small pointer after validation, rather than moving a populated environment and breaking its absolute paths. Runtime processes may write caches: keep writable state in owned run directories. Validate and inventory any permitted writes before using an installation receipt for integrity checks.

Later map verified model bundles through configuration for **Director's instance only**. The [pinned CLI](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/comfy/cli_args.py) supports base/input/output/temp/user paths and extra model configuration. Future startup should explicitly bind loopback, disable custom and partner nodes, use packaged frontend assets, and use `--offline`. That flag restricts frontend networking and disables partner nodes; it is not a complete OS network sandbox or proof that every Python dependency stays offline.

## Future validation sequence — none executed in 4B

Each stage must have a bounded timeout, captured/redacted error category and an explicit pass/fail/not-tested record tied to the profile digest and physical GPU. Stop at the first failure; later stages remain not tested.

1. **Installation verification:** validate official source identity, Python distribution integrity/signature, exact wheel hashes and filenames, dependency lock and installed versions; run dependency consistency checks in the owned environment. Do not fall back to arbitrary package indexes or source builds.
2. **PyTorch import:** in a short-lived trusted runtime process, import torch/torchvision and check versions, DLL loading and the CUDA build. This executes code and requires new authorization beyond 4A passive detection.
3. **CUDA availability:** check availability/device enumeration, matching the selected physical NVIDIA GPU despite index/visibility ordering. Record the driver separately from `torch.version.cuda`. A true result alone is not a passing Wan profile.
4. **Architecture:** measure device capability and inspect compiled architectures. Compare with the expected Blackwell target and account for PTX fallback; list membership alone is not a complete kernel test.
5. **Minimal allocation/kernel check:** explicitly authorize a tiny fixed-budget allocation and simple operation (for example, below 1 MiB), synchronize, check the numerical result, release memory and exit. No model loading, stress test or large allocation. Success proves only that simple operation, not FP8 kernels or Wan.
6. **ComfyUI startup/health:** start only the owned pinned instance, with empty model paths and custom nodes disabled. Verify PID ownership and a free chosen loopback port. Check `/system_stats` and required `/object_info/{node_class}` records, documented in the [pinned server source](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/server.py). Do not invent a `/health` endpoint or trust a different process responding on that port. Sanitize returned argv/paths; node metadata availability is not inference validation.
7. **Native workflow validation, later milestone:** only after licensed, explicitly authorized and verified weights exist, convert/review the pinned graph, test its bounded settings and measure peak RAM/VRAM/time/output validity. Keep generation readiness false until Director's actual integration is tested. Neither 4C planning nor a software smoke check authorizes this stage.

## Storage, integrity, rollback and failures

Budget all volumes independently: source/Python/package download cache, extracted runtime, inactive candidate and retained previous bundle, temporary files, model cache/staging, outputs and an explicit reserve. Runtime sizes remain unknown until the wheel/source inventory is locked; rounded wheel page sizes are not exact capacity requirements. Existing 149.197 GiB free space is not a reservation or assurance of sufficient space. Recheck before transfer, extraction/install and activation. Preserve the model manager's conservative storage policy; its weight budget does not include runtime software.

Reject unsafe archive entries and unexpected executable inputs. Hash artifacts before use and record a frozen installation inventory; a filename or pip exit code alone is not integrity/readiness. Use journaled stages and an OS root lock. Validate the inactive candidate in its final location and atomically switch the active-pointer file on the same filesystem only after the required checks pass. Windows file locks/antivirus may prevent activation; fail without advertising readiness.

Keep the previous bundle until no owned process uses it. A failed install or crash leaves the previous pointer unchanged; record incomplete candidates and never automatically resume package installation or GPU checks. Rollback selects a previously intact, validated receipt and starts no job automatically. Removal accepts only owned inventories and refuses unexpected additions. Stop only the process tree launched for the job, never every Python process on the machine.

Report actionable failures such as missing_base_python, unresolved_dependency_lock, insufficient_space, artifact_integrity_failed, unsafe_path, package_install_failed, import_or_dll_failed, cuda_unavailable, architecture_unresolved, allocation_failed, startup_timeout and activation_failed. These are proposed categories, not existing API error contracts. Include the stage, retry guidance and sanitized cause, without tokens, arbitrary environment dumps or unnecessary paths. Runtime software readiness, model artifact readiness and generation readiness remain separate.

## Exact Milestone 4C implementation boundary

Recommend **runtime provisioning and validation infrastructure with offline fixtures first**, stopping before weights or inference:

1. Add a small declarative profile schema and read-only runtime plan for this candidate. Fail closed until complete dependency/file/license/hash inventory and an approved base-interpreter mechanism exist. Freeze a Windows CPython 3.13 lock with the exact torch/vision CUDA builds; no latest/nightly resolution at installation time.
2. Implement owned runtime storage, safe archive validation, immutable receipts and the non-relocating environment/pointer lifecycle above. Keep it separate from artifact storage and the existing pure model evaluator.
3. Add injectable package/source transfer and process runners. First test installation, progress, cancellation, timeout, crash recovery, rollback and cleanup using tiny fixtures and fake processes; no real downloads or CUDA tests in automated tests.
4. Add separately permissioned installation and execution-validation operations using existing local manager-key/Host/Origin protections. Default real runtime provisioning and GPU validation to disabled; visiting diagnostics pages must start neither. Runtime license acceptance must not reuse model acceptance.
5. Only if the future 4C request explicitly authorizes real software provisioning and smoke tests, use the reviewed lock and complete stages 1–6 above without weights. Otherwise complete infrastructure/tests and leave real operations disabled. Never widen the passive `/api/system/runtime` endpoint into an implicit CUDA import/startup action.
6. Run backend regression tests and loopback API checks for executable changes; document exact performed validation and retained unknowns. No frontend rewrite, Wan installation, inference, Resolve integration or next-milestone work belongs to this initial 4C boundary.

## Verification of this review

Reviewed repository rules, relevant existing research/design/architecture, Wan manifest and passive diagnostics implementation. Checked official release/source pages and small PyPI metadata; did not fetch package or model binaries. The existing hardware endpoint returned the recorded VRAM measurement, and its temporary server was stopped. Only this document and a readiness cross-reference changed. Automated tests were not run because no executable code changed. The latest 4A totals (229 backend passes, two skips; 57 frontend passes) remain historical verification.
