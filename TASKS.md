# Backlog

## Sprint 0 - Implementada

- Configurar monorepo.
- Criar Docker Compose.
- Configurar PostgreSQL.
- Configurar Alembic.
- Criar autenticacao JWT.
- Criar CRUD minimo de usuarios para autenticacao.
- Criar dashboard inicial com metricas zeradas.
- Criar testes automatizados basicos.
- Configurar GitHub Actions.

## Sprint 0.1 - Implementada

- Corrigir Markdown para UTF-8.
- Corrigir caracteres corrompidos.
- Atualizar documentacao para refletir o codigo existente.
- Padronizar endpoints com `/api/v1`.
- Criar pastas base solicitadas sem mover codigo.
- Fixar versoes das dependencias do frontend.
- Validar testes e build.

## Sprint 0.2 - Implementada

- Criar dominio comercial base.
- Criar tabelas `brands`, `categories`, `stores`, `sellers`, `products`, `product_offers` e `price_snapshots`.
- Separar `Product` de `ProductOffer`.
- Criar services internos por entidade.
- Criar endpoints CRUD administrativos basicos.
- Proteger escrita com JWT.
- Manter leitura publica.
- Criar historico de preco por oferta.
- Criar seed idempotente de lojas iniciais.
- Criar testes de dominio.
- Atualizar documentacao.

## Sprint 1 - Planejada

- Definir estrategia de coleta sem implementar scraping antecipado.
- Implementar primeiro conector aprovado pelo roadmap.
- Evoluir consultas publicas do dominio.
- Planejar ingestao de snapshots.

## Sprints Futuras

- Motor de IA.
- Favoritos/watchlist.
- Busca avancada.
- Painel de promocoes.
- Alertas WhatsApp via Make.
- Telegram.
- Email.
