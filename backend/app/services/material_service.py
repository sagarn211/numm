from app.models.material import Material


def create_material(
    db,
    material_data,
    source="manual"
):

    material = Material(

        cpse_id=material_data.cpse_id,

        material_code=material_data.material_code,

        description=material_data.description,

        category=material_data.category,

        unit=material_data.unit,

        manufacturer=material_data.manufacturer,

        model=material_data.model,

        specifications=material_data.specifications,

        source=source
    )

    db.add(material)

    db.commit()

    db.refresh(material)

    return material


def get_materials(db):

    return db.query(
        Material
    ).order_by(
        Material.id.desc()
    ).all()


def get_material(
    db,
    material_id
):

    return db.query(
        Material
    ).filter(
        Material.id == material_id
    ).first()