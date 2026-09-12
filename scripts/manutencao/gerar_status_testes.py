# -*- coding: utf-8 -*-
"""
Gera o bloco 'testes' de PLANO-EXECUCAO-ESTRUTURADO.json rodando pytest de
verdade em cada uma das 5 ferramentas (R8 do
PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md).

Por quê: o JSON afirmava "191 testes verdes" como se fosse o total do
ecossistema inteiro — na realidade era só a contagem isolada de aidd-forge,
nunca atualizada desde a criação do arquivo (write-once, não um estado
vivo). Este script substitui o número digitado à mão por uma medição real,
reproduzível a qualquer momento via `python ecossistema.py status --testes`.

Destinos ao escrever (--write):
  1. docs/testes/status_testes_ferramentas.json — registro auxiliar.
  2. PLANO-EXECUCAO-ESTRUTURADO.json (raiz) — bloco 'testes' sobrescrito
     in-place, preservando todos os outros campos do JSON.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLANO_PATH = os.path.join(ROOT_DIR, "docs", "testes", "status_testes_ferramentas.json")
PLANO_ESTRUTURADO_PATH = os.path.join(ROOT_DIR, "PLANO-EXECUCAO-ESTRUTURADO.json")

FERRAMENTAS = ["aidd-forge", "aidd-generator", "aidd-master", "aidd-enterprise", "aidd-ops"]

_PADRAO_PASSED = re.compile(r"(\d+) passed")
_PADRAO_FAILED = re.compile(r"(\d+) failed")
_PADRAO_SKIPPED = re.compile(r"(\d+) skipped")
_PADRAO_ERRORS = re.compile(r"(\d+) error")


def _rodar_pytest(ferramenta: str) -> dict:
    caminho = os.path.join(ROOT_DIR, "tools", ferramenta)
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no"],
            cwd=caminho, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=900,
        )
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}

    saida = resultado.stdout + resultado.stderr
    # Pytest summary lines contain "in <time>s" and may have ==== padding.
    linhas_resumo = [l for l in saida.splitlines() if re.search(r"\bin\s+[\d.]+s", l)]
    if not linhas_resumo:
        return {"status": "indeterminado", "exit_code": resultado.returncode, "trecho": saida[-300:]}

    linha = linhas_resumo[-1]
    _extrair = lambda padrao: int(padrao.search(linha).group(1)) if padrao.search(linha) else 0
    return {
        "status": "ok" if resultado.returncode == 0 else "falhou",
        "passed": _extrair(_PADRAO_PASSED),
        "failed": _extrair(_PADRAO_FAILED),
        "skipped": _extrair(_PADRAO_SKIPPED),
        "errors": _extrair(_PADRAO_ERRORS),
        "exit_code": resultado.returncode,
    }


def gerar(escrever: bool = True) -> dict:
    testes = {}
    for ferramenta in FERRAMENTAS:
        print(f"Rodando pytest em tools/{ferramenta} ...")
        testes[ferramenta] = _rodar_pytest(ferramenta)
        print(f"  -> {testes[ferramenta]}")

    if not escrever:
        return testes

    dados = {
        "medido_em": datetime.now(timezone.utc).isoformat(),
        "metodo": "python -m pytest -q --tb=no em cada tools/<ferramenta>, "
                  "parseado do resumo real (nao digitado a mao)",
        "por_ferramenta": testes,
    }

    with open(PLANO_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nOK {PLANO_PATH} atualizado com contagem real de testes.")

    # --- patch in-place no PLANO-EXECUCAO-ESTRUTURADO.json (raiz) ---
    _patchar_plano_estruturado(dados)

    return testes


def _patchar_plano_estruturado(dados_testes: dict) -> None:
    """Sobrescreve o bloco 'testes' do PLANO-EXECUCAO-ESTRUTURADO.json,
    preservando todos os demais campos (nome, versao, fases, ferramentas)."""
    if not os.path.isfile(PLANO_ESTRUTURADO_PATH):
        print(f"  [AVISO] {PLANO_ESTRUTURADO_PATH} nao encontrado — patch ignorado.")
        return

    with open(PLANO_ESTRUTURADO_PATH, "r", encoding="utf-8") as f:
        plano = json.load(f)

    plano["testes"] = dados_testes

    with open(PLANO_ESTRUTURADO_PATH, "w", encoding="utf-8") as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"OK {PLANO_ESTRUTURADO_PATH}['testes'] sobrescrito com contagem real.")


if __name__ == "__main__":
    gerar()
