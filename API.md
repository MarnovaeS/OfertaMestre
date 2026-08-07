# API

A OpenAPI e gerada automaticamente pelo FastAPI.

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`

## Endpoints Implementados

### Infraestrutura

- `GET /health`

Resposta:

```json
{
  "status": "ok"
}
```

### Autenticacao

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Dashboard

- `GET /api/v1/dashboard/summary`

## Endpoints Planejados

Os endpoints abaixo pertencem a sprints futuras e ainda nao estao implementados:

- `GET /api/v1/stores`
- `GET /api/v1/categories`
- `GET /api/v1/products`
- `GET /api/v1/products/{id}`
- `GET /api/v1/prices/history/{product_id}`
- `GET /api/v1/deals`
- `POST /api/v1/watchlists`
- `GET /api/v1/alerts`
