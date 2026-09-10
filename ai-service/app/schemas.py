from typing import Any
from pydantic import BaseModel, Field

class MaterialInput(BaseModel):
    id: int
    cpse_id: int | None = None
    material_code: str | None = None
    description: str
    cleaned_description: str | None = None
    category: str | None = None
    unit: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    specifications: dict[str, Any] = Field(default_factory=dict)

class MatchBatchRequest(BaseModel):
    materials: list[MaterialInput]
    focus_material_ids: list[int] = Field(default_factory=list)

class PairMatchRequest(BaseModel):
    material_a: MaterialInput
    material_b: MaterialInput

class CandidateRequest(BaseModel):
    material: MaterialInput
    candidates: list[MaterialInput]
    top_k: int = Field(default=5, ge=1)
