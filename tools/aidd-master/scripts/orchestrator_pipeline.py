#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — MOTOR DE ORQUESTRAÇÃO DE PIPELINE (ISSUE-PIPE-0003)
=============================================================================
Executor determinístico de fases em Git Worktrees efêmeras com Barreira de
Sincronização (Join Barrier) e Fases Sequenciais Síncronas.

Invariantes e Leis Auditadas:
  1. Determinismo First (Lei #1): Despacho estruturado via JSON Schema e Git CLI.
  2. Saída Binária (Lei #2): exit 0 = sucesso completo; exit 1 = qualquer falha.
  3. Zero Stubs (Lei #5): Rejeição de dados incompletos ou não validados.
  4. Isolamento Estrito: Worktrees temporárias em '.worktrees/<task_id>' com
     garantia de cleanup 100% determinístico (bloco try-finally).
  5. Join Barrier: Validação rigorosa em cada branch e bloqueio de merge em
     caso de conflito ou falha de quality gates.
  6. Multiplataforma: Compatibilidade total Windows (PowerShell/CMD) e Linux (Bash).

Uso:
  python tools/aidd-master/scripts/orchestrator_pipeline.py --manifesto <caminho_manifesto.json>
=============================================================================
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class TaskExecutionResult:
    task_id: str
    title: str
    branch_name: str
    worktree_path: Path
    exit_code: int
    duration_sec: float
    stdout: str
    stderr: str
    error_message: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and self.error_message is None


@dataclass
class ActiveWorktree:
    task_id: str
    branch_name: str
    worktree_path: Path
    created_branch: bool = True


class OrchestratorPipeline:
    """Motor de execução de pipeline em Git Worktrees com Join Barrier."""

    def __init__(
        self,
        manifest_path: Path | str,
        repo_root: Optional[Path | str] = None,
        base_branch: Optional[str] = None,
        worktree_base_dir: Optional[Path | str] = None,
        dry_run: bool = False,
        verbose: bool = True,
    ) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        if not self.manifest_path.is_file():
            raise FileNotFoundError(f"Manifesto de handoff não encontrado: {self.manifest_path}")

        self.repo_root = Path(repo_root).resolve() if repo_root else self._detect_repo_root()
        self.dry_run = dry_run
        self.verbose = verbose
        self.active_worktrees: List[ActiveWorktree] = []

        # Determina base branch
        if base_branch:
            self.base_branch = base_branch
        else:
            self.base_branch = self._detect_current_branch()

        if worktree_base_dir:
            self.worktree_base_dir = Path(worktree_base_dir).resolve()
        else:
            self.worktree_base_dir = self.repo_root / ".worktrees"

        self.manifest_data: Dict[str, Any] = {}

    def log(self, message: str) -> None:
        if self.verbose:
            print(f"[ORCHESTRATOR] {message}")

    def _detect_repo_root(self) -> Path:
        """Detecta a raiz do repositório git."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(Path.cwd()),
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(res.stdout.strip()).resolve()
        except Exception:
            return Path.cwd().resolve()

    def _detect_current_branch(self) -> str:
        """Detecta o nome do branch atual."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                check=True,
            )
            branch = res.stdout.strip()
            return branch if branch and branch != "HEAD" else "main"
        except Exception:
            return "main"

    def validate_manifest(self) -> bool:
        """Valida formalmente o manifesto contra G_PIPELINE_HANDOFF."""
        self.log(f"Validando conformidade do manifesto: {self.manifest_path}")
        gate_script = self.repo_root / "gates" / "G_PIPELINE_HANDOFF.py"

        if gate_script.is_file():
            cmd = [sys.executable, str(gate_script), "--manifesto", str(self.manifest_path)]
            proc = subprocess.run(
                cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0:
                self.log(f"ERRO: Manifesto rejeitado por G_PIPELINE_HANDOFF:\n{proc.stderr}\n{proc.stdout}")
                return False
        else:
            self.log(f"AVISO: {gate_script} não encontrado. Realizando validação JSON básica.")

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest_data = json.load(f)
        except Exception as e:
            self.log(f"ERRO: Falha ao decodificar JSON do manifesto: {e}")
            return False

        return True

    def _get_parallel_steps(self) -> List[Dict[str, Any]]:
        return self.manifest_data.get("fase_paralela_assincrona") or self.manifest_data.get("parallel_async_steps") or []

    def _get_join_barrier(self) -> List[str]:
        return self.manifest_data.get("barreira_sincronizacao") or self.manifest_data.get("join_barrier") or []

    def _get_sequential_steps(self) -> List[Dict[str, Any]]:
        return self.manifest_data.get("fase_sequencial_sincrona") or self.manifest_data.get("sequential_sync_steps") or []

    def _create_worktree(self, task_id: str) -> ActiveWorktree:
        """Cria uma Git Worktree efêmera para o ticket."""
        clean_task_id = re.sub(r"[^A-Za-z0-9_.-]", "-", task_id)
        branch_name = f"task/{clean_task_id}"
        worktree_path = self.worktree_base_dir / clean_task_id

        self.worktree_base_dir.mkdir(parents=True, exist_ok=True)

        if worktree_path.exists():
            self._cleanup_single_worktree(worktree_path, branch_name)

        self.log(f"Criando worktree efêmera em '{worktree_path}' na branch '{branch_name}' a partir de '{self.base_branch}'")
        cmd = [
            "git",
            "worktree",
            "add",
            "-b",
            branch_name,
            str(worktree_path),
            self.base_branch,
        ]

        res = subprocess.run(
            cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if res.returncode != 0:
            # Tenta sem -b caso o branch já exista
            cmd_existing = [
                "git",
                "worktree",
                "add",
                str(worktree_path),
                branch_name,
            ]
            res2 = subprocess.run(
                cmd_existing,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if res2.returncode != 0:
                raise RuntimeError(f"Falha ao criar worktree para {task_id}: {res.stderr or res2.stderr}")

        active = ActiveWorktree(task_id=task_id, branch_name=branch_name, worktree_path=worktree_path)
        self.active_worktrees.append(active)
        return active

    def _run_task_in_worktree(self, step: Dict[str, Any], active_wt: ActiveWorktree) -> TaskExecutionResult:
        """Executa a task isolada dentro da worktree."""
        task_id = step["id"]
        title = step.get("titulo") or step.get("title", "")
        validation_cmd = step.get("comando_validacao") or step.get("validation_gate", "")

        self.log(f"Iniciando execução da task {task_id} ('{title}') em {active_wt.worktree_path}")
        start_time = time.time()

        if self.dry_run:
            time.sleep(0.05)
            return TaskExecutionResult(
                task_id=task_id,
                title=title,
                branch_name=active_wt.branch_name,
                worktree_path=active_wt.worktree_path,
                exit_code=0,
                duration_sec=0.05,
                stdout="[DRY-RUN] Simulação bem-sucedida.",
                stderr="",
            )

        try:
            # Executa comando de validação dentro da pasta da worktree
            # Usa shell=True para suportar sintaxe multiplataforma
            proc = subprocess.run(
                validation_cmd,
                cwd=str(active_wt.worktree_path),
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            duration = time.time() - start_time

            # Se a task fez modificações de arquivos, comita na branch da task
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(active_wt.worktree_path),
                capture_output=True,
                text=True,
            )
            if status_res.returncode == 0 and status_res.stdout.strip():
                subprocess.run(["git", "add", "-A"], cwd=str(active_wt.worktree_path), check=False)
                subprocess.run(
                    ["git", "commit", "-m", f"chore(task): auto-commit step {task_id} - {title}"],
                    cwd=str(active_wt.worktree_path),
                    check=False,
                )

            return TaskExecutionResult(
                task_id=task_id,
                title=title,
                branch_name=active_wt.branch_name,
                worktree_path=active_wt.worktree_path,
                exit_code=proc.returncode,
                duration_sec=duration,
                stdout=proc.stdout,
                stderr=proc.stderr,
                error_message=None if proc.returncode == 0 else f"Comando de validação falhou com exit code {proc.returncode}",
            )

        except Exception as ex:
            duration = time.time() - start_time
            return TaskExecutionResult(
                task_id=task_id,
                title=title,
                branch_name=active_wt.branch_name,
                worktree_path=active_wt.worktree_path,
                exit_code=1,
                duration_sec=duration,
                stdout="",
                stderr=str(ex),
                error_message=f"Exceção durante execução: {ex}",
            )

    def _execute_parallel_phase(self, steps: List[Dict[str, Any]]) -> Tuple[bool, List[TaskExecutionResult]]:
        """Cria worktrees e executa tarefas paralelas simultaneamente."""
        self.log(f"--- FASE PARALELA ASSÍNCRONA ({len(steps)} steps) ---")
        results: List[TaskExecutionResult] = []

        if not steps:
            return True, results

        # 1. Criação das worktrees efêmeras
        step_worktrees: List[Tuple[Dict[str, Any], ActiveWorktree]] = []
        for step in steps:
            active_wt = self._create_worktree(step["id"])
            step_worktrees.append((step, active_wt))

        # 2. Execução concorrente
        max_workers = min(len(steps), 8)
        self.log(f"Disparando {len(steps)} tarefas com {max_workers} workers concorrentes...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_step = {
                executor.submit(self._run_task_in_worktree, step, wt): (step, wt)
                for step, wt in step_worktrees
            }

            for future in concurrent.futures.as_completed(future_to_step):
                res = future.result()
                results.append(res)
                if res.passed:
                    self.log(f"  [OK] Task {res.task_id} passou ({res.duration_sec:.2f}s)")
                else:
                    self.log(f"  [FALHA] Task {res.task_id} falhou com código {res.exit_code}: {res.error_message}")
                    if res.stderr:
                        self.log(f"         stderr: {res.stderr.strip()[:200]}")

        # Avalia se todas passaram
        all_passed = all(r.passed for r in results)
        return all_passed, results

    def _execute_quality_gates_on_branch(self, branch_name: str, worktree_path: Path, gates: List[str]) -> bool:
        """Executa Quality Gates requeridos no contexto de uma branch antes do merge."""
        if not gates:
            return True

        self.log(f"Executando {len(gates)} Quality Gates na branch '{branch_name}'...")
        for gate in gates:
            cmd = gate.strip()
            # Se for apenas o nome de um arquivo python em gates/
            gate_path = self.repo_root / "gates" / cmd
            if gate_path.is_file():
                run_cmd = f'"{sys.executable}" "{gate_path}"'
            elif (self.repo_root / cmd).is_file():
                run_cmd = f'"{sys.executable}" "{self.repo_root / cmd}"'
            else:
                run_cmd = cmd

            self.log(f"  -> Rodando gate: {cmd}")
            proc = subprocess.run(
                run_cmd,
                cwd=str(worktree_path),
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0:
                self.log(f"  ❌ Quality Gate '{cmd}' REPROVOU na branch '{branch_name}' (exit code {proc.returncode})")
                if proc.stderr:
                    self.log(f"     stderr: {proc.stderr.strip()[:300]}")
                return False

        return True

    def _execute_join_barrier(
        self,
        parallel_results: List[TaskExecutionResult],
        gates: List[str],
    ) -> bool:
        """Barreira de Sincronização: avalia resultados, roda gates e realiza merge sequencial."""
        self.log(f"--- BARREIRA DE SINCRONIZAÇÃO (JOIN BARRIER) ---")

        # 1. Verifica se alguma task falhou
        failed_tasks = [r for r in parallel_results if not r.passed]
        if failed_tasks:
            self.log(f"❌ BARREIRA BLOQUEADA: {len(failed_tasks)} tarefa(s) falharam na fase paralela:")
            for f in failed_tasks:
                self.log(f"   - {f.task_id}: {f.error_message}")
            return False

        # 2. Executa Quality Gates requeridos em cada branch antes do merge
        for res in parallel_results:
            gate_success = self._execute_quality_gates_on_branch(res.branch_name, res.worktree_path, gates)
            if not gate_success:
                self.log(f"❌ BARREIRA BLOQUEADA: Quality Gate falhou para {res.task_id} ({res.branch_name})")
                return False

        # 3. Se dry-run, simula merge com sucesso
        if self.dry_run:
            self.log("[DRY-RUN] Simulação de Join Barrier e Merges concluída com sucesso.")
            return True

        # 4. Sequencialmente rebaseia/mescla as branches na base branch garantindo zero conflito
        self.log(f"Mesclando {len(parallel_results)} branches na branch '{self.base_branch}'...")
        for res in parallel_results:
            self.log(f"  Mesclando branch '{res.branch_name}'...")
            merge_cmd = [
                "git",
                "merge",
                "--no-ff",
                "-m",
                f"Merge branch '{res.branch_name}' into {self.base_branch} (orchestrator join barrier)",
                res.branch_name,
            ]
            m_proc = subprocess.run(
                merge_cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if m_proc.returncode != 0:
                self.log(f"  ❌ CONFLITO OU ERRO DE MERGE ao mesclar '{res.branch_name}':\n{m_proc.stderr or m_proc.stdout}")
                # Aborta o merge pendente para não deixar o repositório em estado instável
                subprocess.run(["git", "merge", "--abort"], cwd=str(self.repo_root), check=False)
                return False

        self.log("✅ Todas as branches da fase paralela foram mescladas com ZERO conflito.")
        return True

    def _execute_sequential_phase(self, steps: List[Dict[str, Any]]) -> bool:
        """Executa fase sequencial síncrona na árvore principal."""
        self.log(f"--- FASE SEQUENCIAL SÍNCRONA ({len(steps)} steps) ---")

        for idx, step in enumerate(steps, start=1):
            task_id = step["id"]
            title = step.get("titulo") or step.get("title", "")
            validation_cmd = step.get("comando_validacao") or step.get("validation_gate", "")

            self.log(f"[{idx}/{len(steps)}] Executando step {task_id}: '{title}'")
            if self.dry_run:
                self.log(f"  [DRY-RUN] Step {task_id} simulado.")
                continue

            start_t = time.time()
            proc = subprocess.run(
                validation_cmd,
                cwd=str(self.repo_root),
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            dur = time.time() - start_t

            if proc.returncode != 0:
                self.log(f"❌ Step sequencial {task_id} falhou com código {proc.returncode} após {dur:.2f}s:")
                if proc.stderr:
                    self.log(f"   stderr: {proc.stderr.strip()[:300]}")
                return False

            self.log(f"  ✅ Step {task_id} concluído com sucesso ({dur:.2f}s).")

        return True

    def _cleanup_single_worktree(self, worktree_path: Path, branch_name: Optional[str] = None) -> None:
        """Limpa deterministicamente uma única worktree e remove sua branch."""
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=str(self.repo_root),
                capture_output=True,
                check=False,
            )
        except Exception:
            pass

        # Garante remoção física da pasta caso o git deixe sobras no Windows
        if worktree_path.exists():
            try:
                shutil.rmtree(worktree_path, ignore_errors=True)
            except Exception:
                pass

        if branch_name:
            try:
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=str(self.repo_root),
                    capture_output=True,
                    check=False,
                )
            except Exception:
                pass

    def cleanup_all_worktrees(self) -> None:
        """Limpeza obrigatória de todas as worktrees ativas e efêmeras."""
        self.log("Executando limpeza de worktrees efêmeras...")
        for wt in list(self.active_worktrees):
            self._cleanup_single_worktree(wt.worktree_path, wt.branch_name)

        self.active_worktrees.clear()

        # Prune global do git worktree
        try:
            subprocess.run(["git", "worktree", "prune"], cwd=str(self.repo_root), capture_output=True, check=False)
        except Exception:
            pass

        # Remove pasta base se vazia
        if self.worktree_base_dir.exists():
            try:
                if not any(self.worktree_base_dir.iterdir()):
                    self.worktree_base_dir.rmdir()
            except Exception:
                pass

    def execute_pipeline(self) -> int:
        """Fluxo completo de orquestração determinística. Retorna 0 (sucesso) ou 1 (falha)."""
        self.log(f"Iniciando pipeline para manifesto: {self.manifest_path.name}")
        start_global = time.time()

        if not self.validate_manifest():
            return 1

        parallel_steps = self._get_parallel_steps()
        join_gates = self._get_join_barrier()
        sequential_steps = self._get_sequential_steps()

        try:
            # 1. Fase Paralela Assíncrona
            if parallel_steps:
                parallel_success, parallel_results = self._execute_parallel_phase(parallel_steps)

                # 2. Barreira de Sincronização
                join_success = self._execute_join_barrier(parallel_results, join_gates)
                if not join_success:
                    self.log("❌ Falha na Barreira de Sincronização. Abortando pipeline.")
                    return 1
            else:
                self.log("Nenhuma etapa paralela definida.")

            # 3. Fase Sequencial Síncrona
            if sequential_steps:
                seq_success = self._execute_sequential_phase(sequential_steps)
                if not seq_success:
                    self.log("❌ Falha na Fase Sequencial Síncrona. Abortando pipeline.")
                    return 1
            else:
                self.log("Nenhuma etapa sequencial síncrona definida.")

            elapsed = time.time() - start_global
            self.log(f"🎉 Pipeline executado com SUCESSO TOTAL em {elapsed:.2f}s.")
            return 0

        except Exception as e:
            self.log(f"❌ EXCEÇÃO NÃO TRATADA DURANTE A EXECUÇÃO DO PIPELINE: {e}")
            return 1

        finally:
            # Invariante: 100% de garantia de cleanup mesmo sob erro ou Ctrl+C
            self.cleanup_all_worktrees()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orquestrador Determinístico de Pipeline em Git Worktrees (ISSUE-PIPE-0003)"
    )
    parser.add_argument(
        "-m",
        "--manifesto",
        required=True,
        type=str,
        help="Caminho do manifesto JSON de handoff de execução.",
    )
    parser.add_argument(
        "-b",
        "--base-branch",
        type=str,
        default=None,
        help="Branch base para ramificação das worktrees e merge final.",
    )
    parser.add_argument(
        "--worktree-dir",
        type=str,
        default=None,
        help="Diretório onde as worktrees efêmeras serão instanciadas.",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Raiz do repositório git alvo.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo simulação determinístico sem invocar comandos reais.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Modo silencioso (apenas saídas essenciais).",
    )

    args = parser.parse_args()

    orchestrator = OrchestratorPipeline(
        manifest_path=args.manifesto,
        repo_root=args.repo_root,
        base_branch=args.base_branch,
        worktree_base_dir=args.worktree_dir,
        dry_run=args.dry_run,
        verbose=not args.quiet,
    )

    exit_code = orchestrator.execute_pipeline()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
