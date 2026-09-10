from app.services.import_service import process_import_legacy
def process_import(db, file, cpse_id):
    return process_import_legacy(db, file, cpse_id)
