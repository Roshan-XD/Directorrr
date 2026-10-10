# Director — Milestone 2A model research and architecture validation

Initial research date: **8 October 2026**. The 2A findings below are historical; 2B implemented the v2 schema and planner, and the **9 October 2026 Milestone 2C addendum** below supersedes Wan's rounded file-size and missing-pin observations. Milestone 2D implemented the artifact downloader and manager; runtime installation and generation remain unimplemented. The [Milestone 3C readiness review](runtime-readiness.md) reuses this evidence and records remaining licensing and runtime prerequisites.

## Milestone 2C addendum — verified Wan artifact metadata

Checked **9 October 2026** using official Hugging Face file pages, small Git-LFS pointer metadata, pinned tree JSON, and official ComfyUI source/tutorials. No weight bodies were fetched. The three-file selection and destinations are confirmed by the [native example](https://comfyanonymous.github.io/ComfyUI_examples/wan/) and [official tutorial](https://docs.comfy.org/tutorials/video/wan/wan-video).

Actual artifact repository: `Comfy-Org/Wan_2.1_ComfyUI_repackaged`, common pinned snapshot **`123acf1cc74bccbb9bfff8ac1ee72edc08c2341d`**. Source paths below are relative to that repository; destinations remain relative to ComfyUI's model root.

| Source filename | Destination | Exact bytes | Pinned source |
| --- | --- | ---: | --- |
| `split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors` | `diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors` | 2,838,303,560 | [Tree metadata](https://huggingface.co/api/models/Comfy-Org/Wan_2.1_ComfyUI_repackaged/tree/123acf1cc74bccbb9bfff8ac1ee72edc08c2341d/split_files/diffusion_models?expand=true) |
| `split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6,735,906,897 | [Tree metadata](https://huggingface.co/api/models/Comfy-Org/Wan_2.1_ComfyUI_repackaged/tree/123acf1cc74bccbb9bfff8ac1ee72edc08c2341d/split_files/text_encoders?expand=true) |
| `split_files/vae/wan_2.1_vae.safetensors` | `vae/wan_2.1_vae.safetensors` | 253,815,318 | [Tree metadata](https://huggingface.co/api/models/Comfy-Org/Wan_2.1_ComfyUI_repackaged/tree/123acf1cc74bccbb9bfff8ac1ee72edc08c2341d/split_files/vae?expand=true) |

The metadata `size` and `lfs.size` agree, and `lfs.oid` gives the full weight-file SHA-256. [Diffusion file introduction](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/commit/5601df2b72d74886b9df858fcd79c809cce4c4f3) and [encoder/VAE introduction](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/commit/dfcea77bcf258496e20c69cd84e8e8e41909bb3b) independently show the same pointer sizes/hashes. These introduction commits are not confused with the common selected snapshot.

```text
diffusion:    be531024cd9018cb5b48c40cfbb6a6191645b1c792eb8bf4f8c1c6e10f924dc5
text-encoder: c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68
vae:          2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b
```

**Verified expected total:** 9,828,025,775 bytes, **9.828025775 decimal GB / approximately 9.153 GiB**. The earlier 9.834 GB value was a rounded estimate and remains only in historical 2A/2B discussion. The manifest now uses exact expected sizes and null estimates. Published hashes are verified metadata; no local weight integrity check has occurred. Xet hashes and Git pointer blob hashes are not substituted for SHA-256.

Upstream model identity is pinned separately to **`37ec512624d61f7aa208f7ea8140a131f93afc9a`**. Its [license](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/blob/37ec512624d61f7aa208f7ea8140a131f93afc9a/LICENSE.txt) is Apache-2.0; its [card](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/blob/37ec512624d61f7aa208f7ea8140a131f93afc9a/README.md) retains the publisher content-use expectations. The [pinned artifact README](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/blob/123acf1cc74bccbb9bfff8ac1ee72edc08c2341d/README.md) declares Apache-2.0, now recorded on each component. No separate license/NOTICE appears at its pinned root. Complete converted-artifact attribution/provenance remains unknown; this declaration is not treated as a complete legal notice inventory.

Unauthenticated [artifact API metadata](https://huggingface.co/api/models/Comfy-Org/Wan_2.1_ComfyUI_repackaged) and [upstream API metadata](https://huggingface.co/api/models/Wan-AI/Wan2.1-T2V-1.3B) both reported private=false, gated=false, disabled=false. These repositories currently need no authentication/gate for metadata access. Binary transfer was not tested; recheck access at a future installation rather than treating the observation as permanent.

Workflow source is now pinned to **`cb13911e7d83e4f61ca12e29629cab85a6c08856`** in the [official examples repository](https://raw.githubusercontent.com/comfyanonymous/ComfyUI_examples/cb13911e7d83e4f61ca12e29629cab85a6c08856/wan/text_to_video_wan.json). The small JSON confirms the same three loaders, core nodes, preset, WebP output, and disabled WebM node. It gives no minimum runtime version. The tutorial asks for updated ComfyUI; that is insufficient to invent a version constraint or a tested Windows runtime pin. Runtime/PyTorch/CUDA/driver compatibility, hardware minima, full storage overhead, API workflow conversion and video encoding remain unknown.

The unchanged evaluator/planner now calculate an exact download total while still blocking readiness for remaining gaps. Generation stays researched/unverified. See [downloader design](downloader-design.md) for component responsibilities, lifecycle, storage/commit recovery, proposed APIs and the next implementation boundary.

## Decision

Recommend **Wan 2.1 T2V-1.3B**, using the native ComfyUI FP16 workflow and FP8 UMT5 text encoder, for Director's first **text-to-video** demonstration. This is an engineering recommendation, not a tested hardware certification. It offers a small diffusion model, an existing native workflow, and fewer integration dependencies than the CogVideoX wrapper. Wan 2.2 TI2V-5B is the next candidate when adding image-to-video.

Keep the working backend architecture. Improve the manifest's ability to describe exact files, workflow settings, licenses, and evidence before adding real recommendations. Do not put these models in the live v1 registry yet: the current evaluator cannot represent their uncertainty adequately.

No weights were downloaded, no ComfyUI was installed, and no generation or Resolve integration was performed during this phase.

## How to read the evidence

- **Verified metadata**: directly checked in an official model card, license, file listing, or maintainer's workflow/source. This verifies what the source says, not successful execution on our machine.
- **Publisher/maintainer report**: a published memory or performance claim; not measured by Director and not a universal minimum.
- **Estimate**: a calculated total, suggested engineering budget, or prediction. It must not become a hard requirement without validation.
- **Unverified**: information absent from the checked sources or dependent on a future local test.

Only primary sources were used for conclusions: model authors, ComfyUI maintainers, the wrapper authors, and PyTorch. The three candidates have Apache-2.0-labeled weights and publicly available inference code. This does not establish that their complete training datasets or training pipelines are openly reproducible.

Download sizes below use **decimal GB/MB**, as displayed by Hugging Face. Director's existing `_gb` hardware fields use **binary GiB**. Convert bytes explicitly before comparing them. Download size, installed disk space, RAM use, and VRAM use are different quantities. Dependency environments, caches, temporary files, and generated outputs require extra storage.

## Architecture review

Reviewed `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/verification.md`, the two mock manifests, and `backend/director/models/{schemas,registry,compatibility}.py`, plus the app wiring in `main.py`.

The current structure is appropriate:

- Hardware detection is separate from the model registry.
- Compatibility is a pure function, so it can be tested without a GPU or runtime.
- Pydantic validates local JSON metadata and rejects unknown fields.
- Registry errors fail explicitly at startup; loading order and duplicate detection are deterministic.
- FastAPI uses an injectable hardware dependency, with no ComfyUI or Resolve imports.
- Unknown measurements and unreliable CIM VRAM are handled honestly. VRAM is not summed across GPUs.

No architectural rewrite is justified. Startup-only registry loading and a source-checkout deployment are reasonable for this stage. There is no immediate need for a database, plugin framework, background worker, or frontend scaffolding.

The current `compatible` status means only that declared capacity checks passed. It checks total RAM, free space, allowed GPU vendors, and reliable total VRAM. It does not check operating-system/runtime support, drivers, GPU compute capabilities, available VRAM, dependency versions, or workflow readiness. That limitation is documented and acceptable for mocks, but must be addressed before exposing real models as runnable.

## Candidate comparison

The details and sources below define the scope of each number.

| Exact model | Official Hugging Face repository | Tasks for this checkpoint | Approximate selected download | Memory evidence | Integration assessment |
| --- | --- | --- | --- | --- | --- |
| Wan 2.1 T2V-1.3B | [Wan-AI/Wan2.1-T2V-1.3B](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B) | Text-to-video | Native ComfyUI bundle: **9.83 GB**, calculated from three listed files; original repository about **17.6 GB** | Publisher reports **8.19 GB VRAM** with its inference setup; native workflow not benchmarked here | **First demo recommendation**; native workflow, small diffusion component |
| CogVideoX-2B | [zai-org/CogVideoX-2b](https://huggingface.co/zai-org/CogVideoX-2b) | Text-to-video | Official Diffusers weights: **13.77 GB**, calculated; wrapper uses a different text-encoder bundle | Publisher reports **4 GB FP16 / 3.6 GB INT8** with extensive Diffusers optimizations; not a ComfyUI guarantee | Viable alternate; extra custom nodes and workflow adaptation |
| Wan 2.2 TI2V-5B | [Wan-AI/Wan2.2-TI2V-5B](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B) | Text-to-video and image-to-video | Native ComfyUI bundle: **18.15 GB**, calculated; original repository about **34.2 GB** | Official runner documents **at least 24 GB**; ComfyUI reports **8 GB** with native offloading | Useful second integration; one model covers both tasks |

These are three concrete models across two families, deliberately selected for integration practicality rather than newest-release ranking.

## 1. Wan 2.1 T2V-1.3B

### Identity, tasks, and license

**Verified metadata:** the official checkpoint is text-to-video. Wan 2.1's family also has image-to-video models, but that does not make this 1.3B T2V checkpoint an I2V model. The publisher recommends 480p; 720p is described as less stable. It labels the weights Apache-2.0 and its card additionally states content-use expectations concerning unlawful/harmful content, privacy, misinformation, and vulnerable populations. Preserve those statements alongside the actual license rather than describing the model as having no restrictions. [Official model card](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B), [license text](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/blob/main/LICENSE.txt).

Apache-2.0 permits commercial use subject to its terms. Redistribution requires the license and applicable notices; modified files need change notices, and trademark rights are not granted. These are engineering summaries, not an exhaustive legal interpretation. The actual model/component license texts remain authoritative. [Apache-2.0 text in the model repository](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/blob/main/LICENSE.txt).

### Files and download size

**Verified metadata:** the native workflow uses Comfy-Org's repackaging, not a direct whole-repository download of the author's original checkpoint. Model authorship and artifact publisher must be recorded separately. [ComfyUI Wan examples](https://comfyanonymous.github.io/ComfyUI_examples/wan/).

| Required file | ComfyUI destination under `models/` | Listed size | Source |
| --- | --- | --- | --- |
| `wan2.1_t2v_1.3B_fp16.safetensors` | `diffusion_models/` | 2.84 GB | [File metadata](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/blob/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors) |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | 6.74 GB | [Encoder listing](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/tree/main/split_files/text_encoders) |
| `wan_2.1_vae.safetensors` | `vae/` | 254 MB | [VAE listing](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/tree/main/split_files/vae) |

**Calculated estimate:** 2.84 + 6.74 + 0.254 = **9.834 GB**, approximately **9.16 GiB** of selected weights. This excludes software and temporary storage. The original author repository lists roughly **17.6 GB**, including a 5.68 GB diffusion file, 11.4 GB text encoder, and 508 MB VAE. Do not download every variant in the much larger Comfy-Org repository. [Original file listing](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/tree/main).

The upstream UMT5-XXL encoder is labeled Apache-2.0. Preserve the encoder's attribution and verify the exact converted artifact's provenance when pinning downloads. [Google UMT5-XXL](https://huggingface.co/google/umt5-xxl).

### VRAM, offloading, and quantization

**Publisher report:** approximately **8.19 GB VRAM**. Its single-4090 benchmark setup uses diffusion-model offloading and CPU text encoding (`offload_model` and `t5_cpu`). This number is not a measured ComfyUI minimum and must not be copied into a universal `min_vram_gb`. [Official memory/offloading documentation](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B).

**Verified options:** ComfyUI provides FP16, BF16, and FP8 diffusion variants; its examples prefer FP16 and offer FP8 alternatives when memory is limited. The selected bundle already uses an FP8 text encoder. Native ComfyUI manages offloading separately from the original runner's flags. Quantization changes memory and sometimes quality/speed; optional alternatives should be separate execution profiles, not assumed equivalent. [ComfyUI variants](https://comfyanonymous.github.io/ComfyUI_examples/wan/), [ComfyUI memory-management source documentation](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/README.md).

**Engineering target, not a minimum:** start validation on a 12–16 GiB NVIDIA GPU with 32 GiB installed system RAM, at a short 480p preset. Required free RAM, actual peak VRAM, and generation time remain unverified. CPU offloading needs system memory and transfers data across the CPU/GPU connection; it is not CPU-only generation.

### ComfyUI workflow and custom nodes

**Verified source:** [native T2V workflow JSON](https://comfyanonymous.github.io/ComfyUI_examples/wan/text_to_video_wan.json). It uses core loaders, text encoding, sampling, latent-video creation, and VAE decoding. No third-party custom nodes are required for this example. Its inspected preset is **832×480, 33 frames, batch 1, 30 steps**. It saves animated WebP by default and includes a disabled WebM output. This is a UI workflow, not automatically an API submission payload. Its core node names do not imply extra SD3 or Hunyuan model downloads. [Workflow source](https://comfyanonymous.github.io/ComfyUI_examples/wan/text_to_video_wan.json).

**Unverified:** exact minimum ComfyUI release and the chosen Windows encoder/output configuration. MP4 output suitable for later Resolve import needs a separately validated encoding path; the example alone does not prove that requirement is fulfilled.

## 2. CogVideoX-2B

### Identity, tasks, and license

**Verified metadata:** the official repository is now `zai-org/CogVideoX-2b`; the older `THUDM/CogVideoX-2b` URL redirects there. This checkpoint is T2V; do not attribute the separate 5B I2V checkpoint's capabilities or license to it. The 2B transformer and VAE are released under Apache-2.0. The 5B family has a different license. Use the same Apache notice/change obligations described above and retain component licenses separately. [Official model card](https://huggingface.co/zai-org/CogVideoX-2b), [2B license](https://huggingface.co/zai-org/CogVideoX-2b/blob/main/LICENSE).

### Files and download size

The official Diffusers layout includes transformer, text encoder, VAE, tokenizer, scheduler/configuration, and shard index metadata. **Verified listed weight sizes:**

| Component | Listed size | Source |
| --- | --- | --- |
| `transformer/diffusion_pytorch_model.safetensors` | 3.39 GB | [Transformer listing](https://huggingface.co/zai-org/CogVideoX-2b/tree/main/transformer) |
| `text_encoder/model-00001-of-00002.safetensors` + `model-00002-of-00002.safetensors` | 4.99 + 4.53 = 9.52 GB | [Encoder listing](https://huggingface.co/zai-org/CogVideoX-2b/tree/main/text_encoder) |
| `vae/diffusion_pytorch_model.safetensors` | 862 MB | [VAE listing](https://huggingface.co/zai-org/CogVideoX-2b/tree/main/vae) |

**Calculated estimate:** **13.772 GB**, about **12.83 GiB**, plus small supporting files. This is the official Diffusers bundle; the ComfyUI wrapper uses a separately loaded T5 encoder, so its chosen FP8/FP16 bundle total must be calculated independently. Do not download both encoder formats by default. Google T5-v1.1-XXL is Apache-2.0-labeled. [Upstream T5 model](https://huggingface.co/google/t5-v1_1-xxl).

### VRAM, offloading, and quantization

**Publisher reports:** the table gives **18 GB** for SAT FP16, **starting at 4 GB** for optimized Diffusers FP16, and **3.6 GB** for optimized INT8. Tests used NVIDIA A100/H100 and extensive memory optimizations. These are different setups, not guaranteed ComfyUI requirements. Published options include model/sequential CPU offload, VAE slicing/tiling, and TorchAO/Optimum Quanto quantization. Recommended base precision is FP16 for 2B. Its basic example uses 49 frames at 720×480 and 8 fps. [Official model card and caveats](https://huggingface.co/zai-org/CogVideoX-2b).

**Unverified:** peak VRAM/RAM and Windows performance for an exact pinned wrapper workflow. Keep that requirement unknown until measured; do not market it as a universal “4 GB GPU” option. The wrapper also exposes quantization/offload options, but not all Diffusers optimizations transfer unchanged. [Wrapper loader source](https://raw.githubusercontent.com/kijai/ComfyUI-CogVideoXWrapper/main/model_loading.py).

### ComfyUI workflow and dependencies

**Verified source:** [ComfyUI-CogVideoXWrapper](https://github.com/kijai/ComfyUI-CogVideoXWrapper) has example workflows and explicitly supports the 2B model in its loader. It is a third-party wrapper, not the authors' native ComfyUI implementation. Its README documents breaking workflow updates, making version pinning important. [Loader model choices](https://raw.githubusercontent.com/kijai/ComfyUI-CogVideoXWrapper/main/model_loading.py).

For a basic adapted T2V workflow, required pieces are the 2B transformer/VAE and scheduler metadata, a compatible T5 text encoder, the wrapper nodes, and an output path. The inspected [T2V example](https://raw.githubusercontent.com/kijai/ComfyUI-CogVideoXWrapper/main/example_workflows/cogvideox_1_0_5b_T2V_02.json) is configured for **5B**, not 2B: adapting its loader/precision to 2B is a proposal that still needs validation. It uses [VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) for MP4 output. It must not be presented as a tested ready-to-run 2B workflow.

A supplied [2B ControlNet example](https://raw.githubusercontent.com/kijai/ComfyUI-CogVideoXWrapper/main/example_workflows/cogvideox_1_0_2b_controlnet_02.json) does exist, but includes additional ControlNet weights, video loading, and [KJNodes](https://github.com/kijai/ComfyUI-KJNodes). Those are specific to that example, not essential to basic 2B T2V. Do not include them in Director's first bundle.

The wrapper's current [requirements file](https://raw.githubusercontent.com/kijai/ComfyUI-CogVideoXWrapper/main/requirements.txt) lists `huggingface_hub`, `diffusers>=0.33.1`, `accelerate>=0.33.0`, `einops`, `peft`, and `opencv-python`, on top of ComfyUI/PyTorch. This is a live upstream list, not a tested lock. Its automatic-download loaders would need to be controlled by Director's future installation policy. No loader was executed here.

## 3. Wan 2.2 TI2V-5B

### Identity, tasks, and license

**Verified metadata:** this exact **dense 5B** checkpoint supports both T2V and I2V; it is not the larger two-expert A14B model. The card labels weights Apache-2.0 and states the same content-use expectations as Wan 2.1. Retain those statements and applicable component notices. Its documented 720p setting is 1280×704 or portrait equivalent, at 24 fps. [Official model card](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B), [official inference repository](https://github.com/Wan-Video/Wan2.2).

**Verification limit:** direct attempts to open a standalone license file at common `LICENSE`/`LICENSE.txt` paths failed. The card's Apache-2.0 declaration is verified; locating and pinning the exact license text for all artifacts remains a 2B requirement. [Card license section](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B).

### Files and download size

**Verified metadata:** the native 5B workflow uses a Wan **2.2** VAE, not the Wan 2.1 VAE used by the larger A14B workflows. The repackaged files are from `Comfy-Org/Wan_2.2_ComfyUI_Repackaged`. [Official ComfyUI examples](https://comfyanonymous.github.io/ComfyUI_examples/wan22/).

| Required file | ComfyUI destination under `models/` | Listed size | Source |
| --- | --- | --- | --- |
| `wan2.2_ti2v_5B_fp16.safetensors` | `diffusion_models/` | 10.0 GB | [File metadata](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors) |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | 6.74 GB | [Shared encoder listing](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/tree/main/split_files/text_encoders) |
| `wan2.2_vae.safetensors` | `vae/` | 1.41 GB | [VAE metadata](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/vae/wan2.2_vae.safetensors) |

**Calculated estimate:** **18.15 GB**, about **16.90 GiB**, for this selected bundle. The original repository lists about **34.2 GB**, with roughly 20 GB FP32 diffusion shards, an 11.4 GB text encoder, and a 2.82 GB VAE. These formats have different sizes; parameter count alone is not a download budget. [Original listing](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/tree/main).

The native examples link the shared encoder from the Wan 2.1 repackaging. Reuse an existing file only after comparing its pinned checksum, rather than trusting matching filenames. No CLIP vision weights are listed for the 5B native example. [Component instructions](https://comfyanonymous.github.io/ComfyUI_examples/wan22/).

### VRAM, offloading, and quantization

**Publisher report:** the official single-GPU runner documents **at least 24 GB VRAM** with model offload, model dtype conversion, and CPU T5 encoding. It mentions 80 GB for removing those options. [Official runner configuration](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B).

**ComfyUI maintainer report:** its native 5B workflow is described as fitting **8 GB VRAM with native offloading**. This is a distinct workflow/runtime claim. It does not specify a universal system-RAM requirement or certify our laptop. [Native tutorial, 5B section](https://docs.comfy.org/tutorials/video/wan/wan2_2).

**Verified options:** FP16 diffusion plus FP8 text encoding is the native bundle. A community [QuantStack TI2V-5B GGUF conversion](https://huggingface.co/QuantStack/Wan2.2-TI2V-5B-GGUF) exists; the official tutorial links [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) for GGUF loading. Treat that as a separate optional profile requiring a custom node, provenance review, and a local benchmark. It is not necessary for the standard native example. Quantized artifacts do not prove native FP8 compute support on every GPU. [Community options in the tutorial](https://docs.comfy.org/tutorials/video/wan/wan2_2).

**Unverified:** ComfyUI peak RAM/VRAM, throughput, and quality with this laptop at a chosen preset. Do not mark all 16 GB devices incompatible because the original runner says 24 GB, or all 8 GB devices compatible because ComfyUI reports 8 GB.

### Workflows and custom nodes

**Verified source:** native [T2V JSON](https://comfyanonymous.github.io/ComfyUI_examples/wan22/text_to_video_wan22_5B.json) and [I2V JSON](https://comfyanonymous.github.io/ComfyUI_examples/wan22/image_to_video_wan22_5B.json) are available. Both use core nodes; I2V adds an input image to `Wan22ImageToVideoLatent`. The inspected examples use **1280×704, 41 frames, batch 1, 30 steps** and provide WebM output. No third-party custom-node package is required for those examples. They still need a compatible pinned ComfyUI release; do not assume old stable builds contain every node.

## Why Wan 2.1 first, and what remains unknown

The recommendation favors integration simplicity: its diffusion file is much smaller than Wan 2.2's, its native example avoids custom packages, and a short T2V test can establish the generation path before adding image inputs. CogVideoX offers useful low-memory reports, but its wrapper introduces more moving parts. Wan 2.2 is attractive for a later unified T2V/I2V demonstration. These are project tradeoffs, not a measured quality ranking.

Suggested first benchmark: **832×480, 33 frames, batch 1, fixed seed, FP16 diffusion, FP8 UMT5, no prompt-extension model, no optional quantization plugin**. This follows the inspected Wan example's dimensions; success/time/memory are still unknown. Treat 32 GiB system RAM and a 12–16 GiB NVIDIA GPU as validation targets, not proven hard minimums. Leave headroom for Windows and Resolve.

Milestone 1's recorded laptop has an RTX 5080 Laptop GPU with about 15.92 GiB total VRAM and 31.42 GiB usable installed RAM. That makes it a sensible **test candidate**, not a verified supported device. Total VRAM does not establish free VRAM, supported kernels, driver compatibility, or adequate host RAM for offloading. Hardware was not rescanned in 2A. [Local verification record](verification.md).

The software stack must match the GPU architecture. PyTorch introduced Blackwell support through CUDA 12.8 builds in 2.7; its **2.12** release advises CUDA 13.0+ wheels for Blackwell and identifies **580.88** as the Windows driver requirement for that release's path. ComfyUI's current README also recommends newer PyTorch/CUDA builds. These are release-specific facts, not instructions to install anything now. Re-check the selected ComfyUI/PyTorch/driver matrix when pinning the future runtime. An old model card's `torch>=2.4` alone is insufficient. [PyTorch 2.7 release](https://pytorch.org/blog/pytorch-2-7/), [PyTorch 2.12 release](https://pytorch.org/blog/pytorch-2-12-release-blog/), [ComfyUI README](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/README.md).

AMD/Intel detection must remain supported. A first validated **CUDA profile** can target NVIDIA without asserting that the models universally cannot run on other backends. Untested AMD/Intel/CPU paths should say “not validated for this profile”; genuinely unmet profile requirements should be reported separately. CPU offloading is not evidence that a full CPU-only video workflow is practical.

Do not infer a Resolve output format from the workflow preview: WebP and WebM examples are useful for inspection, but later import requires a verified container/codec and Resolve edition/OS combination. MP4 encoding and Resolve import are outside 2A/2B scope.

## Can the existing ModelManifest represent these models?

**Partly.** All three can express their name, id, tasks, `is_mock: false`, intended `comfyui` runtime, license label, and official Hugging Face repository. A basic entry would validate if positive RAM/storage requirements were supplied. That does not mean those entries would be accurate enough for installation or recommendation.

| Current field or behavior | Research finding | Minimal justified improvement |
| --- | --- | --- |
| One `huggingface_repo_id` | Official model and actual ComfyUI artifacts may come from different publishers/repos | Keep it as upstream identity; add a structured `artifacts` list |
| One license string | Component notices and card restrictions need traceable sources | Add `license_info` with license id, source URL, usage notes, and per-artifact license reference |
| Mandatory numeric RAM/VRAM requirements | Real requirements can be unknown or dependent on workflow/offload settings | Permit unknown (`null`) values in v2; attach evidence and profile context |
| One vendor list | Vendor alone does not describe CUDA, operating system, precision, or driver support | Add one concrete `execution_profile` for each deployable manifest variant |
| No workflow/dependency metadata | Native vs custom workflows have different dependencies and formats | Record workflow source/format, required nodes, pinned ComfyUI revision and custom-node packages in that profile |
| `schema_version` accepts only 1; extra fields forbidden | Existing reader would reject proposed additions | Introduce explicit v2 validation while preserving v1 mock loading |
| Compatibility only has capacity checks | Enough VRAM cannot establish readiness | Keep capacity results separate from profile/runtime validation; unverified checks remain unknown |

### Proposed v2 data, not implemented

Use **one manifest per concrete model/workflow/precision variant** initially. This avoids building a complex general variant-selection system. A native FP16 profile and a future GGUF profile should have different registry ids while sharing the upstream identity.

Add only the following structured groups:

1. **`artifacts`**: component role, Hugging Face repo id, immutable revision, relative filename, safe target subdirectory, byte size (nullable until verified), SHA-256 (nullable until verified), precision/format, and license reference. Include required tokenizer/configuration files where the loader needs external files. Do not represent the entire repo as a single “weight”.
2. **`license_info`**: identifier, authoritative text URL, restrictions/notice summary, and verification date. Keep `license` for a simple display label. Include component licenses through artifact references; a string such as `apache-2.0` alone is not a full license record.
3. **`execution_profile`**: task, OS, backend, per-component precision, offloading mode, chosen width/height/frame count/batch, workflow source plus `ui`/`api` format, pinned ComfyUI revision, required core nodes, and pinned custom-node repo revisions (an explicit empty list for native examples). Record software constraints only when verified; never embed arbitrary install commands in manifests.
4. **`evidence`**: source URLs, checked date, `verified_metadata`/`publisher_report`/`estimate`/`locally_measured`/`unverified`, and the scope of each resource claim. A nullable capacity recommendation may have a range or safety budget here; it must not silently become a proven minimum. Memory reports from the official runner and ComfyUI must remain distinguishable.

Retain existing capacity field names initially to avoid unrelated API churn, but document GiB units. For v2, allow missing/unknown minimum RAM and VRAM instead of filling them with invented numbers. The evaluator must return `unknown` for an unknown required capacity. A declared zero should mean “no requirement,” not “we did not research it.” Free-storage planning should sum required artifact bytes and an explicit estimated overhead budget rather than equate weight size with installation size.

Add profile checks for operating system/backend and later for runtime/driver readiness. A capacity pass should say “capacity checks passed; runtime validation pending.” A missing runtime during 2B is expected and must never make a model look ready to generate. Preserve the existing basic status fields where possible; introduce a separate readiness result when its probe exists. No PyTorch import or GPU inference should be added to the backend just to answer metadata requests.

Implement an explicit version-aware loader in 2B, with tests that the existing two v1 mocks still load. Continue rejecting unknown fields, unsupported versions, duplicates, invalid capacities, and invalid paths. Require non-mock v2 entries to have upstream identity, sources, a profile, and their artifact list. Unknown hashes/revisions must block a future install plan until resolved; draft metadata can remain visible as unverified. Do not change the schema during this research phase.

## Proposed Milestone 2B — metadata and compatibility only

The next implementation should make recommendations and a future download plan trustworthy. It should **not yet install ComfyUI, download weights, generate video, or integrate Resolve**.

1. **Introduce v2 manifests and backward-compatible loading.** Add the groups above, support null requirements, and preserve the current mocks/tests. Keep modules in their existing locations. Add validation tests for evidence, component paths, unsupported versions, missing metadata, and precision/profile mismatches.
2. **Pin one Wan 2.1 native profile first.** Check the exact workflow and ComfyUI commit, artifact revisions/sizes/hashes, component licenses, and whether tokenizer data is bundled by that runtime. Add its real manifest as researched/unbenchmarked. Add CogVideoX and Wan 2.2 only when their specific profiles are equally explicit; do not copy family-level task/VRAM claims.
3. **Improve compatibility reporting without claiming execution success.** Compare capacities, chosen OS/backend, evidence quality, and storage overhead. Preserve unknowns. Test that unverified drivers/runtime/RAM cannot produce an unconditional runnable recommendation. AMD/Intel and missing GPU information must continue to work without CUDA imports.
4. **Create a read-only installation-plan representation.** List required files, their publishers, target paths, total bytes, estimated extra storage, and unresolved metadata. Use local metadata and small remote metadata responses only if needed. Do not execute downloads or manifest-supplied code. Show license information in the plan.
5. **Verify regression behavior and documentation.** Run all existing tests plus v2/profile tests. Start the unchanged FastAPI app and check both real endpoints after API/schema changes. Confirm the two mocks remain clearly labeled, invalid manifests still fail explicitly, and real models distinguish researched capacity estimates from runtime readiness.

**2B acceptance criteria:** a validated real-model record and a deterministic read-only file plan; sources and unknowns visible in API results; backward-compatible mock behavior; meaningful passing tests; no weights/runtime/generation installed or executed. Exact API additions should be decided during 2B, not fabricated as existing endpoints here.

After 2B, request a separately scoped runtime/demo milestone: isolate the ComfyUI environment, validate the GPU/driver/PyTorch build, provision the selected artifacts, adapt/export the workflow to API format, and measure one bounded T2V job end to end. Record peak GPU/host memory, timing, output validity, and failure behavior before promoting a profile to locally validated. Resolve and frontend work remain later separate adapters/components.

## Facts still requiring verification

- Exact immutable revisions, byte sizes, checksums, and full license/notice texts for the eventual selected artifact set. The HF file sizes above are rounded live metadata, not hash-verified local files.
- The precise minimum ComfyUI version and required core-node availability for the pinned workflows.
- Compatible Windows/Python/PyTorch/CUDA/driver versions for the RTX 5080 Laptop GPU. The backend's Python 3.11 environment should not become the runtime's environment by accident.
- Free VRAM, usable host RAM while Resolve is open, thermal/power behavior, actual peak memory, and generation time at the selected preset.
- A plain CogVideoX-2B T2V wrapper workflow adapted from the checked examples, including its complete text-encoder artifact source and disk budget.
- Memory/performance results for any quantized alternate or AMD/Intel backend. None were tested here.
- A later MP4 encoding and Resolve import path. Neither WebM/WebP previews nor generic model capabilities verify it.

### Screened alternative: LTX-Video

LTX has attractive native T2V/I2V examples, but its licenses are version-specific. The **0.9.1** weight license limits the permitted purpose to academic/research use. The **0.X open-weights license** linked for newer versions includes use restrictions and requires entities with at least **$10 million annual revenue** to obtain commercial licensing. Therefore it was not counted among the three Apache-licensed candidates. It could be reconsidered as an explicitly restricted open-weight option; do not reuse its code license as its weights license. [0.9.1 license](https://huggingface.co/Lightricks/LTX-Video/blob/main/ltx-video-2b-v0.9.1.license.txt), [0.X license](https://huggingface.co/Lightricks/LTX-Video/blob/main/LTX-Video-Open-Weights-License-0.X.txt), [version/license mapping](https://huggingface.co/Lightricks/LTX-Video).

## Checks performed in 2A

Read the requested local documents and implementation; inspected live official model cards, file metadata, relevant licenses, workflow JSON, wrapper loader/dependency files, and runtime release guidance. A few direct Wan 2.2 license-file URLs failed; that unresolved item is explicitly recorded above. No external model API capability was assumed.

Only this research document was created. No backend, schema, mock manifest, dependency, or architecture implementation was changed.

Reran `.\.venv\Scripts\python.exe -m pytest`: **48 passed, 1 warning in 0.30 seconds**. The warning is the same third-party Starlette TestClient HTTPX deprecation recorded in Milestone 1; it was not suppressed. The command was run outside the sandbox's previously established local-socket restriction. These are regression/unit/API-client tests, not generation benchmarks. No server startup check or hardware rescan was repeated because no API or detection code changed.
