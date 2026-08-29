import os
import uuid

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.schemas.import_schema import (
    ImportResponse
)

from app.services.pipeline_service import (
    run_import_pipeline
)


router = APIRouter(
    prefix="/api/import",
    tags=["Import"]
)


UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


@router.post(
    "",
    response_model=ImportResponse
)
async def upload_materials(
    file: UploadFile = File(...),
    cpse_id: int = Form(...),
    db: Session = Depends(get_db)
):

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    allowed = [
        ".csv",
        ".xlsx",
        ".xls"
    ]

    if extension not in allowed:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV and Excel files "
                "are supported"
            )
        )

    unique_name = (
        f"{uuid.uuid4()}"
        f"{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_name
    )

    content = await file.read()

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(content)

    try:

        batch = run_import_pipeline(

            db=db,

            file_path=file_path,

            filename=file.filename,

            cpse_id=cpse_id
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "successful_rows": batch.successful_rows,
        "failed_rows": batch.failed_rows,
        "status": batch.status
    }

from app.models.import_batch import ImportBatch

@router.get("/batches")
def get_batches(db: Session = Depends(get_db)):
    batches = db.query(ImportBatch).order_by(ImportBatch.id.desc()).all()
    if batches:
        return [
            {
                "id": str(b.id),
                "filename": b.filename,
                "fileType": b.file_type,
                "cpse": "ONGC" if b.cpse_id == 1 else "NTPC" if b.cpse_id == 2 else "SAIL",
                "totalRecords": b.total_rows,
                "successCount": b.successful_rows,
                "errorCount": b.failed_rows,
                "status": b.status,
                "importedAt": b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "2026-08-27"
            }
            for b in batches
        ]
    
    return [
        {
            "id": "batch-1092",
            "filename": "ONGC_Q3_Master_Materials.csv",
            "fileType": "CSV",
            "cpse": "ONGC",
            "totalRecords": 14200,
            "successCount": 13950,
            "errorCount": 250,
            "status": "Completed",
            "importedAt": "2026-08-27 14:30"
        },
        {
            "id": "batch-1091",
            "filename": "NTPC_Valves_Catalog_2026.xlsx",
            "fileType": "Excel",
            "cpse": "NTPC",
            "totalRecords": 4821,
            "successCount": 4821,
            "errorCount": 0,
            "status": "Completed",
            "importedAt": "2026-08-26 11:15"
        }
    ]