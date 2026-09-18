"""Build review clusters from persisted AI recommendation pairs."""
from collections import Counter, defaultdict

from app.models.cpse import CPSE
from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.models.material_mapping import MaterialMapping
from app.services.conflict_resolution_service import propose_canonical


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, value):
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left, right):
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def duplicate_clusters(db, status="PENDING"):
    query = db.query(MaterialMatch).filter(MaterialMatch.classification.in_([
        "EXACT", "NEAR_DUPLICATE", "FUNCTIONAL_EQUIVALENT"
    ]))
    if status:
        query = query.filter(MaterialMatch.status == status)
    mappings = dict(db.query(MaterialMapping.material_id, MaterialMapping.national_material_id).all())
    # A pair already resolved by the same National Material is not actionable work.
    edges = [edge for edge in query.order_by(MaterialMatch.id).all() if not (
        mappings.get(edge.material_a_id) and mappings.get(edge.material_a_id) == mappings.get(edge.material_b_id)
    )]
    visual = _UnionFind()
    identity = _UnionFind()
    for edge in edges:
        visual.union(edge.material_a_id, edge.material_b_id)
        if edge.classification != "FUNCTIONAL_EQUIVALENT":
            identity.union(edge.material_a_id, edge.material_b_id)
    grouped_edges = defaultdict(list)
    for edge in edges:
        grouped_edges[visual.find(edge.material_a_id)].append(edge)
    material_ids = {value for edge in edges for value in (edge.material_a_id, edge.material_b_id)}
    materials = {row.id: row for row in db.query(Material).filter(Material.id.in_(material_ids)).all()} if material_ids else {}
    cpse_ids = {row.cpse_id for row in materials.values()}
    cpse_codes = dict(db.query(CPSE.id, CPSE.code).filter(CPSE.id.in_(cpse_ids)).all()) if cpse_ids else {}
    results = []
    for cluster_number, (root, cluster_edges) in enumerate(sorted(grouped_edges.items()), 1):
        member_ids = sorted({value for edge in cluster_edges for value in (edge.material_a_id, edge.material_b_id)})
        identity_groups = defaultdict(list)
        for member_id in member_ids:
            identity_groups[identity.find(member_id)].append(member_id)
        safe_groups = [sorted(group) for group in identity_groups.values() if len(group) > 1]
        strongest_group = max(safe_groups, key=len, default=[])
        proposal = propose_canonical([materials[value] for value in strongest_group]) if strongest_group else None
        counts = Counter(edge.classification for edge in cluster_edges)
        results.append({
            "cluster_id": f"C{root}",
            "sequence": cluster_number,
            "member_count": len(member_ids),
            "cluster_confidence": round(sum(edge.final_score for edge in cluster_edges) / len(cluster_edges), 4),
            "classification_counts": dict(counts),
            "members": [{
                "id": row.id, "material_code": row.material_code, "description": row.description,
                "category": row.category, "unit": row.unit, "cpse_id": row.cpse_id,
                "cpse_code": cpse_codes.get(row.cpse_id, f"CPSE-{row.cpse_id}"),
            } for row in (materials[value] for value in member_ids if value in materials)],
            "identity_components": safe_groups,
            "functional_equivalent_edges": [{
                "match_id": edge.id, "material_a_id": edge.material_a_id,
                "material_b_id": edge.material_b_id, "score": edge.final_score,
                "explanation": edge.explanation,
            } for edge in cluster_edges if edge.classification == "FUNCTIONAL_EQUIVALENT"],
            "recommended_canonical_identity": proposal,
            "technical_conflicts": proposal.get("conflicts", []) if proposal else [],
            "automatic_cluster_merge_allowed": False,
        })
    return results
