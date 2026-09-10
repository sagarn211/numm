import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/materials", tags=["Materials"])
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sap_materials.json"

def load_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

@router.get("")
def get_materials(cpse_id: int | None = None):
    rows = load_data()
    if cpse_id is not None:
        rows = [x for x in rows if x.get("cpse_id") == cpse_id]
    return {"materials": rows, "count": len(rows)}

@router.get("/{material_code}")
def get_material(material_code: str):
    for row in load_data():
        if row["material_code"] == material_code:
            return row
    raise HTTPException(404, "SAP material not found")
