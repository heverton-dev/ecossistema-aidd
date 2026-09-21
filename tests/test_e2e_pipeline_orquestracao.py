# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTES END-TO-END DO PIPELINE DE ORQUESTRAÇÃO (ISSUE-PIPE-0007)
=============================================================================
Suíte de testes de integração ponta a ponta e regressão:
  1. Cenário 1: Plano sintético de 20 passos (15 paralelos assíncronos, 5 sequenciais):
     - Compilação dos tickets Markdown para 'handoff_evolution.json'.
     - Execução simultânea de 15 worktrees sem conflitos de filesystem.
     - Validação dos Quality Gates na barreira de sincronização (Join Barrier).
     - Merge determinístico e limpo na branch principal.
     - Execução em sequência estrita dos 5 passos sequenciais.
     - Verificação de 100% de cleanup de worktrees e branches temporárias.
  2. Cenário 2: Injeção de falha no passo 8 de 15:
     - Detecção de erro pelo Join Barrier.
     - Bloqueio imediato de merge de todas as branches.
     - Retorno com exit code 1.
     - Cleanup completo e determinístico sem deixar worktrees órfãs.
  3. Cenário 3: Execução real de ponta a ponta via CLI 'python ecossistema.py run-plan'.
=============================================================================
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_ECOSSISTEMA = ROOT_DIR / "ecossistema.py"
SCRIPT_ORCHESTRATOR = ROOT_DIR / "tools" / "aidd-master" / "scripts" / "orchestrator_pipeline.py"
SCRIPT_COMPILADOR = ROOT_DIR / "scripts" / "compilador_tickets_plano.py"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "tools" / "aidd-master" / "scripts"))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from orchestrator_pipeline import OrchestratorPipeline
from compilador_tickets_plano import compilar_plano


def init_test_git_repo(repo_dir: Path) -> str:
    """Inicializa um repositório git temporário com commit inicial e arquivos canônicos."""
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "AIDD Pipeline E2E Runner"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "runner-e2e@aidd.dev"], cwd=str(repo_dir), check=True, capture_output=True)

    # Cria README inicial
    readme = repo_dir / "README.md"
    readme.write_text("# Repositorio Temporario E2E Pipeline AIDD\n", encoding="utf-8")

    # Copia o schema canônico de handoff
    specs_target = repo_dir / "componentes" / "compartilhado" / "specs"
    specs_target.mkdir(parents=True, exist_ok=True)
    schema_orig = ROOT_DIR / "componentes" / "compartilhado" / "specs" / "handoff-execucao.schema.json"
    if schema_orig.is_file():
        shutil.copy(schema_orig, specs_target / "handoff-execucao.schema.json")

    # Copia quality gates essenciais
    gates_target = repo_dir / "gates"
    gates_target.mkdir(parents=True, exist_ok=True)
    gate_orig = ROOT_DIR / "gates" / "G_PIPELINE_HANDOFF.py"
    if gate_orig.is_file():
        shutil.copy(gate_orig, gates_target / "G_PIPELINE_HANDOFF.py")

    # Gate canônico para a barreira de sincronização
    gate_barreira = gates_target / "G_BARREIRA_TESTE.py"
    gate_barreira.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print('Gate de barreira verificado com sucesso!')\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )

    # Cria pasta de fatias para que os diretórios pais existam per G_PIPELINE_HANDOFF
    fatias_dir = repo_dir / "fatias"
    fatias_dir.mkdir(parents=True, exist_ok=True)
    (fatias_dir / ".gitkeep").write_text("", encoding="utf-8")

    subprocess.run(["git", "add", "-A"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit for pipeline e2e test"], cwd=str(repo_dir), check=True, capture_output=True)
    return "main"


def criar_plano_sintetico_20_passos(pasta_plano: Path, falha_no_passo_8: bool = False) -> None:
    """Cria uma iniciativa de plano sintético com 15 fatias paralelas e 5 fatias sequenciais."""
    pasta_plano.mkdir(parents=True, exist_ok=True)

    # 1. 00-PROCESSO-E-DECISOES.md
    decisoes = pasta_plano / "00-PROCESSO-E-DECISOES.md"
    decisoes.write_text(
        "# PROCESSO E DECISÕES — Plano Sintético 20 Passos E2E\n\n"
        "- **Objetivo Principal:** Executar refatoração sintética em 20 passos (15 paralelos assíncronos e 5 sequenciais síncronos).\n"
        "- **Status:** aprovado\n"
        "- **Monorepo:** ecossistema-aidd\n",
        encoding="utf-8",
    )

    # 2. 01-fase-paralela.md com 15 tickets independentes
    linhas_paralelas = [
        "# Fase Paralela Assíncrona — 15 Fatias Independentes\n",
        "Fatias modulares executadas em paralelo isolado via git worktree.\n",
    ]
    for i in range(1, 16):
        num_str = f"{i:02d}"
        if falha_no_passo_8 and i == 8:
            cmd_val = f'"{sys.executable}" -c "import sys; print(\'FALHA_DELIBERADA_STEP_08\'); sys.exit(1)"'
        else:
            cmd_val = f'"{sys.executable}" -c "import os; os.makedirs(\'fatias\', exist_ok=True); open(\'fatias/slice_{num_str}.py\', \'w\').write(\'SLICE_{num_str} = True\\n\')"'

        linhas_paralelas.extend([
            f"\n### [TICKET-PAR-{num_str}] Implementar Fatia Isolada {num_str}",
            f"- **Arquivos Alvo:** `fatias/slice_{num_str}.py`",
            f"- **Comando de Validação:** `{cmd_val}`",
            f"- **Bloqueado por:** []",
            f"- **Isolamento:** worktree",
        ])

    arquivo_paralelo = pasta_plano / "01-fase-paralela.md"
    arquivo_paralelo.write_text("\n".join(linhas_paralelas) + "\n", encoding="utf-8")

    # 3. 02-fase-sequencial.md com 5 tickets dependentes
    linhas_sequenciais = [
        "# Fase Sequencial Síncrona — 5 Passos de Integração e Agregação\n",
        "Execução progressiva após o Join Barrier.\n",
    ]
    for j in range(1, 6):
        num_str = f"{j:02d}"
        dep = "[TICKET-PAR-15]" if j == 1 else f"[TICKET-SEQ-{j-1:02d}]"
        modo_abertura = "'w'" if j == 1 else "'a'"
        cmd_val = f'"{sys.executable}" -c "import os; os.makedirs(\'fatias\', exist_ok=True); open(\'fatias/agregador.py\', {modo_abertura}).write(\'STEP_{num_str} = True\\n\')"'

        linhas_sequenciais.extend([
            f"\n### [TICKET-SEQ-{num_str}] Agregação e Validação Passo {num_str}",
            f"- **Arquivos Alvo:** `fatias/agregador.py`",
            f"- **Comando de Validação:** `{cmd_val}`",
            f"- **Bloqueado por:** {dep}",
            f"- **Isolamento:** principal",
        ])

    arquivo_sequencial = pasta_plano / "02-fase-sequencial.md"
    arquivo_sequencial.write_text("\n".join(linhas_sequenciais) + "\n", encoding="utf-8")


def _obter_worktrees_ativas(repo_dir: Path) -> List[str]:
    """Lista as worktrees ativas registradas no git."""
    res = subprocess.run(["git", "worktree", "list"], cwd=str(repo_dir), capture_output=True, text=True, check=True)
    linhas = [ln.strip() for ln in res.stdout.strip().splitlines() if ln.strip()]
    return linhas


def test_e2e_synthetic_20_steps_plan_execution(tmp_path):
    """
    Cenário 1: Plano sintético de 20 passos (15 paralelos + 5 sequenciais).
    Verifica integridade, concorrência, Join Barrier, merge limpo e 100% cleanup.
    """
    repo_dir = tmp_path / "repo_e2e_success"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    pasta_plano = repo_dir / "docs" / "planos" / "PLAN-9901-refactor-sintetico"
    criar_plano_sintetico_20_passos(pasta_plano, falha_no_passo_8=False)

    # 1. Compilação do plano para handoff_evolution.json
    manifesto, output_path = compilar_plano(
        pasta_plano_arg=pasta_plano,
        barreira_gate_padrao="gates/G_BARREIRA_TESTE.py",
    )

    assert output_path.is_file()
    assert len(manifesto.get("fase_paralela_assincrona", [])) == 15
    assert len(manifesto.get("fase_sequencial_sincrona", [])) == 5
    assert len(manifesto.get("barreira_sincronizacao", [])) == 1
    assert manifesto["barreira_sincronizacao"][0] == "gates/G_BARREIRA_TESTE.py"

    # 2. Execução da orquestração via OrchestratorPipeline
    orchestrator = OrchestratorPipeline(
        manifest_path=output_path,
        repo_root=repo_dir,
        base_branch=base_branch,
    )

    exit_code = orchestrator.execute_pipeline()
    assert exit_code == 0

    # 3. Validação dos artefatos mesclados na branch principal (main)
    # 15 fatias da fase paralela
    for i in range(1, 16):
        num_str = f"{i:02d}"
        slice_file = repo_dir / "fatias" / f"slice_{num_str}.py"
        assert slice_file.is_file(), f"Fatia esperada ausente: {slice_file}"
        conteudo = slice_file.read_text(encoding="utf-8")
        assert f"SLICE_{num_str} = True" in conteudo

    # 5 passos da fase sequencial consolidados no agregador
    agregador_file = repo_dir / "fatias" / "agregador.py"
    assert agregador_file.is_file(), f"Arquivo de agregação sequencial ausente: {agregador_file}"
    conteudo_agg = agregador_file.read_text(encoding="utf-8")
    for j in range(1, 6):
        assert f"STEP_{j:02d} = True" in conteudo_agg

    # 4. Invariante Inviolável: 100% de Cleanup de worktrees e branches
    worktrees_dir = repo_dir / ".worktrees"
    if worktrees_dir.exists():
        assert len(list(worktrees_dir.iterdir())) == 0, "Diretório .worktrees não está vazio!"

    wt_list = _obter_worktrees_ativas(repo_dir)
    assert len(wt_list) == 1, f"Worktrees órfãs encontradas no git: {wt_list}"

    # Verifica que não restaram branches temporárias órfãs (aidd/wt/*)
    res_branches = subprocess.run(["git", "branch"], cwd=str(repo_dir), capture_output=True, text=True, check=True)
    assert "aidd/wt/" not in res_branches.stdout


def test_e2e_error_injection_step_8_aborts_and_cleans_up(tmp_path):
    """
    Cenário 2: Injeção de erro deliberado no passo 8 de 15.
    Verifica que o Join Barrier detecta a falha, bloqueia qualquer merge na branch principal,
    retorna exit 1 e executa cleanup total sem deixar worktrees órfãs.
    """
    repo_dir = tmp_path / "repo_e2e_failure"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    pasta_plano = repo_dir / "docs" / "planos" / "PLAN-9902-falha-step-8"
    criar_plano_sintetico_20_passos(pasta_plano, falha_no_passo_8=True)

    manifesto, output_path = compilar_plano(
        pasta_plano_arg=pasta_plano,
        barreira_gate_padrao="gates/G_BARREIRA_TESTE.py",
    )

    orchestrator = OrchestratorPipeline(
        manifest_path=output_path,
        repo_root=repo_dir,
        base_branch=base_branch,
    )

    exit_code = orchestrator.execute_pipeline()
    assert exit_code == 1

    # Invariante: Bloqueio estrito de merge. Nenhuma fatia pode ter sido mesclada na base_branch
    fatias_dir = repo_dir / "fatias"
    assert not any(f.name.startswith("slice_") for f in fatias_dir.iterdir()), "Merge indevido ocorreu na branch principal após falha da task 8!"
    assert not (fatias_dir / "agregador.py").exists(), "Agregador sequencial executado indevidamente após falha!"

    # Invariante: 100% de Cleanup mesmo sob falha
    worktrees_dir = repo_dir / ".worktrees"
    if worktrees_dir.exists():
        assert len(list(worktrees_dir.iterdir())) == 0, "Diretório .worktrees retém pastas órfãs após falha!"

    wt_list = _obter_worktrees_ativas(repo_dir)
    assert len(wt_list) == 1, f"Worktrees órfãs no git após falha: {wt_list}"

    res_branches = subprocess.run(["git", "branch"], cwd=str(repo_dir), capture_output=True, text=True, check=True)
    assert "aidd/wt/" not in res_branches.stdout


def test_e2e_cli_run_plan_subprocess_execution(tmp_path):
    """
    Cenário 3: Execução real de ponta a ponta chamando a CLI 'python ecossistema.py run-plan'
    como processo filho com resolução automática de plano e flags de execução.
    """
    repo_dir = tmp_path / "repo_e2e_cli"
    repo_dir.mkdir()
    base_branch = init_test_git_repo(repo_dir)

    pasta_plano = repo_dir / "docs" / "planos" / "PLAN-9903-cli-e2e"
    criar_plano_sintetico_20_passos(pasta_plano, falha_no_passo_8=False)

    cmd = [
        sys.executable,
        str(SCRIPT_ECOSSISTEMA),
        "run-plan",
        str(pasta_plano),
        "--repo-root",
        str(repo_dir),
        "--base-branch",
        base_branch,
        "--barreira-gate",
        "gates/G_BARREIRA_TESTE.py",
    ]

    res = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert res.returncode == 0, f"run-plan via CLI falhou com code {res.returncode}:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"

    # Valida que gerou os 15 arquivos de fatia e agregador no repositório de teste
    for i in range(1, 16):
        num_str = f"{i:02d}"
        assert (repo_dir / "fatias" / f"slice_{num_str}.py").is_file()

    assert (repo_dir / "fatias" / "agregador.py").is_file()

    # Valida cleanup no git
    wt_list = _obter_worktrees_ativas(repo_dir)
    assert len(wt_list) == 1
