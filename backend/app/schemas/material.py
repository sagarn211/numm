from typing import Any
from typing import Dict
from typing import Optional

from pydantic import BaseModel


class MaterialBase(BaseModel):

    cpse_id: int

    material_code: str

    description: str

    category: Optional[str] = None

    unit: Optional[str] = None

    manufacturer: Optional[str] = None

    model: Optional[str] = None

    specifications: Optional[
        Dict[str, Any]
    ] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialResponse(MaterialBase):

    id: int

    source: Optional[str] = None

    class Config:
        from_attributes = True