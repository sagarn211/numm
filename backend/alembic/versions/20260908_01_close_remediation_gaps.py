"""close ALADIN remediation gaps

Revision ID: 20260908_01
Revises: 20260908_00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260908_01"
down_revision = "20260908_00"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("cpse_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_cpse_id", "users", "cpses", ["cpse_id"], ["id"])

    for column in (
        sa.Column("import_batch_id", sa.Integer(), nullable=True),
        sa.Column("original_description", sa.String(1000), nullable=True),
        sa.Column("cleaned_description", sa.String(1000), nullable=True),
        sa.Column("normalized_description", sa.String(1000), nullable=True),
        sa.Column("subcategory", sa.String(150), nullable=True),
        sa.Column("classification_confidence", sa.Float(), nullable=True),
        sa.Column("classification_source", sa.String(50), nullable=True),
        sa.Column("classification_version", sa.String(50), nullable=True),
        sa.Column("status", sa.String(40), server_default="ACTIVE", nullable=False),
        sa.Column("matching_status", sa.String(40), server_default="NOT_PROCESSED", nullable=False),
    ):
        op.add_column("materials", column)
    op.create_foreign_key("fk_materials_import_batch", "materials", "import_batches", ["import_batch_id"], ["id"])
    op.create_index("ix_materials_import_batch_id", "materials", ["import_batch_id"])
    op.create_index("ix_materials_subcategory", "materials", ["subcategory"])
    op.create_index("ix_materials_category", "materials", ["category"])
    op.create_index("ix_materials_cpse_id", "materials", ["cpse_id"])
    op.create_unique_constraint("uq_cpse_material_code", "materials", ["cpse_id", "material_code"])

    op.alter_column(
        "national_materials", "national_code", existing_type=sa.String(100),
        nullable=True,
    )
    op.alter_column(
        "national_materials", "specifications", existing_type=sa.Text(),
        type_=sa.JSON(), postgresql_using="CASE WHEN specifications IS NULL THEN NULL ELSE json_build_object('text', specifications) END",
    )
    op.add_column("national_materials", sa.Column("subcategory", sa.String(150), nullable=True))
    op.add_column("national_materials", sa.Column("provenance", sa.JSON(), nullable=True))
    op.add_column("national_materials", sa.Column("code_scheme_version", sa.String(20), server_default="1", nullable=False))
    op.alter_column("national_materials", "code_scheme_version", server_default="2")
    op.add_column("national_materials", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_national_materials_national_code", "national_materials", ["national_code"], unique=True)

    op.add_column("material_matches", sa.Column("fuzzy_score", sa.Float(), nullable=True))
    op.add_column("material_matches", sa.Column("attributes_a", sa.JSON(), nullable=True))
    op.add_column("material_matches", sa.Column("attributes_b", sa.JSON(), nullable=True))
    op.add_column("material_matches", sa.Column("explanation", sa.Text(), nullable=True))
    op.add_column("material_matches", sa.Column("model_name", sa.String(255), nullable=True))
    op.add_column("material_matches", sa.Column("matcher_version", sa.String(80), nullable=True))
    op.add_column("material_matches", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("material_matches", sa.Column("reviewed_by", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_material_matches_reviewed_by", "material_matches", "users", ["reviewed_by"], ["id"])
    op.execute("UPDATE material_matches SET final_score = 0 WHERE final_score IS NULL")
    op.execute("UPDATE material_matches SET classification = 'NO_MATCH' WHERE classification IS NULL")
    op.execute("UPDATE material_matches SET status = 'PENDING' WHERE status IS NULL")
    op.execute("UPDATE material_matches SET status = UPPER(status)")
    op.execute("UPDATE material_matches SET classification = UPPER(classification)")
    op.execute("DELETE FROM material_matches WHERE material_a_id = material_b_id")
    op.execute(
        "UPDATE material_matches SET "
        "material_a_id = CASE WHEN material_a_id < material_b_id THEN material_a_id ELSE material_b_id END, "
        "material_b_id = CASE WHEN material_a_id < material_b_id THEN material_b_id ELSE material_a_id END"
    )
    op.execute(
        "DELETE FROM material_matches duplicate USING material_matches keeper "
        "WHERE duplicate.material_a_id = keeper.material_a_id "
        "AND duplicate.material_b_id = keeper.material_b_id "
        "AND duplicate.id > keeper.id"
    )
    op.alter_column("material_matches", "final_score", existing_type=sa.Float(), nullable=False)
    op.alter_column("material_matches", "classification", existing_type=sa.String(50), nullable=False)
    op.alter_column("material_matches", "status", existing_type=sa.String(50), type_=sa.String(40), nullable=False)
    op.create_check_constraint("ck_material_match_ordered_pair", "material_matches", "material_a_id < material_b_id")
    op.create_unique_constraint("uq_material_match_pair", "material_matches", ["material_a_id", "material_b_id"])
    op.create_index("ix_material_matches_material_a_id", "material_matches", ["material_a_id"])
    op.create_index("ix_material_matches_material_b_id", "material_matches", ["material_b_id"])

    op.add_column("material_mappings", sa.Column("mapping_type", sa.String(50), server_default="MANUAL", nullable=False))
    op.add_column("material_mappings", sa.Column("approved_by", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_material_mappings_approved_by", "material_mappings", "users", ["approved_by"], ["id"])
    op.create_unique_constraint("uq_material_national_mapping", "material_mappings", ["material_id", "national_material_id"])
    op.create_index("ix_material_mappings_material_id", "material_mappings", ["material_id"])
    op.create_index("ix_material_mappings_national_material_id", "material_mappings", ["national_material_id"])

    for column in (
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("warning_rows", sa.Integer(), server_default="0"),
        sa.Column("idempotency_key", sa.String(120), nullable=True),
        sa.Column("processed_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("progress_percent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_stage", sa.String(50), nullable=True),
        sa.Column("cancellation_requested", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
    ):
        op.add_column("import_batches", column)
    op.create_foreign_key("fk_import_batches_cpse_id", "import_batches", "cpses", ["cpse_id"], ["id"])
    op.create_foreign_key("fk_import_batches_requested_by", "import_batches", "users", ["requested_by"], ["id"])
    op.create_index("ix_import_batches_idempotency_key", "import_batches", ["idempotency_key"], unique=True)

    op.alter_column(
        "audit_logs", "details", existing_type=sa.Text(), type_=sa.JSON(),
        postgresql_using="CASE WHEN details IS NULL THEN NULL ELSE json_build_object('message', details) END",
    )
    op.execute("UPDATE audit_logs SET entity_type = 'UNKNOWN' WHERE entity_type IS NULL")
    op.alter_column("audit_logs", "entity_type", existing_type=sa.String(100), nullable=False)
    op.create_foreign_key("fk_audit_logs_user_id", "audit_logs", "users", ["user_id"], ["id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    op.create_table(
        "import_errors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(120)), sa.Column("raw_value", sa.Text()),
        sa.Column("error_code", sa.String(120), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), server_default="ERROR", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_import_errors_id", "import_errors", ["id"])
    op.create_index("ix_import_errors_batch_id", "import_errors", ["batch_id"])

    op.create_table(
        "approval_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("material_matches.id"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(50), nullable=False), sa.Column("comment", sa.Text()),
        sa.Column("previous_status", sa.String(40)), sa.Column("new_status", sa.String(40), nullable=False),
        sa.Column("details", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_approval_actions_id", "approval_actions", ["id"])
    op.create_index("ix_approval_actions_match_id", "approval_actions", ["match_id"])

    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("warehouse", sa.String(255), server_default="MAIN", nullable=False),
        sa.Column("available_quantity", sa.Float(), server_default="0", nullable=False),
        sa.Column("reserved_quantity", sa.Float(), server_default="0", nullable=False),
        sa.Column("uom", sa.String(50), server_default="EA", nullable=False),
        sa.Column("unit_cost", sa.Float()),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("material_id", "warehouse", name="uq_inventory_material_warehouse"),
    )
    for name, columns in (("ix_inventory_id", ["id"]), ("ix_inventory_cpse_id", ["cpse_id"]), ("ix_inventory_material_id", ["material_id"])):
        op.create_index(name, "inventory", columns)

    op.create_table(
        "material_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_number", sa.String(80), unique=True),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("requesting_cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=False),
        sa.Column("status", sa.String(40), server_default="DRAFT", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime()), sa.Column("approved_at", sa.DateTime()),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_index("ix_material_requests_id", "material_requests", ["id"])
    op.create_index("ix_material_requests_request_number", "material_requests", ["request_number"], unique=True)

    op.create_table(
        "request_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("material_requests.id"), nullable=False),
        sa.Column("national_material_id", sa.Integer(), sa.ForeignKey("national_materials.id"), nullable=False),
        sa.Column("requested_quantity", sa.Float(), nullable=False),
        sa.Column("uom", sa.String(50), server_default="EA", nullable=False),
    )
    op.create_index("ix_request_items_id", "request_items", ["id"])
    op.create_index("ix_request_items_request_id", "request_items", ["request_id"])
    op.create_index("ix_request_items_national_material_id", "request_items", ["national_material_id"])

    op.create_table(
        "stock_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_item_id", sa.Integer(), sa.ForeignKey("request_items.id"), nullable=False),
        sa.Column("inventory_id", sa.Integer(), sa.ForeignKey("inventory.id"), nullable=False),
        sa.Column("source_cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=False),
        sa.Column("allocated_quantity", sa.Float(), nullable=False),
        sa.Column("status", sa.String(40), server_default="PROPOSED", nullable=False),
    )
    for name, columns in (("ix_stock_allocations_id", ["id"]), ("ix_stock_allocations_request_item_id", ["request_item_id"]), ("ix_stock_allocations_inventory_id", ["inventory_id"]), ("ix_stock_allocations_source_cpse_id", ["source_cpse_id"])):
        op.create_index(name, "stock_allocations", columns)

    op.create_table(
        "integration_syncs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(50), server_default="SAP", nullable=False),
        sa.Column("cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("records_received", sa.Integer(), server_default="0"),
        sa.Column("records_created", sa.Integer(), server_default="0"),
        sa.Column("records_updated", sa.Integer(), server_default="0"),
        sa.Column("records_skipped", sa.Integer(), server_default="0"),
        sa.Column("records_failed", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(40), server_default="RUNNING", nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("connector", sa.String(50), server_default="MOCK", nullable=False),
        sa.Column("correlation_id", sa.String(80)), sa.Column("delta_token", sa.String(500)),
    )
    op.create_index("ix_integration_syncs_id", "integration_syncs", ["id"])
    op.create_index("ix_integration_syncs_correlation_id", "integration_syncs", ["correlation_id"])

    op.create_table(
        "demand_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("period", sa.String(40), nullable=False),
        sa.Column("required_quantity", sa.Float(), nullable=False),
        sa.Column("uom", sa.String(50), server_default="EA", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_demand_records_id", "demand_records", ["id"])
    op.create_index("ix_demand_records_cpse_id", "demand_records", ["cpse_id"])
    op.create_index("ix_demand_records_material_id", "demand_records", ["material_id"])


def downgrade():
    for table in ("demand_records", "integration_syncs", "stock_allocations", "request_items", "material_requests", "inventory", "approval_actions", "import_errors"):
        op.drop_table(table)

    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_constraint("fk_audit_logs_user_id", "audit_logs", type_="foreignkey")
    op.alter_column("audit_logs", "details", existing_type=sa.JSON(), type_=sa.Text(), postgresql_using="details::text")
    op.alter_column("audit_logs", "entity_type", existing_type=sa.String(100), nullable=True)

    op.drop_index("ix_import_batches_idempotency_key", table_name="import_batches")
    op.drop_constraint("fk_import_batches_requested_by", "import_batches", type_="foreignkey")
    op.drop_constraint("fk_import_batches_cpse_id", "import_batches", type_="foreignkey")
    for column in ("confirmed_at", "requested_by", "error_message", "cancellation_requested", "current_stage", "progress_percent", "processed_rows", "idempotency_key", "warning_rows", "file_path"):
        op.drop_column("import_batches", column)

    for index in ("ix_material_mappings_national_material_id", "ix_material_mappings_material_id"):
        op.drop_index(index, table_name="material_mappings")
    op.drop_constraint("uq_material_national_mapping", "material_mappings", type_="unique")
    op.drop_constraint("fk_material_mappings_approved_by", "material_mappings", type_="foreignkey")
    op.drop_column("material_mappings", "approved_by")
    op.drop_column("material_mappings", "mapping_type")

    for index in ("ix_material_matches_material_b_id", "ix_material_matches_material_a_id"):
        op.drop_index(index, table_name="material_matches")
    op.drop_constraint("uq_material_match_pair", "material_matches", type_="unique")
    op.drop_constraint("ck_material_match_ordered_pair", "material_matches", type_="check")
    op.drop_constraint("fk_material_matches_reviewed_by", "material_matches", type_="foreignkey")
    op.alter_column("material_matches", "status", existing_type=sa.String(40), type_=sa.String(50), nullable=True)
    op.alter_column("material_matches", "classification", existing_type=sa.String(50), nullable=True)
    op.alter_column("material_matches", "final_score", existing_type=sa.Float(), nullable=True)
    for column in ("reviewed_by", "reviewed_at", "matcher_version", "model_name", "explanation", "attributes_b", "attributes_a", "fuzzy_score"):
        op.drop_column("material_matches", column)

    op.drop_index("ix_national_materials_national_code", table_name="national_materials")
    for column in ("updated_at", "code_scheme_version", "provenance", "subcategory"):
        op.drop_column("national_materials", column)
    op.alter_column("national_materials", "specifications", existing_type=sa.JSON(), type_=sa.Text(), postgresql_using="specifications::text")
    op.alter_column("national_materials", "national_code", existing_type=sa.String(100), nullable=False)

    op.drop_constraint("uq_cpse_material_code", "materials", type_="unique")
    for index in ("ix_materials_cpse_id", "ix_materials_category", "ix_materials_subcategory", "ix_materials_import_batch_id"):
        op.drop_index(index, table_name="materials")
    op.drop_constraint("fk_materials_import_batch", "materials", type_="foreignkey")
    for column in ("matching_status", "status", "classification_version", "classification_source", "classification_confidence", "subcategory", "normalized_description", "cleaned_description", "original_description", "import_batch_id"):
        op.drop_column("materials", column)

    op.drop_constraint("fk_users_cpse_id", "users", type_="foreignkey")
    op.drop_column("users", "cpse_id")
