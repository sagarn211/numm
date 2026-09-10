"""Track who submitted a match for maker-checker enforcement."""
from alembic import op
import sqlalchemy as sa

revision = "20260911_07"
down_revision = "20260911_06"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("material_matches", sa.Column("submitted_by", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_material_matches_submitted_by_users", "material_matches", "users", ["submitted_by"], ["id"])
    op.create_index("ix_material_matches_submitted_by", "material_matches", ["submitted_by"])


def downgrade():
    op.drop_index("ix_material_matches_submitted_by", table_name="material_matches")
    op.drop_constraint("fk_material_matches_submitted_by_users", "material_matches", type_="foreignkey")
    op.drop_column("material_matches", "submitted_by")
