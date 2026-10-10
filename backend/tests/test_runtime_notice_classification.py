"""Offline notice classifications are evidence, never installation permission."""
import hashlib
from collections import Counter
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from director.installations.schemas import ManagerError, digest
from director.main import PROJECT_ROOT, create_app
from director.runtimes.lock_validation import load_json
from director.runtimes.preflight import RuntimePreflight
from director.runtimes.review import RuntimeConsentStore, RuntimeReview, NoticeClassification
from director.runtimes.schemas import RuntimeProfile
from director.runtimes.storage import RuntimeStorageManager


def review_packet():
    return RuntimeReview.model_validate(load_json(PROJECT_ROOT / "runtime_profiles/reviews/wan-windows-candidate.json"))


def test_every_original_missing_identity_has_evidenced_classification():
    evidence = load_json(PROJECT_ROOT / "runtime_profiles/licenses/wan-windows-evidence.json")
    section = evidence["notice_classification"]
    rows = section["rows"]
    assert len(rows) == 71
    assert {r["document_id"] for r in rows} == set(section["baseline_missing_document_ids"])
    counts = Counter(r["category"] for r in rows)
    assert {key: counts[key] for key in section["baseline_counts"]} == section["baseline_counts"]
    assert section["baseline_counts"] == {"private_local": 0, "uncertain": 36, "both": 22, "redistribution": 13}
    for row in rows:
        parsed = NoticeClassification.model_validate(row)
        assert parsed.sources and parsed.basis and parsed.unresolved_obligations
        assert parsed.private_local_clearance == "not_cleared" and parsed.preflight_blocker_retained
    assert evidence["review_digest"] == digest(review_packet().model_dump(mode="json"))


def test_redistribution_only_notice_never_bypasses_missing_document_gate(tmp_path):
    packet = review_packet()
    classification = next(c for c in packet.notice_classifications if c.document_id == "package-httpcore")
    assert classification.category == "redistribution"
    consent = RuntimeConsentStore(RuntimeStorageManager(tmp_path / "runtime"))
    response = consent.requirements(packet)
    assert response["classification_does_not_clear_preflight"] is True
    assert response["review_complete"] is False and response["missing_document_ids"]
    with pytest.raises(ManagerError) as refusal:
        consent.record(packet, response["document_set_digest"], accepted=True)
    assert refusal.value.code == "runtime_documents_missing"


def test_uncertain_vendor_terms_remain_uncertain(tmp_path):
    packet = review_packet()
    vendor = next(c for c in packet.notice_classifications if c.document_id == "binary-vendor-notices")
    assert vendor.category == "uncertain" and vendor.document_sha256 is None
    assert vendor.preflight_blocker_retained
    assert "CUDA" in vendor.basis
    storage = RuntimeStorageManager(tmp_path / "runtime")
    manager = SimpleNamespace(storage=storage, has_active_jobs=lambda: False)
    profile = RuntimeProfile.model_validate(load_json(PROJECT_ROOT / "runtime_profiles/wan-windows-candidate.json"))
    report = RuntimePreflight(PROJECT_ROOT, manager).report(profile)
    assert {"runtime_documents_missing", "source_provenance_policy", "real_runtime_disabled", "installation_not_authorized"} <= {
        b["code"] for b in report["blockers"]}
    assert report["installation_authorized"] is False
    assert not storage.base.exists()


@pytest.mark.parametrize("mutation", ["hash", "version", "duplicate", "unknown", "clearance"])
def test_classification_identity_and_hash_validation(mutation):
    data = review_packet().model_dump(mode="json")
    row = next(c for c in data["notice_classifications"] if c["document_id"] == "package-httpcore")
    if mutation == "hash":
        row["document_sha256"] = "0" * 64
    elif mutation == "version":
        row["version"] = "0.0.0"
    elif mutation == "duplicate":
        data["notice_classifications"].append(row)
    elif mutation == "unknown":
        row["document_id"] = "unrequested-notice"
    else:
        row["preflight_blocker_retained"] = False
    with pytest.raises(ValidationError):
        RuntimeReview.model_validate(data)


def test_exact_authorized_artifact_inventory_and_notice_hashes():
    receipt = load_json(PROJECT_ROOT / "runtime_profiles/licenses/pyopengl-3.1.10.inspection.json")
    assert receipt["size_bytes"] == 3194996 < 10 * 1024**2
    assert receipt["observed_sha256"] == receipt["published_sha256"] == "794a943daced39300879e4e47bd94525280685f42dbb5a998d336cfff151d74f"
    assert receipt["source_license_matching_paths"] == []
    assert not any(name.lower().endswith("/license.txt") for name in [f["path"] for f in receipt["inventory"]])
    assert sum(f["path"].endswith(".dll") for f in receipt["inventory"]) == 12
    assert len(receipt["notice_files"]) == 3
    for document in receipt["notice_files"]:
        raw = document["text"].encode("utf-8")
        assert len(raw) == document["size_bytes"]
        assert hashlib.sha256(raw).hexdigest() == document["sha256"]
    assert not receipt["executed"] and not receipt["installed"] and not receipt["extracted"]


def test_changed_classification_invalidates_fixture_consent(tmp_path):
    # All acceptance here is synthetic and isolated; never accept the candidate.
    data = review_packet().model_dump(mode="json")
    text = "MOCK fixture notice only."
    data.update(profile_id="fixture-review", required_document_ids=["fixture-notice"],
                documents=[{"id": "fixture-notice", "version": "1", "text": text,
                            "sha256": hashlib.sha256(text.encode()).hexdigest()}],
                notice_classifications=[{"document_id": "fixture-notice", "version": "1", "category": "both",
                    "basis": "MOCK notice classification.", "sources": ["https://example.invalid/fixture"],
                    "evidence_quality": "uncertain", "unresolved_obligations": ["Mock only; not real use permission"]}],
                license_review_complete=True, unresolved_requirements=[])
    packet = RuntimeReview.model_validate(data)
    consent = RuntimeConsentStore(RuntimeStorageManager(tmp_path / "fixture"))
    record = consent.record(packet, consent.requirements(packet)["document_set_digest"], accepted=True)
    packet.notice_classifications[0].category = "redistribution"
    with pytest.raises(ManagerError) as stale:
        consent.check(packet, record.id)
    assert stale.value.code == "stale_runtime_acknowledgement"


def test_complete_text_cannot_clear_uncertain_obligations(tmp_path):
    # A forged completion flag cannot resolve an explicitly uncertain scope.
    data = review_packet().model_dump(mode="json")
    identity = "package-httpcore"
    document = next(d for d in data["documents"] if d["id"] == identity)
    classification = next(c for c in data["notice_classifications"] if c["document_id"] == identity)
    classification["category"] = "uncertain"
    classification["evidence_quality"] = "uncertain"
    data.update(profile_id="fixture-review", required_document_ids=[identity], documents=[document],
                notice_classifications=[classification], license_review_complete=True, unresolved_requirements=[])
    packet = RuntimeReview.model_validate(data)
    consent = RuntimeConsentStore(RuntimeStorageManager(tmp_path / "fixture"))
    response = consent.requirements(packet)
    assert not response["missing_document_ids"]
    assert response["uncertain_notice_ids"] == [identity] and not response["review_complete"]
    with pytest.raises(ManagerError):
        consent.record(packet, response["document_set_digest"], accepted=True)


def test_api_classification_is_additive_secured_and_installation_disabled(tmp_path):
    key = "offline-classification-test-key-" * 2
    app = create_app(model_root=tmp_path / "models", runtime_root=tmp_path / "runtime", manager_key=key)
    base = "/api/runtime/profiles/wan-windows-candidate"
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get(base + "/runtime-review").status_code == 403
        headers = {"X-Director-Key": key}
        assert client.get(base + "/runtime-review", headers={**headers, "Origin": "https://evil.example"}).status_code == 403
        packet = client.get(base + "/runtime-review", headers=headers).json()
        assert len(packet["notice_classifications"]) == 75
        assert len(packet["missing_document_ids"]) == 68
        assert not packet["review_complete"] and packet["classification_does_not_clear_preflight"]
        assert client.post(base + "/runtime-acknowledgements", headers=headers, json={
            "accepted": True, "document_set_digest": packet["document_set_digest"]}).status_code == 412
        plan = client.get(base + "/preflight", headers=headers).json()
        assert plan["provisionable"] is False and plan["generation_ready"] is False
        assert client.post(base + "/provision", headers=headers, json={
            "confirmed": True, "profile_digest": plan["profile_digest"]}).status_code == 412
