# -*- coding: utf-8 -*-
"""
Validador e Dispatcher de Micro-Gates no Pre-Commit baseado em Git Diff (Ticket 3 VSA).

Mapeia alterações em fatias e executa seletivamente os gates e testes direcionados:
- modulos/01-governanca-e-qualidade/ -> Gates e testes de governança
- modulos/02-triade-motores/         -> Gates e testes de motores
- modulos/03-plataforma-e-entrega/   -> Gates e testes de plataforma
- gates/                            -> Meta-gates e integridade
- ecossistema.py / scripts/         -> Core CLI e boot tests
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Garantir import seguro mesmo se chamado de dentro de scripts/
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.exit_codes import ExitCode

FATIAS_MAPA: Dict[str, Dict[str, List[str]]] = {
    "01-governanca": {
        "prefixo": ["modulos/01-governanca-e-qualidade", "tools/aidd-forge"],
        "testes": ["pytest modulos/01-governanca-e-qualidade/ -q --maxfail=1"],
    },
    "02-motores": {
        "prefixo": ["modulos/02-triade-motores", "tools/aidd-pure", "tools/aidd-open", "tools/aidd-freedom"],
        "testes": ["pytest modulos/02-triade-motores/ -q --maxfail=1"],
    },
    "03-plataforma": {
        "prefixo": ["modulos/03-plataforma-e-entrega", "tools/aidd-master", "tools/aidd-enterprise", "tools/aidd-ops"],
        "testes": ["pytest modulos/03-plataforma-e-entrega/ -q --maxfail=1"],
    },
    "core-cli": {
        "prefixo": ["ecossistema.py", "scripts/", "componentes/compartilhado/src-core/"],
        "testes": ["pytest tests/test_ecossistema_lazy_boot.py scripts/test_exit_codes.py tests/test_subgrafos_federados.py -q"],
    },
}


def obter_arquivos_modificados(root_dir: Path) -> List[str]:
    """Obtém lista de arquivos em staging (git diff --cached --name-only)."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        arquivos = [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]
        if not arquivos:
            # Fallback para diff do commit ou arquivos staged se invocado diretamente
            res_diff = subprocess.run(
                ["git", "diff", "HEAD~1", "--name-only"],
                cwd=str(root_dir),
                capture_output=True,
                text=True,
            )
            arquivos = [line.strip().replace("\\", "/") for line in res_diff.stdout.splitlines() if line.strip()]
        return arquivos
    except Exception:
        return []


def mapear_fatias_afetadas(arquivos: List[str]) -> Set[str]:
    """Identifica quais fatias sofreram alterações estruturais."""
    fatias_afetadas: Set[str] = set()
    for arq in arquivos:
        for fatia, config in FATIAS_MAPA.items():
            for prefixo in config["prefixo"]:
                if arq.startswith(prefixo):
                    fatias_afetadas.add(fatia)
                    break
    return fatias_afetadas


def executar_micro_gates_diff(root_dir: Path, verbose: bool = True) -> int:
    """Dispara os micro-gates correspondentes às fatias modificadas."""
    arquivos = obter_arquivos_modificados(root_dir)
    if not arquivos:
        if verbose:
            print("[MICRO-GATES-DIFF] Nenhum arquivo alterado detectado no diff.")
        return ExitCode.SUCCESS.value

    fatias = mapear_fatias_afetadas(arquivos)
    if not fatias:
        if verbose:
            print(f"[MICRO-GATES-DIFF] {len(arquivos)} arquivo(s) modificado(s) fora das fatias mapeadas.")
        return ExitCode.SUCCESS.value

    if verbose:
        print(f"[MICRO-GATES-DIFF] Fatias afetadas: {', '.join(sorted(fatias))}")

    for fatia in sorted(fatias):
        comandos = FATIAS_MAPA[fatia]["testes"]
        for cmd in comandos:
            if verbose:
                print(f"[MICRO-GATES-DIFF] Executando gate seletivo da fatia '{fatia}': {cmd}")
            proc = subprocess.run(
                cmd,
                cwd=str(root_dir),
                shell=True,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                print(f"[MICRO-GATES-DIFF] [FALHA] Fatia '{fatia}' falhou na verificação:")
                print(proc.stderr or proc.stdout)
                return ExitCode.RULE_VIOLATION.value

    if verbose:
        print("[MICRO-GATES-DIFF] [SUCESSO] Todos os micro-gates das fatias modificadas passaram.")
    return ExitCode.SUCCESS.value


if __name__ == "__main__":
    caminho_raiz = Path(__file__).resolve().parent.parent
    sys.exit(executar_micro_gates_diff(caminho_raiz))
