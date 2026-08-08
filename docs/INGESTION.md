# Ingestao

A Sprint 0.3 cria a fundacao generica de ingestao para ofertas externas futuras. Ela nao implementa coletores reais, scraping, automacao de browser, filas ou integracoes comerciais com marketplaces. A Sprint 1.0 adiciona OAuth Mercado Livre em modulo separado, sem alterar o contrato de ingestao.

## Fluxo

```text
Collector futuro
  -> ExternalOfferInput
  -> Normalizer
  -> Matcher / Deduplicator
  -> Ingestion Service
  -> Product / ProductOffer / PriceSnapshot
```

A camada de dominio nao conhece detalhes especificos de Amazon, Mercado Livre, Steam ou qualquer outra loja.

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

## Seller

Quando `seller_external_id` ou `seller_name` sao informados, a ingestao procura o seller dentro da store correta. Se nao existir, cria um novo seller nessa store. Seller de outra loja nunca e reutilizado.

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

## Endpoint Interno

`POST /api/v1/internal/ingestion/offers`

Este endpoint exige JWT e existe para collectors futuros. Ele nao e uma API publica de usuario final.

## Limitacoes Atuais

- Matching por nome e apenas fallback controlado por slug normalizado.
- Nao ha fuzzy matching avancado.
- Nao ha controle de concorrencia especifico para ingestao simultanea da mesma oferta alem das constraints do banco.
- Nao ha filas, workers, agendamento, Redis ou Celery.
- Reconciliacao manual/assistida entre ofertas e produtos fica para sprint futura.
- Nao ha coletor real ou integracao com lojas.
