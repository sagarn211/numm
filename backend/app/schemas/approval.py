from typing import Any
from pydantic import BaseModel, Field
class ApprovalRequest(BaseModel):
    comment: str | None = None
    canonical_values: dict[str, Any] = Field(default_factory=dict)
    acknowledge_critical_conflicts: bool = False
    acknowledge_functional_equivalent: bool = False
