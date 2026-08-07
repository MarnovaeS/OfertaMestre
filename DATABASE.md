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

### `categories`

- `slug` unico.
- `parent_id` opcional para hierarquia.
- `parent_id` usa `ON DELETE SET NULL`.

### `stores`

- Plataforma/loja monitorada.
- `slug` unico.
- `is_active` controla disponibilidade administrativa.

### `sellers`

- Pertence a uma `store`.
- `external_id` e opcional.
- `store_id + external_id` e unico quando informado.

### `products`

- Produto conceitual.
- Pode ter `brand_id` e `category_id`.
- Nao armazena preco.
- `slug` unico.

### `product_offers`

- Oferta concreta de um produto em uma loja/vendedor.
- `store_id + external_id` e unico.
- Precos possuem checks de nao negativo.
- `currency` inicia como `BRL`.

### `price_snapshots`

- Historico imutavel por oferta.
- `product_offer_id + captured_at` indexado para consulta cronologica.
- Snapshots antigos nao devem ser atualizados.

## Migrations

- `202608060001_create_users.py`
- `202608060002_create_domain_tables.py`

## Decisoes

- Datetimes usam `DateTime(timezone=True)`.
- Alembic e a fonte de verdade para alteracoes de schema.
- O modelo evita recursos exclusivos de PostgreSQL para manter os testes SQLite funcionando.
