"""Persist recommended and human-approved standard descriptions."""
from alembic import op
import sqlalchemy as sa

revision = "20260911_06"
down_revision = "20260910_05"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("materials", sa.Column("recommended_standard_description", sa.String(1000), nullable=True))
    op.add_column("materials", sa.Column("approved_standard_description", sa.String(1000), nullable=True))
    op.execute("UPDATE materials SET recommended_standard_description = normalized_description WHERE normalized_description IS NOT NULL")
    op.execute(
        "UPDATE materials AS m SET approved_standard_description = n.description "
        "FROM material_mappings AS mm JOIN national_materials AS n ON n.id = mm.national_material_id "
        "WHERE mm.material_id = m.id"
    )


def downgrade():
    op.drop_column("materials", "approved_standard_description")
    op.drop_column("materials", "recommended_standard_description")
