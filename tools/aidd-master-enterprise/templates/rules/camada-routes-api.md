# Camada Routes & API — Regras de Endpoints HTTP

> **Escopo:** Toda definicao de rotas HTTP em `routes.py` dos modulos e no core (`server.py`).
> **Referencia:** `templates/core/openapi.py`, `templates/core/security.py`, `templates/core/mcp_server.py`, `templates/rules/05_production_vps.md`.

---

## 1. OpenAPI 3.1 Spec (Obrigatorio)

Toda rota DEVE ser registrada no `RouteRegistry` com documentacao OpenAPI completa:

```python
from src.core.openapi import RouteRegistry

registry = RouteRegistry()

@registry.post(
    "/api/clientes",
    summary="Criar novo cliente",
    tag="Clientes",
    description="Cria um novo cliente no sistema com validacao de dados obrigatorios.",
    body_example={"nome": "Joao Silva", "email": "joao@email.com"},
    responses={
        "200": {"description": "Cliente criado com sucesso"},
        "400": {"description": "Dados invalidos"},
        "409": {"description": "Email ja cadastrado"}
    },
    auth="Bearer Token JWT"
)
def criar_cliente(request):
    ...
```

- `summary` obrigatorio em todo endpoint.
- `tag` agrupa endpoints por modulo/dominio.
- `body_example` com dados realistas para playground.
- `responses` com todos os codigos HTTP possiveis.
- Spec exportada em `/openapi.json` no padrao OpenAPI 3.1.0.

---

## 2. Swagger Studio com design-system.css

- Swagger Studio disponivel em `/docs` com UI Impeccable.
- Layout 3 colunas: Sidebar (endpoints) + Documentacao + Playground.
- Paleta de cores do design system: `--bg-body: #020617`, `--primary: #3b82f6`.
- Scrollbars de 4px, botoes em linha unica, zero emojis.
- Playground interativo com snippets em cURL, JavaScript e Python.
- Filtro de endpoints com `Ctrl+K` (Spotlight/Command Palette).
- Toast notifications para feedback (zero `window.alert`).

---

## 3. Continuous Fuzzing Integration

- Todo endpoint POST/PUT/PATCH DEVE suportar payloads malformados sem crashar.
- Validacao de Content-Type: retornar `415 Unsupported Media Type` se nao for `application/json`.
- Tamanho maximo de body: 1MB (configuravel). Retornar `413 Payload Too Large`.
- JSON malformado: retornar `400 Bad Request` com mensagem descritiva.
- Campos desconhecidos: ignorar silenciosamente ou rejeitar com `422`.
- Rate limiting por IP: 100 req/s com burst (retornar headers `X-RateLimit-*`).

---

## 4. MCP JSON-RPC 2.0 Server

Toda operacao de dominio DEVE ser exportada como ferramenta MCP:

```python
# Endpoint MCP: /mcp e /api/mcp/rpc
# Protocolo: JSON-RPC 2.0
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "criar_cliente",
        "arguments": {"nome": "Joao", "email": "joao@email.com"}
    },
    "id": "req_001"
}
```

- Ferramentas MCP listadas em `tools/list` com schema JSON de entrada/saida.
- Retorno padronizado via `Result.to_dict()` (sucesso/erro/codigo).
- Autenticacao MCP: mesmo Bearer JWT das rotas HTTP.
- Portal MCP em `/mcp` com interface de teste interativa.
- Compativel com Claude Desktop, Cursor, Antigravity e qualquer cliente MCP.

---

## 5. Bearer JWT Authentication

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

- Login: `POST /api/auth/login` retorna JWT com claims (`sub`, `role`, `tenant_id`).
- Verificacao HMAC-SHA256 em toda rota protegida.
- Claims obrigatorias: `sub` (user_id), `role`, `exp`.
- RBAC: `admin`, `operador`, `viewer` como roles padrao.
- Rotas publicas: `/api/auth/login`, `/docs`, `/openapi.json`, `/health`.
- Token expirado: retornar `401 Unauthorized` com header `WWW-Authenticate: Bearer`.
- Refresh token via `POST /api/auth/refresh` (opcional, com rotação de token).

---

## 6. Rate Limiting Headers

Toda resposta DEVE incluir headers de rate limiting:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 97
X-RateLimit-Reset: 1699999999
Retry-After: 1
```

- `X-RateLimit-Limit`: maximo de requisicoes por janela.
- `X-RateLimit-Remaining`: requisicoes restantes.
- `X-RateLimit-Reset`: timestamp Unix do reset da janela.
- `Retry-After`: segundos para retry (apenas em `429`).
- Limite excedido: retornar `429 Too Many Requests`.

---

## 7. Estrutura Padrao de uma Rota

```python
@registry.post(
    "/api/<modulo>/<recurso>",
    summary="Descricao clara da operacao",
    tag="<Modulo>",
    body_example={...},
    responses={"200": ..., "400": ..., "401": ..., "500": ...},
    auth="Bearer Token JWT"
)
def criar_recurso(request):
    # 1. Extrair e validar dados do request
    # 2. Chamar service (retorna Result)
    # 3. Retornar JSON com status code apropriado
    resultado = service.criar(dados)
    if resultado.sucesso:
        return json_response(resultado.to_dict(), status=200)
    return json_response(resultado.to_dict(), status=400)
```

- Rotas DEVEM ser finas: extrair dados, chamar service, retornar resultado.
- NUNCA colocar logica de negocio nas rotas.
- Tratamento de erros padronizado com `try/except` e retorno consistente.

---

## 8. CORS & Security Headers

```python
# Headers de seguranca obrigatorios (via security.py)
{
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

- CORS configuravel por ambiente (dev: `*`, prod: dominios especificos).
- Preflight `OPTIONS` respondido automaticamente.

---

## Checklist de Auditoria Routes & API

| # | Criterio | Gate |
|---|----------|------|
| 1 | OpenAPI 3.1 spec completa em toda rota | G_CONTRACTS |
| 2 | Swagger Studio funcional em `/docs` | G_QUALIDADE |
| 3 | Autenticacao JWT em rotas protegidas | G_SEGURANCA |
| 4 | Rate limiting headers em toda resposta | G_SEGURANCA |
| 5 | Security headers OWASP em toda resposta | G_SEGURANCA |
| 6 | MCP JSON-RPC 2.0 exportando operacoes | G_CONTRACTS |
| 7 | Validacao de Content-Type e body size | G_SEGURANCA |
| 8 | Zero logica de negocio nas rotas | G_ESTRUTURA |
| 9 | Tratamento de erro padronizado (Result) | G_CONTRACTS |
