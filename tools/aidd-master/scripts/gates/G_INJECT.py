#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE DETERMINÍSTICO DO INJETOR UNIVERSAL (G_INJECT)
=============================================================================
Valida a implementação completa do Injetor Universal de Componentes
(Skills, MCPs, Rules, Specs, Configs e Agents): contrato JSON Schema,
motor core (profiles_registry, detector_camada, materializador,
sincronizador_harness), integração CLI/IntentRouter, varredura AST
anti-stubs, suíte Pytest dedicada (100% verde) e a prova de fogo real
('CAPABILITIES.json' com ao menos um componente injetado).
"""

import ast
import json
import os
import subprocess
import sys
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


_ARQUIVOS_CORE = (
    "schema_injector_request.json",
    "profiles_registry.py",
    "detector_camada.py",
    "materializador.py",
    "sincronizador_harness.py",
)


class InjectGate:
    def __init__(self, root_dir: str = "."):
        self.root = os.path.abspath(root_dir)
        self.core_dir = os.path.join(self.root, "src", "core")
        self.errors = []
        self.checks_passed = 0

    def check(self, condition: bool, description: str, error_msg: str):
        if condition:
            print(f"  ✅ [PASS] {description}")
            self.checks_passed += 1
        else:
            print(f"  ❌ [FAIL] {description} ➔ {error_msg}")
            self.errors.append(f"{description}: {error_msg}")

    def _verificar_arquivos_core(self):
        for nome in _ARQUIVOS_CORE:
            caminho = os.path.join(self.core_dir, nome)
            self.check(
                os.path.isfile(caminho) and os.path.getsize(caminho) > 50,
                f"Motor Core do Injetor '{nome}'",
                f"Arquivo ausente ou vazio em {caminho}",
            )

    def _verificar_schema(self):
        caminho = os.path.join(self.core_dir, "schema_injector_request.json")
        if not os.path.isfile(caminho):
            self.check(False, "Contrato JSON Schema Draft 2020-12", "schema_injector_request.json ausente")
            return
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                schema = json.load(f)
            valido = (
                schema.get("$schema", "").endswith("2020-12/schema")
                and set(schema.get("required", [])) >= {"tipo", "nome", "descricao", "alvo_projeto"}
                and "camada_alvo" in schema.get("properties", {})
                and "conteudo" in schema.get("properties", {})
            )
            self.check(valido, "Contrato JSON Schema Draft 2020-12", "Schema não valida os 6 campos exigidos pela Fase 1")
        except (OSError, json.JSONDecodeError) as e:
            self.check(False, "Contrato JSON Schema Draft 2020-12", f"JSON corrompido: {e}")

    def _verificar_compilacao_e_anti_stub(self):
        for nome in _ARQUIVOS_CORE:
            if not nome.endswith(".py"):
                continue
            caminho = os.path.join(self.core_dir, nome)
            if not os.path.isfile(caminho):
                continue

            res = subprocess.run([sys.executable, "-m", "py_compile", caminho], capture_output=True, text=True)
            self.check(res.returncode == 0, f"Compilação sintática '{nome}'", res.stderr.strip()[:300] or "erro de sintaxe")

            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=caminho)
                stubs = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                            stubs.append(node.name)
                        elif (
                            len(node.body) == 1
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and node.body[0].value.value is Ellipsis
                        ):
                            stubs.append(node.name)
                self.check(len(stubs) == 0, f"Zero Stubs (AST) em '{nome}'", f"Funções vazias detectadas: {', '.join(stubs)}")
            except (OSError, SyntaxError) as e:
                self.check(False, f"Varredura AST em '{nome}'", str(e))

    def _verificar_integracao_cli(self):
        aidd_py = os.path.join(self.root, "scripts", "aidd.py")
        if os.path.isfile(aidd_py):
            with open(aidd_py, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.check(
                "def cmd_inject(" in conteudo and '"inject": cmd_inject' in conteudo,
                "Subcomando CLI 'aidd inject <tipo> <nome>'",
                "cmd_inject não encontrado ou não registrado no dispatcher de comandos",
            )
            self.check(
                "_tentar_injecao_por_linguagem_natural" in conteudo,
                "Ponte de Linguagem Natural (IntentRouter -> Injetor)",
                "Roteamento de frases PT-BR para o Injetor ausente em scripts/aidd.py",
            )
        else:
            self.check(False, "Subcomando CLI 'aidd inject <tipo> <nome>'", "scripts/aidd.py ausente")

        intent_router_py = os.path.join(self.core_dir, "intent_router.py")
        if os.path.isfile(intent_router_py):
            with open(intent_router_py, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.check(
                'action="inject"' in conteudo and "_INJECTED_AGENT_PATTERNS" in conteudo,
                "Padrões PT-BR de Injeção no IntentRouter",
                "Padrão action='inject' ou marcador _INJECTED_AGENT_PATTERNS ausente",
            )
        else:
            self.check(False, "Padrões PT-BR de Injeção no IntentRouter", "src/core/intent_router.py ausente")

    def _verificar_auto_carregamento_mcp(self):
        mcp_server_py = os.path.join(self.core_dir, "mcp_server.py")
        if os.path.isfile(mcp_server_py):
            with open(mcp_server_py, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.check(
                "def register_injected_tools(" in conteudo,
                "Auto-Carregamento de MCPs Injetados",
                "MCPServer.register_injected_tools() ausente em src/core/mcp_server.py",
            )
        else:
            self.check(False, "Auto-Carregamento de MCPs Injetados", "src/core/mcp_server.py ausente")

    def _executar_pytest_dedicado(self):
        teste = os.path.join(self.root, "tests", "unit", "test_injector_core.py")
        if not os.path.isfile(teste):
            self.check(False, "Suíte Pytest dedicada (100% verde)", "tests/unit/test_injector_core.py ausente")
            return

        env = os.environ.copy()
        src_path = os.path.join(self.root, "src")
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{self.core_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", teste],
            cwd=self.root, env=env, capture_output=True, text=True,
        )
        print(res.stdout[-2000:])
        if res.returncode != 0:
            print(res.stderr[-1000:])
        self.check(res.returncode == 0, "Suíte Pytest dedicada (100% verde, 0 skips)", f"pytest retornou exit code {res.returncode}")

    def _verificar_prova_de_fogo(self):
        capabilities_path = os.path.join(self.root, "CAPABILITIES.json")
        if not os.path.isfile(capabilities_path):
            self.check(False, "Prova de Fogo (CAPABILITIES.json)", "Nenhum componente foi injetado no repositório ainda")
            return
        try:
            with open(capabilities_path, "r", encoding="utf-8") as f:
                catalogo = json.load(f)
            tem_skill = len(catalogo.get("skill", [])) > 0
            tem_mcp = len(catalogo.get("mcp", [])) > 0
            self.check(
                tem_skill and tem_mcp,
                "Prova de Fogo: 1 skill + 1 mcp reais injetados",
                f"CAPABILITIES.json não contém skill+mcp reais (skill={len(catalogo.get('skill', []))}, mcp={len(catalogo.get('mcp', []))})",
            )
        except (OSError, json.JSONDecodeError) as e:
            self.check(False, "Prova de Fogo (CAPABILITIES.json)", f"JSON corrompido: {e}")

    def run(self) -> int:
        print("=" * 80)
        print("🧩 [GATE G_INJECT v5.1] Auditoria do Injetor Universal de Componentes")
        print(f"📁 Diretório Alvo: {self.root}")
        print("=" * 80)

        self._verificar_arquivos_core()
        self._verificar_schema()
        self._verificar_compilacao_e_anti_stub()
        self._verificar_integracao_cli()
        self._verificar_auto_carregamento_mcp()
        self._executar_pytest_dedicado()
        self._verificar_prova_de_fogo()

        print("\n" + "=" * 80)
        print("📊 RESUMO DO GATE G_INJECT:")
        print(f"   - Validações Aprovadas: {self.checks_passed}")
        print(f"   - Falhas: {len(self.errors)}")
        print("=" * 80)

        if self.errors:
            print("❌ [BLOQUEADO]: Injetor Universal não está 100% homologado.")
            return 1

        print("🏆 [APROVADO]: Injetor Universal de Componentes 100% homologado (exit 0)!")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="G_INJECT — Gate de Validação do Injetor Universal")
    parser.add_argument("--dir", default=".", help="Diretório raiz do projeto")
    args, _ = parser.parse_known_args()

    gate = InjectGate(args.dir)
    sys.exit(gate.run())
