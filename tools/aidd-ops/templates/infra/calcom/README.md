# Cal.com

## O que é

Plataforma open-source de **agendamento e booking** (Cal.com) — alternativa ao Calendly. Conecta-se ao PostgreSQL centralizado do bloco `postgres/` e usa Redis para cache.

## Dependências

- **PostgreSQL centralizado:** banco `calcom_db` criado automaticamente pelo `init-multiple-databases.sh` do bloco `postgres/`.
- **Redis:** incluído neste bloco (requerido pelo Cal.com para cache de sessões).

## Uso

```bash
# 1. Copiar e configurar o .env
cp .env.example .env

# 2. Gerar as chaves de segurança
# openssl rand -hex 32  (repetir 2 vezes para NEXTAUTH_SECRET e ENCRYPTION_KEY)

# 3. Subir (certifique-se de que o PostgreSQL centralizado já está rodando)
docker compose up -d

# 4. Rodar migrações (primeira vez)
docker compose exec calcom-server npx prisma migrate deploy

# 5. Verificar status
docker compose ps
docker compose logs calcom-server | grep "ready"
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `CALCOM_DB_PASSWORD` | Sim | Senha do banco calcom_db |
| `CALCOM_NEXTAUTH_SECRET` | Sim | Segredo NextAuth (openssl rand -hex 32) |
| `CALCOM_ENCRYPTION_KEY` | Sim | Chave de criptografia |
| `POSTGRES_HOST` | Não | Host do PostgreSQL (default: postgres) |
| `CALCOM_DB_NAME` | Não | Nome do banco (default: calcom_db) |
| `CALCOM_DB_USER` | Não | Usuário do banco (default: calcom_user) |
| `CALCOM_LICENSE_KEY` | Não | Chave de licença premium |
| `CALCOM_PORT` | Não | Porta do servidor (default: 3000) |

## Integração com outros blocos

- **PostgreSQL:** conecta via rede `aidd_internal` ao bloco `postgres/`.
- **Traefik:** para expor publicamente, adicione labels Traefik ao container `calcom-server`.
- **Twenty CRM (nicho clínicas/energia solar):** integração bidirecional via API para sincronizar agendamentos com contatos.

## Portas expostas

| Porta | Serviço | Nota |
|---|---|---|
| 3000 | Cal.com | API + Interface de agendamento |

## Imagens

- **Cal.com:** `calcom/cal.com:latest` (Docker Hub — Cal.com Inc)
- **Redis:** `redis:7-alpine` (Docker Hub — Redis Ltd)
- **Sem Dockerfile próprio** — imagens oficiais cobrem 100% do caso de uso.
