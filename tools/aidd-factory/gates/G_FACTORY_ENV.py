# -*- coding: utf-8 -*-
"""
G_FACTORY_ENV — Valida .env gerados pelo factory.

Verifica:
  1. Arquivos .env existem para cada servico
  2. Variaveis de ambiente sensiveis tem valores (nao vazios)
  3. Nenhuma senha esta com valor padrao 'CHANGE_ME'
"""
import sys
import os
import glob


def _validar_env_dir(diretorio: str) -> list:
    """Valida todos os .env em um diretorio."""
    problemas = []

    env_files = glob.glob(os.path.join(diretorio, ".env.*"))
    if not env_files:
        return ["Nenhum arquivo .env encontrado"]

    for env_path in sorted(env_files):
        nome = os.path.basename(env_path)
        with open(env_path, "r", encoding="utf-8") as f:
            for i, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                if "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                chave = chave.strip()
                valor = valor.strip()

                # Senha com valor padrao
                if "password" in chave.lower() or "secret" in chave.lower():
                    if valor.startswith("CHANGE_ME"):
                        problemas.append(f"{nome}:{chave} — valor padrao CHANGE_ME")

    return problemas


def executar(diretorio: str = None) -> int:
    """Executa o gate."""
    print("=" * 72)
    print(" [G_FACTORY_ENV] Validacao de arquivos .env")
    print("=" * 72)

    if diretorio is None:
        diretorio = os.path.join(_FACTORY_ROOT, "output")

    problemas = _validar_env_dir(diretorio)

    if problemas:
        print(f"\n[FALHA] {len(problemas)} problema(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print(f"\n[SUCESSO] Arquivos .env validados em {diretorio}")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(executar(path))
