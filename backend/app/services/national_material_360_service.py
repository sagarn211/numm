"""Database-backed National Material 360 aggregation."""
from collections import defaultdict

from sqlalchemy import or_

from app.models.approval_action import ApprovalAction
from app.models.audit_log import AuditLog
from app.models.cpse import CPSE
from app.models.demand_record import DemandRecord
from app.models.integration_sync import IntegrationSync
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.material_match import MaterialMatch
from app.models.national_material import NationalMaterial
from app.models.procurement_record import ProcurementRecord
from app.services.audit_service import snapshot_model
from app.services.procurement_intelligence_service import procurement_opportunities


def national_material_360(db, national_id):
    national = db.query(NationalMaterial).filter(NationalMaterial.id == national_id).first()
    if not national:
        return None
    mappings = db.query(MaterialMapping).filter(MaterialMapping.national_material_id == national_id).order_by(MaterialMapping.id).all()
    mapping_ids = [row.id for row in mappings]
    material_ids = [row.material_id for row in mappings]
    materials = db.query(Material).filter(Material.id.in_(material_ids)).all() if material_ids else []
    material_by_id = {row.id: row for row in materials}
    cpse_ids = sorted({row.cpse_id for row in materials})
    cpse_codes = dict(db.query(CPSE.id, CPSE.code).filter(CPSE.id.in_(cpse_ids)).all()) if cpse_ids else {}
    inventory = db.query(Inventory).filter(Inventory.material_id.in_(material_ids)).order_by(Inventory.cpse_id, Inventory.warehouse).all() if material_ids else []
    demand = db.query(DemandRecord).filter(DemandRecord.material_id.in_(material_ids)).order_by(DemandRecord.period.desc()).all() if material_ids else []
    procurement = db.query(ProcurementRecord).filter(ProcurementRecord.material_id.in_(material_ids)).order_by(ProcurementRecord.period.desc(), ProcurementRecord.id.desc()).limit(250).all() if material_ids else []
    matches = db.query(MaterialMatch).filter(or_(
        MaterialMatch.material_a_id.in_(material_ids), MaterialMatch.material_b_id.in_(material_ids)
    )).order_by(MaterialMatch.id.desc()).limit(250).all() if material_ids else []
    match_ids = [row.id for row in matches]
    approvals = db.query(ApprovalAction).filter(ApprovalAction.match_id.in_(match_ids)).order_by(ApprovalAction.id.desc()).all() if match_ids else []
    audits = db.query(AuditLog).filter(or_(
        (AuditLog.entity_type == "NationalMaterial") & (AuditLog.entity_id == national_id),
        (AuditLog.entity_type == "Material") & AuditLog.entity_id.in_(material_ids),
        (AuditLog.entity_type == "MaterialMapping") & AuditLog.entity_id.in_(mapping_ids),
        (AuditLog.entity_type == "MaterialMatch") & AuditLog.entity_id.in_(match_ids),
    )).order_by(AuditLog.id.desc()).limit(250).all() if material_ids else db.query(AuditLog).filter(
        AuditLog.entity_type == "NationalMaterial", AuditLog.entity_id == national_id
    ).order_by(AuditLog.id.desc()).limit(250).all()
    syncs = db.query(IntegrationSync).filter(IntegrationSync.cpse_id.in_(cpse_ids)).order_by(
        IntegrationSync.cpse_id, IntegrationSync.id.desc()
    ).all() if cpse_ids else []
    latest_sync = {}
    for row in syncs:
        latest_sync.setdefault(row.cpse_id, row)

    stock_by_uom = defaultdict(lambda: {"available": 0.0, "reserved": 0.0, "ready_to_use": 0.0})
    inventory_rows = []
    for row in inventory:
        summary = stock_by_uom[row.uom]
        summary["available"] += float(row.available_quantity or 0)
        summary["reserved"] += float(row.reserved_quantity or 0)
        summary["ready_to_use"] += max(float(row.available_quantity or 0) - float(row.reserved_quantity or 0), 0)
        inventory_rows.append({**snapshot_model(row), "cpse_code": cpse_codes.get(row.cpse_id)})

    supplier_summary = defaultdict(lambda: {"orders": set(), "quantity": 0.0, "spend": 0.0})
    for row in procurement:
        key = (row.supplier, row.currency, row.uom)
        supplier_summary[key]["orders"].add(row.order_number)
        supplier_summary[key]["quantity"] += row.quantity
        supplier_summary[key]["spend"] += row.quantity * row.unit_price
    opportunities = [row for row in procurement_opportunities(db) if row["national_material_id"] == national_id]
    return {
        "material": snapshot_model(national),
        "legacy_mappings": [
            {**snapshot_model(mapping), "material": snapshot_model(material_by_id[mapping.material_id]),
             "cpse_code": cpse_codes.get(material_by_id[mapping.material_id].cpse_id)}
            for mapping in mappings if mapping.material_id in material_by_id
        ],
        "inventory": inventory_rows,
        "stock_summary": [{"uom": uom, **{key: round(value, 4) for key, value in values.items()}}
                          for uom, values in sorted(stock_by_uom.items())],
        "demand": [{**snapshot_model(row), "cpse_code": cpse_codes.get(row.cpse_id)} for row in demand],
        "procurement_history": [{**snapshot_model(row), "cpse_code": cpse_codes.get(row.cpse_id)} for row in procurement],
        "supplier_summary": [
            {"supplier": key[0], "currency": key[1], "uom": key[2], "order_count": len(value["orders"]),
             "quantity": round(value["quantity"], 4), "spend": round(value["spend"], 2)}
            for key, value in supplier_summary.items()
        ],
        "ai_matching_history": [snapshot_model(row) for row in matches],
        "approval_history": [snapshot_model(row) for row in approvals],
        "audit_history": [snapshot_model(row) for row in audits],
        "sap_sync_status": [{**snapshot_model(row), "cpse_code": cpse_codes.get(cpse_id)} for cpse_id, row in latest_sync.items()],
        "lineage": {
            "legacy_material_ids": material_ids,
            "ai_match_ids": match_ids,
            "approval_action_ids": [row.id for row in approvals],
            "mapping_ids": mapping_ids,
            "national_material_id": national_id,
            "provenance": national.provenance or {},
        },
        "procurement_opportunity": opportunities[0] if opportunities else None,
    }
