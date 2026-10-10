from uuid import uuid4

from director.installations.schemas import Acknowledgement, ManagerError, digest
from director.installations.storage import ModelStorageManager
from director.models.schemas import ModelManifest


class LicenseAcknowledgementStore:
    def __init__(self, storage: ModelStorageManager):
        self.storage = storage

    def requirements(self, model: ModelManifest) -> dict:
        if not model.artifact_installation_reviewed or not model.license_documents:
            raise ManagerError("license_documents_missing", "Complete reviewed license documents are required")
        data = {
            "model_id": model.id, "policy_version": "1",
            "license_info": model.license_info.model_dump(mode="json") if model.license_info else None,
            "documents": [document.model_dump(mode="json") for document in model.license_documents],
            "revisions": [{"id": c.id, "repo": c.repository_id, "revision": c.pinned_revision} for c in model.components],
        }
        return {**data, "document_set_digest": digest(data)}

    def record(self, model: ModelManifest, document_set_digest: str, *, accepted: bool) -> Acknowledgement:
        if accepted is not True:
            raise ManagerError("acknowledgement_missing", "Explicit acceptance is required")
        expected = self.requirements(model)["document_set_digest"]
        if document_set_digest != expected:
            raise ManagerError("stale_license_documents", "License document set changed", 409)
        self.storage.ensure_owned()
        record = Acknowledgement(id=uuid4().hex, model_id=model.id, document_set_digest=expected)
        self.storage.write_json(self.storage.path("acknowledgements", record.id + ".json"), record.model_dump(mode="json"))
        return record

    def check(self, model: ModelManifest, acknowledgement_id: str) -> None:
        try:
            record = Acknowledgement.model_validate(self.storage.read_json(
                self.storage.path("acknowledgements", acknowledgement_id + ".json")))
        except (OSError, ValueError):
            raise ManagerError("acknowledgement_missing", "Explicit license acknowledgement is required")
        if record.model_id != model.id or record.document_set_digest != self.requirements(model)["document_set_digest"]:
            raise ManagerError("stale_acknowledgement", "Acknowledgement does not match this model/document version")
