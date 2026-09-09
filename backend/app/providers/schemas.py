from typing import Literal

from pydantic import BaseModel


ProviderState = Literal[
    "connected",
    "configured",
    "credentials_required",
    "approval_required",
    "partnership_required",
]


class ProviderIntegrationStatus(BaseModel):
    provider: str
    name: str
    store_slug: str | None
    channel: str
    state: ProviderState
    configured: bool
    connected: bool
    store_exists: bool | None
    capabilities: list[str]
    note: str
    setup_url: str | None = None
