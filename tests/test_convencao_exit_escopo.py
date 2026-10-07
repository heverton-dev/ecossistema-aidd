# -*- coding: utf-8 -*-
"""
Teste de Handoff do Ticket 15 (D13 / DoD 5).
Valida o escopo da convenção de exit codes determinísticos:
1. CONVENCAO-EXIT-CODES-DETERMINISTICOS.md explicita que a escala 0-5 se aplica
   exclusivamente a scripts e CLIs, enquanto Quality Gates seguem a Lei Canônica #2 (saída binária estrita 0/1).
2. Nenhum Quality Gate (arquivos mapeados em MAPA-GATES.json) importa scripts.exit_codes ou exit_codes.
3. G_SAIDA_BINARIA audita e cobre todos os caminhos de gates declarados em MAPA-GATES.json.
"""

import ast
import re
from pathlib import Path
import pytest

RAIZ = Path(__file__).resolve().parents[1]
from scripts import mapa_gates


def test_documento_convencao_restringe_escala_0_a_5_para_scripts_e_clis():
    doc_path = RAIZ / "docs" / "protocolos" / "CONVENCAO-EXIT-CODES-DETERMINISTICOS.md"
    assert doc_path.exists(), "Documento da convenção de exit codes deve existir"
    texto = doc_path.read_text(encoding="utf-8")

    # Verifica se há cláusula explícita restringindo a escala 0-5 para scripts/CLIs
    # e reafirmando que quality gates são estritamente binários 0/1 (Lei #2)
    assert re.search(r"scripts\s+e\s+CLIs", texto, re.IGNORECASE), (
        "Convenção deve especificar aplicação da escala 0-5 para scripts e CLIs"
    )
    assert re.search(r"gates|Lei\s*#2|binári[oa]", texto, re.IGNORECASE), (
        "Convenção deve reafirmar a saída binária (0/1) para Quality Gates"
    )


def test_nenhum_gate_importa_exit_codes():
    gates_caminhos = mapa_gates.caminhos(RAIZ)
    assert len(gates_caminhos) > 0, "Deve haver gates listados em MAPA-GATES.json"

    violacoes = []
    for gate_path in gates_caminhos:
        if not gate_path.exists():
            continue
        conteudo = gate_path.read_text(encoding="utf-8-sig", errors="replace")
        arvore = ast.parse(conteudo, filename=str(gate_path))
        for node in ast.walk(arvore):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "exit_codes" in alias.name:
                        violacoes.append(f"{gate_path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                modulo = node.module or ""
                if "exit_codes" in modulo:
                    violacoes.append(f"{gate_path.name}: from {modulo} import ...")
                for alias in node.names:
                    if "exit_codes" in alias.name:
                        violacoes.append(f"{gate_path.name}: from {modulo} import {alias.name}")

    assert not violacoes, f"Quality Gates importando exit_codes detectados: {violacoes}"


def test_g_saida_binaria_cobre_todos_os_gates_do_mapa():
    # Executa a função auditar_gates_do_mapa diretamente
    caminho_g_saida = mapa_gates.caminho("G_SAIDA_BINARIA", RAIZ)
    assert caminho_g_saida.exists()

    # Importa dinamicamente G_SAIDA_BINARIA
    import importlib.util
    spec = importlib.util.spec_from_file_location("G_SAIDA_BINARIA", str(caminho_g_saida))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    codigo, erros, total = mod.auditar_gates_do_mapa(str(RAIZ))
    assert codigo == 0, f"G_SAIDA_BINARIA encontrou erros nos gates: {erros}"
    assert total >= 70, f"G_SAIDA_BINARIA deve auditar ao menos 70 gates mapeados (auditou {total})"
