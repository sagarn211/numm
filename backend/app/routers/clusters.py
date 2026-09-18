from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.material_cluster import MaterialCluster
from app.models.material_cluster_member import MaterialClusterMember
from app.models.material_match import MaterialMatch
from app.models.material_mapping import MaterialMapping
from app.models.user import User
from app.models.material import Material
from app.models.cpse import CPSE
from app.services.audit_service import write_audit
from app.services.cluster_governance_service import (CLUSTER_STATUSES, _cluster_payload, approve_cluster,
    generate_proposed_clusters, get_clusters, has_active_identity_overlap, submit_cluster)
from app.utils.rbac import require_permission

router = APIRouter(prefix="/api/clusters", tags=["Cluster Governance"])

@router.post("/generate")
def generate(db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    rows = generate_proposed_clusters(db, user.id)
    return {"created": len(rows), "clusters": [_cluster_payload(db, row) for row in rows]}

@router.get("")
def list_clusters(status: str | None = None, page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(require_permission("approval.read"))):
    key = status.upper() if status else None
    if key and key not in CLUSTER_STATUSES: raise HTTPException(400, "Invalid cluster status")
    return get_clusters(db, key, page, limit)

@router.get("/detail/{cluster_id}")
def detail(cluster_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.read"))):
    row = db.get(MaterialCluster, cluster_id)
    if not row: raise HTTPException(404, "Cluster not found")
    return _cluster_payload(db, row)

def editable(db, cluster_id):
    row = db.query(MaterialCluster).filter(MaterialCluster.id == cluster_id).with_for_update().first()
    if not row: raise HTTPException(404, "Cluster not found")
    if row.status in {"APPROVED", "REJECTED"}: raise HTTPException(409, "Resolved cluster cannot be edited")
    return row


def ensure_identity_membership_is_available(db, cluster_id: int, material_id: int) -> None:
    """A material has one active identity-governance unit at a time."""
    db.query(Material).filter(Material.id == material_id).with_for_update().first()
    if has_active_identity_overlap(db, [material_id], excluded_cluster_id=cluster_id):
        raise HTTPException(409, "Material already belongs to another active identity cluster")

@router.post("/{cluster_id}/start-review")
def start_review(cluster_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    row = editable(db, cluster_id)
    if row.status == "PROPOSED": row.status="UNDER_REVIEW"; row.reviewed_by=user.id; row.reviewed_at=datetime.utcnow(); row.version += 1
    write_audit(db,"CLUSTER_REVIEW_STARTED","MaterialCluster",row.id,user.id,{},commit=False); db.commit()
    return _cluster_payload(db,row)

@router.patch("/{cluster_id}/members/{material_id}")
def classify_member(cluster_id: int, material_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    row=editable(db,cluster_id); member=db.query(MaterialClusterMember).filter_by(cluster_id=cluster_id,material_id=material_id).first()
    if not member: raise HTTPException(404,"Cluster member not found")
    kind=str(payload.get("member_type", member.member_type)).upper()
    if kind not in {"IDENTITY","FUNCTIONAL_ALTERNATIVE"}: raise HTTPException(400,"Invalid member type")
    if kind == "IDENTITY" and member.relationship_type == "FUNCTIONAL_EQUIVALENT": raise HTTPException(409,"Functional-equivalent evidence cannot be identity-mapped")
    if kind == "IDENTITY" and member.membership_status == "ACTIVE":
        ensure_identity_membership_is_available(db, cluster_id, material_id)
    member.member_type=kind; row.version += 1
    write_audit(db,"CLUSTER_MEMBER_CLASSIFIED","MaterialCluster",row.id,user.id,{"material_id":material_id,"member_type":kind},commit=False); db.commit()
    return _cluster_payload(db,row)

@router.post("/{cluster_id}/members/{material_id}/remove")
def remove_member(cluster_id: int, material_id: int, payload: dict | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    row=editable(db,cluster_id); member=db.query(MaterialClusterMember).filter_by(cluster_id=cluster_id,material_id=material_id).first()
    if not member: raise HTTPException(404,"Cluster member not found")
    member.membership_status="REMOVED"; member.removed_by=user.id; member.removed_at=datetime.utcnow(); member.removal_reason=(payload or {}).get("reason"); row.version += 1
    write_audit(db,"CLUSTER_MEMBER_REMOVED","MaterialCluster",row.id,user.id,{"material_id":material_id,"reason":member.removal_reason},commit=False); db.commit()
    return _cluster_payload(db,row)

@router.post("/{cluster_id}/members/{material_id}/restore")
def restore_member(cluster_id: int, material_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    row=editable(db,cluster_id); member=db.query(MaterialClusterMember).filter_by(cluster_id=cluster_id,material_id=material_id).first()
    if not member: raise HTTPException(404,"Cluster member not found")
    if member.member_type == "IDENTITY":
        ensure_identity_membership_is_available(db, cluster_id, material_id)
    member.membership_status="ACTIVE"; member.removed_by=None; member.removed_at=None; member.removal_reason=None; row.version += 1
    write_audit(db,"CLUSTER_MEMBER_RESTORED","MaterialCluster",row.id,user.id,{"material_id":material_id},commit=False); db.commit()
    return _cluster_payload(db,row)

@router.post("/{cluster_id}/canonical")
def canonical(cluster_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    row=editable(db,cluster_id); material_id=payload.get("material_id")
    member=db.query(MaterialClusterMember).filter_by(cluster_id=cluster_id,material_id=material_id,member_type="IDENTITY",membership_status="ACTIVE").first()
    if not member: raise HTTPException(400,"Canonical material must be an active identity member")
    row.canonical_material_id=material_id; row.version += 1
    write_audit(db,"CLUSTER_CANONICAL_SELECTED","MaterialCluster",row.id,user.id,{"material_id":material_id},commit=False); db.commit(); return _cluster_payload(db,row)

@router.post("/{cluster_id}/submit")
def submit(cluster_id: int, payload: dict | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    row=editable(db,cluster_id); return submit_cluster(db,row,user.id,(payload or {}).get("comment"))

@router.post("/{cluster_id}/return")
def return_changes(cluster_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    reason=(payload.get("comment") or "").strip()
    if not reason: raise HTTPException(400,"Return reason is required")
    row=editable(db,cluster_id)
    if row.status != "READY_FOR_APPROVAL": raise HTTPException(409,"Only submitted clusters can be returned")
    row.status="UNDER_REVIEW"; row.review_comment=reason; row.version += 1
    write_audit(db,"CLUSTER_RETURNED_FOR_CHANGES","MaterialCluster",row.id,user.id,{"comment":reason},commit=False); db.commit(); return _cluster_payload(db,row)

@router.post("/{cluster_id}/reject")
def reject(cluster_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    reason=(payload.get("comment") or "").strip()
    if not reason: raise HTTPException(400,"Rejection reason is required")
    row=editable(db,cluster_id); row.status="REJECTED"; row.rejected_by=user.id; row.rejected_at=datetime.utcnow(); row.approval_comment=reason; row.version += 1
    write_audit(db,"CLUSTER_REJECTED","MaterialCluster",row.id,user.id,{"comment":reason},commit=False); db.commit(); return _cluster_payload(db,row)

@router.post("/{cluster_id}/approve")
def approve(cluster_id: int, payload: dict | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("approval.review"))):
    return approve_cluster(db,cluster_id,user.id,(payload or {}).get("comment"))

@router.get("/queues/identity")
def identity_queue(page:int=Query(1,ge=1),limit:int=Query(25,ge=1,le=100),db:Session=Depends(get_db),user:User=Depends(require_permission("approval.read"))):
    return get_clusters(db,"READY_FOR_APPROVAL",page,limit)

@router.get("/queues/functional")
def functional_queue(page:int=Query(1,ge=1), limit:int=Query(25,ge=1,le=100), db:Session=Depends(get_db),user:User=Depends(require_permission("approval.read"))):
    query=db.query(MaterialMatch).filter(MaterialMatch.status=="PENDING",MaterialMatch.classification=="FUNCTIONAL_EQUIVALENT")
    total=query.count(); rows=query.order_by(MaterialMatch.final_score.desc(), MaterialMatch.id.desc()).offset((page-1)*limit).limit(limit).all()
    ids={value for row in rows for value in (row.material_a_id,row.material_b_id)}
    materials={m.id:m for m in db.query(Material).filter(Material.id.in_(ids)).all()} if ids else {}
    cpse_codes={c.id:c.code for c in db.query(CPSE).filter(CPSE.id.in_({m.cpse_id for m in materials.values()})).all()} if materials else {}
    def source(material_id):
        m=materials.get(material_id)
        return {"id":material_id,"material_code":m.material_code if m else None,"description":m.description if m else None,
                "specifications":m.specifications or {} if m else {},"cpse":cpse_codes.get(m.cpse_id) if m else None,"unit":m.unit if m else None}
    return {"items":[{"match_id":r.id,"confidence":r.final_score,"explanation":r.explanation,
                       "material_a":source(r.material_a_id),"material_b":source(r.material_b_id)} for r in rows],
            "page":page,"limit":limit,"total":total,"pages":max(1,(total+limit-1)//limit)}

@router.get("/queues/conflicts")
def conflicts(db:Session=Depends(get_db),user:User=Depends(require_permission("approval.read"))):
    rows=[]
    for cluster in db.query(MaterialCluster).filter(MaterialCluster.status.in_(["PROPOSED","UNDER_REVIEW","READY_FOR_APPROVAL"])).all():
        payload=_cluster_payload(db,cluster)
        if payload["mapping_destination"]["state"]=="CONFLICT":
            rows.append({"id":payload["id"],"cluster_code":payload["cluster_code"],"risk_level":payload["risk_level"],
                         "proposed_canonical_description":payload["proposed_canonical_description"],"identity_members":payload["identity_members"],
                         "mapping_destination":payload["mapping_destination"],"conflicts":payload["conflicts"]})
    return {"items":rows}

@router.post("/batch-approve")
def batch_approve(payload:dict,db:Session=Depends(get_db),user:User=Depends(require_permission("approval.review"))):
    result={"submitted":0,"approved":0,"already_resolved":0,"moved_to_conflict":0,"failed":0,"results":[]}
    for cluster_id in payload.get("cluster_ids",[]):
        result["submitted"] += 1
        try:
            cluster=db.get(MaterialCluster,cluster_id)
            if not cluster or cluster.status!="READY_FOR_APPROVAL" or cluster.risk_level!="LOW": raise HTTPException(409,"Only ready low-risk clusters can be batch approved")
            outcome=approve_cluster(db,cluster_id,user.id,payload.get("comment")); state=outcome["status"]
            result["approved" if state=="APPROVED" else "already_resolved"] += 1; result["results"].append({"cluster_id":cluster_id,"status":state})
        except HTTPException as exc:
            db.rollback(); key="moved_to_conflict" if exc.status_code==409 and "conflict" in str(exc.detail).lower() else "failed"; result[key]+=1; result["results"].append({"cluster_id":cluster_id,"status":"CONFLICT" if key=="moved_to_conflict" else "FAILED","detail":exc.detail})
    return result

@router.get("/approval-counts")
def approval_counts(db:Session=Depends(get_db),user:User=Depends(require_permission("approval.read"))):
    identity=db.query(MaterialCluster).filter(MaterialCluster.status=="READY_FOR_APPROVAL").count()
    functional=db.query(MaterialMatch).filter(MaterialMatch.status=="PENDING",MaterialMatch.classification=="FUNCTIONAL_EQUIVALENT").count()
    conflict=len(conflicts(db,user)["items"])
    return {"identity_approvals":identity,"functional_substitutions":functional,"mapping_conflicts":conflict,"actionable_total":identity+functional+conflict}
