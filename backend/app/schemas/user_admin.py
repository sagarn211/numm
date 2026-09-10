from pydantic import BaseModel


class UserRoleUpdate(BaseModel):
    role: str
    cpse_id: int | None = None
