# Director architecture — Milestones 1–4J

The focused H3 Optimized extension uses one frozen four-artifact DmitryDB FL2VA NVFP4 recipe, not the full official Diffusers subset. `product/optimized_h3.py` specializes the existing download worker only for that exact recipe and explicit hashed-plan/license confirmation. Verified same-drive staging files register into the existing owned Windows model directories; failed activation rolls back new files and preserves Wan. Native object-info/loader discovery gates registration; first inference remains experimental. `generation/h3_workflow.py` dispatches a fixed native T2VA graph with MP4/H.264 and audio. Generic transfers and production provisioning retain their separate disabled gates. H3 Resolve/audio handoff remains unvalidated.

The additive `director.product.h3` boundary reviews only the pinned official MiniMaxAI T2VA component subset. Its separate Diffusers path allowlist does not broaden ComfyUI model destinations. Protected review/start-refusal routes report live hardware/disk and versioned license identity; they never call a downloader, install dependencies or turn a file-presence check into Ready. Wan's adapter/runtime and production gates remain unchanged. See `h3-installation-review.md` for current feasibility blockers.

The creative-studio extension is additive to V1.1. `product/studio.py` manages bounded projects/history and verified media copies in an ownership-locked `studio_data/.director` namespace. `studio_api.py` exposes manager-protected media/project and data-download operations. `product/downloads.py` reuses the existing storage/SDK/verifier for pinned inert data; `product/adapters.py` identifies exact reviewed families, and `model_tools.py` provides explicit native-file inspection, verification and metadata-only update checks. Atomic persistence retains the prior project snapshot; tests inject independent temporary roots. React components stay separate from typed clients/guards. See [creative-studio.md](creative-studio.md) for boundaries and unfinished adapter/installer work. Existing generation/conversion/Resolve adapters remain the execution path; no production installation gate changes.

## Windows launcher session authorization (Stage 13)

The private launcher generates `secrets.token_urlsafe(48)` per launch (384 bits). `DIRECTOR_MANAGER_TOKEN` goes to the backend and `DIRECTOR_LAUNCHER_TOKEN` only to the Vite server process. Neither is a VITE/client variable. An explicit non-secret `VITE_LAUNCHER_SESSION=1` flag enables same-origin UI discovery; `/api/launcher-session` returns only `{automatic:true}`. The browser client sends a non-secret request marker on privileged operations. The server proxy injects the credential only for exact `127.0.0.1:5173` Host plus matching Origin, or same-origin Fetch Metadata and matching Referer when GET omits Origin. Foreign/missing origin proof is rejected; supplied wrong credentials are never overwritten. Backend authentication remains unchanged.

Production builds/preview and default standalone development do not receive an automatic credential. No credential file, cookie, browser storage, URL or bundle contains the key. Stop signals only recorded owned processes, clears the in-memory key and removes the current session record/signals after all children exit. Model/media files and production provisioning gates remain untouched.

Milestone 4J adds optional validated notice classifications to runtime review metadata and its secured response. Classifications bind required document IDs, versions and available text hashes, retain unresolved obligations, and cannot clear preflight or installation authorization. Any uncertain notice classification also blocks review completion even when a completion flag is supplied. Their changes invalidate the document-set consent digest. Real provisioning remains disabled. A committed PyOpenGL ZIP inventory/notice receipt supports offline tests; the separately authorized binary itself stays in ignored quarantine and is never installed or imported.

## Runtime source, preflight and consent (4H)

The existing runtime adapter now includes `source.py` (separate source path policy, reviewed Git tree validation, bounded local ZIP extraction and staging journals), `preflight.py` (read-only lock/artifact/storage/license/conflict checks), and `review.py` (versioned runtime documents and explicit acknowledgements). Frozen metadata lives under `runtime_profiles/sources/` and `runtime_profiles/reviews/`. Source extraction reuses the streaming artifact verifier and owned runtime staging; model path rules are unchanged. No remote source acquisition or real activation is implemented.

Runtime acknowledgements use a separate owned namespace from model acknowledgements. The review digest binds document versions/checksums and approved artifact identities; acceptance is never installation authorization. The three review/preflight routes enforce existing manager-key and Host/Origin checks. Real preflight always remains installation-ineligible. Fixture activation restores the previous active pointer when publication fails and preserves its installed bundle; this does not implement real Python environment rollback. The frontend remains unchanged.

## Offline runtime provisioning (4C)

`backend/director/runtimes/` is a separate adapter with versioned profiles, isolated storage, an offline byte provider, durable jobs and HTTP routes. `runtime_profiles/wan-windows-candidate.json` represents the existing 4B proposal; its artifact inventory is incomplete and provisioning is always blocked. The built-in `runtime-fixture-tiny` appears only with `DIRECTOR_ENABLE_RUNTIME_FIXTURES=1`. No remote provider, package installer or execution validator exists.

`DIRECTOR_RUNTIME_ROOT` defaults to the ignored project `runtime_storage/` directory. Its `.director-runtime` namespace contains an ownership marker, staging, immutable installed bundles, active pointers, jobs and journals. Runtime storage reuses `ModelStorageManager` locks, atomic JSON records, space checks and link protection, with a distinct marker format. Model storage retains its original `.director` default. The common exact-inventory helper and streaming `ArtifactVerifier` serve both managers.

Roots inside Python installations, virtual environments, backend code, owned namespaces or external ComfyUI installations are refused. Relative paths reject traversal, Windows reserved names and conflicting destinations. Symlinks, Windows reparse points and hardlinked files are rejected. Removal refuses unexpected user additions and deletes only validated receipt files. These checks do not guarantee protection against a hostile same-user process changing paths between checks.

Provisioning is serialized with an in-process mutex and an OS ownership lock. It freezes the built-in profile digest, rechecks space while writing, verifies every exact size/hash, records ownership and profile identity, then activates a same-volume fixture bundle with an atomic pointer update. The fixture needs 149 payload bytes, a 16 KiB record allowance and 16 MiB reserve. Space is checked, not reserved. Fixture rename is appropriate for inert text; future real virtual environments must be constructed at their final candidate path rather than moved.

Lifecycle: `not_installed → checking → staging → verifying → activating → installed_unvalidated`. Failures/cancellation leave no successful active pointer; corrupted active files report `corrupted`. Startup marks nonterminal durable jobs `interrupted`, never resumes or executes them. Cancellation is cooperative and refused during activation/removal. Failed/cancelled/interrupted staging can be explicitly removed; orphan installed bundles, audit retention and repair remain deferred. Job errors are sanitized.

**Installed** means an owned bundle and active receipt exist. **Structurally verified** means the inventory, profile identity, ownership, sizes and hashes passed; status rechecks active bytes. **Execution validated** would require separately authorized interpreter/GPU/ComfyUI tests and remains false. Neither structural state nor the 4B proposal feeds a verified runtime into model compatibility or enables generation.

| Method | Path under `/api/runtime` | Purpose |
| --- | --- | --- |
| GET | `/profiles` | Profiles and `real_provisioning_enabled: false` |
| GET | `/profiles/{id}/installation-plan` | Read-only digest, bytes, destinations and blockers |
| GET | `/profiles/{id}/installation` | Fresh structural status; no execution |
| POST | `/profiles/{id}/provision` | Explicit `confirmed: true` plus reviewed `profile_digest`; 202 job |
| GET | `/jobs/{id}` | Durable state, bytes, verification and error |
| POST | `/jobs/{id}/cancel` | Cooperative cancellation; 202 or 409 when too late |
| POST | `/profiles/{id}/installation/verify` | Offline structural verification job |
| DELETE | `/profiles/{id}/installation` | Exact-inventory fixture removal job |
| DELETE | `/jobs/{id}/staging` | Explicit stopped-fixture staging cleanup |

All mutations reuse the existing manager key and trusted Host/Origin dependency. IDs are looked up in memory; callers cannot supply paths, commands, URLs or credentials. Missing key configuration gives 503; unauthorized requests 403; unknown IDs 404; conflicting/stale operations 409; disabled/unsupported provisioning 412; invalid bodies 422. Read-only endpoints do not create directories. The frontend and passive `/api/system/runtime` contract are unchanged. See the [fixture instructions](../README.md#milestone-4c-offline-runtime-fixture).

Director's eventual goal is to let a Resolve user generate video locally without learning model installation or ComfyUI nodes. The implemented backend provides hardware detection, researched metadata, compatibility reporting, read-only installation planning, and controlled artifact management. It is not a working video generator or Resolve plugin yet. The existing module boundaries are preserved.

## Frontend foundation (3A)

`frontend/` is a standalone React/TypeScript/Vite app with a committed npm lockfile. Plain CSS tokens control charcoal surfaces, a warm accent, typography and spacing. Original inline icons and an SVG favicon avoid proprietary Resolve assets. There are no remote fonts, image dependencies or placeholder successful responses.

```text
React pages: Generate / Models / Jobs / System
                 |
Typed API client + runtime guards + abort/timeouts
                 |
same-origin /api -> trusted loopback Vite proxy -> FastAPI API
```

`src/App.tsx` owns hash navigation, the shared model request and known job IDs. Native links support keyboard/browser history; a skip link and main focus follow navigation. `src/components/ui.tsx` provides panels, badges, notices, loading/error states and formatting. `src/hooks/useResource.ts` cancels stale requests, supports retry and prevents unmounted views receiving late data.

`src/api/types.ts` describes fields the UI consumes. `client.ts` performs basic runtime checks, handles JSON/FastAPI errors and network failures, uses a 45-second timeout and aborts discarded reads. Guards reject missing nested data rather than allowing a render crash; unfamiliar compatibility assessments display unknown. These guards do not replace backend Pydantic or implement the entire OpenAPI schema.

Generate is an explicitly disabled local draft. Models loads manifests and installation status; selection loads the existing read-only plan, licensing metadata, budgets and issues. System requests hardware on entry/refresh. No client-side hardware compatibility calculation substitutes for the backend. Jobs looks up known IDs, polls active jobs every four seconds after each batch completes, and refreshes terminal/error lookups manually. A maximum of 12 validated IDs is stored in tab session storage; no nonexistent list endpoint is called.

Explicit fixture acknowledgement, fixture installation confirmation and job cancellation are frontend mutations in 3B. Manager keys entered in Models or Jobs remain only in memory; GETs omit them. The client has typed acknowledgement and installation methods, but the UI restricts installation to the built-in fixture in explicit local development mode. Real-model installation, inference, upload, preview playback and Resolve controls remain disabled or absent.

Vite dev (5173) and local build preview (4173) proxy `/api` to `DIRECTOR_BACKEND_URL` (default loopback port 8000). `src/proxy.ts` accepts only loopback origins and checks incoming local Host/matching Origin before forwarding the backend Origin with `changeOrigin`. The proxy does not inject credentials; the backend still validates its existing key/Host/Origin rules. No CORS, proxy authentication or Host/Origin change was needed; 3B adds only a read-only artifact review to the existing plan route. Public `VITE_API_BASE_URL` defaults to `/api`; direct cross-origin deployment needs separately designed configuration. A built bundle requires a trusted same-origin API proxy outside Vite.

Frontend tests use test-only JSON exported from real backend schemas/registry/planner with synthetic hardware. No production fallback imports those fixtures. React Testing Library/Vitest cover UI/API behavior independently of GPUs; the actual local browser/proxy was checked separately. Full Windows startup, fixture/job tracking and key instructions are in [README.md](../README.md).

## Backend components

### Installation UI and artifact preflight (3B)

`ManagerAuthorization` is shared by Models and Jobs, keeping the key only in API-instance memory. `InstallationWorkflow` handles review, explicit consent, confirmation and returned job IDs. `ReviewDialog` uses a native modal for focus isolation, Escape dismissal and focus return. License text is escaped plain text, never manifest HTML. Opening pages/dialogs makes only read requests.

The existing installation-plan endpoint adds optional `artifact_review`: `can_review`, artifact blockers, expected bytes, manager storage budget, owned destination template, mandatory acknowledgement/key flags and `generation_ready: false`. Original `status`, `blockers`, compatibility and `ready_for_installation: false` retain their combined generation-planning meanings. Unknown fictional fixture runtime requirements remain visible without claiming generation support. `InstallationJobManager.artifact_review()` shares artifact metadata gates with startup, checks storage without creating folders, and rejects missing server-key configuration, active operations and existing receipts. It is a snapshot, not a reservation or consent.

Opening review refreshes plan and versioned/hashed license documents. Mismatched identities and missing documents fail closed. The initially unchecked checkbox enables an acknowledgement POST; a separate confirmation refreshes preflight, detects changed components/budget/destination and POSTs the reviewed manifest digest plus returned acknowledgement ID. Backend checks remain authoritative. Uncertain mutation responses are never automatically retried; users inspect Models/Jobs.

Only `fixture-tiny` can reach these UI controls, with backend `DIRECTOR_ENABLE_FIXTURES=1` and development-only frontend `VITE_ENABLE_FIXTURES=1`. Production hides fixture entries; Generate excludes them in every mode. The existing offline allowlisted provider cannot access Hugging Face. No real manifest or download permissions changed.

Inline progress polls a known ID every two seconds after completed requests, aborts reads on unmount, and stops at terminal/error states. Jobs keeps four-second polling and capped tab ID history. Transfer and verified bytes are separate; terminal errors include interrupted recovery guidance. Cancellation requires a key and is disabled during the commit section. The live fixture often finishes before intermediate states can be observed. Verified bytes reflect backend totals, not fine-grained hash progress.

```text
HTTP client (browser or PowerShell)
             |
      FastAPI backend
       /           \
Hardware detector  JSON model registry
       \           /
     Compatibility evaluator
             |
    Validated JSON response

Installation-plan route -> loaded manifest + hardware/runtime observations
                      -> planner + destination-volume disk snapshot
                      -> components, destinations, prerequisites, blockers
```

`backend/director/main.py` defines the original GET routes, wires the installation router and owns application startup. Startup validates and loads all JSON manifests once. An invalid manifest, duplicate id, or missing registry directory produces a clear startup failure so incorrect metadata is not silently hidden. An existing empty directory is valid and returns an empty model list. Restart the server after editing a manifest. Model IDs are matched in this in-memory registry, never used to construct paths. `get_hardware` and `get_runtime_state` remain injectable dependencies; runtime state is currently unknown and does not inspect or import ComfyUI.

`backend/director/system/schemas.py` defines `HardwareProfile` and nested CPU, RAM, GPU, and storage data. Pydantic describes the JSON shape and checks numeric bounds. All capacities use **GiB** (bytes divided by 1024 cubed), despite the concise `_gb` field names. Unknown values are `null`; they are not assumed to be zero.

`backend/director/system/hardware.py` reads CPU core counts and RAM through psutil, and disk capacity through Python's `shutil.disk_usage`. Storage refers to the filesystem containing the project root by default. `DIRECTOR_STORAGE_PATH` can select an existing directory on a different drive. This is a current free-space snapshot, not a reservation for future downloads.

On Windows, a fixed PowerShell CIM query reads CPU names and display adapters. It does not require NVIDIA. If an installed `nvidia-smi` command is available, a separate optional query gives NVIDIA total VRAM. The NVIDIA results replace CIM NVIDIA entries while preserving AMD/Intel entries. Subprocesses have a ten-second timeout each and use no shell interpolation. psutil and disk reads have operating-system-dependent latency.

Windows `Win32_VideoController.AdapterRAM` uses a limited integer field and may underreport modern GPU memory. CIM values are exposed as estimates (`vram_is_estimate: true`) and are **not trusted** by the evaluator. AMD/Intel VRAM may therefore remain uncertain. CIM enumeration is a basic display-adapter inventory, not a guarantee that a runtime can use those devices. If probes fail, warnings explain the missing information and the API still returns the remaining measurements. Non-Windows systems get basic CPU/RAM/storage detection and an explicit Windows GPU detection warning; optional nvidia-smi can still report NVIDIA memory.

`backend/director/models/schemas.py` defines version 1 and version 2 `ModelManifest` plus nested component, license, workflow, execution-profile, dependency, custom-node, and evidence models. Version 1 defaults preserve the unchanged mock JSON files. Version 2 requires a real repository identity, component inventory, license information, execution profile, and evidence; unknown pins, sizes, version constraints, and minima can remain null for research. Unknown fields, nonfinite capacities, malformed sizes/hashes/revisions, and inconsistent mock metadata are rejected. These fields are metadata, not executable commands or promises of runtime support. Wan is a real researched entry with `support_status: researched`, not generation-validated metadata.

Each component records its own artifact publisher separately from the model author. `expected_size_bytes` is exact; `estimated_size_bytes` is explicitly approximate. Byte sizes are strict positive integers, hashes are optional 64-character lowercase SHA-256 strings, and pins are full 40-character lowercase commit IDs. License summaries retain source URLs, restrictions, and acknowledgement obligations; per-component license provenance is separately tracked. `tasks` continues to describe checkpoint capabilities. `execution_profile` scopes OS/backend, runtime constraints/pin, core/custom nodes, dependency constraints, a workflow reference and format, dimensions/frames/batch, and offloading notes. The UI workflow reference is not treated as an API payload. Quantized/offloading variants would require independently researched profiles rather than changing a universal minimum.

`backend/director/models/validation.py` centralizes repository IDs, relative paths, destinations, and PEP 440 version constraints. Repository values must be owner/name identifiers, not URLs. Windows-safe destinations must be files beneath allowlisted ComfyUI model subdirectories: diffusion_models, text_encoders, vae, clip_vision, checkpoints, or loras. Absolute/drive/UNC paths, backslashes, traversal, empty path segments, alternate data streams, Windows device names, trailing dots/spaces, and unsafe characters are rejected. Case-insensitive duplicate destinations and file/directory ancestor conflicts are rejected, including conflicts separated by other entries in sorting order.

`backend/director/models/registry.py` reads top-level `*.json` files in deterministic filename order and validates them. `DIRECTOR_REGISTRY_DIR` can select another local directory. The registry does not contact Hugging Face or install anything. For this milestone, run the project from its source checkout using an editable install; the external registry is not bundled into a distributable wheel.

`backend/director/models/compatibility.py` compares total installed RAM, current free disk space, allowed GPU vendors, and reliable total VRAM. It does not require a particular CPU model. Available RAM is displayed but not used as the minimum-capacity criterion. The evaluator checks a single GPU at a time, even on machines with multiple GPUs.

Each resource produces a status and a reason. The overall result is:

- `incompatible` if at least one requirement is definitely unmet.
- `unknown` if no requirement definitely fails but some required information is uncertain.
- `compatible` if all declared checks pass.

A CPU-only mock skips GPU requirements. Successful GPU detection with no supported GPU fails a GPU-required model; failed/incomplete detection leaves that check unknown. The original `status` and `checks` retain these capacity-only meanings for existing consumers.

The additive `assessment` and `profile_checks` distinguish verified_compatible, potentially_compatible, unsupported, and unknown. OS/backend constraints, architecture and VRAM on the same GPU, runtime version/revision, dependency versions, and custom-node pins are compared. Estimated/unverified capacity and architecture requirements do not certify or definitively reject hardware in the assessment. A known profile failure yields unsupported; this refers to the chosen profile, not all possible model backends. A locally validated model with measured requirements, all observations passing, and no unresolved assumptions can yield verified_compatible. A plausible device with incomplete prerequisites yields potentially_compatible; mocks and incomplete inventories can yield unknown. The evaluator remains pure, accepting optional `RuntimeState` rather than probing packages or executing subprocesses. Synthetic passing profiles in tests do not validate real Wan generation.

Current probes do not identify GPU architecture, so `GPUInfo.architecture` defaults to null. Milestone 4A exposes passive runtime metadata separately; the model evaluator's execution `RuntimeState` remains unknown. Driver/kernel compatibility, free VRAM/RAM, speed, and generation success still require future adapter observations and local experiments. Wan therefore cannot be verified_compatible in the current application.

## Read-only installation planning

`backend/director/models/planning.py` consumes validated manifests, hardware, optional runtime observations, and a model root. It returns `InstallationPlan` with nested components and absolute destinations, exact known subtotal, exact total only when every file length is known, a separate complete estimated total where possible, and a full required-storage total only when overhead is known. All byte calculations use integers; storage capacities passed to compatibility use explicit bytes-to-GiB conversion.

`DIRECTOR_MODEL_ROOT` defaults to `DIRECTOR_STORAGE_PATH/model_weights`. It need not exist. The planner walks to its nearest existing ancestor and uses `shutil.disk_usage` there; it does not create installation directories. This measures the destination volume independently of the hardware endpoint's storage selection. Storage errors stay unknown and block review. Space is a snapshot, never reserved. Partial exact lengths provide only a lower bound; insufficient known/estimated space blocks review, and unknown overhead remains explicit.

Destinations are resolved and checked for containment beneath the resolved model root. Escaping symlinks/junctions, parent files, conflicting resolved destinations, and existing files/directories produce blockers. Existing files are not hashed, trusted, reused, or overwritten. Schema validation is repeated at the service boundary to reject mutated objects that bypassed normal Pydantic construction. Invalid local manifests still fail at registry startup.

Missing revision pins, exact sizes, component license/evidence, runtime/workflow constraints/pins, hardware minima/architecture, unknown runtime prerequisites, and unresolved assumptions are exposed as structured metadata gaps/blockers. Optional missing checksums are warnings. Licenses, acknowledgements, runtime dependencies, core nodes, and custom nodes are reported but not installed or executed. Explicit versioned license acceptance tracking is implemented separately in the installation package.

`status` is blocked or reviewable. Reviewable only means no declared blocker was found. `read_only` is always true and `ready_for_installation` is always false: no installer exists through Milestone 2C. Unsupported or incomplete profiles never become ready. Wan now has exact expected sizes, published SHA-256 values, common component revision pins, and pinned upstream/workflow sources. Its plan remains blocked by incomplete component provenance/notices, measured minima, runtime constraints and overhead. No network requests are made by registry loading, compatibility evaluation, or planning.

## Milestone 2C — evidence and design, no new services

The Wan JSON was refined within the existing v2 schema; schema/validator/evaluator/planner/route implementations were not changed. Its exact weight total is 9,828,025,775 bytes. Metadata verification does not mean downloaded files have been checked or generation has been validated. Public/ungated access flags and license declarations are source evidence, with their limits recorded explicitly. The initial mocks remain unchanged.

The five services are implemented in `backend/director/installations`: ModelStorageManager, ArtifactVerifier, HuggingFaceDownloader, InstallationJobManager, and LicenseAcknowledgementStore. A single worker thread supervises jobs; real SDK transfers run in a spawned process. FastAPI lifespan owns the manager and closes it at shutdown. A root OS lock prevents two backends managing the same storage.

Storage lives under `DIRECTOR_MODEL_ROOT/.director`, with separate staging, installed bundles, SDK cache, receipts/pointers, jobs/journals, and acknowledgements. Activation renames a fully verified bundle on the same volume, then replaces the active pointer atomically. Recovery checks durable records without starting a download. Link/reparse and hardlink checks fail closed; removal accepts only the frozen receipt inventory and refuses unexpected additions.

Artifact `ready` means verified files in an active Director bundle. It does not establish runtime/hardware compatibility: `generation_ready` is always false. The combined legacy planner remains conservative and unchanged, including its logical flat destinations. Actual managed destinations add the owned bundle prefix; no ComfyUI directory is modified.

Schema additions default safely for legacy manifests: `is_fixture=false`, `artifact_installation_reviewed=false`, and `license_documents=[]`. Documents carry exact text/version/hash; changed documents, restrictions or component pins invalidate acknowledgement. Wan's metadata is preserved, but its incomplete reviewed document set blocks installation even when downloads are explicitly enabled.

See [downloader-design.md](downloader-design.md) for implemented contracts, routes, transition rules and deferred features, and [README.md](../README.md) for configuration/offline demo commands.

## HTTP API and testing

- `GET /api/system/hardware` reads and returns a fresh hardware snapshot.
- `GET /api/models` reads one fresh snapshot and evaluates every loaded manifest against it, returning `models` and `hardware_warnings`.
- `GET /api/models/{model_id}/installation-plan` returns a read-only plan with a separate destination-volume measurement. Unknown/invalid IDs return HTTP 404 before hardware probing; URL-normalized nonexistent routes also return 404.
- FastAPI publishes `/openapi.json`, `/docs`, and `/redoc` automatically. Its interactive documentation UI may require internet access for CDN-hosted assets; the API itself and OpenAPI JSON work locally.

The HTTP handlers are synchronous so blocking probes run in FastAPI's worker threads; long installation tasks run in the separate job executor. Durable JSON records replace a database. Management mutations use a local API key, Host/Origin checks and loopback binding. The frontend foundation exists; there is no multi-user authentication. Offline tests inject hardware and synthetic bytes; the registry/evaluator can still be tested independently of real GPUs and transfers.

## Future components — not implemented

The frontend foundation and Milestone 3B installation review/license acknowledgement workflow exist, with an opt-in offline model fixture. The 4C runtime adapter provisions inert fixtures only; real ComfyUI installation, startup, health checks and inference remain future work. A separate Resolve adapter will handle scripting availability, Media Pool imports and timeline operations. Complete real dependency management and generation previews are not implemented.

The [runtime readiness review](runtime-readiness.md) documents remaining license/provenance gaps and runtime validation gates. Milestone 4A implements passive inventory in `backend/director/system/runtime.py` and `GET /api/system/runtime`. Typed observations distinguish installed, not_detected, unknown, not_tested and ComfyUI not_configured. The pure readiness summary can only return incomplete or unknown; GPU execution is always not_tested and generation_ready is false. It does not feed package presence into the existing compatibility evaluator as a validated runtime.

`DIRECTOR_RUNTIME_ENV` optionally selects an existing Windows virtual environment; otherwise only backend Python/package metadata is inspected. `DIRECTOR_COMFYUI_DIR` selects an existing ComfyUI root. Configuration is captured at backend startup. There is no filesystem-wide discovery, arbitrary interpreter execution or package import. Expected ComfyUI files and bounded pyproject metadata are inspected without executing source. Paths reject traversal and symlink/reparse ancestors; responses omit configured absolute paths. File inspection is not a security audit or immutable-source verification.

Windows driver metadata uses a fixed CIM script through the OS PowerShell location. NVIDIA queries use trusted OS/vendor locations and support CUDA Version and CUDA UMD Version labels. External commands are capped at five seconds/64 KiB. Missing tools, malformed data and timeout failures produce unknowns/warnings. The CUDA toolkit is not probed. The frontend's guarded, abortable API client loads hardware and runtime independently, so one failure does not hide the other. Runtime installation and generation remain future work; real Wan downloads remain disabled and blocked.
# Stage 8 development adapter

`backend/director/generation/` contains the fixed Wan workflow, bounded loopback ComfyUI HTTP client and small in-memory generation job adapter. It reuses manager authentication and existing link/junction checks; it remains separate from installation/provisioning jobs because submitting inference is not artifact installation. It never starts or installs a runtime. `DIRECTOR_ENABLE_DEV_GENERATION=1` is the opt-in boundary. No production installer setting is changed.

The frontend development Generate panel uses the existing typed API client and in-memory manager authorization. It polls job history, retrieves authenticated job-associated WebM bytes through Director, then previews a browser blob URL. Output roots are configured server-side and not exposed as arbitrary file APIs. See [development generation](development-generation.md) for exact settings, endpoints and recovery limitations. Production builds hide this panel.

# Development-only Resolve boundary (Stage 10)

`backend/director/resolve` is a separate opt-in adapter (`DIRECTOR_ENABLE_DEV_RESOLVE=1`). It lazily connects through Blackmagic's installed scripting API, reports timelines in Director Development, and requires an explicit confirmed target before one placement of the verified Stage 9 Media Pool item. No ComfyUI/Resolve module is imported during hardware, registry or ordinary backend startup tests. The development UI has a review, target selection and initially unchecked approval. It preserves manager-key protections and never accepts filesystem paths or arbitrary media IDs. Placement rechecks the MP4 size/hash, online media identity, target ID/name, and existing placement; verification checks returned timeline item identity, item inventory and duration to within one timeline frame. Attempt receipts in `.verification/stage10` prevent retry after partial failure. This is not a general timeline editor or production integration.

# Stage 11 job-associated development results

`GenerationResolveJobs` joins the existing generation service and separate Resolve adapter, without changing production installation gates. Completed generation IDs select safe per-job Windows output folders. A fixed bounded `WslVideoConverter` executes only the existing trusted WSL PyAV conversion; callers cannot supply paths, binaries or command arguments. Decoded frame metadata plus stable regular-file bytes/hash are verified before import and rechecked before placement/output retrieval. Conversion/import receipts conservatively block retry after interruption; placement uses the shared Stage 10 identity/target/inventory/duration checks and a per-job attempt marker. Job result actions use the same local manager key and Host/Origin protections. UI actions require explicit import and separate unchecked target approval; visiting Generate starts neither action.

# Stage 12 private Windows adapter

The private Windows runtime is separate from production runtime provisioning: `runtime/windows-dev-001` contains the final-path CPython 3.13.16 environment, pinned ComfyUI source, verified copied models and receipts. The existing generation adapter accepts a configured Windows output path without a WSL dependency. With `DIRECTOR_DEV_WINDOWS_RUNTIME=1`, Resolve result conversion uses the fixed `WindowsVideoConverter` and owned PyAV interpreter. It reuses the existing frame/codec/hash verification and job-associated import/placement flow; requests cannot select paths, executables or workflows. The WSL converter remains an explicit fallback for the prior environment.

`scripts/windows_launcher.py` starts only loopback Windows services, never installs/downloads, refuses occupied ports and records process ownership without keys. Manager authorization remains a user-entered in-memory secret; the startup and UI fields are masked. Cooperative shutdown signals the owned ComfyUI runner and interrupts each other owned service console. Start/Stop wrappers provide a development convenience, not installer/redistribution readiness. Default backend flags and production frontend generation remain disabled.


## V1.1 additive product layer

`backend/director/product` contains validated capability/scene/audio contracts, metadata-only discovery, exact owned asset references, storage inventory and redacted activity events. Authenticated `/api/product` routes reuse the generation and model manager rather than accepting new workflows. `ProductWorkspace` is launcher-selected and preserves automatic session authorization and the existing Resolve result/confirmation components. See [implemented behavior and explicit limits](product-v1.1.md). The native Windows runtime and production NO-GO boundary remain unchanged.
## V1.1 component and metadata boundary

The product page coordinates session state and polling; its creative form, result/Resolve actions, Model Store, storage review and visual shot planning are separate `frontend/src/components/product` components. Shot plans remain browser-memory drafts and never queue continuity inference. Backend `Shot`/`SequencePlan` and audio-output contracts reject unsupported execution and unowned references.

HF details inspect bounded official metadata at an immutable revision, then fetch only a small model-card text. Published file sizes/hashes are displayed as metadata, not installed-artifact verification or a download recipe. Whole-repository totals include variants. Cached search/details results are explicitly labeled; neither discovered metadata nor an installed filename grants execution readiness.

