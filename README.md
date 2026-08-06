# OfertaMestre

OfertaMestre is a promotion intelligence platform. Sprint 0 delivers the project foundation: monorepo, FastAPI backend, React dashboard, PostgreSQL, Alembic, JWT authentication, Docker Compose and CI.

## Stack

- Backend: Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, JWT
- Frontend: React, Vite, TypeScript
- Infra: Docker Compose, PostgreSQL, Nginx for the frontend container
- Quality: Pytest, GitHub Actions

## Run Locally

```bash
docker compose up
```

Services:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- PostgreSQL: localhost:5432

The backend runs Alembic migrations automatically before starting the API.

## Environment

Copy `.env.example` to `.env` when you need custom local values. Docker Compose already includes safe development defaults.

Important variables:

- `DATABASE_URL`
- `SECRET_KEY`: must be at least 32 characters and changed outside development
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `BACKEND_CORS_ORIGINS`
- `VITE_API_URL`

## Sprint 0 Scope

Included:

- Project structure
- Docker Compose
- PostgreSQL
- FastAPI
- React + Vite + TypeScript
- JWT login/register
- Initial dashboard summary
- Alembic migrations
- Basic tests
- GitHub Actions

Not included yet:

- Scrapers
- Price history ingestion
- AI scoring engine
- Watchlists and alerts workflow
- External notification integrations

## API

FastAPI generates OpenAPI automatically:

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

Current Sprint 0 endpoints:

- `GET /health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/dashboard/summary`

