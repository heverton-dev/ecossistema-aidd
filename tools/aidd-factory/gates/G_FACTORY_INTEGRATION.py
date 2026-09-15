# -*- coding: utf-8 -*-
"""
G_FACTORY_INTEGRATION — Valida cadeia completa do pipeline factory.

Verifica:
  1. factory_analysis.json existe e e valido
  2. docker-compose.yml existe e e valido
  3. init-multiple-databases.sh existe e e valido
  4. Pelo menos 1 .env existe
  5. FACTORY_OUTPUT.json existe e lista todos os artefatos
"""
import json
import os
import sys
import glob

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _validar_integracao(diretorio: str) -> list:
    """Valida integridade da saida do factory."""
    problemas = []

    # factory_analysis.json
    analysis_path = os.path.join(diretorio, "factory_analysis.json")
    if not os.path.isfile(analysis_path):
        problemas.append("factory_analysis.json ausente")

    # docker-compose.yml
    compose_path = os.path.join(diretorio, "docker-compose.yml")
    if not os.path.isfile(compose_path):
        problemas.append("docker-compose.yml ausente")

    # init-multiple-databases.sh
    init_path = os.path.join(diretorio, "init-multiple-databases.sh")
    if not os.path.isfile(init_path):
        problemas.append("init-multiple-databases.sh ausente")

    # .env files
    env_files = glob.glob(os.path.join(diretorio, ".env.*"))
    if not env_files:
        problemas.append("Nenhum arquivo .env encontrado")

    # FACTORY_OUTPUT.json
    output_path = os.path.join(diretorio, "FACTORY_OUTPUT.json")
    if not os.path.isfile(output_path):
        problemas.append("FACTORY_OUTPUT.json ausente")
    else:
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                output = json.load(f)
            if "artefatos" not in output:
                problemas.append("FACTORY_OUTPUT.json sem campo 'artefatos'")
            elif len(output["artefatos"]) == 0:
                problemas.append("FACTORY_OUTPUT.json com 0 artefatos")
        except json.JSONDecodeError:
            problemas.append("FACTORY_OUTPUT.json invalido")

    return problemas


def executar(diretorio: str = None) -> int:
    """Executa o gate."""
    print("=" * 72)
    print(" [G_FACTORY_INTEGRATION] Validacao de Integracao Completa")
    print("=" * 72)

    if diretorio is None:
        diretorio = os.path.join(_FACTORY_ROOT, "output")

    problemas = _validar_integracao(diretorio)

    if problemas:
        print(f"\n[FALHA] {len(problemas)} problema(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print(f"\n[SUCESSO] Pipeline factory completo em {diretorio}")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(executar(path))
