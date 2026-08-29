from typing import Any
from typing import Dict
from typing import Optional

from pydantic import BaseModel


class NationalMaterialCreate(BaseModel):

    description: str

    category: Optional[str] = None

    unit: Optional[str] = None

    specifications: Optional[
        Dict[str, Any]
    ] = None


class NationalMaterialResponse(BaseModel):

    id: int

    national_code: str

    description: str

    category: Optional[str]

    unit: Optional[str]

    status: str

    class Config:
        from_attributes = True