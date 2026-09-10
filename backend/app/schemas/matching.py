from pydantic import BaseModel
class MatchingResult(BaseModel):
    id: int
    material_a_id: int
    material_b_id: int
    final_score: float
    classification: str
    status: str
    model_config = {"from_attributes": True}
