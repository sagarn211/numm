"""Add CDN-backed images for materials."""
from alembic import op
import sqlalchemy as sa

revision = "20260914_08"
down_revision = "20260911_07"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("material_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("national_material_id", sa.Integer(), sa.ForeignKey("national_materials.id"), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=False),
        sa.Column("imagekit_file_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("image_type", sa.String(length=30), nullable=False, server_default="OTHER"),
        sa.Column("source_type", sa.String(length=40), nullable=False, server_default="WAREHOUSE_UPLOAD"),
        sa.Column("verification_status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_url", sa.String(length=2048)), sa.Column("checksum", sa.String(length=128)),
        sa.Column("original_filename", sa.String(length=512)),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("verified_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("verified_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for name, column in [("ix_material_images_material_id", "material_id"), ("ix_material_images_national_material_id", "national_material_id"), ("ix_material_images_verification_status", "verification_status"), ("ix_material_images_checksum", "checksum")]:
        op.create_index(name, "material_images", [column])

def downgrade():
    op.drop_table("material_images")
