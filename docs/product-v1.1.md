# Director V1.1 product workspace

## Everyday use

Double-click **Start Director.cmd**, then use the automatically opened local page. The launcher enables `VITE_PRODUCT_WORKSPACE=1` only in development and retains session-only internal authorization. No manager key is saved or requested in normal launch. Stop with **Stop Director.cmd**; user media/models survive. Standalone developer mode and production builds retain the previous guarded interface.

Choose installed Wan -> Text to Video -> describe a shot -> select duration/aspect/quality -> Generate. Job Center and the footer track the session even while browsing other pages. Return to a completed result for preview/Open video/Save video, controlled MP4 import to Resolve, and the existing explicitly confirmed timeline action. Open video uses a validated authenticated blob, not arbitrary filesystem execution.

## Implemented architecture and limits

Capabilities live in `model_registry/capabilities/`, separate from installation manifests. Pydantic rejects unknown fields, invalid defaults, temporal grids, unsafe sources and component inventories. An installed file inventory requires every expected component. File-size presence and previous hash receipts are reported as metadata; they are not new streaming verification or arbitrary generation guarantees.

The new `/api/product/*` API is additive and manager-authenticated with unchanged Host/Origin checks. The legacy generation endpoint remains fixed prompt/seed-only. The product endpoint validates declarative choices before varying the same approved native graph. No request can supply nodes, component names, executable paths or workflow code. Wan workspaces remain T2V only. The H3 family is a published, blocked candidate, not an enabled adapter.

| Area | Behavior |
|---|---|
| Duration | Human 1/2/4/6/8-second choices map to 17/33/65/97/129 frames. Exact duration is frames/16: labels are approximate, technical details are exact. |
| Aspect/resolution | Exact paired presets: 320x192 preview (5:3), 512x288 (16:9), 288x512 (9:16), 384x384 (1:1), 512x384 (4:3). No invalid Cartesian product. |
| FPS | Wan generates and exports 16 fps. No fake interpolation or independent 24/60 fps conversion. |
| Quality | Fast 8, Balanced 16, High 24 steps. Only original preview/17 frames/8 steps/CFG6/shift8 is execution validated. Other combinations show experimental warnings. |
| Advanced | Bounded steps 1-32, CFG1-10, shift1-12 and negative prompt. Sampler uni_pc/simple, batch1, models and precision stay fixed. |
| Camera | Natural-language static/pan/push/pull/orbit guidance; no guarantee of camera motion. |
| Seeds | Cryptographically random new seeds by default; optional lock; job settings/seed reusable. Creative draft survives navigation in memory. |
| Job Center | Automatic bounded 12-job backend-session history; no required ID entry. Actual queued/running/completed/failed/cancelled states. Percentages stay absent when unavailable. Separate manager job records show actual transferred/verified bytes. |
| Cancellation | Pending deletion targets only the owned prompt. Running interruption requires an exclusively owned empty-external queue. Cancellation is not confirmed until ComfyUI reports interruption. No ambiguous submission retries. |
| History/retry | Removing history never deletes video. User retry creates a new job; uncertain prior submissions remain blocked. History is not a durable media database. |
| Model Store | Installed versus candidate states, details, sources/licenses, Use model, exact removal review. Existing installation review/acknowledgement/fixture flow is reused in its developer disclosure. |
| Discovery | Manual official HF metadata search, capped responses, fixed host/no redirects/no credentials. Details re-query an immutable revision and show publisher, tags, license declaration, update time, file sizes and published LFS hashes. Whole-repository size includes variants and is not an installation recipe. Unknown metadata stays unknown. Search/card caches explicitly label offline results. Plain model-card text never renders HTML or executes repository code. Discovered repositories are not runnable/installable adapters. |
| Installation | Existing license/digest/disk/hash/job gates remain authoritative. Real downloads remain disabled; H3 has no install button that can transfer weights. |
| Removal | Explicit unchecked confirmation and exact inventory digest. All exclusive hashes verified before any rename; staged rename failures roll back. Shared references lose only the removed model. User videos, runtime files and unregistered files are preserved. Native reference state persists in the owned receipt. Interrupted filesystem cleanup is reported; it is not silently retried. |
| Storage | Bounded non-link traversal, category totals, incomplete measurements and free-space warnings. Models, Python, packages, ComfyUI, output, cache/temp are separate. Native outputs and Windows handoffs are separate copies, not unique-media totals. |
| Cache/orphans | Only registered unreferenced cache assets can enter a digest-reviewed deletion plan. The current native setup has no registered disposable cache files. Unknown files are retained; general orphan adoption/deletion is intentionally not inferred. |
| Console | 300 bounded application events, search/level filter/copy/clear. Exact session-key and token-pattern redaction. Generation/explicit installation/Resolve events only; this is not a raw subprocess terminal or complete ComfyUI sampling log. |
| Resolve | Existing job-associated conversion/import and fresh explicit timeline selection are reused. Conversion supports the bounded Wan sizes/durations and validates matching output metadata. It rejects unexpected audio rather than silently dropping it. |

Removing the only installed Wan model disables local generation. Real-download gates do not permit automatic reinstall. The removal review should be treated as deliberate irreversible file deletion; no real model/cache removal was performed during verification.

## Sequence and audio contracts

`Shot` and `SequencePlan` separate creative notes from completed owned job references. Duplicate shots, unowned references, unsupported continuation/native audio are rejected. Adapter capability determines whether references, first/last or native continuation can execute. Generate includes a visual plan of up to 12 shots, with copied creative settings, editable continuity notes and references to completed session jobs. It survives page navigation in memory and queues nothing. Wan has no conditioned continuity; Continue Previous Shot stays disabled. Executable reference uploads, conditioned continuation and the H3 adapter await a validated supporting model.

`SceneOutput` and `AudioTrack` keep origin, codec, sample rate/channels and decode verification explicit. Native audio cannot be represented as Resolve compatible if audio was not decoded/verified. The future H3 adapter must carry audio latent -> audio VAE -> mux -> preview -> AAC/MP4 conversion -> Resolve and preserve synchronization. Separate user soundtracks are a different origin, never called native model audio. Current Wan is silent; no audio controls are shown.

## Reviewed Developer Terminal design (not enabled)

Keep the Activity Console separate. A future local terminal should use Windows ConPTY under the current non-admin user, explicit Developer Mode plus per-session confirmation, a fixed project working directory and shell chosen by the local application. Strip manager/HF credentials, tokens and inherited private service settings. No remote PTY endpoint, no automatic commands and no frontend-submitted command fragments. Bound scrollback/process lifetime, display exit status and close only the owned process tree on Stop. Repository/module execution requires its own approval. A terminal is deferred rather than introducing an unaudited HTTP shell in this release.

## APIs

All routes below require existing manager authorization. The launcher proxy supplies it only for its trusted marked local session requests.

- GET `/api/product/models`, `/jobs`, `/installation-jobs`, `/storage`, `/console`
- GET `/api/product/discovery?q=...`, `/discovery/details?repository=...`
- POST `/api/product/generation` with typed CreativeRequest
- POST `/api/product/jobs/{id}/cancel`, `/{id}/forget`
- GET `/api/product/models/{id}/removal-plan`; POST `/{id}/remove` with fresh digest and confirmed=true
- GET `/api/product/cache/removal-plan`; POST `/cache/remove` with reviewed digest and confirmed=true
- POST `/api/product/console/clear`

Existing `/api/models/*`, `/api/dev/generation/*`, `/api/dev/resolve/*` and runtime preflight remain intact. Productization does not change installation authorization or third-party redistribution clearance.

## Verification and remaining boundaries

See docs/verification.md and docs/product-live-check.json. Automated external calls/inference are mocked and removal fixtures are tiny. Live UI/API checks use the actual Windows-only launcher without generation or Resolve mutations. A new Wan inference with experimental settings is not claimed. Model-card discovery is metadata, not a hardware benchmark.

See [the exact H3 plan](minimax-h3-plan.md). The selected Turbo artifact set is about 39 GiB and needs explicit acceptance/transfer authorization and a constrained memory feasibility test. Native audio/sequence execution, durable media history, arbitrary discovered-model installation, general orphan cleanup, runnable Developer Terminal and bundled redistribution are not claimed complete. The complete 30-point delivery matrix is in [product-v1.1-completion.md](product-v1.1-completion.md).

The workspace orchestrator is separate from `components/product/`: CreativeForm, ProductResult, ProductModelStore, ProductStorage and ShotPlanner. The interrupted large refactor did not run; the resumed work moved each component separately and verified the result.
