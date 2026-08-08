# Mercado Livre OAuth

A Sprint 1.0 implementa somente a fundacao OAuth 2.0 do Mercado Livre. Ela nao implementa scraping, coleta de produtos, coleta de precos, reconciliacao de catalogo ou ingestao automatica de ofertas.

## Objetivo

Permitir que um usuario autenticado conecte uma conta Mercado Livre de forma segura para uso em sprints futuras.

## Variaveis de Ambiente

- `MERCADOLIVRE_CLIENT_ID`: client id do aplicativo Mercado Livre.
- `MERCADOLIVRE_CLIENT_SECRET`: client secret do aplicativo Mercado Livre.
- `MERCADOLIVRE_REDIRECT_URI`: URL publica de callback cadastrada no Mercado Livre.
- `OAUTH_TOKEN_ENCRYPTION_KEY`: chave local usada para criptografar tokens antes da persistencia.

Para esta fase, o redirect URI esperado para testes externos deve apontar para:

```text
https://nature-dating-repeated.ngrok-free.dev/oauth/mercadolivre/callback
```

Esse valor nao fica hardcoded no codigo. Ele deve ser configurado por ambiente.

## Endpoints

### `GET /api/v1/integrations/mercadolivre/authorize`

Endpoint autenticado. Gera `state`, PKCE `code_verifier`/`code_challenge`, persiste o estado temporario no banco e retorna a URL de autorizacao do Mercado Livre.

Resposta:

```json
{
  "authorization_url": "https://auth.mercadolivre.com.br/authorization?..."
}
```

### `GET /oauth/mercadolivre/callback`

Endpoint publico de callback do provedor. Recebe `code` e `state`, valida o `state`, recupera o PKCE verifier, troca o codigo por tokens, criptografa os tokens e persiste a integracao.

Resposta:

```json
{
  "status": "connected",
  "provider": "mercadolivre"
}
```

Tokens nunca sao retornados ao frontend.

### `GET /api/v1/integrations/mercadolivre/status`

Endpoint autenticado. Informa se o usuario autenticado possui integracao ativa.

### `DELETE /api/v1/integrations/mercadolivre`

Endpoint autenticado. Remove a integracao local e seus tokens criptografados.

## Persistencia

### `oauth_states`

Tabela temporaria para protecao CSRF e PKCE:

- `user_id`
- `provider`
- `state_hash`
- `code_verifier`
- `redirect_uri`
- `expires_at`
- `consumed`

O `state` puro nao e persistido; apenas hash SHA-256. O `code_verifier` e persistido criptografado.

### `oauth_integrations`

Tabela de integracoes OAuth por usuario:

- `user_id`
- `provider`
- `provider_user_id`
- `access_token`
- `refresh_token`
- `token_type`
- `expires_at`
- `scope`
- `is_active`

Existe unicidade por `user_id + provider`.

## Refresh de Token

`get_valid_access_token` retorna o token atual quando ainda e valido. Quando o token esta perto de expirar, usa o `refresh_token`, atualiza os tokens criptografados e substitui o refresh token quando o provedor retornar um novo.

Se o refresh falhar por autorizacao revogada, a integracao local e marcada como inativa.

## Seguranca

- OAuth `state` aleatorio e validado no callback.
- PKCE S256 habilitado.
- Tokens sao criptografados com Fernet antes de ir ao banco.
- O client HTTP tem timeout explicito.
- Segredos nao sao logados.
- O callback nunca retorna tokens.

## Fora do Escopo

- Scrapers.
- Coleta de produtos ou precos.
- Jobs ou agendadores.
- Reconciliacao de ofertas/produtos.
- Sincronizacao de catalogo Mercado Livre.
