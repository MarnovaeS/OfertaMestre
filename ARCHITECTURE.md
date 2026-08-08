# Arquitetura

## Visao Geral

OfertaMestre permanece como monolito modular nesta fase. O backend e uma unica aplicacao FastAPI, com separacao interna por rotas, schemas, models, services e ingestion.

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
- `app/schemas`: contratos Pydantic de entrada e saida do dominio administrativo.
- `app/ingestion`: contrato externo, normalizacao, matching e service transacional de ingestao.
- `app/integrations`: conectores de APIs oficiais e adaptadores por provedor.
- `app/services`: regras de aplicacao e persistencia do CRUD administrativo.
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

## Ingestao

A Sprint 0.3 adiciona uma camada generica de ingestao para ofertas externas futuras:

```text
ExternalOfferInput -> Normalizer -> Matcher -> Ingestion Service -> Domain Models
```

A ingestao e transacional, usa `flush` durante o fluxo e faz `commit` apenas ao final. Ela nao conhece detalhes de marketplaces especificos.

## Mercado Livre Product Ingestion

A Sprint 2 adiciona um modulo especifico de integracao:

```text
app/integrations/mercadolivre/client.py
app/integrations/mercadolivre/adapter.py
app/integrations/mercadolivre/collector.py
```

Responsabilidades:

- `client.py`: chamadas HTTP oficiais autenticadas, timeout, tratamento de erros e retry limitado.
- `adapter.py`: conversao de payloads Mercado Livre para `ExternalOfferInput`.
- `collector.py`: orquestracao por usuario autenticado, validacao da Store `mercadolivre`, uso de `get_valid_access_token` e chamada da ingestion existente.

O coletor Mercado Livre nao duplica matching, criacao de seller, criacao de produto, idempotencia de oferta ou snapshots; essas regras continuam em `app/ingestion/service.py`.

## Frontend

Stack atual:

- React
- Vite
- TypeScript
- CSS nativo

O frontend ainda exibe um dashboard inicial com metricas zeradas. Nao consome o dominio comercial nem a ingestao nesta sprint.

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
    ingestion/
    integrations/
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
- Endpoint de ingestao e interno e autenticado.
- Coleta Mercado Livre usa somente API oficial e OAuth persistido.
- Retry e rate-limit ficam dentro do client Mercado Livre.
- Roles/permissoes ficam fora da Sprint 2.
- Scrapers, IA, filas, notificacoes e dashboard real continuam fora do escopo.
