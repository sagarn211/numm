from app.models.material import Material
def material_code_exists(db, cpse_id: int, material_code: str):
    return db.query(Material).filter(
        Material.cpse_id == cpse_id,
        Material.material_code == material_code
    ).first() is not None
