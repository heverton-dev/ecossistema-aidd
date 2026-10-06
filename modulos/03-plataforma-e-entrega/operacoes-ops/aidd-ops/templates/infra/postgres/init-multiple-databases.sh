# PostgreSQL Centralizado — init-multiple-databases.sh
#
# Script de inicialização do PostgreSQL para criar múltiplos bancos lógicos
# isolados e seus respectivos usuários dedicados (Cenário A do plano AIDD-Ops).
#
# Comportamento:
#   1. Lê POSTGRES_MULTIPLE_DATABASES (separados por vírgula)
#   2. Para cada banco: cria o banco + usuário dedicado <banco>_user
#   3. Concede privilégios restritos ao usuário do banco
#   4. Suporta senhas individuais via POSTGRES_PASSWORD_<banco>
#
# Referência: 06-09-2026_feature-arquitetura-aidd-ops.md §5.4 e §5.5
# Montagem: /docker-entrypoint-initdb.d/01-init-multiple-databases.sh

#!/bin/bash
set -euo pipefail

# --- Função auxiliar: criar banco + usuário dedicado ---
create_user_and_database() {
    local database="$1"
    local user="${database}_user"
    local password_var="POSTGRES_PASSWORD_${database}"

    # Resolver senha: variável individual ou fallback para admin
    local password="${!password_var:-}"
    if [ -z "$password" ]; then
        password="${POSTGRES_ADMIN_PASSWORD}"
    fi

    if [ -z "$password" ]; then
        echo "[ERRO] Nenhuma senha definida para '${database}'."
        echo "  Defina POSTGRES_PASSWORD_${database} ou POSTGRES_ADMIN_PASSWORD no .env"
        exit 1
    fi

    echo "[init] Criando banco '${database}' e usuário '${user}'..."

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        -- Criar banco lógico isolado
        CREATE DATABASE "${database}"
            WITH OWNER = "${POSTGRES_USER}"
            ENCODING = 'UTF8'
            LC_COLLATE = 'en_US.utf8'
            LC_CTYPE = 'en_US.utf8'
            TEMPLATE = template0;

        -- Criar usuário dedicado para este banco
        CREATE USER "${user}" WITH ENCRYPTED PASSWORD '${password}';

        -- Conceder privilégios restritos (apenas neste banco)
        GRANT ALL PRIVILEGES ON DATABASE "${database}" TO "${user}";

        -- Conectar ao banco recém-criado para conceder permissões de schema
EOSQL

    # Conceder permissões no schema public dentro do banco específico
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$database" <<-EOSQL2
        GRANT ALL ON SCHEMA public TO "${user}";
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "${user}";
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "${user}";
EOSQL2

    echo "[init] Banco '${database}' criado com sucesso. Usuário '${user}' configurado."
}

# --- Ponto de entrada ---
if [ -z "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
    echo "[init] POSTGRES_MULTIPLE_DATABASES não definido. Pulando criação de bancos."
    exit 0
fi

echo "[init] Iniciando criação de bancos lógicos: ${POSTGRES_MULTIPLE_DATABASES}"

IFS=',' read -ra DB_ARRAY <<< "${POSTGRES_MULTIPLE_DATABASES}"
for db in "${DB_ARRAY[@]}"; do
    db=$(echo "$db" | xargs)  # trim whitespace
    if [ -n "$db" ]; then
        create_user_and_database "$db"
    fi
done

echo "[init] Todos os bancos lógicos foram criados com sucesso."
