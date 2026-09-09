"""enforce oauth state code verifier not null

Revision ID: 202609090001
Revises: 202608090002
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202609090001"
down_revision: str | None = "202608090002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # States without a PKCE verifier cannot complete OAuth and are safe to discard.
    op.execute(sa.text("DELETE FROM oauth_states WHERE code_verifier IS NULL"))
    with op.batch_alter_table("oauth_states") as batch_op:
        batch_op.alter_column(
            "code_verifier",
            existing_type=sa.Text(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("oauth_states") as batch_op:
        batch_op.alter_column(
            "code_verifier",
            existing_type=sa.Text(),
            nullable=True,
        )
