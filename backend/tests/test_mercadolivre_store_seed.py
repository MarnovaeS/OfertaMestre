import importlib.util
from pathlib import Path

import sqlalchemy as sa

from app.database.session import SessionLocal
from app.models.store import Store
from app.services.seed import seed_initial_stores


def test_seed_initial_stores_creates_mercadolivre_store(client):
    with SessionLocal() as db:
        created = seed_initial_stores(db)
        store = db.query(Store).filter(Store.slug == "mercadolivre").one_or_none()

    assert created > 0
    assert store is not None
    assert store.name == "Mercado Livre"
    assert store.base_url == "https://www.mercadolivre.com.br"
    assert store.is_active is True


def test_seed_initial_stores_is_idempotent_for_mercadolivre(client):
    with SessionLocal() as db:
        seed_initial_stores(db)
        seed_initial_stores(db)
        count = db.query(Store).filter(Store.slug == "mercadolivre").count()

    assert count == 1


def test_mercadolivre_store_migration_inserts_store_when_missing():
    migration = _load_mercadolivre_store_migration()
    engine = _create_store_migration_engine()

    with engine.begin() as connection:
        migration._seed_mercadolivre_store(connection)
        migration._seed_mercadolivre_store(connection)
        rows = connection.execute(sa.text("SELECT name, slug, base_url, is_active FROM stores")).mappings().all()

    assert rows == [
        {
            "name": "Mercado Livre",
            "slug": "mercadolivre",
            "base_url": "https://www.mercadolivre.com.br",
            "is_active": True,
        }
    ]


def test_mercadolivre_store_migration_updates_legacy_slug_without_duplicate():
    migration = _load_mercadolivre_store_migration()
    engine = _create_store_migration_engine()

    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                INSERT INTO stores (name, slug, base_url, is_active)
                VALUES ('Mercado Livre', 'mercado-livre', 'https://www.mercadolivre.com.br', true)
                """
            )
        )
        migration._seed_mercadolivre_store(connection)
        rows = connection.execute(sa.text("SELECT slug FROM stores")).scalars().all()

    assert rows == ["mercadolivre"]


def _load_mercadolivre_store_migration():
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202608080001_seed_mercadolivre_store.py"
    spec = importlib.util.spec_from_file_location("seed_mercadolivre_store_migration", migration_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _create_store_migration_engine():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE stores (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL UNIQUE,
                    base_url VARCHAR(2048) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
                """
            )
        )
    return engine
