# PostgreSQL Centralizado

## O que é

Contêiner PostgreSQL 16 (Alpine) que serve como a **camada 4 centralizada** do Cenário A do plano AIDD-Ops. Uma única instância gerencia múltiplos bancos lógicos isolados via script `init-multiple-databases.sh`.

## Por que não múltiplos PostgreSQL?

Uma instância com bancos lógicos economiza **1-2 GB de RAM** em comparação com N contêineres PostgreSQL separados. Backup consolidado via `pg_dumpall` (Fase 10 do pipeline).

## Uso

```bash
# 1. Copiar e configurar o .env
cp .env.example .env

# 2. Editar .env com os bancos desejados
# POSTGRES_MULTIPLE_DATABASES=authentik_db,twenty_db,chatwoot_db,calcom_db

# 3. Subir
docker compose up -d

# 4. Verificar status
docker compose ps
docker compose logs postgres | grep "init]"
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `POSTGRES_ADMIN_USER` | Sim | Usuário admin do PostgreSQL |
| `POSTGRES_ADMIN_PASSWORD` | Sim | Senha do admin (sem valor default seguro) |
| `POSTGRES_MULTIPLE_DATABASES` | Sim | Lista de bancos separados por vírgula |
| `POSTGRES_PASSWORD_<banco>` | Não | Senha individual por banco (fallback: admin) |
| `POSTGRES_PORT` | Não | Porta no host (default: 5432) |
| `POSTGRES_MAX_RAM` | Não | Limite de memória (default: 1g) |

## Criação automática de usuários

Para cada banco listado em `POSTGRES_MULTIPLE_DATABASES`, o script cria automaticamente:
- O banco lógico isolado
- Um usuário dedicado `<nome_banco>_user` com senha individual
- Permissões restritas ao schema public do próprio banco

## Integração com outros blocos

Outros blocos (Twenty, Chatwoot, Cal.com, Authentik) conectam-se via rede interna `aidd_internal`. Variáveis de conexão típicas:

```
DATABASE_URL=postgresql://<banco>_user:<senha>@postgres:5432/<banco>
```

## Portas expostas

| Porta | Serviço | Nota |
|---|---|---|
| 5432 | PostgreSQL | Apenas para debug. Em produção, usar rede interna |

## Imagem

- **Oficial:** `postgres:16-alpine` (Docker Hub — PostgreSQL Global Dev Group)
- **Por que Alpine:** ~150MB vs ~400MB da variante full. Sem necessidade de compiladores em runtime.
