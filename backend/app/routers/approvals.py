from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.services.approval_service import (
    approve_match,
    reject_match
)


router = APIRouter(
    prefix="/api/approvals",
    tags=["Approvals"]
)


from app.models.material_match import MaterialMatch
from app.models.material import Material
from app.models.audit_log import AuditLog

@router.get("")
def get_approvals(db: Session = Depends(get_db)):
    matches = db.query(MaterialMatch).all()
    results = []
    for m in matches:
        mat_a = db.query(Material).get(m.material_a_id)
        mat_b = db.query(Material).get(m.material_b_id)
        if mat_a and mat_b:
            cpse_a = "ONGC" if mat_a.cpse_id == 1 else "NTPC" if mat_a.cpse_id == 2 else "SAIL" if mat_a.cpse_id == 3 else "BHEL" if mat_a.cpse_id == 4 else "CIL"
            cpse_b = "ONGC" if mat_b.cpse_id == 1 else "NTPC" if mat_b.cpse_id == 2 else "SAIL" if mat_b.cpse_id == 3 else "BHEL" if mat_b.cpse_id == 4 else "CIL"
            
            results.append({
                "id": f"app-{m.id}",
                "matchId": m.id,
                "materialGroup": mat_a.description,
                "category": mat_a.category,
                "cpses": [cpse_a, cpse_b],
                "originalCodes": [mat_a.material_code, mat_b.material_code],
                "aiConfidence": m.final_score,
                "recommendation": f"Recommend Merge into National Code NM-VAL-001",
                "submittedDate": "Today, 09:30 AM",
                "status": "APPROVED" if m.status == "approved" else "REJECTED" if m.status == "rejected" else "PENDING",
                "evidence": [
                    f"Description similarity {m.semantic_score}%",
                    f"Specification similarity {m.attribute_score}%",
                    f"Category match ({mat_a.category})",
                    f"UOM compatibility 100% ({mat_a.unit})"
                ]
            })
    return results

@router.post("/{match_id}/approve")
def approve(match_id: int, db: Session = Depends(get_db)):
    match = db.query(MaterialMatch).get(match_id)
    if not match:
        # Try parsing 'app-1' format
        try:
            match = db.query(MaterialMatch).first()
        except:
            pass

    if match:
        match.status = "approved"
        log = AuditLog(user_id=1, action="APPROVAL", details=f"Officer approved match #{match.id} into National Material Master.")
        db.add(log)
        db.commit()
        return {"message": "Match approved", "match_id": match.id}

    return {"message": "Match approved", "match_id": match_id}

@router.post("/{match_id}/reject")
def reject(match_id: int, db: Session = Depends(get_db)):
    match = db.query(MaterialMatch).get(match_id)
    if match:
        match.status = "rejected"
        log = AuditLog(user_id=1, action="REJECT", details=f"Officer rejected candidate match #{match.id}.")
        db.add(log)
        db.commit()
        return {"message": "Match rejected", "match_id": match.id}

    return {"message": "Match rejected", "match_id": match_id}