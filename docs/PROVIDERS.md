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
| Awin | Rede de afiliados | Consulta de programas e promocoes implementada; exige conta publisher, token e aprovacao dos anunciantes. |
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

## Awin Publisher API

A Awin e tratada como uma rede de afiliados, nao como uma loja. Cada programa retornado representa um anunciante que podera ser associado a uma `Store` em uma etapa futura de ingestao e reconciliacao.

Configure somente no ambiente local ou no cofre do ambiente de deploy:

```env
AWIN_PUBLISHER_ID=
AWIN_API_TOKEN=
AWIN_API_BASE_URL=https://api.awin.com
```

O publisher ID deve ser numerico. O token pessoal e obtido em `https://ui.awin.com/awin-api` por um usuario com permissao sobre a conta publisher.

Rotas autenticadas:

```text
GET /api/v1/integrations/awin/status
GET /api/v1/integrations/awin/programs?country_code=BR&relationship=joined
GET /api/v1/integrations/awin/promotions?page=1&page_size=20&membership=joined&promotion_status=active&promotion_type=all&region_code=BR
```

As consultas usam exclusivamente o cabecalho `Authorization: Bearer`; o token nao e colocado na URL, em respostas ou em logs. A rota de promocoes apenas consulta a API e nao persiste nem ingere dados. O limite por pagina segue o contrato oficial, entre 10 e 200 registros.

Referencias oficiais consultadas em 2026-09-09:

- Amazon Creators API: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction
- Amazon SearchItems: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/search-items
- Steam Web API: https://steamcommunity.com/dev
- Magalu Developers: https://developers.magalu.com/docs/
- Awin Brasil: https://www.awin.com/br/
- Awin API - autenticacao: https://help.awin.com/apidocs/api-authentication
- Awin API - programas: https://help.awin.com/apidocs/get-program-information
- Awin API - ofertas: https://help.awin.com/apidocs/promotions
