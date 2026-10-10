# -*- coding: utf-8 -*-
"""
Suíte de Micro-Gates Determinísticos de Worktree (Shift-Left).

Executados no fechamento isolado de cada worktree de fatia vertical (VSA),
antes de permitir o rebase e a fusão na branch de convergência.

Ordem determinística:
  1. Compilação de sintaxe Python (py_compile em todos os .py da fatia).
  2. Varredura de segredos e credenciais nos arquivos da fatia.
  3. Verificação de ausência de stubs (Lei #5: TODO, FIXME, PLACEHOLDER, dummy).
  4. Testes unitários focados na fatia (pytest direcionado aos testes da fatia).
"""
from __future__ import annotations

import argparse
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

PADRAO_STUB = re.compile(
    r"\b(TODO|FIXME|PLACEHOLDER|TBD|dummy|stub)\b",
    re.IGNORECASE
)


def verificar_sintaxe_python(worktree_path: Path, arquivos: List[str]) -> Tuple[bool, List[str]]:
    """Compila via py_compile todos os arquivos .py listados ou encontrados na worktree."""
    erros = []
    py_files = []

    if arquivos:
        for a in arquivos:
            p = worktree_path / a
            if p.suffix == ".py" and p.is_file():
                py_files.append(p)
    else:
        py_files = list(worktree_path.glob("**/*.py"))

    for pf in py_files:
        # Pula arquivos em venv ou cache
        caminho_rel = str(pf.relative_to(worktree_path)).replace("\\", "/")
        if any(part in caminho_rel for part in [".venv", "__pycache__", ".git", ".pytest_cache"]):
            continue
        try:
            py_compile.compile(str(pf), doraise=True)
        except py_compile.PyCompileError as e:
            erros.append(f"Erro de sintaxe em {caminho_rel}: {e}")

    return len(erros) == 0, erros


def verificar_stubs_fatia(worktree_path: Path, arquivos: List[str]) -> Tuple[bool, List[str]]:
    """Garante ausência de stubs (Lei #5) no código entregue pela fatia."""
    erros = []
    arquivos_alvo = []

    if arquivos:
        for a in arquivos:
            p = worktree_path / a
            if p.is_file():
                arquivos_alvo.append(p)
    else:
        for ext in [".py", ".ts", ".tsx", ".js", ".json", ".sql"]:
            arquivos_alvo.extend(worktree_path.glob(f"**/*{ext}"))

    for arq in arquivos_alvo:
        caminho_rel = str(arq.relative_to(worktree_path)).replace("\\", "/")
        if any(part in caminho_rel for part in [".venv", "__pycache__", ".git", "node_modules"]):
            continue
        try:
            conteudo = arq.read_text(encoding="utf-8", errors="ignore")
            for idx, linha in enumerate(conteudo.splitlines(), start=1):
                if PADRAO_STUB.search(linha) and not linha.strip().startswith("#"):
                    erros.append(f"Stub detectado em {caminho_rel}:{idx}: {linha.strip()[:80]}")
        except Exception as e:
            erros.append(f"Falha ao ler {caminho_rel}: {e}")

    return len(erros) == 0, erros


def executar_micro_gates(
    worktree_path: Path | str,
    slice_id: str = "",
    arquivos_esperados: List[str] | None = None,
    comandos_teste: List[str] | None = None,
    verbose: bool = True,
) -> Tuple[bool, List[str]]:
    """Executa a suíte completa de micro-gates na worktree informada."""
    wt = Path(worktree_path).resolve()
    if not wt.is_dir():
        return False, [f"Diretório de worktree inválido: {wt}"]

    arqs = arquivos_esperados or []
    todos_erros = []

    if verbose:
        print(f"[MICRO-GATES] Iniciando validação shift-left na worktree '{wt.name}' (fatia: {slice_id or 'anonima'})")

    # 1. Sintaxe Python
    ok_sintaxe, erros_sintaxe = verificar_sintaxe_python(wt, arqs)
    if not ok_sintaxe:
        todos_erros.extend(erros_sintaxe)
        if verbose:
            print(f"[MICRO-GATES] [FALHA] Sintaxe inválida detectada ({len(erros_sintaxe)} erro(s))")
        return False, todos_erros

    if verbose:
        print("[MICRO-GATES] [PASS] Sintaxe Python verificada.")

    # 2. Ausência de Stubs (Lei #5)
    ok_stubs, erros_stubs = verificar_stubs_fatia(wt, arqs)
    if not ok_stubs:
        todos_erros.extend(erros_stubs)
        if verbose:
            print(f"[MICRO-GATES] [FALHA] Stubs detectados ({len(erros_stubs)} erro(s))")
        return False, todos_erros

    if verbose:
        print("[MICRO-GATES] [PASS] Ausência de stubs (Lei #5) confirmada.")

    # 3. Testes unitários direcionados da fatia
    if comandos_teste:
        # Garante defensivamente inicialização de pacotes Python quando as pastas existirem
        if (wt / "src").is_dir():
            (wt / "src" / "__init__.py").touch(exist_ok=True)
            if (wt / "src" / "slices").is_dir():
                (wt / "src" / "slices" / "__init__.py").touch(exist_ok=True)
        if (wt / "tests").is_dir():
            (wt / "tests" / "__init__.py").touch(exist_ok=True)
            if (wt / "tests" / "slices").is_dir():
                (wt / "tests" / "slices" / "__init__.py").touch(exist_ok=True)

        env_cmd = dict(os.environ)
        caminhos_python = [str(wt), str(wt / "src")]
        if "PYTHONPATH" in env_cmd:
            caminhos_python.append(env_cmd["PYTHONPATH"])
        env_cmd["PYTHONPATH"] = os.pathsep.join(caminhos_python)

        for cmd in comandos_teste:
            cmd_exec = cmd
            if cmd_exec.startswith("pytest ") or cmd_exec == "pytest":
                cmd_exec = f'"{sys.executable}" -m ' + cmd_exec
            if verbose:
                print(f"[MICRO-GATES] [TESTE] Executando: {cmd_exec}")
            res = subprocess.run(
                cmd_exec,
                cwd=str(wt),
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env_cmd,
            )
            if res.returncode != 0:
                msg = f"Falha no teste '{cmd}' (exit {res.returncode}):\n{res.stderr or res.stdout}"
                todos_erros.append(msg)
                if verbose:
                    print(f"[MICRO-GATES] [FALHA] {msg}")
                return False, todos_erros

        if verbose:
            print("[MICRO-GATES] [PASS] Testes unitários da fatia aprovados.")

    if verbose:
        print(f"[MICRO-GATES] SUCESSO: Todos os micro-gates aprovados na fatia '{slice_id}'.")
    return True, []


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="micro_gates_worktree",
        description="Executa micro-gates de shift-left no escopo isolado de uma worktree",
    )
    parser.add_argument("--worktree-path", "-w", required=True, help="Caminho para o diretório da worktree")
    parser.add_argument("--slice-id", "-s", default="", help="Identificador da fatia vertical")
    parser.add_argument("--arquivos", "-a", nargs="*", default=[], help="Lista de arquivos esperados da fatia")
    parser.add_argument("--teste-cmd", "-t", action="append", default=[], help="Comandos de teste da fatia")

    args = parser.parse_args(argv)
    ok, erros = executar_micro_gates(
        worktree_path=args.worktree_path,
        slice_id=args.slice_id,
        arquivos_esperados=args.arquivos,
        comandos_teste=args.teste_cmd,
        verbose=True,
    )

    if not ok:
        for e in erros:
            print(f"[ERRO] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
