"""Explainable inventory, demand, and procurement intelligence.

All quantities remain partitioned by UOM and all prices by currency. The score
is a transparent prioritization rule, not an ML prediction or savings claim.
"""
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException

from app.models.cpse import CPSE
from app.models.demand_record import DemandRecord
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.national_material import NationalMaterial
from app.models.procurement_record import ProcurementRecord
from app.services.cleaning_service import normalize_uom


def _identity_context(db, period=None):
    period = period or datetime.utcnow().strftime("%Y-%m")
    nationals = {row.id: row for row in db.query(NationalMaterial).filter(NationalMaterial.status == "ACTIVE").all()}
    material_rows = db.query(Material.id, Material.cpse_id, MaterialMapping.national_material_id).join(
        MaterialMapping, MaterialMapping.material_id == Material.id
    ).all()
    material_to_national = {material_id: national_id for material_id, _, national_id in material_rows}
    material_to_cpse = {material_id: cpse_id for material_id, cpse_id, _ in material_rows}
    stock = defaultdict(lambda: defaultdict(float))
    for row in db.query(Inventory).filter(Inventory.material_id.in_(material_to_national)).all() if material_to_national else []:
        national_id = material_to_national[row.material_id]
        national = nationals.get(national_id)
        if national and normalize_uom(row.uom) == normalize_uom(national.unit):
            stock[national_id][row.cpse_id] += max(float(row.available_quantity or 0) - float(row.reserved_quantity or 0), 0)
    demand = defaultdict(lambda: defaultdict(float))
    if material_to_national:
        for row in db.query(DemandRecord).filter(
            DemandRecord.material_id.in_(material_to_national), DemandRecord.period == period
        ).all():
            national_id = material_to_national[row.material_id]
            national = nationals.get(national_id)
            if national and normalize_uom(row.uom) == normalize_uom(national.unit):
                demand[national_id][row.cpse_id] += float(row.required_quantity or 0)
    purchases = defaultdict(list)
    if material_to_national:
        for row in db.query(ProcurementRecord).filter(ProcurementRecord.material_id.in_(material_to_national)).all():
            purchases[material_to_national[row.material_id]].append(row)
    cpse_codes = dict(db.query(CPSE.id, CPSE.code).all())
    return period, nationals, material_to_national, material_to_cpse, stock, demand, purchases, cpse_codes


def procurement_opportunities(db, period=None):
    period, nationals, _, _, stock, demand, purchases, cpse_codes = _identity_context(db, period)
    results = []
    for national_id, national in nationals.items():
        all_cpses = set(stock[national_id]) | set(demand[national_id]) | {row.cpse_id for row in purchases[national_id]}
        if not all_cpses:
            continue
        surplus = sum(max(stock[national_id][cpse] - demand[national_id][cpse], 0) for cpse in all_cpses)
        shortage = sum(max(demand[national_id][cpse] - stock[national_id][cpse], 0) for cpse in all_cpses)
        reusable = min(surplus, shortage)
        demand_cpses = {cpse for cpse, quantity in demand[national_id].items() if quantity > 0}
        suppliers = {row.supplier for row in purchases[national_id]}
        prices = defaultdict(list)
        for row in purchases[national_id]:
            prices[row.currency].append(float(row.unit_price))
        price_ranges = {
            currency: {"minimum": min(values), "maximum": max(values),
                       "variance_percent": round((max(values) - min(values)) * 100 / min(values), 2) if min(values) > 0 else None}
            for currency, values in prices.items()
        }
        participation_points = min(len(demand_cpses), 5) * 5
        overlap_points = min(max(len(demand_cpses) - 1, 0), 4) * 5
        reuse_points = min(reusable / shortage, 1) * 25 if shortage else 0
        supplier_points = min(max(len(suppliers) - 1, 0), 3) * 5
        comparable_variances = [row["variance_percent"] for row in price_ranges.values() if row["variance_percent"] is not None]
        price_points = min(max(comparable_variances, default=0) / 25, 1) * 15
        score = round(participation_points + overlap_points + reuse_points + supplier_points + price_points, 1)
        if len(demand_cpses) < 2 and reusable <= 0 and len(suppliers) < 2:
            continue
        remaining = max(shortage - reusable, 0)
        recommendation_parts = []
        if reusable > 0:
            recommendation_parts.append(f"Review cross-CPSE stock for up to {reusable:g} {national.unit} before buying")
        if len(demand_cpses) >= 2:
            recommendation_parts.append(f"{len(demand_cpses)} CPSEs have demand in {period}; consider a consolidated sourcing review")
        if len(suppliers) >= 2:
            recommendation_parts.append(f"Historical supply is fragmented across {len(suppliers)} suppliers")
        results.append({
            "national_material_id": national_id,
            "national_code": national.national_code,
            "description": national.description,
            "period": period,
            "uom": normalize_uom(national.unit),
            "participating_cpses": sorted(cpse_codes.get(cpse, str(cpse)) for cpse in demand_cpses),
            "aggregate_demand": round(sum(demand[national_id].values()), 4),
            "available_stock": round(sum(stock[national_id].values()), 4),
            "cross_cpse_reuse_potential": round(reusable, 4),
            "net_fresh_procurement_demand": round(remaining, 4),
            "supplier_count": len(suppliers),
            "price_ranges": price_ranges,
            "opportunity_score": score,
            "score_formula": "CPSE participation 25 + demand overlap 20 + reusable stock ratio 25 + supplier fragmentation 15 + within-currency price variance 15",
            "recommendation": ". ".join(recommendation_parts) + ".",
        })
    return sorted(results, key=lambda row: (-row["opportunity_score"], row["national_code"] or ""))


def reuse_before_buy(db, national_id, requesting_cpse_id, requested_quantity, uom, period=None):
    period, nationals, _, _, stock, demand, purchases, cpse_codes = _identity_context(db, period)
    national = nationals.get(national_id)
    if not national:
        raise HTTPException(404, "Active National Material not found")
    base_uom = normalize_uom(national.unit)
    if normalize_uom(uom) != base_uom:
        raise HTTPException(400, f"Requested UOM must match the National Material base unit ({base_uom})")
    own = stock[national_id].get(requesting_cpse_id, 0)
    own_use = min(requested_quantity, own)
    after_own = max(requested_quantity - own_use, 0)
    external_rows = [
        {"cpse_id": cpse, "cpse_code": cpse_codes.get(cpse, str(cpse)), "available": round(quantity, 4)}
        for cpse, quantity in stock[national_id].items()
        if cpse != requesting_cpse_id and quantity > 0
    ]
    external_total = sum(row["available"] for row in external_rows)
    cross_reuse = min(after_own, external_total)
    remaining = max(after_own - cross_reuse, 0)
    other_demand = [
        {"cpse_id": cpse, "cpse_code": cpse_codes.get(cpse, str(cpse)), "quantity": round(quantity, 4)}
        for cpse, quantity in demand[national_id].items() if cpse != requesting_cpse_id and quantity > 0
    ]
    suppliers = sorted({row.supplier for row in purchases[national_id]})
    return {
        "national_material_id": national_id,
        "national_code": national.national_code,
        "description": national.description,
        "period": period,
        "uom": base_uom,
        "requested_quantity": requested_quantity,
        "own_available": round(own, 4),
        "own_stock_applicable": round(own_use, 4),
        "other_cpse_stock": sorted(external_rows, key=lambda row: -row["available"]),
        "cross_cpse_reuse_potential": round(cross_reuse, 4),
        "remaining_fresh_procurement": round(remaining, 4),
        "other_open_demand": other_demand,
        "potential_consolidated_procurement": round(remaining + sum(row["quantity"] for row in other_demand), 4),
        "historical_suppliers": suppliers,
        "decision_required": True,
        "available_actions": ["REQUEST_AVAILABLE_STOCK", "CONTINUE_FRESH_PROCUREMENT", "JOIN_CONSOLIDATED_REVIEW", "CANCEL"],
        "warning": "Decision support only. No stock transfer, reservation, or procurement has been executed.",
    }
