# Authentik SSO com PostgreSQL Próprio

## O que é

Stack completa do **Authentik** (SSO/OpenID Connect/SAML) com seu próprio PostgreSQL dedicado. Oferece autenticação centralizada (login único) para todos os serviços da stack AIDD-Ops.

## Por que PostgreSQL próprio?

O Authentik exige um PostgreSQL com schemas e configurações específicas que não são compatíveis com compartilhamento via `init-multiple-databases.sh` do bloco centralizado. Por isso, ele mantém sua própria instância dedicada — esta é uma restrição técnica documentada pela equipe do Authentik.

## Uso

```bash
# 1. Copiar e configurar o .env
cp .env.example .env

# 2. Gerar chave secreta
# openssl rand -hex 32
# Coloque o resultado em AUTHENTIK_SECRET_KEY

# 3. Subir
docker compose up -d

# 4. Verificar status
docker compose ps
docker compose logs authentik-server | grep "started"
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `AUTHENTIK_DB_PASSWORD` | Sim | Senha do banco PostgreSQL |
| `AUTHENTIK_SECRET_KEY` | Sim | Chave secreta (gerar com `openssl rand -hex 32`) |
| `AUTHENTIK_DB_NAME` | Não | Nome do banco (default: authentik) |
| `AUTHENTIK_DB_USER` | Não | Usuário do banco (default: authentik) |
| `AUTHENTIK_HTTP_PORT` | Não | Porta HTTP (default: 9000) |
| `AUTHENTIK_HTTPS_PORT` | Não | Porta HTTPS (default: 9443) |

## Integração com outros blocos

O Authentik fornece OIDC para todos os demais serviços. Após configurar provedores OIDC no dashboard, cada serviço conecta via:

```
AUTHENTIK_ISSUER=http://authentik-server:9000/application/o/<app-slug>/
AUTHENTIK_CLIENT_ID=<client_id>
AUTHENTIK_CLIENT_SECRET=<client_secret>
```

## Portas expostas

| Porta | Serviço | Nota |
|---|---|---|
| 9000 | Authentik HTTP | Interface admin + API |
| 9443 | Authentik HTTPS | HTTPS direto (alternativo ao Traefik) |

## Imagens

- **Servidor/Worker:** `ghcr.io/goauthentik/server:2025.4` (GHCR — Authentik Project)
- **PostgreSQL:** `postgres:16-alpine` (Docker Hub — PostgreSQL Global Dev Group)
- **Sem Dockerfile próprio** — imagens oficiais cobrem 100% do caso de uso.
