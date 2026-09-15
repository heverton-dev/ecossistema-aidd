# -*- coding: utf-8 -*-
"""AIDD-Factory pipeline phases.

Phases:
  01_analisador  - Reads PLANO-INFRAESTRUTURA.json, extracts factory_analysis.json (deterministic)
  04_compose     - Merges infra templates into unified docker-compose.yml (deterministic)
  05_init_db     - Generates init-multiple-databases.sh from bancos_logicos (deterministic)
  06_env         - Generates .env per service with crypto passwords (deterministic)
"""

FASE_REGISTRY = {
    1: ("analisador", "01_analisador", "analisador"),
    4: ("compose", "04_compose", "compose"),
    5: ("init_db", "05_init_db", "init_db"),
    6: ("env", "06_env", "env"),
}
