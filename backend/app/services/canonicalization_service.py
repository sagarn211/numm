import re


ALIASES = {
    "legacy_material_code": "material_code",
    "legacy_code": "material_code",
    "code": "material_code",
    "material_description": "description",
    "material_desc": "description",
    "desc": "description",
    "uom": "unit",
    "model_number": "model",
}

INVENTORY_ALIASES = {
    "code": "material_code",
    "legacy_code": "material_code",
    "legacy_material_code": "material_code",
    "cpse": "cpse_code",
    "depot": "warehouse",
    "warehouse_depot": "warehouse",
    "available": "available_quantity",
    "quantity": "available_quantity",
    "stock_quantity": "available_quantity",
    "reserved": "reserved_quantity",
    "uom": "unit",
    "cost": "unit_cost",
    "price": "unit_cost",
}

def _normalize_key(key):
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def canonicalize_row(row: dict):
    data = {}
    for key, value in row.items():
        normalized = _normalize_key(key)
        canonical = ALIASES.get(normalized, normalized)
        if canonical in data and data[canonical] is not None:
            continue
        data[canonical] = value
    return {
        "material_code": data.get("material_code"),
        "description": data.get("description"),
        "category": data.get("category"),
        "subcategory": data.get("subcategory"),
        "unit": data.get("unit"),
        "manufacturer": data.get("manufacturer"),
        "model": data.get("model"),
        "specifications": data.get("specifications") or {},
    }


def canonicalize_inventory_row(row: dict):
    data = {}
    for key, value in row.items():
        normalized = _normalize_key(key)
        canonical = INVENTORY_ALIASES.get(normalized, normalized)
        if canonical in data and data[canonical] is not None:
            continue
        data[canonical] = value
    return {
        "cpse_code": data.get("cpse_code"),
        "material_code": data.get("material_code"),
        "warehouse": data.get("warehouse"),
        "available_quantity": data.get("available_quantity"),
        "reserved_quantity": data.get("reserved_quantity"),
        "unit": data.get("unit"),
        "unit_cost": data.get("unit_cost"),
    }
