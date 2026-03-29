"""001_create_case.py"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cases',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('product_id', sa.String(64), nullable=True),
        sa.Column('summary', sa.Text, nullable=False),
        sa.Column('suggested_close_date', sa.Date, nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='待處理'),
        sa.Column('assignee_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('cases')