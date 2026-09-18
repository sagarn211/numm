"""Persist reviewer-owned identity clusters and memberships."""
from alembic import op
import sqlalchemy as sa
revision = "20260914_09"
down_revision = "20260914_08"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("material_clusters", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("status", sa.String(30), nullable=False, server_default="PROPOSED"), sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("reviewed_at", sa.DateTime()), sa.Column("national_material_id", sa.Integer(), sa.ForeignKey("national_materials.id")), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_material_clusters_status", "material_clusters", ["status"])
    op.create_table("material_cluster_members", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("cluster_id", sa.Integer(), sa.ForeignKey("material_clusters.id", ondelete="CASCADE"), nullable=False), sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False), sa.Column("member_type", sa.String(30), nullable=False, server_default="IDENTITY"), sa.Column("classification", sa.String(40)), sa.Column("added_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("cluster_id", "material_id", name="uq_cluster_material_member"))
    op.create_index("ix_material_cluster_members_cluster_id", "material_cluster_members", ["cluster_id"]); op.create_index("ix_material_cluster_members_material_id", "material_cluster_members", ["material_id"])
def downgrade():
    op.drop_table("material_cluster_members"); op.drop_table("material_clusters")
