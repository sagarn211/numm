"""Add a forward-only hash boundary for tamper-evident audit events."""
from alembic import op
import sqlalchemy as sa

revision = "20260910_05"
down_revision = "20260910_04"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("audit_logs", sa.Column("previous_hash", sa.String(64), nullable=True))
    op.add_column("audit_logs", sa.Column("current_hash", sa.String(64), nullable=True))
    op.add_column("audit_logs", sa.Column("payload_checksum", sa.String(64), nullable=True))
    op.add_column("audit_logs", sa.Column("hash_version", sa.String(20), nullable=True))
    op.create_index("ix_audit_logs_current_hash", "audit_logs", ["current_hash"])


def downgrade():
    op.drop_index("ix_audit_logs_current_hash", table_name="audit_logs")
    op.drop_column("audit_logs", "hash_version")
    op.drop_column("audit_logs", "payload_checksum")
    op.drop_column("audit_logs", "current_hash")
    op.drop_column("audit_logs", "previous_hash")
