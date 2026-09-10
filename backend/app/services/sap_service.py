from datetime import datetime
import uuid

from app.models.integration_sync import IntegrationSync
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.national_material import NationalMaterial
from app.services.audit_service import write_audit, snapshot_model
from app.services.classification_service import classify_material
from app.services.cleaning_service import clean_description, normalize_uom, standardize_description
from app.services.duplicate_service import material_code_exists
from app.services.erp_connector import connector_for
from app.services.material_schema_service import canonical_standard_description


async def sync_from_sap(db, cpse_id, connector_name="MOCK", actor_id=None):
    connector = connector_for(connector_name)
    correlation_id = uuid.uuid4().hex
    previous = db.query(IntegrationSync).filter(
        IntegrationSync.cpse_id == cpse_id,
        IntegrationSync.connector == connector.name,
        IntegrationSync.status == "COMPLETED",
    ).order_by(IntegrationSync.id.desc()).first()
    previous_delta_token = previous.delta_token if previous else None
    sync = IntegrationSync(
        cpse_id=cpse_id, source="SAP", connector=connector.name,
        correlation_id=correlation_id, status="RUNNING",
    )
    db.add(sync); db.flush()
    write_audit(db, "SAP_SYNC_STARTED", "IntegrationSync", sync.id, actor_id, {
        "connector": connector.name, "correlation_id": correlation_id,
    }, commit=False)
    db.commit(); db.refresh(sync)

    try:
        rows, delta_token = await connector.fetch_materials(cpse_id, previous_delta_token)
        sync.records_received = len(rows)
        sync.delta_token = delta_token
        seen_codes = set()
        for row in rows:
            code = str(row.get("material_code") or row.get("legacy_material_code") or row.get("MaterialCode") or "").strip().upper()
            desc = str(row.get("description") or row.get("Description") or "").strip()
            if not code or not desc:
                sync.records_failed += 1
                continue
            if code in seen_codes:
                sync.records_skipped += 1
                continue
            seen_codes.add(code)
            cleaned = clean_description(desc)
            supplied_category = row.get("category") or row.get("Category")
            specifications = row.get("specifications") or row.get("Specifications") or {}
            classification = classify_material(cleaned, supplied_category, specifications)
            existing = db.query(Material).filter(Material.cpse_id == cpse_id, Material.material_code == code).with_for_update().first()
            if existing:
                before = snapshot_model(existing)
                updates = {"description": desc, "cleaned_description": cleaned,
                           "normalized_description": standardize_description(cleaned)}
                for target, aliases in {
                    "specifications": ("specifications", "Specifications"),
                    "unit": ("unit", "uom", "Uom"),
                    "manufacturer": ("manufacturer", "Manufacturer"),
                    "model": ("model", "model_number", "Model"),
                }.items():
                    for alias in aliases:
                        if alias in row:
                            updates[target] = normalize_uom(row[alias]) if target == "unit" else row[alias]
                            break
                if not isinstance(updates.get("specifications", {}), dict):
                    sync.records_failed += 1
                    continue
                changed = any(getattr(existing, key) != value for key, value in updates.items())
                if not changed:
                    sync.records_skipped += 1
                    continue
                for key, value in updates.items():
                    setattr(existing, key, value)
                classification = classify_material(cleaned, supplied_category, existing.specifications)
                if existing.classification_source != "MANUAL_REVIEW":
                    existing.category = classification.category
                    existing.subcategory = classification.subcategory
                    existing.classification_confidence = classification.confidence
                    existing.classification_source = classification.source
                    existing.classification_version = classification.rule_version
                existing.recommended_standard_description = canonical_standard_description(
                    cleaned, existing.subcategory, existing.specifications
                )
                existing.matching_status = "NOT_PROCESSED"
                mapping = db.query(MaterialMapping).filter(MaterialMapping.material_id == existing.id).first()
                if mapping:
                    from app.services.identity_service import validate_members
                    validate_members(db, mapping.national_material_id, [existing])
                write_audit(db, "SAP_MATERIAL_UPDATED", "Material", existing.id, actor_id,
                            {"before": before, "after": snapshot_model(existing), "sync_id": sync.id}, commit=False)
                sync.records_updated += 1
                continue
            db.add(Material(
                cpse_id=cpse_id, material_code=code, description=desc,
                original_description=desc, cleaned_description=cleaned,
                normalized_description=standardize_description(cleaned), category=classification.category,
                recommended_standard_description=canonical_standard_description(
                    cleaned, classification.subcategory, specifications
                ),
                subcategory=classification.subcategory,
                classification_confidence=classification.confidence,
                classification_source=classification.source,
                classification_version=classification.rule_version,
                unit=normalize_uom(row.get("unit") or row.get("uom") or row.get("Uom")),
                manufacturer=row.get("manufacturer") or row.get("Manufacturer"),
                model=row.get("model") or row.get("model_number") or row.get("Model"),
                specifications=specifications,
                source=f"SAP_{connector.name}",
            ))
            sync.records_created += 1

        sync.status = "COMPLETED"
        sync.completed_at = datetime.utcnow()
        write_audit(db, "SAP_SYNC_COMPLETED", "IntegrationSync", sync.id, actor_id, {
            "connector": connector.name, "received": sync.records_received,
            "created": sync.records_created, "updated": sync.records_updated,
            "skipped": sync.records_skipped,
            "failed": sync.records_failed, "correlation_id": correlation_id,
        }, commit=False)
        db.commit(); db.refresh(sync)
        return sync
    except Exception as exc:
        sync_id = sync.id
        db.rollback()
        sync = db.query(IntegrationSync).filter(IntegrationSync.id == sync_id).first()
        if sync is None:
            raise
        sync.status = "FAILED"
        sync.error_message = str(exc)[:1000]
        sync.completed_at = datetime.utcnow()
        write_audit(db, "SAP_SYNC_FAILED", "IntegrationSync", sync.id, actor_id, {
            "connector": connector.name, "error": str(exc)[:500], "correlation_id": correlation_id,
        }, commit=False)
        db.commit()
        raise


async def push_mappings_to_sap(db, cpse_id, connector_name="ODATA", actor_id=None):
    connector = connector_for(connector_name)
    rows = db.query(MaterialMapping, Material, NationalMaterial).join(
        Material, Material.id == MaterialMapping.material_id
    ).join(
        NationalMaterial, NationalMaterial.id == MaterialMapping.national_material_id
    ).filter(Material.cpse_id == cpse_id).all()
    payload = [{
        "legacy_material_code": material.material_code,
        "national_material_code": national.national_code,
        "mapping_type": mapping.mapping_type,
    } for mapping, material, national in rows]
    result = await connector.push_national_mappings(cpse_id, payload)
    write_audit(db, "SAP_MAPPINGS_PUSHED", "CPSE", cpse_id, actor_id, {
        "connector": connector.name, "records": len(payload), "status": result.get("status"),
    })
    return result


async def reconcile_mappings_with_sap(db, cpse_id, connector_name="ODATA", actor_id=None):
    connector = connector_for(connector_name)
    local_rows = db.query(MaterialMapping, Material, NationalMaterial).join(
        Material, Material.id == MaterialMapping.material_id
    ).join(
        NationalMaterial, NationalMaterial.id == MaterialMapping.national_material_id
    ).filter(Material.cpse_id == cpse_id).all()
    local = {
        (material.material_code, national.national_code)
        for _mapping, material, national in local_rows
    }
    remote_rows = await connector.fetch_national_mappings(cpse_id)
    remote = {
        (
            str(row.get("legacy_material_code") or row.get("LegacyMaterialCode") or ""),
            str(row.get("national_material_code") or row.get("NationalMaterialCode") or ""),
        )
        for row in remote_rows
    }
    result = {
        "connector": connector.name,
        "cpse_id": cpse_id,
        "in_sync": sorted(local & remote),
        "missing_in_sap": sorted(local - remote),
        "unexpected_in_sap": sorted(remote - local),
    }
    write_audit(db, "SAP_MAPPINGS_RECONCILED", "CPSE", cpse_id, actor_id, {
        "connector": connector.name,
        "in_sync": len(result["in_sync"]),
        "missing_in_sap": len(result["missing_in_sap"]),
        "unexpected_in_sap": len(result["unexpected_in_sap"]),
    })
    return result


async def sync_from_mock_sap(db, cpse_id):
    return await sync_from_sap(db, cpse_id, "MOCK")
