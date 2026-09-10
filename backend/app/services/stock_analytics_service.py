"""Comparable stock and demand totals; quantities never cross UOM boundaries."""
from collections import defaultdict
from datetime import datetime
from app.models.inventory import Inventory
from app.models.demand_record import DemandRecord
from app.models.material_mapping import MaterialMapping
from app.services.cleaning_service import normalize_uom


def stock_analytics(db, period=None):
    period = period or datetime.utcnow().strftime("%Y-%m")
    mapping = dict(db.query(MaterialMapping.material_id, MaterialMapping.national_material_id).all())
    def identity(material_id):
        return ("NATIONAL", mapping[material_id]) if material_id in mapping else ("SOURCE", material_id)
    groups = defaultdict(lambda: {"available": 0.0, "required": 0.0})
    for stock in db.query(Inventory).all():
        key = (*identity(stock.material_id), normalize_uom(stock.uom))
        groups[key]["available"] += max(stock.available_quantity - stock.reserved_quantity, 0)
    for demand in db.query(DemandRecord).filter(DemandRecord.period == period).all():
        key = (*identity(demand.material_id), normalize_uom(demand.uom))
        groups[key]["required"] += demand.required_quantity
    totals = defaultdict(lambda: {"available": 0.0, "required": 0.0, "surplus": 0.0, "shortage": 0.0})
    rows = []
    for (kind, identity_id, uom), values in groups.items():
        values = {**values, "surplus": max(values["available"] - values["required"], 0),
                  "shortage": max(values["required"] - values["available"], 0)}
        for field, value in values.items():
            totals[uom][field] += value
        rows.append({"identity_type": kind, "identity_id": identity_id, "uom": uom, "period": period, **values})
    return {"period": period, "by_unit": [{"uom": unit, **values} for unit, values in sorted(totals.items(), key=lambda item: item[0] or '')], "materials": rows}
