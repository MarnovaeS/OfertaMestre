"""create provider foundation

Revision ID: 202608090001
Revises: 202608080001
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202608090001"
down_revision: str | None = "202608080001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STEAM_STORE = {
    "name": "Steam",
    "slug": "steam",
    "base_url": "https://store.steampowered.com",
    "is_active": True,
}


def upgrade() -> None:
    op.create_table(
        "provider_sync_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("cursor", sa.String(length=255), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider", name="uq_provider_sync_states_provider"),
    )
    op.create_index("ix_provider_sync_states_provider", "provider_sync_states", ["provider"])

    op.create_table(
        "provider_catalog_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("last_modified", sa.Integer(), nullable=True),
        sa.Column("price_change_number", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.UniqueConstraint("provider", "external_id", name="uq_provider_catalog_items_provider_external_id"),
    )
    op.create_index("ix_provider_catalog_items_provider", "provider_catalog_items", ["provider"])
    op.create_index("ix_provider_catalog_items_store_id", "provider_catalog_items", ["store_id"])
    op.create_index(
        "ix_provider_catalog_items_provider_last_modified",
        "provider_catalog_items",
        ["provider", "last_modified"],
    )

    _seed_steam_store()


def downgrade() -> None:
    op.drop_index("ix_provider_catalog_items_provider_last_modified", table_name="provider_catalog_items")
    op.drop_index("ix_provider_catalog_items_store_id", table_name="provider_catalog_items")
    op.drop_index("ix_provider_catalog_items_provider", table_name="provider_catalog_items")
    op.drop_table("provider_catalog_items")
    op.drop_index("ix_provider_sync_states_provider", table_name="provider_sync_states")
    op.drop_table("provider_sync_states")


def _seed_steam_store() -> None:
    connection = op.get_bind()
    exists = connection.execute(
        sa.text("SELECT id FROM stores WHERE slug = :slug"),
        {"slug": STEAM_STORE["slug"]},
    ).first()
    if exists:
        connection.execute(
            sa.text(
                """
                UPDATE stores
                SET name = :name,
                    base_url = :base_url,
                    is_active = :is_active
                WHERE slug = :slug
                """
            ),
            STEAM_STORE,
        )
        return

    connection.execute(
        sa.text(
            """
            INSERT INTO stores (name, slug, base_url, is_active)
            VALUES (:name, :slug, :base_url, :is_active)
            """
        ),
        STEAM_STORE,
    )
