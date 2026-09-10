from pydantic import BaseModel

class CPSECreate(BaseModel):
    name: str
    code: str
    sector: str

class CPSEUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    sector: str | None = None
