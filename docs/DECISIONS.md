# Architecture Decisions

## Sprint 0

- Use a monorepo with `backend`, `frontend`, `docs` and root infrastructure files.
- Keep the backend synchronous with SQLAlchemy sessions to avoid unnecessary async complexity in the foundation.
- Version application routes under `/api/v1`; keep `/health` at the root for infrastructure probes.
- Use JWT bearer tokens with bcrypt password hashing.
- Let FastAPI generate OpenAPI automatically through `/openapi.json` and `/docs`.
- Run Alembic migrations when the backend container starts so `docker compose up` is enough for local bootstrapping.
- Serve the built frontend through Nginx in Docker while keeping Vite available for local development.

## Deferred

- Scrapers are intentionally deferred to Sprint 1.
- AI scoring is intentionally deferred to Sprint 2.
- Watchlists, alerts and notification delivery are intentionally deferred to later sprints.

