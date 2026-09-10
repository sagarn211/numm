from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=12)
    role: str = "REQUESTING_OFFICER"
    cpse_id: int | None = None

class LoginJSONRequest(BaseModel):
    email: EmailStr
    password: str
