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

## Sprint 0.3 - Implementada

- Criar contrato `ExternalOfferInput`.
- Criar normalizacao deterministica.
- Criar matching e deduplicacao de produtos.
- Criar ingestao transacional.
- Criar endpoint interno autenticado para ingestao de ofertas.
- Garantir idempotencia de oferta e snapshots.
- Adicionar logging estruturado basico.
- Criar testes de ingestao.
- Documentar fluxo em `docs/INGESTION.md`.

## Sprint 1 - Implementada

- Criar OAuth Mercado Livre.
- Persistir tokens criptografados.
- Criar authorize, callback, status e disconnect.
- Preparar callback real sem retornar tokens.

## Sprint 2 - Implementada

- Cliente Mercado Livre autenticado para item, multiget, sale price, prices e seller.
- Retry limitado para 429/5xx com backoff, jitter e suporte a Retry-After.
- Adaptador Mercado Livre para `ExternalOfferInput`.
- `MercadoLivreCollectorService` delegando para `ingest_external_offer`.
- Endpoint `GET /api/v1/integrations/mercadolivre/items/{item_id}`.
- Endpoint `POST /api/v1/integrations/mercadolivre/items/{item_id}/ingest`.
- Testes mockados para normalizacao, ingestao, idempotencia, preco, seller, erros e rate limit.

## Sprint 3 - Planejada

- Busca por palavra-chave ou estrategia de descoberta aprovada.
- Planejar varredura controlada sem scraping.
- Evoluir consultas publicas do dominio.

## Sprints Futuras

- Motor de IA.
- Favoritos/watchlist.
- Busca avancada.
- Painel de promocoes.
- Alertas WhatsApp via Make.
- Telegram.
- Email.
