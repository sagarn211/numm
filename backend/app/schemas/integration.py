from pydantic import BaseModel
class SAPSyncRequest(BaseModel):
    cpse_id: int
    connector: str = "MOCK"

class SAPPushRequest(BaseModel):
    cpse_id: int
    connector: str = "ODATA"
