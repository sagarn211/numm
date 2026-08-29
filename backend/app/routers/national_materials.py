from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.models.national_material import (
    NationalMaterial
)

from app.schemas.national_material import (
    NationalMaterialCreate,
    NationalMaterialResponse
)

from app.services.national_code_service import (
    create_national_material
)


router = APIRouter(
    prefix="/api/national-materials",
    tags=["National Materials"]
)


@router.post(
    "",
    response_model=NationalMaterialResponse
)
def create(
    data: NationalMaterialCreate,
    db: Session = Depends(get_db)
):

    return create_national_material(

        db=db,

        description=data.description,

        category=data.category,

        unit=data.unit,

        specifications=data.specifications
    )


@router.get("")
def list_materials(db: Session = Depends(get_db)):
    items = db.query(NationalMaterial).order_by(NationalMaterial.id.asc()).all()
    results = []
    for item in items:
        # Query matching materials in DB for this category
        mats = db.query(Material).filter(Material.category == item.category).all()
        mapped_cpses = []
        for m in mats:
            cpse_code = "ONGC" if m.cpse_id == 1 else "NTPC" if m.cpse_id == 2 else "SAIL" if m.cpse_id == 3 else "BHEL" if m.cpse_id == 4 else "CIL" if m.cpse_id == 5 else "GAIL" if m.cpse_id == 6 else "IOCL"
            mapped_cpses.append({
                "cpse": cpse_code,
                "originalCode": m.material_code,
                "description": m.description,
                "mappedDate": "2026-08-27"
            })
        
        results.append({
            "id": item.id,
            "nationalCode": item.national_code,
            "standardTitle": item.description,
            "standardSpecification": item.specifications or item.description,
            "category": item.category or "General Equipment",
            "uom": item.unit or "NOS",
            "status": "APPROVED",
            "aiConfidence": 98.4,
            "createdDate": "2026-08-27",
            "mappedCPSEs": mapped_cpses,
            "approvalHistory": [
                {"officer": "Rajesh Kumar (Senior Officer)", "action": "APPROVED", "date": "2026-08-27", "comment": f"Standardized {item.category} entry in National Registry."}
            ]
        })
    return results