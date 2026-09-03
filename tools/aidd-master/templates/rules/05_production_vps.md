# 🌐 Produção em Alta Escala & Deploy em VPS (AIDD v4)

O AIDD v4 foi concebido para suportar milhões de requisições por dia em ambientes de produção com **Nginx**, **SSL/TLS**, **Rate Limiting** e autenticação **JSON Web Token (JWT)**.

---

## 🏛️ 1. Arquitetura de Produção em Escala

```
[ Usuários / Agentes AI (Claude / Cursor) ]
                   │
                   ▼ (HTTPS / TLS 1.3 / Porta 443)
┌─────────────────────────────────────────────────────────┐
│ NGINX High-Performance Reverse Proxy                    │
│ ├─ SSL Termination (Certbot / Let's Encrypt)            │
│ ├─ Rate Limiting (100 req/s por IP com burst)          │
│ ├─ Anti-DDoS & Buffer Overflow Protection               │
│ ├─ Gzip Compression & Static Asset Cache               │
│ └─ Upstream Pool com Keepalive Connections              │
└──────────────────────────┬──────────────────────────────┘
                           │ (HTTP Interno / Porta 3000)
┌──────────────────────────▼──────────────────────────────┐
│ AIDD Monolith Container (Non-Root User)                 │
│ ├─ JWT Middleware (HS256 Bearer Token Verification)     │
│ ├─ SQLite Concorrente (WAL Mode em Volume Persistente)  │
│ ├─ EventBus Cross-Domain & Webhook HMAC Dispatcher      │
│ ├─ Swagger Studio & OpenAPI 3.1 (/docs)                 │
│ └─ Servidor Nativo Universal MCP (/mcp)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 2. Autenticação JWT (JSON Web Token)

- **Geração de Token:** `POST /api/auth/login` com credenciais válidas.
- **Formato:** Token padrão RFC 7519 `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` assinado com HMAC-SHA256.
- **Cabeçalho nas Requisições:**
  ```http
  Authorization: Bearer <TOKEN_JWT>
  ```
- **Controle de Acesso RBAC:** Validação de claims (`role: admin`, `role: operador`).

---

## 🚀 3. Como Fazer o Deploy em Qualquer VPS (DigitalOcean, AWS, Hetzner, Oracle)

```bash
# 1. Clonar o repositório na VPS
git clone https://github.com/seu-usuario/sua-suite.git
cd sua-suite

# 2. Gerar os certificados SSL
python nginx/ssl/generate_ssl.py

# 3. Subir os containers em background
docker compose up -d --build

# 4. Verificar o status dos serviços
docker compose ps
docker compose logs -f
```
