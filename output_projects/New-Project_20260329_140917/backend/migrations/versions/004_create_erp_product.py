"""create erp_product table

修訂 ID: 004
建立時間: 2024-05-xx

"""

revision = "004_create_erp_product"
down_revision = "003_create_attachment"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "erp_product",
        sa.Column("product_id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table("erp_product")