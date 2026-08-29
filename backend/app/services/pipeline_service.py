from app.services.import_service import (
    process_import
)


def run_import_pipeline(
    db,
    file_path,
    filename,
    cpse_id
):

    return process_import(
        db=db,
        file_path=file_path,
        filename=filename,
        cpse_id=cpse_id
    )