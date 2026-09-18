from datetime import datetime
from fastapi import HTTPException
from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.models.material_mapping import MaterialMapping
from app.models.approval_action import ApprovalAction
from app.services.national_code_service import create_national_material
from app.services.mapping_service import map_material
from app.services.audit_service import write_audit
from app.services.conflict_resolution_service import propose_canonical, unresolved_critical_conflicts

def approve_match(
    db, match_id, reviewer_id=None, comment=None, canonical_values=None,
    acknowledge_critical_conflicts=False, acknowledge_functional_equivalent=False,
    automated=False,
):
    match = db.query(MaterialMatch).filter(
        MaterialMatch.id == match_id
    ).with_for_update().first()
    if not match:
        raise HTTPException(404, "Match not found")
    if match.status != "PENDING":
        raise HTTPException(409, f"Match has already been {match.status.lower()}")
    if reviewer_id is not None and match.submitted_by == reviewer_id:
        raise HTTPException(403, "Maker-checker rule: you cannot approve your own submitted recommendation")
    if automated and match.classification != "EXACT":
        raise HTTPException(409, "Only exact matches can be approved automatically")
    if match.classification == "FUNCTIONAL_EQUIVALENT" and not acknowledge_functional_equivalent:
        raise HTTPException(409, "Functional-equivalent mappings require explicit reviewer acknowledgement")
    if match.classification == "FUNCTIONAL_EQUIVALENT":
        # Approval records an engineering recommendation, never an identity merge.
        if not comment or not comment.strip():
            raise HTTPException(400, "Document the application and limitations for this substitution recommendation")
        previous = match.status
        match.status = "APPROVED"
        match.reviewed_at = datetime.utcnow()
        match.reviewed_by = reviewer_id
        db.add(ApprovalAction(match_id=match.id, reviewer_id=reviewer_id,
            action="APPROVE_SUBSTITUTION", comment=comment,
            previous_status=previous, new_status="APPROVED",
            details={"identity_merge": False, "conditions": comment}))
        write_audit(db, "SUBSTITUTION_RECOMMENDATION_APPROVED", "MaterialMatch", match.id,
            reviewer_id, {"conditions": comment, "material_a_id": match.material_a_id,
                          "material_b_id": match.material_b_id, "identity_merge": False}, commit=False)
        db.commit(); db.refresh(match)
        return match

    materials = db.query(Material).filter(Material.id.in_([match.material_a_id, match.material_b_id])).order_by(Material.id).with_for_update().all()
    if len(materials) != 2:
        raise HTTPException(409, "Both source materials must exist before approval")
    if automated:
        from app.services.material_schema_service import material_readiness
        if not all(material_readiness(material)["ready"] for material in materials):
            raise HTTPException(409, "Automatic approval requires a supported category schema and complete engineering attributes")
        from app.services.conflict_resolution_service import canonical_specs, CRITICAL_FIELDS
        evidence = [canonical_specs(material) for material in materials]
        missing = (set(evidence[0]) ^ set(evidence[1])) & CRITICAL_FIELDS
        if missing:
            raise HTTPException(409, "Automatic approval requires critical attributes on both records")
    proposal = propose_canonical(materials, canonical_values)
    critical = unresolved_critical_conflicts(proposal, canonical_values)
    if critical:
        raise HTTPException(409, {"message": "Critical material conflicts require explicit resolution", "conflicts": critical})

    existing_mappings = db.query(MaterialMapping).filter(
        MaterialMapping.material_id.in_([match.material_a_id, match.material_b_id])
    ).all()
    existing_national_ids = {item.national_material_id for item in existing_mappings}
    if len(existing_national_ids) > 1:
        raise HTTPException(409, "Source materials are already mapped to different National Material Codes")
    if existing_national_ids:
        raise HTTPException(409, "Source materials are already mapped to a National Material Code")

    previous = match.status
    match.status = "APPROVED"
    match.reviewed_at = datetime.utcnow()
    match.reviewed_by = reviewer_id

    db.add(ApprovalAction(
        match_id=match.id, reviewer_id=reviewer_id,
        action="AUTO_APPROVE" if automated else "APPROVE",
        comment=comment or ("System-approved exact match" if automated else None),
        previous_status=previous, new_status="APPROVED",
        details={"canonical_values": canonical_values or {}, "proposal": proposal},
    ))

    created_national = False
    national, created_national = create_national_material(
        db,
        proposal["description"], proposal["category"], proposal["unit"],
        proposal["specifications"], proposal.get("subcategory"),
        {
            "source_material_ids": proposal["source_material_ids"],
            "source_records": proposal["source_records"],
            "conflicts": proposal["conflicts"],
        },
        actor_id=None, commit=False, return_created=True,
    )
    national_id = national.id

    mapping_type = "AUTO_EXACT" if automated else match.classification
    map_material(db, match.material_a_id, national_id, mapping_type, reviewer_id)
    map_material(db, match.material_b_id, national_id, mapping_type, reviewer_id)
    write_audit(
        db, "MATCH_AUTO_APPROVED" if automated else "MATCH_APPROVED",
        "MaterialMatch", match.id, reviewer_id,
        {
            "classification": match.classification,
            "national_material_id": national_id,
            "canonical_proposal": proposal,
            "critical_conflicts_acknowledged": acknowledge_critical_conflicts,
            "functional_equivalent_acknowledged": acknowledge_functional_equivalent,
            "automated": automated,
        },
        commit=False,
    )
    if created_national:
        write_audit(db, "NATIONAL_MATERIAL_CREATED", "NationalMaterial", national_id, reviewer_id, {
            "source_material_ids": proposal["source_material_ids"], "approval_match_id": match.id,
        }, commit=False)
    db.commit()
    db.refresh(match)
    return match


def auto_approve_exact_matches(db, min_score=0.95):
    """Approve only high-confidence exact matches that pass every conflict guard."""
    candidates = db.query(MaterialMatch).filter(
        MaterialMatch.status == "PENDING",
        MaterialMatch.classification == "EXACT",
        MaterialMatch.final_score >= min_score,
    ).order_by(MaterialMatch.final_score.desc(), MaterialMatch.id).all()
    approved_ids = []
    skipped = []
    for candidate in candidates:
        try:
            approve_match(
                db,
                candidate.id,
                reviewer_id=None,
                comment=f"Automatic exact-match approval at score {candidate.final_score:.4f}",
                automated=True,
            )
            approved_ids.append(candidate.id)
        except HTTPException as exc:
            db.rollback()
            skipped.append({"match_id": candidate.id, "reason": str(exc.detail)})
    return {"approved_ids": approved_ids, "skipped": skipped}

def reject_match(db, match_id, reviewer_id=None, comment=None):
    match = db.query(MaterialMatch).filter(
        MaterialMatch.id == match_id
    ).with_for_update().first()
    if not match:
        raise HTTPException(404, "Match not found")
    if match.status != "PENDING":
        raise HTTPException(409, f"Match has already been {match.status.lower()}")
    if reviewer_id is not None and match.submitted_by == reviewer_id:
        raise HTTPException(403, "Maker-checker rule: you cannot reject your own submitted recommendation")
    if reviewer_id is not None and not (comment or "").strip():
        raise HTTPException(400, "A rejection reason is required")

    previous = match.status
    match.status = "REJECTED"
    match.reviewed_at = datetime.utcnow()
    match.reviewed_by = reviewer_id
    db.add(ApprovalAction(
        match_id=match.id, reviewer_id=reviewer_id, action="REJECT",
        comment=comment, previous_status=previous, new_status="REJECTED"
    ))
    write_audit(db, "MATCH_REJECTED", "MaterialMatch", match.id, reviewer_id, {"comment": comment}, commit=False)
    db.commit()
    db.refresh(match)
    return match
