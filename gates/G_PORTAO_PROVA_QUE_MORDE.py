#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_PORTAO_PROVA_QUE_MORDE (Lei Canônica #13)
=============================================================================
Meta-Quality Gate que audita e bloqueia qualquer gate que seja entregue
sem um teste automatizado que prove que ele reprova (exit 1).

Regra Canônica (docs/protocolos/CONVENCAO-AUTORIA-GATES.md e Lei #13 do AGENTS.md):
  Todo gate DEVE ser acompanhado de teste automatizado que deliberadamente quebra
  a condição resguardada e asserte exit 1 (reprovação).
  Testes de caminho feliz (que apenas afirmam exit 0) NÃO satisfazem o requisito.

Critérios determinísticos validados por este meta-gate para cada gates/G_*.py:
  1. Paridade de Arquivo: Existência de gates/test_g_<nome_minusculo>.py.
  2. Presença de Funções de Teste: Ao menos uma função test_*().
  3. Prova de Reprovação (Exit 1): Ao menos uma asserção de código de erro 1
     (returncode == 1, assertEqual(..., 1), pytest.raises(SystemExit) com code 1, etc.)
     em cenário deliberado de quebra da invariante.

Saída:
  exit 0 = Todos os gates possuem testes comprovando caminho de reprovação (exit 1).
  exit 1 = Ao menos um gate carece de teste ou seu teste não asserte exit 1.
"""

import ast
import os
import re
import sys
from typing import Dict, List, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")

# Padrões que indicam asserção de saída com falha (exit 1)
PATTERNS_FAILING_EXIT = [
    re.compile(r"returncode\s*==\s*1\b"),
    re.compile(r"returncode\s*!=\s*0\b"),
    re.compile(r"code\s*==\s*1\b"),
    re.compile(r"codigo\s*==\s*1\b"),
    re.compile(r"saida\s*==\s*1\b"),
    re.compile(r"exit_code\s*==\s*1\b"),
    re.compile(r"assert\s+[\w\.]+\(\)\s*==\s*1\b"),
    re.compile(r"assertEqual\s*\(\s*[\w\.]+\s*,\s*1\s*\)"),
    re.compile(r"assertNotEqual\s*\(\s*[\w\.]+\s*,\s*0\s*\)"),
    re.compile(r"excinfo\.value\.code\s*==\s*1\b"),
    re.compile(r"SystemExit\s*\(\s*1\s*\)"),
]

# Nomes ou termos que indicam função voltada a testar falha/reprovação
TERMOS_CENARIO_FALHA = {
    "reprova", "falha", "violacao", "detecta", "invalido", "inconsistente",
    "corrompido", "orfa", "ausente", "sem_", "bloqueio", "leak", "proibido",
    "morde", "bite", "fail", "broken", "dirty"
}


def encontrar_arquivo_teste(gate_file: str, gates_dir: str) -> str | None:
    """Mapeia G_NOME_DO_GATE.py para test_g_nome_do_gate.py."""
    base = os.path.splitext(gate_file)[0]
    expected_name = f"test_{base.lower()}.py"
    path = os.path.join(gates_dir, expected_name)
    if os.path.isfile(path):
        return path
    return None


def auditar_teste_de_falha(test_path: str) -> Tuple[bool, List[str]]:
    """Verifica se o arquivo de teste contém teste de caminho de falha com exit 1."""
    erros = []
    try:
        with open(test_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return False, [f"Erro ao ler arquivo de teste {test_path}: {e}"]

    # 1. Checagem sintática via AST
    try:
        tree = ast.parse(content, filename=test_path)
    except SyntaxError as e:
        return False, [f"Erro de sintaxe em {test_path}: {e}"]

    test_funcs = [
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]

    if not test_funcs:
        return False, ["Nenhuma função de teste (def test_*) encontrada."]

    # 2. Verifica se há função direcionada a reprovação/falha
    failing_scenario_funcs = [
        fn for fn in test_funcs
        if any(termo in fn.lower() for termo in TERMOS_CENARIO_FALHA)
    ]

    # 3. Verifica se o teste asserte código de saída 1 (reprovação real do gate)
    tem_assercao_exit_1 = any(p.search(content) for p in PATTERNS_FAILING_EXIT)

    if not tem_assercao_exit_1:
        erros.append(
            "Ausência de asserção de código de reprovação (exit 1 / returncode == 1 / code == 1). "
            "Testes de caminho feliz (exit 0) não provam que o portão morde (Lei #13)."
        )

    if not failing_scenario_funcs and not tem_assercao_exit_1:
        erros.append(
            "Nenhum cenário deliberado de quebra de condição ou detecção de violação identificado."
        )

    return len(erros) == 0, erros


def auditar_gates(gates_dir: str = GATES_DIR) -> int:
    """Executa a auditoria em todos os scripts de gate no diretório."""
    print("=" * 72)
    print(" [GATE] G_PORTAO_PROVA_QUE_MORDE — Meta-Gate de Reprovação (Lei #13)")
    print("=" * 72)

    if not os.path.isdir(gates_dir):
        print(f"[ERRO] Diretório de gates não encontrado: {gates_dir}")
        return 1

    todos_arquivos = sorted(os.listdir(gates_dir))
    gates = [
        f for f in todos_arquivos
        if f.startswith("G_") and f.endswith(".py") and f != "G_PORTAO_PROVA_QUE_MORDE.py"
    ]

    if not gates:
        print("[AVISO] Nenhum script de Quality Gate (G_*.py) encontrado para auditar.")
        return 0

    erros_totais: Dict[str, List[str]] = {}
    conformes = []

    for gate_file in gates:
        test_file = encontrar_arquivo_teste(gate_file, gates_dir)
        if not test_file:
            erros_totais[gate_file] = [
                f"Arquivo de teste ausente. Esperado: test_{os.path.splitext(gate_file)[0].lower()}.py"
            ]
            continue

        valido, erros = auditar_teste_de_falha(test_file)
        if not valido:
            erros_totais[gate_file] = erros
        else:
            conformes.append(gate_file)

    # Exibição de Resultados
    for g in conformes:
        print(f"[OK] {g:<35} -> Teste de reprovação (exit 1) comprovado.")

    if erros_totais:
        print("\n" + "=" * 72)
        print(f" [FALHA] {len(erros_totais)} gate(s) sem teste de reprovação válido (Lei #13):")
        print("=" * 72)
        for g, errs in sorted(erros_totais.items()):
            print(f"\n  [VIOLAÇÃO] {g}:")
            for err in errs:
                print(f"    - {err}")
        print("\n" + "=" * 72)
        print(" REGRA CANÔNICA VIOLADA (Lei #13):")
        print(" Nenhum quality gate é aceito sem teste automatizado que deliberadamente")
        print(" quebre a condição resguardada e asserte exit 1.")
        print("=" * 72)
        return 1

    print("\n" + "=" * 72)
    print(f" [SUCESSO] 100% dos {len(gates)} Quality Gates provam que mordem (exit 1)!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(auditar_gates())
