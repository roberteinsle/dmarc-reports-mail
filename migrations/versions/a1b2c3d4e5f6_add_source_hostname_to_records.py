"""add source_hostname to records

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('records', sa.Column('source_hostname', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('records', 'source_hostname')
