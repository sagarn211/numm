"""Require administrator approval for public account registrations."""
from alembic import op
import sqlalchemy as sa

revision = "20260917_11"
down_revision = "20260914_10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("account_status", sa.String(20), nullable=True, server_default="APPROVED"))
    op.add_column("users", sa.Column("requested_role", sa.String(40), nullable=True))
    op.add_column("users", sa.Column("requested_cpse_id", sa.Integer(), sa.ForeignKey("cpses.id"), nullable=True))
    op.add_column("users", sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("users", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("review_comment", sa.Text(), nullable=True))
    op.execute("UPDATE users SET account_status = 'APPROVED' WHERE account_status IS NULL")
    op.alter_column("users", "account_status", nullable=False, server_default="APPROVED")
    op.create_index("ix_users_account_status", "users", ["account_status"], unique=False)


def downgrade():
    pass
