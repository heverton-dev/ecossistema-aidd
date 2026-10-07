# -*- coding: utf-8 -*-
"""Interface publica da fatia blindagem-enterprise: unico ponto que outras fatias podem usar (ciclo-03 T10).

Expoe so o que outras fatias consomem hoje. Carregar por caminho, com nome de modulo unico
(ex.: importlib.util.spec_from_file_location("interface_blindagem_enterprise", <este arquivo>)).
"""
from pathlib import Path

_FATIA = Path(__file__).resolve().parent
RAIZ_ENTERPRISE = _FATIA / "aidd-enterprise"

__all__ = ["RAIZ_ENTERPRISE"]
