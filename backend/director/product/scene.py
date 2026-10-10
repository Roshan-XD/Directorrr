"""Scene continuity and audio contracts; execution requires a model-specific adapter."""
from typing import Literal
from pydantic import Field, model_validator
from director.product.capabilities import StrictModel, Shot, Capability

class SequencePlan(StrictModel):
    model_id: str
    shots: list[Shot] = Field(min_length=1,max_length=12)
    continuity_notes: str = Field(default="",max_length=4000)
    @model_validator(mode="after")
    def unique_shots(self):
        if len({shot.id for shot in self.shots})!=len(self.shots): raise ValueError("Duplicate shot identity")
        return self
    def validate_for(self,capability:Capability,owned_completed_jobs:set[str]):
        if capability.id!=self.model_id: raise ValueError("Model identity mismatch")
        for shot in self.shots:
            shot.validate_for(capability)
            if shot.previous_job_id and shot.previous_job_id not in owned_completed_jobs:
                raise ValueError("Reference must belong to a completed Director job")

class AudioTrack(StrictModel):
    origin: Literal["none","native","separate-track"]
    present: bool
    codec: str | None = None
    sample_rate: int | None = Field(default=None,ge=8000,le=192000)
    channels: int | None = Field(default=None,ge=1,le=8)
    @model_validator(mode="after")
    def consistent(self):
        if self.origin=="none" and self.present: raise ValueError("Unexpected audio")
        if self.present and (not self.codec or self.sample_rate is None or self.channels is None): raise ValueError("Audio verification metadata missing")
        return self

class SceneOutput(StrictModel):
    job_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    width:int=Field(ge=1)
    height:int=Field(ge=1)
    frames:int=Field(ge=1)
    fps:float=Field(gt=0)
    audio:AudioTrack
    decoded_video:bool
    decoded_audio:bool | None = None
    resolve_compatible:bool=False
    @model_validator(mode="after")
    def verified(self):
        if self.resolve_compatible and (not self.decoded_video or (self.audio.present and self.decoded_audio is not True)):
            raise ValueError("Resolve output must preserve and validate advertised native audio")
        return self
