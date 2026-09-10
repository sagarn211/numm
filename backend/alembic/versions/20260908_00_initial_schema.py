"""baseline schema before remediation features

Revision ID: 20260908_00
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "20260908_00"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cpses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("sector", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_cpses_id", "cpses", ["id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="officer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("cpse_id", sa.Integer(), nullable=False),
        sa.Column("total_rows", sa.Integer(), server_default="0"),
        sa.Column("successful_rows", sa.Integer(), server_default="0"),
        sa.Column("failed_rows", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(50), server_default="processing"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_import_batches_id", "import_batches", ["id"])

    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=False),
        sa.Column("material_code", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(150)),
        sa.Column("unit", sa.String(50)),
        sa.Column("manufacturer", sa.String(200)),
        sa.Column("model", sa.String(200)),
        sa.Column("specifications", sa.JSON()),
        sa.Column("source", sa.String(50), server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_materials_id", "materials", ["id"])
    op.create_index("ix_materials_material_code", "materials", ["material_code"])

    op.create_table(
        "national_materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("national_code", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(150)),
        sa.Column("unit", sa.String(50)),
        sa.Column("specifications", sa.Text()),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_national_materials_id", "national_materials", ["id"])

    op.create_table(
        "material_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_a_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("material_b_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("semantic_score", sa.Float(), server_default="0"),
        sa.Column("attribute_score", sa.Float(), server_default="0"),
        sa.Column("final_score", sa.Float(), server_default="0"),
        sa.Column("classification", sa.String(50)),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_material_matches_id", "material_matches", ["id"])

    op.create_table(
        "material_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("national_material_id", sa.Integer(), sa.ForeignKey("national_materials.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_material_mappings_id", "material_mappings", ["id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer()),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100)),
        sa.Column("entity_id", sa.Integer()),
        sa.Column("details", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])


def downgrade():
    for table in (
        "audit_logs", "material_mappings", "material_matches",
        "national_materials", "materials", "import_batches", "users", "cpses",
    ):
        op.drop_table(table)
