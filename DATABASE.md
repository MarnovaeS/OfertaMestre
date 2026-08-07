# Banco de Dados

## Estado Atual

Banco configurado:

- PostgreSQL via Docker Compose.
- SQLAlchemy 2 no backend.
- Alembic para migracoes.

Tabela implementada:

- `users`

Campos principais de `users`:

- `id`
- `email`
- `full_name`
- `hashed_password`
- `is_active`
- `created_at`

## Modelo Planejado

Tabelas planejadas para sprints futuras:

- `stores`
- `categories`
- `products`
- `prices`
- `alerts`
- `watchlists`

Relacionamentos planejados:

- `users` -> `watchlists`
- `products` -> `prices`
- `stores` -> `products`
- `products` -> `categories`
- `alerts` -> `users`
