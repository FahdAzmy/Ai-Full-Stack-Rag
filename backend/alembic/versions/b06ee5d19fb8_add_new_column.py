"""add new column

Revision ID: b06ee5d19fb8
Revises: 60fc8261209d
Create Date: 2026-03-09 02:17:45.542195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b06ee5d19fb8'
down_revision: Union[str, None] = '60fc8261209d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
