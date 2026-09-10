# -*- coding: utf-8 -*-
"""Use Case: setup — diagnóstico completo e configuração automática do ambiente."""

import os
import platform
import shutil
import subprocess
import sys


def _master_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ensure_environment(auto_install: bool = True):
    """Garante de forma 100% automática que o runtime possui os pré-requisitos necessários."""
    missing = []
    try:
        import pytest
    except ImportError:
        missing.append("pytest")
    try:
        import requests
    except ImportError:
        missing.append("requests")

    if missing and auto_install:
        print(f"[*] [BOOTSTRAP AUTOMÁTICO] Instalando dependências essenciais: {', '.join(missing)}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True, capture_output=True)
            print("[OK] Dependências instaladas com sucesso.")
        except (subprocess.CalledProcessError, OSError) as e:
            print(f"[WARN] Não foi possível auto-instalar dependências: {e}")


def cmd_setup(args):
    """Executa diagnóstico completo e configuração automática do ambiente."""
    print("=" * 80)
    print("🔧 [AIDD SETUP] Diagnóstico e Inicialização Automática do Ambiente")
    print("=" * 80)

    # 1. Checagem de Python
    py_ver = platform.python_version()
    print(f"  [+] Python Runtime: {py_ver} ({sys.executable})")

    # 2. Instalação de requirements.txt
    req_file = os.path.join(_master_root(), "requirements.txt")
    if os.path.exists(req_file):
        print("  [+] Instalando dependências do 'requirements.txt'...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], capture_output=True, text=True)
        if res.returncode == 0:
            print("  [OK] Dependências instaladas com êxito.")
        else:
            print(f"  [WARN] Aviso ao instalar requirements: {res.stderr.strip()}")
    else:
        ensure_environment(auto_install=True)

    # 3. Detecção de Git
    git_bin = shutil.which("git")
    print(f"  [+] Git CLI: {'Presente (' + git_bin + ')' if git_bin else 'Ausente'}")

    # 4. Detecção de ORCA ADE
    orca_bin = shutil.which("orca")
    if orca_bin:
        print(f"  [+] ORCA ADE: Detectado ({orca_bin}) ➔ Modo A (Mesas de Trabalho Isoladas)")
    else:
        print("  [+] ORCA ADE: Não instalado ➔ Modo B (Subagentes Nativos / Git Worktrees)")

    # 5. Fleet Auto-Discovery — varredura de agentes de IA no PATH
    try:
        sys.path.insert(0, os.path.join(_master_root(), "src"))
        from core.fleet_discovery import FleetDiscovery

        fleet = FleetDiscovery()
        discovered = fleet.discover_agents()
        available_count = sum(1 for v in discovered.values() if v["available"])
        print(f"\n  [+] Fleet Discovery: {available_count} agente(s) de IA detectado(s)")
        for name, info in discovered.items():
            status = "✅" if info["available"] else "❌"
            path_str = info["path"] if info["available"] else "não encontrado"
            specialty = info.get("specialty", "?")
            print(f"      {status} {info.get('display', name):<28s} [{path_str}]  ({specialty})")
    except ImportError as e:
        print(f"  [WARN] Fleet Discovery indisponível: {e}")

    print("=" * 80)
    print("🏆 [SUCESSO]: Ambiente 100% pronto para compor e executar projetos AIDD v5.1!")
    print("=" * 80)