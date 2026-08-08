# Dominio Comercial

Este documento descreve a fundacao de dominio criada na Sprint 0.2 e consumida pela ingestao da Sprint 0.3.

## Principio Central

`Product` nao e a mesma coisa que `ProductOffer`.

- `Product`: produto conceitual, sem preco.
- `ProductOffer`: uma oferta concreta desse produto em uma loja/vendedor, com preco atual administrativo.
- `PriceSnapshot`: um registro historico do preco de uma oferta em um momento.

Exemplo:

```text
Product: Galaxy Watch Ultra
  ProductOffer: Samsung Oficial na Samsung
    PriceSnapshot: 2026-08-06 10:00 - BRL 2199.00
  ProductOffer: Amazon Brasil
    PriceSnapshot: 2026-08-06 10:00 - BRL 2249.00
  ProductOffer: Mercado Livre / Samsung Oficial
    PriceSnapshot: 2026-08-06 10:00 - BRL 2089.00
```

## Brand

Representa uma marca, como Samsung, Apple, Acer ou Nike. A ingestao pode criar brand quando receber `brand_name`.

Campos principais:

- `id`
- `name`
- `slug`
- `created_at`
- `updated_at`

Regras:

- `name` e obrigatorio.
- `slug` e unico.
- `name` e indexado para pesquisa simples futura.

## Category

Representa uma categoria de produto. Pode ter uma categoria pai. A ingestao cria categoria apenas quando recebe `category_name`.

Exemplo:

```text
Eletronicos
  Smartwatches
  Celulares
Informatica
  Notebooks
  Monitores
```

Campos principais:

- `id`
- `name`
- `slug`
- `parent_id`
- `created_at`
- `updated_at`

## Store

Representa a plataforma ou loja monitorada, nao necessariamente o vendedor. A ingestao exige `store_slug` existente e nao cria lojas automaticamente.

Exemplos:

- Amazon Brasil
- Mercado Livre
- Magazine Luiza
- Samsung
- Steam

Campos principais:

- `id`
- `name`
- `slug`
- `base_url`
- `is_active`
- `created_at`
- `updated_at`

## Seller

Representa o vendedor de uma oferta dentro de uma `Store`. A ingestao localiza ou cria seller sempre dentro da store correta.

Exemplo:

```text
Store: Mercado Livre
Seller: Samsung Oficial
```

Campos principais:

- `id`
- `store_id`
- `name`
- `external_id`
- `reputation_score`
- `is_official`
- `created_at`
- `updated_at`

Relacionamento:

- `Store 1:N Seller`

## Product

Representa o produto conceitual. Nao armazena preco.

Campos principais:

- `id`
- `brand_id`
- `category_id`
- `name`
- `slug`
- `model`
- `description`
- `gtin`
- `sku`
- `image_url`
- `is_active`
- `created_at`
- `updated_at`

Relacionamentos:

- `Brand 1:N Product`
- `Category 1:N Product`
- `Product 1:N ProductOffer`

Matching de ingestao:

1. GTIN exato.
2. SKU + marca.
3. Marca + modelo.
4. Nome normalizado como fallback controlado.

## ProductOffer

Representa uma oferta concreta de um produto em uma loja e, opcionalmente, em um vendedor.

Campos principais:

- `id`
- `product_id`
- `store_id`
- `seller_id`
- `external_id`
- `url`
- `title`
- `current_price`
- `original_price`
- `shipping_price`
- `currency`
- `is_available`
- `is_prime`
- `is_free_shipping`
- `installment_count`
- `installment_value`
- `last_checked_at`
- `created_at`
- `updated_at`

Regras:

- `store_id + external_id` e unico.
- Precos nao podem ser negativos.
- `currency` inicia como `BRL`.
- A ingestao cria ou atualiza por `store_id + external_id`.

## PriceSnapshot

Representa o historico de preco de uma oferta.

Campos principais:

- `id`
- `product_offer_id`
- `price`
- `original_price`
- `shipping_price`
- `captured_at`

Regras:

- Snapshots antigos nao devem ser atualizados.
- Cada oferta tem seu proprio historico.
- Consultas de historico sao ordenadas por `captured_at`.
- A ingestao evita snapshot duplicado quando os precos nao mudaram.

## Fora do Escopo

Esta fundacao nao executa coletas externas. A Sprint 1.0 adiciona apenas OAuth do Mercado Livre para conexao de conta, sem coleta de produtos, precos ou ofertas. Nao ha scraping, browser automation, filas, IA, notificacoes, watchlist, score de promocao, cupons, cashback ou dashboard real nesta sprint.
