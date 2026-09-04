# -*- coding: utf-8 -*-
"""
Gera o bloco 'testes' de PLANO-EXECUCAO-ESTRUTURADO.json rodando pytest de
verdade em cada uma das 4 ferramentas (R8 do
PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md).

Por quê: o JSON afirmava "191 testes verdes" como se fosse o total do
ecossistema inteiro — na realidade era só a contagem isolada de aidd-forge,
nunca atualizada desde a criação do arquivo (write-once, não um estado
vivo). Este script substitui o número digitado à mão por uma medição real,
reproduzível a qualquer momento via `python ecossistema.py status --testes`.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLANO_PATH = os.path.join(ROOT_DIR, "PLANO-EXECUCAO-ESTRUTURADO.json")

FERRAMENTAS = ["aidd-forge", "aidd-generator", "aidd-master", "aidd-master-enterprise"]

_PADRAO_RESUMO = re.compile(
    r"(?:(?P<passed>\d+) passed)?"
    r"(?:, (?P<failed>\d+) failed)?"
    r"(?:, (?P<skipped>\d+) skipped)?"
    r"(?:, (?P<errors>\d+) error)?"
)


def _rodar_pytest(ferramenta: str) -> dict:
    caminho = os.path.join(ROOT_DIR, "tools", ferramenta)
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no"],
            cwd=caminho, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}

    saida = resultado.stdout + resultado.stderr
    linhas_resumo = [l for l in saida.splitlines() if " in " in l and ("passed" in l or "failed" in l or "error" in l)]
    if not linhas_resumo:
        return {"status": "indeterminado", "exit_code": resultado.returncode, "trecho": saida[-300:]}

    m = _PADRAO_RESUMO.search(linhas_resumo[-1])
    return {
        "status": "ok" if resultado.returncode == 0 else "falhou",
        "passed": int(m.group("passed") or 0) if m else 0,
        "failed": int(m.group("failed") or 0) if m else 0,
        "skipped": int(m.group("skipped") or 0) if m else 0,
        "errors": int(m.group("errors") or 0) if m else 0,
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

    with open(PLANO_PATH, "r", encoding="utf-8") as f:
        plano = json.load(f)

    plano["testes"] = {
        "medido_em": datetime.now(timezone.utc).isoformat(),
        "metodo": "python -m pytest -q --tb=no em cada tools/<ferramenta>, "
                  "parseado do resumo real (nao digitado a mao)",
        "por_ferramenta": testes,
    }

    with open(PLANO_PATH, "w", encoding="utf-8") as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nOK {PLANO_PATH} atualizado com contagem real de testes.")
    return testes


if __name__ == "__main__":
    gerar()
