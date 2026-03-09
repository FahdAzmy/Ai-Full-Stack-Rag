"""add new column

Revision ID: 5655b9fad93d
Revises: b06ee5d19fb8
Create Date: 2026-03-09 02:23:41.758243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5655b9fad93d'
down_revision: Union[str, None] = 'b06ee5d19fb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('source_chunks', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'source_chunks')
