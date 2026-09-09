# Providers e canais de dados

O OfertaMestre integra apenas APIs, feeds e programas oficialmente autorizados. Uma loja cadastrada no dominio nao representa uma integracao ativa.

## Estados

- `connected`: autorizacao de usuario concluida e ativa.
- `configured`: credenciais tecnicas completas; nao implica aprovacao comercial.
- `credentials_required`: o conector existe, mas faltam variaveis de ambiente.
- `approval_required`: depende da aprovacao de publisher, seller ou anunciante.
- `partnership_required`: requer feed ou contrato direto ainda nao validado.

## Matriz atual

| Provider | Canal | Situacao |
| --- | --- | --- |
| Mercado Livre | OAuth oficial | Conexao de conta; a aplicacao testada nao recebeu acesso a busca publica de terceiros. |
| Steam | Steam Web API | Catalogo oficial. Preco por `appdetails` e experimental, desativavel e registrado como fonte publica nao documentada. |
| Amazon Brasil | Creators API | Busca implementada; exige Amazon Associates aceito, Partner Tag e credenciais Creators API. |
| Magazine Luiza | API de Sellers | Voltada aos dados do seller autorizado, nao ao catalogo publico completo. |
| Awin | Rede de afiliados | Aguardando conta publisher e aprovacao dos anunciantes/feeds. |
| Casas Bahia, Centauro, Nike, Adidas e Shopee | Afiliacao ou parceria | Aguardando canal e contrato aprovados. |
| Havan | Parceria direta | Nenhuma API publica oficial foi validada. |

## Amazon Creators API

Configure somente no ambiente local ou no cofre do ambiente de deploy:

```env
AMAZON_CREATORS_CLIENT_ID=
AMAZON_CREATORS_CLIENT_SECRET=
AMAZON_CREATORS_PARTNER_TAG=
AMAZON_CREATORS_MARKETPLACE=www.amazon.com.br
```

Rotas autenticadas:

```text
GET /api/v1/integrations/amazon/status
GET /api/v1/integrations/amazon/search?keywords=notebook&item_count=10
```

O token OAuth cliente e mantido apenas em memoria e renovado antes de expirar. Credenciais, token e cabecalho `Authorization` nunca fazem parte das respostas.

Referencias oficiais consultadas em 2026-09-09:

- Amazon Creators API: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction
- Amazon SearchItems: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/search-items
- Steam Web API: https://steamcommunity.com/dev
- Magalu Developers: https://developers.magalu.com/docs/
- Awin Brasil: https://www.awin.com/br/
