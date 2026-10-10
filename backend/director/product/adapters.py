"""Deterministic, fail-closed family identification; never guesses from model names."""
from typing import Literal
from pydantic import Field
from director.product.capabilities import StrictModel, Capability

class FamilyAdapter(StrictModel):
    schema_version: Literal[1]=1
    family_id: str
    repositories: list[str] = Field(min_length=1)
    capability: Capability
    backend: Literal["comfyui-native"]="comfyui-native"
    workflow: str | None
    status: Literal["validated_development","configured_development","metadata_only"]
    optional_assets: list[str]=[]
    dependency_policy: Literal["reviewed_exact_inventory_only"]="reviewed_exact_inventory_only"
    arbitrary_repository_code: Literal[False]=False

def family(capability):
    return FamilyAdapter(family_id=capability.id,repositories=[capability.repository],capability=capability,
        workflow="wan-stage7-native-v1" if capability.adapter=="wan-native-v1" else "minimax-h3-native-t2va-v1" if capability.adapter=="minimax-h3-native-v1" else None,
        status="validated_development" if capability.adapter=="wan-native-v1" else "configured_development" if capability.adapter=="minimax-h3-native-v1" else "metadata_only")

def classify(repository, catalog):
    match=next((m for m in catalog["models"] if m["repository"]==repository),None)
    if not match: return {"state":"adapter_required","model_id":None,"runnable":False,"reason":"No exact reviewed repository adapter. Architecture compatibility is unknown."}
    return {"state":"director_ready" if match["runnable"] else "installed" if match["installed"] else "candidate_blocked",
            "model_id":match["id"],"runnable":match["runnable"],"reason":"Exact capability match; installation and execution remain separate."}
