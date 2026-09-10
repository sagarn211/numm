from typing import Any
from pydantic import BaseModel, Field
class NationalMaterialCreate(BaseModel):
    description: str
    category: str | None = None
    subcategory: str | None = None
    unit: str | None = None
    specifications: dict[str, Any] = Field(default_factory=dict)

class NationalMaterialUpdate(BaseModel):
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    unit: str | None = None
    specifications: dict[str, Any] | None = None
    status: str | None = None
