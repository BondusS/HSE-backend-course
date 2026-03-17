"""create account table

Revision ID: d4e1b2c3d5f5
Revises: 5f5a1b2c3d4e
Create Date: 2024-05-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e1b2c3d5f5'
down_revision: Union[str, None] = '5f5a1b2c3d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'account',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('login', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('is_blocked', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('login')
    )


def downgrade() -> None:
    op.drop_table('account')
