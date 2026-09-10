from io import BytesIO, StringIO
from collections import defaultdict
import pandas as pd
from app.models.national_material import NationalMaterial
from app.models.material_mapping import MaterialMapping
from app.models.material import Material
from app.models.cpse import CPSE
from app.models.inventory import Inventory

def rows(db):
    mappings_by_national = defaultdict(list)
    for mapping in db.query(MaterialMapping).all():
        mappings_by_national[mapping.national_material_id].append(mapping)
    materials = {material.id: material for material in db.query(Material).all()}
    cpses = {cpse.id: cpse for cpse in db.query(CPSE).all()}
    quantity_by_material = defaultdict(float)
    for inventory in db.query(Inventory).all():
        quantity_by_material[inventory.material_id] += max(
            inventory.available_quantity - inventory.reserved_quantity,
            0,
        )

    output = []
    for n in db.query(NationalMaterial).all():
        mappings = mappings_by_national[n.id]

        if not mappings:
            output.append({
                "National Code": n.national_code,
                "Standard Description": n.description,
                "Category": n.category,
                "UOM": n.unit,
                "CPSE": None,
                "Legacy Code": None,
                "Available Quantity": 0,
                "Mapping Type": None,
            })

        for mp in mappings:
            material = materials.get(mp.material_id)
            cpse = cpses.get(material.cpse_id) if material else None
            qty = quantity_by_material[mp.material_id]
            output.append({
                "National Code": n.national_code,
                "Standard Description": n.description,
                "Category": n.category,
                "UOM": n.unit,
                "CPSE": cpse.name if cpse else None,
                "Legacy Code": material.material_code if material else None,
                "Available Quantity": qty,
                "Mapping Type": mp.mapping_type,
            })
    return output

def export_csv(db):
    s = StringIO()
    pd.DataFrame(rows(db)).to_csv(s, index=False)
    return s.getvalue().encode()

def export_xlsx(db):
    b = BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as writer:
        pd.DataFrame(rows(db)).to_excel(writer, index=False, sheet_name="National Registry")
    return b.getvalue()
