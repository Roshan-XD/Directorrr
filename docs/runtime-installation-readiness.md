# Runtime installation readiness — Milestones 4G–4J

## Milestone 4K — Experimental scope remains separate

See the [disposable PyTorch GPU experiment plan](experimental-gpu-validation.md) for exact artifact, disk, approval, smoke-test and cleanup scope. No transfers, installations or CUDA execution occurred. Its ten-wheel subset excludes ComfyUI/vision/media dependencies but does not resolve or downgrade any production document blocker. Python/bootstrap and torch/CUDA binary terms still need applicable local-use review before experimental installation/execution. Production remains **NO-GO and disabled**. Approval for the experiment must be explicit and separate; no production runtime readiness is implied.

## Milestone 4J — Notice classification and bounded inspection

Reviewed **9 October 2026**. **Real installation remains NO-GO and disabled.** Reused the complete dependency lock and source inventory. One inert PyOpenGL wheel transfer was explicitly approved by the user after its filename, official URL, size, published hash and purpose were presented. No other artifact transfer was requested or performed. No package was installed, extracted to an environment, imported or executed; no CUDA, ComfyUI or model operations occurred.

### Classification of the original 71 missing identities

The [evidence inventory](../runtime_profiles/licenses/wan-windows-evidence.json) records a unique, versioned classification for every original identity, its exact package metadata sources, applicable authoritative terms, unresolved obligations and captured-document hash where available. The table at the end of this section enumerates all 71. Classification concerns **notice/retention triggers**, not permission to use every byte of a package or a legal clearance for a distribution arrangement.

| Notice scope | Original identities | Meaning |
| --- | ---: | --- |
| Private local only | **0** | No reviewed gap was established to concern only private use. This does not mean there are no local-use blockers. |
| Redistribution-triggered | **13** | Declared BSD/Apache notice clauses are triggered by distribution; package provenance, use/patent/trademark conditions and Director's consent policy remain separate. |
| Both | **22** | Copy-retention conditions such as MIT, ISC and PSF must not be discarded merely because the runtime is private. |
| Uncertain | **36** | Native/vendor components, content rights, ambiguous terms or unchosen license alternatives require more evidence. |

Authoritative bases include [MIT's copy-retention condition](https://opensource.org/license/mit), [BSD distribution and endorsement clauses](https://opensource.org/license/bsd-3-clause), [Apache-2.0 grants and section 4](https://www.apache.org/licenses/LICENSE-2.0.txt), [PSF terms](https://docs.python.org/3.13/license.html), [ISC conditions](https://opensource.org/license/isc-license-txt), and [MPL-2.0 sections 2–3](https://www.mozilla.org/en-US/MPL/2.0/). These are read alongside the already verified exact selected-wheel metadata. Generic license text does not replace package copyright/NOTICE texts or attest included library/content rights. BSD-variant ambiguity and OR alternatives were left uncertain rather than silently selecting terms. AND expressions require review of all applicable terms.

The native/vendor and media identities remain uncertain even where a wrapper declares MIT/BSD/Apache. In particular, [NVIDIA's terms](https://docs.nvidia.com/cuda/archive/13.0.0/eula/index.html) address use as well as distribution; treating their absence as packaging-only would be unjustified. Private execution of GPL-covered code differs from conveying it, but that distinction alone does not clear templates, media, bundled libraries or a combined release. These are engineering evidence assessments with explicit legal uncertainty, not a determination that obligations may be ignored.

### Metadata-first evidence resolved

Small official versioned files added httpcore 1.0.9 LICENSE, Requests 2.34.2 LICENSE and NOTICE, and typing-extensions 4.16.0 LICENSE. Their exact UTF-8 bodies and SHA-256 values are bound into the review. An annotated-types `v0.8.0/LICENSE` request returned 404; its existing metadata declaration was retained and no guessed text substituted. Small Apache reference text and [PyOpenGL version-specific JSON](https://pypi.org/pypi/PyOpenGL/3.1.10/json) were also inspected. No dependency selection or resolution was repeated.

Three original missing full-text identities are now present. Adding the Requests NOTICE and three newly observed binary notices gives **26 captured texts / 94 required identities / 68 missing identities**. Some of the 26 are source-level evidence only; this is not complete binary clearance. The 71-row baseline remains in the evidence so historical gap classifications can be audited.

### Authorized artifact inspection findings

| Field | Verified observation |
| --- | --- |
| Artifact | `pyopengl-3.1.10-py3-none-any.whl` |
| Official source | [Exact PyPI-hosted wheel](https://files.pythonhosted.org/packages/de/e4/1ba6f44e491c4eece978685230dde56b14d51a0365bc1b774ddaa94d14cd/pyopengl-3.1.10-py3-none-any.whl) |
| Transferred bytes | **3,194,996** (3.047 MiB); exact size matches official metadata |
| Published and observed SHA-256 | `794a943daced39300879e4e47bd94525280685f42dbb5a998d336cfff151d74f` |
| ZIP inventory | **2,899 entries**; no extraction or execution |
| Bundled native files | **12 FreeGLUT/GLE DLLs**, with 32/64-bit and VC build variants |
| Exact notices read | `OpenGL/DLLS/freeglut_COPYING.txt`, `gle_COPYING`, `gle_COPYING.src` |
| Top-level source license correspondence | No archive member matching the captured PyOpenGL source-license hash; no root/dist-info LICENSE document detected |

The [committed inspection receipt](../runtime_profiles/licenses/pyopengl-3.1.10.inspection.json) contains the exact artifact identity, declared ZIP inventory, full three notice texts and member SHA-256 values. The authorized wheel remains only in ignored `.verification/4j/` quarantine; no wheel or DLL is committed. Inventory sizes outside the three read notices are ZIP declarations, not DLL analysis or execution tests.

FreeGLUT's copy-retention text is now exact binary evidence. GLE's texts describe alternative terms, including IBM source-code conditions and a GPL alternative; no alternative was accepted or silently selected. The IBM text's source-only scope, actual DLL/source-build correspondence and any documentation licensing remain unresolved. No Togl binary/notice was detected by inventory naming; this is not proof of runtime behavior. The top-level source license remains useful authoritative source evidence, but its absence from the wheel is a notice packaging discrepancy that must be reviewed, not automatically treated as either infringement or permission to ignore it.

The wheel is the smallest **relevant binary artifact** for this question. The officially listed **1,915,580-byte sdist** is smaller but cannot establish which DLLs/notices were actually shipped in the selected wheel. Successful scripted metadata/text payloads totaled **42,550 bytes**, separately recorded from the binary transfer; this is not a measurement of all browser research traffic or HTTP headers. The single artifact is below **10 MiB**, and cumulative artifact transfers are below **20 MiB**. No additional artifacts are authorized. No PyTorch, TorchVision or CUDA binaries were fetched.

### Preflight integration, blockers and exact next step

The backward-compatible review schema adds validated `notice_classifications`. The existing secured runtime-review response exposes them plus `classification_does_not_clear_preflight: true` and `uncertain_notice_ids`. Each entry retains `private_local_clearance: not_cleared` and `preflight_blocker_retained: true`; hashes/versions must match captured documents, duplicate or unrequested identities are rejected. Uncertain classifications prevent review completion even if texts are present and a completion flag is supplied. Classification changes affect the consent digest. No required identity was removed or exemption enabled. All 68 missing texts, incomplete binary/vendor/content coverage and explicit review requirements continue to block acceptance.

Other unchanged blockers include Python/pip bootstrap notices/inventory, NVIDIA/codec/native component terms, GLE scope/alternative choice, media rights, unsigned-source trust acceptance, real installer/rollback validation, fresh disk checks and explicit installation authorization. No model consent or Wan provenance gate is affected. **Notice scope, Director consent, artifact integrity, installation permission and execution validation remain distinct.**

Checks: **65 focused tests passed** before the final additional consent-invalidation and uncertainty-gate cases; the final full suite reports **369 passed, 3 privilege-related skips, 1 existing warning**. Actual loopback HTTP verified the 26-text/68-missing/75-classification response and its 36 uncertain identities, missing-key/untrusted-Origin refusals and blocked consent/provisioning. The backend verification process was stopped. No frontend changes or frontend checks were needed.

Recommend **Milestone 4K — Targeted terms closure and local-validation approval design**. Obtain authoritative small files to close the remaining copy-retention/use terms, resolve GLE scope and license alternative explicitly, and seek publisher binary/build notice manifests for large native artifacts. Specify exact private-local gates separately from packaging duties without deleting either. If a blocked binary inventory needs transfers exceeding this scope, present a new bounded artifact plan for separate authorization. Only after terms, source trust and installer/rollback gates are resolved should a separately authorized isolated installation milestone be proposed. Do not execute tests against the candidate runtime at this stage.

### Original missing-identity inventory

The classifications below are advisory and conditional on the exact declaration/evidence recorded in JSON. A captured source text does not by itself clear actual binary notices. All existing approval blockers are retained.

| Original missing identity | Version | Notice scope | Text now captured |
| --- | --- | --- | --- |
| `binary-vendor-notices` | wan-windows-candidate | uncertain | no |
| `package-aiohappyeyeballs` | 2.7.1 | both | no |
| `package-aiohttp` | 3.14.4 | uncertain | no |
| `package-aiosignal` | 1.4.0 | redistribution | no |
| `package-alembic` | 1.20.0 | both | no |
| `package-annotated-doc` | 0.0.5 | both | no |
| `package-annotated-types` | 0.8.0 | both | no |
| `package-anyio` | 4.15.1 | both | no |
| `package-attrs` | 26.1.0 | both | no |
| `package-blake3` | 1.0.11 | uncertain | no |
| `package-certifi` | 2026.7.22 | uncertain | no |
| `package-charset-normalizer` | 3.5.2 | uncertain | no |
| `package-click` | 8.5.0 | redistribution | no |
| `package-comfy-angle` | 0.1.1 | uncertain | no |
| `package-comfy-kitchen` | 0.2.37 | uncertain | no |
| `package-comfyui-embedded-docs` | 0.5.13 | uncertain | no |
| `package-comfyui-workflow-templates` | 0.11.76 | uncertain | no |
| `package-comfyui-workflow-templates-core` | 0.3.367 | uncertain | no |
| `package-comfyui-workflow-templates-json` | 0.1.102 | uncertain | no |
| `package-comfyui-workflow-templates-media-api` | 0.3.84 | uncertain | no |
| `package-comfyui-workflow-templates-media-assets-01` | 0.1.48 | uncertain | no |
| `package-comfyui-workflow-templates-media-assets-02` | 0.1.9 | uncertain | no |
| `package-comfyui-workflow-templates-media-image` | 0.3.160 | uncertain | no |
| `package-comfyui-workflow-templates-media-other` | 0.3.229 | uncertain | no |
| `package-comfyui-workflow-templates-media-video` | 0.3.101 | uncertain | no |
| `package-einops` | 0.8.2 | both | no |
| `package-filelock` | 4.0.12 | both | no |
| `package-frozenlist` | 1.8.0 | uncertain | no |
| `package-fsspec` | 2026.9.0 | redistribution | no |
| `package-h11` | 0.16.0 | both | no |
| `package-hf-xet` | 1.7.0 | uncertain | no |
| `package-httpcore` | 1.0.9 | redistribution | yes |
| `package-httpx` | 0.28.1 | redistribution | no |
| `package-huggingface-hub` | 1.33.0 | redistribution | no |
| `package-idna` | 3.20 | redistribution | no |
| `package-kornia` | 0.8.3 | redistribution | no |
| `package-mako` | 1.4.3 | both | no |
| `package-markupsafe` | 3.0.4 | uncertain | no |
| `package-mpmath` | 1.3.0 | uncertain | no |
| `package-multidict` | 6.9.1 | uncertain | no |
| `package-networkx` | 3.7 | redistribution | no |
| `package-numpy` | 2.5.3 | uncertain | no |
| `package-packaging` | 26.3 | uncertain | no |
| `package-pillow` | 12.3.0 | uncertain | no |
| `package-propcache` | 0.5.4 | uncertain | no |
| `package-psutil` | 7.2.2 | uncertain | no |
| `package-pydantic` | 2.14.0 | both | no |
| `package-pydantic-core` | 2.50.0 | uncertain | no |
| `package-pydantic-settings` | 2.15.0 | both | no |
| `package-pygments` | 2.21.0 | redistribution | no |
| `package-python-dotenv` | 1.2.4 | redistribution | no |
| `package-pyyaml` | 6.0.3 | uncertain | no |
| `package-regex` | 2026.9.29 | uncertain | no |
| `package-requests` | 2.34.2 | redistribution | yes |
| `package-rich` | 15.0.0 | both | no |
| `package-scipy` | 1.18.1 | uncertain | no |
| `package-sentencepiece` | 0.2.2 | uncertain | no |
| `package-setuptools` | 81.0.0 | uncertain | no |
| `package-shellingham` | 1.5.4 | both | no |
| `package-simpleeval` | 1.0.8 | both | no |
| `package-spandrel` | 0.4.2 | both | no |
| `package-sqlalchemy` | 2.1.4 | uncertain | no |
| `package-sympy` | 1.14.0 | uncertain | no |
| `package-tqdm` | 4.70.1 | both | no |
| `package-trampoline` | 0.1.2 | both | no |
| `package-transformers` | 5.19.0 | redistribution | no |
| `package-typer` | 0.27.3 | both | no |
| `package-typing-extensions` | 4.16.0 | both | yes |
| `package-typing-inspection` | 0.4.4 | both | no |
| `package-urllib3` | 2.8.0 | both | no |
| `package-yarl` | 1.25.1 | uncertain | no |

## Milestone 4I — License documents and source provenance

Reviewed **9 October 2026**. **Decision remains NO-GO.** This milestone captured only bounded official license text and small publishing metadata. No wheels, Python ZIPs, ComfyUI archives, model weights, installers or runtime programs were acquired or executed. The completed 84-package dependency resolution and 1,248-file source inventory were reused unchanged.

### Evidence completed

The versioned [runtime review packet](../runtime_profiles/reviews/wan-windows-candidate.json) now contains **19 full source license/notice documents**, each with applicable version, authoritative URL and SHA-256. The [evidence inventory](../runtime_profiles/licenses/wan-windows-evidence.json) records document identities, exact hashes, byte sizes, attribution/acknowledgement policy and limitations; it also enumerates every locked package and its remaining coverage. Hashes are computed from the exact UTF-8 HTTP bodies without newline normalization. They are **observed document hashes**, not publisher-issued checksums for runtime binaries. JSON escapes preserve the original text while avoiding Windows default-encoding damage.

Recorded texts cover Python 3.13.16; pip 26.2.1; torch 2.12.1 LICENSE and NOTICE; torchvision 0.27.1; pinned ComfyUI; PyOpenGL 3.1.10; PyAV 19.0.1; colorama 0.4.6; comfy-aimdo 0.5.5; frontend 1.53.10; jinja2 3.1.6; kornia-rs 0.2.0; markdown-it-py 4.2.0 and its upstream notice; mdurl 0.1.2; safetensors 0.8.0; tokenizers 0.23.2; and torchsde 0.2.6. Source-release texts for torch/vision do not establish all terms for the selected `+cu130` wheels. Version tags outside the pinned ComfyUI/PyOpenGL commits are mutable upstream references; retained hashes identify the reviewed snapshots rather than attesting their builds.

The former **PyOpenGL exact-release text gap is closed at source level**. [PyPI's 3.1.10 publishing evidence](https://pypi.org/project/PyOpenGL/3.1.10/) binds the exact locked wheel name/hash to publishing commit `bca277036974e5ed9567b90c8176f8c09cd035ec`. Its [license.txt](https://raw.githubusercontent.com/mcfletch/pyopengl/bca277036974e5ed9567b90c8176f8c09cd035ec/license.txt) is captured in full, including OpenGL-ctypes, older PyOpenGL/Pyglet terms and conditional GLE/FreeGLUT/Togl references plus OS-Mesa/Regal notices. PyPI's small provenance statement was checked against the existing locked artifact hash; no wheel was fetched. This is **PyPI-reported publishing evidence**, not independently verified Sigstore cryptography or proof of every notice included in the wheel. Conditional library files still require inspection if present.

ComfyUI's retrieved LICENSE bytes also match the exact size and Git blob identity already frozen in the source inventory. PyTorch's source NOTICE and markdown-it's additional upstream notice have separate required identities: the review now has **90 required identities, 19 present, 71 missing**. Presence of a source text does not mark its binary/vendor notice set complete. No acknowledgement was recorded for the candidate.

### Exact remaining notice gaps

- **Python/bootstrap:** actual full-ZIP notices and incorporated OpenSSL, libffi, Expat, Tcl/Tk and Microsoft runtime component versions/terms. The [Python license documentation](https://docs.python.org/3.13/license.html) supplies source-level context, not an inventory of the selected ZIP. The pinned pip [vendored inventory](https://raw.githubusercontent.com/pypa/pip/26.2.1/src/pip/_vendor/vendor.txt) is captured; bundled wheel identity and all vendored license texts remain unverified.
- **torch/vision:** actual wheel NOTICE/LICENSE correspondence, bundled CUDA/cuDNN/cuBLAS versions and applicable vendor agreements, redistribution lists and multimedia notices. [CUDA 13.0 terms](https://docs.nvidia.com/cuda/archive/13.0.0/eula/index.html) identify use/distribution constraints; they cannot be assumed to govern every unidentified embedded library. No standalone CUDA toolkit is selected.
- **Other native wheels:** PyAV/FFmpeg build configuration and applicable codec licenses; scientific/native/Rust library notices; any MPL covered-file source obligations. Package-level BSD/Apache/MIT declarations do not settle included libraries.
- **ComfyUI packages/content:** exact frontend/docs source-to-wheel correspondence, templates/media attribution and usage rights, and corresponding-source delivery for any packaged release.
- **Remaining documents:** the evidence JSON lists all 71 missing identities, including `binary-vendor-notices` and package license texts not yet captured. Current IDs are a minimum inventory; inert binary inspection may identify additional required documents. Missing hashes remain `null`; no substitute text is generated.

### Source acquisition and provenance result

The [source provenance record](../runtime_profiles/sources/wan-comfyui.provenance.json) freezes a **reviewed, conditional design**, not approval. Future separately authorized acquisition should use the official full-commit [ZIP URL](https://github.com/Comfy-Org/ComfyUI/archive/b0b743566f65daafc423b4fea8a2fbda94b3384a.zip), allowlisted HTTPS redirects to GitHub/codeload and bounded transfers. No archive was requested here. [GitHub's archive documentation](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives) distinguishes commit-pinned content from potentially changing compressed archive bytes.

After a future acquisition, quarantine bytes and record their observed size/SHA-256; do not label a first-download digest as an independently published checksum. The existing local extractor requires an explicitly reviewed archive identity before use. Independently bind the frozen inventory digest, revision and reconstructed Git tree; enforce exact ordinary-file membership, sizes, Git blob identities, optional SHA-256, ownership and archive limits. Reject any extra/missing/changed file or revision. Neither a matching URL nor archive filename is sufficient.

Remaining trust assumptions are the unsigned upstream commit, GitHub/TLS origin and reviewed Git SHA-1 content identities. These establish content consistency, not publisher signatures or code safety. Published archive SHA-256/length remain unknown. No explicit acceptance of that trust policy exists, so **`source_provenance_policy` remains active**. The advisory provenance record cannot bypass the existing verifier or authorize activation.

### Local installation, redistribution and consent

Local use still requires applicable use terms and retained notices, especially where proprietary binary components have separate agreements. Do not infer that an open-source wrapper relicenses vendor binaries. Director's explicit runtime-review acknowledgement is an additional product policy; it is not a claim that every BSD/MIT license legally requires click-through. Source documents alone are insufficient for the selected binary review.

Redistributing a packaged Director runtime requires a separate component-by-component assessment: preserve copyright/licenses/disclaimers; applicable Apache NOTICE and modification notices; GPL corresponding source and installation information where applicable; MPL covered source; vendor redistributable-list restrictions; media attribution/rights; and any binary relinking/source obligations. Private execution of GPL-covered software does not itself impose the same conveying obligations as distributing it. Process separation does not by itself clear a packaged distribution. These findings do not authorize redistribution or any Wan download.

### Preflight integration and next step

Existing services/APIs are unchanged. Runtime review now exposes the 19 checked documents and 71 missing identities, with revised gap warnings; `license_review_complete` stays false. Missing notices still refuse acknowledgement. Changed document bytes, versions or review identities invalidate consent using the existing digest checks. Manager-key and Host/Origin protections are unchanged; `installation_authorized`, provisioning and execution validation remain false. Source integrity, disk checks, real installer/rollback validation and explicit authorization remain separate gates.

Verification: **55 focused tests passed**; full backend **357 passed, 3 privilege-related skips, 1 existing warning**. Nine new offline tests validate recorded evidence, locked PyOpenGL identity, ComfyUI LICENSE blob identity, missing texts, checksum changes, consent invalidation, wrong revisions and real provisioning remaining disabled. No application service or frontend code changed. The earlier Windows encoding issue in test JSON reads was corrected by ASCII escaping the JSON representation, preserving the original UTF-8 document content and hashes.

Recommend **Milestone 4J — Separately scoped inert binary/notice inspection**: first specify exact existing allowlisted artifacts, maximum transfer bytes, hashes, non-executing ZIP/wheel inspection, notice extraction and quarantine/cleanup rules. Seek separate authorization for required artifact transfers; this milestone grants none. Use the resulting inventories to close vendor/media/license gaps, decide the unsigned-source trust policy explicitly, and only then review a later isolated installation plan. No installer, pip, imports, CUDA tests or model downloads belong in that inspection milestone.

## Milestone 4H implementation result

**Decision remains NO-GO for real installation.** Offline source extraction, preflight and version-bound runtime consent are now implemented. The 4G evidence below remains historical; its implementation gaps are superseded only where described here. No software or model downloads, installers, package managers, CUDA tests or ComfyUI execution were performed.

### Source inventory and extraction

`runtime_profiles/sources/wan-comfyui.inventory.json` freezes the previously reviewed official Git tree metadata: commit `b0b743566f65daafc423b4fea8a2fbda94b3384a`, tree `8696d307caa30c871887b99d8059bcce6ed7bf51`, **1,248 regular files / 48,552,928 bytes**. Validation reconstructs the Git tree from file names, modes and blob IDs and compares its identity. This is reused metadata, not newly downloaded source. Per-file SHA-256 values remain unknown; Git blob identities are recorded honestly.

The separate source policy permits legitimate `.github`, `__init__.py` and reviewed names containing spaces, parentheses and ampersands. Model artifact path validation is unchanged. Source verification rejects traversal, absolute paths, drive prefixes, unsafe separators, Windows device names, case collisions, duplicate entries, symlinks and special files. The archive must contain exactly the approved file inventory, with matching sizes and Git blob hashes (and SHA-256 where supplied).

The internal extraction helper accepts only a local archive with an explicitly supplied expected size and SHA-256. It verifies the archive before writing and again through the opened descriptor, extracts exclusively into new Director-owned staging, and verifies every file while streaming. Default limits are 8,192 entries, 64 MiB compressed archive, 64 MiB per file, 128 MiB expanded content and a 200:1 compression ratio. These are extraction caps, not measured real archive size. No extraction endpoint or real activation path is exposed.

Source journals retain verified-staging, failure, cancellation and interrupted states. Recovery is explicit and never resumes extraction automatically. Cleanup requires the matching journal, ownership and exact inventory; added user files or links stop removal. Retained source journals remain a conservative preflight blocker until separately reviewed. Staging verification never means installed or execution-validated.

### Preflight and runtime consent

Preflight independently checks the unchanged COMPLETE 84-wheel lock, profile identity, Python bootstrap identity/hash/size, approved source tree, review packet, storage ownership, current free space, active jobs and existing installation conflicts. It creates no directories and acquires no artifacts. Its result contains blockers, warnings and evidence quality; it always reports real provisioning disabled and installation authorization false.

The conservative current disk gate reserves known compressed artifacts plus a **64 MiB source allowance**, **20 GiB candidate installed size**, **10 GiB extra staging overhead**, **20 GiB rollback reserve**, and a margin of at least **10 GiB or 20%**. This is approximately **63.1 GiB**, deliberately higher than the earlier first-install estimate. Expansion and overhead are estimates; the rollback allowance is retained even for a first installation. Only the configured storage volume is measured. Future installers must also check any separate temporary volume and replace estimates with measured bounds.

`runtime_profiles/reviews/wan-windows-candidate.json` binds the candidate, wheel lock, source inventory and bootstrap identities. It lists **88 required document identities** (84 packages plus Python, pip/bootstrap, ComfyUI source and binary/vendor notices). Its document list is empty and license review is incomplete: no license text or acceptance is fabricated. Runtime consent is separate from Wan consent. Acknowledgement requires literal `true`, complete reviewed documents, versioned identities, document checksums and the current review digest. Changed documents or artifact identities invalidate previous acknowledgements. Records contain no unnecessary personal data and cannot authorize installation.

The following APIs require the existing manager key and trusted Host/Origin even for reads:

- `GET /api/runtime/profiles/{profile_id}/preflight`
- `GET /api/runtime/profiles/{profile_id}/runtime-review`
- `POST /api/runtime/profiles/{profile_id}/runtime-acknowledgements`

The current real review refuses acknowledgement with HTTP 412 because documents are missing. No frontend installation button or real enabling switch was added.

### Rollback evidence and remaining blockers

Tiny fixture tests cover extraction failure, corruption, interruption, cancellation, failed activation and cleanup. Failure both before and after active-pointer publication preserves the old fixture runtime and returns the new fixture to staging. This relocation behavior is fixture-only: it does not establish that Python environments can safely be moved or rolled back.

Real installation remains blocked by incomplete exact license/binary notice documents (including PyOpenGL evidence), unapproved unsigned-source provenance policy, unavailable independent archive SHA-256/size, uninspected bootstrap/wheel contents, unimplemented real installer and offline pip flow, unmeasured installed inventory and rollback requirements, and absent explicit installation authorization. The frozen source inventory closes the inventory gap; it does not approve trust in the unsigned commit. Local archive hashes used by fixtures are not publisher hashes for ComfyUI.

Recommended **Milestone 4I: runtime license-document and source-provenance closure**. Assemble authoritative versioned documents, decide the unsigned Git-content trust policy, and specify separately authorized inert artifact inspection where binary notices cannot be established from metadata. Keep installation, execution and Wan downloads blocked until their separate gates are satisfied.

Reviewed **9 October 2026**. **Decision: NO-GO for real installation.** The software inventory and isolation design have advanced, but source verification implementation, exact binary notices, runtime consent and installer/rollback tests remain material blockers. This document grants no installation authorization.

The approved candidate remains Windows AMD64, standard CPython **3.13.16**, torch **2.12.1+cu130**, torchvision **0.27.1+cu130**, and ComfyUI **v0.39.0** at `b0b743566f65daafc423b4fea8a2fbda94b3384a`. The [84-wheel dependency metadata lock](runtime-dependency-lock.md#milestone-4f--current-result) is COMPLETE and unchanged. Its independence checks do not cover bootstrap software, source archives, notices, actual binary integrity or execution.

Only existing evidence, cached wheel metadata, official documentation/license text, bounded Git commit/tree metadata and artifact **HEAD** headers were inspected. No installer, runtime ZIP, wheel, ComfyUI archive or model weight was fetched. No runtime interpreter, package manager, CUDA or ComfyUI was executed. No executable application/test files changed; tests were not rerun. The **302 passes / 3 skips / 1 warning** backend result remains the historical 4F result.

## 1. Preferred isolated Python bootstrap

Prefer the official **full runtime ZIP**, not the embeddable ZIP or a registered Windows installation. The [Python 3.13.16 release](https://www.python.org/downloads/release/python-31316/) links an official [Windows release manifest](https://www.python.org/ftp/python/3.13.16/windows-3.13.16.json). Its `pythoncore-3.13-64` entry identifies the standard 64-bit runtime:

| Field | Verified metadata |
| --- | --- |
| Filename | `python-3.13.16-amd64.zip` |
| Official URL | `https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.zip` |
| Published SHA-256 | `bbf675bb5e763c1efbb09a3a461b259d81598a63c30c4b0d7ea11b9f063df159` |
| Exact expected compressed size | **31,153,407 bytes**, official HEAD Content-Length, HTTP 200 |
| Runtime identity | PythonCore, standard `3.13-64`; executable `python.exe`; not `3.13t` or PythonEmbed |
| Manifest integrity evidence | Release page publishes manifest SHA-256 `e95d3e68177b2c459f3b6415245dae02357018d9b0c8de85fd0c877996688c09` and a Sigstore link; signature/attestation was not cryptographically verified in 4G |
| Binary verification | **Not performed**; the expected hash is publisher metadata, not a measured ZIP digest |

Official [Windows install-manager guidance](https://docs.python.org/3.14/using/windows.html#offline-installs) explicitly allows extracting full runtime ZIPs without registering an installation, using their executables directly. This is distribution/acquisition guidance, **not a recommendation to change the runtime to Python 3.14 or install the manager**. Director can implement bounded extraction itself; no manager, MSI, registry registration, launcher, PATH change, file association or shortcut is needed.

The version-specific [CPython packaging preset](https://raw.githubusercontent.com/python/cpython/v3.13.16/PC/layout/support/options.py) includes **pip and venv** for the `pymanager` layout. Its [layout source](https://raw.githubusercontent.com/python/cpython/v3.13.16/PC/layout/main.py) includes the standard library, venv launchers and `LICENSE.txt`. This supports the proposed full-ZIP method at source/documentation level; the contents and operation of this exact ZIP still need verification after a separately authorized acquisition. Stop if it lacks the expected full library, `venv`, `ensurepip`, launchers or bundled pip; do not improvise a bootstrap download.

The pinned [ensurepip source](https://raw.githubusercontent.com/python/cpython/v3.13.16/Lib/ensurepip/__init__.py) identifies bundled **pip 26.2.1**, with expected internal wheel `pip-26.2.1-py3-none-any.whl`. [ensurepip](https://docs.python.org/3.13/library/ensurepip.html) uses bundled resources without internet access. This bootstrap is outside the 84 runtime dependency wheels and must appear in a separate bootstrap receipt. Its ZIP-contained bytes, pip/vendor notices and actual version must be checked; no standalone pip hash or exact internal wheel size is invented. Never use `get-pip.py`, `--upgrade-deps`, automatic upgrades or latest package selection.

Use the private base interpreter to create the environment **at its final candidate path**, with copies rather than symlinks and no system site-packages. [venv documentation](https://docs.python.org/3.13/library/venv.html) explains why environments must not be moved. No activation script or execution-policy change is needed: future subprocesses use the exact owned interpreter path. Executing venv/pip is part of a future explicitly authorized installation, not this read-only review.

### Alternatives and safe removal

The previously audited full installer `python-3.13.16-amd64.exe` remains officially available, with published SHA-256 `fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b`; HEAD supplies **29,935,584 bytes**. It is **not selected**. [Installer documentation](https://docs.python.org/3.13/using/windows.html#installing-without-ui) allows a target directory and disabled launcher/PATH options, but does not establish zero registry/maintenance effects or safe coexistence with an existing same-version installation. It therefore remains **BLOCKED as Director's strict-isolation method**. Do not invoke it or its uninstaller against a user installation.

The embeddable distribution remains excluded: [official documentation](https://docs.python.org/3.13/using/windows.html#the-embeddable-package) says it omits pip and normal pip dependency management is unsupported. A small ZIP is not interchangeable with the full ZIP above.

For the selected extracted full ZIP, removal needs no system uninstaller. Future cleanup must stop only Director-owned processes, validate owner/profile/receipt identity and link-free containment, delete only the recorded candidate inventory, and refuse unknown additions. Remove the candidate's venv before its private base interpreter; retain any shared base while another candidate references it. The proposed simplest layout gives each candidate its own base, avoiding sharing. Do not recursively delete a guessed Python directory or alter system/backend Python. This removal flow is designed, not implemented or tested for real Python.

## 2. Pinned ComfyUI source inventory and integrity

| Field | Evidence/status |
| --- | --- |
| Official repository | `https://github.com/Comfy-Org/ComfyUI` |
| Release / immutable commit | v0.39.0 / `b0b743566f65daafc423b4fea8a2fbda94b3384a`; reuse 4D release mapping |
| Proposed archive URL | `https://github.com/Comfy-Org/ComfyUI/archive/b0b743566f65daafc423b4fea8a2fbda94b3384a.zip` |
| Official delivery URL | `https://codeload.github.com/Comfy-Org/ComfyUI/zip/b0b743566f65daafc423b4fea8a2fbda94b3384a` |
| Expected archive filename/root | `ComfyUI-b0b743566f65daafc423b4fea8a2fbda94b3384a.zip` / `ComfyUI-b0b743566f65daafc423b4fea8a2fbda94b3384a/`; filename confirmed by HEAD Content-Disposition; root is expected, not inspected |
| Compressed size | **Unknown**; HEAD HTTP 200 supplies no Content-Length; no binary GET attempted |
| Independently published archive SHA-256 | **Not established**; remains unknown |
| Commit's Git tree identity | `8696d307caa30c871887b99d8059bcce6ed7bf51` |
| Complete recursive tree metadata | **1,248 regular blobs, 48,552,928 source-file bytes**, `truncated=false`; no symlink/submodule modes observed |
| Signature scope | GitHub commit metadata reports `verified=false`, reason `unsigned`; no signed release attestation established |

The tree/count/byte figures come from the official [commit API](https://api.github.com/repos/Comfy-Org/ComfyUI/git/commits/b0b743566f65daafc423b4fea8a2fbda94b3384a) and [recursive tree API](https://api.github.com/repos/Comfy-Org/ComfyUI/git/trees/8696d307caa30c871887b99d8059bcce6ed7bf51?recursive=1). These are source metadata, **not archive size or locally verified files**. The reviewed `.gitattributes` contains only GitHub linguist classifications, no export-ignore, LFS filter or byte-transformation directives; the tree lists no `.gitmodules`. Future acquisition must still compare the exact reviewed tree, not silently update it.

[GitHub documents](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives) that commit-addressed contents are reproducible while archive compression can change. The 64-hex HEAD ETag is **not treated as a published SHA-256**. A Git commit/tree SHA is also not the checksum of a ZIP.

Proposed safe verification without an invented archive checksum:

1. Freeze a reviewed, complete official commit/tree metadata snapshot, its own SHA-256 and expected per-file paths, Git blob IDs, modes and lengths. Independently check the commit-to-tree association; reject truncated responses. This persisted inventory/verifier is **not yet implemented**.
2. During a later authorized transfer, restrict HTTPS origins/redirects to the approved GitHub endpoints; stream to an owned temporary file with size/time limits and disk rechecks. Compute its local SHA-256 for a receipt, labelling it **observed**, not publisher-published.
3. Validate every ZIP member before writing. After removing exactly the expected root prefix, require every ordinary file to match the frozen tree's path and byte length, and recompute the Git blob ID over its raw bytes (`blob <length>` + NUL + content). Permit only expected ancestor directories; reject extra/missing files and duplicate names.
4. Record verified per-file SHA-256 values after the tree comparison for subsequent repair/verification. A second mirror observation may add evidence, but a first-download digest alone is not independent provenance. Git SHA-1 identity and unsigned publisher metadata have a weaker authentication boundary than a publisher-signed SHA-256 attestation; record that limitation explicitly. If policy requires such an attestation, **source acquisition remains BLOCKED** until one exists or the reviewed Git-content approach is explicitly accepted.

Safe extraction must reject absolute/drive/UNC paths, traversal, backslash ambiguities, Windows device names, ADS colons, trailing-dot/space aliases, case-insensitive collisions, links/reparse points/hard links, encrypted members and file/directory conflicts. Enforce member-count, per-file, compressed/uncompressed and actual-streamed-byte limits, including compression-ratio limits; never rely only on claimed central-directory sizes or ZIP CRC. Write only beneath a fresh owned candidate after containment/parent-link checks. Do not run archive scripts, Git hooks, submodule fetches, filters or custom-node installers. These rules need hostile tiny-archive tests before real use.

A metadata-only check found **no case-insensitive collisions** in the 1,248 source paths, but the existing `relative_file_path` manifest validator rejects **240** of them because it requires every segment to begin with a letter/digit. Legitimate examples include `.ci/`, `.github/`, `.gitattributes` and `__init__.py`. Do **not** weaken that existing model/manifest rule, drop required source files or pass arbitrary archive paths through it. A future source/bootstrap inventory adapter needs its own Windows-safe member policy that permits reviewed leading-dot/underscore names, still rejects `.`/`..` and all escape/alias cases, and requires exact frozen inventory membership. Existing containment, ownership and link checks remain mandatory. Full Python also contains such ordinary library names; this is a real provisioning design gap, not an authorization to change code in 4G.

ComfyUI's [pinned LICENSE](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/b0b743566f65daafc423b4fea8a2fbda94b3384a/LICENSE) is GPL v3. Preserve it and copyright headers. The metadata tree contains a root LICENSE and no separately named NOTICE; that does not certify that all embedded third-party notices or assets have been reviewed. A local source copy and a shipped runtime bundle have different distribution obligations.

## 3. Runtime license and notice review

This is an engineering evidence inventory, not clearance to redistribute a combined Director/runtime bundle. **Runtime license/notice closure remains BLOCKED.** Review local acquisition/use terms before download; if an upstream provides needed texts only inside binaries, obtain a separately approved inert artifact-inspection scope before installing them. Redistribution review must additionally cover actual bundled libraries/assets and corresponding-source delivery. Do not treat an absence of metadata as absence of copyright.

| Component | Verified license evidence | Remaining obligation/evidence |
| --- | --- | --- |
| Python 3.13.16 | [Versioned PSF/history license](https://raw.githubusercontent.com/python/cpython/v3.13.16/LICENSE), [third-party license documentation](https://docs.python.org/3.13/license.html) | Preserve full license/copyright text; applicable historical licenses and modification notices. Inspect actual ZIP LICENSE, bundled OpenSSL/libffi/Expat/Tcl/Tk and Microsoft runtime notices; source-level review does not inventory the selected binary. |
| Bundled pip 26.2.1 | [MIT license](https://raw.githubusercontent.com/pypa/pip/26.2.1/LICENSE.txt), [vendored inventory](https://raw.githubusercontent.com/pypa/pip/26.2.1/src/pip/_vendor/vendor.txt) | Include bootstrap and vendored licenses, e.g. vendored setuptools/certifi. Vendored versions are private contents, not substitutions for the approved 84-package environment. Check actual bundled bytes/notices. |
| torch 2.12.1+cu130 | Exact cached CUDA sidecar declares BSD-3-Clause and `LICENSE`/`NOTICE`; [release source license](https://raw.githubusercontent.com/pytorch/pytorch/v2.12.1/LICENSE) | Retain full copyright/conditions/disclaimer and third-party notices. Source tag alone does not establish provenance or terms for every binary library. |
| torchvision 0.27.1+cu130 | Exact cached sidecar declares BSD and LICENSE; [release source license](https://raw.githubusercontent.com/pytorch/vision/v0.27.1/LICENSE) is BSD-3-Clause | Preserve copyright/conditions/disclaimer; inspect bundled codecs and libraries independently. |
| ComfyUI, frontend 1.53.10, embedded docs 0.5.13, aimdo 0.5.5 | Pinned ComfyUI GPL v3 above; [frontend tag](https://raw.githubusercontent.com/Comfy-Org/ComfyUI_frontend/v1.53.10/LICENSE), [aimdo tag](https://raw.githubusercontent.com/Comfy-Org/comfy-aimdo/v0.5.5/LICENSE); docs lock declares GPL-3.0 | For conveying covered binaries, plan license/notices, corresponding source and installation information where applicable. Do not assume process separation or a plugin label eliminates GPL obligations. Exact binary/source correspondence and bundled frontend/docs asset rights remain to review. |
| NVIDIA binaries carried by CUDA wheels | [CUDA 13.0 EULA/distribution provisions](https://docs.nvidia.com/cuda/archive/13.0.0/eula/index.html) | Identify actual CUDA/cuDNN/cuBLAS and other library versions and their applicable agreements/redist lists. Preserve notices and required terms; torch's BSD license does not relicense NVIDIA libraries. No standalone CUDA toolkit is selected. |
| PyAV 19.0.1 and linked multimedia libraries | Lock and [release source](https://raw.githubusercontent.com/PyAV-Org/PyAV/v19.0.1/LICENSE.txt) declare BSD-3-Clause for PyAV | Exact FFmpeg/library build options and LGPL/GPL/other obligations require binary/build provenance and notices. PyAV's license does not cover every codec or establish an external FFmpeg-install requirement. |
| Other locked dependencies | Existing version-specific metadata and sidecar evidence reused below | Review full license files, notices, native/vendor libraries, template/media assets and any MPL source obligations; declaration coverage is not binary-notice coverage. |

All **84** cached selected-wheel sidecars were inspected without refetching packages, and their observed hashes matched the recorded evidence. **73/84** contain a nonempty License or License-Expression header; **65/84** identify License-File paths. A License-File header only names a file; its text was not obtained from a wheel. The lock's declarations are blank/null for 13 packages; exact torch/vision sidecars close two declaration gaps. The other 11 are listed below, with focused official source-text review rather than renewed dependency resolution.

| Package/version with absent sidecar declaration | Authoritative version-specific source evidence | Finding / limitation |
| --- | --- | --- |
| colorama 0.4.6 | [LICENSE.txt](https://raw.githubusercontent.com/tartley/colorama/0.4.6/LICENSE.txt) | BSD-3-Clause text; actual wheel notice binding remains unverified |
| comfy-aimdo 0.5.5 | GPL v3 source above | Source declaration known; native binary notices pending |
| comfyui-frontend-package 1.53.10 | GPL v3 source above | Source declaration known; wheel/asset provenance pending |
| jinja2 3.1.6 | [LICENSE.txt](https://raw.githubusercontent.com/pallets/jinja/3.1.6/LICENSE.txt) | BSD-3-Clause text; retain attribution/disclaimer |
| kornia-rs 0.2.0 | [LICENSE](https://raw.githubusercontent.com/kornia/kornia-rs/v0.2.0/LICENSE) | Apache-2.0; native/library notice inventory pending |
| markdown-it-py 4.2.0 | [LICENSE](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v4.2.0/LICENSE), [upstream notice](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v4.2.0/LICENSE.markdown-it) | MIT; preserve both notice texts |
| mdurl 0.1.2 | [LICENSE](https://raw.githubusercontent.com/executablebooks/mdurl/0.1.2/LICENSE) | MIT with additional Joyent/Node attribution |
| pyopengl 3.1.10 | No exact-version authoritative license text established in this review | **BLOCKED**: sidecar has neither a declaration nor License-File header. A guessed release-tag text returned 404; no license was inferred from another version. Resolve the exact release's authoritative text and included libraries. |
| safetensors 0.8.0 | [LICENSE](https://raw.githubusercontent.com/huggingface/safetensors/v0.8.0/LICENSE) | Apache-2.0; source-text evidence, not exact binary notice clearance |
| tokenizers 0.23.2 | [LICENSE](https://raw.githubusercontent.com/huggingface/tokenizers/v0.23.2/LICENSE) | Apache-2.0; Rust/vendor inventory pending |
| torchsde 0.2.6 | [LICENSE](https://raw.githubusercontent.com/google-research/torchsde/v0.2.6/LICENSE) | Apache-2.0; exact wheel notice binding pending |

These source tags are version-specific upstream references, not immutable signed attestations binding a wheel to its sources. This documentation does not rewrite license fields or pins in the lock.

For the other 71 existing nonempty lock declarations, retain each package's full terms, not merely an SPDX label. BSD/MIT/ISC/PSF families generally require preserved notices; Apache-2.0 adds applicable NOTICE/patent/modification provisions. certifi and parts of tqdm declare MPL-2.0: assess covered-file source availability and notice requirements under the [authoritative MPL](https://www.mozilla.org/en-US/MPL/2.0/). Preserve both clauses of AND expressions; choose and document an applicable OR alternative rather than silently discarding terms. NumPy/SciPy/Pillow and other native wheels have layered library licenses; templates/media require content provenance beyond their package-level declaration. No complete redistribution notice bundle has been produced.

Before a packaged Director release, decide whether software is user-acquired or redistributed, how covered source/changes and licenses are provided, which NVIDIA binaries may be redistributed, and whether the planned linked/bundled components can satisfy all terms together. Keep the runtime separate architecturally, without asserting that separation settles licensing. Review exact distribution arrangements before shipping a proprietary bundle.

Future runtime review documents must bind authoritative text, version, UTF-8 digest and component references to the runtime/profile/lock digest. Require explicit installation confirmation and any necessary acceptance under a defined runtime policy; never preaccept, record consent from this audit or assume every open-source license mandates a checkbox. Existing model acknowledgements cannot substitute for runtime consent. **Wan remains independently blocked** by its reviewed license-document set, checkpoint/conversion provenance, UMT5 scaling lineage and workflow redistribution review; runtime review never authorizes weights.

## 4. Isolated layout, installation and rollback design

Reuse `.director-runtime` ownership, OS root locking, containment/link checks, ArtifactVerifier, durable jobs and atomic pointer records. Existing tests cover fixture interruption, corruption, junction escapes, deletion refusal for user additions and real-profile rejection. They do **not** validate real extraction, venv/pip execution, full inventories or rollback after real interpreter failures. `RuntimeStorageManager.active()` explicitly accepts only fixture receipts; its activation currently renames fixture staging. Neither behavior may be silently reused for a real venv.

Proposed future layout beneath a dedicated configured local storage root:

```text
<root>/.director-runtime/
  owner.json
  staging/<job-id>/                 # downloads, temporary files, source inspection
  installed/<profile-id>/<job-id>/  # unpublished candidate at its FINAL path
    python/                         # private full ZIP contents
    env/                            # fixed-path venv
    ComfyUI/                        # verified source tree
    receipt.json
  installations/<profile-id>.json  # atomic active pointer
  jobs/ journals/ logs/            # owned records; redacted failure logs
```

No directory is created by this milestone. A directory under `installed/` is **not active** unless a verified receipt is published; partial candidates remain quarantined. Runtime outputs, model files and mutable caches should stay in separately owned data locations so user-created data never enters a runtime deletion allowlist.

Minimal future sequence:

1. **Explicit approval:** show a software-only artifact plan, exact hashes/versions, download bytes and source-size uncertainty/cap, destination, disk estimate, runtime documents and failure/rollback policy. Bind approval to plan/document digests. Never interpret this report or a complete lock as approval.
2. **Preflight:** rerun the offline lock checker, inspect software/library prerequisites read-only and freshly check capacity on every target/temp volume. Reject missing license/source-verification policy, unsafe roots or concurrent provisioning. Do not install/repair drivers or system runtimes automatically.
3. **Owned staging/candidate:** acquire the existing root lock; create fresh owned staging and an unpublished final-path candidate. Validate all ancestors against traversal/reparse escapes and backend/system/external ComfyUI roots. Keep prior pointer/candidate intact.
4. **Acquire allowlisted artifacts:** bounded transfer of the exact full Python ZIP, pinned source ZIP and the 84 approved wheel filenames only, with progress, timeouts, cancellation and disk rechecks. No indexes/resolution, source builds, custom nodes, extra packages or models. Bootstrap pip is ZIP-contained; do not fetch a replacement.
5. **Verify before use:** exact sizes/SHA-256 for Python and wheels; reviewed Git-tree verification for source under the approved policy. Safely extract; verify Python bootstrap module/notice inventory and expected pip identity before executing its interpreter. Stop on any unexpected metadata, member, byte or term.
6. **Create private venv and install only approved wheels:** invoke owned, verified interpreter paths with fixed argument lists and bounded/redacted logs. No shell or manifest commands. Use a fresh venv with copied executables, no system packages, no unpinned upgrades, and no activation script. Render a reviewed hash-pinned requirements file from the lock. Run pip offline with `--no-index`, an exact owned wheelhouse, `--require-hashes`, `--only-binary=:all:`, `--no-deps`, no shared cache/version checks and controlled temp/config/environment. All 84 packages are explicit; independent closure validation justifies disabling dependency selection. Reject unexpected effective config/network activity. [pip secure-install guidance](https://pip.pypa.io/en/stable/topics/secure-installs/) supplies hashing/binary restrictions. This runs trusted bootstrap/package-management code and requires future installation scope; it is not a sandbox or an import validation.
7. **Structural verification:** compare all 84 installed name/version records plus separately approved bundled pip against the inventory; verify wheel RECORD mappings, extracted/package file hashes, generated script paths, ownership, profiles/lock digests and complete license documents. RECORD alone is not trusted provenance or an inventory for generated files. Document/hash installer-generated files explicitly and refuse unaccounted additions. No torch/ComfyUI imports here.
8. **Activate:** write a verified structural receipt, then atomically replace only the same-volume active pointer. Never rename Python/venv directories after creation. Result stays `installed_unvalidated`; execution validation and generation readiness remain false.
9. **Separate execution approval:** only later run bounded CPU/Python/PyTorch imports, CUDA availability, actual GPU architecture support, minimal allocation/kernel smoke and loopback ComfyUI health checks. No model/workflow inference follows automatically. Bootstrap commands in step 6 do not grant permission for these tests.
10. **Failure/rollback:** preserve stage, failed-candidate state, digests, error codes and redacted logs. Before activation, leave the previous pointer unchanged. If an explicitly authorized post-activation check fails, atomically restore a still-structurally-valid previous candidate pointer; on first install, unpublish and report failed/corrupted, not ready. Cancellation stops future stages; subprocess termination may leave partial files. Mark interrupted on restart without auto-resume. Offer explicit inventory-scoped cleanup; refuse unknown additions or changed ownership/links. Retain required old base/venv files until rollback references are removed.

Windows file locks, antivirus interference and power loss can delay cleanup. A failure to delete is a clear retained-quarantine state, not permission to force recursive deletion or kill unrelated processes. A rollback pointer cannot undo system installer effects, which is another reason to prefer direct full-ZIP extraction.

## 5. Disk budget

All figures exclude models, generation outputs and inference caches. Sizes are expected metadata, not downloaded-byte measurements.

| Item | Bytes / allowance | Evidence quality |
| --- | --- | --- |
| 84 compressed wheels | **2,677,041,805 bytes (2.49319 GiB)** | Reused complete lock; no re-resolution |
| Full Python ZIP | **31,153,407 bytes (0.02901 GiB)** | Official HEAD metadata |
| Known download subtotal | **2,708,195,212 bytes (2.52220 GiB)** | Sum of the two verified metadata inventories; not the complete runtime total |
| ComfyUI compressed ZIP | **Unknown**; use **64 MiB** planning allowance | No HEAD length; allowance is a policy estimate, not a verified size |
| ComfyUI raw Git blobs | **48,552,928 bytes (46.30368 MiB)** | Complete official Git tree lengths; not extracted disk allocation or archive size |
| One installed candidate | **10–20 GiB**, including private Python, venv and source | Reused conservative estimate; expanded wheel/Python inventories unmeasured |
| Additional staging/temp | **5–10 GiB**, beyond retained downloads | Proposed extraction/pip/interruption allowance, not measured |
| Rollback reserve | **0 on first install; 10–20 GiB for one previous candidate** | Use actual existing-candidate occupancy when available; no duplicate counting if already on disk |
| Free-space safety margin | **max(10 GiB, 20% of download + candidate + temp + rollback budgets)** | Proposed real-install policy; existing tiny fixture margin is not sufficient |

With a roughly **2.585 GiB** download-cache allowance, the proposed first-install additional-space budget is **28–43 GiB**, rounded upward. Reserving space for one rollback candidate gives **38–64 GiB**; when a previous candidate already occupies the same volume, account for its measured occupancy in total capacity without counting it twice against current free space. The exact compressed runtime total remains unknown until source acquisition supplies a length/observed count. Exceeding approved allowances must stop and trigger recalculation, not silently grow staging.

Read ZIP inventories only after authorized acquisition to replace expansion estimates. Recheck space before each write/install/activation; disk checks are not reservations. Configure child-process temp/cache within owned storage, account for filesystem allocation overhead and concurrent users, and enforce streaming caps for unknown-length archives. The earlier **149.197 GiB free-space / 15.9209 GiB VRAM** observations are dated snapshots, not fresh preflight or GPU validation. No local hardware/storage reprobe occurred in 4G.

## 6. Go/no-go matrix and exact next milestone

| Gate | Status | Reason / closure step |
| --- | --- | --- |
| Complete target dependency lock | **VERIFIED** | 84-wheel metadata closure, sizes and publisher hashes independently checked in 4F; actual binary bytes untested |
| Python bootstrap integrity | **VERIFIED (expected metadata)** | Official full-ZIP URL/hash and exact HEAD size; future transfer must verify bytes |
| ComfyUI source integrity | **CONDITIONAL** | Immutable commit/tree and complete blob inventory identified; no published archive hash/length or signature. Accept the stated Git-content policy explicitly and implement/test it, otherwise BLOCKED |
| Runtime licenses and notices | **BLOCKED** | PyOpenGL exact-version text unresolved; binary/vendor/media notices, source delivery, source-to-wheel binding and runtime document/consent package incomplete |
| Isolated installation method | **CONDITIONAL** | Official full-ZIP extraction/venv mechanism documented; real extractor, fixed-path candidates, offline pip controls and exact bootstrap inventory unimplemented/untested |
| Disk preflight | **BLOCKED** | No fresh volume check or measured expanded inventory; budget/limits designed, not implemented |
| Rollback plan | **CONDITIONAL** | Pointer/final-path design defined; real install/cancellation/crash/removal regression coverage absent |
| Explicit installation authorization | **BLOCKED** | Not requested or granted; remains a separate user decision after a concrete reviewed plan |

**Overall: NO-GO.** This is not a finding that the approved stack cannot work. It identifies the evidence and infrastructure still needed before attempting it safely. Real provisioning remains rejected by `real_runtime_disabled`; the candidate profile, lock flags, API/security behavior and frontend are unchanged.

Recommend **Milestone 4H — Offline real-runtime preflight, source verification and consent gates**, with no real transfers:

1. Freeze the selected full-ZIP bootstrap manifest, versioned/hash-bound runtime documents and source tree inventory; resolve PyOpenGL's authoritative exact-release text and record unresolved binary-only evidence separately.
2. Implement plan validation that combines the existing complete wheel lock with Python/bootstrap/source inventory, policy-bounded unknown source size, provenance policy, runtime-document prerequisites, volume budgets and explicit approval binding. Keep real provisioning disabled.
3. Add an archive-member policy bound to the reviewed source/bootstrap inventory, preserving existing manifest validation; test legitimate leading-dot/underscore names as well as tiny hostile ZIPs, Git-content mismatch/missing/extra files, source inventory truncation, ownership/junction escapes, final-path pointer rollback, cancellation and crash journals. Exercise pip-command rendering with fake processes only; execute no runtime/package manager.
4. Define a separate inert binary-notice inspection authorization if required to obtain exact packaged terms unavailable as small official text. Finish that review before requesting real installation. Then present a concrete software-only acquisition/install plan for an independently authorized later milestone; CPU/GPU smoke testing requires its own explicit scope.

No next milestone is begun by this recommendation. No runtime licensing decision authorizes Wan model downloads.
