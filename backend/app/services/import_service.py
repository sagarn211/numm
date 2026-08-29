import os

from app.models.material import Material
from app.models.import_batch import ImportBatch

from app.services.csv_service import read_csv
from app.services.excel_service import read_excel
from app.services.validation_service import (
    validate_material_row
)
from app.services.normalization_service import (
    normalize_material
)


def process_import(
    db,
    file_path,
    filename,
    cpse_id
):

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension == ".csv":

        rows = read_csv(file_path)

        file_type = "csv"

    elif extension in [
        ".xlsx",
        ".xls"
    ]:

        rows = read_excel(file_path)

        file_type = "excel"

    else:

        raise ValueError(
            "Only CSV and Excel files are supported"
        )

    batch = ImportBatch(

        filename=filename,

        file_type=file_type,

        cpse_id=cpse_id,

        total_rows=len(rows),

        status="processing"
    )

    db.add(batch)

    db.commit()

    db.refresh(batch)

    successful = 0

    failed = 0

    for row in rows:

        errors = validate_material_row(
            row
        )

        if errors:

            failed += 1

            continue

        normalized = normalize_material(
            row
        )

        material = Material(

            cpse_id=cpse_id,

            material_code=normalized[
                "material_code"
            ],

            description=normalized[
                "description"
            ],

            category=normalized[
                "category"
            ],

            unit=normalized[
                "unit"
            ],

            manufacturer=normalized[
                "manufacturer"
            ],

            model=normalized[
                "model"
            ],

            source=file_type
        )

        db.add(material)

        successful += 1

    batch.successful_rows = successful

    batch.failed_rows = failed

    batch.status = "completed"

    db.commit()

    db.refresh(batch)

    return batch