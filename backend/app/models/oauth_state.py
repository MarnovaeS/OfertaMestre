from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    state_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    code_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(2048), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
