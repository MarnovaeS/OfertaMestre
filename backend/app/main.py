from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    brands,
    categories,
    dashboard,
    health,
    internal_ingestion,
    mercadolivre,
    offers,
    products,
    sellers,
    steam,
    stores,
)
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="OfertaMestre API",
        description="Domain foundation API for OfertaMestre.",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
    app.include_router(brands.router, prefix="/api/v1/brands", tags=["brands"])
    app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
    app.include_router(stores.router, prefix="/api/v1/stores", tags=["stores"])
    app.include_router(sellers.router, prefix="/api/v1/sellers", tags=["sellers"])
    app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
    app.include_router(offers.router, prefix="/api/v1/offers", tags=["offers"])
    app.include_router(mercadolivre.router, prefix="/api/v1/integrations/mercadolivre", tags=["mercadolivre"])
    app.include_router(mercadolivre.callback_router, tags=["mercadolivre"])
    app.include_router(steam.router, prefix="/api/v1/integrations/steam", tags=["steam"])
    app.include_router(
        internal_ingestion.router,
        prefix="/api/v1/internal/ingestion",
        tags=["internal-ingestion"],
    )

    return app


app = create_app()
