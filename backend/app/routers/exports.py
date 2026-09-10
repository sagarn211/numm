from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.export_service import export_csv, export_xlsx
from app.models.user import User
from app.utils.rbac import require_permission

router = APIRouter(prefix="/api/exports", tags=["Exports"])

@router.get("/national-registry.csv")
def csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.read")),
):
    return Response(
        export_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=national_material_registry.csv"},
    )

@router.get("/national-registry.xlsx")
def xlsx(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.read")),
):
    return Response(
        export_xlsx(db),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=national_material_registry.xlsx"},
    )
