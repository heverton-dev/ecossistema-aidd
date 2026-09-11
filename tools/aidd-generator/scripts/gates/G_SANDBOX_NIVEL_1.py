#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_SANDBOX_NIVEL_1 — Subprocessos de código gerado nunca herdam os.environ.

Audita (via AST, Zero Token) todo código Python de um projeto gerado pela
Fase 8: qualquer subprocesso que passe `env` derivado de `os.environ`
(os.environ, os.environ.copy(), {**os.environ, ...}) é violação de SANDBOX
NÍVEL 1 e bloqueia com exit 1.

Falha com exit 1 se houver violação. Exit 0 = aprovado.

Uso:
    python scripts/gates/G_SANDBOX_NIVEL_1.py <pasta_projeto>
    python scripts/gates/G_SANDBOX_NIVEL_1.py --cache-dir .aidd/cache

Princípio AIDD: Gate mecânico — 100% determinístico, zero LLM.
"""

import sys
import importlib.util
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Helper compartilhado (sandbox_nivel_1.py) vive em scripts/phases/ — irmão de gates/.
_HELPER_PATH = Path(__file__).resolve().parent.parent / 'phases' / 'sandbox_nivel_1.py'

_EXCLUIDOS = {
    '__pycache__', '.git', 'node_modules', '.venv', 'venv', '.aidd',
    'dist', 'build', '.pytest_cache', 'htmlcov', '.coverage',
}


def _carregar_helper():
    """Carrega sandbox_nivel_1.py via importlib (padrão _carregar_modulo)."""
    if not _HELPER_PATH.exists():
        raise FileNotFoundError(
            f"Helper do SANDBOX NÍVEL 1 não encontrado: {_HELPER_PATH}"
        )
    spec = importlib.util.spec_from_file_location('sandbox_nivel_1', _HELPER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f'Não foi possível carregar {_HELPER_PATH}')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _descobrir_python_files(pasta_projeto: Path):
    """Descobre arquivos .py do projeto gerado (src/, raiz e testes)."""
    if not pasta_projeto.exists():
        return []
    arquivos = []
    for py_file in sorted(pasta_projeto.rglob('*.py')):
        partes = py_file.relative_to(pasta_projeto).parts
        if any(p in _EXCLUIDOS for p in partes):
            continue
        arquivos.append(py_file)
    return arquivos


def executar_gate(pasta_projeto) -> int:
    """Executa a auditoria AST de subprocessos/ambiente. 0 = aprovado, 1 = falhou."""
    print("\n" + "=" * 70)
    print("GATE: G_SANDBOX_NIVEL_1 — env mínimo de subprocessos (código gerado)")
    print("=" * 70 + "\n")

    if not Path(pasta_projeto).exists():
        print(f"❌ Pasta do projeto não encontrada: {pasta_projeto}")
        print("=" * 70)
        print("❌ GATE FALHOU")
        print("=" * 70)
        return 1

    try:
        helper = _carregar_helper()
    except (FileNotFoundError, ImportError) as e:
        print(f"❌ {e}")
        print("=" * 70)
        print("❌ GATE FALHOU")
        print("=" * 70)
        return 1

    arquivos = _descobrir_python_files(Path(pasta_projeto))
    print(f"🔍 {len(arquivos)} arquivo(s) Python audito(s)")

    total_violacoes = 0
    for py_file in arquivos:
        try:
            codigo = py_file.read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            print(f"   ❌ {py_file.relative_to(pasta_projeto)}: não legível ({e})")
            total_violacoes += 1
            continue
        violacoes = helper.auditar_subprocess_env_ast(codigo)
        for v in violacoes:
            v['arquivo'] = str(py_file.relative_to(pasta_projeto))
        if violacoes:
            print(f"   ❌ {py_file.relative_to(pasta_projeto)}:")
            for v in violacoes:
                print(f"      linha {v['linha']}: {v['detalhe']}")
            total_violacoes += len(violacoes)
        else:
            print(f"   ✅ {py_file.relative_to(pasta_projeto)}")

    print("\n" + "=" * 70)
    if total_violacoes:
        print(f"❌ GATE FALHOU — {total_violacoes} subprocesso(s) com herança de os.environ")
        print("   Corrija: env=os.environ → dicionário explícito com variáveis necessárias")
        print("=" * 70 + "\n")
        return 1
    print("✅ GATE PASSOU — nenhum subprocesso herda os.environ completo")
    print("=" * 70 + "\n")
    return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Gate SANDBOX NÍVEL 1: auditoria AST de subprocessos/código gerado'
    )
    parser.add_argument(
        'pasta_projeto',
        nargs='?',
        default='.',
        help='Pasta raiz do projeto a ser analisada (default: diretório atual)',
    )
    parser.add_argument(
        '--cache-dir',
        help='Pasta de cache do projeto (alternativa a pasta_projeto)',
    )
    args = parser.parse_args()

    return executar_gate(args.cache_dir if args.cache_dir else args.pasta_projeto)


if __name__ == '__main__':
    sys.exit(main())