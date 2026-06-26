"""merge heads

Revision ID: 699fd9c3995e
Revises: a50b25f23040, e8185a2a21c9
Create Date: 2026-06-12 06:53:54.117409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '699fd9c3995e'
down_revision: Union[str, Sequence[str], None] = ('a50b25f23040', 'e8185a2a21c9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
