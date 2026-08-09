"""provider foundation compatibility marker

Revision ID: 202608080001
Revises: 202608070001
Create Date: 2026-08-08
"""

from collections.abc import Sequence

revision: str = "202608080001"
down_revision: str | None = "202608070001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
