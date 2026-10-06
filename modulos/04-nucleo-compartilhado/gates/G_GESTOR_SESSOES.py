#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_GESTOR_SESSOES (Leis Canônicas #1, #3, #13)
=============================================================================
Valida a integridade determinística do subsistema de rastreamento de sessões:
  1. scripts/gestor_sessoes.py deve existir e compilar via AST sem erros.
  2. Deve expor as funções de contrato: registrar_sessao, listar_sessoes,
     buscar_sessao, carregar_historico, salvar_historico.
  3. Deve executar com sucesso na CLI registrando em ambiente isolado.
  4. Deve rejeitar IDs vazios ou inválidos com código binário de erro (1).

Saída:
  exit 0 = Contrato do gestor de sessões 100% íntegro.
  exit 1 = Falha ou ausência de conformidade do gestor de sessões.
=============================================================================
"""

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(ROOT_DIR, "scripts", "gestor_sessoes.py")

FUNCOES_OBRIGATORIAS = [
    "registrar_sessao",
    "listar_sessoes",
    "buscar_sessao",
    "carregar_historico",
    "salvar_historico",
]


def verificar_ast(caminho: str) -> bool:
    if not os.path.exists(caminho):
        print(f"[FALHA] Arquivo não encontrado: {caminho}")
        return False

    with open(caminho, "r", encoding="utf-8") as f:
        codigo = f.read()

    try:
        arvore = ast.parse(codigo, filename=caminho)
    except SyntaxError as e:
        print(f"[FALHA] Erro de sintaxe em {caminho}: {e}")
        return False

    nomes_funcoes = {
        node.name
        for node in ast.walk(arvore)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    faltantes = [f for f in FUNCOES_OBRIGATORIAS if f not in nomes_funcoes]
    if faltantes:
        print(f"[FALHA] Funções obrigatórias ausentes em {caminho}: {faltantes}")
        return False

    return True


def verificar_execucao_cli() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_json = Path(tmpdir) / "teste_sessoes.json"
        
        # Teste 1: registrar com sucesso
        cmd_reg = [
            sys.executable,
            SCRIPT_PATH,
            "registrar",
            "--id", "gate-test-id-001",
            "--harness", "gate-tester",
            "--modelo", "test-model",
            "--titulo", "Teste Automatizado do Gate",
            "--arquivo", str(tmp_json),
            "--no-md"
        ]
        res_reg = subprocess.run(cmd_reg, capture_output=True, text=True)
        if res_reg.returncode != 0:
            print(f"[FALHA] Falha na execução CLI do registrar: {res_reg.stderr}")
            return False

        # Teste 2: listar
        cmd_lis = [
            sys.executable,
            SCRIPT_PATH,
            "listar",
            "--arquivo", str(tmp_json),
            "--json"
        ]
        res_lis = subprocess.run(cmd_lis, capture_output=True, text=True)
        if res_lis.returncode != 0 or "gate-test-id-001" not in res_lis.stdout:
            print(f"[FALHA] Falha na listagem CLI: {res_lis.stderr}")
            return False

        # Teste 3: rejeição de ID vazio (deve falhar com returncode != 0)
        cmd_inv = [
            sys.executable,
            SCRIPT_PATH,
            "registrar",
            "--id", "   ",
            "--arquivo", str(tmp_json)
        ]
        res_inv = subprocess.run(cmd_inv, capture_output=True, text=True)
        if res_inv.returncode == 0:
            print("[FALHA] Script aceitou ID vazio indevidamente (esperava returncode != 0).")
            return False

    return True


def main() -> int:
    print("=" * 70)
    print("  AUDITORIA DE QUALIDADE: G_GESTOR_SESSOES (Leis #1, #3, #13)")
    print("=" * 70)

    if not verificar_ast(SCRIPT_PATH):
        print("\n[RESULTADO] REPROVADO (Falha estrutural AST)")
        return 1

    if not verificar_execucao_cli():
        print("\n[RESULTADO] REPROVADO (Falha funcional CLI)")
        return 1

    print("\n[RESULTADO] APROVADO — Gestor de sessões 100% conforme.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
