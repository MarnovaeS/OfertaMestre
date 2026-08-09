from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_price_snapshots_price_non_negative"),
        CheckConstraint("original_price IS NULL OR original_price >= 0", name="ck_price_snapshots_original_price_non_negative"),
        CheckConstraint("shipping_price IS NULL OR shipping_price >= 0", name="ck_price_snapshots_shipping_price_non_negative"),
        Index("ix_price_snapshots_offer_captured_at", "product_offer_id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_offer_id: Mapped[int] = mapped_column(ForeignKey("product_offers.id"), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_source_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product_offer = relationship("ProductOffer", back_populates="price_snapshots")
