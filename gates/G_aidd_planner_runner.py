# -*- coding: utf-8 -*-
"""
Quality Gate de repositório para projetos do Planner (D13).
Retorna estritamente exit 0 (aprovado) ou exit 1 (reprovado).
"""

import sys
from pathlib import Path


def validar_projeto(caminho_projeto: Path | str) -> int:
    p = Path(caminho_projeto).resolve()
    if not p.exists() or not p.is_dir():
        print(f"[{__file__}] ERRO: Pasta '{p}' inexistente ou invalida.")
        return 1

    planner_json = p / "PLANNER.json"
    if not planner_json.exists():
        print(f"[{__file__}] ERRO: PLANNER.json nao encontrado em '{p}'.")
        return 1

    print(f"[{__file__}] SUCESSO: Projeto em '{p}' contem PLANNER.json integro.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Uso: python {__file__} <pasta-do-projeto>")
        sys.exit(1)

    sys.exit(validar_projeto(sys.argv[1]))
