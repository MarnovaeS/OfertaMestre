# Architecture Decisions

## Sprint 0

- Use a monorepo with `backend`, `frontend`, `docs` and root infrastructure files.
- Keep the backend synchronous with SQLAlchemy sessions to avoid unnecessary async complexity in the foundation.
- Version application routes under `/api/v1`; keep `/health` at the root for infrastructure probes.
- Use JWT bearer tokens with bcrypt password hashing.
- Let FastAPI generate OpenAPI automatically through `/openapi.json` and `/docs`.
- Run Alembic migrations when the backend container starts so `docker compose up` is enough for local bootstrapping.
- Serve the built frontend through Nginx in Docker while keeping Vite available for local development.

## Sprint 0.2

- Keep the system as a modular monolith.
- Model `Product` as the conceptual product without price.
- Model `ProductOffer` as the commercial offer that owns current administrative price fields.
- Model `PriceSnapshot` as immutable price history per offer.
- Protect write routes with JWT while keeping read routes public.
- Avoid database features exclusive to PostgreSQL so tests can keep using SQLite.
- Provide seed as an explicit idempotent command, not automatic startup behavior.

## Deferred

- Scrapers are intentionally deferred.
- External marketplace APIs are intentionally deferred.
- AI scoring is intentionally deferred.
- Watchlists, alerts and notification delivery are intentionally deferred to later sprints.
