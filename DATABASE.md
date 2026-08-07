# Banco de Dados

## Estado Atual

Banco configurado:

- PostgreSQL via Docker Compose.
- SQLAlchemy 2 no backend.
- Alembic para migracoes.

Tabelas implementadas:

- `users`
- `brands`
- `categories`
- `stores`
- `sellers`
- `products`
- `product_offers`
- `price_snapshots`

A Sprint 0.3 nao cria novas tabelas. A ingestao reutiliza o modelo de dominio existente.

## Users

Campos principais:

- `id`
- `email`
- `full_name`
- `hashed_password`
- `is_active`
- `created_at`

A tabela `users` foi mantida compativel com a migration inicial.

## Dominio Comercial

### `brands`

- `slug` unico.
- `name` indexado para pesquisa simples.
- Pode ser criado pela ingestao quando `brand_name` e informado.

### `categories`

- `slug` unico.
- `parent_id` opcional para hierarquia.
- `parent_id` usa `ON DELETE SET NULL`.
- Pode ser criada pela ingestao quando `category_name` e informado.

### `stores`

- Plataforma/loja monitorada.
- `slug` unico.
- `is_active` controla disponibilidade administrativa.
- A ingestao exige store existente e nao cria lojas automaticamente.

### `sellers`

- Pertence a uma `store`.
- `external_id` e opcional.
- `store_id + external_id` e unico quando informado.
- A ingestao nunca reutiliza seller de outra store.

### `products`

- Produto conceitual.
- Pode ter `brand_id` e `category_id`.
- Nao armazena preco.
- `slug` unico.
- A ingestao tenta deduplicar por GTIN, SKU + marca, marca + modelo e nome normalizado.

### `product_offers`

- Oferta concreta de um produto em uma loja/vendedor.
- `store_id + external_id` e unico.
- Precos possuem checks de nao negativo.
- `currency` inicia como `BRL`.
- A ingestao cria ou atualiza oferta por `store_id + external_id`.

### `price_snapshots`

- Historico imutavel por oferta.
- `product_offer_id + captured_at` indexado para consulta cronologica.
- Snapshots antigos nao devem ser atualizados.
- A ingestao cria snapshot somente quando os precos mudam em relacao ao snapshot mais recente.

## Migrations

- `202608060001_create_users.py`
- `202608060002_create_domain_tables.py`

## Decisoes

- Datetimes usam `DateTime(timezone=True)`.
- Alembic e a fonte de verdade para alteracoes de schema.
- O modelo evita recursos exclusivos de PostgreSQL para manter os testes SQLite funcionando.
- A ingestao controla transacao no service e evita commits intermediarios.
