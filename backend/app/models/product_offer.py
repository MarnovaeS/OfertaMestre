from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class ProductOffer(Base):
    __tablename__ = "product_offers"
    __table_args__ = (
        UniqueConstraint("store_id", "external_id", name="uq_product_offers_store_external_id"),
        CheckConstraint("current_price >= 0", name="ck_product_offers_current_price_non_negative"),
        CheckConstraint("original_price IS NULL OR original_price >= 0", name="ck_product_offers_original_price_non_negative"),
        CheckConstraint("shipping_price IS NULL OR shipping_price >= 0", name="ck_product_offers_shipping_price_non_negative"),
        CheckConstraint(
            "installment_value IS NULL OR installment_value >= 0",
            name="ck_product_offers_installment_value_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False, index=True)
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("sellers.id"), nullable=True, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", server_default="BRL", nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False, index=True)
    is_prime: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_free_shipping: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    installment_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    installment_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    product = relationship("Product", back_populates="offers")
    store = relationship("Store", back_populates="offers")
    seller = relationship("Seller", back_populates="offers")
    price_snapshots = relationship("PriceSnapshot", back_populates="product_offer", order_by="PriceSnapshot.captured_at")
