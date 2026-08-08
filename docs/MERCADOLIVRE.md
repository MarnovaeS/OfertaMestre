# Mercado Livre OAuth

A Sprint 1.1 prepara o fluxo OAuth 2.0 real do Mercado Livre para teste manual de ponta a ponta. Ela nao implementa scraping, coleta de produtos, coleta de precos, reconciliacao de catalogo ou ingestao automatica de ofertas.

## Objetivo

Permitir que um usuario autenticado conecte uma conta Mercado Livre de forma segura para uso em sprints futuras.

## Variaveis de Ambiente

- `MERCADOLIVRE_CLIENT_ID`: client id do aplicativo Mercado Livre.
- `MERCADOLIVRE_CLIENT_SECRET`: client secret do aplicativo Mercado Livre.
- `MERCADOLIVRE_REDIRECT_URI`: URL publica de callback cadastrada no Mercado Livre.
- `OAUTH_TOKEN_ENCRYPTION_KEY`: chave Fernet valida usada diretamente para criptografar tokens antes da persistencia.

Gere `OAUTH_TOKEN_ENCRYPTION_KEY` explicitamente com Python:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Nao use senha arbitraria nesse campo; o valor precisa ser uma chave Fernet valida. Nunca versione `MERCADOLIVRE_CLIENT_SECRET`, tokens ou `OAUTH_TOKEN_ENCRYPTION_KEY`.

Para esta fase, o redirect URI esperado para testes externos deve apontar para:

```text
https://nature-dating-repeated.ngrok-free.dev/oauth/mercadolivre/callback
```

Esse valor nao fica hardcoded no codigo. Ele deve ser configurado por ambiente e precisa bater exatamente com o redirect cadastrado no aplicativo do Mercado Livre.

## Endpoints

### `GET /api/v1/integrations/mercadolivre/authorize`

Endpoint autenticado. Gera `state`, PKCE `code_verifier`/`code_challenge`, persiste o estado temporario no banco e retorna a URL de autorizacao do Mercado Livre.

Resposta:

```json
{
  "authorization_url": "https://auth.mercadolivre.com.br/authorization?..."
}
```

A URL contem:

- `response_type=code`
- `client_id`
- `redirect_uri`
- `state`
- `code_challenge`
- `code_challenge_method=S256`

### `GET /oauth/mercadolivre/callback`

Endpoint publico de callback do provedor. Nao exige JWT porque a chamada vem do navegador apos autorizacao no Mercado Livre. A associacao com o usuario interno e preservada pelo `state` criado previamente para o usuario autenticado.

O callback:

- valida `state`;
- valida expiracao do `state`;
- impede reutilizacao do `state`;
- recupera o PKCE verifier criptografado;
- troca o authorization code por tokens;
- criptografa tokens antes da persistencia;
- salva `provider_user_id`, quando retornado;
- marca a integracao como ativa;
- nunca retorna tokens ao navegador.

Resposta de sucesso para teste manual:

```text
Mercado Livre conectado com sucesso ao OfertaMestre.
```

### `GET /api/v1/integrations/mercadolivre/status`

Endpoint autenticado. Informa se o usuario autenticado possui integracao ativa.

Resposta conectada:

```json
{
  "connected": true,
  "provider": "mercadolivre",
  "expires_at": "2026-08-07T18:00:00Z",
  "provider_user_id": "123456"
}
```

Tokens nunca sao retornados.

### `DELETE /api/v1/integrations/mercadolivre`

Endpoint autenticado. Remove a integracao local e seus tokens criptografados.

## Teste OAuth Real

1. Configure `.env` a partir de `.env.example`.

2. Preencha somente no `.env` local:

```text
MERCADOLIVRE_CLIENT_ID=<seu_app_id>
MERCADOLIVRE_CLIENT_SECRET=<seu_client_secret>
MERCADOLIVRE_REDIRECT_URI=https://nature-dating-repeated.ngrok-free.dev/oauth/mercadolivre/callback
OAUTH_TOKEN_ENCRYPTION_KEY=<chave_fernet_gerada_localmente>
```

3. Suba o ambiente:

```bash
docker compose up --build
```

4. Verifique a API:

```bash
curl http://localhost:8000/health
```

5. Crie ou use um usuario local e obtenha um JWT:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"oauth@example.com","full_name":"OAuth User","password":"strong-password"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=oauth@example.com&password=strong-password"
```

6. Obtenha a authorization URL:

```bash
curl http://localhost:8000/api/v1/integrations/mercadolivre/authorize \
  -H "Authorization: Bearer <JWT>"
```

7. Abra `authorization_url` no navegador e autorize o aplicativo no Mercado Livre.

8. O navegador deve voltar para `/oauth/mercadolivre/callback` e exibir:

```text
Mercado Livre conectado com sucesso ao OfertaMestre.
```

9. Confirme o status da integracao:

```bash
curl http://localhost:8000/api/v1/integrations/mercadolivre/status \
  -H "Authorization: Bearer <JWT>"
```

10. Desconecte a integracao quando terminar o teste:

```bash
curl -X DELETE http://localhost:8000/api/v1/integrations/mercadolivre \
  -H "Authorization: Bearer <JWT>"
```

11. Encerre o ambiente:

```bash
docker compose down
```

## Tratamento de Erros

- `access_denied`: autorizacao negada pelo usuario no Mercado Livre.
- State invalido: o `state` nao existe ou nao pertence a uma autorizacao iniciada pelo backend.
- State expirado: a authorization URL deve ser gerada novamente.
- State reutilizado: o callback ja foi processado ou negado anteriormente.
- Authorization code invalido/expirado: gere uma nova authorization URL e repita a autorizacao.
- Refresh revogado: a integracao local e marcada como inativa.

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
