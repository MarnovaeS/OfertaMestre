from sqlalchemy.orm import Session

from app.models.store import Store
from app.services._persistence import commit_refresh

INITIAL_STORES = [
    ("Amazon Brasil", "amazon-brasil", "https://www.amazon.com.br"),
    ("Mercado Livre", "mercado-livre", "https://www.mercadolivre.com.br"),
    ("Magazine Luiza", "magazine-luiza", "https://www.magazineluiza.com.br"),
    ("KaBuM!", "kabum", "https://www.kabum.com.br"),
    ("Casas Bahia", "casas-bahia", "https://www.casasbahia.com.br"),
    ("Samsung", "samsung", "https://www.samsung.com/br"),
    ("Shopee", "shopee", "https://shopee.com.br"),
    ("Steam", "steam", "https://store.steampowered.com"),
    ("Acer", "acer", "https://www.acer.com/br-pt"),
    ("Nike", "nike", "https://www.nike.com.br"),
    ("Netshoes", "netshoes", "https://www.netshoes.com.br"),
    ("Centauro", "centauro", "https://www.centauro.com.br"),
    ("Dafiti", "dafiti", "https://www.dafiti.com.br"),
]


def seed_initial_stores(db: Session) -> int:
    created = 0
    for name, slug, base_url in INITIAL_STORES:
        exists = db.query(Store).filter(Store.slug == slug).first()
        if exists:
            continue
        commit_refresh(db, Store(name=name, slug=slug, base_url=base_url, is_active=True))
        created += 1
    return created
