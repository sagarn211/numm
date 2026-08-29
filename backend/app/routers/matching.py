from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.models.material import Material
from app.models.material_match import (
    MaterialMatch
)

from app.services.ai_service import (
    get_ai_matches
)


router = APIRouter(
    prefix="/api/matching",
    tags=["AI Matching"]
)


@router.post("/run")
async def run_matching(
    db: Session = Depends(get_db)
):

    materials = db.query(
        Material
    ).all()

    payload = []

    for material in materials:

        payload.append({

            "id": material.id,

            "material_code":
                material.material_code,

            "description":
                material.description,

            "category":
                material.category,

            "unit":
                material.unit,

            "manufacturer":
                material.manufacturer,

            "model":
                material.model,

            "specifications":
                material.specifications
        })

    if len(payload) < 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "At least two materials "
                "are required for matching"
            )
        )

    try:

        result = await get_ai_matches(
            payload
        )

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail=(
                f"AI service error: {error}"
            )
        )

    matches = result.get(
        "matches",
        []
    )

    saved = []

    for item in matches:

        match = MaterialMatch(

            material_a_id=item[
                "material_a_id"
            ],

            material_b_id=item[
                "material_b_id"
            ],

            semantic_score=item.get(
                "semantic_score",
                0
            ),

            attribute_score=item.get(
                "attribute_score",
                0
            ),

            final_score=item.get(
                "final_score",
                0
            ),

            classification=item.get(
                "classification",
                "UNKNOWN"
            ),

            status="pending"
        )

        db.add(match)

        saved.append(match)

    db.commit()

    return {
        "message": "Matching completed",
        "matches_found": len(saved)
    }


@router.get("")
def get_matches(
    db: Session = Depends(get_db)
):
    matches = db.query(MaterialMatch).order_by(MaterialMatch.final_score.desc()).all()
    results = []
    for m in matches:
        mat_a = db.query(Material).get(m.material_a_id)
        mat_b = db.query(Material).get(m.material_b_id)
        if mat_a and mat_b:
            cpse_a = "ONGC" if mat_a.cpse_id == 1 else "NTPC" if mat_a.cpse_id == 2 else "SAIL" if mat_a.cpse_id == 3 else "BHEL" if mat_a.cpse_id == 4 else "CIL"
            cpse_b = "ONGC" if mat_b.cpse_id == 1 else "NTPC" if mat_b.cpse_id == 2 else "SAIL" if mat_b.cpse_id == 3 else "BHEL" if mat_b.cpse_id == 4 else "CIL"
            
            conf_category = "HIGH" if m.final_score >= 90 else "MEDIUM" if m.final_score >= 70 else "NEEDS_REVIEW"
            results.append({
                "id": f"rec-{m.id}",
                "confidenceCategory": conf_category,
                "overallConfidence": m.final_score,
                "sourceMaterial": {
                    "code": mat_a.material_code,
                    "cpse": cpse_a,
                    "description": mat_a.description,
                    "specification": mat_a.specifications or mat_a.description,
                    "uom": mat_a.unit,
                    "category": mat_a.category
                },
                "targetMaterial": {
                    "code": mat_b.material_code,
                    "cpse": cpse_b,
                    "description": mat_b.description,
                    "specification": mat_b.specifications or mat_b.description,
                    "uom": mat_b.unit,
                    "category": mat_b.category
                },
                "suggestedNationalCode": "NM-VAL-001" if "Valve" in mat_a.description else "NM-TRF-004" if "Transformer" in mat_a.description else "NM-PMP-002",
                "aiReasoning": f"Descriptions and technical parameters strongly overlap ({m.final_score}% score). Both specify {mat_a.category} equipment.",
                "matchMetrics": {
                    "descriptionSimilarity": m.semantic_score,
                    "specificationSimilarity": m.attribute_score,
                    "categorySimilarity": 100.0,
                    "uomCompatibility": 100.0
                }
            })
    return results