# Milestone 4D — Real runtime artifact and dependency audit

## Milestone 4G bootstrap/source/license follow-up

The [installation-readiness review](runtime-installation-readiness.md) closes the preferred bootstrap metadata with Python's official **full runtime ZIP**, expected SHA-256 `bbf675bb5e763c1efbb09a3a461b259d81598a63c30c4b0d7ea11b9f063df159` and 31,153,407 expected bytes. It supersedes the historical installer/embedded-only method discussion below without changing Python/core pins. Direct full-ZIP extraction is officially documented; real contents and operation remain untested.

The pinned ComfyUI commit maps to Git tree `8696d307caa30c871887b99d8059bcce6ed7bf51`, with 1,248 regular blobs totaling 48,552,928 bytes in complete metadata. Archive length/published SHA-256 remain unknown; the unsigned commit and proposed Git-content comparison are explicit provenance limits. Cached license metadata and focused official texts improve source-license coverage but do not close binary/vendor notices or distribution obligations. Controlled real installation remains **NO-GO**, with no package/archive download, provisioning enablement or executable code change in 4G.

## Milestone 4F follow-up

The [current dependency lock report](runtime-dependency-lock.md#milestone-4f--current-result) closes the torch/vision/Pydantic metadata gaps and independently validates the complete 84-wheel graph. Expected wheel sizes total 2,677,041,805 bytes, with 84 published artifact SHA-256 values. The earlier partial subtotals and dependency gaps below describe historical 4D/4E evidence. Actual binary integrity and execution remain untested.

Controlled real installation remains **BLOCKED**. The private Python/bootstrap/source inventory, software/binary notices, isolated provisioning/rollback implementation, fresh disk checks and explicit authorization are still required. The full-runtime download/installed size is not established by the wheel-only total. Separate Wan licensing and conversion provenance remain unresolved.

## Milestone 4E follow-up

The [Windows dependency lock report](runtime-dependency-lock.md) advances the dated partial inventory below to **84 exact known wheel selections with 84 published hashes**. Target constraints/tags pass, and the known-size subtotal is now 741,453,448 bytes (82 wheels). It remains **INCOMPLETE** because exact selected-wheel metadata is missing for torch/vision and exceeds the metadata ceiling for Pydantic. The original 599,514,961-byte subtotal below remains the historical 4D subset, not the current known subtotal. No complete runtime size or graph is established.

All current known targets have matching wheels; multidict 7.0.0 was excluded by aiohttp's <7 constraint and 6.9.1 selected from official history/metadata. The real candidate remains untested, installation stays blocked, and bootstrap/source-integrity/runtime notice obligations plus separate Wan gates remain unresolved. No installer, wheel, source archive or weight was fetched. See the new report for resolution method, evidence scopes and next-stage no-go conditions.

Audit date: **9 October 2026**. Scope: standard CPython 3.13 on Windows AMD64, the existing torch/cu130 candidate and native Wan 2.1 T2V-1.3B. This is research and documentation only. No installers, wheels, package archives, ComfyUI archive or weights were downloaded. Small official pages, JSON/index metadata and relevant source/license text were read; binary URLs received HEAD requests only. No dependency resolver, package installation, CUDA test or runtime startup ran.

## 1. Executive summary

**Controlled real installation: BLOCKED.** The proposed core versions exist and the exact Windows wheel tags are published. No candidate-version substitution is justified by this audit. Availability is not execution compatibility or a complete installation inventory.

The missing pieces are the full target-specific dependency lock, accessible artifact size/metadata for torch and vision, source/archive integrity inventory, reviewed binary notices/licenses, a proven isolated full-Python provisioning/rollback method, and a real provisioning implementation. The existing JSON remains proposed with an empty artifact list. Its `verified_metadata` label must not be read as a resolved or validated runtime.

Wan licensing/conversion provenance remains a separate blocked gate. A software-only runtime experiment does not require model weights and cannot authorize their download. Structural verification and local GPU execution are also separate gates; neither has validated the real candidate.

Evidence labels used here: **published** means independently read from the official publisher/index; **inferred** means tags/source make a combination plausible; **unknown** means not established; **untested** means no execution or actual artifact-byte verification. A published checksum is an expected checksum, not a locally measured match.

## 2. Candidate runtime verification matrix

| Candidate | Official evidence | Platform / ABI | Result |
| --- | --- | --- | --- |
| CPython 3.13.16 | [Release files and checksums](https://www.python.org/downloads/release/python-31316/) list `python-3.13.16-amd64.exe` and the x64 embedded ZIP | Standard CPython x64; choose `cp313`, not free-threaded `cp313t`, x86 or ARM64 | Published; isolated installer behavior untested |
| torch 2.12.1+cu130 | [Official version pair](https://pytorch.org/get-started/previous-versions/), [CUDA 13.0 torch index](https://download.pytorch.org/whl/cu130/torch/) | `torch-2.12.1+cu130-cp313-cp313-win_amd64.whl` | Published filename/hash; transfer size and selected wheel METADATA unknown; import/GPU untested |
| torchvision 0.27.1+cu130 | Same official pairing, [vision index](https://download.pytorch.org/whl/cu130/torchvision/) | `torchvision-0.27.1+cu130-cp313-cp313-win_amd64.whl` | Published paired version/filename/hash; exact wheel metadata and execution untested |
| ComfyUI v0.39.0 | [Official release](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.39.0), [commit](https://github.com/Comfy-Org/ComfyUI/commit/b0b743566f65daafc423b4fea8a2fbda94b3384a), [package declaration](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/pyproject.toml) | Source commit `b0b743566f65daafc423b4fea8a2fbda94b3384a`; package declares Python >=3.10 | Release/pin verified; source archive bytes and startup untested |
| Native Wan T2V support | [Official tutorial](https://docs.comfy.org/tutorials/video/wan/wan-video), [pinned loader source](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/nodes.py) includes `wan` CLIP loader type | Core workflow; no selected third-party custom nodes | Source support documented; complete graph execution and output encoding untested |

All requested core candidate versions were found; none is marked unavailable. No fallback is proposed. Installation remains blocked for reasons below, rather than silently choosing newer releases. `abi3` Windows wheels below describe stable CPython ABI compatibility; that does not certify their DLL/GPU kernels on this device. Pure `py3-none-any` wheels describe Python/platform tags, not tested application behavior.

Reuse the existing pinned [UI graph](https://raw.githubusercontent.com/comfyanonymous/ComfyUI_examples/cb13911e7d83e4f61ca12e29629cab85a6c08856/wan/text_to_video_wan.json) and [model readiness evidence](runtime-readiness.md): diffusion FP16, UMT5 scaled FP8 and Wan VAE; UNET/CLIP/VAE loaders, text encoding, latent video, sampling, decoding and animated output nodes. No I2V CLIP Vision model, TorchAudio, standalone CUDA toolkit, xformers, FlashAttention or custom node is selected. The recorded 832×480/33-frame/batch-1/30-step example is a UI graph with animated WEBP output and disabled WEBM, not a validated API graph or MP4/Resolve path. Tokenizer assets, every required node, extension imports and encoding behavior must be checked against the exact runtime later; this review does not claim exhaustive startup dependency validation.

## 3. Exact verified artifact sources

### Python and ComfyUI

- Python full x64 installer URL: `https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe`. The release page publishes SHA-256 **`fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b`**, Sigstore, signature and SBOM links; rounded size **28.5 MB**, not an independently established exact byte count.
- Embedded x64 ZIP: `https://www.python.org/ftp/python/3.13.16/python-3.13.16-embed-amd64.zip`. Published SHA-256 **`97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297`**, rounded **10.9 MB**. It is an audited alternative artifact, **not a selected provisioning method**. [Python's Windows documentation](https://docs.python.org/3.13/using/windows.html#the-embeddable-package) explains that the embedded distribution omits pip and does not support normal pip dependency management.
- ComfyUI source origin: `https://github.com/Comfy-Org/ComfyUI.git` at the full commit above. A future commit-addressed archive is `https://github.com/Comfy-Org/ComfyUI/archive/b0b743566f65daafc423b4fea8a2fbda94b3384a.tar.gz`; its exact size and trusted published SHA-256 are **unknown**. Do not mistake a Git commit identifier for an archive's SHA-256. The tarball was not fetched. A reviewed Git object tree or downloaded archive must later be verified and extraction paths bounded.

### Published wheel metadata

The following table records artifact identities, **publisher/index SHA-256 values** and sizes where published. Direct binary links are recorded for a future allowlist; none was fetched. Torch/vision links are those actually returned by the official index, including the `download-r2.pytorch.org` host. HEAD and `.metadata` requests returned HTTP errors; no binary GET fallback was attempted. Thus their exact size and wheel-level dependency metadata remain unknown; an index listing alone does not prove accessible transfer.

| Package / exact version | Exact artifact (binary URL) | Published bytes | Published SHA-256 | Metadata source / declared license |
| --- | --- | --- | --- | --- |
| torch 2.12.1+cu130 | [torch-2.12.1+cu130-cp313-cp313-win_amd64.whl](https://download-r2.pytorch.org/whl/cu130/torch-2.12.1%2Bcu130-cp313-cp313-win_amd64.whl) | unknown | `76dd848312a40d29499614b714a4318841734ff309ad922f2365868395b6b054` | [Official cu130 index](https://download.pytorch.org/whl/cu130/torch/); BSD source, binary notices pending |
| torchvision 0.27.1+cu130 | [torchvision-0.27.1+cu130-cp313-cp313-win_amd64.whl](https://download-r2.pytorch.org/whl/cu130/torchvision-0.27.1%2Bcu130-cp313-cp313-win_amd64.whl) | unknown | `04f6bda2ab9589ad0a63d44fe6e1dc3ff86f379c100a491b6daba9ec9ec72499` | [Official cu130 index](https://download.pytorch.org/whl/cu130/torchvision/); BSD source, binary notices pending |
| comfyui-frontend-package 1.53.10 | [comfyui_frontend_package-1.53.10-py3-none-any.whl](https://files.pythonhosted.org/packages/86/3c/600826dab85bc5bf625d3f7a233bd16960276b52e2d30a2731a4cfd6659f/comfyui_frontend_package-1.53.10-py3-none-any.whl) | 25,297,944 | `57520f050a18c1b33e3a19d37831566e2bb1d496307a30b701b4c3bd9ec87dc1` | [Versioned JSON](https://pypi.org/pypi/comfyui-frontend-package/1.53.10/json); GPL v3 source tag; blank PyPI field |
| comfyui-workflow-templates 0.11.76 | [comfyui_workflow_templates-0.11.76-py3-none-any.whl](https://files.pythonhosted.org/packages/10/dd/9ce51cca6b2ddf1102a442e82d00278109bbdf201be81f7cdaf7a330304e/comfyui_workflow_templates-0.11.76-py3-none-any.whl) | 10,877 | `fcb40359461d290f400dd882fa6d43d725f56907d8289777f10a664f37f4ac05` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates/0.11.76/json); MIT |
| comfyui-embedded-docs 0.5.13 | [comfyui_embedded_docs-0.5.13-py3-none-any.whl](https://files.pythonhosted.org/packages/f1/1a/9de9581595364bc427c1c5d993585370e0f0e45482cbc2248d2e8be632a1/comfyui_embedded_docs-0.5.13-py3-none-any.whl) | 19,872,156 | `10d8be868f3bb64edf0b6238ec2f0967ad2b6d3f5e08c970f95180d1c0c34690` | [Versioned JSON](https://pypi.org/pypi/comfyui-embedded-docs/0.5.13/json); GPL-3.0 |
| comfy-kitchen 0.2.37 | [comfy_kitchen-0.2.37-cp312-abi3-win_amd64.whl](https://files.pythonhosted.org/packages/bf/0a/96c1141180bdc4dce2664cd9316390069c66c6f03e79963a17f252b4b730/comfy_kitchen-0.2.37-cp312-abi3-win_amd64.whl) | 48,759,733 | `31e1b59351d10374b6351f62a9130712e0cb06c90f059c25522ac1f79249fdb8` | [Versioned JSON](https://pypi.org/pypi/comfy-kitchen/0.2.37/json); Apache-2.0 |
| comfy-aimdo 0.5.5 | [comfy_aimdo-0.5.5-cp39-abi3-win_amd64.whl](https://files.pythonhosted.org/packages/ca/c4/83483278fefcb56d76b21c3ceab92e63426ba4a9c49227685d8049524819/comfy_aimdo-0.5.5-cp39-abi3-win_amd64.whl) | 280,848 | `a86906b230d067f7b7390afd7783742777d56df4ad52790c137d8a0236ab8524` | [Versioned JSON](https://pypi.org/pypi/comfy-aimdo/0.5.5/json); GPL v3 source tag; blank PyPI field |
| comfyui-workflow-templates-core 0.3.367 | [comfyui_workflow_templates_core-0.3.367-py3-none-any.whl](https://files.pythonhosted.org/packages/8f/07/22dd7e393a929426e84cecf6e02ff3334d93e236b412838824c897e8dc5a/comfyui_workflow_templates_core-0.3.367-py3-none-any.whl) | 79,878 | `6ba7c25b8da5dcee2491d3f156edf24e59d3dd68edfb649032f689f03fdc5101` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-core/0.3.367/json); MIT |
| comfyui-workflow-templates-json 0.1.102 | [comfyui_workflow_templates_json-0.1.102-py3-none-any.whl](https://files.pythonhosted.org/packages/ee/d4/1e4cf2bf12d4a353dc046683facef7147f22ca2959a3687a7fd5029a1716/comfyui_workflow_templates_json-0.1.102-py3-none-any.whl) | 3,806,387 | `7c1361d148be87d74e51cb51e7f43fdedc3adff0a853f46221781433514034be` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-json/0.1.102/json); MIT |
| comfyui-workflow-templates-media-api 0.3.84 | [comfyui_workflow_templates_media_api-0.3.84-py3-none-any.whl](https://files.pythonhosted.org/packages/35/47/e4c723615b396f75893049af38a4b53bcb0e8944418819bb0e0d72f342e8/comfyui_workflow_templates_media_api-0.3.84-py3-none-any.whl) | 100,148,800 | `c2d6a5999ac39e4f37f47ae231c92557defe5addb2cc6ab5c11410b4d5a2910a` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-media-api/0.3.84/json); MIT |
| comfyui-workflow-templates-media-video 0.3.101 | [comfyui_workflow_templates_media_video-0.3.101-py3-none-any.whl](https://files.pythonhosted.org/packages/e5/9e/49e1fbe9f05df7e4410a8d485af2a2d6fe80b247d44b3bfa7166c54012ef/comfyui_workflow_templates_media_video-0.3.101-py3-none-any.whl) | 104,342,671 | `6270fd61c8c3931b6f0031abac7d4c90ced624de6c7918bff85b89e6c3d7493c` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-media-video/0.3.101/json); MIT |
| comfyui-workflow-templates-media-image 0.3.160 | [comfyui_workflow_templates_media_image-0.3.160-py3-none-any.whl](https://files.pythonhosted.org/packages/bd/2e/aa57dc75cc2a73921d8472a398678e1ac40c011756ad0ab2dfe41eb0ba15/comfyui_workflow_templates_media_image-0.3.160-py3-none-any.whl) | 89,401,690 | `d4a5c5541c7088f6adb1c7da41f5d7c1c14a037eda6a61cd8b4b76c251faaa93` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-media-image/0.3.160/json); MIT |
| comfyui-workflow-templates-media-other 0.3.229 | [comfyui_workflow_templates_media_other-0.3.229-py3-none-any.whl](https://files.pythonhosted.org/packages/a7/46/feed5492a2def46fee71a52fcbb3b7443a048e402c40bedfaaebcc6fa234/comfyui_workflow_templates_media_other-0.3.229-py3-none-any.whl) | 89,097,925 | `ce3d98fa9d84b914c335fe5c9bc903cfefbe1932b1bc3cb6baef7f371b4bd435` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-media-other/0.3.229/json); MIT |
| comfyui-workflow-templates-media-assets-01 0.1.48 | [comfyui_workflow_templates_media_assets_01-0.1.48-py3-none-any.whl](https://files.pythonhosted.org/packages/7c/4c/39858b7dd6036fae44e15baf6eb5e55671291d25b9e0931bc0956ce12055/comfyui_workflow_templates_media_assets_01-0.1.48-py3-none-any.whl) | 94,172,110 | `7733ed12867e95e6b8b39be20bcc73579c28e97e5a44086ffb977cc2c1c78c43` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-media-assets-01/0.1.48/json); MIT |
| comfyui-workflow-templates-media-assets-02 0.1.9 | [comfyui_workflow_templates_media_assets_02-0.1.9-py3-none-any.whl](https://files.pythonhosted.org/packages/1b/c7/a03ea2de6e2e19584c5eb247a9f2c2eb6220eae375335f842089c4a8940c/comfyui_workflow_templates_media_assets_02-0.1.9-py3-none-any.whl) | 24,243,942 | `66cb3fc16eab8410742d6949550df6cfc7124571065d50e1a90128c4913b59ec` | [Versioned JSON](https://pypi.org/pypi/comfyui-workflow-templates-media-assets-02/0.1.9/json); MIT |

For the PyPI rows, the version-specific JSON link provides size, digest, `requires_python`, declared license and dependency metadata. All selected files were non-yanked at the observation time. Index metadata can change; retain a reviewed manifest snapshot and recheck before future consent. Hashes were read independently of Director's candidate JSON, **not calculated from downloaded wheels**.

The kitchen stable-ABI wheel is `cp312-abi3-win_amd64`; aimdo is `cp39-abi3-win_amd64`. Choose these native Windows candidates rather than silently falling back to their separately published pure-Python wheels. Their project Python floors are >=3.10 and >=3.9 respectively. The other PyPI files are `py3-none-any` and require >=3.9. Version availability/ABI plausibility is established; native loading and GPU operation are untested.

## 4. Dependency and lockfile gaps

The exact [ComfyUI requirements at the commit](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/requirements.txt) contain **34 direct requirements**. Seven have selected exact versions: torch/vision are Director's constraints; the other five are upstream exact pins, audited above. The remaining 27 are listed below. `null` means no exact selection/hash/license artifact has been audited, not that the package is optional or absent. Their proposed source is each project's versioned PyPI metadata and `files.pythonhosted.org` wheel, after resolution. For **every row**, CPython 3.13/Windows AMD64 wheel selection, exact bytes and binary notices remain unresolved; the upstream requirement itself is verified. No latest-version guess has been added.

| Package | Upstream constraint | Selected exact version | Expected SHA-256 | Selected artifact license |
| --- | --- | --- | --- | --- |
| torchsde | unpinned | null | null | unknown |
| numpy | >=1.25.0 | null | null | unknown |
| einops | unpinned | null | null | unknown |
| transformers | >=4.50.3 | null | null | unknown |
| tokenizers | >=0.13.3 | null | null | unknown |
| sentencepiece | unpinned | null | null | unknown |
| safetensors | >=0.4.2 | null | null | unknown |
| aiohttp | >=3.11.8 | null | null | unknown |
| yarl | >=1.18.0 | null | null | unknown |
| pyyaml | unpinned | null | null | unknown |
| Pillow | unpinned | null | null | unknown |
| scipy | unpinned | null | null | unknown |
| tqdm | unpinned | null | null | unknown |
| psutil | unpinned | null | null | unknown |
| alembic | unpinned | null | null | unknown |
| SQLAlchemy | >=2.0.0 | null | null | unknown |
| filelock | unpinned | null | null | unknown |
| av | >=17.0.0 | null | null | unknown |
| requests | unpinned | null | null | unknown |
| simpleeval | >=1.0.0 | null | null | unknown |
| blake3 | unpinned | null | null | unknown |
| kornia | >=0.7.1 | null | null | unknown |
| spandrel | unpinned | null | null | unknown |
| pydantic | ~=2.0 | null | null | unknown |
| pydantic-settings | ~=2.0 | null | null | unknown |
| PyOpenGL | >=3.1.8 | null | null | unknown |
| comfy-angle | unpinned | null | null | unknown |

The last six are labelled nonessential upstream, but remain inputs until exact startup imports justify exclusions. Do not optimize the package set by assumption.

One previously missing closure is now explicit: `comfyui-workflow-templates==0.11.76` declares the eight exact subordinate packages shown above **without extra markers**, as well as repeated extra-marked requirements. They are base dependencies; a normal install is not just the small templates meta-wheel. Their version-specific PyPI metadata was independently checked. This is one verified branch, not a complete global dependency lock.

[Torch v2.12.1 source packaging](https://raw.githubusercontent.com/pytorch/pytorch/v2.12.1/setup.py) declares filelock, typing-extensions>=4.10.0, setuptools<82, sympy>=1.13.3, networkx>=2.5.1, jinja2 and fsspec>=0.8.5, and supports build-injected requirements. These are resolution inputs, **not certification of the exact cu130 Windows wheel METADATA**. Their exact versions, target markers, hashes and licenses remain unknown. Do not copy a Linux CUDA dependency list into the Windows profile.

Kitchen metadata declares NVIDIA cuBLAS only behind its `cublas` extra, and pytest/benchmark/ruff/nanobind behind development/build extras. These are not implicitly selected. Transformer/tokenizer, HTTP, scientific, database, multimedia and settings packages have further dependency closures that this audit has not resolved. Bootstrap pip/setuptools/wheel tooling and the applicable Windows VC++ runtime also need exact version/artifact/license decisions; no auto-upgrade or source build is allowed by this report.

An authorized later resolver must target standard Windows x64 CPython 3.13, preserve `torch==2.12.1+cu130` and `torchvision==0.27.1+cu130`, reject source distributions/build hooks, evaluate markers/extras, and produce a complete report including origins, filenames, sizes, SHA-256, licenses and dependency edges. Read-only pip resolution can still fetch wheel bodies when metadata is unavailable; therefore **no pip resolver or dry-run was executed under 4D's no-package-download rule**. No `requirements.lock` exists or is claimed complete.

## 5. Integrity and provenance findings

- Official origins: Python's release server, PyTorch's official wheel index and its listed delivery host, versioned PyPI JSON/files.pythonhosted.org, and Comfy-Org's immutable source commit. These establish publisher-origin evidence, not a guarantee of benign code.
- Published installer hashes/Sigstore/signatures and wheel-index/PyPI digests can be frozen as expected integrity values. Future authorized transfers must compare actual bytes and exact sizes before activation. MD5 is not selected for integrity.
- Unknown archive hashes must remain unknown. A hash computed later from a first download identifies those bytes but is not an independently published checksum. Review archive provenance, signed attestations where present, source tree identity and extraction safety before trusting it.
- Pin distribution filenames and ABI tags, not just package versions. Avoid dependency confusion through mixed-index resolution: bind torch/vision to their approved official artifact URLs; bind each other wheel to its reviewed source. Do not run unpinned custom-node installers, arbitrary setup hooks or source builds.
- Wheel tags and SHA-256 do not verify DLL load behavior, GPU architecture support, embedded-library licenses, security advisories or workflow success. A tag's source license is not proof that a particular wheel was built from that tag; preserve that remaining provenance distinction.
- `runtime_profiles/wan-windows-candidate.json` currently lists partial dependencies and no real artifacts. The planner always rejects non-fixtures, and the fixture's storage calculation is not a real-runtime capacity calculation. This audit changes neither the JSON nor those controls.

## 6. Licensing findings

Runtime software and model weights need separate reviews and acknowledgement boundaries. The following are verified source/metadata declarations; a complete redistributed binary notice inventory is **not** finished.

| Component | Verified declaration/source | Remaining packaging review |
| --- | --- | --- |
| CPython 3.13.16 | [PSF license and incorporated-component licenses](https://docs.python.org/3.13/license.html) | Preserve Python and bundled third-party notices; review release SBOM and installer/runtime components |
| torch 2.12.1 | [BSD-style source license](https://raw.githubusercontent.com/pytorch/pytorch/v2.12.1/LICENSE) | Preserve notices; inventory exact Windows wheel's bundled libraries and their licenses |
| torchvision 0.27.1 | [BSD-3-Clause source license](https://raw.githubusercontent.com/pytorch/vision/v0.27.1/LICENSE) | Preserve notices; inspect selected binary's image/media dependencies |
| ComfyUI v0.39.0 | [GPL v3 at immutable commit](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/LICENSE) | Notices, modifications and corresponding-source obligations for redistribution must be planned |
| Frontend 1.53.10 | [GPL v3 at version tag](https://raw.githubusercontent.com/Comfy-Org/ComfyUI_frontend/v1.53.10/LICENSE); PyPI license field empty | Bind source tag/notice inventory to the actual wheel; blank metadata is not permissionless software |
| Embedded docs 0.5.13 | Versioned PyPI expression GPL-3.0 | Review exact bundled text/notices and content licensing |
| Workflow templates 0.11.76 + eight pinned dependencies | Versioned PyPI metadata declares MIT | Review bundled media/assets/attribution separately; package-level MIT does not establish every asset's provenance |
| Kitchen 0.2.37 | Versioned PyPI metadata declares Apache-2.0 | Preserve license/notices and review bundled native kernels/libraries |
| Aimdo 0.5.5 | [GPL v3 at version tag](https://raw.githubusercontent.com/Comfy-Org/comfy-aimdo/v0.5.5/LICENSE); PyPI license field empty | Bind the wheel to its reviewed source/notices |
| NVIDIA libraries inside selected distributions | [CUDA 13.0 EULA and distribution sections](https://docs.nvidia.com/cuda/archive/13.0.0/eula/index.html) | Identify actual library versions, applicable CUDA/cuDNN/cuBLAS notices and allowed redistribution; open-source torch does not relicense NVIDIA binaries |
| Other direct/transitive packages and VC++ runtime | Exact artifact selection unresolved | No complete license/notice or redistribution finding yet; PyAV/FFmpeg-linked binary components especially need inspection |

Local use and shipping a runtime bundle raise different obligations. Do not infer that a separate process resolves GPL/NVIDIA distribution questions, or that every license requires click-through. Review the intended distribution arrangement against the exact texts and retain relevant notices/source provisions before packaging. Director's future runtime consent/document policy remains unimplemented; no acknowledgement was recorded here.

**Wan blockers reused, not re-researched:** exact upstream checkpoint/revision and conversion history for diffusion/VAE; exact UMT5 source checkpoint/revision and FP8/scaling recipe; applicable authoritative license/NOTICE texts and card usage expectations; bundled workflow rights/notices; reviewed hashed document set and explicit current acknowledgement. The existing empty `license_documents` and `artifact_installation_reviewed=false` keep `license_documents_missing` in force. See [existing detailed gates](runtime-profile.md#exact-licensing-gates-before-a-real-wan-download). Runtime license review is never permission to obtain model weights.

## 7. Hardware and disk considerations

Reuse the dated 4B hardware-endpoint observation: RTX 5080 Laptop, **15.9208984375 GiB total VRAM** from nvidia-smi (not an estimate), **31.420948 GiB total RAM**, approximately **149.197 GiB project-volume free space**. These were not remeasured in 4D and free storage/VRAM can change. Driver 616.92 and driver-reported CUDA 13.4 are prior observations, not proof of wheel CUDA 13.0 execution. Blackwell kernel support, DLL loading, free-memory headroom, offloading and native Wan peak RAM/VRAM remain untested. No GPU compatibility claim is made.

The 13 selected PyPI wheel files above have published compressed sizes totaling **599,514,961 bytes (0.55834 GiB)**. This is a partial metadata-derived subtotal, excluding Python, torch/vision, ComfyUI source and 27 unresolved direct requirements plus their closures. The total exact runtime download and installed sizes are **unknown**; wheel compression does not establish expanded disk occupancy.

Planning estimates, **not measured requirements**:

| Budget | Estimate | Rationale/limit |
| --- | --- | --- |
| Complete runtime download/cache | 5–10 GiB | Provisional allowance for CUDA torch, remaining binaries and media; replace with lock totals |
| One expanded runtime candidate | 10–20 GiB | Includes Python, environment and source; no archive inventory measured |
| Additional staging/temp overhead | 5–10 GiB | Installer/extraction/temp working allowance beyond retained download cache |
| Retained rollback candidate | 10–20 GiB when present | Count separately; fixtures do not measure this |
| Free-space safety margin | max(10 GiB, 20% of the above subtotal) | Proposed conservative policy, not the implemented fixture's 16 MiB reserve |

Thus a first candidate without rollback retention has an estimated **30–50 GiB** additional-space budget; an upgrade with one retained candidate about **40–72 GiB**. Recompute per volume once the lock and expanded inventories exist, and recheck before/while writing. Other processes can consume space; a check is not a reservation. These estimates exclude weights, model staging/cache, outputs and generation temp files. The dated free-space snapshot is not approval to proceed.

## 8. Remaining blockers

1. Complete Windows CPython 3.13 lock and all marker/extras decisions, with verified artifacts for every direct/transitive/bootstrap requirement.
2. Exact torch/vision sizes and selected wheel METADATA; binary inventory and independently reviewed transfer provenance. Their official listing/hash does not resolve the failed metadata requests.
3. Frozen ComfyUI source/archive integrity and safe extraction inventory; relevant source-tag-to-wheel provenance where still uncertain.
4. An isolated full-Python mechanism with tested uninstall/rollback behavior. The official installer can affect registration/launcher/PATH depending on options; embedded Python is not a supported normal pip/venv shortcut. No zero-system-change installer behavior has been validated.
5. Complete runtime license/notice inventory, bundled NVIDIA/multimedia/asset terms and distribution approach; a defined explicit runtime review/consent boundary.
6. Real provisioning/installer security implementation and regression coverage. Current real profiles are always rejected, by design.
7. Fresh target-volume capacity and existing-system-library observations, followed only after separate authorization by bounded execution validation. Wan license/provenance gates remain independently blocked.

## 9. Go/no-go criteria for controlled real installation

**GO for a separately authorized software-only installation experiment** only when blockers 1–6 have a reviewed concrete resolution, fresh disk/system prerequisite checks pass, the plan has exact artifact allowlists/hashes/sizes and explicit consent, staging/final-path environment creation and rollback are implemented/tested, and source/build hooks/unapproved extras/network origins are refused. Stop on missing artifact metadata, resolver conflicts, unsupported tags, license gaps, unknown extraction paths or a requested system modification outside consent.

After installed bytes verify, keep `installed_unvalidated`. A later authorized sequence can check import, CUDA availability, actual architecture, minimal allocation/kernel operation and owned ComfyUI loopback startup/health; each has its own failure reporting and remains distinct from workflow success. No models are needed for those software checks. **GO for Wan weights or generation** additionally requires the separate model-document/provenance/acknowledgement gates and explicit scope. That is not authorized here.

## 10. Proposed next implementation milestone and performed checks

Recommend **Milestone 4E — target dependency resolution and audited lock generation**. Scope it explicitly to metadata-first Windows CPython 3.13 resolution in isolated temporary tooling, approved wheel-origin mapping, a complete machine-readable lock/integrity/license inventory and a report of unresolved conflicts. If the resolver needs wheel bytes because metadata is unavailable, obtain separate scope for package-only fetching; do not silently download them, run setup code, install a runtime or fetch weights. Freeze the Python bootstrap method and exact notice documents alongside the lock. Real provisioning and GPU tests should remain later milestones.

Performed: reviewed the requested local documents/schema/planner and dated hardware/model evidence; independently read official release pages, immutable requirements/package declaration, relevant native loader source, licenses, PyTorch wheel indices, and 13 version-specific PyPI JSON records. Metadata requests were bounded to 2 MiB with timeouts; HEAD/sidecar metadata requests failed for the selected torch/vision delivery links and no binary fallback ran. An ignored local metadata snapshot/research helper was used for transcription; neither is application behavior. No resolver, installer, package/wheel/model download, CUDA operation or ComfyUI startup was performed. Application code, runtime JSON and security controls are unchanged; full tests were not run. The **274 passed / 3 skips / 1 warning** result remains historical 4C verification, not a new test run.
