"""005_create_email_template.py

Revision ID: 005
Revises: 004_create_erp_product
Create Date: 2024-05-XX

"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004_create_erp_product"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_templates",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("template_name", sa.String(100), nullable=False, unique=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body_html", sa.Text, nullable=True),
        sa.Column("body_text", sa.Text, nullable=True),
    )


def downgrade():
    op.drop_table("email_templates")