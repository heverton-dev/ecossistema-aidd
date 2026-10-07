#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atualiza o .secrets.baseline (comando explícito, separado do gate G_SEGREDOS).

O gate G_SEGREDOS só LÊ o baseline (ciclo-03 VSA, Ticket 9). Quando um achado
novo for revisado como falso positivo, ou quando os números de linha mudarem,
quem atualiza o arquivo é este comando:

  python scripts/atualizar_baseline_segredos.py [--raiz <repo>]
  python -m detect_secrets audit .secrets.baseline   (marca real/falso positivo)

Varre os arquivos rastreados pelo git (menos o próprio baseline, sem passá-los na linha de comando), mantém as
marcações de auditoria já feitas (detect-secrets scan --baseline) e grava o
filtro is_baseline_file com caminho relativo. Rodar duas vezes seguidas não
muda nada. Saída: exit 0 = baseline atualizado; exit 1 = erro.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_BASELINE = ".secrets.baseline"
FILTRO_BASELINE = "detect_secrets.filters.common.is_baseline_file"


def _rastreados(raiz: Path) -> list[str]:
    proc = subprocess.run(["git", "ls-files"], cwd=str(raiz), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git ls-files falhou")
    return [p for p in proc.stdout.splitlines()
            if p and p != ARQUIVO_BASELINE and (raiz / p).is_file()]


def _sanitizar(caminho: Path) -> None:
    """Filtro is_baseline_file sempre com caminho relativo (sem vazar caminho absoluto)."""
    texto = caminho.read_text(encoding="utf-8")
    dados = json.loads(texto)
    alterado = False
    for filtro in dados.get("filters_used", []):
        if filtro.get("path") == FILTRO_BASELINE and filtro.get("filename") != ARQUIVO_BASELINE:
            filtro["filename"] = ARQUIVO_BASELINE
            alterado = True
    if alterado:
        novo = json.dumps(dados, indent=2) + "\n"
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo.replace("\n", "\r\n") if "\r\n" in texto else novo)


def _sem_mudanca_real(antes: bytes, depois: bytes) -> bool:
    """True se só o carimbo generated_at mudou."""
    try:
        a, d = json.loads(antes), json.loads(depois)
    except ValueError:
        return False
    a.pop("generated_at", None)
    d.pop("generated_at", None)
    return a == d


def atualizar(raiz: Path) -> int:
    baseline = raiz / ARQUIVO_BASELINE
    if not baseline.is_file():
        print(f"[ERRO] {ARQUIVO_BASELINE} não existe em {raiz}.")
        return 1
    try:
        arquivos = _rastreados(raiz)
    except (OSError, RuntimeError) as erro:
        print(f"[ERRO] {erro}")
        return 1
    antes = baseline.read_bytes()
    # Sem a lista na linha de comando: com milhares de caminhos ela estoura o limite do
    # Windows (WinError 206). Sem caminho, o detect-secrets varre os mesmos arquivos
    # rastreados pelo git, e o filtro is_baseline_file tira o proprio baseline.
    proc = subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan", "--baseline", ARQUIVO_BASELINE],
        cwd=str(raiz), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        print(f"[ERRO] detect-secrets scan falhou: {proc.stderr.strip()}")
        return 1
    _sanitizar(baseline)
    if _sem_mudanca_real(antes, baseline.read_bytes()):
        baseline.write_bytes(antes)  # só o carimbo generated_at mudou: idempotente
        print(f"[OK] {ARQUIVO_BASELINE} já estava em dia; nada mudou.")
        return 0
    print(f"[OK] {ARQUIVO_BASELINE} atualizado ({len(arquivos)} arquivo(s) varrido(s)). "
          "Revise com `python -m detect_secrets audit .secrets.baseline` e comite.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Atualiza o .secrets.baseline (fora do gate G_SEGREDOS).")
    parser.add_argument("--raiz", default=str(RAIZ), help="raiz do repositório (padrão: ecossistema)")
    args = parser.parse_args(argv)
    return atualizar(Path(args.raiz))


if __name__ == "__main__":
    sys.exit(main())
