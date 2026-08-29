from app.models.national_material import (
    NationalMaterial
)


def generate_national_code(db):

    count = db.query(
        NationalMaterial
    ).count()

    return f"NMC-{count + 1:06d}"


def create_national_material(
    db,
    description,
    category=None,
    unit=None,
    specifications=None
):

    code = generate_national_code(
        db
    )

    material = NationalMaterial(

        national_code=code,

        description=description,

        category=category,

        unit=unit,

        specifications=(
            str(specifications)
            if specifications
            else None
        )
    )

    db.add(material)

    db.commit()

    db.refresh(material)

    return material