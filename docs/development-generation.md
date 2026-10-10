# Stage 8: development-only generation adapter

## Stage 12 Windows development route

The Start Director launcher selects `DIRECTOR_DEV_WINDOWS_RUNTIME=1`, `DIRECTOR_DEV_GENERATION_OUTPUT=D:\DIRECTOR-Resolve\runtime\windows-dev-001\data\output` and the existing loopback ComfyUI URL. It uses the copied verified models and pinned Windows ComfyUI candidate, not WSL. Conversion executes the private Windows PyAV/libx264 interpreter with the same fixed controlled script. No workflow settings changed. Start/Stop instructions and remaining portability limits are in [the Windows guide](windows-native-runtime.md). The earlier WSL commands below remain reference/fallback instructions; never run both routes on the same ports.

## Stage 11 result actions

For the complete development flow, also set `$env:DIRECTOR_ENABLE_DEV_RESOLVE = '1'` before starting the backend. Resolve must already be open with **Director Development** loaded. After a completed generation and preview, **Import to Resolve** explicitly converts that job's WebM using the existing WSL venv's PyAV/libx264, verifies all 17 frames, and imports its H.264/MP4. A normal Windows copy lives under `generated_videos/development/<job_id>/`; the original WSL WebM and a Windows WebM copy are retained. No runtime, tool or model is installed/downloaded.

Then choose **Review Resolve timelines**, select the target, check the initially unchecked approval, and choose **Add to Timeline**. **Decline placement** makes no mutation. Only an imported, online, size/hash-verified result can be placed. Stage 9/10 legacy media is never substituted for a new result. Each job has a durable conversion/import state receipt and a placement-attempt receipt. Failures/uncertain mutations require inspection; no automatic retry or resume is provided. In-memory generation jobs still require the same backend session; restarting loses their lookup. No cleanup is performed.

All `/api/dev/resolve/jobs/{job_id}` routes require manager authentication and existing Host/Origin protections: GET result, POST `/import` (controlled conversion plus import), GET `/output` (MP4), POST `/placement` (confirmed target). No route accepts a file path, media ID or command fragment. The current UI previews the authenticated original WebM; the validated MP4 is available from the authenticated output route. Generation remains the same 320×192, 17 frames, 8 steps, CFG 6, shift 8, uni_pc/simple, 16 fps workflow. Production runtime remains NO-GO.

This adapter connects Director to the separately validated WSL ComfyUI server. It does not install software, download models, start ComfyUI, or authorize Director's native Windows runtime. Production installation remains NO-GO.

## Start the existing development server

Use the already installed Stage 6 source and Stage 7 model files. This command starts only the existing server, bound to loopback, with custom nodes and online model lookup disabled:

```powershell
wsl.exe -d Director-GPU-Dev -u root --exec /opt/director-gpu-dev/venv/bin/python -s /opt/director-gpu-dev/stage6/ComfyUI/main.py --listen 127.0.0.1 --port 8188 --offline --disable-all-custom-nodes --disable-auto-launch --disable-dynamic-vram --use-pytorch-cross-attention --base-directory /opt/director-gpu-dev/stage7/data --user-directory /opt/director-gpu-dev/stage7/data/user --models-directory /opt/director-gpu-dev/stage7/models --temp-directory /opt/director-gpu-dev/stage7/data/temp
```

Leave that terminal open. Stop it with Ctrl+C when finished. This does not install a service or modify drivers. Do not run the Stage 7 generation script again: Director supplies the workflow.

In a separate PowerShell terminal at the repository root:

```powershell
$env:DIRECTOR_ENABLE_DEV_GENERATION = '1'
$env:DIRECTOR_DEV_COMFY_URL = 'http://127.0.0.1:8188'
$env:DIRECTOR_DEV_GENERATION_OUTPUT = '\\wsl.localhost\Director-GPU-Dev\opt\director-gpu-dev\stage7\data\output'
# Set DIRECTOR_MANAGER_TOKEN using your existing private manager-key procedure.
# It must contain at least 32 characters; never place it in source or a URL.
.\.venv\Scripts\python.exe -m uvicorn director.main:app --host 127.0.0.1 --port 8000
```

The output setting is the Windows view of the exact approved WSL output directory. The backend does not start WSL automatically and does not expose that absolute path in responses. Only a numeric loopback ComfyUI origin is accepted; redirects and environment HTTP proxies are disabled.

In a third PowerShell terminal:

```powershell
cd frontend
$env:VITE_DEV_GENERATION = '1'
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. On Generate, enter your manager key, a prompt and a seed, then click Generate video once. The key stays in browser memory. Both backend and frontend flags are required. Production frontend builds hide this flow even if the frontend flag is set.

## Fixed workflow and API

Only prompt and a nonnegative, JavaScript-safe integer seed are accepted. Unknown request fields are rejected. The native workflow matches Stage 7: Wan 2.1 T2V-1.3B FP16, scaled FP8 UMT5, Wan VAE, 320×192, 17 frames, batch 1, eight steps, CFG 6, shift 8, uni_pc/simple, denoise 1, 16 fps, VP9/WebM. A job-specific output prefix is the only additional substitution. No arbitrary node, model, directory or workflow input is accepted.

| Route | Behavior |
| --- | --- |
| `GET /api/dev/generation/config` | Public enabled/development-only flags; no server address or paths |
| `POST /api/dev/generation/jobs` | Manager-authenticated explicit submission; body `{ "prompt": "Ocean at sunset", "seed": 20261009 }` |
| `GET /api/dev/generation/jobs/{id}` | Manager-authenticated status polling |
| `GET /api/dev/generation/jobs/{id}/output` | Manager-authenticated, bounded WebM response for that completed job only |

Existing Host, Origin and manager-key checks are reused. The Vite proxy preserves their existing trust boundary. The frontend sends the key only to privileged Director routes, never to ComfyUI, and retrieves video bytes before creating a browser-local blob URL. Blob URLs are revoked on replacement/unmount.

## Jobs, output and limitations

Jobs transition queued → running → completed/failed. Running is established from ComfyUI's queue, completion from history plus validated job-associated output. Polling does not provide a trustworthy step percentage, so `progress` is null. Fast jobs may complete before running is observed. Execution failures are summarized safely; exact tracebacks stay in the ComfyUI development logs.

Only one Director generation can be active. A nonempty ComfyUI queue blocks submission. Ambiguous submission failures block further submissions until the operator inspects ComfyUI and restarts Director; there is no automatic submission retry. Tracking times out after 30 minutes without silently interrupting unrelated work. Cancellation is deferred because ComfyUI's global interrupt could affect other clients.

The last generation is remembered only in the API client's memory, permitting Refresh status / preview after navigation. Reloading the frontend loses this reference; restarting the backend loses its bounded 12-job in-memory history. Neither restart resubmits work. Leaving the page stops monitoring, not inference. Polling resumes explicitly via Refresh. There is no generation job-list API or integration with installation job history.

Output filenames must match the exact job prefix, originate in output node 47, have output type, and have an empty subfolder. The backend rejects traversal, links/junctions, nonregular or multiply linked files, changed files, missing/empty files, files above 32 MiB, and missing WebM container signatures. Reads recheck file identity and return bounded bytes rather than serving arbitrary paths. This handoff is not a complete codec validator; actual end-to-end verification decodes the produced video independently.

No Resolve import, image-to-video, custom nodes, presets, production readiness or installer changes are included.

## Verification

From the repository root, ` .\.venv\Scripts\python.exe -m pytest` runs offline backend tests. From `frontend/`, `npm.cmd test`, `npm.cmd run build`, and `npm.cmd run format:check` verify frontend behavior, TypeScript, production build and formatting. Automated tests use mocked ComfyUI and inert output bytes, never real inference. Actual Stage 8 validation is recorded separately in `docs/verification.md`.
