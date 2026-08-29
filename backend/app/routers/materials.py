from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.schemas.material import (
    MaterialCreate,
    MaterialResponse
)

from app.services.material_service import (
    create_material,
    get_material,
    get_materials
)


router = APIRouter(
    prefix="/api/materials",
    tags=["Materials"]
)


@router.post(
    "",
    response_model=MaterialResponse
)
def create(
    material: MaterialCreate,
    db: Session = Depends(get_db)
):

    return create_material(
        db,
        material
    )


@router.get(
    "",
    response_model=list[
        MaterialResponse
    ]
)
def list_materials(
    db: Session = Depends(get_db)
):

    return get_materials(db)


@router.get(
    "/{material_id}",
    response_model=MaterialResponse
)
def get_one(
    material_id: int,
    db: Session = Depends(get_db)
):

    material = get_material(
        db,
        material_id
    )

    if not material:

        raise HTTPException(
            status_code=404,
            detail="Material not found"
        )

    return material