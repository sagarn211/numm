from fastapi import HTTPException
from app.models.cpse import CPSE

def create_cpse(db, payload):
    code = payload.code.upper()
    if db.query(CPSE).filter(CPSE.code == code).first():
        raise HTTPException(409, "CPSE code already exists")
    obj = CPSE(name=payload.name, code=code, sector=payload.sector)
    db.add(obj); db.flush()
    return obj

def get_cpse(db, cpse_id):
    obj = db.query(CPSE).filter(CPSE.id == cpse_id).first()
    if not obj:
        raise HTTPException(404, "CPSE not found")
    return obj
