# Install Director on another Windows PC

Download **Director-Windows-Setup.zip** from [GitHub Releases](https://github.com/Roshan-XD/Directorrr/releases). Extract the entire ZIP to a short writable local folder, such as `D:\Director` or `C:\Users\YourName\Director`. Keep this folder: private Python environments cannot be moved after setup. Avoid Program Files, network shares and unrelated installations.

1. Open **Setup Director.exe**. Review the included Python terms and click **Prepare Director setup**. It downloads the official full Python ZIP, verifies its exact size/SHA-256 and extracts privately. No administrator access or system Python changes are required.
2. The wizard shows the budget, destination and complete agreement references. Review the full terms and preserved bundled notices, then explicitly acknowledge private installation and the small CUDA check. Nothing is preselected or copied from the developer's acceptance.
3. Confirm the separate **three Wan files** option, then click **Confirm / Install Director**. The next panels show the exact bundled Python 3.11.9 terms and downloaded backend wheel notices; explicitly review/accept them before their software is executed or installed. Setup verifies pinned software/model hashes, checks all 1,248 ComfyUI files against the frozen Git tree, runs `pip check` and a 16-element CUDA operation. It performs no video generation or Resolve editing. H3 is not downloaded.
4. Open **Start Director.cmd** when setup finishes. It starts Windows services and opens the built UI. No Node, npm, manual activation, WSL or manager key is needed. **Stop Director.cmd** stops the owned session.

## Requirements and budget

- Windows AMD64 with .NET Framework 4.x, internet access and at least **32 GiB free** for downloads, installed files and model handoff. This is an estimate; disk space is rechecked. Caches are retained privately, not automatically removed.
- A CUDA 13-compatible NVIDIA Windows driver/GPU. The developer's RTX 5080 Laptop, approximately 16 GiB VRAM and 32 GiB RAM passed the fixed Wan preview. Other PCs need their own tests; RAM/VRAM alone do not prove compatibility. Setup never installs drivers or a standalone toolkit.
- Known software transfers: **2,751,945,221 bytes**, including separate Python 3.13.16 (GPU runtime) and Python 3.11.9 (backend), 84 runtime wheels and 33 backend wheels. ComfyUI source adds up to **64 MiB**; its identity is verified using the frozen Git tree, not an invented publisher archive hash.
- Wan transfers: **9,828,025,775 bytes**, confirmed separately. Known total: **12,579,970,996 bytes** plus source. Existing valid managed files are verified rather than replaced; no other model variants are fetched.
- Resolve is installed separately and must be running with the development project named **Director Development** and scripting access for import/timeline actions. Placement still requires fresh confirmation.

## Scope and failure handling

This is a **private development setup preview**, not a cleared bundled production installer. The ZIP includes Director's source/UI/bootstrap and review documents, not third-party runtime binaries or weights. Each user acquires those directly and accepts their own applicable terms. Redistribution and production provisioning remain uncleared/disabled.

Configuration, CUDA validation and generation validation are distinct. Setup never writes a fake native-inference PASS. A receiving PC still needs a first real generation test. Offline fixtures and the author's working runtime do not constitute a fresh-PC installation test.

Failures stop setup and retain logs under `setup/state`. Drivers, global Python, Resolve, other runtimes and user media are preserved. Cancellation stops the current owned pip operation or SDK transfer. Retries reuse verified artifacts/source and reject changed notices/files. Partial Python bootstrap failures require a fresh extracted folder rather than silent repair.

To remove a fresh private installation: Stop Director, preserve your videos/library, then remove only that extracted folder after checking ownership. Shared Python, Node, drivers and Resolve need no uninstall.

The setup EXE is currently unsigned and compiled from `setup/Bootstrap.cs`; source and release ZIP SHA-256 are published. It does not modify registry/PATH or create global services/file associations.
