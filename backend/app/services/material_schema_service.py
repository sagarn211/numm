"""Versioned starting schemas; missing engineering evidence stays unknown."""
from app.services.conflict_resolution_service import canonical_specs
from app.services.cleaning_service import standardize_description

SCHEMA_VERSION = "2026.09.10"
REQUIRED = {
    "BOLTS": ("material_grade", "diameter", "length"),
    "NUTS": ("material_grade", "diameter"),
    "PIPES": ("material_grade", "diameter"),
    "BALL VALVES": ("material_grade", "nominal_size", "pressure_class"),
    "GATE VALVES": ("material_grade", "nominal_size", "pressure_class"),
    "MOTORS": ("voltage", "power"),
    "TRANSFORMERS": ("voltage", "capacity"),
    "LIGHTING": ("voltage", "power"),
    "SWITCHGEAR": ("voltage", "rating"),
    "PUMPS": ("capacity", "power"),
    "BEARINGS": ("part_number",),
}


def canonical_standard_description(description, subcategory, specifications=None):
    """Create a bounded family template from explicit attributes only."""
    specs = {str(key).lower(): value for key, value in (specifications or {}).items() if value not in (None, "")}

    def first(*keys):
        return next((str(specs[key]).upper() for key in keys if key in specs), None)

    templates = {
        "BOLTS": ("HEXAGONAL HEAD BOLT", (first("diameter", "size"), first("length"), first("material_grade", "grade"))),
        "NUTS": ("HEXAGONAL NUT", (first("diameter", "size"), first("material_grade", "grade"))),
        "WASHERS": ("WASHER", (first("diameter", "size"), first("material_grade", "grade"))),
        "BALL VALVES": ("BALL VALVE", (first("nominal_diameter", "nominal_size", "size"), first("pressure_rating", "pressure_class", "pressure"), first("body_material", "material_grade", "grade"), first("connection"))),
        "GATE VALVES": ("GATE VALVE", (first("nominal_diameter", "nominal_size", "size"), first("pressure_rating", "pressure_class", "pressure"), first("body_material", "material_grade", "grade"), first("connection"))),
        "MOTORS": (first("motor_type") or "INDUCTION MOTOR", (first("power"), first("voltage"), first("phase"), first("frequency"), first("rpm"), first("frame"), first("ip_rating"), first("efficiency_class"))),
        "BEARINGS": ("BEARING", (first("bearing_designation", "part_number"), first("bore"), first("outer_diameter"), first("width"), first("seal_designation"))),
        "PUMPS": ((first("pump_type") + " PUMP") if first("pump_type") else "PUMP", (first("flow", "capacity"), first("head"), first("power"), first("rpm"), first("body_material", "material_grade"))),
        "PIPES": ("PIPE", (first("nominal_diameter", "diameter", "size"), first("schedule"), first("pressure_rating", "pressure_class"), first("body_material", "material_grade", "grade"), first("standard"))),
        "FLANGES": ("FLANGE", (first("nominal_diameter", "diameter", "size"), first("pressure_rating", "pressure_class"), first("body_material", "material_grade", "grade"), first("standard"))),
    }
    template = templates.get((subcategory or "").upper())
    if not template:
        return standardize_description(description)
    base, values = template
    explicit = [value for value in values if value]
    return " | ".join([base, *explicit]) if explicit else base


def material_readiness(material):
    specs = canonical_specs(material)
    required = REQUIRED.get(material.subcategory or "")
    missing = [field for field in (required or ()) if specs.get(field) is None or not str(specs[field]).strip()]
    return {"material_id": material.id, "material_code": material.material_code,
            "schema_version": SCHEMA_VERSION, "schema_supported": required is not None,
            "missing_attributes": missing, "ready": required is not None and not missing,
            "suggested_description": canonical_standard_description(material.description, material.subcategory, specs)}
