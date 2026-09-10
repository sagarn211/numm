from pydantic import BaseModel
class DashboardStats(BaseModel):
    total_materials: int
    total_national_materials: int
    total_cpses: int
    pending_matches: int
    mapped_materials: int
    unmapped_materials: int
