# -*- coding: utf-8 -*-
"""
Validador e Dispatcher de Micro-Gates no Pre-Commit baseado em Git Diff (Ticket 3 VSA).

Mapeia alterações em fatias e executa seletivamente os gates e testes direcionados:
- modulos/01-governanca-e-qualidade/ -> suítes do forge e do planner
- modulos/02-triade-motores/         -> suítes do pure, open e freedom
- modulos/03-plataforma-e-entrega/   -> suítes do enterprise, master e ops
- ecossistema.py / scripts/         -> Core CLI e boot tests

Cada suíte roda de dentro da pasta da ferramenta (ciclo-03 VSA, Ticket 16): o
pytest da fatia inteira a partir da raiz quebrava na coleta (módulos de mesmo nome
em pastas diferentes) e barrava todo commit em modulos/.
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
from scripts.worktree_hermetico import obter_env_sanitizado

FATIAS_MAPA: Dict[str, Dict[str, List[str]]] = {
    "01-governanca": {
        "prefixo": ["modulos/01-governanca-e-qualidade"],
        "suites": [
            "modulos/01-governanca-e-qualidade/core/aidd-forge",
            "modulos/01-governanca-e-qualidade/core/aidd-planner",
        ],
    },
    "02-motores": {
        "prefixo": ["modulos/02-triade-motores"],
        "suites": [
            "modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure",
            "modulos/02-triade-motores/fluxo-02-open/core/aidd-open",
            "modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom",
        ],
    },
    "03-plataforma": {
        "prefixo": ["modulos/03-plataforma-e-entrega"],
        "suites": [
            "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise",
            "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master",
            "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops",
        ],
    },
    "core-cli": {
        "prefixo": ["ecossistema.py", "scripts/", "componentes/compartilhado/src-core/"],
        "testes": ["pytest tests/test_ecossistema_lazy_boot.py scripts/test_exit_codes.py tests/test_subgrafos_federados.py tests/test_lazy_skills_scope.py -q"],
    },
}


def comando_suite() -> List[str]:
    """pytest de uma suíte, rodado com cwd na pasta da ferramenta."""
    return [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--maxfail=1"]


def _rodar(cmd, cwd: Path, shell: bool) -> subprocess.CompletedProcess:
    """Sem o GIT_DIR/GIT_INDEX_FILE do hook: os testes de git em tmp_path das suítes
    gravavam no repositório real (06/10: core.bare=true e [user] forge-test no .git/config)."""
    return subprocess.run(cmd, cwd=str(cwd), shell=shell, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=obter_env_sanitizado())


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
        execucoes = [(" ".join(comando_suite()[1:]) + f"  (em {suite})", comando_suite(), root_dir / suite, False)
                     for suite in FATIAS_MAPA[fatia].get("suites", [])]
        execucoes += [(cmd, cmd, root_dir, True) for cmd in FATIAS_MAPA[fatia].get("testes", [])]
        for rotulo, cmd, cwd, shell in execucoes:
            if verbose:
                print(f"[MICRO-GATES-DIFF] Executando gate seletivo da fatia '{fatia}': {rotulo}")
            proc = _rodar(cmd, cwd, shell)
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
