# Arquitetura

## Visao Geral

OfertaMestre permanece como monolito modular nesta fase. O backend e uma unica aplicacao FastAPI, com separacao interna por rotas, schemas, models e services.

## Backend

Stack atual:

- Python 3.13
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Pydantic Settings
- PyJWT
- Passlib + bcrypt

Camadas:

- `app/api/routes`: interface HTTP.
- `app/schemas`: contratos Pydantic de entrada e saida.
- `app/services`: regras de aplicacao e persistencia de dominio.
- `app/models`: modelos SQLAlchemy.
- `app/database`: engine, session e metadata.
- `app/exceptions`: excecoes internas.

As rotas validam entrada, chamam services e retornam schemas. Regras de negocio nao devem ser concentradas nas rotas.

## Dominio Atual

Entidades implementadas:

- Brand
- Category
- Store
- Seller
- Product
- ProductOffer
- PriceSnapshot

`Product` representa o item conceitual. `ProductOffer` representa uma oferta em uma loja/vendedor e armazena o preco atual administrativo. `PriceSnapshot` guarda o historico da oferta.

## Frontend

Stack atual:

- React
- Vite
- TypeScript
- CSS nativo

O frontend ainda exibe um dashboard inicial com metricas zeradas. Nao consome o dominio comercial nesta sprint.

Bibliotecas planejadas para sprints futuras:

- Tailwind CSS
- TanStack Query
- React Router
- Chart.js

## Infraestrutura

- Docker Compose
- PostgreSQL
- Nginx no container do frontend
- GitHub Actions

## Estrutura Atual

```text
backend/
  app/
    api/
    config/
    core/
    crud/
    database/
    events/
    exceptions/
    jobs/
    models/
    schemas/
    security/
    services/
    utils/
  alembic/
  tests/
frontend/
  src/
docs/
```

## Decisoes

- Rotas de aplicacao sao versionadas em `/api/v1`.
- `GET /health` fica fora do versionamento para probes de infraestrutura.
- SQLAlchemy esta sincrono nesta fase para manter a fundacao simples.
- Alembic e a fonte de verdade para migracoes.
- O frontend e servido por Nginx no container de producao.
- Leituras de dominio sao publicas; escrita administrativa exige JWT.
- Roles/permissoes ficam fora da Sprint 0.2.
- Scrapers, IA, notificacoes e dashboard real continuam fora do escopo.
