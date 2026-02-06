"""create_users_and_items_tables

Revision ID: 03de1619f2a1
Revises: 
Create Date: 2026-02-06 01:41:53.437889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03de1619f2a1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Applies the migration.
    """
    op.execute("""
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        is_verified_seller BOOLEAN NOT NULL DEFAULT FALSE
    );
    """)
    op.execute("""
    CREATE TABLE items (
        id SERIAL PRIMARY KEY,
        seller_id INT REFERENCES users(id),
        name VARCHAR(100) NOT NULL,
        description VARCHAR(1000),
        category INT,
        images_qty INT
    );
    """)


def downgrade() -> None:
    """
    Reverts the migration.
    """
    op.execute("DROP TABLE items;")
    op.execute("DROP TABLE users;")
