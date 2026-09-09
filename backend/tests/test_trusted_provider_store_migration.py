import importlib.util
from pathlib import Path

import sqlalchemy as sa


def _migration():
    path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "202609090002_seed_trusted_provider_stores.py"
    )
    spec = importlib.util.spec_from_file_location("trusted_stores", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_trusted_stores_seed_is_complete_and_idempotent():
    migration = _migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "CREATE TABLE stores (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, "
                "slug VARCHAR NOT NULL UNIQUE, base_url VARCHAR NOT NULL, "
                "is_active BOOLEAN NOT NULL)"
            )
        )
        original = migration.op.get_bind
        migration.op.get_bind = lambda: connection
        try:
            migration._seed_stores()
            migration._seed_stores()
        finally:
            migration.op.get_bind = original

        slugs = set(connection.execute(sa.text("SELECT slug FROM stores")).scalars())
        count = connection.execute(sa.text("SELECT COUNT(*) FROM stores")).scalar_one()

    assert {"mercadolivre", "amazon-brasil", "magazine-luiza", "casas-bahia", "centauro", "nike", "adidas", "havan", "shopee"} <= slugs
    assert count == len(migration.STORES)
