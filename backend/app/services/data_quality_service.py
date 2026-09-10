from app.models.material import Material
from app.models.material_mapping import MaterialMapping

def quality_metrics(db):
    from app.services.material_schema_service import material_readiness
    materials = db.query(Material).all()
    total = len(materials)
    if not total:
        return {
            "total_materials": 0,
            "description_completeness": 0,
            "category_completeness": 0,
            "uom_completeness": 0,
            "manufacturer_completeness": 0,
            "mapping_coverage": 0,
            "data_quality_score": 0,
            "automatic_classification_coverage": 0,
            "technical_readiness_percent": 0,
            "technical_issues": [],
        }

    def pct(n): return round(n * 100 / total, 2)

    desc = pct(sum(bool(m.description) for m in materials))
    category = pct(sum(bool(m.category and m.category != "UNCLASSIFIED") for m in materials))
    uom = pct(sum(bool(m.unit) for m in materials))
    manufacturer = pct(sum(bool(m.manufacturer) for m in materials))
    mapped_ids = {x.material_id for x in db.query(MaterialMapping).all()}
    mapping = pct(sum(m.id in mapped_ids for m in materials))
    automatic_classification = pct(sum(m.classification_source == "RULE_ENGINE" for m in materials))
    readiness = [material_readiness(m) for m in materials]
    score = round((desc + category + uom + manufacturer + mapping + automatic_classification) / 6, 2)

    return {
        "technical_readiness_percent": pct(sum(row["ready"] for row in readiness)),
        "technical_issues": [row for row in readiness if not row["ready"]][:100],
        "total_materials": total,
        "description_completeness": desc,
        "category_completeness": category,
        "uom_completeness": uom,
        "manufacturer_completeness": manufacturer,
        "mapping_coverage": mapping,
        "data_quality_score": score,
        "automatic_classification_coverage": automatic_classification,
    }
