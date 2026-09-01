"""initial

Revision ID: 4ad1217dfbf3
Revises: 
Create Date: 2026-08-31 15:04:31.422577

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '4ad1217dfbf3'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
