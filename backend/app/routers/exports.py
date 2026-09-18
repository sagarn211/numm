from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.export_service import export_csv, export_xlsx, export_governance_docx, export_governance_pdf
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


@router.get("/governance-report.pdf")
def governance_pdf(db: Session = Depends(get_db), current_user: User = Depends(require_permission("audit.read", "export.read"))):
    return Response(export_governance_pdf(db), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=numm_governance_report.pdf"})


@router.get("/governance-report.docx")
def governance_docx(db: Session = Depends(get_db), current_user: User = Depends(require_permission("audit.read", "export.read"))):
    return Response(export_governance_docx(db), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=numm_governance_report.docx"})
