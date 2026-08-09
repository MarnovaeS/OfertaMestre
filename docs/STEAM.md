# Steam Provider

A Sprint 2.1 adiciona a Steam como provider de **Catalog Discovery** usando apenas API oficial Steamworks. Nao ha scraping, scheduler, IA, alertas ou ingestao de oferta com preco nesta sprint.

## Endpoint Oficial

API usada:

```text
GET https://partner.steam-api.com/IStoreService/GetAppList/v1/
```

Fonte oficial: Steamworks Web API, `IStoreService/GetAppList`.

A chave deve vir exclusivamente de:

```text
STEAM_WEB_API_KEY
```

Nunca versionar, logar ou retornar essa chave.

## Catalog Discovery

Fluxo atual:

```text
Steam GetAppList
  -> Steam adapter/service
  -> ProviderCatalogItem
  -> ProviderSyncState
  -> futura etapa de enriquecimento de preco
```

Nesta sprint, Steam nao cria `ExternalOfferInput`, `ProductOffer` ou `PriceSnapshot`, porque `GetAppList` nao retorna preco atual.

## Dados Disponiveis

Cada app pode trazer:

- `appid`
- `name`
- `last_modified`
- `price_change_number`

`last_modified` indica alteracao em informacoes ou preco do app. `price_change_number` alterado indica que o preco **pode** ter mudado. Isso nao significa que o novo preco e conhecido.

## Dados Nao Disponiveis Nesta Fonte

`IStoreService/GetAppList/v1` nao fornece:

- preco atual;
- preco anterior;
- moeda;
- desconto;
- disponibilidade comercial detalhada.

Por isso o OfertaMestre nao inventa preco e nao cria historico de preco para Steam nesta sprint.

## Paginacao

Parametros suportados:

- `max_results`: limite por pagina, limitado pela API interna do OfertaMestre.
- `last_appid`: cursor da pagina anterior.
- `modified_since`: enviado como `if_modified_since`.
- `include_games`: default `true`.
- `include_dlc`: default `false`.

A resposta oficial e ordenada por `appid`; chamadas seguintes devem usar o ultimo `appid` como `last_appid`.

## Endpoints Internos

Todos exigem JWT:

```text
GET /api/v1/integrations/steam/status
GET /api/v1/integrations/steam/apps
POST /api/v1/integrations/steam/sync
```

`/status` retorna apenas:

- `configured`
- `provider=steam`
- `store_exists`

`/apps` retorna lista sanitizada com `appid`, `name`, `last_modified` e `price_change_number`.

`/sync` persiste catalogo minimo em `provider_catalog_items` e estado incremental em `provider_sync_states`.

## Change Detection

A funcao `has_app_changed(previous, current)` considera alteracao quando muda:

- `name`
- `last_modified`
- `price_change_number`

Mudanca em `price_change_number` significa apenas: **preco possivelmente alterado**.

## Provider Roadmap

1. Steam
2. Amazon Creators API / Keepa
3. Affiliate Feed Provider
4. Mercado Livre - waiting external access resolution
