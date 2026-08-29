REQUIRED_COLUMNS = [
    "material_code",
    "description"
]


def validate_columns(columns):

    missing = []

    normalized_columns = [
        str(column).strip().lower()
        for column in columns
    ]

    for column in REQUIRED_COLUMNS:

        if column not in normalized_columns:

            missing.append(column)

    return missing


def validate_material_row(row):

    errors = []

    material_code = row.get(
        "material_code"
    )

    description = row.get(
        "description"
    )

    if not material_code:

        errors.append(
            "material_code is required"
        )

    if not description:

        errors.append(
            "description is required"
        )

    return errors