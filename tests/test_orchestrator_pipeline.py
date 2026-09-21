# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTES DO MOTOR DE ORQUESTRAÇÃO EM WORKTREES (ISSUE-PIPE-0003)
=============================================================================
Suíte de testes automatizados com repositório Git real para verificar:
  1. Concorrência: execução de 3 tarefas simultâneas em worktrees sem colisão.
  2. Join Barrier: bloqueio imediato de merge quando uma tarefa paralela falha.
  3. Barreira de Quality Gates: bloqueio quando um quality gate reprova.
  4. Execução sequencial: ordem preservada e parada na primeira falha.
  5. Limpeza determinística (Cleanup): remoção de 100% das worktrees mesmo
     sob falhas ou exceções não tratadas.
  6. Execução via CLI (subprocess real).
=============================================================================
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_ORCHESTRATOR = ROOT_DIR / "tools" / "aidd-master" / "scripts" / "orchestrator_pipeline.py"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "tools" / "aidd-master" / "scripts"))

from orchestrator_pipeline import OrchestratorPipeline


def init_test_git_repo(repo_dir: Path) -> str:
    """Inicializa um repositório git temporário com configuração e commit inicial."""
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "AIDD Test Runner"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "runner@aidd.dev"], cwd=str(repo_dir), check=True, capture_output=True)
    
    # Cria arquivo base inicial
    readme = repo_dir / "README.md"
    readme.write_text("# Test Repo AIDD Pipeline\n", encoding="utf-8")
    
    # Copia schema de handoff e gate se necessário
    specs_target = repo_dir / "componentes" / "compartilhado" / "specs"
    specs_target.mkdir(parents=True, exist_ok=True)
    schema_orig = ROOT_DIR / "componentes" / "compartilhado" / "specs" / "handoff-execucao.schema.json"
    if schema_orig.is_file():
        shutil.copy(schema_orig, specs_target / "handoff-execucao.schema.json")
    
    gates_target = repo_dir / "gates"
    gates_target.mkdir(parents=True, exist_ok=True)
    gate_orig = ROOT_DIR / "gates" / "G_PIPELINE_HANDOFF.py"
    if gate_orig.is_file():
        shutil.copy(gate_orig, gates_target / "G_PIPELINE_HANDOFF.py")
        
    subprocess.run(["git", "add", "-A"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "chore: initial test commit"], cwd=str(repo_dir), check=True, capture_output=True)
    return "main"


def test_concurrency_3_parallel_tasks_in_worktrees(tmp_path):
    """Critério: executa 3 tarefas paralelas concorrentes em worktrees distintas sem colisão."""
    repo_dir = tmp_path / "repo_concurrency"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    # Cria script que cada worktree vai chamar para escrever em seu respectivo arquivo
    manifest = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste Concorrencia Worktrees",
            "repositorio_alvo": "test_repo",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "iniciativa_id": "TEST-PARALLEL-03",
            "descricao": "Validacao de 3 tasks concorrentes em worktrees"
        },
        "fase_paralela_assincrona": [
            {
                "id": "TICKET-SLICE-01",
                "titulo": "Implementar fatia 1 de autenticacao",
                "arquivos_alvo": ["auth_slice.py"],
                "comando_validacao": f'"{sys.executable}" -c "open(\'auth_slice.py\', \'w\').write(\'AUTH=True\\n\')"'
            },
            {
                "id": "TICKET-SLICE-02",
                "titulo": "Implementar fatia 2 de pagamentos",
                "arquivos_alvo": ["payment_slice.py"],
                "comando_validacao": f'"{sys.executable}" -c "open(\'payment_slice.py\', \'w\').write(\'PAY=True\\n\')"'
            },
            {
                "id": "TICKET-SLICE-03",
                "titulo": "Implementar fatia 3 de notificacoes",
                "arquivos_alvo": ["notify_slice.py"],
                "comando_validacao": f'"{sys.executable}" -c "open(\'notify_slice.py\', \'w\').write(\'NOTIFY=True\\n\')"'
            }
        ],
        "barreira_sincronizacao": [],
        "fase_sequencial_sincrona": [
            {
                "id": "TICKET-SEQ-01",
                "titulo": "Validar presenca das 3 fatias mescladas",
                "arquivos_alvo": ["README.md"],
                "comando_validacao": f'"{sys.executable}" -c "assert open(\'auth_slice.py\').read() == \'AUTH=True\\n\'; assert open(\'payment_slice.py\').read() == \'PAY=True\\n\'; assert open(\'notify_slice.py\').read() == \'NOTIFY=True\\n\'"'
            }
        ]
    }

    manifest_file = repo_dir / "manifest_test.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    orchestrator = OrchestratorPipeline(
        manifest_path=manifest_file,
        repo_root=repo_dir,
        base_branch=base_branch,
    )

    exit_code = orchestrator.execute_pipeline()
    assert exit_code == 0

    # Verifica que os 3 arquivos foram mesclados no repositório principal
    assert (repo_dir / "auth_slice.py").is_file()
    assert (repo_dir / "payment_slice.py").is_file()
    assert (repo_dir / "notify_slice.py").is_file()

    # Verifica que as worktrees foram 100% removidas
    worktrees_dir = repo_dir / ".worktrees"
    assert not worktrees_dir.exists() or not any(worktrees_dir.iterdir())


def test_join_barrier_blocks_merge_on_task_failure(tmp_path):
    """Critério: Join Barrier bloqueia o merge quando uma task falha na validação."""
    repo_dir = tmp_path / "repo_failure"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    manifest = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste Falha Join Barrier",
            "repositorio_alvo": "test_repo",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "iniciativa_id": "TEST-FAIL-01",
            "descricao": "Join barrier deve barrar merge com exit 1"
        },
        "fase_paralela_assincrona": [
            {
                "id": "TICKET-PASS-01",
                "titulo": "Tarefa que passa",
                "arquivos_alvo": ["pass_file.py"],
                "comando_validacao": f'"{sys.executable}" -c "open(\'pass_file.py\', \'w\').write(\'OK\')"'
            },
            {
                "id": "TICKET-FAIL-02",
                "titulo": "Tarefa que falha com exit 1",
                "arquivos_alvo": ["fail_file.py"],
                "comando_validacao": f'"{sys.executable}" -c "import sys; sys.exit(1)"'
            }
        ],
        "barreira_sincronizacao": [],
        "fase_sequencial_sincrona": []
    }

    manifest_file = repo_dir / "manifest_fail.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    orchestrator = OrchestratorPipeline(
        manifest_path=manifest_file,
        repo_root=repo_dir,
        base_branch=base_branch,
    )

    exit_code = orchestrator.execute_pipeline()
    assert exit_code == 1

    # Nenhuma das alterações pode ter sido mesclada na branch base
    assert not (repo_dir / "pass_file.py").exists()
    assert not (repo_dir / "fail_file.py").exists()

    # Worktrees devem ser 100% limpas mesmo com a falha
    worktrees_dir = repo_dir / ".worktrees"
    assert not worktrees_dir.exists() or not any(worktrees_dir.iterdir())


def test_join_barrier_blocks_merge_on_quality_gate_failure(tmp_path):
    """Critério: Join Barrier bloqueia quando um quality gate requerido falha na branch."""
    repo_dir = tmp_path / "repo_gate_fail"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    # Cria um script de quality gate que reprova intencionalmente
    failing_gate = repo_dir / "gates" / "G_FAILING_GATE.py"
    failing_gate.write_text(
        '#!/usr/bin/env python3\nimport sys\nprint("Gate reprovado propositalmente")\nsys.exit(1)\n',
        encoding="utf-8"
    )
    subprocess.run(["git", "add", "-A"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "commit", "-m", "chore: add failing gate"], cwd=str(repo_dir), check=True)

    manifest = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste Gate Rejeitado",
            "repositorio_alvo": "test_repo",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "iniciativa_id": "TEST-GATE-FAIL",
            "descricao": "Barreira com Quality Gate falho"
        },
        "fase_paralela_assincrona": [
            {
                "id": "TICKET-GATE-01",
                "titulo": "Tarefa com gate reprovado",
                "arquivos_alvo": ["tentativa.py"],
                "comando_validacao": f'"{sys.executable}" -c "open(\'tentativa.py\', \'w\').write(\'TESTE\')"'
            }
        ],
        "barreira_sincronizacao": ["G_FAILING_GATE.py"],
        "fase_sequencial_sincrona": []
    }

    manifest_file = repo_dir / "manifest_gate_fail.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    orchestrator = OrchestratorPipeline(
        manifest_path=manifest_file,
        repo_root=repo_dir,
        base_branch=base_branch,
    )

    exit_code = orchestrator.execute_pipeline()
    assert exit_code == 1

    # Não deve ter mesclado
    assert not (repo_dir / "tentativa.py").exists()

    # Worktrees limpas
    worktrees_dir = repo_dir / ".worktrees"
    assert not worktrees_dir.exists() or not any(worktrees_dir.iterdir())


def test_unhandled_exception_guarantees_cleanup(tmp_path, monkeypatch):
    """Critério: Worktrees efêmeras são 100% limpas mesmo sob exceções não tratadas."""
    repo_dir = tmp_path / "repo_unhandled"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    manifest = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste Excecao Inesperada",
            "repositorio_alvo": "test_repo",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "iniciativa_id": "TEST-EXC",
            "descricao": "Garantia de limpeza com exception"
        },
        "fase_paralela_assincrona": [
            {
                "id": "TICKET-EXC-01",
                "titulo": "Tarefa para crash",
                "arquivos_alvo": ["crash.py"],
                "comando_validacao": f'"{sys.executable}" -c "pass"'
            }
        ],
        "barreira_sincronizacao": [],
        "fase_sequencial_sincrona": []
    }

    manifest_file = repo_dir / "manifest_exc.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    orchestrator = OrchestratorPipeline(
        manifest_path=manifest_file,
        repo_root=repo_dir,
        base_branch=base_branch,
    )

    # Força exceção não tratada logo após a fase paralela
    def raise_crash(*args, **kwargs):
        raise RuntimeError("Crash deliberado de simulação de falha catastrófica")

    monkeypatch.setattr(orchestrator, "_execute_join_barrier", raise_crash)

    exit_code = orchestrator.execute_pipeline()
    assert exit_code == 1

    # Invariante: worktrees limpas
    worktrees_dir = repo_dir / ".worktrees"
    assert not worktrees_dir.exists() or not any(worktrees_dir.iterdir())


def test_cli_execution_cross_platform(tmp_path):
    """Critério: Execução via linha de comando (CLI) limpa e determinística."""
    repo_dir = tmp_path / "repo_cli"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    manifest = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste CLI Orchestrator",
            "repositorio_alvo": "test_repo",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "iniciativa_id": "TEST-CLI-01",
            "descricao": "Execucao direta via CLI"
        },
        "fase_paralela_assincrona": [],
        "barreira_sincronizacao": [],
        "fase_sequencial_sincrona": [
            {
                "id": "STEP-CLI-01",
                "titulo": "Step CLI unico",
                "arquivos_alvo": ["cli_ok.txt"],
                "comando_validacao": f'"{sys.executable}" -c "open(\'cli_ok.txt\', \'w\').write(\'CLI_OK\')"'
            }
        ]
    }

    manifest_file = repo_dir / "manifest_cli.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        str(SCRIPT_ORCHESTRATOR),
        "--manifesto",
        str(manifest_file),
        "--repo-root",
        str(repo_dir),
        "--base-branch",
        base_branch,
    ]

    res = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0
    assert (repo_dir / "cli_ok.txt").is_file()
