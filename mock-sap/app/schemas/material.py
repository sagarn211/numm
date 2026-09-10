from typing import Any
from pydantic import BaseModel, Field

class SAPMaterial(BaseModel):
    cpse_id: int
    material_code: str
    description: str
    category: str | None = None
    uom: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    specifications: dict[str, Any] = Field(default_factory=dict)
