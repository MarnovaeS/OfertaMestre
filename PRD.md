# OfertaMestre - Product Requirements Document

## Missao

Criar uma plataforma SaaS de inteligencia para promocoes que identifica oportunidades reais de compra utilizando historico de precos, IA e regras de negocio.

## Objetivos

- Monitorar precos em multiplas lojas.
- Construir historico por oferta.
- Separar produto conceitual de oferta comercial.
- Receber ofertas externas por uma camada generica de ingestao.
- Classificar promocoes em sprint futura.
- Alertar apenas ofertas realmente vantajosas em sprint futura.
- Evoluir para um produto comercial.

## MVP Planejado

- Amazon, Mercado Livre e Steam em sprints futuras.
- Historico de precos por oferta.
- Dashboard.
- Login.
- Alertas via Make/WhatsApp em sprint futura.

## Estado Atual

A fundacao da Sprint 0.3 esta implementada. Existem backend FastAPI, frontend React/Vite, PostgreSQL via Docker Compose, Alembic, autenticacao JWT, endpoint de health, dashboard inicial com metricas zeradas, dominio comercial administrativo e camada interna de ingestao para ofertas externas futuras.

## Escopo Fora da Sprint 0.3

- Scrapers.
- Browser automation.
- Integracoes Amazon, Mercado Livre, Steam ou APIs externas de lojas.
- Filas, Redis ou Celery.
- APScheduler.
- Motor de IA.
- Notificacoes.
- Watchlist.
- Score de promocao.
- Cashback.
- Cupons.
- Dashboard real.
