from datetime import datetime

from pydantic import BaseModel, Field


class MercadoLivreAuthorizeResponse(BaseModel):
    authorization_url: str


class MercadoLivreStatusResponse(BaseModel):
    connected: bool
    provider: str = "mercadolivre"
    expires_at: datetime | None = None
    provider_user_id: str | None = None


class MercadoLivreTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)
    scope: str | None = None
    user_id: int | str | None = None
