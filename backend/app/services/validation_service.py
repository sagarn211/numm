REQUIRED_COLUMNS = {"material_code", "description"}

def validate_columns(columns):
    return sorted(REQUIRED_COLUMNS - set(columns))

def validate_material_row(row):
    errors = []
    if not row.get("material_code"):
        errors.append(("material_code", "MISSING_MATERIAL_CODE", "Material code is required"))
    if not row.get("description"):
        errors.append(("description", "MISSING_DESCRIPTION", "Description is required"))
    return errors
