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

Critérios determinísticos validados por este meta-gate para cada gate do MAPA-GATES.json:
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
from concurrent.futures import ThreadPoolExecutor
import os
import re
import subprocess
import sys
from typing import Dict, List, Tuple

from pathlib import Path as _Path
ROOT_DIR = str(next((p.parent for p in _Path(__file__).resolve().parents if p.name == "modulos"), _Path(__file__).resolve().parent.parent))  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
GATES_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from scripts import mapa_gates  # noqa: E402  (lista de gates vem de MAPA-GATES.json)

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


PASTAS_GATES_VSA = [
    os.path.join(ROOT_DIR, "modulos", "01-governanca-e-qualidade", "gates"),
    os.path.join(ROOT_DIR, "modulos", "02-triade-motores", "fluxo-01-pure", "gates"),
    os.path.join(ROOT_DIR, "modulos", "02-triade-motores", "fluxo-02-open", "gates"),
    os.path.join(ROOT_DIR, "modulos", "02-triade-motores", "fluxo-03-freedom", "gates"),
    os.path.join(ROOT_DIR, "modulos", "03-plataforma-e-entrega", "gates"),
    os.path.join(ROOT_DIR, "modulos", "04-nucleo-compartilhado", "gates"),
]


def encontrar_arquivo_teste(gate_file: str, gates_dir: str) -> str | None:
    """Mapeia G_NOME_DO_GATE.py para test_g_nome_do_gate.py em gates_dir ou nas pastas canônicas VSA."""
    base = os.path.splitext(gate_file)[0]
    expected_name = f"test_{base.lower()}.py"
    path = os.path.join(gates_dir, expected_name)
    if os.path.isfile(path):
        return path
    for p in PASTAS_GATES_VSA:
        candidato = os.path.join(p, expected_name)
        if os.path.isfile(candidato):
            return candidato
    return None


def executar_suite_teste(test_path: str) -> Tuple[bool, str]:
    """Executa a suíte de teste usando pytest e valida saída bem-sucedida (exit 0 do pytest)."""
    test_dir = os.path.dirname(os.path.abspath(test_path))
    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{test_dir}{os.pathsep}{ROOT_DIR}" + (f"{os.pathsep}{existing_pp}" if existing_pp else "")

    cmd = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", test_path]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=ROOT_DIR,
            # 300s: modulos/03-plataforma-e-entrega/gates/test_g_infra_compose.py roda Checkov real e leva ~224s nesta máquina (medido 2026-09-30).
            timeout=300,
        )
        if res.returncode == 0:
            return True, ""
        detalhe = (res.stdout.strip() or res.stderr.strip()).splitlines()
        resumo_falha = "\n".join(detalhe[-5:]) if detalhe else f"retorno={res.returncode}"
        return False, f"Falha na execução em runtime (código {res.returncode}):\n{resumo_falha}"
    except subprocess.TimeoutExpired:
        return False, "Execução da suíte de teste excedeu o timeout de 300s."
    except Exception as e:
        return False, f"Erro ao disparar execução do teste: {e}"


def auditar_teste_de_falha(test_path: str, executar: bool = True) -> Tuple[bool, List[str]]:
    """Verifica se o arquivo de teste contém asserção de exit 1 e executa com sucesso."""
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

    # 4. Execução real do teste (ISSUE-0019)
    if not erros and executar:
        sucesso_exec, motivo_exec = executar_suite_teste(test_path)
        if not sucesso_exec:
            erros.append(
                f"Teste contém padrão de exit 1 mas falhou na execução real (Lei #13 / ISSUE-0019):\n{motivo_exec}"
            )

    return len(erros) == 0, erros


def _gates_a_auditar(gates_dir: str | None, raiz: str) -> Dict[str, str]:
    """{arquivo: pasta}. Com gates_dir, só aquela pasta; sem, todos os gates de MAPA-GATES.json."""
    if gates_dir is not None:
        arquivos = {f: gates_dir for f in os.listdir(gates_dir)}
    else:
        arquivos = {p.name: str(p.parent) for p in mapa_gates.caminhos(raiz)}
    return {f: d for f, d in arquivos.items()
            if f.startswith("G_") and f.endswith(".py") and f != "G_PORTAO_PROVA_QUE_MORDE.py"}


def auditar_gates(gates_dir: str | None = None, raiz: str = ROOT_DIR) -> int:
    """Audita os gates de uma pasta (gates_dir) ou, por padrão, todos os do mapa de donos."""
    print("=" * 72)
    print(" [GATE] G_PORTAO_PROVA_QUE_MORDE — Meta-Gate de Reprovação (Lei #13)")
    print("=" * 72)

    if gates_dir is not None and not os.path.isdir(gates_dir):
        print(f"[ERRO] Diretório de gates não encontrado: {gates_dir}")
        return 1
    try:
        pasta_de = _gates_a_auditar(gates_dir, raiz)
    except (OSError, KeyError, ValueError) as erro:
        print(f"[ERRO] MAPA-GATES.json ilegível: {erro!r}")
        return 1
    gates = sorted(pasta_de)

    if not gates:
        print("[AVISO] Nenhum script de Quality Gate (G_*.py) encontrado para auditar.")
        return 0

    erros_totais: Dict[str, List[str]] = {}
    conformes = []

    def processar_gate(gate_file: str) -> Tuple[str, bool, List[str]]:
        test_file = encontrar_arquivo_teste(gate_file, pasta_de[gate_file])
        if not test_file:
            return gate_file, False, [
                f"Arquivo de teste ausente. Esperado: test_{os.path.splitext(gate_file)[0].lower()}.py"
            ]
        valido, errs = auditar_teste_de_falha(test_file, executar=True)
        return gate_file, valido, errs

    max_workers = min(os.cpu_count() or 4, 6) if len(gates) > 3 else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        resultados = list(executor.map(processar_gate, gates))

    for gate_file, valido, errs in resultados:
        if not valido:
            test_file = encontrar_arquivo_teste(gate_file, pasta_de[gate_file])
            if test_file:
                valido_retry, errs_retry = auditar_teste_de_falha(test_file, executar=True)
                if valido_retry:
                    conformes.append(gate_file)
                    continue
                erros_totais[gate_file] = errs_retry
            else:
                erros_totais[gate_file] = errs
        else:
            conformes.append(gate_file)

    # Exibição de Resultados
    for g in conformes:
        print(f"[OK] {g:<35} -> Teste de reprovação (exit 1) executado e comprovado.")

    if erros_totais:
        print("\n" + "=" * 72)
        print(f" [FALHA] {len(erros_totais)} gate(s) com teste ausente, inválido ou falho na execução (Lei #13):")
        print("=" * 72)
        for g, errs in sorted(erros_totais.items()):
            print(f"\n  [VIOLAÇÃO] {g}:")
            for err in errs:
                print(f"    - {err}")
        print("\n" + "=" * 72)
        print(" REGRA CANÔNICA VIOLADA (Lei #13):")
        print(" Nenhum quality gate é aceito sem teste automatizado que deliberadamente")
        print(" quebre a condição resguardada, asserte exit 1 e execute com sucesso em runtime.")
        print("=" * 72)
        return 1

    print("\n" + "=" * 72)
    print(f" [SUCESSO] {len(conformes)}/{len(gates)} Quality Gates verificados:")
    print("           Suítes de teste de reprovação executadas e aprovadas com sucesso em runtime.")
    print("=" * 72)
    print(" [LIMITE METROLÓGICO — LEI #8 / ISSUE-0019]:")
    print("   A execução automatizada comprova que os testes de reprovação rodam e passam.")
    print("   A verificação determinística de que o cenário de teste quebra estritamente a")
    print("   invariante sob guarda (e não um erro colateral genérico) requer auditoria")
    print("   semântica / teste de mutação (ISSUE-0011 escopo 3), não sendo afirmada como")
    print("   cobertura total de 100% da integridade da invariante.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--raiz":
        sys.exit(auditar_gates(raiz=sys.argv[2]))
    sys.exit(auditar_gates())
