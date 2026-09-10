"""Procurement history and expanded taxonomy."""
from alembic import op
import sqlalchemy as sa

revision = "20260910_04"
down_revision = "20260909_03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("procurement_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("order_number", sa.String(100), nullable=False),
        sa.Column("line_number", sa.String(30), nullable=False),
        sa.Column("supplier", sa.String(255), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("uom", sa.String(50), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("lead_time_days", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("cpse_id", "order_number", "line_number", name="uq_procurement_line"))
    op.create_index("ix_procurement_records_cpse_id", "procurement_records", ["cpse_id"])
    op.create_index("ix_procurement_records_material_id", "procurement_records", ["material_id"])
    taxonomy = sa.table("material_taxonomy_codes", sa.column("level"), sa.column("name"), sa.column("code"), sa.column("parent_name"))
    op.bulk_insert(taxonomy, [
        {"level": "SUBCATEGORY", "name": name, "code": code, "parent_name": parent}
        for name, code, parent in [
            ("LIGHTING", "LGT", "ELECTRICAL EQUIPMENT"),
            ("SWITCHGEAR", "SWG", "ELECTRICAL EQUIPMENT"),
            ("CABLE ACCESSORIES", "CAC", "ELECTRICAL EQUIPMENT"),
            ("TRANSMISSION", "TRN", "BEARINGS & POWER TRANSMISSION"),
            ("SEALS", "SEA", "PIPES & FITTINGS"),
        ]])


def downgrade():
    op.drop_table("procurement_records")
    op.execute("DELETE FROM material_taxonomy_codes WHERE level = 'SUBCATEGORY' AND code IN ('LGT','SWG','CAC','TRN','SEA')")
