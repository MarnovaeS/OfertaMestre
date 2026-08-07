from app.database.session import SessionLocal
from app.services.seed import seed_initial_stores


def main() -> None:
    db = SessionLocal()
    try:
        created = seed_initial_stores(db)
        print(f"Initial stores created: {created}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
