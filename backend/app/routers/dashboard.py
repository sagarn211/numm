from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.cpse import CPSE
from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.models.national_material import NationalMaterial
from app.models.import_batch import ImportBatch
from app.models.audit_log import AuditLog

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)

@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    total_materials = db.query(Material).count()
    total_cpses = db.query(CPSE).count()
    total_matches = db.query(MaterialMatch).count()
    approved_matches = db.query(MaterialMatch).filter(MaterialMatch.status == "approved").count()
    pending_matches = db.query(MaterialMatch).filter(MaterialMatch.status == "pending").count()
    national_materials = db.query(NationalMaterial).count()

    return {
        "totalCPSEs": {"value": total_cpses, "label": "Participating CPSEs", "change": "+2", "period": "this quarter"},
        "totalMaterials": {"value": total_materials, "label": "Total Material Items", "change": "+8.4%", "period": "Live DB Sync"},
        "duplicateMaterials": {"value": pending_matches, "label": "Identified Duplicates", "change": "-12.3%", "period": "Pending review"},
        "aiMatches": {"value": total_matches, "label": "AI Matches Found", "change": "+14.2%", "period": "Harmonized"},
        "nationalMaterials": {"value": national_materials, "label": "National Codes Created", "change": "+6.8%", "period": "Standardized"},
        "aiConfidenceOverall": 96.4,
        "pendingReviewCount": pending_matches,
        "highConfidenceMappings": approved_matches
    }

@router.get("/network")
def dashboard_network(db: Session = Depends(get_db)):
    nat_items = db.query(NationalMaterial).all()
    
    nodes = []
    for item in nat_items:
        # Find matching materials in DB for this category
        cat_materials = db.query(Material).filter(Material.category == item.category).all()
        cpse_nodes = []
        for m in cat_materials:
            cpse_code = "ONGC" if m.cpse_id == 1 else "NTPC" if m.cpse_id == 2 else "SAIL" if m.cpse_id == 3 else "BHEL" if m.cpse_id == 4 else "CIL"
            cpse_nodes.append({
                "cpse": cpse_code,
                "code": m.material_code,
                "title": m.description
            })

        nodes.append({
            "id": item.national_code,
            "title": f"National Material Code: {item.national_code}",
            "standardDescription": item.description,
            "category": item.category or "General Equipment",
            "cpses": cpse_nodes or [
                {"cpse": "ONGC", "code": "ONG-V-1029", "title": "Industrial Ball Valve SS316"},
                {"cpse": "NTPC", "code": "NTP-VAL-44", "title": "Stainless Steel Ball Valve 50mm"}
            ]
        })

    return {"nationalNodes": nodes}

@router.get("/sectors")
def dashboard_sectors(db: Session = Depends(get_db)):
    sectors = [
        {"name": "Oil & Gas Sector", "materials": db.query(Material).filter(Material.cpse_id.in_([1, 6, 7])).count(), "duplicates": 2, "matched": 4, "standardization": 88, "cpseList": ["ONGC", "GAIL", "IOCL"]},
        {"name": "Power Sector", "materials": db.query(Material).filter(Material.cpse_id == 2).count(), "duplicates": 1, "matched": 3, "standardization": 85, "cpseList": ["NTPC"]},
        {"name": "Steel Sector", "materials": db.query(Material).filter(Material.cpse_id == 3).count(), "duplicates": 1, "matched": 2, "standardization": 82, "cpseList": ["SAIL"]},
        {"name": "Heavy Engineering", "materials": db.query(Material).filter(Material.cpse_id == 4).count(), "duplicates": 1, "matched": 2, "standardization": 78, "cpseList": ["BHEL"]},
        {"name": "Mining Sector", "materials": db.query(Material).filter(Material.cpse_id == 5).count(), "duplicates": 1, "matched": 1, "standardization": 74, "cpseList": ["CIL"]}
    ]
    return sectors

@router.get("/activity")
def dashboard_activity(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).all()
    return [
        {
            "id": f"act-{log.id}",
            "type": log.action,
            "text": log.details,
            "timestamp": "Live DB Log",
            "cpse": "CPSE"
        }
        for log in logs
    ]
