from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainNotFoundError
from app.ingestion.contracts import ExternalOfferInput, IngestionResult
from app.ingestion.service import ingest_external_offer
from app.integrations.mercadolivre.adapter import STORE_SLUG, normalize_item
from app.integrations.mercadolivre.client import MercadoLivreHttpClient
from app.integrations.mercadolivre.service import get_valid_access_token
from app.models.store import Store
from app.models.user import User


class MercadoLivreCollectorService:
    def __init__(self, db: Session, user: User, client: MercadoLivreHttpClient | None = None) -> None:
        self.db = db
        self.user = user
        self.client = client or MercadoLivreHttpClient()
        self._seller_cache: dict[str, dict[str, Any]] = {}

    def fetch_normalized_item(self, item_id: str) -> ExternalOfferInput:
        self._require_store()
        access_token = get_valid_access_token(self.db, self.user.id)
        item = self.client.get_item(item_id, access_token)
        sale_price = self.client.get_sale_price(item_id, access_token)
        seller = self._get_seller_if_needed(item, access_token)
        return normalize_item(item, sale_price=sale_price, seller=seller)

    def ingest_item(self, item_id: str) -> IngestionResult:
        payload = self.fetch_normalized_item(item_id)
        return ingest_external_offer(self.db, payload)

    def _require_store(self) -> Store:
        store = self.db.scalars(select(Store).where(Store.slug == STORE_SLUG)).first()
        if store is None:
            raise DomainNotFoundError("Store mercadolivre not found")
        return store

    def _get_seller_if_needed(self, item: dict[str, Any], access_token: str) -> dict[str, Any] | None:
        seller_id = item.get("seller_id")
        if seller_id is None:
            return None
        cache_key = str(seller_id)
        if cache_key not in self._seller_cache:
            self._seller_cache[cache_key] = self.client.get_seller(seller_id, access_token)
        return self._seller_cache[cache_key]
