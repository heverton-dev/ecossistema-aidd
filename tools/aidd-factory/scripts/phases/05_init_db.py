# -*- coding: utf-8 -*-
"""
AIDD-Factory — Fase 5: Gerador de init-multiple-databases.sh.

Gera o script bash de inicializacao do PostgreSQL centralizado
a partir da lista de bancos logicos do factory_analysis.
100% deterministico — zero LLM.
"""
import os
import sys

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from core.result import Result

_SCRIPT_TEMPLATE = '''#!/bin/bash
# =============================================================================
# AIDD-Factory — init-multiple-databases.sh
# Gerado automaticamente pelo pipeline factory.
# Cria bancos logicos isolados + usuarios dedicados no PostgreSQL centralizado.
# =============================================================================
set -euo pipefail

# Ler variavel de ambiente com lista de bancos (separados por virgula)
# Formato: BANCOS_LOGICOS="banco1:usuario1,banco2:usuario2,..."
BANCOS_LOGICOS="${{BANCOS_LOGICOS:-{bancos_default}}}"

IFS=',' read -ra BANCOS <<< "$BANCOS_LOGICOS"

for entry in "${{BANCOS[@]}}"; do
    IFS=':' read -r DB_NAME DB_USER <<< "$entry"

    echo "[init-db] Criando banco: $DB_NAME (usuario: $DB_USER)"

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE $DB_NAME;
        CREATE USER $DB_USER WITH ENCRYPTED PASSWORD 'CHANGE_ME_${{DB_NAME}}';
        GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
        ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
EOSQL

    # Conceder privilegios no schema public
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL2
        GRANT ALL ON SCHEMA public TO $DB_USER;
        GRANT ALL ON ALL TABLES IN SCHEMA public TO $DB_USER;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOSQL2

    echo "[init-db] Banco $DB_NAME criado com sucesso."
done

echo "[init-db] Todos os bancos logicos foram criados."
'''


def gerar_init_db(analysis: dict, pasta_saida: str) -> Result:
    """Gera init-multiple-databases.sh a partir do factory_analysis.

    Args:
        analysis: Dicionario do factory_analysis.json.
        pasta_saida: Diretorio onde salvar o script.

    Returns:
        Result.ok(conteudo_script) ou Result.fail.
    """
    bancos = analysis.get("bancos_logicos", [])

    if not bancos:
        return Result.ok("# Nenhum banco logico necessario.\nexit 0\n")

    # Montar string default para BANCOS_LOGICOS
    bancos_default = ",".join(
        f"{b['nome']}:{b['usuario']}" for b in bancos
    )

    conteudo = _SCRIPT_TEMPLATE.format(bancos_default=bancos_default)

    return Result.ok(conteudo)
