from pydantic import BaseModel


class UserRoleUpdate(BaseModel):
    role: str
    cpse_id: int | None = None


class UserAccountApproval(BaseModel):
    role: str = "REQUESTING_OFFICER"
    cpse_id: int | None = None
    comment: str | None = None


class UserAccountRejection(BaseModel):
    comment: str | None = None
