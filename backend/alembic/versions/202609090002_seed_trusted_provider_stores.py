"""seed trusted provider stores

Revision ID: 202609090002
Revises: 202609090001
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202609090002"
down_revision: str | None = "202609090001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STORES = (
    {"name": "Mercado Livre", "slug": "mercadolivre", "base_url": "https://www.mercadolivre.com.br", "is_active": True},
    {"name": "Amazon Brasil", "slug": "amazon-brasil", "base_url": "https://www.amazon.com.br", "is_active": True},
    {"name": "Magazine Luiza", "slug": "magazine-luiza", "base_url": "https://www.magazineluiza.com.br", "is_active": True},
    {"name": "Casas Bahia", "slug": "casas-bahia", "base_url": "https://www.casasbahia.com.br", "is_active": True},
    {"name": "Centauro", "slug": "centauro", "base_url": "https://www.centauro.com.br", "is_active": True},
    {"name": "Nike", "slug": "nike", "base_url": "https://www.nike.com.br", "is_active": True},
    {"name": "Adidas", "slug": "adidas", "base_url": "https://www.adidas.com.br", "is_active": True},
    {"name": "Havan", "slug": "havan", "base_url": "https://www.havan.com.br", "is_active": True},
    {"name": "Shopee", "slug": "shopee", "base_url": "https://shopee.com.br", "is_active": True},
)


def upgrade() -> None:
    _seed_stores()


def downgrade() -> None:
    # Stores may already be referenced by offers, so business data is preserved.
    pass


def _seed_stores() -> None:
    connection = op.get_bind()
    for store in STORES:
        exists = connection.execute(
            sa.text("SELECT id FROM stores WHERE slug = :slug"),
            {"slug": store["slug"]},
        ).first()
        if exists:
            connection.execute(
                sa.text(
                    "UPDATE stores SET name=:name, base_url=:base_url, "
                    "is_active=:is_active WHERE slug=:slug"
                ),
                store,
            )
        else:
            connection.execute(
                sa.text(
                    "INSERT INTO stores (name, slug, base_url, is_active) "
                    "VALUES (:name, :slug, :base_url, :is_active)"
                ),
                store,
            )
