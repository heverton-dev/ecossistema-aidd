# -*- coding: utf-8 -*-
"""
Preflight Host - diagnostico instantaneo (< 2s) de binarios do sistema.

Detecta presenca, caminho e versao de: Git, Node, Docker, Hadolint, Checkov.
Reutiliza detectores de G_HADOLINT e G_INFRA_COMPOSE como fonte unica de verdade.
Sem dependencia de rede.

Uso standalone:
    python scripts/preflight_host.py [--json] [--fix]

Uso via ecossistema.py:
    python ecossistema.py preflight-host [--json] [--fix]
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def _run(cmd: List[str], timeout: float = 5.0) -> Tuple[int, str]:
    """Executa comando e retorna (exit_code, stdout.strip()). Nunca levanta excecao."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def _versao_de_output(stdout: str) -> Optional[str]:
    """Extrai a primeira string que parece versao (X.Y.Z ou vX.Y.Z) de um stdout."""
    import re
    m = re.search(r"v?(\d+\.\d+[\.\d]*[^\s]*)", stdout)
    return m.group(1) if m else stdout.splitlines()[0] if stdout.strip() else None


# ---------------------------------------------------------------------------
# Detectores por binario
# ---------------------------------------------------------------------------

def _detectar_git() -> Dict:
    caminho = shutil.which("git")
    if not caminho:
        return {"binario": "git", "presente": False, "caminho": None, "versao": None, "instalar": "https://git-scm.com/downloads"}
    _, out = _run(["git", "--version"])
    return {"binario": "git", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


def _detectar_node() -> Dict:
    caminho = shutil.which("node")
    if not caminho:
        return {"binario": "node", "presente": False, "caminho": None, "versao": None, "instalar": "https://nodejs.org/"}
    _, out = _run(["node", "--version"])
    return {"binario": "node", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


def _detectar_docker() -> Dict:
    caminho = shutil.which("docker")
    if not caminho:
        return {"binario": "docker", "presente": False, "caminho": None, "versao": None, "instalar": "https://docs.docker.com/get-docker/"}
    code, out = _run(["docker", "--version"])
    versao = _versao_de_output(out) if code == 0 else None
    return {"binario": "docker", "presente": True, "caminho": caminho, "versao": versao, "instalar": None}


def _detectar_hadolint() -> Dict:
    """Reutiliza G_HADOLINT.encontrar_binario_hadolint como fonte unica de verdade."""
    sys.path.insert(0, os.path.join(ROOT_DIR, "gates"))
    try:
        from G_HADOLINT import encontrar_binario_hadolint
        caminho = encontrar_binario_hadolint()
    except Exception:
        caminho = shutil.which("hadolint")
    if not caminho:
        return {"binario": "hadolint", "presente": False, "caminho": None, "versao": None,
                "instalar": "winget install hadolint.hadolint / brew install hadolint"}
    _, out = _run([caminho, "--version"])
    return {"binario": "hadolint", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


def _detectar_checkov() -> Dict:
    """Reutiliza G_INFRA_COMPOSE.verificar_checkov_disponivel como fonte unica de verdade."""
    sys.path.insert(0, os.path.join(ROOT_DIR, "gates"))
    try:
        from G_INFRA_COMPOSE import verificar_checkov_disponivel
        presente = verificar_checkov_disponivel()
    except Exception:
        presente = shutil.which("checkov") is not None
    if not presente:
        return {"binario": "checkov", "presente": False, "caminho": None, "versao": None,
                "instalar": "pip install checkov"}
    caminho = shutil.which("checkov") or shutil.which("checkov.cmd") or "checkov"
    _, out = _run([caminho, "--version"])
    return {"binario": "checkov", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


# ---------------------------------------------------------------------------
# Orquestracao principal
# ---------------------------------------------------------------------------

_DETECTORES = [
    _detectar_git,
    _detectar_node,
    _detectar_docker,
    _detectar_hadolint,
    _detectar_checkov,
]


def executar_preflight() -> Dict:
    """Executa todos os detectores e retorna resultado consolidado."""
    resultados = []
    for detector in _DETECTORES:
        resultados.append(detector())
    ausentes = [r["binario"] for r in resultados if not r["presente"]]
    return {
        "sucesso": len(ausentes) == 0,
        "total": len(resultados),
        "presentes": sum(1 for r in resultados if r["presente"]),
        "ausentes": ausentes,
        "detalhes": resultados,
        "sistema": {
            "os": platform.system(),
            "arquitetura": platform.machine(),
            "python": platform.python_version(),
        },
    }


def _formatar_tabela(resultado: Dict) -> str:
    """Formata resultado como tabela legivel para terminal."""
    linhas = []
    linhas.append("=" * 72)
    linhas.append(" PREFLIGHT HOST — Diagnostico de Binarios do Sistema")
    linhas.append("=" * 72)
    linhas.append(f" OS: {resultado['sistema']['os']} | Arch: {resultado['sistema']['arquitetura']} | Python: {resultado['sistema']['python']}")
    linhas.append("-" * 72)
    linhas.append(f" {'Binario':<12} {'Status':<10} {'Versao':<22} {'Caminho'}")
    linhas.append("-" * 72)
    for d in resultado["detalhes"]:
        status = "[OK]" if d["presente"] else "[FALTA]"
        versao = d["versao"] or "-"
        caminho = d["caminho"] or "-"
        linhas.append(f" {d['binario']:<12} {status:<10} {versao:<22} {caminho}")
    linhas.append("-" * 72)
    if resultado["sucesso"]:
        linhas.append(f" RESULTADO: {resultado['presentes']}/{resultado['total']} binarios detectados — OK")
    else:
        linhas.append(f" RESULTADO: {resultado['presentes']}/{resultado['total']} binarios — AUSENTES: {', '.join(resultado['ausentes'])}")
        linhas.append("")
        for d in resultado["detalhes"]:
            if not d["presente"] and d.get("instalar"):
                linhas.append(f"   Instalar {d['binario']}: {d['instalar']}")
    linhas.append("=" * 72)
    return "\n".join(linhas)


def _sugerir_fixes(resultado: Dict) -> int:
    """Imprime instrucoes de correcao. Retorna 1 se ha ausentes, 0 se tudo OK."""
    if resultado["sucesso"]:
        print("Todos os binarios detectados. Nenhuma correcao necessaria.")
        return 0
    print("\nCorrecoes recomendadas:")
    for d in resultado["detalhes"]:
        if not d["presente"] and d.get("instalar"):
            print(f"  - {d['binario']}: {d['instalar']}")
    return 1


# ---------------------------------------------------------------------------
# CLI standalone
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Preflight Host — diagnostico de binarios do sistema")
    parser.add_argument("--json", action="store_true", help="Saida em formato JSON")
    parser.add_argument("--fix", action="store_true", help="Exibe instrucoes de correcao")
    args = parser.parse_args()

    resultado = executar_preflight()

    if args.json:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        print(_formatar_tabela(resultado))

    if args.fix:
        sys.exit(_sugerir_fixes(resultado))

    sys.exit(0 if resultado["sucesso"] else 1)


if __name__ == "__main__":
    main()
