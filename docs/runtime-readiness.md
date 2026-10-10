# Milestone 3C — Wan licensing and runtime readiness

**Milestone 4B review update:** [runtime-profile.md](runtime-profile.md) now proposes an exact core runtime candidate, pins ComfyUI source, records VRAM from the hardware endpoint and defines the remaining dependency-lock/licensing and execution gates. This updates the earlier missing-candidate observation, not the missing validation: no runtime was installed or executed, no full dependency lock was completed, and Wan remains blocked/unverified.

**Milestone 4A implementation update:** passive diagnostics are now implemented at `GET /api/system/runtime` and shown on the System page. The historical 3C review and proposal below remain evidence/design context. The implemented endpoint uses optional `DIRECTOR_RUNTIME_ENV` and `DIRECTOR_COMFYUI_DIR`, bounded file metadata and Windows driver queries. It does not run configured interpreters or import PyTorch. Backend Python is the default inspection scope; environment-file presence is not interpreter execution validation. Toolkit metadata remains not_tested, while driver CUDA can be observed independently. The model evaluator's RuntimeState remains unknown and generation readiness remains false.

Statuses distinguish installed metadata, not_detected within the inspected scope, unknown after a failed/incomplete probe, not_tested execution/toolkit checks and not_configured ComfyUI. ComfyUI expected-file detection is not a source-integrity or dependency check. Invalid/traversing/linked configured paths fail closed without exposing paths. Five-second process and 64 KiB process/file limits prevent unbounded diagnostics; site-packages discovery is limited to 2,048 immediate entries. No network or system modifications are part of detection. Runtime software installation, CUDA imports, architecture/kernel validation, memory benchmarks, license closure and inference remain future milestones.

Review date: **9 October 2026**. This is a documentation review, not a runtime installation or hardware certification. No model weights, ComfyUI or PyTorch were downloaded or installed; no inference, local runtime probes or license acknowledgements were performed.

## Evidence and readiness boundaries

The [2C research addendum](model-research.md) already records the three required artifacts, exact sizes, SHA-256 metadata, immutable repository revisions, workflow pin and public-access observations. That evidence is reused here, not reverified by downloading binaries. The [downloader design](downloader-design.md) describes the implemented installation safeguards.

Keep four separate questions:

1. **Artifacts installed:** every required file passed exact-size and SHA-256 verification.
2. **Runtime detected:** software and driver observations are available.
3. **Workflow validated:** a particular pinned runtime successfully executed the selected workflow on a particular device.
4. **Generation ready:** Director's complete, tested generation path is available.

Passing an earlier gate does not establish a later one. Currently Wan is researched, its installation is blocked, runtime observations are unknown, and `generation_ready` remains false.

## Existing artifact evidence

The model-author snapshot is `Wan-AI/Wan2.1-T2V-1.3B` at `37ec512624d61f7aa208f7ea8140a131f93afc9a`. The actual ComfyUI artifacts come from `Comfy-Org/Wan_2.1_ComfyUI_repackaged` at `123acf1cc74bccbb9bfff8ac1ee72edc08c2341d`:

| Component | ComfyUI destination | Evidence already recorded |
| --- | --- | --- |
| FP16 Wan diffusion model | `diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors` | Exact file, publisher pin, size and SHA-256 |
| Scaled FP8 UMT5 encoder | `text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` | Exact file, publisher pin, size and SHA-256 |
| Wan VAE | `vae/wan_2.1_vae.safetensors` | Exact file, publisher pin, size and SHA-256 |

The total is **9,828,025,775 bytes** (about 9.15 GiB). Hash metadata identifies bytes; it does not prove conversion lineage, licensing completeness or runtime compatibility. Earlier public/ungated observations are dated evidence, not a promise of future availability.

## Remaining licensing and provenance blockers

| Item | Verified evidence reused | Work still required |
| --- | --- | --- |
| Wan upstream | [Pinned Apache-2.0 license](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/blob/37ec512624d61f7aa208f7ea8140a131f93afc9a/LICENSE.txt) and model-card usage expectations | Package reviewed license text, relevant notices and usage expectations with exact document versions and hashes. Distinguish card expectations from license terms. |
| Comfy-Org artifacts | Pinned repository README declares Apache-2.0; prior root inventory found no standalone LICENSE/NOTICE | Determine applicable component notices and redistribution information. Root-file absence does not establish absence of notices everywhere or invalidate the declared license. |
| Diffusion and VAE conversion | Publisher artifacts and hashes are known | Record the exact upstream source files/revisions and conversion provenance. A publisher declaration alone does not establish this mapping. |
| UMT5 FP8 conversion | [Google UMT5-XXL](https://huggingface.co/google/umt5-xxl) declares Apache-2.0 | Establish the selected artifact's source checkpoint/revision, conversion/scaling recipe and applicable notices. Google UMT5 is candidate lineage, not verified lineage for these exact bytes. |
| Workflow redistribution | A pinned example is already recorded | Review applicable example-repository license/notices before bundling the workflow. A public URL is not a redistribution review. |
| Runtime and dependencies | [ComfyUI's current license](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/LICENSE) is GPL-3.0 | Review the selected runtime pin and dependency licenses, including Python, PyTorch/CUDA distributions and multimedia packages. Bundling/distributing runtime software needs a separate notice/source-obligation review. |

The Wan manifest has no reviewed `license_documents` package and defaults to `artifact_installation_reviewed=false`. The existing acknowledgement store therefore rejects installation with `license_documents_missing`. Do not set the review flag merely because a license name is known.

The future reviewed package must contain authoritative document text, source/version, its exact UTF-8 hash, relevant restrictions and component references. The existing store binds acknowledgement to the document set, model and component pins; changed terms or pins invalidate acceptance. Explicit acceptance must remain unchecked initially and separate from download confirmation. Director's acknowledgement policy does not imply that Apache-2.0 itself mandates publisher click-through acceptance. No acceptance is recorded in this review.

Runtime license review should have its own package and consent boundary when runtime installation is implemented. Do not treat Wan weight acknowledgement as acceptance of every future software dependency, or assume a separate process alone resolves distribution obligations.

## Official runtime prerequisites verified in this review

These are **current upstream observations**, not a tested Director version matrix. Mutable source URLs below do not supply an immutable runtime pin.

| Prerequisite | Official observation | Director implication |
| --- | --- | --- |
| Python | Current [package declaration](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/pyproject.toml) permits Python >=3.10. [System guidance](https://docs.comfy.org/installation/system_requirements) recommends 3.13, with 3.12 as a fallback for dependency issues. | A declared floor and a recommendation differ. Director's backend Python 3.11 environment is not a validated ComfyUI environment. |
| PyTorch/CUDA | System guidance reports PyTorch 2.7+ support; current [ComfyUI README](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/README.md) recommends CUDA 13.0 wheels for its NVIDIA setup. | Select and test one stable Windows/Python/wheel/driver/GPU tuple later. This guidance is not a universal Wan minimum. |
| Dependencies | Current [requirements](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/requirements.txt) include torch, torchvision, transformers, sentencepiece, safetensors and PyAV, among other runtime packages; torch is not fixed to one version. | Resolve and lock the complete dependency set at a selected ComfyUI pin. Requirements alone do not prove compatibility. |
| Windows libraries | The [manual installation guide](https://docs.comfy.org/installation/manual_install) identifies Microsoft Visual C++ Redistributable setup. | Inspect availability and report missing prerequisites; never install or repair system libraries automatically. |
| Native Wan workflow | The [official tutorial](https://docs.comfy.org/tutorials/video/wan/wan-video) uses the same three selected files. The previously pinned example uses core nodes and no third-party custom nodes. | No CLIP Vision checkpoint is required for this T2V profile. Do not import requirements from the I2V workflow or original Wan runner automatically. |

No minimum ComfyUI release/immutable runtime commit was established. The upstream tutorial's update guidance is not a numeric compatibility constraint. Official PyTorch installation pages and evolving ComfyUI guidance do not establish one jointly tested stack; verify release-specific wheel availability and Python ABI when choosing a pin. Prior Blackwell/PyTorch research remains in [model research](model-research.md).

The pinned example is a **UI graph**, not an API request payload. It specifies 832×480, 33 frames, batch 1 and 30 sampling steps. Its active output is animated WEBP; WEBM output is disabled. A later generation milestone must validate API graph conversion and an appropriate video encoder/container. Do not assert MP4 support, a mandatory external FFmpeg installation or Resolve import readiness from this example alone.

## Unknown requirements

- Exact tested ComfyUI commit, Python version, dependency lock, CUDA wheel and Windows driver requirement.
- Measured minimum and peak RAM/VRAM for this native FP16/FP8 workflow, including offloading and competing applications.
- GPU architecture/kernel support for the selected stack. FP8 file storage does not establish a requirement for native FP8 hardware execution.
- Runtime/environment/cache/output storage overhead and multimedia encoding behavior.
- Complete component provenance, reviewed document inventory and any required redistribution notices.

The original runner's 8.19 GB claim is not a measured native ComfyUI minimum. Previously proposed RAM/VRAM targets are experiment targets, not verified requirements. No current-machine measurements were collected here.

## Hardware and runtime validation plan

Start with passive observations, then separately authorize execution checks. Every observation should retain source, timestamp, scope and warnings. Missing measurements remain `null`; failed detection is distinct from successfully detected absence.

**Passive phase (recommended 4A):** reuse hardware detection and inspect an explicitly configured, trusted runtime location. Record the backend interpreter separately from the runtime interpreter. Read environment configuration and bounded package metadata without importing PyTorch, ComfyUI, custom nodes or startup hooks. Python's [package metadata interface](https://docs.python.org/3/library/importlib.metadata.html) supports distribution inspection without importing the target package; explicit metadata directories are needed when inspecting another environment.

If an interpreter probe is needed, execute only a trusted configured interpreter with a fixed standard-library script, bounded output and timeout, no shell and no user-supplied code. Consider `-I -B -S` to isolate Python, avoid bytecode writes and skip site startup. These [flags](https://docs.python.org/3/using/cmdline.html) are not a sandbox. Older virtual environments, including Python 3.11, need explicit environment-path handling with `-S`; do not infer package absence from incorrect site-directory discovery. Refuse unsafe paths/reparse escapes. Do not execute arbitrary discovered executables or Windows Store aliases.

For NVIDIA, use a bounded read-only `nvidia-smi` query for each device's identity, driver and memory; tolerate unsupported fields and missing tools. The [NVIDIA documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html) distinguishes driver-supported CUDA from an installed toolkit. Never equate that display with PyTorch's CUDA build. Keep AMD/Intel observations independent; never sum VRAM or trust CIM AdapterRAM as a requirement check.

**Later opt-in execution phase:** a short-lived process in the trusted runtime can import PyTorch and report its version, CUDA/HIP build, [CUDA availability](https://docs.pytorch.org/docs/2.14/generated/torch.cuda.is_available.html), device count, device capability and [compiled architectures](https://docs.pytorch.org/docs/2.14/generated/torch.cuda.get_arch_list.html). Imports execute package code and can initialize libraries or caches, so this is beyond static detection. Record import/DLL/timeout failures honestly. Do not allocate model tensors or execute ComfyUI during detection.

Compare driver compatibility to the **selected wheel's release-specific** requirements, including [CUDA compatibility limitations](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html). The toolkit compiler is a separate concern: [building CUDA extensions](https://docs.pytorch.org/docs/2.14/cpp_extension.html) needs additional tooling; a missing `nvcc` alone must not reject a prebuilt-wheel profile. Match observations to the same physical GPU, accounting for visibility/ordering, and do not reject architecture solely by exact membership in a compiled list when PTX fallback may apply.

CUDA availability is still not proof of Wan success. A separately authorized workflow experiment must measure peak RAM/VRAM, offloading, time and output validity for the pinned settings, with headroom for Windows and other applications. Disk checks must include runtime staging, package caches, weights and output space and be repeated before installation. The existing model manager's conservative artifact budget does not cover the runtime.

## Proposed runtime installation approach — future work

Use a Director-owned runtime directory and a separate Python environment, leaving the backend environment and external ComfyUI installations untouched. Select an immutable official ComfyUI commit and reviewed software/license inventory, then lock compatible Windows wheels and their integrity metadata. Do not use automatic updates, unpinned custom nodes or automatic system driver/toolchain changes.

Apply the existing ownership/path principles to runtime staging and activation, with a separate receipt and health checks. Map verified Director-owned artifact bundles through configuration in Director's own ComfyUI instance; the manual guide documents `extra_model_paths.yaml`. Never edit another installation's model paths. Loopback process management, runtime installation consent, rollback and API workflow execution require later designs/tests. None are implemented or enabled by this document.

## Smallest practical Milestone 4A

Implement **read-only runtime inventory**, with no installer and no PyTorch import:

1. Add a small runtime observation schema and detector under a separate backend runtime module. Include configured location, Python/package metadata, driver observations, evidence and warnings. Distinguish unknown, missing and observed; keep execution compatibility unknown.
2. Accept trusted configuration at startup, not arbitrary executable paths or commands through HTTP. Bound probes and metadata reads; no network, directory creation, startup scan/resume or package installation.
3. Add one proposed `GET /api/runtime/readiness` endpoint for on-demand observations, using existing Host/Origin protections. Preserve current endpoints and the pure compatibility evaluator. Do not populate the existing `RuntimeState.status="available"` from filenames or package metadata alone.
4. Test missing environments, malformed metadata, unsafe paths, probe failure/timeout, multiple GPUs and unknown CUDA using offline fixtures. Run backend regression tests and a loopback HTTP smoke check when code exists.
5. Document exactly what was observed. Leave `cuda_available` unknown until a separately authorized execution probe and keep generation readiness false. No frontend change is necessary for this first step.

After 4A, separately close the licensing/provenance inventory, choose and lock a runtime stack, and implement/test an owned runtime installer without weights. Only after those reviews should a user-authorized real Wan installation and bounded generation experiment be considered. 4A must not automatically enable downloads or unblock Wan.

## Review verification

Reviewed repository rules, research, architecture, downloader design, Wan manifest and relevant runtime/license implementation contracts. Checked the official sources linked above. Only documentation changed; no executable schema, manifest, backend or frontend changes were made. Per milestone instructions, tests were not run. Existing test results remain historical verification, not a fresh run for 3C.
