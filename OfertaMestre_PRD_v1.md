# OfertaMestre - PRD v1.0

## Visao

**OfertaMestre** e uma plataforma de inteligencia para promocoes. O objetivo nao e apenas monitorar precos, mas identificar o momento certo para comprar utilizando historico de precos, IA e regras de negocio.

## Objetivos

- Monitorar lojas online.
- Construir historico de precos.
- Classificar promocoes.
- Enviar alertas apenas para oportunidades realmente vantajosas.
- Evoluir para um SaaS.

## Publico-alvo

Consumidores que desejam comprar melhor e evitar falsas promocoes.

## Stack Planejada

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Pydantic
- APScheduler, planejado para rotinas futuras

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS, planejado
- TanStack Query, planejado
- React Router, planejado
- Chart.js, planejado

### Infraestrutura

- Docker
- Docker Compose
- Nginx para servir o frontend em container
- GitHub Actions
- Hostinger VPS, planejado

## Estrutura Atual

```text
ofertamestre/
├── backend/
├── frontend/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Funcionalidades

### Sprint 0 - Implementada

- Estrutura do projeto.
- Docker Compose.
- Banco PostgreSQL.
- FastAPI.
- React + Vite + TypeScript.
- Login JWT no backend.
- Dashboard inicial com metricas zeradas.
- CI GitHub Actions.

### Sprint 0.1 - Consolidacao

- Corrigir documentacao e encoding.
- Alinhar endpoints documentados com `/api/v1`.
- Criar pastas base para evolucao futura sem mover codigo.
- Fixar versoes de dependencias.
- Validar testes e build.

### Sprint 1 - Planejada

- Historico de precos.
- Coletor Mercado Livre.
- Coletor Amazon.
- Coletor Steam.

### Sprint 2 - Planejada

- Classificacao por IA.
- Favoritos.
- Busca.
- Painel de promocoes.

### Sprint 3 - Planejada

- Integracao WhatsApp via Make.
- Telegram.
- Email.

### Sprint 4 - Planejada

- KaBuM.
- Magazine Luiza.
- Casas Bahia.
- Samsung.
- Acer.
- Shopee.
- Nike.
- Centauro.
- Netshoes.
- Dafiti.

## Modelo de Dados Planejado

Tabelas planejadas:

- users
- stores
- categories
- products
- prices
- alerts
- watchlists

Tabela implementada atualmente:

- users

## Motor de IA Planejado

Cada promocao recebera:

- Nota de 0 a 100.
- Motivo da classificacao.
- Recomendacao: comprar agora, aguardar ou nao recomendado.

Criterios planejados:

- Historico.
- Desconto real.
- Frete.
- Cupom.
- Cashback.
- Reputacao do vendedor.
- Sazonalidade.

## Dashboard Atual

Indicadores expostos pelo backend em `GET /api/v1/dashboard/summary`:

- Promocoes hoje.
- Promocoes excelentes.
- Produtos monitorados.
- Alertas enviados.
- Lojas online.

Na Sprint 0, todos os valores retornam `0` porque a ingestao de dados ainda nao existe.

## Diretrizes

1. Trabalhar em pequenas entregas.
2. Criar testes para novas funcionalidades.
3. Manter arquitetura limpa.
4. Documentar decisoes importantes.
5. Abrir PR por sprint.
6. Nao adicionar dependencias sem justificativa.
7. Priorizar codigo legivel e manutenivel.
