#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE DETERMINÍSTICO DE ESTRUTURA (G_ESTRUTURA)
=============================================================================
Valida layout do projeto, presença do Shared Kernel, módulos desacoplados,
manifesto estruturado, AST Anti-Acoplamento e Zero Connection Leak.
"""

import os
import sys
import json
import argparse
import ast

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class StructureGate:
    def __init__(self, root_dir: str = "."):
        self.root = os.path.abspath(root_dir)
        self.errors = []
        self.warnings = []
        self.checks_passed = 0

    def check(self, condition: bool, description: str, error_msg: str):
        if condition:
            print(f"  ✅ [PASS] {description}")
            self.checks_passed += 1
        else:
            print(f"  ❌ [FAIL] {description} ➔ {error_msg}")
            self.errors.append(f"{description}: {error_msg}")

    def warn(self, condition: bool, description: str, warn_msg: str):
        if condition:
            print(f"  ✅ [PASS] {description}")
            self.checks_passed += 1
        else:
            print(f"  ⚠️ [WARN] {description} ➔ {warn_msg}")
            self.warnings.append(f"{description}: {warn_msg}")

    def run(self) -> int:
        print("=" * 80)
        print("🏗️  [GATE G_ESTRUTURA v5.1] Auditoria de Arquitetura e Layout do Projeto")
        print(f"📁 Diretório Alvo: {self.root}")
        print("=" * 80)

        # 1. Diretórios Principais
        src_dir = os.path.join(self.root, "src")
        core_dir = os.path.join(src_dir, "core")
        modules_dir = os.path.join(src_dir, "modules")
        static_dir = os.path.join(src_dir, "static")
        tests_dir = os.path.join(self.root, "tests", "unit")
        scripts_gates_dir = os.path.join(self.root, "scripts", "gates")

        self.check(os.path.isdir(src_dir), "Diretório 'src/'", "Pasta raiz de código-fonte não encontrada")
        self.check(os.path.isdir(core_dir), "Shared Kernel 'src/core/'", "Pasta de core kernel não encontrada")
        self.check(os.path.isdir(modules_dir), "Fatias Verticais 'src/modules/'", "Pasta de módulos não encontrada")
        self.check(os.path.isdir(static_dir), "Assets e UI 'src/static/'", "Pasta estática de front-end não encontrada")
        self.check(os.path.isdir(tests_dir), "Suíte de Testes 'tests/unit/'", "Pasta de testes unitários não encontrada")
        self.check(os.path.isdir(scripts_gates_dir), "Quality Gates 'scripts/gates/'", "Pasta de gates mecânicos não encontrada")

        # 2. Shared Kernel Core Files
        core_files = ["database.py", "events.py", "openapi.py", "security.py", "webhooks.py", "mcp_server.py"]
        for cf in core_files:
            cf_path = os.path.join(core_dir, cf)
            self.check(
                os.path.isfile(cf_path) and os.path.getsize(cf_path) > 50,
                f"Core Kernel '{cf}'",
                f"Arquivo ausente ou vazio em {cf_path}"
            )

        # 3. Módulos / Fatias Verticais
        mod_dirs = []
        if os.path.isdir(modules_dir):
            mod_dirs = [
                d for d in os.listdir(modules_dir)
                if os.path.isdir(os.path.join(modules_dir, d)) and not d.startswith("__")
            ]
            self.check(
                len(mod_dirs) > 0,
                f"Detecção de Fatias Verticais ({len(mod_dirs)} módulo(s) ativo(s))",
                f"Nenhum módulo encontrado em {modules_dir}"
            )

            for m in mod_dirs:
                m_path = os.path.join(modules_dir, m)
                for req_f in ["__init__.py", "models.py", "services.py", "routes.py"]:
                    f_path = os.path.join(m_path, req_f)
                    self.check(
                        os.path.isfile(f_path),
                        f"Módulo '{m}' -> {req_f}",
                        f"Arquivo obrigatório {req_f} ausente no módulo {m}"
                    )

        # 4. Manifestos Estruturais
        plano_path = os.path.join(self.root, "PLANO-EXECUCAO-ESTRUTURADO.json")
        if os.path.isfile(plano_path):
            try:
                with open(plano_path, "r", encoding="utf-8") as f:
                    plano_data = json.load(f)
                has_proj = "projeto" in plano_data and "nome" in plano_data["projeto"]
                has_mods = "modulos" in plano_data or "fases" in plano_data
                self.check(has_proj and has_mods, "Manifesto 'PLANO-EXECUCAO-ESTRUTURADO.json'", "JSON sem campos 'projeto' e 'modulos'")
            except Exception as e:
                self.check(False, "Manifesto 'PLANO-EXECUCAO-ESTRUTURADO.json'", f"JSON corrompido: {e}")
        else:
            self.check(False, "Manifesto 'PLANO-EXECUCAO-ESTRUTURADO.json'", "Arquivo de plano estruturado ausente na raiz")

        req_path = os.path.join(self.root, "requirements.txt")
        self.check(
            os.path.isfile(req_path) and os.path.getsize(req_path) > 0,
            "Manifesto 'requirements.txt'",
            "Arquivo requirements.txt ausente ou vazio"
        )

        # 5. Arquivo de Entrada do Servidor
        server_path = os.path.join(src_dir, "server.py")
        self.check(
            os.path.isfile(server_path) and os.path.getsize(server_path) > 100,
            "Servidor Monolítico Modular 'src/server.py'",
            "Servidor ausente ou vazio"
        )

        # 6. Testes Unitários Presentes
        if os.path.isdir(tests_dir):
            test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
            self.check(
                len(test_files) > 0,
                f"Arquivos de Teste em tests/unit/ ({len(test_files)} encontrados)",
                "Nenhum arquivo de teste 'test_*.py' encontrado"
            )

        # 7. Linter AST Anti-Acoplamento Cross-Module & Zero Connection Leak
        coupling_violations = []
        connection_leaks = []
        if os.path.isdir(modules_dir) and mod_dirs:
            for m in mod_dirs:
                mod_path = os.path.join(modules_dir, m)
                for root_f, _, files in os.walk(mod_path):
                    for f in files:
                        if f.endswith(".py"):
                            f_path = os.path.join(root_f, f)
                            try:
                                with open(f_path, "r", encoding="utf-8", errors="ignore") as py_f:
                                    content = py_f.read()
                                    tree = ast.parse(content, filename=f_path)
                                    for node in ast.walk(tree):
                                        if isinstance(node, ast.Import):
                                            for alias in node.names:
                                                for other in mod_dirs:
                                                    if other != m and alias.name.startswith(f"modules.{other}"):
                                                        coupling_violations.append(f"{m}/{f} -> {alias.name}")
                                        elif isinstance(node, ast.ImportFrom):
                                            if node.module:
                                                for other in mod_dirs:
                                                    if other != m and (node.module == f"modules.{other}" or node.module.startswith(f"modules.{other}.")):
                                                        coupling_violations.append(f"{m}/{f} -> {node.module}")

                                    if "sqlite3.connect(" in content and "with " not in content and "def " in content and "init_schema" not in content:
                                        connection_leaks.append(f"{m}/{f}")
                            except Exception:
                                pass

        self.check(
            len(coupling_violations) == 0,
            "Linter AST Anti-Acoplamento Cross-Module (Zero Acoplamento Direto)",
            f"Violações de import detectadas: {', '.join(coupling_violations)}"
        )
        self.check(
            len(connection_leaks) == 0,
            "Scanner Anti-Vazamento de Conexões SQLite (Zero Connection Leak)",
            f"Conexões sem context manager detectadas: {', '.join(connection_leaks)}"
        )

        print("\n" + "=" * 80)
        print(f"📊 RESUMO DO GATE G_ESTRUTURA:")
        print(f"   - Validações Aprovadas: {self.checks_passed}")
        print(f"   - Falhas Estruturais:   {len(self.errors)}")
        print(f"   - Alertas:              {len(self.warnings)}")
        print("=" * 80)

        if self.errors:
            print("❌ [BLOQUEADO]: Estrutura do projeto não atende aos requisitos AIDD v5.1 Enterprise.")
            return 1

        print("🏆 [APROVADO]: Layout estrutural 100% em conformidade com Clean Architecture Modular!")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="G_ESTRUTURA — Gate de Validação Estrutural")
    parser.add_argument("--dir", default=".", help="Diretório raiz do projeto")
    args = parser.parse_args()

    gate = StructureGate(args.dir)
    sys.exit(gate.run())
