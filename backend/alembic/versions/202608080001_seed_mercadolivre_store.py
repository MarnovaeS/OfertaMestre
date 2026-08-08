"""seed mercadolivre store

Revision ID: 202608080001
Revises: 202608070001
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision: str = "202608080001"
down_revision: str | None = "202608070001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MERCADOLIVRE_STORE = {
    "name": "Mercado Livre",
    "slug": "mercadolivre",
    "base_url": "https://www.mercadolivre.com.br",
    "is_active": True,
}
LEGACY_MERCADOLIVRE_SLUG = "mercado-livre"


def upgrade() -> None:
    _seed_mercadolivre_store(op.get_bind())


def downgrade() -> None:
    pass


def _seed_mercadolivre_store(connection: Connection) -> None:
    canonical = connection.execute(
        sa.text("SELECT id FROM stores WHERE slug = :slug"),
        {"slug": MERCADOLIVRE_STORE["slug"]},
    ).first()
    if canonical:
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
            MERCADOLIVRE_STORE,
        )
        return

    legacy = connection.execute(
        sa.text("SELECT id FROM stores WHERE slug = :slug"),
        {"slug": LEGACY_MERCADOLIVRE_SLUG},
    ).first()
    if legacy:
        connection.execute(
            sa.text(
                """
                UPDATE stores
                SET name = :name,
                    slug = :slug,
                    base_url = :base_url,
                    is_active = :is_active
                WHERE slug = :legacy_slug
                """
            ),
            {**MERCADOLIVRE_STORE, "legacy_slug": LEGACY_MERCADOLIVRE_SLUG},
        )
        return

    connection.execute(
        sa.text(
            """
            INSERT INTO stores (name, slug, base_url, is_active)
            VALUES (:name, :slug, :base_url, :is_active)
            """
        ),
        MERCADOLIVRE_STORE,
    )
