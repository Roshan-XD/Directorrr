# Focused official MiniMax H3 installation review

Reviewed 2026-10-10. **Download/setup is NO-GO on the current laptop.** The Install action now opens a live authenticated review; it is not a working weight installer or an execution adapter. No H3 weights, new runtime dependencies or inference were acquired/executed.

## Why the old button could not install H3

V1.1's candidate used Comfy-Org's converted checkpoints, `adapter: null`, and a deliberately disabled placeholder Install button. Generic repository data transfers cannot register an executable model. Wan's execution adapter is Wan-only. This change recognizes the requested official `MiniMaxAI/MiniMax-H3` repository and replaces the placeholder with an explicit actionable installation review, including on its live discovery card.

## Exact official subset

Immutable revision: `42ed227ee7df40d41602854ae760620d6eb651fe` (reconfirmed against the live official Hub API). Selected workflow: Modular Diffusers `t2va`, text to video **and native stereo audio**. No hosted Context-IR, 2K service, Turbo variant, optional embedding, reference transformer, original duplicate checkpoints or custom nodes.

The [official Diffusers 0.41.0 integration](https://huggingface.co/docs/diffusers/v0.41.0/api/pipelines/minimax_h3) identifies the transformer and seven common components. The pinned modular index and three small shard-index JSON files were inspected, never imported or executed. Encoder tokenizer-related duplicates outside its model/config/index/shards are excluded. Tokenizer/processor folder assets are retained conservatively for their standard loaders; further removing individual tokenizer assets would require loader validation.

| Component | Files | Exact bytes |
|---|---:|---:|
| Transformer (14 shards + config/index) | 16 | 66,280,569,250 |
| Qwen3-VL text encoder (14 shards + config/index) | 16 | 66,715,012,177 |
| Video VAE | 5 | 10,415,635,127 |
| Audio VAE | 2 | 605,431,611 |
| Tokenizer | 4 | 11,492,078 |
| Processor | 7 | 11,498,352 |
| Video scheduler | 1 | 97 |
| Audio scheduler | 1 | 96 |
| Modular index | 1 | 2,935 |
| License | 1 | 17,604 |
| **Total** | **54** | **144,039,659,327** |

Exact filenames, immutable official resolve URLs, byte sizes and published LFS SHA-256 values are in `model_registry/plans/minimax-h3-official-t2va.json`. Weight files have published SHA-256; normal Git files have published Git blob SHA-1, with SHA-256 explicitly unknown. The SHA-256-only installer cannot silently treat those as verified SHA-256 artifacts. `docs/h3-official-metadata.json` contains the bounded source evidence and captured pinned license text/checksum. `scripts/inspect_h3_metadata.py` refreshes metadata explicitly; normal UI review never performs transfers.

These are original official BF16 files, not the earlier 42,030,035,159-byte Comfy-Org converted Turbo set. Downloading original BF16 and quantizing at load still requires original-file storage. The two routes are not interchangeable without explicit review. The earlier converted route remains documented in `docs/minimax-h3-plan.md`; no automatic substitution occurs.

## Current feasibility and disk budget

Read-only Director probes observed 31.421 GiB total RAM, 14.327 GiB available RAM, reliable NVIDIA 15.921 GiB VRAM and 135.631 GiB free D: space. Values change and the endpoint rechecks them. Current measurements are captured in `docs/h3-current-hardware.json`.

The official documentation describes INT8 group-offloaded execution on 12–16 GB GPUs, with video-VAE offload and a 960×544 canvas, but estimates **about 75 decimal GB host RAM**. This is published guidance, not a measured minimum or a Windows execution guarantee. Current 32 GB-class RAM is substantially below that working set. Reducing frames/pixels saves activations but does not remove weight residency. No supported disk-offload/paging recipe has been validated here; increasing Windows paging is not proposed as a fix.

Payload is **134.15 GiB** before runtime dependencies. Current disk would leave roughly 1.48 GiB after one payload copy, without staging/cache/activation reserve. The existing conservative 3×payload + 10 GiB budget is **442,856,396,221 bytes (412.44 GiB)**. This is an installation estimate, not measured peak usage. Final runtime packages need additional space and a reviewed lock. A leaner acquisition/activation strategy cannot solve the current host-RAM limitation by itself.

Proposed future test, only on adequate/validated hardware: 960×544, 124 frames (~5.167 seconds), 24 fps, batch 1, 20 sigma-grid points; synchronized 32 kHz stereo audio preserved. Smaller canvas is documented; execution remains untested. No Wan CFG/negative-prompt controls are applied: the documented H3 weights are guidance-distilled.

## Terms and acknowledgement

The [pinned August 2, 2026 Community License](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/42ed227ee7df40d41602854ae760620d6eb651fe/LICENSE) is a conditional territorial grant, not an unrestricted open-source license. Its private-use restrictions include the territory and Acceptable Use Policy; public outputs require disclosure. Commercial/redistribution obligations and Qwen Apache-2.0 notices are separate. The user's eligibility and acceptance have not been assumed. UI review is expressly not acceptance or transfer authorization.

## Implemented boundary and endpoints

- `GET /api/product/h3/installation-plan`: manager-protected exact subset, current hardware/disk, estimates, license identity, immutable sources, blockers and digest; `can_install=false`, `ready=false`.
- `POST /api/product/h3/installations`: strict explicit-confirmation body and fresh review digest; always refuses unavailable H3 execution support. No acknowledgement enables a transfer or writes acceptance. It cannot call the generic data downloader to masquerade as installation.
- Model Store `Install MiniMax H3`: opens the review with exact inventory and unchecked non-binding review box. Blockers keep transfer disabled. Closing/cancelling a review starts no job.

No partial official H3 installation was found/registered. Previously downloaded repository data, if any, is not execution readiness. Existing cancellation/transfer tests remain offline tiny fixtures; no H3 transfer/Ready/load test has occurred. The new H3 tests exercise strict recipe identity, path/hash validation, size calculations, unknown/insufficient resources, and authenticated refusal even after explicit confirmations.

## Remaining work / next decision

Verification: **537 backend passed**, 4 privilege skips and the existing warning; **101 frontend passed**, TypeScript/production build/Prettier passed. Live protected HTTP and actual browser review passed; verification services were stopped. These verify planning/refusal/UI safety, not an H3 installer or execution test.

The full requested download → automatic setup → load validation → Ready → Use Model flow is **not implemented or claimed ready**. It cannot be safely proposed for the documented official route on this 32 GB laptop. Resolve RAM/disk feasibility first; alternatively request a separate explicit feasibility review of the already documented Comfy-Org quantized route, whose host-memory behavior is unknown rather than assumed adequate. Do not authorize a 144 GB transfer merely to find out.

Once a feasible route is selected: freeze its isolated dependency lock and integrity metadata, implement an owned downloader/registration job using existing storage/SDK/verifier, add the fixed reviewed H3 runtime adapter with audio-preserving output, then seek exact transfer/terms approval. Activation must validate paths/hashes; Ready additionally needs a real component-load test. Additional first/last/reference workflows require separate adapter validation; `transformer_ref` must not be downloaded for this first text-only test. Removal must use exact owned inventory and shared-reference protection, preserving Wan and user media.
