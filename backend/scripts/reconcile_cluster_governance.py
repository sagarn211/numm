"""Read-only legacy governance reconciliation report.

Run with ``python scripts/reconcile_cluster_governance.py`` in the backend
container. It deliberately has no --apply mode: historical pair decisions are
evidence and require an explicitly designed, separately approved repair action.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from app.config.database import SessionLocal
from app.models.material_cluster import MaterialCluster
from app.models.material_cluster_member import MaterialClusterMember
from app.models.material_mapping import MaterialMapping
from app.models.material_match import MaterialMatch

def main():
    db = SessionLocal()
    try:
        mappings = db.query(MaterialMapping).all()
        by_material = {}
        for row in mappings: by_material.setdefault(row.material_id, []).append(row.national_material_id)
        same_nmc_pending = 0
        for match in db.query(MaterialMatch).filter(MaterialMatch.status == "PENDING").all():
            a, b = by_material.get(match.material_a_id, []), by_material.get(match.material_b_id, [])
            if a and b and set(a) == set(b): same_nmc_pending += 1
        anomalies = []
        for cluster in db.query(MaterialCluster).all():
            members = db.query(MaterialClusterMember).filter(MaterialClusterMember.cluster_id == cluster.id).all()
            active_identity = [m for m in members if m.member_type == "IDENTITY" and m.membership_status == "ACTIVE"]
            if cluster.status in {"READY_FOR_APPROVAL", "APPROVED"} and not active_identity:
                anomalies.append({"cluster_id": cluster.id, "problem": "resolved cluster without active identity member"})
            if any(m.member_type == "IDENTITY" and m.relationship_type == "FUNCTIONAL_EQUIVALENT" for m in members):
                anomalies.append({"cluster_id": cluster.id, "problem": "functional evidence classified as identity"})
        print({
            "mode": "REPORT_ONLY", "pending_pairs_already_resolved_by_same_nmc": same_nmc_pending,
            "materials_with_multiple_active_nmc_mappings": {k:v for k,v in by_material.items() if len(set(v)) > 1},
            "duplicate_mapping_rows": len(mappings) - len(by_material), "cluster_member_anomalies": anomalies,
        })
    finally: db.close()

if __name__ == "__main__": main()
