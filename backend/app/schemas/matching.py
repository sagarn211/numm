from typing import Optional

from pydantic import BaseModel


class MatchingResult(BaseModel):

    material_a_id: int

    material_b_id: int

    semantic_score: float

    attribute_score: float

    final_score: float

    classification: str

    status: Optional[str] = "pending"


class ApprovalRequest(BaseModel):

    decision: str