"""Offline regression checks for captured source evidence, never real consent."""
import hashlib
import shutil
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from director.installations.schemas import ManagerError, digest
from director.main import PROJECT_ROOT
from director.runtimes.lock_validation import load_json
from director.runtimes.preflight import RuntimePreflight
from director.runtimes.review import RuntimeConsentStore, RuntimeReview
from director.runtimes.schemas import RuntimeProfile
from director.runtimes.source import SourceInventory
from director.runtimes.storage import RuntimeStorageManager


def packet():
    return RuntimeReview.model_validate(load_json(
        PROJECT_ROOT / "runtime_profiles/reviews/wan-windows-candidate.json"))


def test_authoritative_document_snapshots_and_coverage():
    review = packet()
    evidence = load_json(PROJECT_ROOT / "runtime_profiles/licenses/wan-windows-evidence.json")
    assert evidence["review_digest"] == digest(review.model_dump(mode="json"))
    assert len(review.documents) == 26 and len(review.required_document_ids) == 94
    documents = {d.id: d for d in review.documents}
    assert {"python", "pip-bootstrap", "package-torch", "torch-source-notice",
            "package-torchvision", "comfyui-source", "package-pyopengl"} <= documents.keys()
    for observed in evidence["documents"]:
        document = documents[observed["id"]]
        payload = document.text.encode("utf-8")
        assert hashlib.sha256(payload).hexdigest() == observed["sha256"] == document.sha256
        assert len(payload) == observed["size_bytes"]
        assert str(document.source) == observed["source"]
        assert document.version == observed["version"]
        assert str(document.source).startswith(("https://raw.githubusercontent.com/", "https://files.pythonhosted.org/"))
        assert observed["exact_binary_notice_coverage"] in {
            "unverified", "specific_member_verified_not_complete_vendor_clearance"}
    assert len(evidence["package_coverage"]) == 84
    assert all(row["binary_notice_status"] == "UNVERIFIED" for row in evidence["package_coverage"] if row["name"] != "pyopengl")
    assert len(evidence["missing_required_document_ids"]) == 68
    assert evidence["installation_authorized"] is False


def test_pyopengl_release_publishing_evidence_matches_exact_locked_wheel():
    evidence = load_json(PROJECT_ROOT / "runtime_profiles/licenses/wan-windows-evidence.json")
    publishing = evidence["pyopengl_publishing_evidence"]
    lock = load_json(PROJECT_ROOT / "runtime_profiles/locks/wan-windows-cp313-cu130.lock.json")
    selected = next(p for p in lock["packages"] if p["name"] == "pyopengl")
    subject = publishing["statement"]["subject"][0]
    assert subject["name"] == selected["wheel_filename"]
    assert subject["digest"]["sha256"] == selected["sha256"]
    document = next(d for d in packet().documents if d.id == "package-pyopengl")
    assert publishing["publishing_commit"] in str(document.source)
    assert document.version == "3.1.10"
    assert "Pyglet" in document.text and "GLE" in document.text and "Regal" in document.text
    assert publishing["local_sigstore_verification"] is False
    assert publishing["wheel_bytes_inspected"] is True


def test_comfyui_license_matches_previously_frozen_source_blob():
    inventory = SourceInventory.model_validate(load_json(
        PROJECT_ROOT / "runtime_profiles/sources/wan-comfyui.inventory.json"))
    document = next(d for d in packet().documents if d.id == "comfyui-source")
    payload = document.text.encode("utf-8")
    file = next(f for f in inventory.files if f.path == "LICENSE")
    assert len(payload) == file.size_bytes
    assert hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest() == file.git_blob_sha1
    provenance = load_json(PROJECT_ROOT / "runtime_profiles/sources/wan-comfyui.provenance.json")
    assert provenance["revision"] == inventory.revision
    assert provenance["tree"] == inventory.tree
    assert provenance["inventory_digest"] == digest(inventory.model_dump())
    assert provenance["publisher_archive_sha256"] is None
    assert provenance["trust_acceptance_recorded"] is False
    assert provenance["activation_authorized"] is False


@pytest.mark.parametrize("field,value", [("text", "Changed document"), ("sha256", "0" * 64)])
def test_changed_document_checksum_rejected(field, value):
    data = packet().model_dump(mode="json")
    data["documents"][0][field] = value
    with pytest.raises(ValidationError, match="hash"):
        RuntimeReview.model_validate(data)


def test_partial_real_packet_cannot_record_consent(tmp_path):
    storage = RuntimeStorageManager(tmp_path / "runtime")
    consent = RuntimeConsentStore(storage)
    requirements = consent.requirements(packet())
    assert len(requirements["missing_document_ids"]) == 68
    assert requirements["review_complete"] is False
    with pytest.raises(ManagerError) as refused:
        consent.record(packet(), requirements["document_set_digest"], accepted=True)
    assert refused.value.code == "runtime_documents_missing"
    assert not storage.base.exists()


def test_document_content_change_invalidates_fixture_consent(tmp_path):
    # Deliberately synthetic review; acceptance exists only in temporary test storage.
    review = packet()
    review.profile_id = "fixture-review"
    review.notice_classifications = []
    review.required_document_ids = ["python"]
    review.documents = [review.documents[0]]
    review.license_review_complete = True
    review.unresolved_requirements = []
    consent = RuntimeConsentStore(RuntimeStorageManager(tmp_path / "fixture"))
    original = consent.requirements(review)["document_set_digest"]
    record = consent.record(review, original, accepted=True)
    review.documents[0].text += "\nSynthetic test revision only."
    review.documents[0].sha256 = hashlib.sha256(review.documents[0].text.encode()).hexdigest()
    with pytest.raises(ManagerError) as stale:
        consent.check(review, record.id)
    assert stale.value.code == "stale_runtime_acknowledgement"


@pytest.mark.parametrize("change_revision", [False, True])
def test_incomplete_provenance_and_wrong_revision_remain_blocked(tmp_path, change_revision):
    root = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT / "runtime_profiles", root / "runtime_profiles")
    if change_revision:
        path = root / "runtime_profiles/sources/wan-comfyui.inventory.json"
        import json
        inventory = load_json(path)
        inventory["revision"] = "a" * 40
        path.write_text(json.dumps(inventory), encoding="utf-8")
    storage = RuntimeStorageManager(tmp_path / "runtime")
    manager = SimpleNamespace(storage=storage, has_active_jobs=lambda: False)
    service = RuntimePreflight(root, manager, disk_usage=lambda _: SimpleNamespace(free=100 * 1024**3))
    profile = RuntimeProfile.model_validate(load_json(root / "runtime_profiles/wan-windows-candidate.json"))
    result = service.report(profile)
    codes = {item["code"] for item in result["blockers"]}
    assert ("source_inventory_missing" if change_revision else "source_provenance_policy") in codes
    assert {"runtime_documents_missing", "installation_not_authorized", "real_runtime_disabled"} <= codes
    assert result["provisionable"] is False and result["generation_ready"] is False
    assert not storage.base.exists()
