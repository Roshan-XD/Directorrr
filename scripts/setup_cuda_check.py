"""Runs only after the setup user explicitly authorizes a bounded CUDA check."""
import json
import sys
from pathlib import Path

import torch

target = Path(sys.argv[1])
root = Path(__file__).resolve().parents[1] / "runtime/windows-dev-001/receipts"
if target.parent != root or target.name != "setup-smoke.json":
    raise ValueError("Invalid CUDA receipt destination")
result = {"torch": torch.__version__, "cuda": torch.version.cuda, "available": torch.cuda.is_available(), "tensor_pass": False}
if result["available"]:
    result.update(gpu=torch.cuda.get_device_name(0), capability=list(torch.cuda.get_device_capability(0)))
    x = torch.arange(16, device="cuda", dtype=torch.float32)
    torch.cuda.synchronize()
    result["tensor_pass"] = (x * 2).cpu().tolist() == [float(i * 2) for i in range(16)]
    torch.cuda.synchronize()
target.write_text(json.dumps(result, indent=2))
if not result["tensor_pass"]:
    raise SystemExit("The GPU test failed; no driver changes were attempted")
