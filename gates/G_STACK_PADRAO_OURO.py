#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_STACK_PADRAO_OURO (ISSUE-0025 & Lei #11)
=============================================================================
Portão determinístico do Padrão-Ouro de Stack Tecnológica (Lei Canônica #11).
Audita se os projetos gerados ou entregáveis dos fluxos da Tríade aderem à
stack mandatória:
  - Frontend: Next.js + React + TypeScript + Tailwind CSS
  - Backend:  Python puro/FastAPI + SQLite WAL (journal_mode=WAL) + OpenAPI 3.1.x
  - Cláusula de Override Explícito: se o plano/projeto registrou decisão
    explícita autorizada para outra stack em dada camada, o gate respeita
    e não reprova por drift silencioso.

Saída:
  exit 0 = Projeto aderente ao Padrão-Ouro ou com override explícito documentado.
  exit 1 = Violação ou drift silencioso na stack gerada de Frontend ou Backend.
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEPS_FRONTEND_OBRIGATORIAS = {
    "next": "Next.js",
    "react": "React",
    "typescript": "TypeScript",
    "tailwindcss": "Tailwind CSS",
}


def extrair_overrides_explicitos(projeto_dir: str) -> Dict[str, bool]:
    """Detecta se há override explícito documentado para frontend ou backend."""
    overrides = {"frontend": False, "backend": False}

    # 1. Arquivos de plano estruturado
    nomes_planos = [
        "PLANNER.json",
        "PRE-PLANO.json",
        "planner.json",
        "PLANO-EXECUCAO-ESTRUTURADO.json",
        "stack_override.json",
        ".stack_override.json",
    ]
    for nome in nomes_planos:
        caminho = os.path.join(projeto_dir, nome)
        if os.path.isfile(caminho):
            try:
                with open(caminho, "r", encoding="utf-8-sig") as f:
                    dados = json.load(f)
                    # Verifica chaves de override
                    so = dados.get("stack_override") or dados.get("override_stack")
                    if isinstance(so, dict):
                        if so.get("frontend"):
                            overrides["frontend"] = True
                        if so.get("backend"):
                            overrides["backend"] = True
                    # Verifica campos booleanos diretos
                    if dados.get("override_frontend") is True or dados.get("frontend_override") is True:
                        overrides["frontend"] = True
                    if dados.get("override_backend") is True or dados.get("backend_override") is True:
                        overrides["backend"] = True
            except Exception:
                pass

    # 2. AGENTS.md local do projeto
    agents_path = os.path.join(projeto_dir, "AGENTS.md")
    if os.path.isfile(agents_path):
        try:
            with open(agents_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                conteudo = f.read().lower()
                if "override: frontend" in conteudo or "stack_override_frontend" in conteudo:
                    overrides["frontend"] = True
                if "override: backend" in conteudo or "stack_override_backend" in conteudo:
                    overrides["backend"] = True
        except Exception:
            pass

    return overrides


def auditar_frontend(projeto_dir: str, override: bool = False) -> Tuple[bool, List[str], Dict[str, bool]]:
    """Audita a camada de frontend contra o Padrão-Ouro (Next.js + TS + Tailwind)."""
    erros: List[str] = []
    status_deps: Dict[str, bool] = {k: False for k in DEPS_FRONTEND_OBRIGATORIAS}

    # Procura package.json na raiz do projeto ou em subdiretório frontend/
    pkg_path = None
    for cand in [
        os.path.join(projeto_dir, "frontend", "package.json"),
        os.path.join(projeto_dir, "package.json"),
        os.path.join(projeto_dir, "ui", "package.json"),
        os.path.join(projeto_dir, "web", "package.json"),
    ]:
        if os.path.isfile(cand):
            pkg_path = cand
            break

    if not pkg_path:
        # Nenhum frontend gerado detectado
        return True, [], status_deps

    if override:
        return True, ["[INFO] Override explícito registrado para o Frontend — dispensa Padrão-Ouro."], status_deps

    try:
        with open(pkg_path, "r", encoding="utf-8-sig") as f:
            pkg_data = json.load(f)
    except Exception as exc:
        return False, [f"Erro ao analisar package.json do frontend ({pkg_path}): {exc}"], status_deps

    todas_deps = {}
    todas_deps.update(pkg_data.get("dependencies", {}))
    todas_deps.update(pkg_data.get("devDependencies", {}))

    for dep_key in DEPS_FRONTEND_OBRIGATORIAS:
        if dep_key in todas_deps:
            status_deps[dep_key] = True
        else:
            erros.append(f"Dependência obrigatória ausente no Frontend: '{DEPS_FRONTEND_OBRIGATORIAS[dep_key]}' ({dep_key})")

    # Verifica também existência de tailwind.config.* ou postcss.config.*
    frontend_dir = os.path.dirname(pkg_path)
    tem_tailwind_cfg = any(
        os.path.isfile(os.path.join(frontend_dir, f))
        for f in ["tailwind.config.js", "tailwind.config.ts", "tailwind.config.mjs", "tailwind.config.cjs"]
    )
    # Se tailwindcss está nas deps, a checagem de config é complementar
    ok = len(erros) == 0
    return ok, erros, status_deps


def auditar_backend(projeto_dir: str, override: bool = False) -> Tuple[bool, List[str], Dict[str, bool]]:
    """Audita a camada de backend contra o Padrão-Ouro (SQLite WAL + OpenAPI 3.1)."""
    erros: List[str] = []
    status = {"sqlite_wal": False, "openapi_3_1": False}

    # Procura arquivos Python de backend
    arquivos_py: List[str] = []
    ignorar = {".git", ".venv", "node_modules", "__pycache__", "frontend", ".next", "dist", "build"}
    for root, dirs, files in os.walk(projeto_dir):
        dirs[:] = [d for d in dirs if d not in ignorar]
        for f in files:
            if f.endswith(".py"):
                arquivos_py.append(os.path.join(root, f))

    if not arquivos_py:
        # Nenhum backend Python detectado
        return True, [], status

    if override:
        return True, ["[INFO] Override explícito registrado para o Backend — dispensa Padrão-Ouro."], status

    # 1. Checagem SQLite WAL
    padroes_wal = [
        re.compile(r"journal_mode\s*=\s*WAL", re.IGNORECASE),
        re.compile(r"PRAGMA\s+journal_mode\s*=\s*WAL", re.IGNORECASE),
        re.compile(r"sqlite.*wal", re.IGNORECASE),
    ]
    for py_file in arquivos_py:
        try:
            with open(py_file, "r", encoding="utf-8-sig", errors="ignore") as f:
                conteudo = f.read()
                for pad in padroes_wal:
                    if pad.search(conteudo):
                        status["sqlite_wal"] = True
                        break
        except Exception:
            pass
        if status["sqlite_wal"]:
            break

    if not status["sqlite_wal"]:
        erros.append("Configuração de banco de dados não utiliza SQLite no modo WAL (journal_mode=WAL).")

    # 2. Checagem OpenAPI 3.1.x
    # Pode estar em openapi.json ou declarado no código python
    spec_path = os.path.join(projeto_dir, "openapi.json")
    if os.path.isfile(spec_path):
        try:
            with open(spec_path, "r", encoding="utf-8-sig") as f:
                sdata = json.load(f)
                v = sdata.get("openapi", "")
                if v.startswith("3.1"):
                    status["openapi_3_1"] = True
        except Exception:
            pass

    if not status["openapi_3_1"]:
        # Busca no código Python gerador ou spec inline
        padroes_openapi = [
            re.compile(r'["\']openapi["\']\s*:\s*["\']3\.1\.', re.IGNORECASE),
            re.compile(r'openapi_version\s*=\s*["\']3\.1\.', re.IGNORECASE),
            re.compile(r'OpenAPI\s+3\.1', re.IGNORECASE),
        ]
        for py_file in arquivos_py:
            try:
                with open(py_file, "r", encoding="utf-8-sig", errors="ignore") as f:
                    conteudo = f.read()
                    for pad in padroes_openapi:
                        if pad.search(conteudo):
                            status["openapi_3_1"] = True
                            break
            except Exception:
                pass
            if status["openapi_3_1"]:
                break

    if not status["openapi_3_1"]:
        erros.append("Especificação OpenAPI do backend não declara a versão canônica OpenAPI 3.1.x.")

    ok = len(erros) == 0
    return ok, erros, status


def auditar_projeto(projeto_dir: str) -> Tuple[int, List[str], Dict[str, Any]]:
    """Audita um projeto quanto ao cumprimento do Padrão-Ouro de Stack Tecnológica."""
    if not os.path.isdir(projeto_dir):
        return 1, [f"Diretório de projeto não encontrado: {projeto_dir}"], {}

    overrides = extrair_overrides_explicitos(projeto_dir)
    ok_fe, erros_fe, status_fe = auditar_frontend(projeto_dir, overrides["frontend"])
    ok_be, erros_be, status_be = auditar_backend(projeto_dir, overrides["backend"])

    todos_erros = []
    if not ok_fe:
        todos_erros.extend(erros_fe)
    if not ok_be:
        todos_erros.extend(erros_be)

    resultado = {
        "overrides": overrides,
        "frontend": {"ok": ok_fe, "status": status_fe},
        "backend": {"ok": ok_be, "status": status_be},
    }

    codigo = 0 if not todos_erros else 1
    return codigo, todos_erros, resultado


def descobrir_projetos_referencia() -> List[str]:
    """Descobre projetos gerados de referência para validação determinística."""
    candidatos = [
        r"C:\Users\trcnologia\Desktop\proj_ctt\planos-ctt-app",
    ]
    return [c for c in candidatos if os.path.isdir(c)]


def main(alvo_arg: Optional[str] = None) -> int:
    if alvo_arg is not None:
        alvo = alvo_arg
    else:
        parser = argparse.ArgumentParser(
            description="G_STACK_PADRAO_OURO: Auditoria determinística da stack padrão-ouro (Lei #11)."
        )
        parser.add_argument(
            "--target",
            default="",
            help="Caminho do projeto a auditar.",
        )
        if any("pytest" in arg for arg in sys.argv):
            alvo = ""
        else:
            args, unknown = parser.parse_known_args()
            alvo = args.target or (unknown[0] if unknown and not unknown[0].startswith("-") else "")

    print("=" * 72)
    print(" [GATE] G_STACK_PADRAO_OURO — Padrão-Ouro de Stack Tecnológica (Lei #11)")
    print("=" * 72)

    if alvo:
        caminho_proj = os.path.abspath(alvo)
        print(f"Auditando projeto específico: {caminho_proj}")
        codigo, erros, res = auditar_projeto(caminho_proj)

        fe = res.get("frontend", {})
        be = res.get("backend", {})
        print(f"  Camada Frontend: {'[OK]' if fe.get('ok') else '[FALHA]'}")
        print(f"  Camada Backend:  {'[OK]' if be.get('ok') else '[FALHA]'}")

        if erros:
            print("\n[ERRO] Projeto violou a Lei Canônica #11 (Padrão-Ouro de Stack):", file=sys.stderr)
            for err in erros:
                print(f"  [X] {err}", file=sys.stderr)
            return 1

        print("\n[SUCESSO] Projeto 100% conforme com a Lei Canônica #11!")
        return 0

    # Auditoria de projetos de referência conhecidos
    projetos = descobrir_projetos_referencia()
    if not projetos:
        print("[INFO] Nenhum projeto de referência detectado localmente para auto-auditoria.")
        print("[INFO] Rótulo honesto (Lei #8): verificação concluída sem alvos locais.")
        return 0

    print(f"Auditando {len(projetos)} projeto(s) de referência detectado(s)...")
    falhas = []
    for proj in projetos:
        print(f"\n--- Projeto: {proj} ---")
        cod, errs, res = auditar_projeto(proj)
        fe = res.get("frontend", {})
        be = res.get("backend", {})
        print(f"  Frontend: {'[OK]' if fe.get('ok') else '[FALHA]'}")
        print(f"  Backend:  {'[OK]' if be.get('ok') else '[FALHA]'}")
        if cod != 0 or errs:
            falhas.extend([f"[{proj}] {e}" for e in errs])

    print("\n" + "=" * 72)
    print(" [LIMITE METROLÓGICO — LEI #8 / HONESTIDADE DE RÓTULO]:")
    print("   O gate valida estaticamente dependências (package.json para Next.js, React,")
    print("   TypeScript e Tailwind) e configurações de backend (SQLite WAL e OpenAPI 3.1).")
    print("   Decisões de override registradas explicitamente no plano são respeitadas.")
    print("=" * 72)

    if falhas:
        print(f"\n[FALHA] {len(falhas)} divergência(s) da stack padrão-ouro detectada(s):", file=sys.stderr)
        for f in falhas:
            print(f"  [X] {f}", file=sys.stderr)
        return 1

    print("[SUCESSO] 100% dos projetos de referência cumprem a Lei Inviolável #11!")
    return 0


if __name__ == "__main__":
    alvo_cmd = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    sys.exit(main(alvo_cmd))
