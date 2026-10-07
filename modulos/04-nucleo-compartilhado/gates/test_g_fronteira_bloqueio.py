# -*- coding: utf-8 -*-
"""
Testes do Quality Gate G_FRONTEIRA_FERRAMENTAS em modo bloqueio e validação de contratos (Ticket 20 - D13 / DoD 9).

Lei #13 (o portão precisa provar que morde):
1. Repositório temporário com violação de fronteira plantada: sem variável de ambiente
   (modo padrão), o gate agora roda em bloqueio e sai com exit 1.
2. Orquestrador sincrono (run-fluxo): se a etapa produzir contrato de handoff sem
   evidência ou inválido perante validar_handoff, o orquestrador aborta imediatamente
   com falha crítica (run-fluxo / etapa sai False / exit 1).
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
GATE_SCRIPT = RAIZ / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_FRONTEIRA_FERRAMENTAS.py"
MAPA_REAL = RAIZ / "componentes" / "compartilhado" / "specs" / "MAPA-DONOS-FERRAMENTAS.json"
DOCKERFILE_VIOLACAO = "modulos/02-triade-motores/fluxo-02-open/core/aidd-open/Dockerfile"


def _subprocesso(args, cwd, env_vars=None):
    env = os.environ.copy()
    env.pop("AIDD_FRONTEIRA_MODO", None)
    if env_vars:
        env.update(env_vars)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _git(cwd, *args):
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, f"git {' '.join(args)} falhou: {r.stderr}"
    return r


def montar_repo_violacao(tmp_path):
    mapa_dir = tmp_path / "componentes" / "compartilhado" / "specs"
    mapa_dir.mkdir(parents=True)
    shutil.copy(MAPA_REAL, mapa_dir / "MAPA-DONOS-FERRAMENTAS.json")

    catalogo = {
        "versao": 1,
        "gerado_por": "test_g_fronteira_bloqueio",
        "ferramentas": [
            {
                "id": "aidd-open",
                "entrada_cli": "modulos/02-triade-motores/fluxo-02-open/core/aidd-open/scripts/pipeline_factory.py",
                "gates_proprios": [],
            }
        ],
    }
    docs_dir = tmp_path / "docs" / "auditoria" / "mapa-pecas"
    docs_dir.mkdir(parents=True)
    (docs_dir / "catalogo-pecas.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    docker = tmp_path / DOCKERFILE_VIOLACAO
    docker.parent.mkdir(parents=True, exist_ok=True)
    docker.write_text("FROM alpine:3.20\n", encoding="utf-8")

    gates_dir = tmp_path / "modulos" / "04-nucleo-compartilhado" / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    contratos = tmp_path / "modulos" / "04-nucleo-compartilhado" / "contracts"
    contratos.mkdir(parents=True, exist_ok=True)
    (contratos / "allowlist_fronteira.json").write_text(
        json.dumps({"violacoes": []}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    shutil.copy(GATE_SCRIPT, gates_dir / "G_FRONTEIRA_FERRAMENTAS.py")

    _git(tmp_path, "init")
    _git(tmp_path, "add", "-A")
    return gates_dir / "G_FRONTEIRA_FERRAMENTAS.py"


def test_padrao_sem_env_e_bloqueio_e_reprova_com_exit_1(tmp_path):
    """Com AIDD_FRONTEIRA_MODO ausente (padrão do sistema), o gate deve rodar em bloqueio e sair com exit 1."""
    gate = montar_repo_violacao(tmp_path)
    res = _subprocesso([str(gate)], tmp_path, env_vars=None)
    assert res.returncode == 1, res.stdout + res.stderr
    assert "modo=bloqueio" in res.stdout
    assert "modo bloqueio —" in res.stdout


def test_handoff_sem_evidencia_derruba_run_fluxo(tmp_path, capsys):
    """Handoff gravado sem evidências válidas (validar_handoff=False) aborta o fluxo sincrono."""
    from scripts import orquestrador_sincrono

    orq = orquestrador_sincrono.OrquestradorSincrono(
        fluxo=1,
        nome="Teste Falha Handoff",
        slug="teste-falha-handoff",
        dominio="saude",
        pasta=str(tmp_path / "projeto"),
        dry_run=False,
    )

    handoff_invalido = {
        "versao_schema": "1.0.0",
        "projeto_dir": str(orq.pasta),
        "git": {"inicializado": False, "commit_inicial": ""},  # sem git válido nem commit
        "dependencias": [],  # sem dependências comprovadas
        "leis_e_guardas": [],
        "harnesses": ["claude"],
        "almoxarifado": {"catalogo_sha256": "", "pecas_disponiveis": []},
        "capacidade_llm": "nenhuma",
        "estrutura_projeto": {"pastas_criadas": []},
    }

    def forge_fake(cmd, cwd=None, env_extra=None):
        c1_caminho = orq.pasta / ".aidd" / "HANDOFF_FORGE_PLANNER.json"
        c1_caminho.parent.mkdir(parents=True, exist_ok=True)
        c1_caminho.write_text(json.dumps(handoff_invalido), encoding="utf-8")
        return 0

    orq._executar_comando = forge_fake
    sucesso = orq.etapa_01_forge()
    assert sucesso is False, "Etapa 1 deveria ter sido reprovada por falta de evidência no handoff"
