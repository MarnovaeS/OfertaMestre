from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CatalogItem:
    provider: str
    external_id: str
    name: str
    last_modified: int | None = None
    price_change_number: int | None = None
    metadata: dict | None = None


class Provider(Protocol):
    provider: str


class CatalogProvider(Provider, Protocol):
    def list_catalog_items(self, *, max_results: int, cursor: str | None = None) -> list[CatalogItem]: ...


class OfferProvider(Provider, Protocol):
    """Provider capable of returning real priced offers for ingestion."""
