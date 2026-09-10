from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.cpse import CPSE
from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.models.national_material import NationalMaterial
from app.models.material_mapping import MaterialMapping
from app.models.inventory import Inventory
from app.models.material_request import MaterialRequest
from app.models.user import User
from app.utils.rbac import require_permission
from app.services.dashboard_service import comprehensive_dashboard_metrics

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.read")),
):
    total_materials = db.query(Material).count()
    total_national = db.query(NationalMaterial).count()
    total_cpses = db.query(CPSE).count()
    pending = db.query(MaterialMatch).filter(MaterialMatch.status == "PENDING").count()
    mapped = db.query(func.count(func.distinct(MaterialMapping.material_id))).scalar() or 0
    inventory = db.query(
        func.coalesce(
            func.sum(
                case(
                    (
                        Inventory.available_quantity - Inventory.reserved_quantity > 0,
                        Inventory.available_quantity - Inventory.reserved_quantity,
                    ),
                    else_=0,
                )
            ),
            0,
        )
    ).scalar()
    requests = db.query(MaterialRequest).count()

    return {
        "total_materials": total_materials,
        "total_national_materials": total_national,
        "total_cpses": total_cpses,
        "pending_matches": pending,
        "mapped_materials": mapped,
        "unmapped_materials": max(total_materials - mapped, 0),

        # New dashboard aliases/additions
        "participating_cpses": total_cpses,
        "total_legacy_materials": total_materials,
        "national_materials": total_national,
        "ai_recommendations_pending": pending,
        "cross_cpse_inventory": inventory,
        "material_requests": requests,
        **comprehensive_dashboard_metrics(db),
    }

@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.read")),
):
    return comprehensive_dashboard_metrics(db)
