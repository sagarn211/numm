from typing import Any
from pydantic import BaseModel, Field

class MaterialCreate(BaseModel):
    cpse_id: int
    material_code: str
    description: str
    category: str | None = None
    subcategory: str | None = None
    unit: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    specifications: dict[str, Any] = Field(default_factory=dict)
    source: str = "MANUAL"

class MaterialUpdate(BaseModel):
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    unit: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    specifications: dict[str, Any] | None = None
    status: str | None = None
