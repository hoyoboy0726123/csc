"""003_create_attachment.py – 建立 Attachment 資料表"""

from alembic import op
import sqlalchemy as sa

revision = "003_create_attachment"
down_revision = "002_create_user"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("case_id", sa.Integer, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("blob_url", sa.String(512), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("attachments")