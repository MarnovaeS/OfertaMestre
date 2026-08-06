# OfertaMestre --- PRD v1.0

## Visão

**OfertaMestre** é uma plataforma de inteligência para promoções. O
objetivo não é apenas monitorar preços, mas identificar **o momento
certo para comprar**, utilizando histórico de preços, IA e regras de
negócio.

### Objetivos

-   Monitorar lojas online.
-   Construir histórico de preços.
-   Classificar promoções.
-   Enviar alertas apenas para oportunidades realmente vantajosas.
-   Evoluir para um SaaS.

## Público-alvo

Consumidores que desejam comprar melhor e evitar falsas promoções.

## Stack

### Backend

-   Python 3.13
-   FastAPI
-   SQLAlchemy 2
-   Alembic
-   APScheduler
-   PostgreSQL
-   Pydantic

### Frontend

-   React
-   Vite
-   TypeScript
-   Tailwind CSS
-   TanStack Query
-   React Router
-   Chart.js

### Infraestrutura

-   Docker
-   Docker Compose
-   Nginx
-   GitHub
-   Hostinger VPS

## Estrutura

    ofertamestre/
    ├── backend/
    ├── frontend/
    ├── docs/
    ├── docker-compose.yml
    ├── .env.example
    └── README.md

## Funcionalidades

### Sprint 0

-   Estrutura do projeto
-   Docker
-   Banco PostgreSQL
-   FastAPI
-   React
-   Login JWT
-   Dashboard inicial
-   CI/CD GitHub Actions

### Sprint 1

-   Histórico de preços
-   Coletor Mercado Livre
-   Coletor Amazon
-   Coletor Steam

### Sprint 2

-   Classificação por IA
-   Favoritos
-   Busca
-   Painel de promoções

### Sprint 3

-   Integração WhatsApp (via Make)
-   Telegram
-   Email

### Sprint 4

Adicionar: - KaBuM - Magazine Luiza - Casas Bahia - Samsung - Acer -
Shopee - Nike - Centauro - Netshoes - Dafiti

## Categorias monitoradas

-   Eletrônicos
-   Informática
-   Celulares
-   Smartwatch
-   Videogames
-   Ferramentas
-   Tênis
-   Fones de ouvido
-   Bebidas
-   Eletrodomésticos

## Modelo de dados inicial

Tabelas: - users - stores - categories - products - prices - alerts -
watchlists

## Motor de IA

Cada promoção receberá: - Nota de 0 a 100 - Motivo da classificação -
Recomendação: - Comprar agora - Aguardar

Critérios: - Histórico - Desconto real - Frete - Cupom - Cashback -
Reputação do vendedor - Sazonalidade

## Dashboard

Indicadores: - Promoções hoje - Promoções excelentes - Produtos
monitorados - Alertas enviados - Lojas online

## Notificações

Primeira versão: - WhatsApp (Make)

Depois: - Telegram - Discord - Email

## Requisitos de arquitetura

-   Código limpo
-   Testes
-   Tipagem
-   API REST
-   Modularização por loja
-   Fácil expansão

## Organização do backend

    app/
     api/
     ai/
     core/
     database/
     models/
     notifications/
     scrapers/
     services/

## Organização dos scrapers

Um arquivo por loja:

-   amazon.py
-   mercadolivre.py
-   steam.py
-   kabum.py
-   samsung.py ...

Sempre que possível utilizar APIs oficiais ou fontes permitidas. Evitar
scraping agressivo.

## Deploy

Destino: Hostinger VPS

Usar: - Docker Compose - Nginx - HTTPS - PostgreSQL

## Diretrizes para o Codex

1.  Trabalhar em pequenas entregas.
2.  Criar testes para novas funcionalidades.
3.  Manter arquitetura limpa.
4.  Documentar decisões importantes.
5.  Abrir PR por sprint.
6.  Não adicionar dependências sem justificativa.
7.  Priorizar código legível e manutenível.

## Meta do MVP

Entregar uma aplicação funcional capaz de: - Monitorar Amazon, Mercado
Livre e Steam. - Armazenar histórico de preços. - Classificar
promoções. - Exibir dashboard. - Enviar alertas via Make/WhatsApp.
