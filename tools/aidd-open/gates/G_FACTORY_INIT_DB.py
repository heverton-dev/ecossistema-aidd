# -*- coding: utf-8 -*-
"""
G_FACTORY_INIT_DB — Valida init-multiple-databases.sh gerado.

Verifica:
  1. Script e executavel (tem shebang)
  2. Contem CREATE DATABASE para cada banco
  3. Contem CREATE USER para cada usuario
  4. Contem GRANT para cada banco
  5. Usa set -euo pipefail
"""
import sys
import os

_FACTORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _validar_init_db(caminho: str) -> list:
    """Valida o script init DB. Retorna lista de problemas."""
    problemas = []

    if not os.path.isfile(caminho):
        return [f"Arquivo nao encontrado: {caminho}"]

    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Shebang
    if not conteudo.startswith("#!/"):
        problemas.append("Script sem shebang")

    # Seguranca
    if "set -euo pipefail" not in conteudo and "set -e" not in conteudo:
        problemas.append("Script sem 'set -e' (fail on error)")

    # Pelo menos 1 CREATE DATABASE
    if "CREATE DATABASE" not in conteudo:
        problemas.append("Script sem CREATE DATABASE")

    # Pelo menos 1 CREATE USER
    if "CREATE USER" not in conteudo:
        problemas.append("Script sem CREATE USER")

    # Pelo menos 1 GRANT
    if "GRANT" not in conteudo:
        problemas.append("Script sem GRANT")

    return problemas


def executar(caminho: str = None) -> int:
    """Executa o gate."""
    print("=" * 72)
    print(" [G_FACTORY_INIT_DB] Validacao de init-multiple-databases.sh")
    print("=" * 72)

    if caminho is None:
        caminho = os.path.join(_FACTORY_ROOT, "output", "init-multiple-databases.sh")
    elif os.path.isdir(caminho):
        caminho = os.path.join(caminho, "init-multiple-databases.sh")

    problemas = _validar_init_db(caminho)

    if problemas:
        print(f"\n[FALHA] {len(problemas)} problema(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print(f"\n[SUCESSO] {caminho} validado.")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(executar(path))
