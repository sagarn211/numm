from pydantic import BaseModel, Field
class RequestCreate(BaseModel):
    requesting_cpse_id: int

class RequestItemCreate(BaseModel):
    national_material_id: int
    requested_quantity: float = Field(gt=0)
    uom: str = Field(default="EA", min_length=1, max_length=50)


class DirectMaterialRequestCreate(BaseModel):
    """Create a request for an already approved/material-mapped product."""
    material_id: int
    requesting_cpse_id: int
    requested_quantity: float = Field(gt=0)
    uom: str = "EA"
