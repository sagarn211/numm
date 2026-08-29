from pydantic import BaseModel


class ImportResponse(BaseModel):

    batch_id: int

    filename: str

    total_rows: int

    successful_rows: int

    failed_rows: int

    status: str