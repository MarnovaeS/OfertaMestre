# Arquitetura

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

## Frontend

Stack atual:

- React
- Vite
- TypeScript
- CSS nativo

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
