# OfertaMestre

OfertaMestre e uma plataforma de inteligencia para promocoes. A base atual entrega monorepo, backend FastAPI, frontend React/Vite, PostgreSQL, Alembic, autenticacao JWT, Docker Compose, CI, fundacao do dominio comercial, ingestao interna generica e fundacao OAuth do Mercado Livre.

## Estado Atual

Esta base corresponde a Sprint 0, Sprint 0.1, Sprint 0.2, Sprint 0.3 e Sprint 1.0.

Incluido:

- Backend FastAPI.
- PostgreSQL via Docker Compose.
- SQLAlchemy 2.
- Alembic.
- Autenticacao JWT no backend.
- Frontend React + Vite + TypeScript.
- Dashboard inicial com metricas zeradas.
- Dominio comercial administrativo: marcas, categorias, lojas, vendedores, produtos, ofertas e snapshots de preco.
- Ingestao interna generica para ofertas externas futuras.
- Fundacao OAuth 2.0 do Mercado Livre com state, PKCE, callback, status, desconexao e refresh de token.
- GitHub Actions.
- Testes automatizados basicos.

Nao incluido ainda:

- Scrapers.
- Coleta de produtos, precos ou ofertas do Mercado Livre.
- Integracoes Amazon, Steam ou outras APIs comerciais.
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

3. Opcionalmente configure as variaveis do Mercado Livre se for testar OAuth.

4. Suba a aplicacao:

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

Variaveis opcionais para OAuth Mercado Livre:

- `MERCADOLIVRE_CLIENT_ID`
- `MERCADOLIVRE_CLIENT_SECRET`
- `MERCADOLIVRE_REDIRECT_URI`
- `OAUTH_TOKEN_ENCRYPTION_KEY`

`SECRET_KEY` deve ter pelo menos 32 caracteres e deve ser trocada fora do ambiente local. `OAUTH_TOKEN_ENCRYPTION_KEY` tambem deve ser uma string forte e diferente da chave JWT. O backend nao define valor padrao para `DATABASE_URL` ou `SECRET_KEY`.

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
- `POST /api/v1/internal/ingestion/offers`
- `GET /api/v1/integrations/mercadolivre/authorize`
- `GET /api/v1/integrations/mercadolivre/status`
- `DELETE /api/v1/integrations/mercadolivre`
- `GET /oauth/mercadolivre/callback`

Rotas `GET` de dominio sao publicas. Rotas administrativas `POST`, `PATCH` e `DELETE` exigem JWT. A rota de callback OAuth e publica por necessidade do provedor, mas valida `state` emitido pelo backend.

## Mercado Livre OAuth

A Sprint 1.0 implementa apenas a fundacao OAuth 2.0 do Mercado Livre. Ela permite conectar uma conta, persistir tokens criptografados, consultar status, desconectar e renovar token expirado. Nao existe coleta de produtos, precos ou ofertas nesta etapa.

Mais detalhes em `docs/MERCADOLIVRE.md`.

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
