from pydantic import BaseModel, Field
class InventoryCreate(BaseModel):
    cpse_id: int
    material_id: int
    warehouse: str = Field(min_length=1, max_length=255)
    available_quantity: float = Field(ge=0)
    reserved_quantity: float = Field(default=0, ge=0)
    uom: str = Field(min_length=1, max_length=50)
    unit_cost: float | None = Field(default=None, ge=0)

class InventoryUpdate(BaseModel):
    available_quantity: float | None = Field(default=None, ge=0)
    reserved_quantity: float | None = Field(default=None, ge=0)
    warehouse: str | None = Field(default=None, min_length=1, max_length=255)
    uom: str | None = Field(default=None, min_length=1, max_length=50)
    unit_cost: float | None = Field(default=None, ge=0)
