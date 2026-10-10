import hashlib
import json
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from director.models.schemas import ModelManifest

State = Literal["not_installed", "checking", "downloading", "verifying", "installing", "ready", "failed", "cancelled", "corrupted"]
TERMINAL = {"not_installed", "ready", "failed", "cancelled", "corrupted"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def manifest_digest(model: ModelManifest) -> str:
    return digest(model.model_dump(mode="json"))


class ManagerError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 412):
        super().__init__(message)
        self.code, self.message, self.status_code = code, message, status_code


class Cancelled(Exception):
    pass


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VerificationResult(Record):
    component_id: str
    valid: bool
    code: str
    expected_size: int | None
    actual_size: int | None = None
    expected_sha256: str | None
    actual_sha256: str | None = None


class Job(Record):
    id: str
    model_id: str
    operation: Literal["install", "verify", "remove"]
    state: State = "checking"
    manifest: ModelManifest
    manifest_digest: str
    acknowledgement_id: str | None = None
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
    cancel_requested: bool = False
    total_expected_bytes: int = 0
    candidate_bytes: int = 0
    verified_bytes: int = 0
    current_component: str | None = None
    error: dict[str, str] | None = None
    verification: list[VerificationResult] = Field(default_factory=list)
    generation_ready: Literal[False] = False


class Receipt(Record):
    job_id: str
    model_id: str
    manifest: ModelManifest
    manifest_digest: str
    acknowledgement_id: str
    verified_at: str = Field(default_factory=now)
    verification: list[VerificationResult]


class Acknowledgement(Record):
    id: str
    model_id: str
    document_set_digest: str
    policy_version: Literal["1"] = "1"
    accepted_at: str = Field(default_factory=now)


class InstallRequest(Record):
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    acknowledgement_id: str = Field(pattern=r"^[0-9a-f]{32}$")


class AcknowledgeRequest(Record):
    accepted: Literal[True]
    document_set_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_version: Literal["1"] = "1"

    @field_validator("accepted", mode="before")
    @classmethod
    def explicit_boolean(cls, value):
        if value is not True:
            raise ValueError("Acceptance must be the boolean true")
        return value
