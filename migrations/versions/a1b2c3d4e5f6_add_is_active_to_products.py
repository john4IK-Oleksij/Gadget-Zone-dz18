"""add is_active to products

Revision ID: a1b2c3d4e5f6
Revises: ee492b507ca0
Create Date: 2026-11-08 11:06:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'ee492b507ca0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )


def downgrade() -> None:
    op.drop_column('products', 'is_active')
