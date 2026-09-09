"""add price snapshot provenance

Revision ID: 202608090002
Revises: 202608090001
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202608090002"
down_revision: str | None = "202608090001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("price_snapshots", sa.Column("price_source", sa.String(length=100), nullable=True))
    op.add_column("price_snapshots", sa.Column("price_source_class", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("price_snapshots", "price_source_class")
    op.drop_column("price_snapshots", "price_source")
