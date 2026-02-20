"""create moderation_results table

Revision ID: 90881fbe3807
Revises: 03de1619f2a1
Create Date: 2026-02-20 10:37:24.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90881fbe3807'
down_revision: Union[str, None] = '03de1619f2a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE moderation_results (
        id SERIAL PRIMARY KEY,
        item_id INTEGER REFERENCES items(id),
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        is_violation BOOLEAN,
        probability FLOAT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE moderation_results;")
