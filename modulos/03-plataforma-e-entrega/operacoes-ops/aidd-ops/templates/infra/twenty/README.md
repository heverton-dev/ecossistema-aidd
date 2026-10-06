# Twenty CRM

## O que é

CRM open-source (Twenty) com dois componentes: **server** (API/backend NestJS) e **front** (interface React). Usa Redis para cache/sessões e conecta-se ao PostgreSQL centralizado do bloco `postgres/`.

## Dependências

- **PostgreSQL centralizado:** banco `twenty_db` criado automaticamente pelo `init-multiple-databases.sh` do bloco `postgres/`.
- **Redis:** incluído neste bloco (requerido pelo Twenty para sessões e filas).

## Uso

```bash
# 1. Copiar e configurar o .env
cp .env.example .env

# 2. Gerar os 4 tokens de segurança
# openssl rand -hex 32  (repetir 4 vezes)

# 3. Subir (certifique-se de que o PostgreSQL centralizado já está rodando)
docker compose up -d

# 4. Verificar status
docker compose ps
docker compose logs twenty-server | grep "started"
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `TWENTY_DB_PASSWORD` | Sim | Senha do banco twenty_db |
| `TWENTY_ACCESS_TOKEN_SECRET` | Sim | Token de acesso (openssl rand -hex 32) |
| `TWENTY_LOGIN_TOKEN_SECRET` | Sim | Token de login |
| `TWENTY_REFRESH_TOKEN_SECRET` | Sim | Token de refresh |
| `TWENTY_FILE_TOKEN_SECRET` | Sim | Token de arquivos |
| `POSTGRES_HOST` | Não | Host do PostgreSQL (default: postgres) |
| `TWENTY_DB_NAME` | Não | Nome do banco (default: twenty_db) |
| `TWENTY_DB_USER` | Não | Usuário do banco (default: twenty_user) |
| `TWENTY_SERVER_HOST` | Não | Host Traefik da API (default: twenty.localhost) |
| `TWENTY_FRONT_HOST` | Não | Host Traefik do frontend (default: twenty-ui.localhost) |

## Integração com outros blocos

- **PostgreSQL:** conecta via rede `aidd_internal` ao bloco `postgres/`.
- **Traefik (NIH #16):** Twenty já vem com labels de roteamento Traefik habilitados.
  Servidor (`twenty-server:3000`) roteado em `TWENTY_SERVER_HOST` e frontend
  (`twenty-front:3001`) em `TWENTY_FRONT_HOST`. Não há porta de host publicada —
  o acesso é exclusivamente via reverse proxy (sem colisão na porta 3000).

## Acesso via Traefik

Aponte o DNS/`/etc/hosts` para o IP do host onde o Traefik roda:

```
ip.do.host    twenty.localhost twenty-ui.localhost
```

Acesso: `https://twenty-ui.localhost` (frontend) e `https://twenty.localhost` (API).

## Imagens

- **Twenty:** `ghcr.io/twentyhq/twenty:latest` (GHCR — Twenty PBC)
- **Redis:** `redis:7-alpine` (Docker Hub — Redis Ltd)
- **Sem Dockerfile próprio** — imagens oficiais cobrem 100% do caso de uso.
