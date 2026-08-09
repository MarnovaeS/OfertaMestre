# API

A OpenAPI e gerada automaticamente pelo FastAPI.

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`

## Convencoes

- Rotas de aplicacao usam o prefixo `/api/v1`.
- `GET /health` fica fora do versionamento para probes de infraestrutura.
- Listagens de dominio aceitam paginacao simples com `limit` e `offset`.
- Leituras de dominio sao publicas.
- Criacao, alteracao e exclusao exigem JWT Bearer.
- Rotas em `/api/v1/internal` sao internas e autenticadas.

## Infraestrutura

### `GET /health`

Resposta:

```json
{
  "status": "ok"
}
```

## Autenticacao

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

## Dashboard Inicial

- `GET /api/v1/dashboard/summary`

Retorna metricas zeradas enquanto o dashboard real permanece fora do escopo.

## Dominio Comercial

### Brands

- `GET /api/v1/brands?limit=20&offset=0`
- `GET /api/v1/brands/{brand_id}`
- `POST /api/v1/brands`
- `PATCH /api/v1/brands/{brand_id}`
- `DELETE /api/v1/brands/{brand_id}`

### Categories

- `GET /api/v1/categories?limit=20&offset=0`
- `GET /api/v1/categories/{category_id}`
- `POST /api/v1/categories`
- `PATCH /api/v1/categories/{category_id}`
- `DELETE /api/v1/categories/{category_id}`

### Stores

- `GET /api/v1/stores?limit=20&offset=0`
- `GET /api/v1/stores/{store_id}`
- `POST /api/v1/stores`
- `PATCH /api/v1/stores/{store_id}`
- `DELETE /api/v1/stores/{store_id}`

### Sellers

- `GET /api/v1/sellers?limit=20&offset=0`
- `GET /api/v1/sellers/{seller_id}`
- `POST /api/v1/sellers`
- `PATCH /api/v1/sellers/{seller_id}`
- `DELETE /api/v1/sellers/{seller_id}`

### Products

- `GET /api/v1/products?limit=20&offset=0`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/products`
- `PATCH /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`

`Product` nao armazena preco.

### Offers

- `GET /api/v1/offers?limit=20&offset=0`
- `GET /api/v1/offers/{offer_id}`
- `POST /api/v1/offers`
- `PATCH /api/v1/offers/{offer_id}`
- `DELETE /api/v1/offers/{offer_id}`
- `GET /api/v1/offers/{offer_id}/price-history`
- `POST /api/v1/offers/{offer_id}/price-history` - endpoint administrativo/interno nesta fase

`ProductOffer` representa uma oferta concreta de um produto em uma loja/vendedor. Cada oferta possui historico proprio em `PriceSnapshot`.

## Ingestao Interna

### `POST /api/v1/internal/ingestion/offers`

Endpoint autenticado e interno para collectors futuros enviarem `ExternalOfferInput`.

Retorna `IngestionResult` com:

- `product_id`
- `offer_id`
- `seller_id`
- `product_created`
- `offer_created`
- `seller_created`
- `snapshot_created`
- `matched_by`

Este endpoint nao e publico para usuarios finais e nao executa coleta externa.

## Fora do Escopo Atual

Nao ha endpoints de scraping, browser automation, filas, IA, watchlist, notificacoes, cupons, cashback, score de promocao ou integracoes com marketplaces nesta sprint.


## Integracao Steam

Endpoints autenticados/admin para teste manual da Sprint 2.1:

- `GET /api/v1/integrations/steam/status`
- `GET /api/v1/integrations/steam/apps?max_results=100&last_appid=0&modified_since=0`
- `POST /api/v1/integrations/steam/sync?max_results=100`

`/status` nunca retorna `STEAM_WEB_API_KEY`.

`/apps` retorna apenas catalogo sanitizado:

- `appid`
- `name`
- `last_modified`
- `price_change_number`

`/sync` atualiza `provider_catalog_items` e `provider_sync_states`. Nao cria `ProductOffer` nem `PriceSnapshot`, pois a API Steam usada nesta sprint nao retorna preco atual.
