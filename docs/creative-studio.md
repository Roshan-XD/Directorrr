# Director creative studio

This extends the validated V1.1 workspace. Start and Stop Director remain Windows-only and retain ephemeral, server-side authorization. Wan is still the only execution-validated adapter. Production provisioning and binary redistribution remain disabled.

## Everyday workflow

1. Run `Start Director.cmd`. Generate uses the installed Wan adapter and its bounded controls.
2. Choose/create a project. Prompt/settings and planned shots autosave after 900 ms of idle editing. Named presets retain prompt and settings together. A changed model preserves compatible choices and resets incompatible resolution, duration, quality and workspace choices.
3. Open Library to view managed images, video and WAV audio. Add media or drop up to 12 files, each under 64 MiB. Existing trusted private PyAV performs bounded CPU decoding and creates thumbnails. No uploaded code is executed.
4. Completed live jobs are copied to the Library automatically when observed by Director. Index existing Director videos explicitly to recover earlier native outputs. Recovered clips have unknown original generation settings; recovery does not fabricate those settings.
5. Search/filter, favorite, rename, compare two assets, reveal a copy in Explorer or download it. Deleting a Library copy requires an unchecked confirmation and preserves the original generated output. Project references block removal.
6. Resolve import and timeline approval continue through the existing live job result. Archived Library records do not restore a live Resolve mutation session.

## Live model discovery

Model Store uses the official public [Hub API](https://huggingface.co/docs/hub/api) and its documented [model listing parameters](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api#huggingface_hub.HfApi.list_models). Search, publisher, task, downloads/likes/update/trending sorts and explicit pagination are available. Results are twelve per page; only the official same-endpoint Link cursor is followed, represented by an opaque local token. Cards are pinned to a 40-character commit and displayed as plain text. Unknown repositories are never called Director-compatible merely because their names resemble a known model.

Successful metadata is cached in owned local storage. Offline results are labelled cached; an offline card cannot authorize a new transfer. Installed local generation does not depend on catalog access.

## Data downloads versus installation

Select exact files on a model card and review the data-only plan. The service reuses ModelStorageManager, HuggingFaceDownloader and ArtifactVerifier. Exact immutable revision, positive byte size and published SHA-256 are mandatory. Gated access, missing/custom license review, unavailable pinned license text or offline metadata block transfer. The license text and checksum are included in the plan digest; acknowledgement and confirmation are never preselected. A changed plan requires another review.

Repository downloads default to disabled. `DIRECTOR_ENABLE_REPOSITORY_DOWNLOADS=1` is a separately reviewed development opt-in; the launcher does not set it. Do not enable it or transfer weights until the user has approved the exact files/volume/terms. This setting permits inert selected data only. It does not enable production provisioning, install dependencies, custom nodes, repository Python, `trust_remote_code`, or generation.

Jobs persist under `repository_data/.director/`. States: queued → downloading → verifying → completed, or failed/cancelled. Size and streaming SHA-256 pass before each file is marked verified. Approximate observed candidate speed/ETA are nullable and separate from verified bytes. Conflicting concurrent starts are rejected. Cancellation stops the existing bounded SDK worker; interrupted sessions become failed and never resume automatically. Retry requires a fresh plan. Explicit removal requires a current inventory digest; unknown files block deletion and SDK cache is retained for separate review. Pause and automatic resume are not implemented.

Supported-family installation continues through the existing manifest planner, license review and Model Manager. The fixture flow is available under its explicit development settings. A general family install-to-ready pipeline for new real models is **not complete**: a family must first have an approved recipe, current grants, runtime binding and validated execution adapter. Current Wan is already installed; H3 remains blocked. Repository data cannot become Ready by download completion.

## Persistence and security

`DIRECTOR_STUDIO_ROOT` optionally selects a separate Director-owned studio data root. Automated endpoint tests use isolated temporary roots, never the user's live Library. The launcher retains the project-local default.

`studio_data/.director/studio.json` contains bounded projects, presets, shots, media metadata and up to 500 archived job observations. Writes are atomic and retain a previous metadata snapshot. Metadata failure preserves files; automatic recovery from an invalid snapshot is not attempted. Media is copied into ID-associated owned directories, limited to 500 assets. Neither session keys nor arbitrary input/output paths are accepted. A second process cannot acquire the same storage lock. File retrieval and deletion check ownership/link/hardlink containment and integrity. Source outputs remain separate.

New protected APIs: `/api/product/studio`, `/studio/projects`, `/library/upload`, `/library/{id}/file`, `/edit`, `/delete`, `/reveal`, `/handoffs`, `/library/import-outputs`, `/downloads`, `/downloads/plan`, `/downloads/{id}/cancel`, `/removal-plan`, `/remove`, `/adapters`, `/discovery/compatibility`, `/models/{id}/files`, `/verify`, `/update-check`. All preserve manager, Host and Origin checks. Model update checks are metadata-only and never replace files.

## Deliberate limitations

- Image-mode contracts and an honest image workspace exist; no image-generation adapter/weights are installed. Animate/reference checks offer only actual runnable compatible adapters. Wan T2V accepts no image reference, so no image→video inference is available yet.
- Pipeline is read-only inspection of the approved Wan graph. Arbitrary node editing/execution remains unavailable.
- Console supports level/category/text filters, auto-scroll and collapsed consecutive repeated events. It is not a terminal. The safe local-terminal design remains documented in V1.1; no command execution is added.
- Catalog caching does not establish legal grants or compatibility. Restricted and gated repositories need a specific reviewed route.
- Asset previews are paginated (24 initially), lazy thumbnails and authenticated object URLs. Import decoding is CPU-only with a 20-second limit and maximum 4096×4096 geometry. The private media decoder must already be present.
- Undo/redo beyond native text editing, pause/resume, automatic repair, a general new-family installer, image execution and cross-model conditioned execution remain unfinished.

Next practical step: approve one image model's exact recipe/terms/weights, implement its native adapter, then validate one image → Library flow before adding an image-to-video adapter. Do not download it as part of this implementation.
