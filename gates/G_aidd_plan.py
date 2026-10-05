# -*- coding: utf-8 -*-
"""
Quality Gate de repositório para pastas de planos (D13).
Retorna estritamente exit 0 (aprovado) ou exit 1 (reprovado).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.gerenciador_planos import verificar_cercas_arquivo


def validar_pasta_plano(caminho_pasta: Path | str) -> int:
    p = Path(caminho_pasta).resolve()
    if not p.exists() or not p.is_dir():
        print(f"[{__file__}] ERRO: Pasta '{p}' inexistente ou invalida.")
        return 1

    proc_file = p / "00-PROCESSO-E-DECISOES.md"
    if not proc_file.exists():
        print(f"[{__file__}] ERRO: 00-PROCESSO-E-DECISOES.md nao encontrado em '{p}'.")
        return 1

    arquivos_md = list(p.glob("*.md"))
    if not arquivos_md:
        print(f"[{__file__}] ERRO: Nenhum arquivo Markdown encontrado em '{p}'.")
        return 1

    for arq in arquivos_md:
        valido, msg = verificar_cercas_arquivo(arq)
        if not valido:
            print(f"[{__file__}] ERRO de cercas em '{arq}': {msg}")
            return 1

    print(f"[{__file__}] SUCESSO: Plano em '{p}' conforme com regras e cercas.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Uso: python {__file__} <caminho-pasta-plano>")
        sys.exit(1)

    sys.exit(validar_pasta_plano(sys.argv[1]))
