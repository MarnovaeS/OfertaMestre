# Mercado Livre OAuth e Product Ingestion

A Sprint 2 adiciona a primeira ingestao manual de anuncios do Mercado Livre usando somente API oficial e a camada de ingestion existente do OfertaMestre. Nao ha scraping, busca por palavra-chave, varredura de catalogo, scheduler, filas, Redis, Celery ou IA.

## Variaveis de Ambiente

- `MERCADOLIVRE_CLIENT_ID`: client id do aplicativo Mercado Livre.
- `MERCADOLIVRE_CLIENT_SECRET`: client secret do aplicativo Mercado Livre.
- `MERCADOLIVRE_REDIRECT_URI`: URL publica de callback cadastrada no Mercado Livre.
- `OAUTH_TOKEN_ENCRYPTION_KEY`: chave Fernet valida usada diretamente para criptografar tokens antes da persistencia.

Gere `OAUTH_TOKEN_ENCRYPTION_KEY` explicitamente com Python:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Nunca versione client secret, access token, refresh token ou chave Fernet.

## OAuth

O OAuth permanece a base para chamadas autenticadas na API oficial do Mercado Livre.

Endpoints:

- `GET /api/v1/integrations/mercadolivre/authorize`
- `GET /oauth/mercadolivre/callback`
- `GET /api/v1/integrations/mercadolivre/status`
- `DELETE /api/v1/integrations/mercadolivre`

Tokens sao criptografados com Fernet e nunca retornam em respostas HTTP.

## Ingestao Manual por Item

### Consultar item normalizado sem persistir

```http
GET /api/v1/integrations/mercadolivre/items/{item_id}
Authorization: Bearer <JWT>
```

Retorna `ExternalOfferInput` sanitizado e normalizado. Nao retorna tokens.

### Ingerir item

```http
POST /api/v1/integrations/mercadolivre/items/{item_id}/ingest
Authorization: Bearer <JWT>
```

Fluxo:

```text
Mercado Livre API
  -> raw item
  -> sale_price / seller quando necessario
  -> MercadoLivre adapter
  -> ExternalOfferInput
  -> IngestionService
  -> Product / ProductOffer / PriceSnapshot
```

O endpoint e interno/admin para teste nesta fase.

## Store

A ingestao exige uma `Store` existente com slug:

```text
mercadolivre
```

A coleta nao cria Store automaticamente. Se a Store nao existir, a API retorna erro claro.

## Precos

A documentacao oficial atual do Mercado Livre orienta consultar endpoints especificos de precos porque `price`, `base_price` e `original_price` de `/items` serao descontinuados para consulta de preco.

Nesta sprint, o coletor prioriza:

```text
GET /items/{item_id}/sale_price?context=channel_marketplace
```

Mapeamento:

- `current_price`: `sale_price.amount`.
- `original_price`: `sale_price.regular_amount`, quando disponivel.
- `currency`: `sale_price.currency_id`.

Fallback:

- Se `sale_price` nao estiver disponivel, usa `item.price` e `item.original_price` como fallback controlado.

Limitacao atual:

- Precos por quantidade, price lists avancadas e contextos por nivel de comprador ficam para sprint futura.

## Seller

Quando o item retorna `seller_id`, o coletor consulta `/users/{seller_id}` para obter `nickname` somente quando necessario. Existe cache em memoria por request do `MercadoLivreCollectorService`; nao ha Redis nesta sprint.

Mapeamento:

- `seller_external_id`: `seller_id`.
- `seller_name`: `users/{seller_id}.nickname`, quando disponivel.
- `seller_is_official`: `official_store_id != null`.

## Rate Limit e Retry

Para chamadas autenticadas, o client HTTP usa timeout explicito e retry limitado somente para:

- `429`
- `500`
- `502`
- `503`
- `504`

Para `429`, respeita `Retry-After` quando presente. Sem `Retry-After`, usa exponential backoff com jitter. Nao ha retry indiscriminado.

Erros tratados:

- `401`: autorizacao falhou.
- `403`: acesso proibido.
- `404`: recurso nao encontrado.
- `429`: rate limit excedido.
- `5xx`: indisponibilidade temporaria.

## Campos Normalizados

O adaptador mapeia para `ExternalOfferInput` quando a API fornece os dados:

- `source = mercadolivre`
- `external_id`
- `store_slug = mercadolivre`
- `seller_external_id`
- `seller_name`
- `seller_is_official`
- `title`
- `product_name`
- `brand_name`
- `model`
- `gtin`
- `sku`
- `url`
- `image_url`
- `current_price`
- `original_price`
- `shipping_price`
- `currency`
- `is_available`
- `is_free_shipping`
- `installment_count`
- `installment_value`
- `captured_at`

`category_name` nao e inferido a partir de `category_id` nesta sprint, para evitar inventar dados sem consultar um endpoint complementar de categorias.

## Fora do Escopo

- Busca por palavra-chave.
- Varredura massiva de catalogo.
- Scheduler, filas, Redis ou Celery.
- Scraping.
- Alertas, WhatsApp, IA ou recomendacao de promocoes.
- Comparacao historica avancada.
