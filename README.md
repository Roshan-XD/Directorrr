# Director

This repository shares Director's source code, tests, model manifests and documentation. It does not include Python environments, ComfyUI/runtime binaries, model weights, generated videos or private session evidence. Cloning it does not recreate the author's installed runtime. Friends should read [the teammate setup requirements](docs/teammate-setup.md) before running it; a bundled installer is not available yet. Historical validation reports describe the author's machine, not a guarantee for another computer. No open-source license for Director itself has been selected yet.

MiniMax H3 Optimized is available in Model Store: the reviewed DmitryDB FL2VA NVFP4 (non-HQ) build plus Qwen NVFP4 AWQ encoder and both VAEs totals **33,163,649,303 bytes**. Install opens the exact-file/license/disk review; only your explicit Confirm starts transfers. Director verifies every SHA-256, registers files with the existing private Windows runtime and enables the fixed native text-to-video/audio adapter. No custom nodes or repository scripts. First generation on 16 GB VRAM/32 GB RAM remains experimental; Ready means verified configuration, not measured execution compatibility. Generic repository downloads and production provisioning remain separately disabled.

MiniMax H3: Model Store now offers **Install MiniMax H3** as an exact official-file preflight review. Transfer remains blocked on this laptop by RAM/disk and unimplemented runtime requirements; this is not a ready H3 installer. See [the focused review](docs/h3-installation-review.md).

The creative studio extension adds live paginated model discovery, managed data-download planning, persistent projects/presets/history, a media Library and pipeline inspection. See [the creative studio guide](docs/creative-studio.md) for operation, ownership, new APIs and explicit limitations. Start/Stop Director and the validated Windows Wan/Resolve path are retained. New weight downloads are disabled by default; image execution and general new-family install-to-ready are not yet available.

## Windows-only local use after cleanup (Stage 13)

The validated private runtime is `runtime/windows-dev-001`. Start with **Start Director.cmd** and stop with **Stop Director.cmd**; neither requires WSL. The obsolete Director WSL distro and experimental downloads were removed with explicit approval after preserving all unique generated videos and compact evidence. Source, backend `.venv`, frontend `node_modules`, native Python/ComfyUI/models, generated videos and manifests are retained. See [the cleanup report](docs/cleanup-report.md), [final evidence](docs/final-evidence/README.md) and [teammate setup boundary](docs/teammate-setup.md). Historical instructions referring to the removed Linux environment are reference material, not the normal launch route.

Working private execution does **not** authorize redistribution of the runtime or model binaries. Production provisioning remains disabled. Removed wheel/source-download caches can be reacquired only through a separately reviewed setup procedure; the launcher never downloads them.

## Private Windows development launcher (Stage 12)

Double-click **Start Director.cmd** in this folder. It creates a fresh private session credential automatically, starts Windows ComfyUI/backend/local UI, and opens `http://127.0.0.1:5173`. Wait for **Local session connected** on the Generate page, then enter your prompt. No key creation, copying, terminal activation, npm command or WSL startup is needed. Startup may take a couple of minutes; the status window reports progress. The credential exists only in launcher/backend/server-proxy memory and process environments; it is never sent to browser code or saved.

Use **Stop Director.cmd** or **Stop Director** in the status window to stop that launcher's services. Finish generation/import/placement first. Nothing is uninstalled or deleted. Existing occupied ports cause startup to stop rather than replace unknown services. This is a development launcher, not a redistributable installer. Existing Node.js, the project backend environment and configured Resolve scripting are still prerequisites. See [the Windows runtime guide](docs/windows-native-runtime.md). Historical milestone sections below describe earlier default-disabled production behavior; they do not supersede the explicit development scope.

## Development generation (Stage 8)

An explicitly enabled development adapter can connect the existing Generate page to the separately validated `Director-GPU-Dev` ComfyUI server. Only prompt and seed vary; the small Stage 7 Wan workflow is fixed. See [launch instructions, APIs and limitations](docs/development-generation.md). Director's native Windows production runtime and model-installation gates remain unchanged and NO-GO; default and production frontend generation stay disabled.

Director is a final-year engineering project: a Windows-first, local AI video assistant intended for DaVinci Resolve. The eventual application will inspect hardware, recommend and download supported models, manage a local ComfyUI runtime, generate video, preview results, and import them into Resolve.

**Current status: Milestones 1 through 4J complete.** Director has a React/TypeScript frontend, read-only runtime diagnostics, audited dependency metadata, offline runtime fixture provisioning, source verification, runtime preflight, consent gates and advisory notice classifications. Generation and image upload are disabled. The installation UI supports only the explicitly enabled model fixture. Automatic real downloads and real provisioning stay disabled; one separately authorized PyOpenGL wheel was inspected as inert ZIP data. No real weights or runtime software have been installed by Director. Wan and real runtime installation remain blocked pending license/provenance review and separate authorization. ComfyUI execution and Resolve integration are not implemented. No GPU is required to run either app.

## Offline runtime safety review (4H)

Milestone 4J adds advisory notice classifications to the existing secured runtime review. The [readiness report](docs/runtime-installation-readiness.md#milestone-4j--notice-classification-and-bounded-inspection) explains the local-use/redistribution distinction and the one explicitly authorized inert PyOpenGL wheel inspection. No software was installed or executed. The review now has 26 texts and 68 missing identities; classifications do not exempt required documents, and real provisioning stays disabled. Tests use the committed text/inventory receipt, never an artifact transfer.

See [runtime installation readiness](docs/runtime-installation-readiness.md) for source verification, runtime consent, remaining blockers and the conservative disk budget. Source fixtures exercise extraction only; no runtime program is executed. Run this focused offline test from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_runtime_preflight.py
```

This uses the existing backend environment to check tiny archives, consent, preflight and rollback. It does not install the proposed runtime. After starting the backend using the instructions below with your existing manager token configured, inspect the secured read-only reports:

```powershell
$runtimeHeaders = @{ "X-Director-Key" = $env:DIRECTOR_MANAGER_TOKEN }
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/runtime/profiles/wan-windows-candidate/preflight -Headers $runtimeHeaders
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/runtime/profiles/wan-windows-candidate/runtime-review -Headers $runtimeHeaders
```

The token must already be configured in the backend and this shell; do not place it in source, URLs or frontend variables. These commands read reports and never start provisioning. `POST /api/runtime/profiles/{profile_id}/runtime-acknowledgements` records explicit acceptance only when a complete reviewed document packet exists. The current candidate deliberately returns HTTP 412 for acknowledgement because its documents are missing. Review acceptance would still not authorize real installation. There is no new frontend installation control.

## Project structure

```text
Director/
├── AGENTS.md                     Rules for future coding sessions
├── README.md                     Setup, usage, and limitations
├── pyproject.toml                Python package and dependency configuration
├── .gitignore                    Excludes local files and large artifacts
├── backend/
│   ├── director/
│   │   ├── __init__.py
│   │   ├── main.py               FastAPI app and routes
│   │   ├── system/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py        HardwareProfile
│   │   │   └── hardware.py       Safe hardware probes
│   │   ├── installations/        Model artifact jobs, storage and verification
│   │   ├── runtimes/             Offline runtime profiles, fixture jobs and storage
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── schemas.py        ModelManifest and response schemas
│   │       ├── registry.py       Reads and validates JSON manifests
│   │       ├── compatibility.py  Capacity and execution-profile checks
│   │       ├── validation.py     Repository, path, and version validation
│   │       └── planning.py       Read-only installation plans and storage checks
│   └── tests/
│       ├── conftest.py
│       ├── test_hardware.py
│       ├── test_registry.py
│       ├── test_compatibility.py
│       ├── test_api.py
│       ├── test_metadata.py
│       ├── test_planning.py
│       └── test_profile_compatibility.py
├── frontend/
│   ├── package.json / package-lock.json  Pinned frontend tools and dependency lock
│   ├── vite.config.ts / vitest.config.ts Local proxy and offline test setup
│   ├── public/favicon.svg              Original Director icon
│   └── src/
│       ├── App.tsx / main.tsx           Navigation and React entry point
│       ├── api/                        Typed HTTP client and response contracts
│       ├── components/                 Reusable controls and status views
│       ├── hooks/                      Request lifecycle and tab job history
│       ├── pages/                      Generate, Models, Jobs, System
│       ├── test/                       Component/API tests and test-only fixtures
│       └── styles.css / tokens.css      Responsive dark interface
├── runtime_profiles/            Proposed runtime metadata; no installable software
│   └── wan-windows-candidate.json
├── model_registry/
│   ├── mock-cpu-video.json
│   ├── mock-gpu-video.json
│   └── wan-2-1-t2v-1-3b.json
└── docs/
    ├── architecture.md
    ├── verification.md           Checks actually performed
    ├── model-research.md         Primary-source model research
    └── downloader-design.md      Artifact evidence and proposed downloader/lifecycle/API
```

The new `backend/director/installations/` package contains `storage.py`, `verifier.py`, `downloader.py`, `jobs.py`, `licenses.py`, `schemas.py`, `api.py`, `fixtures.py`, and `demo.py`. New offline tests are `test_installations.py` and `test_installation_api.py`. Hardware, registry, evaluator and planner remain separate from model management and need no AI runtime or Resolve.

## Set up on Windows

Open **PowerShell**. You need Python 3.11 or newer, and internet access for the first dependency installation. The examples use this workspace's location; change it if you move the project.

```powershell
Set-Location D:\DIRECTOR-Resolve
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

1. `Set-Location` opens the project directory in your terminal.
2. `py -3.11 -m venv .venv` creates an isolated Python environment. If you use another supported version, replace `-3.11` with its version, or use `python -m venv .venv` after checking `python --version`. Skip creation if `.venv` already exists.
3. The `pip install` command installs Director and its backend/test dependencies. `-e` means Python uses your source files directly, so edits do not require reinstalling Director. `[dev]` includes pytest and HTTPX for tests. It downloads Python packages only, not AI models.

These commands call the virtual environment's Python directly; PowerShell activation and execution-policy changes are unnecessary. Dependencies have bounded version ranges in `pyproject.toml`; an exact reproducibility lockfile is not included yet.

## Run the backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn director.main:app --host 127.0.0.1 --port 8000
```

This starts the local HTTP server. Keep the terminal open. `127.0.0.1` makes it accessible from your computer only. Press **Ctrl+C** to stop it. For automatic reload after Python source edits, add `--reload`; restart manually after JSON manifest edits.

Open [API documentation](http://127.0.0.1:8000/docs) in your browser after the server starts. The documentation UI uses CDN assets; if offline, use the endpoints or [OpenAPI JSON](http://127.0.0.1:8000/openapi.json) directly.

In a **second PowerShell terminal**, inspect the endpoints:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/system/hardware | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/api/models | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/api/models/wan-2-1-t2v-1-3b/installation-plan | ConvertTo-Json -Depth 15
```

`Invoke-RestMethod` sends a GET request. `ConvertTo-Json -Depth 10` displays nested results clearly. Hardware requests can take time while Windows queries run; each subprocess has a ten-second timeout.

## Launch the Director frontend on Windows (Milestones 3A–3B)

Install a supported Node.js version first: **Node 22.12+ in the 22 series, Node 24, or Node 26+**. This workspace was tested with Node **22.20.0** and npm **10.9.3**. The selected test tools need Node 22+, even though [Vite itself also supports suitable Node 20 releases](https://vite.dev/guide/). Stable dependencies were checked against official npm metadata and the [React](https://react.dev/versions) / [Vitest](https://vitest.dev/guide/) documentation.

In **terminal 1**, start the backend from the repository root:

```powershell
Set-Location D:\DIRECTOR-Resolve
$env:DIRECTOR_ALLOW_REAL_DOWNLOADS = "0"
.\.venv\Scripts\python.exe -m uvicorn director.main:app --host 127.0.0.1 --port 8000
```

`Set-Location` chooses the project folder. The environment setting explicitly keeps real downloads disabled. Uvicorn starts the existing backend on your computer only. If the Python environment is missing, follow the setup section above first.

In **terminal 2**, install the locked frontend dependencies and start Vite:

```powershell
Set-Location D:\DIRECTOR-Resolve\frontend
npm.cmd ci
npm.cmd run dev
```

`npm.cmd ci` installs exactly the versions recorded in `package-lock.json` (no AI weights or runtime). `npm.cmd run dev` starts the local frontend with automatic source updates. Using `npm.cmd` avoids PowerShell script execution-policy issues. Both ports are fixed; if one is already running, use that process instead of starting a second copy. Press **Ctrl+C** in each terminal to stop the corresponding server.

Open **[Director](http://127.0.0.1:5173)**. The browser calls `/api` on the frontend origin, and Vite forwards requests to the backend. No CORS change or backend rewrite was needed. Initial hardware/model requests can take several seconds.

![Director frontend foundation](docs/director-preview.jpg)

### What each page does

- **Generate:** editable local draft prompt, model selection, text/image mode and seed; resolution/duration, upload, preview playback and Generate are disabled. No generation endpoint is called. Draft controls reset when leaving this page or reloading.
- **Models:** real manifests, capability labels, installation status and exact/estimated download size. Selecting a card loads the read-only plan, storage budget, license requirements, blockers and warnings. Compatibility reasons/research notes can be expanded. Unknown values remain unknown; mock requirements remain fictional. Real-model installation stays disabled. In explicitly enabled local development mode, the tiny fixture has a reviewed license dialog and a separate installation confirmation.
- **Jobs:** look up a backend's 32-character hexadecimal job ID. Up to 12 IDs are kept in this tab's session storage; the backend has no job-list endpoint. Model status may reveal a recent ID. Active known jobs poll every four seconds without overlapping requests; completed/error jobs require manual refresh. A failed lookup is visible, never a fake success. Forgetting an ID does not cancel/delete a backend job.
- **System:** live CPU, RAM, each GPU/VRAM, storage and detection warnings. Estimated VRAM is labeled unreliable; failed detection is distinguished from no detected GPU. This is not a generation benchmark.

### URL and key configuration

Default backend target is `http://127.0.0.1:8000`. To change its port, set this in the **frontend terminal** before startup:

```powershell
$env:DIRECTOR_BACKEND_URL = "http://127.0.0.1:8001"
npm.cmd run dev
```

Start Uvicorn on the matching port. Targets must be loopback HTTP(S) origins with no credentials/path/query. You can instead copy `frontend/.env.example` to `frontend/.env.local` and edit the public URL settings; that local file is ignored. Restart Vite after configuration changes. `VITE_API_BASE_URL` defaults to `/api`; a direct local absolute URL is supported by the client, but browser cross-origin access is not enabled by the backend. Use the documented same-origin proxy for this milestone. Production hosting needs an equivalent trusted same-origin proxy; the build alone does not supply one.

Read-only pages need no manager key. To acknowledge fixture terms, install the offline fixture or cancel an active job, configure `DIRECTOR_MANAGER_TOKEN` in the **backend terminal** before starting Uvicorn (see the Model Manager section below), then enter that same key in the **Models** or **Jobs** page. The key stays in JavaScript memory, is sent only on explicit acknowledgement, installation or cancellation, and is cleared on page reload or **Clear key**. It is never saved in browser storage or compiled into the app. **Never put a key in a `VITE_` variable**: those values are public build configuration. No Hugging Face credential is requested by the frontend.

The proxy rejects foreign Host/Origin requests before rewriting a trusted browser Origin to the fixed backend origin. It never adds a key for the user. Backend authentication and Host/Origin checks remain unchanged. There is no backend setting endpoint and no UI action that enables real downloads.

### Frontend checks and production preview

From `frontend/`:

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run preview
```

The first command runs offline component/API tests. The second checks TypeScript and writes the production bundle to ignored `frontend/dist/`. The third previews that build at **[127.0.0.1:4173](http://127.0.0.1:4173)** using the same local API proxy; keep the backend running. The preview is a local check, not a deployed application. Run `npm.cmd run format` to format source files or `npm.cmd run format:check` to check formatting.

Backend regression tests still run from the repository root with `.\.venv\Scripts\python.exe -m pytest`. Latest results and the browser/proxy checks are recorded in [verification.md](docs/verification.md).

### Frontend limitations and recommended next work

There is no inference, Resolve integration, saved-project system, runtime inspection, generation upload or real-model installation UI. Job history is per-tab and limited to known IDs. Reads are snapshots; large installed-model status checks can be slow because the backend hashes files. Basic runtime guards validate the response fields used by the UI; they are not a generated complete OpenAPI validator. A full assistive-technology accessibility audit and packaged deployment are future work.

Recommended **Milestone 3C:** review real-model license/provenance gaps and design runtime validation, with separately authorized scope. Keep weights and inference disabled until their checks are complete. No next milestone has started.

## Test the complete offline fixture installation (3B)

Use **two PowerShell terminals**. Stop an existing backend with Ctrl+C before restarting with fixture configuration. This copies a **60-byte synthetic text file**, never AI weights. No GPU, Hugging Face login or internet transfer is needed. Keep the manager key private and never use a `VITE_` variable for it.

Backend terminal:

```powershell
Set-Location D:\DIRECTOR-Resolve
$env:DIRECTOR_ENABLE_FIXTURES = "1"
$env:DIRECTOR_ALLOW_REAL_DOWNLOADS = "0"
$env:DIRECTOR_MODEL_ROOT = "D:\DIRECTOR-Resolve\model_weights\ui-fixture"
$fixtureKey = Read-Host "Enter a private manager key (at least 32 characters)" -AsSecureString
$env:DIRECTOR_MANAGER_TOKEN = [System.Net.NetworkCredential]::new("", $fixtureKey).Password
.\.venv\Scripts\python.exe -m uvicorn director.main:app --host 127.0.0.1 --port 8000
```

`Set-Location` chooses the repository. The flags expose the fixture while keeping real downloads disabled. The dedicated model root isolates test files in an ignored project folder. `Read-Host` masks your key, and the conversion supplies it to the backend without saving it in source. Uvicorn runs the API only on your machine. Never use an external ComfyUI directory as this root.

Frontend terminal:

```powershell
Set-Location D:\DIRECTOR-Resolve\frontend
npm.cmd ci
$env:DIRECTOR_BACKEND_URL = "http://127.0.0.1:8000"
$env:VITE_ENABLE_FIXTURES = "1"
npm.cmd run dev
```

`npm.cmd ci` installs the locked web-development packages (skip if already installed). The public fixture flag enables the test UI **only in Vite development**, and the proxy points at your local backend. Open [Director](http://127.0.0.1:5173/#models).

1. On **Models**, enter the same manager key and click **Use key**. It remains in app memory and the input clears.
2. Select **MOCK installation fixture (not an AI model)**. This is a test utility, not a generation recommendation.
3. Review expected **60 B**, the owned destination, disk budget (three copies plus a **16 MiB** safety margin), warnings and blockers. Combined generation prerequisites remain unresolved; the separate backend artifact preflight controls copying this test file.
4. Click **Review license and installation**. Read the bundled synthetic document and its version/checksum. There is no invented publisher license link.
5. Explicitly check the unchecked acknowledgement box and click **Record acknowledgement**. This records acceptance only; **it installs nothing**.
6. Click **Confirm offline installation**. The frontend refreshes preflight, and the backend rechecks manifest, acceptance, paths, concurrency and disk space.
7. Inspect transfer/verification separately, then **Fixture files installed and verified**. **Generation remains unavailable**. Jobs remembers the returned ID. The tiny job usually finishes too quickly for cancellation; offline tests cover active cancellation and failures.

Closing review starts no job. Recorded acknowledgement stays in backend storage, but each new UI review requires explicit acknowledgement again. Missing/changed documents and backend refusals remain blocking. An uncertain installation response is never automatically retried; refresh Models/Jobs before another attempt.

Existing fixtures cannot be installed over their bundle. Use the authenticated backend removal API described below, or deliberately select a new dedicated test root; no removal/repair UI is added. Do not delete external or unknown files.

Use **Clear key** or reload to clear the UI key. Stop both processes with Ctrl+C. In the backend terminal run `Remove-Item Env:DIRECTOR_MANAGER_TOKEN` to remove its environment value. In the frontend terminal set `$env:VITE_ENABLE_FIXTURES = "0"` before the next normal start. Production always hides fixtures even if that flag is set.

## Expected backend responses

`GET /api/system/hardware` returns CPU, RAM, GPU, VRAM, and storage information. **Illustrative response; your hardware and warnings will differ:**

```json
{
  "platform": "Windows",
  "cpu": {"name": "Example CPU", "physical_cores": 8, "logical_cores": 16},
  "ram": {"total_gb": 32.0, "available_gb": 20.0},
  "gpus": [{"name": "Example NVIDIA GPU", "vendor": "nvidia", "vram_gb": 12.0, "vram_is_estimate": false, "source": "nvidia_smi"}],
  "gpu_detection_complete": true,
  "storage": {"path": "D:\\DIRECTOR-Resolve", "total_gb": 500.0, "free_gb": 100.0},
  "warnings": []
}
```

Capacity fields ending in `_gb` use **GiB** (1024 cubed bytes). Unknown fields are `null`. Failed GPU detection returns `gpu_detection_complete: false` and a warning; it does not imply there is no GPU.

`GET /api/models` returns a `models` array with **three entries**, each containing the full `manifest` and its `compatibility`, plus top-level `hardware_warnings`. Here is a shortened illustration of one entry; full responses include the new metadata and profile checks:

```json
{
  "models": [
    {
      "manifest": {"id": "mock-cpu-video", "name": "MOCK CPU Video Example", "is_mock": true},
      "compatibility": {
        "status": "compatible",
        "assessment": "unknown",
        "checks": [
          {"resource": "ram", "status": "compatible", "reason": "32.00 GiB detected; 8 GiB required."},
          {"resource": "storage", "status": "compatible", "reason": "100.00 GiB detected; 10 GiB required."},
          {"resource": "gpu", "status": "compatible", "reason": "This manifest allows CPU-only operation."}
        ],
        "notes": [
          "Basic declared hardware check only; driver, runtime, speed, and generation success are not verified.",
          "MOCK metadata only: requirements are fictional; this model cannot generate video."
        ]
      }
    }
  ],
  "hardware_warnings": []
}
```

- `compatible`: all declared basic checks pass.
- `incompatible`: at least one known measurement fails a requirement.
- `unknown`: a required measurement is missing or unreliable, with no definite failure elsewhere.

The CPU mock declares 8 GiB RAM and 10 GiB free storage. The GPU mock declares 16 GiB RAM, 30 GiB free storage, and one NVIDIA/AMD/Intel GPU with 8 GiB reliable VRAM. These are **fictional test requirements**, not recommendations of real models or claims about real ComfyUI support. Neither manifest has a Hugging Face download source.

The new `compatibility.assessment` adds evidence-aware reporting without changing `status`:

- `verified_compatible`: a locally validated profile, measured requirements, and all supplied hardware/runtime observations pass, with no unresolved assumptions.
- `potentially_compatible`: a plausible device exists, but requirements or prerequisites remain unverified.
- `unsupported`: a known requirement fails for the selected execution profile.
- `unknown`: evidence is too incomplete to identify even a plausible match; mocks also use this assessment.

This remains a comparison with declared metadata, not a live generation test. Runtime observations are currently `unknown`, and the hardware detector leaves GPU architecture `null`. A selected CUDA profile does not establish that AMD/Intel are unsupported by the entire model family. Wan normally has capacity `status: "unknown"`; a detected NVIDIA GPU with reliable VRAM may yield `assessment: "potentially_compatible"`.

## Model metadata and installation plans

Version 1 mock JSON files remain unchanged and valid. Version 2 real manifests add:

| Fields | Meaning |
| --- | --- |
| `huggingface_repo_id`, `pinned_revision` | Model author's repository and optional full 40-character immutable commit |
| `components` | Per-file publisher repository, revision, source filename, model-root-relative destination, exact/estimated bytes, optional SHA-256, precision, license, and evidence |
| `license_info` | License identifier/source, usage restrictions, and acknowledgement obligations |
| `tasks` | Existing generation capabilities, specific to this checkpoint |
| `execution_profile` | OS/backend scope, runtime version constraint/pin, UI/API workflow reference, core nodes, dependencies, custom-node sources/pins, resolution/frame preset, and offloading notes |
| `requirements` | RAM/storage/VRAM, GPU vendors/architectures, and limitations; unverified minima use `null` |
| `support_status`, `requirements_quality`, `evidence`, `unresolved_assumptions` | Research versus local validation, source quality, and outstanding assumptions |
| `installation_overhead_bytes` | Extra installation/cache/temporary budget; currently unknown for Wan |
| `artifact_installation_reviewed` | Defaults false; explicit review of full artifact/license inventory, separate from generation support |
| `license_documents` | Exact UTF-8 text, stable id/version, optional source, and SHA-256 checked against text; needed before acknowledgement |
| `is_fixture` | Defaults false; permits only clearly labeled offline mock component fixtures |

Unknown values use `null`. Exact file lengths are positive integer bytes; rounded publisher sizes use `estimated_size_bytes` separately. Runtime constraints use Python-style version ranges such as `>=0.3,<1`; a range must be researched, not guessed. A missing revision is accepted for research but blocks installation planning. Hashes are optional and absence produces a warning. Unknown JSON fields and unsafe/conflicting destinations are rejected at startup.

The Wan manifest references [the official Wan checkpoint](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B), the three [Comfy-Org artifacts](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged), and a [pinned native UI workflow](https://raw.githubusercontent.com/comfyanonymous/ComfyUI_examples/cb13911e7d83e4f61ca12e29629cab85a6c08856/wan/text_to_video_wan.json). It selects FP16 diffusion, FP8 UMT5, and the Wan 2.1 VAE. **Exact expected total: 9,828,025,775 bytes (9.828025775 decimal GB, about 9.153 GiB)**, excluding software/cache/staging/temporary space. All three expected sizes and published SHA-256 values were checked against pinned Hugging Face tree/LFS metadata. Components share pin `123acf1cc74bccbb9bfff8ac1ee72edc08c2341d`; the author repository has its own pin. No weights were downloaded or locally hashed. Both repositories currently report public, ungated access; binary transfer was not tested. Component publisher license declarations are recorded, but full conversion provenance/notices, supported runtime versions, storage overhead, and measured hardware requirements remain incomplete. No third-party custom nodes are required by this example. Details and the proposed installation services/API are in [downloader-design.md](docs/downloader-design.md); the implementation status and current routes are documented there.

`GET /api/models/{model_id}/installation-plan` returns all required components, absolute destinations, prerequisites, licenses, missing metadata, blockers, warnings, and destination-volume space. The service measures the nearest existing ancestor of the configured model root without creating it. It does not reuse or overwrite existing files, reserve space, inspect a runtime, or contact Hugging Face.

**Shortened Wan response; paths, free bytes, and compatibility depend on your machine:**

```json
{
  "model_id": "wan-2-1-t2v-1-3b",
  "read_only": true,
  "ready_for_installation": false,
  "status": "blocked",
  "components": [
    {
      "component": {
        "id": "diffusion",
        "repository_id": "Comfy-Org/Wan_2.1_ComfyUI_repackaged",
        "pinned_revision": "123acf1cc74bccbb9bfff8ac1ee72edc08c2341d",
        "filename": "split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors",
        "destination": "diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors",
        "expected_size_bytes": 2838303560,
        "estimated_size_bytes": null
      },
      "destination_path": "D:\\DIRECTOR-Resolve\\model_weights\\diffusion_models\\wan2.1_t2v_1.3B_fp16.safetensors"
    }
  ],
  "known_download_bytes": 9828025775,
  "total_expected_download_bytes": 9828025775,
  "total_estimated_download_bytes": 9828025775,
  "required_storage_bytes": null,
  "missing_metadata": ["installation_overhead_bytes", "requirements.min_ram_gb"],
  "blockers": [{"code": "missing_metadata", "message": "Required installation metadata is incomplete; see missing_metadata.", "component_id": null}]
}
```

The full response lists all three components and every missing field. `known_download_bytes` is a subtotal of exact known lengths; it is never a complete total when any component length is unknown. `total_expected_download_bytes` is available only when all lengths are exact. The legacy `total_estimated_download_bytes` prefers exact lengths when present, so it equals the exact total for Wan now. `required_storage_bytes` also needs declared overhead. Estimated shortfalls conservatively block review, with wording that identifies the budget as estimated. Existing destinations, unsafe links, unsupported profiles, unknown prerequisites, missing metadata, and unknown disk space also block review. Plans with no blockers are `reviewable`, never install-ready: `ready_for_installation` remains always false; this conservative runtime-aware review remains unchanged in 2D. Artifact installation uses separate checks described below. Unknown or invalid model IDs return HTTP 404; model IDs never become filesystem paths.

## Run the tests

The model-manager tests run entirely offline, with tiny synthetic bytes and mocked SDK calls. A Windows symlink case may skip without symlink privileges; real Windows junction protection is also tested.

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

This runs all automated tests. `pytest` checks hardware fallbacks, manifest validation, registry errors, capacity/profile compatibility, planner security and budgets, and API routes. Tests simulate hardware/runtime state and do not require a GPU or modify drivers. Synthetic test metadata marked locally measured does not certify Wan. Add `-v` to see each test name. Actual checks are recorded in `docs/verification.md`.

## Optional local configuration

No environment variables are required. To evaluate another drive or registry, set these before starting the server:

```powershell
$env:DIRECTOR_STORAGE_PATH = "D:\DIRECTOR-Resolve"
$env:DIRECTOR_REGISTRY_DIR = "D:\DIRECTOR-Resolve\model_registry"
$env:DIRECTOR_MODEL_ROOT = "D:\DIRECTOR-Resolve\model_weights"
```

The first selects the hardware endpoint's storage directory. The second selects the manifest directory. The third selects isolated model storage and logical planning destinations; the planner measures that drive separately, so a different hardware-storage drive does not produce a misleading budget. By default the model root is `model_weights` under the configured storage path. The directory need not exist and planning never creates it. Acknowledgement or installation creates only a marked .director namespace inside it. Relative paths are relative to the server's working directory; absolute paths are clearer. The app does not load `.env` files automatically. Changes apply on the next server startup.

## Test a tiny installation offline (Milestone 2D)

From PowerShell in the project root, after the setup above:

```powershell
Set-Location D:\DIRECTOR-Resolve
.\.venv\Scripts\python.exe -m director.installations.demo --root .\model_weights\fixture-demo
.\.venv\Scripts\python.exe -m director.installations.demo --root .\model_weights\fixture-demo --acknowledge-fixture-license
.\.venv\Scripts\python.exe -m director.installations.demo --root .\model_weights\fixture-demo --remove
```

The first command displays the fixture license and exits without accepting or installing anything (exit code 2). Read it, then the second command explicitly accepts it and installs a **60-byte synthetic text file**. It prints `install: ready` and `generation ready: False`. Repeating the second command verifies the existing installation. The third safely removes the active fixture; job, acknowledgement, journal and private cache records remain for recovery. No network, Hugging Face account, GPU or optional SDK is needed. This is a storage demonstration, not an AI model.

## Model Manager configuration and API

Read-only endpoints need no manager key. To enable local mutation endpoints and the built-in fixture, set these in the server terminal before running Uvicorn:

```powershell
$env:DIRECTOR_ENABLE_FIXTURES = "1"
$env:DIRECTOR_ALLOW_REAL_DOWNLOADS = "0"
$env:DIRECTOR_MODEL_ROOT = "D:\DIRECTOR-Resolve\model_weights\api-fixture"
$env:DIRECTOR_MANAGER_TOKEN = Read-Host "Enter a private local API key of at least 32 characters"
.\.venv\Scripts\python.exe -m uvicorn director.main:app --host 127.0.0.1 --port 8000
```

These settings add `fixture-tiny` to the registry response (four entries instead of the default three), keep real downloads disabled, select dedicated storage, and require a local authorization key. Keep the key private; do not put it in source files, URLs or logs. In a second PowerShell terminal, enter the same key:

```powershell
$managerKey = Read-Host "Enter the same local API key"
$headers = @{ "X-Director-Key" = $managerKey }
$base = "http://127.0.0.1:8000/api/models/fixture-tiny"
$requirements = Invoke-RestMethod "$base/license-requirements"
$requirements.documents | Format-List
```

After reading the exact fixture terms, explicitly acknowledge and request installation:

```powershell
$body = @{ accepted = $true; document_set_digest = $requirements.document_set_digest } | ConvertTo-Json
$ack = Invoke-RestMethod "$base/license-acknowledgements" -Method Post -Headers $headers -ContentType "application/json" -Body $body
$body = @{ manifest_digest = $requirements.manifest_digest; acknowledgement_id = $ack.id } | ConvertTo-Json
$job = Invoke-RestMethod "$base/installations" -Method Post -Headers $headers -ContentType "application/json" -Body $body
Invoke-RestMethod "http://127.0.0.1:8000/api/installation-jobs/$($job.id)" | ConvertTo-Json -Depth 10
Invoke-RestMethod "$base/installation" | ConvertTo-Json -Depth 10
```

POST returns HTTP 202 immediately; poll the job GET until it finishes. A successful job returns `state: "ready"`, `candidate_bytes: 60`, `verified_bytes: 60`, and `generation_ready: false`. Installation status separately returns `artifact_ready: true` only after hashing all active files. Failed jobs include an error code/message; a past ready job is not evidence files remain unchanged.

| Method/path | Behavior |
| --- | --- |
| GET `/api/models/{id}/license-requirements` | Reviewed exact document set and manifest digest; 412 if incomplete |
| POST `/api/models/{id}/license-acknowledgements` | Explicit boolean `accepted`, document digest, optional policy version `1`; 201 acknowledgement |
| POST `/api/models/{id}/installations` | Manifest digest plus acknowledgement id; 202 durable job |
| GET `/api/installation-jobs/{job_id}` | Phase, bytes, verification reports, cancellation flag, sanitized error |
| POST `/api/installation-jobs/{job_id}/cancel` | 202 request; 409 during commit/after completion |
| GET `/api/models/{id}/installation` | Verified active artifact status and separate generation readiness |
| POST `/api/models/{id}/installation/verify` | 202 offline integrity-check job |
| DELETE `/api/models/{id}/installation` | 202 inventory-scoped removal job; keeps cache/audit records |

Every POST/DELETE requires `X-Director-Key`, local Host and a matching Origin when present. Missing server key returns 503; unauthorized requests return 403; unknown IDs return 404; busy/duplicate/stale requests return 409; unmet prerequisites return 412; invalid bodies return 422. Repair is deferred. Requests cannot supply repositories, paths or Hugging Face tokens.

The optional real-transfer adapter dependency can be installed with `.\.venv\Scripts\python.exe -m pip install -e ".[dev,downloads]"`. This installs Python packages only. `huggingface_hub==1.0.0` is pinned and its installed public signature was checked. **Keep `DIRECTOR_ALLOW_REAL_DOWNLOADS=0` for this milestone.** Future opt-in uses `1`, but this alone cannot install Wan: reviewed complete license documents are still missing. Public transfers explicitly use `token=False`. Future authenticated transfers can select `DIRECTOR_HF_AUTH=login`, using the SDK's supported `hf auth login`/token-store mechanisms; Director never accepts token values in its API. The SDK's default token store is not encrypted by Director.

## Model Manager limitations

- Only tiny offline installations have been exercised. Real HTTP/Xet downloads, authentication and resume remain untested. Resume relies on reusing intact SDK partial cache; cancellation may force a restart.
- Cancellation terminates a supervised transfer process, but is refused during the short activation/removal commit section. Shutdown waits for that section.
- Storage reserves no space; it checks a conservative three-times-remaining-artifact budget plus 16 MiB and rechecks while writing. Other processes can still fill the disk.
- Link/reparse/hardlink checks reduce filesystem escapes but do not provide hardened Windows handle-level isolation against malicious concurrent same-user changes. Use a dedicated local directory. NTFS behavior on this machine was tested; other filesystems/network roots are not supported guarantees.
- Activation uses same-volume rename and an atomic pointer update, with durable records. Power-loss guarantees, antivirus locks and every crash boundary are not exhaustively tested. Interrupted transfers fail safely; startup never resumes network activity.
- Partial/orphan bundles, private caches and audit records are retained. Repair, cache garbage collection, shared artifacts, job pruning, idempotency keys and credential-vault integration are deferred.
- Status hashing is synchronous and can be slow for large models. No generation readiness is inferred from artifact readiness.

## Other limitations and next milestone

- Windows detection is best effort. Missing tools, drivers, or permissions produce partial results and warnings.
- NVIDIA total VRAM is read only if an existing `nvidia-smi` succeeds. Windows CIM VRAM values are estimates; AMD/Intel VRAM may therefore produce `unknown` compatibility.
- Capacity checks use total RAM/VRAM, not free RAM/VRAM. Profile checks compare declared OS/backend/architecture and supplied runtime observations; architecture and runtime remain unknown in the current detectors. CPU performance and generation success are unmeasured.
- Free space refers to one configured filesystem; it is not a complete inventory of all drives.
- Model metadata is loaded at startup. Invalid JSON, invalid schema, duplicate ids, or a missing registry folder fail startup with a diagnostic.
- Use this source checkout with an editable install; a standalone distributable package is future work.
- Wan is researched metadata, not a runnable supported model. The original 8.19 GB publisher report is not a ComfyUI minimum.
- Storage is a changing snapshot; dependencies, temporary downloads, shared artifact reuse, license acknowledgement state, and output encoding need future validation.
- There is no generation, ComfyUI runtime or Resolve integration. The frontend foundation is implemented.

Recommended next milestone: complete the real runtime artifact inventory, dependency lock and license review before separately authorizing software installation. See the Milestone 4C section below. Real model transfers and generation require later explicit authorization.

See [architecture](docs/architecture.md) and [engineering rules](AGENTS.md). The testing approach follows the [official FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/); data schemas use [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/).
# Milestone 4A runtime diagnostics

The System page now reads `GET /api/system/runtime` alongside the hardware endpoint. It reports OS/architecture, Python and PyTorch metadata, GPU driver versions, driver-reported CUDA capability, configured ComfyUI metadata, missing prerequisites and warnings. It never imports PyTorch, initializes CUDA, starts ComfyUI or installs anything. `installed` means observed metadata/file presence, not verified execution. Generation remains disabled.

Without configuration, Python/PyTorch observations describe **Director's backend environment only**; they do not inventory every Python installation. ComfyUI reports `not_configured`. Optional PowerShell configuration before starting the backend:

```powershell
$env:DIRECTOR_RUNTIME_ENV = 'D:\AI\existing-runtime-env'
$env:DIRECTOR_COMFYUI_DIR = 'D:\AI\existing-ComfyUI'
```

These variables select existing directories; they do not create or install them. The environment inspector currently understands Windows virtual environments (`Scripts/python.exe`, `Lib/site-packages`, optional `pyvenv.cfg`). It never executes that interpreter. Use absolute local paths without links/junctions or traversal. Unsafe/unreadable paths report unknown, without exposing their absolute locations in the runtime response. Restart the backend after changing configuration. Leave these variables unset if no runtime exists.

Start the backend from the repository root with `.\.venv\Scripts\python.exe -m uvicorn director.main:app --host 127.0.0.1 --port 8000`; this serves the local API. From `frontend/`, run `npm.cmd run dev`; open its local URL and select **System**. To inspect JSON directly, run `Invoke-RestMethod http://127.0.0.1:8000/api/system/runtime` in PowerShell.

CUDA toolkit discovery is intentionally `not_tested`; driver CUDA is a separate observation. AMD/Intel driver metadata remains visible without CUDA. Diagnostic commands have five-second timeouts and 64 KiB output limits. No manager key is sent for this GET request. See [runtime-readiness.md](docs/runtime-readiness.md) for remaining validation gates.

## Milestone 4C offline runtime fixture

Director can now provision a **simulated runtime** through the backend. It writes three harmless text files (149 bytes), verifies their exact sizes and SHA-256 hashes and activates an owned bundle. It installs no Python, PyTorch, CUDA or ComfyUI. The real Wan runtime profile remains an untested proposal and cannot be provisioned. This feature does not change the frontend.

The versioned profile schema records Python/architecture, ComfyUI commit, torch/CUDA wheel versions, optional TorchVision, dependencies, artifact URLs/size/hash, relative directories, validation stages and evidence gaps. Unknown metadata stays unknown. See [runtime-profile.md](docs/runtime-profile.md) and [architecture](docs/architecture.md#offline-runtime-provisioning-4c).

To try the fixture, stop any old backend first. In **PowerShell terminal 1**, use a dedicated local root and a private manager key of at least 32 characters:

```powershell
Set-Location D:\DIRECTOR-Resolve
$env:DIRECTOR_ENABLE_RUNTIME_FIXTURES = '1'
$env:DIRECTOR_ALLOW_REAL_DOWNLOADS = '0'
$env:DIRECTOR_RUNTIME_ROOT = 'D:\DIRECTOR-Resolve\runtime_storage'
$runtimeSecret = Read-Host 'Enter a private manager key (at least 32 characters)' -AsSecureString
$env:DIRECTOR_MANAGER_TOKEN = [System.Net.NetworkCredential]::new('', $runtimeSecret).Password
.\.venv\Scripts\python.exe -m uvicorn director.main:app --host 127.0.0.1 --port 8000
```

`Set-Location` selects the project. The fixture flag is an explicit development opt-in; the real-download flag stays off. The root isolates Director's test files; never point it into an existing environment or ComfyUI directory. The masked prompt supplies a key only to this backend process environment. Uvicorn starts the loopback API using the existing backend environment, without installing any software.

In **PowerShell terminal 2**, enter the same key, then review the plan. These GET requests create no installation directories:

```powershell
$runtimeSecret = Read-Host 'Enter the same private manager key' -AsSecureString
$runtimeKey = [System.Net.NetworkCredential]::new('', $runtimeSecret).Password
$origin = 'http://127.0.0.1:8000'
$headers = @{ 'X-Director-Key' = $runtimeKey; 'Origin' = $origin }
$base = "$origin/api/runtime/profiles/runtime-fixture-tiny"
Invoke-RestMethod "$origin/api/runtime/profiles" | ConvertTo-Json -Depth 12
$plan = Invoke-RestMethod "$base/installation-plan"
$plan | ConvertTo-Json -Depth 12
```

Expect `provisionable: true`, `total_expected_bytes: 149` and relative destinations under `.director-runtime/installed/<profile-id>/<job-id>`. The storage budget adds 16 KiB for records and a 16 MiB reserve. If blockers exist, resolve them before continuing. Existing fixtures must be verified or removed before another provision.

Only after reviewing the plan, explicitly confirm and submit:

```powershell
$confirm = Read-Host 'Type INSTALL to provision only the tiny text fixture'
if ($confirm -ne 'INSTALL' -or -not $plan.provisionable) { throw 'Fixture provisioning not confirmed or blocked' }
$body = @{ profile_digest = $plan.profile_digest; confirmed = $true } | ConvertTo-Json
$job = Invoke-RestMethod "$base/provision" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
Invoke-RestMethod "$origin/api/runtime/jobs/$($job.id)" | ConvertTo-Json -Depth 12
Invoke-RestMethod "$base/installation" | ConvertTo-Json -Depth 12
```

POST returns 202 immediately. Repeat the job GET until terminal. The lifecycle is `checking → staging → verifying → activating → installed_unvalidated`. Successful status shows `structurally_verified: true`, **`execution_validated: false` and `generation_ready: false`**. This proves the three text files match their inventory, not that any runtime can execute.

Optional controls (run each deliberately; the fixture may finish before cancellation):

```powershell
# Request cancellation before activation; completed/activating jobs return 409.
Invoke-RestMethod "$origin/api/runtime/jobs/$($job.id)/cancel" -Method Post -Headers $headers
# Recheck all installed bytes without executing software.
$verificationJob = Invoke-RestMethod "$base/installation/verify" -Method Post -Headers $headers
Invoke-RestMethod "$origin/api/runtime/jobs/$($verificationJob.id)" | ConvertTo-Json -Depth 12
# After verification finishes, remove only this owned fixture inventory.
$removalJob = Invoke-RestMethod "$base/installation" -Method Delete -Headers $headers
Invoke-RestMethod "$origin/api/runtime/jobs/$($removalJob.id)" | ConvertTo-Json -Depth 12
# For a failed/cancelled/interrupted provisioning job, explicitly clean its staging.
Invoke-RestMethod "$origin/api/runtime/jobs/$($job.id)/staging" -Method Delete -Headers $headers
```

Successful removal finishes `not_installed`; job history, journals and ownership records remain. Unexpected files, links or invalid ownership block deletion. Startup marks interrupted jobs without resuming; an active bundle after interruption needs explicit verification. Partial/orphan bundles are retained for manual inspection; repair and garbage collection are deferred. File/path checks do not protect against every malicious same-user filesystem race. No model licensing blocker is bypassed by this inert runtime fixture.

Stop the backend with Ctrl+C. In terminal 1, run `Remove-Item Env:DIRECTOR_MANAGER_TOKEN` and set `$env:DIRECTOR_ENABLE_RUNTIME_FIXTURES = '0'`. In terminal 2, run `Remove-Variable runtimeKey, runtimeSecret, headers`. Credentials are not stored in files or browser storage. Restart normally to hide the fixture. No configuration switch enables real runtime provisioning.

Run the complete offline backend tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

This checks the existing backend and runtime fixtures with temporary test directories and mocked interactions; it does not install or execute AI runtime software. See [verification history](docs/verification.md) for checks actually performed. Recommended next milestone: freeze and review the real runtime artifact inventory, complete dependency lock and licenses before any separately authorized installation.
# Stage 10 development timeline action

The opt-in `DIRECTOR_ENABLE_DEV_RESOLVE=1` backend adapter uses only Blackmagic's installed scripting module and the already verified Stage 9 clip. Open **Director Development** in Resolve and use the development Generate page (`VITE_DEV_GENERATION=1`) to **Review Resolve timelines**. Enter the manager key in memory, select an existing timeline or review creation of **Director AI Test** if none exists, explicitly check the approval box, then choose **Add to Timeline**. Visiting the page does not contact Resolve or modify timelines.

`GET /api/dev/resolve/timelines` and `POST /api/dev/resolve/placement` require the existing local manager authentication and Host/Origin checks. This deliberately supports only the known Stage 9 media item, not arbitrary files or new generation previews. A durable attempt receipt prevents automatic retries after ambiguous failures; inspect Resolve before further action. Production runtime provisioning remains disabled. No cleanup is performed.

# Stage 11 complete development workflow

Use [development-generation.md](docs/development-generation.md) to start the existing WSL runtime and Director with both development flags. Generate one fixed-workflow video, preview it, choose **Import to Resolve**, then explicitly review/approve a target before **Add to Timeline**. The result actions now follow the current generation job, rather than the historical Stage 9 clip. Conversion uses only the already installed WSL PyAV/libx264. Windows files and conservative operation receipts are retained under `generated_videos/development/<job_id>`. No cleanup, packaging or production installation is enabled.


## V1.1 product workspace

Start Director.cmd now opens the model-driven Windows development workspace with Generate, Model Store, Job Center, Storage and System. Normal authorization stays automatic and session-only. See [the user guide and feature boundaries](docs/product-v1.1.md) and [the exact blocked H3 proposal](docs/minimax-h3-plan.md). No new weights, production provisioning or redistribution are enabled.
## Director V1.1 delivery report

The resumed implementation and exact status of all 30 requested items are in [docs/product-v1.1-completion.md](docs/product-v1.1-completion.md). Use **Start Director.cmd** for the Windows-only development product workspace; stop its services with **Stop Director.cmd**. No manual manager key is required. The new visual shot planner is session-only and starts no inference; H3/audio/conditioned continuation remain blocked pending adapter validation and explicit artifact approval. No H3 weights or models were downloaded/deleted during this work.

