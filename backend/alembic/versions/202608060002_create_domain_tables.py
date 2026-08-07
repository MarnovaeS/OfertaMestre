"""create domain tables

Revision ID: 202608060002
Revises: 202608060001
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202608060002"
down_revision: str | None = "202608060001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_brands_slug"),
    )
    op.create_index("ix_brands_name", "brands", ["name"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_stores_slug"),
    )
    op.create_index("ix_stores_name", "stores", ["name"])

    op.create_table(
        "sellers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("reputation_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_official", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.UniqueConstraint("store_id", "external_id", name="uq_sellers_store_external_id"),
    )
    op.create_index("ix_sellers_name", "sellers", ["name"])
    op.create_index("ix_sellers_store_id", "sellers", ["store_id"])

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("gtin", sa.String(length=32), nullable=True),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
    )
    op.create_index("ix_products_brand_id", "products", ["brand_id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_gtin", "products", ["gtin"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_sku", "products", ["sku"])

    op.create_table(
        "product_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("seller_id", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("original_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("shipping_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="BRL", nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_prime", sa.Boolean(), nullable=True),
        sa.Column("is_free_shipping", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("installment_count", sa.Integer(), nullable=True),
        sa.Column("installment_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("current_price >= 0", name="ck_product_offers_current_price_non_negative"),
        sa.CheckConstraint("original_price IS NULL OR original_price >= 0", name="ck_product_offers_original_price_non_negative"),
        sa.CheckConstraint("shipping_price IS NULL OR shipping_price >= 0", name="ck_product_offers_shipping_price_non_negative"),
        sa.CheckConstraint("installment_value IS NULL OR installment_value >= 0", name="ck_product_offers_installment_value_non_negative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["sellers.id"]),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.UniqueConstraint("store_id", "external_id", name="uq_product_offers_store_external_id"),
    )
    op.create_index("ix_product_offers_is_available", "product_offers", ["is_available"])
    op.create_index("ix_product_offers_last_checked_at", "product_offers", ["last_checked_at"])
    op.create_index("ix_product_offers_product_id", "product_offers", ["product_id"])
    op.create_index("ix_product_offers_seller_id", "product_offers", ["seller_id"])
    op.create_index("ix_product_offers_store_id", "product_offers", ["store_id"])

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_offer_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("original_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("shipping_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("price >= 0", name="ck_price_snapshots_price_non_negative"),
        sa.CheckConstraint("original_price IS NULL OR original_price >= 0", name="ck_price_snapshots_original_price_non_negative"),
        sa.CheckConstraint("shipping_price IS NULL OR shipping_price >= 0", name="ck_price_snapshots_shipping_price_non_negative"),
        sa.ForeignKeyConstraint(["product_offer_id"], ["product_offers.id"]),
    )
    op.create_index("ix_price_snapshots_offer_captured_at", "price_snapshots", ["product_offer_id", "captured_at"])
    op.create_index("ix_price_snapshots_product_offer_id", "price_snapshots", ["product_offer_id"])


def downgrade() -> None:
    op.drop_index("ix_price_snapshots_product_offer_id", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_offer_captured_at", table_name="price_snapshots")
    op.drop_table("price_snapshots")
    op.drop_index("ix_product_offers_store_id", table_name="product_offers")
    op.drop_index("ix_product_offers_seller_id", table_name="product_offers")
    op.drop_index("ix_product_offers_product_id", table_name="product_offers")
    op.drop_index("ix_product_offers_last_checked_at", table_name="product_offers")
    op.drop_index("ix_product_offers_is_available", table_name="product_offers")
    op.drop_table("product_offers")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_gtin", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_brand_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_sellers_store_id", table_name="sellers")
    op.drop_index("ix_sellers_name", table_name="sellers")
    op.drop_table("sellers")
    op.drop_index("ix_stores_name", table_name="stores")
    op.drop_table("stores")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_brands_name", table_name="brands")
    op.drop_table("brands")

