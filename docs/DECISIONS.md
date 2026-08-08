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

## Sprint 0.3

- Add ingestion as an internal backend module, not a microservice.
- Keep collectors out of scope; ingestion receives normalized external inputs through an internal authenticated endpoint.
- Keep marketplace-specific logic out of the domain.
- Use deterministic normalization and conservative matching only.
- Make ingestion atomic with one commit at the end and rollback on failure.
- Create price snapshots only when relevant price fields change.
- Do not automatically reassign an existing offer to another product; product-offer reconciliation is deferred.
- Add basic structured logging without secrets.

## Sprint 1.0

- Add Mercado Livre OAuth as an integration module under `app/integrations`, separate from domain and ingestion.
- Store OAuth state and PKCE verifier in the database instead of process memory.
- Persist only a SHA-256 hash of OAuth `state` and encrypt the PKCE verifier.
- Encrypt access and refresh tokens before persistence using authenticated encryption.
- Keep the OAuth callback at `/oauth/mercadolivre/callback` to match provider redirect configuration.
- Keep product, price and offer collection out of scope for this sprint.

## Deferred

- Scrapers are intentionally deferred.
- Product, price and offer collection from Mercado Livre are intentionally deferred.
- Browser automation is intentionally deferred.
- Queues, Redis, Celery and schedulers are intentionally deferred.
- AI scoring is intentionally deferred.
- Watchlists, alerts and notification delivery are intentionally deferred to later sprints.
