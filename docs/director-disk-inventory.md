# Director disk inventory and proposed cleanup — Stage 12

**Superseded by Stage 13:** the explicitly approved obsolete WSL/experiment roots and disposable caches have now been removed after verified media/evidence preservation. Current exact before/after sizes and ownership decisions are in [cleanup-report.md](cleanup-report.md) and `final-evidence/cleanup-report.json`. The table below is a historical pre-migration snapshot, not the current runtime layout.

Read-only snapshot, 10 October 2026. Sizes below are logical file bytes, rounded to GiB (2^30 bytes); VHDX logical length does not necessarily equal NTFS allocated space. Links/junctions were skipped. No deletion, move, unregister or compaction occurred. Local detailed receipts are `.verification/stage12/windows-inventory.json`, `wsl-inventory.json` and `project-details.json`. A bounded C-drive inspection is not proof that no other Director-related files exist anywhere on C:.

## Windows locations

| Exact location | Approximate size | Ownership | Proposed classification |
| --- | ---: | --- | --- |
| `D:\DIRECTOR-Resolve` | 0.250 GiB total | Director workspace; preserve user contributions | **KEEP** |
| `D:\DIRECTOR-Resolve\.venv` | 0.075 GiB / 80,340,007 bytes | Project backend environment | **KEEP** |
| `D:\DIRECTOR-Resolve\frontend\node_modules` | 0.113 GiB / 120,998,414 bytes | Director dependencies, reproducible from lock | **KEEP** while developing; **SAFE TO DELETE AFTER APPROVAL** if rebuilding later |
| `D:\DIRECTOR-Resolve\frontend\dist` | 0.00028 GiB / 299,611 bytes | Director build | **SAFE TO DELETE AFTER APPROVAL**; rebuildable, not deleted |
| `D:\DIRECTOR-Resolve\.verification` | 0.058 GiB / about 62.37 MB | Director test/experiment receipts, source quarantine, logs, scripts and recovered output | **OPTIONAL ARCHIVE** after audit; do not blanket-delete evidence |
| `D:\DIRECTOR-Resolve\generated_videos` | 221,076 bytes | Verified Stage 9/11 MP4s, Windows WebM copy and receipts | **KEEP**: Resolve references these files |
| `D:\DIRECTOR-Resolve\runtime_profiles` | 1,699,420 bytes | Locked metadata, notices, inventories | **KEEP** |
| `D:\DIRECTOR-Resolve\runtime` | Not present | Proposed native runtime only | **KEEP** when created; no installed runtime exists here |
| `D:\DIRECTOR-Resolve\model_weights`, `runtime_storage`, `outputs` | Not present | No real native model copies/provisioned runtime found here | Nothing to delete |
| `D:\Director-Dev-WSL\Director-GPU-Dev\ext4.vhdx` | About 29.99 GiB / 32,201,768,960-byte later observation | Director reference distro | **KEEP** until native replacement and recovery verification pass; only then eligible for separately approved removal |
| `D:\Director-Dev-WSL\Director-GPU-Dev\shortcut.ico` | 5,430 bytes | Distro launcher support | **KEEP** with distro |
| `D:\Director-GPU-Experiment\run-001` | 1.836 GiB / 1,971,476,687 bytes | Director private Windows experiment | **OPTIONAL ARCHIVE** now; acquisition bytes still useful for native reuse |
| `D:\Director-GPU-Experiment\run-001\quarantine` | Exactly 1,968,154,400 artifact bytes | 11 verified Python/torch/dependency artifacts | **KEEP** for possible native reuse; **SAFE TO DELETE AFTER APPROVAL** after replacement/evidence retention |
| `D:\Director-GPU-Experiment\run-001\notices`, owner, inspection receipt and inventory JSONs | Included in experiment total | Captured Director evidence | **OPTIONAL ARCHIVE**, not disposable licence clearance |

No installed Windows torch/ComfyUI or Windows Wan weight copy was found in these Director locations. The Windows Python ZIP is quarantined, not installed. Tiny mock/test outputs are not real models.

## Inside Director-GPU-Dev

These sizes are **inside the VHDX**; do not add them to its size when estimating total recovery.

| Location | Approximate size | Ownership | Proposed classification |
| --- | ---: | --- | --- |
| `/opt/director-gpu-dev/venv` | 5.232 GiB | Proven Python 3.12.3 / torch 2.12.1+cu130 and ComfyUI dependencies | **KEEP** until Windows proof; do not relocate |
| `/opt/director-gpu-dev/wheels` | 2.735 GiB | Stage 5 Linux artifact cache | **KEEP** reference; **SAFE TO DELETE AFTER APPROVAL** after replacement and provenance retention |
| `/opt/director-gpu-dev/cache` | 0.024 GiB | Director-scoped cache | **SAFE TO DELETE AFTER APPROVAL**, not during replacement |
| `/opt/director-gpu-dev/receipts` | 0.005 GiB | Stage 5 notices/environment receipts | **OPTIONAL ARCHIVE** |
| `/opt/director-gpu-dev/stage6/ComfyUI` | 60,553,036 bytes | Pinned, proven source | **KEEP** |
| `/opt/director-gpu-dev/stage6/wheels` | 225,856,214 bytes | ComfyUI dependency cache | **SAFE TO DELETE AFTER APPROVAL** after replacement |
| `/opt/director-gpu-dev/stage6/quarantine` | 242,688,567 bytes | Source/wheel quarantine | **OPTIONAL ARCHIVE**; **SAFE TO DELETE AFTER APPROVAL** once evidence retained |
| `/opt/director-gpu-dev/stage6/receipts` | 6,697,029 bytes | Source/installation/API evidence | **OPTIONAL ARCHIVE** |
| `/opt/director-gpu-dev/stage7/models` | **9,828,025,775 bytes / 9.153 GiB** | The three verified active Wan artifacts | **KEEP** until verified native copies and end-to-end proof |
| `/opt/director-gpu-dev/stage7/quarantine` | 9,836,307,274 bytes / 9.161 GiB | Duplicate artifact quarantine plus ancillary evidence | **SAFE TO DELETE AFTER APPROVAL** after copy/hash verification and evidence archive |
| `/opt/director-gpu-dev/stage7/data` | 363,864,943 bytes / 0.339 GiB | ComfyUI outputs/input/temp/cache/user data | **KEEP** pending exact-file cleanup inventory; generated clips must not be mistaken for disposable cache |
| `/opt/director-gpu-dev/stage7/receipts` | 195,817 bytes | Wan licences, model checks, inference proof | **OPTIONAL ARCHIVE** |
| `/opt/director-gpu-dev/stage8/receipts`, `stage11/receipts` | 43,626 and 37,977 bytes | Real integration logs/receipts | **OPTIONAL ARCHIVE** |
| `/root/.cache/pip` | 0.018 GiB | Inside disposable distro; ownership of individual entries not established | **DO NOT TOUCH** without exact inventory |
| `/root/.cache/huggingface`, `/root/.cache/torch` | Not present/zero observed | No measured contents | Nothing classified for deletion |

The Linux system Python/base Ubuntu files are inside this distro, not separately owned global Windows components. They were not measured individually; subtracting Director file totals from a live VHDX is not a reliable base-OS measurement.

## C: and shared software

| Location | Size/evidence | Ownership | Classification |
| --- | --- | --- | --- |
| `C:\Program Files\Python311` | Actual backend venv base, pre-existing global Python 3.11 | Shared/pre-existing | **DO NOT TOUCH / SHARED** |
| `C:\Program Files\nodejs` | Actual Node/npm command location | Shared/pre-existing | **DO NOT TOUCH / SHARED** |
| `C:\Program Files\Blackmagic Design\DaVinci Resolve` and `C:\ProgramData\Blackmagic Design\DaVinci Resolve` | Installed Resolve/scripting SDK; not Director runtime copies | Shared/user installation | **DO NOT TOUCH / SHARED** |
| `C:\Users\Roshankanna\AppData\Local\pip\Cache` | 163,366,516 bytes / 0.152 GiB | Shared/uncertain; no exact Director entry ownership established | **DO NOT TOUCH / SHARED** |
| `C:\Users\Roshankanna\AppData\Local\uv\cache` | 574,337,966 bytes / 0.535 GiB | Shared/uncertain | **DO NOT TOUCH / SHARED** |
| `C:\Users\Roshankanna\Downloads\# Director verification history.txt` | 60,771 bytes | Director-related, creator/user ownership uncertain | **KEEP** / user-owned evidence |
| User `.codex` and Windows temporary/tool directories | No top-level Director-named directory found in bounded check; other nested/chat/tool files not attributed | Shared/uncertain | **DO NOT TOUCH / SHARED**; no broad cache deletion |

No Director-specific model/cache folder was observed in the bounded C-drive candidates. This does not assert a whole-drive exhaustive search. NVIDIA driver caches and Windows/WSL components were not declared Director-owned.

## Reclaimable space, only after future approval

**Authorized deletion now: zero bytes.** All references remain required because Stage 12 has not passed.

After native proof and selected evidence preservation, the entire reference VHDX plus obsolete Windows experiment could recover **approximately 31.82 GiB in logical file length** (29.99 + 1.836). Actual NTFS freed allocation may differ. A further approximately 0.17 GiB of project dependency/build/verification data is conditionally rebuildable/archiveable, with receipts/media exceptions; do not sum included child folders twice. Internal Linux quarantine/cache deletion alone does not guarantee host space recovery without separately approved compaction, and that operation is expressly excluded now. Shared C-drive caches are excluded from all reclaimable totals.

**WSL removal decision: NOT SAFE YET.** Retain Director-GPU-Dev until a native runtime proves generation, conversion, authenticated retrieval, Media Pool import, approved placement and preservation of old media. Cleanup requires a separate exact-target approval and ownership/path checks, never a guessed recursive delete.
# Stage 12 Windows candidate inventory update

The new owned `D:\DIRECTOR-Resolve\runtime\windows-dev-001` contains approximately **17,361,022,833 bytes (16.17 GiB)** of logical file content: models 9,828,025,775; installed venv 4,271,105,742; verified wheelhouse 2,677,041,805; private Python 120,885,183; ComfyUI source/generated bytecode 60,596,880; GPU cache 387,929,388; receipts/notices/source ZIP about 14,451,574; temp 912,684; output 73,802. File totals can grow with subsequent runs. Inventory receipt: `runtime/windows-dev-001/receipts/native-disk-inventory.json`. **KEEP** this known-good replacement runtime and generated outputs. Retained wheelhouse/cache may later be **OPTIONAL ARCHIVE** after separate approval; they are not deleted here.

Outside the main project, the preserved prior inventory remains: `D:\Director-Dev-WSL\Director-GPU-Dev\ext4.vhdx` about 29.99 GiB logical file size; `D:\Director-GPU-Experiment\run-001` about 1.836 GiB. Both are **SAFE TO DELETE AFTER APPROVAL** only once the user accepts the replacement and archives desired evidence. Do not sum WSL internal models/caches again with the VHDX. Potential reclaim from these two roots is roughly **31.83 GiB**, subject to fresh physical-allocation measurement. No unregister/delete/compact/move occurred. The Windows final chain no longer needs WSL technically; the reference is retained by instruction.

Existing project `.venv` (~0.075 GiB), frontend node_modules (~0.113 GiB), committed runtime metadata and generated videos are **KEEP**. `.verification` (~0.058 GiB prior snapshot; now includes the 30,721,954-byte Intel wheel and new evidence), old logs/test outputs and old frontend dist are **OPTIONAL ARCHIVE**, not blindly deletable because receipts support the audit. Old generated videos are **KEEP** where Resolve references them. Existing WSL model/quarantine duplicates, Linux environment/source and caches remain inside the preserved VHDX; defer granular decisions until cleanup approval.

Shared C: Python 3.11, Node.js, Resolve, user pip/uv caches and driver caches remain **DO NOT TOUCH / SHARED**. Existing bounded C: inventory includes `Downloads\# Director verification history.txt`; ownership is uncertain/user-owned, **KEEP**. No new Director-owned runtime was intentionally installed on C:. Python/driver/Windows internals can create shared caches despite child TEMP/CUDA cache settings; no ownership or deletion permission is inferred for them. The earlier bounded inventory below is not an exhaustive scan of C:.

