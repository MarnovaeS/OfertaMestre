# OfertaMestre

OfertaMestre e uma plataforma de inteligencia para promocoes. A base atual entrega monorepo, backend FastAPI, frontend React/Vite, PostgreSQL, Alembic, autenticacao JWT, Docker Compose, CI e a fundacao do dominio comercial.

## Estado Atual

Esta base corresponde a Sprint 0, Sprint 0.1 e Sprint 0.2.

Incluido:

- Backend FastAPI.
- PostgreSQL via Docker Compose.
- SQLAlchemy 2.
- Alembic.
- Autenticacao JWT no backend.
- Frontend React + Vite + TypeScript.
- Dashboard inicial com metricas zeradas.
- Dominio comercial administrativo: marcas, categorias, lojas, vendedores, produtos, ofertas e snapshots de preco.
- GitHub Actions.
- Testes automatizados basicos.

Nao incluido ainda:

- Scrapers.
- Integracoes Amazon, Mercado Livre, Steam ou outras APIs comerciais.
- IA.
- Notificacoes.
- Watchlist.
- Dashboard com dados reais.
- Score de promocao, cupons ou cashback.

## Pre-requisitos

Para executar com Docker:

- Docker Desktop instalado e em execucao.
- Comando `docker` disponivel no terminal.

Para executar localmente sem Docker:

- Python 3.13.
- Node.js 22 ou superior.
- npm.
- PostgreSQL, caso nao use o banco do Docker.

## Como Executar com Docker

1. Crie o arquivo `.env` a partir do exemplo:

```powershell
Copy-Item .env.example .env
```

2. Revise `POSTGRES_PASSWORD`, `DATABASE_URL` e `SECRET_KEY` no `.env`.

3. Suba a aplicacao:

```bash
docker compose up --build
```

Servicos:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Healthcheck: http://localhost:8000/health
- Swagger: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- PostgreSQL: localhost:5432

O backend executa `alembic upgrade head` antes de iniciar a API.

## Variaveis de Ambiente

Variaveis principais:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `BACKEND_CORS_ORIGINS`
- `VITE_API_URL`

`SECRET_KEY` deve ter pelo menos 32 caracteres e deve ser trocada fora do ambiente local. O backend nao define valor padrao para `DATABASE_URL` ou `SECRET_KEY`.

## Como Executar o Backend Localmente

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m pytest
```

Para iniciar a API localmente, configure `DATABASE_URL` e `SECRET_KEY`, depois execute:

```bash
uvicorn app.main:app --reload
```

Seed idempotente das lojas iniciais:

```bash
cd backend
python -m app.seed
```

## Como Executar o Frontend Localmente

```bash
cd frontend
npm ci
npm run dev
```

Build de producao:

```bash
npm run build
```

## Endpoints Implementados

- `GET /health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/dashboard/summary`
- `GET|POST /api/v1/brands`
- `GET|PATCH|DELETE /api/v1/brands/{brand_id}`
- `GET|POST /api/v1/categories`
- `GET|PATCH|DELETE /api/v1/categories/{category_id}`
- `GET|POST /api/v1/stores`
- `GET|PATCH|DELETE /api/v1/stores/{store_id}`
- `GET|POST /api/v1/sellers`
- `GET|PATCH|DELETE /api/v1/sellers/{seller_id}`
- `GET|POST /api/v1/products`
- `GET|PATCH|DELETE /api/v1/products/{product_id}`
- `GET|POST /api/v1/offers`
- `GET|PATCH|DELETE /api/v1/offers/{offer_id}`
- `GET|POST /api/v1/offers/{offer_id}/price-history`

Rotas `GET` de dominio sao publicas. Rotas administrativas `POST`, `PATCH` e `DELETE` exigem JWT.

## Testes

Backend:

```bash
cd backend
python -m pytest
```

Frontend:

```bash
cd frontend
npm ci
npm run build
```

## Branch Principal

A branch principal do projeto e `main`.
