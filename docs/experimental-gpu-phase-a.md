# Milestone 4L Phase A — Quarantine acquisition and inert inspection

Completed **9 October 2026**, under explicit authorization for acquisition and non-executing inspection only. **Phase A is complete; installation and execution remain unauthorized.** Director's production gates, profiles, consent state, backend and frontend were not changed.

## Destination, limits and verified artifacts

Before transfer, confirmed `D:\Director-GPU-Experiment\run-001` did not exist, checked existing ancestors for reparse/link escapes and measured **160,134,799,360 bytes free** on D:. Created a new experiment ownership marker, `quarantine/` and `notices/` there. No Python extraction/install directory, virtual environment or runtime activation was created.

Validated the exact filenames, URLs and published hashes against [the approved 4K allowlist](experimental-gpu-validation.md#appendix-a--exact-acquisition-allowlist) and the existing complete lock before acquisition. Requested only those official URLs, with redirects rejected, exact Content-Length required, bounded streamed writes and **no automatic retries**. Partial files were renamed only after successful size/hash verification.

| Artifact | Verified transferred bytes |
| --- | ---: |
| `python-3.13.16-amd64.zip` | 31,153,407 |
| `torch-2.12.1+cu130-cp313-cp313-win_amd64.whl` | 1,926,432,963 |
| `filelock-4.0.12-py3-none-any.whl` | 111,732 |
| `typing_extensions-4.16.0-py3-none-any.whl` | 45,571 |
| `setuptools-81.0.0-py3-none-any.whl` | 1,062,021 |
| `sympy-1.14.0-py3-none-any.whl` | 6,299,353 |
| `networkx-3.7-py3-none-any.whl` | 2,142,205 |
| `jinja2-3.1.6-py3-none-any.whl` | 134,899 |
| `fsspec-2026.9.0-py3-none-any.whl` | 221,738 |
| `mpmath-1.3.0-py3-none-any.whl` | 536,198 |
| `markupsafe-3.0.4-cp313-cp313-win_amd64.whl` | 14,313 |
| **Total — 11/11 verified** | **1,968,154,400** |

Every transferred file matched its exact expected size and published SHA-256. An independent second on-disk size/hash pass also passed **11/11**. The transfer cap was met exactly (artifact response-body bytes); ordinary HTTP/TLS protocol overhead is not included. No other network artifacts were requested. The later D: free-space snapshot was **158,163,083,264 bytes**; the volume difference includes local records, filesystem allocation and concurrent activity, not additional transfers.

## Inspection and evidence retained

Used the existing backend interpreter's standard-library ZIP/text readers, never an acquired interpreter or package. Listed ZIP paths, declared sizes/CRC values and binary member names; refused unsafe paths, duplicates, links/special entries, encryption and inventory limits. Opened the bundled pip wheel as inert in-memory ZIP bytes. Read bounded notice/metadata members and retained their original bytes as checksum-named text files. No executable/library/package code was extracted to a runtime, imported or executed. Whole-artifact SHA-256 verifies the acquired archive bytes; this is not per-member execution or a full binary/ABI audit.

- **116 notice-path observations**, representing **44 distinct notice text SHA-256 values**, plus **48 metadata-path observations**. Duplicated pip/vendor notices across the bootstrap and embedded wheel count as separate paths, not new distinct documents. This keyword-bounded inspection is not proof of exhaustive license coverage.
- Python contains its root `LICENSE.txt`, HTML incorporated-software license documentation, full-library/venv/ensurepip paths, bundled **pip 26.2.1**, installed pip metadata and vendor notices. Binary inventory identifies OpenSSL, libffi, Tcl/Tk, SQLite, zlib and Microsoft runtime DLLs. Presence does not prove binary versions, every applicable notice or bootstrap execution.
- PyTorch's acquired METADATA identifies **2.12.1+cu130**; WHEEL identifies **cp313-cp313-win_amd64**. Its declared mandatory dependencies match the planned seven direct dependencies; optional extras remain excluded. Root LICENSE and NOTICE are captured from the actual approved wheel, not just upstream source.
- All nine dependency wheels contain a primary license document. Setuptools additionally includes vendored license texts and notices. These establish actual packaged document presence; permission/acknowledgement and redistribution analysis remain distinct.
- Torch's binary inventory includes CUDA runtime/cuBLAS/cuFFT/cuRAND/cuSOLVER/cuSPARSE, cuDNN 9, NVRTC, CUPTI, NVJitLink, Intel OpenMP, zlib and other DLLs. DLL names reveal families, **not exact versions or definitive notice correspondence**.

Key actual-byte document identities:

| Document | Observed SHA-256 |
| --- | --- |
| Python root `LICENSE.txt` | `62bec384df47b0328307db41455ff6ea2559e5546b394ac69148561b21703120` |
| Python `Doc/html/license.html` | `163dfd2d2e67ad6e84a0485781f6350ab53e29fdc47319512b35f0bc16335ce6` |
| Torch wheel `dist-info/LICENSE` | `5cb5a2b12a3422a30a8a3be813847732f8c8bf4f650b4d61eaaafaa785b90e0f` |
| Torch wheel `dist-info/NOTICE` | `1c3dec6c0342c7ed9e12af59b296c7bb1d394af5cf881db74191cc8299efce5c` |

Full artifact URLs, expected/observed hashes and sizes, notice paths/hashes and binary names are retained in **`D:\Director-GPU-Experiment\run-001\inspection-receipt.json`**. Per-archive inventory JSON files and `notices/<sha256>.txt` retain local evidence. These local files are outside source control. The acquisition helper is a one-off ignored `.verification/phase_a_inspect.py`, not a production downloader or installer.

## Unresolved findings and stop gate

1. **CUDA/vendor use terms and exact correspondence:** torch LICENSE contains third-party and NVIDIA text, including a proprietary license reference and a CuTeDSL EULA URL reference. Those references do not establish which terms govern every included CUDA/cuDNN/CUPTI/other vendor DLL. Applicable documents, component versions, use conditions and any explicit acknowledgements still need evidence. A source/header license reference is not automatically the DLL's license, nor evidence of a violation.
2. **Bootstrap incorporated binaries:** Python's documents contain OpenSSL/libffi/Expat and other incorporated-software terms, but Tcl/Tk and Microsoft redistributable correspondence is not fully established. The acquired DLLs and bundled pip/vendor notices are inventoried, not fully cleared for use or redistribution.
3. **Notice completeness and acceptance:** all nine primary dependency licenses are present, but keyword capture and wrapper declarations cannot prove complete bundled/vendored coverage. Retain reviewed copy/attribution notices; no consent was recorded automatically. Private use and redistribution must remain separate reviews. No production missing-document count was reduced by this experiment.
4. **One filename-search false positive:** Python documentation image `Doc/html/_images/mac_installer_03_license.png` was hashed but not treated as license text (`non_text_unresolved` in receipt). It is not evidence of an unresolved Windows runtime license requirement.
5. **Execution:** private bootstrap operation, pip installation, imports, driver/DLL compatibility, observed compute capability and CUDA tensor execution remain untested. Artifact integrity does not imply installation readiness or GPU compatibility.

**Stop here.** A subsequent installation phase requires fresh, explicit authorization and resolution/review of applicable local-use terms; GPU execution needs its own explicit scope. Do not create a venv, invoke the acquired Python/pip, import torch, initialize CUDA or install anything under the Phase A authorization. Production remains **NO-GO and disabled**; model, ComfyUI and Resolve work remains excluded.

## Checks actually performed

Path/ownership and disk preflight; exact allowlist/transfer-cap checks; all 11 streamed size/SHA-256 checks; independent on-disk rechecks; inert bounded ZIP inventories and notice/metadata reads. No package installation, venv creation, acquired-code execution, CUDA or ComfyUI operation occurred. No application code changed; full backend/frontend tests were not rerun. Historical test results are not presented as new verification.
