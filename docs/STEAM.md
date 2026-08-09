# Steam Provider

A integracao Steam esta dividida em duas fontes isoladas:

1. Catalog Discovery usando API oficial Steamworks `IStoreService/GetAppList/v1`.
2. Enriquecimento experimental de preco usando o endpoint publico nao documentado da Steam Store `appdetails`.

Nao ha scraping, browser automation, scheduler, IA, alertas ou coleta em massa nesta fase.

## Fonte Oficial de Catalogo

API usada para catalogo:

```text
GET https://api.steampowered.com/IStoreService/GetAppList/v1/
```

Fonte oficial: Steamworks Web API, `IStoreService/GetAppList`.

Configuracoes:

```text
STEAM_WEB_API_KEY
STEAM_WEB_API_BASE_URL=https://api.steampowered.com
```

A chave deve vir exclusivamente de variavel de ambiente. Nunca versionar, logar ou retornar `STEAM_WEB_API_KEY`.

## Fonte Experimental de Preco

API usada para preco real:

```text
GET https://store.steampowered.com/api/appdetails?appids={appid}&cc=br&filters=price_overview
```

Esta fonte e classificada como:

```text
price_source=store_appdetails
price_source_class=undocumented_public
```

`appdetails` e um endpoint publico da Steam Store, mas nao faz parte da documentacao oficial Steamworks. Por isso o enriquecimento fica atras de feature flag e deve ser tratado como experimental.

Configuracoes:

```text
STEAM_STORE_BASE_URL=https://store.steampowered.com
STEAM_APPDETAILS_ENABLED=false
STEAM_COUNTRY_CODE=br
```

Com `STEAM_APPDETAILS_ENABLED=false`, o catalogo Steam continua funcionando e apenas os endpoints de preco/ingestao retornam indisponibilidade controlada.

## Normalizacao de Preco

O OfertaMestre usa somente campos numericos de `price_overview`:

- `initial`: preco original em centavos/minor units.
- `final`: preco atual em centavos/minor units.
- `currency`: moeda.
- `discount_percent`: percentual de desconto.

Exemplo: `19990` vira `199.90`.

Campos `*_formatted` nunca sao usados como fonte numerica.

Validacoes aplicadas:

- `currency` obrigatoria.
- `final` obrigatorio e nao negativo.
- `initial` obrigatorio e nao negativo quando `price_overview` existe.
- `initial >= final`.
- `discount_percent` entre 0 e 100.
- desconto positivo exige diferenca real entre preco original e atual.

## Apps Gratuitos

Se `success=true` e nao houver `price_overview`, o OfertaMestre so considera preco zero quando a resposta provar explicitamente que o app e gratuito, por exemplo com `is_free=true`.

Se a resposta nao provar gratuidade, o preco e tratado como desconhecido e nenhuma ingestao de oferta deve ser feita.

## Fluxos

Catalogo:

```text
Steam GetAppList -> Steam adapter/service -> ProviderCatalogItem -> ProviderSyncState
```

Preco/ingestao:

```text
ProviderCatalogItem -> appdetails price enrichment -> ExternalOfferInput -> IngestionService -> Product / ProductOffer / PriceSnapshot
```

A oferta Steam usa:

- `store_slug=steam`
- `external_id={appid}`
- URL canonica `https://store.steampowered.com/app/{appid}`

## Resiliencia Operacional

O client de `appdetails` possui:

- timeout;
- retry limitado para 429 e 5xx;
- respeito a `Retry-After` quando presente;
- backoff exponencial com jitter;
- cache em memoria por `appid + country` dentro da instancia do client;
- rate limit local simples;
- circuit breaker simples apos falhas repetidas.

Nenhum token ou segredo e enviado para `appdetails`.

## Endpoints Internos

Todos exigem JWT:

```text
GET /api/v1/integrations/steam/status
GET /api/v1/integrations/steam/apps
POST /api/v1/integrations/steam/sync
GET /api/v1/integrations/steam/apps/{appid}/price
POST /api/v1/integrations/steam/apps/{appid}/ingest
```

`/status` retorna apenas:

- `provider=steam`
- `configured`
- `store_exists`

`/apps` retorna lista sanitizada com `appid`, `name`, `last_modified` e `price_change_number`.

`/sync` persiste catalogo minimo em `provider_catalog_items` e estado incremental em `provider_sync_states`. Nao cria preco nem oferta.

`/apps/{appid}/price` consulta apenas o enriquecimento experimental de preco e nao persiste dados.

`/apps/{appid}/ingest` exige que o app ja exista em `ProviderCatalogItem`, enriquece o preco e envia `ExternalOfferInput` para a camada generica de ingestao.

## Change Detection

A funcao `has_app_changed(previous, current)` considera alteracao quando muda:

- `name`
- `last_modified`
- `price_change_number`

Mudanca em `price_change_number` significa apenas: **preco possivelmente alterado**. A confirmacao depende do enriquecimento de preco.

## Provider Roadmap

1. Steam
2. Amazon Creators API / Keepa
3. Affiliate Feed Provider
4. Mercado Livre - waiting external access resolution
