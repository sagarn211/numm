"""Complete persisted cluster governance fields without changing historical rows."""
from alembic import op
import sqlalchemy as sa

revision = "20260914_10"
down_revision = "20260914_09"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("material_clusters", sa.Column("cluster_code", sa.String(40), nullable=True))
    op.create_index("ix_material_clusters_cluster_code", "material_clusters", ["cluster_code"], unique=True)
    for name, target in (("submitted_by", "users.id"), ("approved_by", "users.id"), ("rejected_by", "users.id"), ("canonical_material_id", "materials.id")):
        op.add_column("material_clusters", sa.Column(name, sa.Integer(), sa.ForeignKey(target), nullable=True))
    for name in ("submitted_at", "approved_at", "rejected_at"):
        op.add_column("material_clusters", sa.Column(name, sa.DateTime(), nullable=True))
    op.add_column("material_clusters", sa.Column("risk_level", sa.String(10), nullable=False, server_default="MEDIUM"))
    op.add_column("material_clusters", sa.Column("review_comment", sa.Text(), nullable=True))
    op.add_column("material_clusters", sa.Column("approval_comment", sa.Text(), nullable=True))
    op.add_column("material_clusters", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    member_columns = (
        ("relationship_type", sa.String(40)), ("membership_status", sa.String(20)),
        ("ai_match_id", sa.Integer()), ("confidence", sa.Float()),
        ("added_by", sa.Integer()), ("removed_by", sa.Integer()),
        ("removed_at", sa.DateTime()), ("removal_reason", sa.Text()), ("updated_at", sa.DateTime()),
    )
    for name, type_ in member_columns:
        if name == "ai_match_id": op.add_column("material_cluster_members", sa.Column(name, type_, sa.ForeignKey("material_matches.id"), nullable=True))
        elif name in {"added_by", "removed_by"}: op.add_column("material_cluster_members", sa.Column(name, type_, sa.ForeignKey("users.id"), nullable=True))
        else: op.add_column("material_cluster_members", sa.Column(name, type_, nullable=True))
    op.execute("UPDATE material_cluster_members SET membership_status = 'ACTIVE' WHERE membership_status IS NULL")
    op.execute("UPDATE material_cluster_members SET updated_at = added_at WHERE updated_at IS NULL")
    op.alter_column("material_cluster_members", "membership_status", nullable=False, server_default="ACTIVE")
    op.alter_column("material_cluster_members", "updated_at", nullable=False)

def downgrade():
    # Downgrade intentionally omitted: governance history must not be dropped casually.
    pass
