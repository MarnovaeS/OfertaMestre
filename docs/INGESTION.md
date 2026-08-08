# Ingestao

A Sprint 0.3 cria a fundacao generica de ingestao para ofertas externas futuras. Ela nao implementa scraping, automacao de browser, filas ou integracoes comerciais diretas com marketplaces. A Sprint 1.0 adiciona OAuth Mercado Livre em modulo separado, sem alterar o contrato de ingestao. A Sprint 2 adiciona coleta manual por item_id do Mercado Livre usando API oficial e delegando para esta camada.

## Fluxo Generico

```text
Collector futuro
  -> ExternalOfferInput
  -> Normalizer
  -> Matcher / Deduplicator
  -> Ingestion Service
  -> Product / ProductOffer / PriceSnapshot
```

A camada de dominio nao conhece detalhes especificos de Amazon, Mercado Livre, Steam ou qualquer outra loja.

## Fluxo Mercado Livre

```text
Mercado Livre API oficial
  -> raw item / sale_price / seller
  -> MercadoLivre adapter
  -> ExternalOfferInput
  -> ingest_external_offer
  -> Product / ProductOffer / PriceSnapshot
```

A Store `mercadolivre` deve existir antes da coleta. Ela nao e criada automaticamente.

## Contrato de Entrada

O endpoint interno recebe `ExternalOfferInput` com os campos principais:

- `source`
- `external_id`
- `store_slug`
- `seller_external_id`
- `seller_name`
- `seller_is_official`
- `title`
- `product_name`
- `brand_name`
- `category_name`
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
- `is_prime`
- `installment_count`
- `installment_value`
- `captured_at`

Precos negativos sao rejeitados pelo schema antes da persistencia.

## Normalizacao

A normalizacao atual e deterministica e cobre:

- trim e remocao de espacos duplicados;
- normalizacao simples de moeda para caixa alta;
- URLs sem fragmento e com host em caixa baixa;
- nomes de marca e seller em formato de titulo;
- slugs ASCII em caixa baixa.

Nao ha IA, embeddings ou fuzzy matching nesta sprint.

## Matching e Deduplicacao

A prioridade de matching de produto e:

1. `gtin` exato;
2. `sku + brand`;
3. `brand + model`;
4. `product_name` normalizado como fallback controlado.

Se nenhuma correspondencia segura for encontrada, um novo `Product` e criado.

## Store

A ingestao recebe `store_slug` e exige que a `Store` ja exista. Lojas nao sao criadas automaticamente durante a ingestao.

Para Mercado Livre, o slug esperado e:

```text
mercadolivre
```

## Seller

Quando `seller_external_id` ou `seller_name` sao informados, a ingestao procura o seller dentro da store correta. Se nao existir, cria um novo seller nessa store. Seller de outra loja nunca e reutilizado.

No coletor Mercado Livre, `seller_id` vira `seller_external_id` e `users/{seller_id}.nickname` vira `seller_name` quando disponivel.

## Oferta

A oferta e localizada por `store_id + external_id`.

- Se nao existir, cria `ProductOffer`.
- Se existir, atualiza campos mutaveis.
- `external_id` da oferta existente nao e alterado.
- `product_id` da oferta existente nao e trocado automaticamente.
- Se o matching apontar para outro produto, a ingestao retorna conflito e faz rollback.

## Snapshots

A primeira ingestao de uma oferta sempre cria um `PriceSnapshot`.

Ingestoes seguintes criam snapshot somente quando houver mudanca em:

- `current_price`;
- `original_price`;
- `shipping_price`.

Se os precos forem identicos ao snapshot mais recente, nenhum snapshot duplicado e criado.

## Precos Mercado Livre

O coletor Mercado Livre prioriza `GET /items/{item_id}/sale_price?context=channel_marketplace` para obter `current_price`, `original_price` e `currency`. Quando esse endpoint nao esta disponivel, usa `item.price` e `item.original_price` como fallback controlado.

`shipping_price` e tratado separadamente: quando `shipping.free_shipping` e verdadeiro, usa `0.00`; quando a API nao informa preco de frete, permanece `null`.

## Transacao

A ingestao de uma oferta e atomica. O service usa `flush` durante o fluxo e executa `commit` apenas no final. Qualquer erro provoca rollback completo.

## Resultado

`IngestionResult` retorna:

- `product_id`
- `offer_id`
- `seller_id`
- `product_created`
- `offer_created`
- `seller_created`
- `snapshot_created`
- `matched_by`

Valores atuais de `matched_by`:

- `gtin`
- `sku_brand`
- `brand_model`
- `normalized_name`
- `created_new`

## Endpoints

### Ingestao Interna

`POST /api/v1/internal/ingestion/offers`

Este endpoint exige JWT e existe para collectors futuros. Ele nao e uma API publica de usuario final.

### Mercado Livre

- `GET /api/v1/integrations/mercadolivre/items/{item_id}`: consulta e normaliza sem persistir.
- `POST /api/v1/integrations/mercadolivre/items/{item_id}/ingest`: consulta, normaliza e persiste via ingestion.

Ambos exigem JWT e OAuth Mercado Livre conectado.

## Limitacoes Atuais

- Matching por nome e apenas fallback controlado por slug normalizado.
- Nao ha fuzzy matching avancado.
- Nao ha controle de concorrencia especifico para ingestao simultanea da mesma oferta alem das constraints do banco.
- Nao ha filas, workers, agendamento, Redis ou Celery.
- Reconciliacao manual/assistida entre ofertas e produtos fica para sprint futura.
- Nao ha scraping, busca por palavra-chave ou varredura massiva de catalogo.
- Precos avancados por quantidade e contextos adicionais do Mercado Livre ficam para sprint futura.

## Semantica de Frete

Na ingestao Mercado Livre, `shipping_price = 0.00` significa frete gratis confirmado por `free_shipping=true`. `shipping_price = null` significa frete desconhecido; nao deve ser interpretado como frete gratis e o sistema nao inventa valores de frete.
