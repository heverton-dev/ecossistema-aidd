# -*- coding: utf-8 -*-
"""Interface publica da fatia operacoes-ops: unico ponto que outras fatias podem usar (ciclo-03 T10).

Expoe so o que outras fatias consomem hoje. Carregar por caminho, com nome de modulo unico
(ex.: importlib.util.spec_from_file_location("interface_operacoes_ops", <este arquivo>)).
"""
from pathlib import Path

_FATIA = Path(__file__).resolve().parent
RAIZ_OPS = _FATIA / "aidd-ops"
DIR_SCRIPTS_OPS = RAIZ_OPS / "scripts"
DIR_FASES_OPS = DIR_SCRIPTS_OPS / "phases_ops"
DIR_TEMPLATES_INFRA = RAIZ_OPS / "templates" / "infra"
DIR_NICHOS_INFRA = DIR_TEMPLATES_INFRA / "nichos"
ARQ_REQUISITOS_RECURSOS = RAIZ_OPS / "data" / "requisitos_recursos.json"

__all__ = ["RAIZ_OPS", "DIR_SCRIPTS_OPS", "DIR_FASES_OPS", "DIR_TEMPLATES_INFRA", "DIR_NICHOS_INFRA", "ARQ_REQUISITOS_RECURSOS"]
