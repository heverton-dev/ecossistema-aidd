#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDADOR CENTRAL: verificar_gates — Executa todos os gates do pipeline AIDD.

Orquestra a execução sequencial de todos os gates mecânicos:
  - G_BLOQUEAR_SEGREDOS: Bloqueio de segredos hardcoded
  - G_VERIFICAR_LLM_PRONTO: Pré-voo de credenciais LLM
  - G_HARNESS_COMPAT: Compatibilidade de harness
  - G_INTEGRACAO_CROSS_SCRIPT (I3): Compatibilidade entre scripts irmãos
  - G_CYBERSECURITY_OWASP: Varredura OWASP Top 10

Uso:
    python scripts/verificar_gates.py <pasta_projeto>
    python scripts/verificar_gates.py --cache-dir .aidd/cache
    python scripts/verificar_gates.py --apenas I3        # roda só o Gate I3
    python scripts/verificar_gates.py --apenas OWASP     # roda só o Gate OWASP

Exit code: 0 = todos passaram, 1 = pelo menos um falhou.
"""

import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple, Callable

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

GATES_DIR = Path(__file__).resolve().parent / 'gates'


def _carregar_modulo(nome: str, caminho: Path):
    """Carrega um módulo Python por caminho (importlib)."""
    spec = importlib.util.spec_from_file_location(nome, caminho)
    if spec is None or spec.loader is None:
        raise ImportError(f'Não foi possível carregar {caminho}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# =============================================================================
# DEFINIÇÃO DOS GATES
# =============================================================================

def _gate_bloquear_segredos(pasta: Path) -> int:
    """G_BLOQUEAR_SEGREDOS: escaneia arquivos por segredos hardcoded."""
    mod = _carregar_modulo('G_BLOQUEAR_SEGREDOS', GATES_DIR / 'G_BLOQUEAR_SEGREDOS.py')
    # Este gate opera sobre staged files por padrão.
    # Quando chamado via verificar_gates, escaneia a pasta do projeto.
    # Usamos --arquivo em cada .py da pasta.
    import subprocess
    py_files = list(pasta.rglob('*.py'))
    excluidos = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'tests'}
    py_files = [
        f for f in py_files
        if not any(p in excluidos for p in f.relative_to(pasta).parts)
    ]

    if not py_files:
        print("   (nenhum arquivo .py para escanear)")
        return 0

    todos_achados = []
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read()
            achados = mod.escanear_conteudo(conteudo, str(py_file.relative_to(pasta)))
            todos_achados.extend(achados)
        except OSError:
            pass

    if todos_achados:
        print("   ❌ SEGREDO(S) ENCONTRADO(S):")
        for a in todos_achados:
            print(f"   {a}")
        return 1
    print("   ✅ Nenhum segredo encontrado")
    return 0


def _gate_verificar_llm(pasta: Path) -> int:
    """G_VERIFICAR_LLM_PRONTO: verifica se LLM está configurado."""
    mod = _carregar_modulo('G_VERIFICAR_LLM_PRONTO', GATES_DIR / 'G_VERIFICAR_LLM_PRONTO.py')
    return mod.main()


def _gate_harness_compat(pasta: Path) -> int:
    """G_HARNESS_COMPAT: verifica compatibilidade de harness."""
    mod = _carregar_modulo('G_HARNESS_COMPAT', GATES_DIR / 'G_HARNESS_COMPAT.py')
    return mod.main()


def _gate_integracao_cross_script(pasta: Path) -> int:
    """G_INTEGRACAO_CROSS_SCRIPT (I3): compatibilidade entre scripts irmãos."""
    mod = _carregar_modulo('G_INTEGRACAO_CROSS_SCRIPT', GATES_DIR / 'G_INTEGRACAO_CROSS_SCRIPT.py')
    return mod.executar_gate(pasta)


def _gate_cybersecurity_owasp(pasta: Path) -> int:
    """G_CYBERSECURITY_OWASP: varredura OWASP Top 10."""
    mod = _carregar_modulo('G_CYBERSECURITY_OWASP', GATES_DIR / 'G_CYBERSECURITY_OWASP.py')
    return mod.executar_gate(pasta)


def _gate_inject(pasta: Path) -> int:
    """G_INJECT: valida o Injetor Universal de Componentes (schema, profiles, materialização, rollback)."""
    mod = _carregar_modulo('G_INJECT', GATES_DIR / 'G_INJECT.py')
    return mod.executar_gate(pasta)


# Mapa de gates disponíveis: (nome, aliases, função, obrigatório)
GATES_DISPONIVEIS: List[Tuple[str, List[str], Callable, bool]] = [
    ('G_BLOQUEAR_SEGREDOS', ['segredos', 'secrets'], _gate_bloquear_segredos, True),
    ('G_VERIFICAR_LLM_PRONTO', ['llm', 'preflight'], _gate_verificar_llm, False),
    ('G_HARNESS_COMPAT', ['harness', 'compat'], _gate_harness_compat, False),
    ('G_INTEGRACAO_CROSS_SCRIPT', ['I3', 'integracao', 'cross-script'], _gate_integracao_cross_script, True),
    ('G_CYBERSECURITY_OWASP', ['OWASP', 'owasp', 'cybersecurity', 'ciberseguranca'], _gate_cybersecurity_owasp, True),
    ('G_INJECT', ['inject', 'injecao', 'injetor'], _gate_inject, False),
]


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Validador central: executa todos os gates do pipeline AIDD'
    )
    parser.add_argument(
        'pasta_projeto',
        nargs='?',
        default='.',
        help='Pasta raiz do projeto (default: diretório atual)',
    )
    parser.add_argument(
        '--cache-dir',
        help='Pasta de cache (alternativa a pasta_projeto)',
    )
    parser.add_argument(
        '--apenas',
        help='Executar apenas um gate específico (nome ou alias)',
    )
    parser.add_argument(
        '--pular',
        action='append',
        default=[],
        help='Pular um gate específico (pode ser usado múltiplas vezes)',
    )
    args = parser.parse_args()

    pasta = Path(args.cache_dir) if args.cache_dir else Path(args.pasta_projeto)

    print("\n" + "=" * 70)
    print("VALIDADOR CENTRAL DE GATES — Pipeline AIDD")
    print(f"Pasta: {pasta.resolve()}")
    print("=" * 70 + "\n")

    # Filtrar gates
    gates_para_executar = []
    for nome, aliases, func, obrigatorio in GATES_DISPONIVEIS:
        # Filtro --apenas
        if args.apenas:
            if args.apenas.lower() not in ([nome.lower()] + [a.lower() for a in aliases]):
                continue
        # Filtro --pular
        if any(p.lower() in ([nome.lower()] + [a.lower() for a in aliases]) for p in args.pular):
            continue
        gates_para_executar.append((nome, func, obrigatorio))

    if not gates_para_executar:
        print("⚠️  Nenhum gate selecionado")
        return 0

    resultados = []
    for nome, func, obrigatorio in gates_para_executar:
        print(f"\n{'─' * 70}")
        print(f"▶ Executando: {nome}" + (" (obrigatório)" if obrigatorio else " (opcional)"))
        print(f"{'─' * 70}")

        try:
            exit_code = func(pasta)
            passou = exit_code == 0
        except Exception as e:
            print(f"   ❌ ERRO: {type(e).__name__}: {e}")
            passou = False
            exit_code = 1

        resultados.append((nome, passou, obrigatorio))

    # Relatório final
    print("\n" + "=" * 70)
    print("RELATÓRIO FINAL DE GATES")
    print("=" * 70)

    todos_obrigatorios_passaram = True
    for nome, passou, obrigatorio in resultados:
        icon = "✅" if passou else "❌"
        tag = " [obrigatório]" if obrigatorio else " [opcional]"
        print(f"  {icon} {nome}{tag}")
        if not passou and obrigatorio:
            todos_obrigatorios_passaram = False

    total = len(resultados)
    passaram = sum(1 for _, p, _ in resultados if p)

    print(f"\n📊 {passaram}/{total} gates passaram")

    print("\n" + "=" * 70)
    if todos_obrigatorios_passaram:
        print("✅ TODOS OS GATES OBRIGATÓRIOS PASSARAM")
        print("=" * 70 + "\n")
        return 0
    else:
        print("❌ PELO MENOS UM GATE OBRIGATÓRIO FALHOU")
        print("=" * 70 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
