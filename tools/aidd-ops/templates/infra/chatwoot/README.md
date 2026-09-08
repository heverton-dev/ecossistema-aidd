# Chatwoot

## O que é

Plataforma open-source de **atendimento ao cliente** (chat, WhatsApp, e-mail, redes sociais) composta por: **rails** (API/backend Ruby on Rails), **sidekiq** (processador de filas background) e **Redis** (cache/filas). Conecta-se ao PostgreSQL centralizado do bloco `postgres/`.

## Dependências

- **PostgreSQL centralizado:** banco `chatwoot_db` criado automaticamente pelo `init-multiple-databases.sh` do bloco `postgres/`.
- **Redis:** incluído neste bloco (requerido pelo Chatwoot para filas Sidekiq e cache).

## Uso

```bash
# 1. Copiar e configurar o .env
cp .env.example .env

# 2. Gerar SECRET_KEY_BASE
# rake secret  (ou: ruby -e "require 'securerandom'; puts SecureRandom.hex(64)")

# 3. Subir (certifique-se de que o PostgreSQL centralizado já está rodando)
docker compose up -d

# 4. Rodar migrações (primeira vez)
docker compose exec chatwoot-rails bundle exec rails db:chatwoot:prepare

# 5. Verificar status
docker compose ps
docker compose logs chatwoot-rails | grep "listening"
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `CHATWOOT_DB_PASSWORD` | Sim | Senha do banco chatwoot_db |
| `CHATWOOT_SECRET_KEY_BASE` | Sim | Chave secreta Rails (rake secret) |
| `POSTGRES_HOST` | Não | Host do PostgreSQL (default: postgres) |
| `CHATWOOT_DB_NAME` | Não | Nome do banco (default: chatwoot_db) |
| `CHATWOOT_DB_USER` | Não | Usuário do banco (default: chatwoot_user) |
| `CHATWOOT_HOST` | Não | Host Traefik do Chatwoot (default: chat.localhost) |

## Integração com outros blocos

- **PostgreSQL:** conecta via rede `aidd_internal` ao bloco `postgres/`.
- **Traefik (NIH #16):** Chatwoot já vem com labels de roteamento Traefik habilitados.
  `chatwoot-rails:3000` é roteado em `CHATWOOT_HOST`. Não há porta de host
  publicada — o acesso é exclusivamente via reverse proxy (sem colisão na porta 3000).
- **Evolution API (nicho clínicas/farmácias):** integração via webhook para WhatsApp.

## Acesso via Traefik

Aponte o DNS/`/etc/hosts` para o IP do host onde o Traefik roda:

```
ip.do.host    chat.localhost
```

Acesso: `https://chat.localhost`.

## Imagens

- **Chatwoot:** `chatwoot/chatwoot:latest` (Docker Hub — Chatwoot Inc)
- **Redis:** `redis:7-alpine` (Docker Hub — Redis Ltd)
- **Sem Dockerfile próprio** — imagens oficiais cobrem 100% do caso de uso.
