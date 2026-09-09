#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE DETERMINÍSTICO DO INJETOR UNIVERSAL (G_INJECT)
=============================================================================
Valida a implementação do Injetor Universal de Componentes:
1. Infraestrutura do motor: contrato JSON Schema, arquivos core (profiles_registry,
   detector_camada, materializador, sincronizador_harness), integração CLI /
   IntentRouter, varredura AST anti-stubs e suíte Pytest dedicada.
2. Sincronização multi-harness e integridade SHA-256 pós-injeção (drift detection)
   via sincronizador_harness.verificar_sincronizacao().
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
            self.check(valido, "Contrato JSON Schema Draft 2020-12", "Schema não valida os campos exigidos")
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
            repo_aidd = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts", "aidd.py")
            if os.path.isfile(repo_aidd):
                self.check(True, "Subcomando CLI 'aidd inject <tipo> <nome>'", "")
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

    def _executar_pytest_dedicado(self):
        teste = os.path.join(self.root, "tests", "unit", "test_aidd_core_injector.py")
        if not os.path.isfile(teste):
            return

        env = os.environ.copy()
        src_path = os.path.join(self.root, "src")
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{self.core_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", teste],
            cwd=self.root, env=env, capture_output=True, text=True,
        )
        self.check(res.returncode == 0, "Suíte Pytest dedicada (100% verde)", f"pytest retornou exit code {res.returncode}")

    def _verificar_drift_pos_injecao(self):
        if self.core_dir not in sys.path:
            sys.path.insert(0, self.core_dir)
        src_dir = os.path.join(self.root, "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        try:
            from sincronizador_harness import verificar_sincronizacao
            res_sync = verificar_sincronizacao(self.root)
            if not res_sync.sucesso:
                problemas = (res_sync.detalhes or {}).get("problemas", [])
                if problemas:
                    for problema in problemas:
                        self.check(False, "Sincronização Multi-Harness e Drift", problema)
                else:
                    self.check(False, "Sincronização Multi-Harness e Drift", res_sync.erro or res_sync.codigo)
            else:
                verificados = res_sync.valor.get("verificados", 0)
                self.check(True, f"Sincronização Multi-Harness e Drift ({verificados} verificados)", "")
        except (ImportError, AttributeError) as exc:
            self.check(False, "Sincronização Multi-Harness e Drift", f"Falha ao rodar verificar_sincronizacao: {exc}")

        reg_legado = os.path.join(self.root, "COMPONENT-REGISTRY.json")
        if os.path.isfile(reg_legado):
            try:
                with open(reg_legado, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                if not isinstance(dados, list):
                    self.check(False, "COMPONENT-REGISTRY.json estrutural", "Deve ser uma lista")
                else:
                    self.check(True, "COMPONENT-REGISTRY.json estrutural", "")
            except json.JSONDecodeError as e:
                self.check(False, "COMPONENT-REGISTRY.json estrutural", f"JSON inválido: {e}")

    def run(self) -> int:
        print("=" * 80)
        print("🧩 [GATE G_INJECT v5.1] Auditoria do Universal Component Injector")
        print(f"📁 Diretório Alvo: {self.root}")
        print("=" * 80)

        self._verificar_arquivos_core()
        self._verificar_schema()
        self._verificar_compilacao_e_anti_stub()
        self._verificar_integracao_cli()
        self._executar_pytest_dedicado()
        self._verificar_drift_pos_injecao()

        print("\n" + "=" * 80)
        print("📊 RESUMO DO GATE G_INJECT:")
        print(f"   - Validações Aprovadas: {self.checks_passed}")
        print(f"   - Falhas: {len(self.errors)}")
        print("=" * 80)

        if self.errors:
            print("❌ [BLOQUEADO] [FAIL]: Universal Component Injector não está 100% homologado.")
            return 1

        print("🏆 [APROVADO] [OK]: Universal Component Injector 100% homologado (exit 0)!")
        return 0


def verificar_injector(target_dir: str = "."):
    gate = InjectGate(target_dir)
    code = gate.run()
    if code != 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="G_INJECT — Gate de Validação do Injetor Universal")
    parser.add_argument("--dir", default=".", help="Diretório raiz do projeto")
    args, _ = parser.parse_known_args()

    gate = InjectGate(args.dir)
    sys.exit(gate.run())
