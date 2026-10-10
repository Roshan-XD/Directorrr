"""Synthetic audit inputs only; these tests perform no network or runtime work."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from director.runtimes.lock_validation import load_json, validate_lock
from director.runtimes.schemas import RuntimeProfile

ROOT = Path(__file__).resolve().parents[2]


def package(name, version, dependencies=(), cuda=False):
    tags = "cp313-cp313-win_amd64" if cuda else "py3-none-any"
    filename = f"{name.replace('-', '_')}-{version}-{tags}.whl"
    index = f"https://download.pytorch.org/whl/cu130/{name}/" if cuda else f"https://pypi.org/simple/{name}/"
    url = f"https://download.pytorch.org/whl/cu130/{filename}" if cuda else f"https://files.pythonhosted.org/packages/test/{filename}"
    return dict(name=name, version=version, source_index=index, artifact_url=url,
                wheel_filename=filename, wheel_tags=[tags], sha256="a" * 64,
                size_bytes=10, requires_python=">=3.10", requires_dist=list(dependencies),
                dependency_evidence="SELECTED_WHEEL_SIDECAR", license_declaration=None,
                evidence=[{"source": url + ".metadata", "observed_metadata_sha256": "b" * 64}],
                limitations=[], requested_extras=[], incoming_constraints=[], dependency_metadata_complete=True)


@pytest.fixture
def inputs():
    profile = RuntimeProfile(id="test", name="Synthetic audit profile", python_version="3.13.16",
                             architecture="AMD64", comfyui_commit="c" * 40,
                             pytorch_version="2.12.1+cu130", torchvision_version="0.27.1+cu130", cuda_wheel="cu130")
    roots = "torch\ntorchvision\n"
    lock = dict(lock_schema_version=1, status="INCOMPLETE", installation_eligible=False,
                authorized_real_installation=False, execution_validated=False, profile_id="test",
                target=dict(implementation_name="cpython", implementation_version="3.13.16", os_name="nt",
                            platform_machine="AMD64", platform_system="Windows", python_full_version="3.13.16",
                            platform_python_implementation="CPython", python_version="3.13", sys_platform="win32",
                            extra="", platform_release="UNKNOWN", platform_version="UNKNOWN"),
                wheel_target=dict(python_version="3.13.16", interpreter="cp313", abi="cp313", platform="win_amd64", cuda="cu130"),
                comfyui=dict(commit="c" * 40,
                             requirements_source="https://raw.githubusercontent.com/Comfy-Org/ComfyUI/" + "c" * 40 + "/requirements.txt",
                             requirements_sha256=hashlib.sha256(roots.encode()).hexdigest()),
                resolution={}, packages=[package("torch", "2.12.1+cu130", ["helper>=1", "never; sys_platform == 'linux'"], True),
                                         package("torchvision", "0.27.1+cu130", ["torch==2.12.1"], True), package("helper", "1.0")],
                relationships=[], issues=[], summary={}, graph_complete=False, audited_at="2026-10-09",
                profile_source="fixture.json", profile_file_sha256="d" * 64,
                readiness=dict(complete_audited_lock=False, authorized_real_installation=False,
                               execution_validated_runtime=False, generation_ready=False), limitations=[])
    summarize(lock)
    return lock, profile, roots


def summarize(lock):
    packages = lock["packages"]
    size_count = sum(p["size_bytes"] is not None for p in packages)
    total = sum(p["size_bytes"] or 0 for p in packages)
    lock["summary"] = dict(selected_package_count=len(packages), published_hash_count=len(packages),
                           known_size_count=size_count, known_download_bytes=total,
                           exact_total_download_bytes=total if size_count == len(packages) else None,
                           wheel_sidecar_count=sum(p["dependency_evidence"] == "SELECTED_WHEEL_SIDECAR" for p in packages),
                           missing_selected_wheel_metadata=sorted(p["name"] for p in packages if not p["dependency_metadata_complete"]))


def codes(report):
    return {e["code"] for e in report["errors"] + report["blockers"]}


def test_valid_lock_ignores_resolver_claims(inputs):
    lock, profile, roots = inputs
    report = validate_lock(lock, profile, roots)
    assert report["complete"] and report["valid"]
    assert report["verified_metadata_artifact_bytes"] == 30
    assert report["installation_authorized"] is False
    # There are deliberately no recorded relationships/incoming constraints.
    assert report["active_relationship_count"] > 0


@pytest.mark.parametrize("mutation,expected", [
    (lambda x: x["packages"].pop(), "missing_dependency"),
    (lambda x: x["packages"].append(copy.deepcopy(x["packages"][2])), "duplicate_package"),
    (lambda x: x["packages"][0].update(sha256="invalid"), "schema"),
    (lambda x: x["packages"][2].update(wheel_filename="helper-1.0-cp313-cp313-manylinux_2_28_x86_64.whl", wheel_tags=["cp313-cp313-manylinux_2_28_x86_64"]), "wheel_tags"),
    (lambda x: x["packages"][0]["requires_dist"].append("helper>=2"), "version_conflict"),
    (lambda x: x["packages"][0].update(version="2.12.1+cpu"), "cuda_pin"),
    (lambda x: x["packages"][0].update(requires_dist=None, dependency_metadata_complete=False), "dependency_metadata"),
    (lambda x: x["packages"][0].update(size_bytes=None), "artifact_size"),
    (lambda x: x["packages"][0].update(evidence=[]), "dependency_metadata"),
    (lambda x: x["packages"][2].update(requires_python=">=3.14"), "python_constraint"),
    (lambda x: x["packages"][2].update(version=">=1"), "package_metadata"),
    (lambda x: x["packages"][2].update(artifact_url="https://example.com/helper-1.0-py3-none-any.whl"), "artifact_source"),
    (lambda x: x["packages"][2].update(artifact_url="https://[malformed"), "artifact_source"),
    (lambda x: x["packages"][0]["requires_dist"].append("helper; platform_release == '10'"), "unknown_marker"),
    (lambda x: x["packages"][0]["requires_dist"].append("helper @ https://example.com/test.whl"), "requirement"),
    (lambda x: x["packages"].append(package("orphan", "1.0")), "orphan_package"),
    (lambda x: x["wheel_target"].update(platform="win_arm64"), "profile_mismatch"),
    (lambda x: x.update(authorized_real_installation=True), "schema"),
    (lambda x: x["readiness"].update(generation_ready=True), "unsafe_gate"),
    (lambda x: x["packages"][0]["evidence"][0].update(published_metadata_sha256="c" * 64), "metadata_hash"),
])
def test_rejects_invalid_or_incomplete_lock(inputs, mutation, expected):
    lock, profile, roots = inputs
    mutation(lock)
    summarize(lock)
    report = validate_lock(lock, profile, roots)
    assert not report["complete"]
    assert expected in codes(report)
    assert report["installation_authorized"] is False


def test_extras_are_propagated_from_requirements(inputs):
    lock, profile, roots = inputs
    lock["packages"][0]["requires_dist"][0] = "helper[option]>=1"
    lock["packages"][2]["requires_dist"] = ["extra-pkg; extra == 'option'"]
    lock["packages"][2]["requested_extras"] = ["option"]
    assert "missing_dependency" in codes(validate_lock(lock, profile, roots))
    lock["packages"].append(package("extra-pkg", "1.0"))
    summarize(lock)
    assert validate_lock(lock, profile, roots)["complete"]


def test_no_requires_python_declaration_is_not_an_invented_constraint(inputs):
    lock, profile, roots = inputs
    lock["packages"][2]["requires_python"] = None
    assert validate_lock(lock, profile, roots)["complete"]


def test_completion_claim_requires_evidence(inputs):
    lock, profile, roots = inputs
    lock.update(status="COMPLETE", graph_complete=True)
    lock["readiness"]["complete_audited_lock"] = True
    lock["packages"][0]["requires_dist"] = None
    assert "false_completion" in codes(validate_lock(lock, profile, roots))


def test_duplicate_normalized_package(inputs):
    lock, profile, roots = inputs
    lock["packages"].append({**lock["packages"][2], "name": "HELPER"})
    assert "duplicate_package" in codes(validate_lock(lock, profile, roots))


def test_root_snapshot_and_profile_digest(inputs):
    lock, profile, roots = inputs
    assert "root_identity" in codes(validate_lock(lock, profile, roots + "missing\n"))
    assert "profile_digest" in codes(validate_lock(lock, profile, roots, b"changed profile"))


def test_rejects_duplicate_json_keys(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"status":"COMPLETE","status":"INCOMPLETE"}')
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        load_json(path)


def test_real_lock_offline_regression():
    path = ROOT / "runtime_profiles/locks/wan-windows-cp313-cu130.lock.json"
    profile_path = ROOT / "runtime_profiles/wan-windows-candidate.json"
    roots = (path.parent / "wan-windows-comfyui-requirements.txt").read_text(encoding="utf-8")
    result = validate_lock(load_json(path), RuntimeProfile.model_validate_json(profile_path.read_text()), roots, profile_path.read_bytes())
    assert result["complete"] and result["valid"]
    assert result["package_count"] == 84
    assert result["verified_metadata_artifact_bytes"] == 2_677_041_805
    assert not result["installation_authorized"]
