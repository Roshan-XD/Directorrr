# Stage 13 — authorized Director cleanup

Cleanup prerequisites passed: current launcher-selected paths are Windows-only, native `pip check` passed, torch/CUDA reports the RTX 5080, PyAV/libx264 and backend dependencies are present, and all three native Wan file sizes and SHA-256 values match. Dormant historical WSL adapter code remains source only; the launcher explicitly selects native output and conversion.

The exact registered Director-owned `Director-GPU-Dev` distro was terminated and unregistered. Its VHDX was removed, then the empty/owned residual `D:\Director-Dev-WSL` directory was removed. No other distro or global WSL feature was changed. All three unique generated WSL videos were first copied into `generated_videos/retained-wsl` and independently size/hash verified. Captured small Linux receipts/terms remain in `docs/final-evidence/linux-reference`.

The owned `D:\Director-GPU-Experiment` was removed after retaining exact Intel correspondence, applicable license text and compact manifests. Removed project junk includes `.verification`, `.pytest_cache`, obsolete root/receipt logs, the rebuildable frontend `dist` and Vite caches, Python source bytecode caches, the native cached wheelhouse/source ZIP and disposable native cache/temp contents. Required cache/temp parent directories remain. Exact targets and logical bytes are recorded in `final-evidence/deletions.json`.

## Retained resources

Source/backend/scripts, all user-authored project documentation, package locks and runtime/model manifests, `.venv`, frontend source and **node_modules**, Start/Stop launchers, private `runtime/windows-dev-001` Python/venv/ComfyUI/models/data/receipts, all generated videos and compact final evidence remain. Resolve-referenced videos stayed at their original normal Windows paths. No wheel binaries are needed as license evidence; hashes, URLs and captured texts remain.

Outside the project, `C:\Users\Roshankanna\Downloads\# Director verification history.txt` (60,771 bytes) was intentionally retained as user-authored history. No other certain obsolete Director-owned C-drive target was found in the bounded locations inspected. The similarly named `Documents\Ghost of Tsushima DIRECTOR'S CUT` is unrelated user/game data and was not touched. This is not a claim that the entire C drive was exhaustively searched.

Shared/global Python 3.11, Node.js, Resolve, NVIDIA drivers, Windows CUDA components, the Windows WSL feature, shared pip/uv/npm caches, `.codex`, browser/AppData and unrelated user data were untouched. Normal local Director use has no WSL/Linux dependency, but currently still needs shared Python 3.11 for the backend environment and existing Node.js.

## Disk accounting and rehearsal

See `final-evidence/cleanup-report.json` for exact before/after logical sizes, file counts and measured D-drive free-space change. Logical deletion differs from physical reclaim because of allocation, the VHDX changing during preservation, new evidence files and other disk activity. A positive free-space difference is a drive-level observation, not an exact attribution of every allocated byte to Director.

Final rehearsal: **STAGE_13_CLEANUP_PASS**. The launcher now generates a fresh 384-bit ephemeral credential automatically. It is passed only to backend/server-proxy process environments, never to the browser, URL, files or VITE bundle. The browser receives a non-secret session flag; trusted-origin privileged requests are authenticated by the proxy without changing backend key checks. No handoff file exists.

The actual Start wrapper opened Director in Edge without a credential dialog. ComfyUI/backend/frontend health, native RTX 5080 detection, required nodes, automatic authenticated read-only Resolve access, and Generate-page readiness passed. Wrong/missing credentials, hostile Origin and missing origin proof returned 403. Stop wrapper shut down all owned processes, closed ports 8188/8000/5173 and removed current session records/signals. No new generation or timeline mutation occurred. Source/build/test changes after the disk snapshot are excluded from its exact cleanup sizes.

Final checks: **427 backend passed, four privilege skips, one existing warning; 76 frontend passed; TypeScript/build/format passed**. A canary server credential was absent from production artifacts and build stdout. The initial frontend run hit a sandbox temporary-file limitation; permitted offline rerun passed. Focused tests cover automatic generation, matched process credentials, rejection checks, non-secret proxy discovery and cleanup.

Production installation remains disabled and NO-GO. See [teammate setup](teammate-setup.md): private validated local use, reproducible teammate acquisition/setup and binary/model redistribution clearance are separate. Do not distribute a ZIP of the private runtime.

## Exact size snapshot

| Directory | Before logical bytes | After logical bytes |
| --- | ---: | ---: |
| `D:\DIRECTOR-Resolve` | 17,660,848,015 | 14,488,809,114 |
| `D:\Director-Dev-WSL` | 32,214,357,302 | 0 |
| `D:\Director-GPU-Experiment` | 1,971,476,687 | 0 |

Logical bytes deleted: **37,388,955,063**. D-drive free-space increase: **37,363,032,064 bytes** (34.80 GiB). Snapshot excludes subsequent user activity.
