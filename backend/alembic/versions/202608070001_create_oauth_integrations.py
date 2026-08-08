"""create oauth integration tables

Revision ID: 202608070001
Revises: 202608060002
Create Date: 2026-08-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202608070001"
down_revision: str | None = "202608060002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("token_type", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "provider", name="uq_oauth_integrations_user_provider"),
    )
    op.create_index("ix_oauth_integrations_expires_at", "oauth_integrations", ["expires_at"])
    op.create_index("ix_oauth_integrations_provider", "oauth_integrations", ["provider"])
    op.create_index("ix_oauth_integrations_user_id", "oauth_integrations", ["user_id"])

    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("state_hash", sa.String(length=128), nullable=False),
        sa.Column("code_verifier", sa.Text(), nullable=False),
        sa.Column("redirect_uri", sa.String(length=2048), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("state_hash", name="uq_oauth_states_state_hash"),
    )
    op.create_index("ix_oauth_states_expires_at", "oauth_states", ["expires_at"])
    op.create_index("ix_oauth_states_provider", "oauth_states", ["provider"])
    op.create_index("ix_oauth_states_user_id", "oauth_states", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_oauth_states_user_id", table_name="oauth_states")
    op.drop_index("ix_oauth_states_provider", table_name="oauth_states")
    op.drop_index("ix_oauth_states_expires_at", table_name="oauth_states")
    op.drop_table("oauth_states")
    op.drop_index("ix_oauth_integrations_user_id", table_name="oauth_integrations")
    op.drop_index("ix_oauth_integrations_provider", table_name="oauth_integrations")
    op.drop_index("ix_oauth_integrations_expires_at", table_name="oauth_integrations")
    op.drop_table("oauth_integrations")
