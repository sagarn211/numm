import re


def normalize_text(value):

    if value is None:

        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def normalize_material(row):

    return {

        "material_code": str(
            row.get(
                "material_code",
                ""
            )
        ).strip(),

        "description": normalize_text(
            row.get("description")
        ),

        "category": normalize_text(
            row.get("category")
        ),

        "unit": normalize_text(
            row.get("unit")
        ),

        "manufacturer": normalize_text(
            row.get("manufacturer")
        ),

        "model": normalize_text(
            row.get("model")
        )
    }