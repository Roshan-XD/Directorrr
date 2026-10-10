# MiniMax H3 local candidate — no transfer authorization

Reviewed 2026-10-10. This is a metadata-only proposal, not an installation or compatibility claim.

## Local versus hosted

The [pinned publisher model card](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/42ed227ee7df40d41602854ae760620d6eb651fe/README.md) publishes H3-Base local weights with 24 fps, 768-pixel short-side video and 32 kHz stereo audio. Text, first/last image and reference conditioning are published. Context-IR and the full 2K regeneration system are hosted; the base download does not reproduce those systems. This proposal uses no paid endpoint or external prompt transmission.

The [native ComfyUI tutorial](https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native) provides local T2V/I2V/reference workflows. Our existing pinned ComfyUI contains native H3 nodes, so custom nodes are not proposed. Its local T2V template uses the five artifacts below; default prompting does not require optional embedding files. Reference generation needs a different diffusion component and is outside this first set.

## Exact first T2V artifacts

Official Comfy-Org repository revision: `e5eb578a89295337b8ff433a035929ce0279e0b6`. [Frozen source listing](https://huggingface.co/Comfy-Org/MiniMax-H3/tree/e5eb578a89295337b8ff433a035929ce0279e0b6). Exact immutable resolve URLs are in [the machine-readable plan](../model_registry/plans/minimax-h3-download-plan.json). Published LFS digests are integrity expectations, not proof of an already downloaded file.

| Artifact / relative model directory | Exact bytes | Published SHA-256 |
|---|---:|---|
| `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 20,970,379,616 | `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a` |
| `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 | `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` |
| `vae/minimax_h3_video_vae_int8_convrot.safetensors` | 2,811,065,184 | `52a2c8c73583c86e4f41cdcce3a6ad0ea562987bc0bf3d60a0cef5f5c8e60c0e` |
| `vae/minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 | `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48` |
| `loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | 1,956,193,000 | `2339acdf19bfe123f46b971ea35d367a84adb85de43627e1eceafa5a5b2b111e` |

Base four files: **40,073,842,159 bytes**, 37.322 GiB. Turbo set, adding the optional 8-step LoRA: **42,030,035,159 bytes**, 39.144 GiB. No other artifacts are approved or queued.

The [Comfy-Org model card](https://huggingface.co/Comfy-Org/MiniMax-H3/blob/e5eb578a89295337b8ff433a035929ce0279e0b6/README.md) recommends INT8 ConvRot with CUDA 13.0 PyTorch. It declares that the NVFP4/AWQ encoder originates from cybermotaz/Qwen3-VL-32B-Instruct-NVFP4; it does not require a Blackwell GPU. Turbo originates from lightx2v. Those are declared conversion lineages, not independent reproduction evidence. Original text-encoder weights have Apache-2.0 terms; preserve derivative notices and review the exact quantized/Turbo card and terms before transfer. No claim of full third-party redistribution clearance is made.

## License decision

The [pinned MiniMax H3 Community License, August 2, 2026](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/42ed227ee7df40d41602854ae760620d6eb651fe/LICENSE) gives a conditional territorial grant. EU, UK, South Korea and USA are excluded. Private development must satisfy the territory, applicable-law and acceptable-use conditions; the user's location is not assumed. Public outputs need AI disclosure. Training other AI models with these outputs is restricted. Redistribution adds agreement/notice obligations. Commercial UI attribution applies; revenue above USD20 million triggers prior written authorization. This is restricted open-weight licensing, not a blanket OSI open-source or commercial permission. No acknowledgement has been recorded by Director.

The Comfy tutorial's general commercial-license summary is not treated as a substitute for the pinned agreement. Resolve any inconsistent interpretation before commercial distribution. Hosted service terms are separate and not accepted by this local plan.

## Hardware and storage: observations versus estimates

Observed by Director's existing endpoint: RAM **31.421 GiB**, available at the check **13.826 GiB**; NVIDIA VRAM **15.921 GiB**; free D: space about **135.633 GiB**. The current Windows Wan pipeline has execution evidence; H3 does not.

The INT8 diffusion payload alone is 19.530 GiB, exceeding VRAM before activations. Sequential loading and CPU offload are necessary. Encoder and diffusion residency, attention activations, audio and allocator peaks remain unknown. Current free RAM is smaller than the encoder payload. Disk size is not RAM/VRAM usage. No defensible speed or fit promise exists for this laptop. More available RAM or a larger-memory machine may be needed; 64 GiB is a conservative engineering preference, **not a verified publisher minimum**.

The unchanged manager's conservative staging/cache/rollback estimate is **136,827,523,717 bytes (127.431 GiB)** for the Turbo set, including 10 GiB reserve. About 8 GiB disk headroom remains at the observed free-space snapshot. Recheck disk before any authorized acquisition. A separately reviewed direct-activation layout could reduce duplicate disk storage; it is not implemented here.

## Smallest next test and approval boundary

1. Review the exact pinned license/territory and converted encoder/Turbo evidence; approve only this named local set if desired. Do not silently choose other precision or hosted services.
2. Recheck RAM/free disk and define an explicit bounded offload/load test with failure limits. Given current free RAM, downloading is not itself a feasibility decision.
3. Only after separate authorization, transfer/verify the exact files into Director-owned storage. Never execute repository code.
4. Start with native 124 frames / 24 fps (~5.167 seconds), the pinned template and its declared 768 short side. The node describes training around 124-362 frames. Smaller grids/resolutions would be unvalidated experiments, not guaranteed low-memory presets.
5. Validate video **and stereo audio**, decoding/muxing and controlled Resolve conversion before exposing a runnable H3 adapter. Do not change the working Wan default or production gate.

No weights, package installations, custom nodes or H3 execution were performed in this productization pass.
