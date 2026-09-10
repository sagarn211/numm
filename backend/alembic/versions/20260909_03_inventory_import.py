"""add inventory import metadata

Revision ID: 20260909_03
Revises: 20260909_02
"""
from alembic import op
import sqlalchemy as sa


revision = "20260909_03"
down_revision = "20260909_02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "import_batches",
        sa.Column("import_type", sa.String(30), nullable=False, server_default="MATERIAL"),
    )
    op.add_column(
        "import_batches",
        sa.Column("conflict_policy", sa.String(30), nullable=False, server_default="REJECT"),
    )


def downgrade():
    op.drop_column("import_batches", "conflict_policy")
    op.drop_column("import_batches", "import_type")
