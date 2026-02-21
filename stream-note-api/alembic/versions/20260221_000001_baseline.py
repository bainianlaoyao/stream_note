"""Baseline revision for migration-managed schema.

Revision ID: 20260221_000001
Revises:
Create Date: 2026-02-21 00:00:01
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "20260221_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline revision is applied via `stamp` after legacy-safe bootstrap.
    pass


def downgrade() -> None:
    # Downgrade is intentionally a no-op to avoid destructive rollback.
    pass
