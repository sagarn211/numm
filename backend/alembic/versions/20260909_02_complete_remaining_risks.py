"""complete remaining ALADIN risks

Revision ID: 20260909_02
Revises: 20260908_01
"""
from alembic import op
import sqlalchemy as sa


revision = "20260909_02"
down_revision = "20260908_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "material_taxonomy_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(3), nullable=False),
        sa.Column("parent_name", sa.String(150)),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("level", "name", name="uq_taxonomy_level_name"),
        sa.UniqueConstraint("level", "code", name="uq_taxonomy_level_code"),
    )
    taxonomy = sa.table(
        "material_taxonomy_codes",
        sa.column("level", sa.String), sa.column("name", sa.String),
        sa.column("code", sa.String), sa.column("parent_name", sa.String),
    )
    op.bulk_insert(taxonomy, [
        {"level": "CATEGORY", "name": "FASTENERS", "code": "FST", "parent_name": None},
        {"level": "CATEGORY", "name": "VALVES & ACTUATORS", "code": "VLV", "parent_name": None},
        {"level": "CATEGORY", "name": "PUMPS & COMPRESSORS", "code": "PMP", "parent_name": None},
        {"level": "CATEGORY", "name": "PIPES & FITTINGS", "code": "PIP", "parent_name": None},
        {"level": "CATEGORY", "name": "ELECTRICAL EQUIPMENT", "code": "ELC", "parent_name": None},
        {"level": "CATEGORY", "name": "BEARINGS & POWER TRANSMISSION", "code": "BRG", "parent_name": None},
        {"level": "CATEGORY", "name": "UNCLASSIFIED", "code": "GEN", "parent_name": None},
        {"level": "SUBCATEGORY", "name": "BOLTS", "code": "BLT", "parent_name": "FASTENERS"},
        {"level": "SUBCATEGORY", "name": "NUTS", "code": "NUT", "parent_name": "FASTENERS"},
        {"level": "SUBCATEGORY", "name": "WASHERS", "code": "WSH", "parent_name": "FASTENERS"},
        {"level": "SUBCATEGORY", "name": "BALL VALVES", "code": "BLV", "parent_name": "VALVES & ACTUATORS"},
        {"level": "SUBCATEGORY", "name": "GATE VALVES", "code": "GTV", "parent_name": "VALVES & ACTUATORS"},
        {"level": "SUBCATEGORY", "name": "PUMPS", "code": "PMP", "parent_name": "PUMPS & COMPRESSORS"},
        {"level": "SUBCATEGORY", "name": "TRANSFORMERS", "code": "TRF", "parent_name": "ELECTRICAL EQUIPMENT"},
        {"level": "SUBCATEGORY", "name": "MOTORS", "code": "MTR", "parent_name": "ELECTRICAL EQUIPMENT"},
        {"level": "SUBCATEGORY", "name": "CABLES", "code": "CBL", "parent_name": "ELECTRICAL EQUIPMENT"},
        {"level": "SUBCATEGORY", "name": "BEARINGS", "code": "BRG", "parent_name": "BEARINGS & POWER TRANSMISSION"},
        {"level": "SUBCATEGORY", "name": "PIPES", "code": "PIP", "parent_name": "PIPES & FITTINGS"},
        {"level": "SUBCATEGORY", "name": "FLANGES", "code": "FLG", "parent_name": "PIPES & FITTINGS"},
        {"level": "SUBCATEGORY", "name": "UNSPECIFIED", "code": "GEN", "parent_name": None},
    ])

    op.create_table(
        "material_mapping_conflicts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_mapping_id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("national_material_id", sa.Integer(), nullable=False),
        sa.Column("mapping_type", sa.String(50), nullable=False),
        sa.Column("approved_by", sa.Integer()),
        sa.Column("original_created_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("quarantined_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.execute(
        "INSERT INTO material_mapping_conflicts "
        "(original_mapping_id, material_id, national_material_id, mapping_type, approved_by, original_created_at, reason) "
        "SELECT id, material_id, national_material_id, mapping_type, approved_by, created_at, 'MULTIPLE_NATIONAL_CODES' FROM ("
        "SELECT id, material_id, national_material_id, mapping_type, approved_by, created_at, "
        "row_number() OVER (PARTITION BY material_id ORDER BY id DESC) AS position "
        "FROM material_mappings) ranked WHERE position > 1"
    )
    op.execute(
        "DELETE FROM material_mappings WHERE id IN ("
        "SELECT original_mapping_id FROM material_mapping_conflicts)"
    )
    op.drop_constraint("uq_material_national_mapping", "material_mappings", type_="unique")
    op.create_unique_constraint(
        "uq_material_single_national_mapping", "material_mappings", ["material_id"]
    )

    op.create_table(
        "import_dead_letters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("task_id", sa.String(255)),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_import_dead_letters_batch_id", "import_dead_letters", ["batch_id"])


def downgrade():
    op.drop_index("ix_import_dead_letters_batch_id", table_name="import_dead_letters")
    op.drop_table("import_dead_letters")
    op.drop_constraint("uq_material_single_national_mapping", "material_mappings", type_="unique")
    op.execute(
        "INSERT INTO material_mappings "
        "(id, material_id, national_material_id, mapping_type, approved_by, created_at) "
        "SELECT original_mapping_id, material_id, national_material_id, mapping_type, approved_by, original_created_at "
        "FROM material_mapping_conflicts"
    )
    op.execute(
        "SELECT setval(pg_get_serial_sequence('material_mappings', 'id'), "
        "COALESCE((SELECT MAX(id) FROM material_mappings), 1))"
    )
    op.create_unique_constraint(
        "uq_material_national_mapping", "material_mappings", ["material_id", "national_material_id"]
    )
    op.drop_table("material_mapping_conflicts")
    op.drop_table("material_taxonomy_codes")
