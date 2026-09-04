#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE DETERMINÍSTICO DE ARQUITETURA (G_ARQUITETURA)
=============================================================================
Linter AST de Bounded Context que bloqueia imports diretos entre fatias
verticais (módulos). Cada módulo em src/modules/ é um Bounded Context
isolado — só pode importar de core.* ou comunicar via EventBus.

Regras:
  1. modules.<A> NÃO pode importar de modules.<B> (A != B)
  2. Imports de core.* são permitidos (Shared Kernel)
  3. Imports locais (.) dentro do próprio módulo são permitidos
  4. Qualquer violação gera FAIL com file:line detalhado
"""

import os
import sys
import ast
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class ArchitectureGate:
    def __init__(self, root_dir: str = "."):
        self.root = os.path.abspath(root_dir)
        self.src_dir = os.path.join(self.root, "src")
        self.modules_dir = os.path.join(self.src_dir, "modules")
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

    def log(self, status: str, layer: str, test_name: str, detail: str = ""):
        symbol = "✅ [PASS]" if status == "PASS" else ("❌ [FAIL]" if status == "FAIL" else "⚠️ [WARN]")
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.warnings += 1

        msg = f"{symbol} [{layer}] {test_name}"
        if detail:
            msg += f" ➔ {detail}"
        print(msg)
        self.results.append({"status": status, "layer": layer, "test": test_name, "detail": detail})

    def _discover_modules(self) -> list:
        """Descobre todos os módulos (fatias verticais) em src/modules/."""
        if not os.path.isdir(self.modules_dir):
            return []
        return [
            d for d in os.listdir(self.modules_dir)
            if os.path.isdir(os.path.join(self.modules_dir, d))
            and not d.startswith("__")
        ]

    def _get_module_name(self, filepath: str, module_names: list) -> str | None:
        """Retorna o nome do módulo ao qual o arquivo pertence, ou None."""
        rel = os.path.relpath(filepath, self.modules_dir)
        parts = rel.split(os.sep)
        if parts and parts[0] in module_names:
            return parts[0]
        return None

    def _is_cross_module_import(self, import_module: str, current_module: str, module_names: list) -> bool:
        """
        Verifica se o import é cross-module (violação).
        Retorna True se modules.<outro> está sendo importado.
        """
        if not import_module:
            return False

        # Imports de core.* são permitidos (Shared Kernel)
        if import_module.startswith("core") or import_module.startswith("core."):
            return False

        # Imports de modules.<mesmo_modulo> são permitidos
        if import_module == f"modules.{current_module}":
            return False
        if import_module.startswith(f"modules.{current_module}."):
            return False

        # Imports de modules.<outro_modulo> são VIOLAÇÃO
        for other in module_names:
            if other != current_module:
                if import_module == f"modules.{other}" or import_module.startswith(f"modules.{other}."):
                    return True

        return False

    def _scan_file(self, filepath: str, current_module: str, module_names: list) -> list:
        """Escaneia um arquivo .py com AST e retorna violações encontradas."""
        violations = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except (SyntaxError, UnicodeDecodeError) as e:
            self.log("WARN", "AST Parse", f"Falha ao parsear {os.path.basename(filepath)}", str(e))
            return violations

        rel_path = os.path.relpath(filepath, self.root)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if self._is_cross_module_import(alias.name, current_module, module_names):
                        violations.append((rel_path, node.lineno, alias.name))

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                # Relative imports (from . import X) são sempre intra-módulo
                if node.level and node.level > 0:
                    continue
                if self._is_cross_module_import(module_name, current_module, module_names):
                    violations.append((rel_path, node.lineno, module_name))

        return violations

    def run_all_checks(self) -> int:
        print("=" * 80)
        print("🏛️  [GATE G_ARQUITETURA v5.1] Linter AST de Bounded Context")
        print(f"📁 Diretório Alvo: {self.root}")
        print("=" * 80)

        # 1. Verificar se src/modules existe
        if not os.path.isdir(self.modules_dir):
            self.log("FAIL", "Estrutura", "Diretório src/modules/", "Não encontrado — impossível validar arquitetura")
            self._print_report()
            return 1

        # 2. Descobrir módulos
        module_names = self._discover_modules()
        if not module_names:
            self.log("WARN", "Estrutura", "Módulos em src/modules/", "Nenhum módulo encontrado — nada a validar")
            self._print_report()
            return 0

        self.log("PASS", "Estrutura", f"Módulos detectados ({len(module_names)})", ", ".join(sorted(module_names)))

        # 3. Verificar EventBus em core/events.py
        events_path = os.path.join(self.src_dir, "core", "events.py")
        if os.path.isfile(events_path):
            self.log("PASS", "EventBus", "core/events.py presente", "Comunicação inter-módulo via EventBus disponível")
        else:
            self.log("WARN", "EventBus", "core/events.py", "Não encontrado — EventBus pode não estar configurado")

        # 4. Escanear cada módulo em busca de imports cross-module
        all_violations = []
        files_scanned = 0

        for mod in sorted(module_names):
            mod_path = os.path.join(self.modules_dir, mod)
            mod_violations = []

            for root_dir, _, files in os.walk(mod_path):
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(root_dir, fname)
                    files_scanned += 1
                    violations = self._scan_file(fpath, mod, module_names)
                    mod_violations.extend(violations)

            if mod_violations:
                for filepath, lineno, target in mod_violations:
                    self.log(
                        "FAIL", "Bounded Context",
                        f"Import cross-module em {filepath}:{lineno}",
                        f"'{mod}' importa de '{target}' (violação de Bounded Context)"
                    )
                all_violations.extend(mod_violations)
            else:
                self.log("PASS", "Bounded Context", f"Módulo '{mod}' isolado", "Zero imports cross-module")

        # 5. Verificar se todos os módulos usam EventBus (opcional/warn)
        for mod in sorted(module_names):
            mod_path = os.path.join(self.modules_dir, mod)
            services_path = os.path.join(mod_path, "services.py")
            if os.path.isfile(services_path):
                try:
                    with open(services_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if "EventBus" in content or "event_bus" in content or "events" in content:
                        self.log("PASS", "EventBus Integration", f"Módulo '{mod}' usa EventBus", "Comunicação desacoplada confirmada")
                    else:
                        self.log("WARN", "EventBus Integration", f"Módulo '{mod}' sem EventBus", "Recomenda-se usar EventBus para comunicação inter-módulo")
                except Exception:
                    pass

        # 6. Resumo de arquivos escaneados
        self.log("PASS", "Cobertura", f"Arquivos .py escaneados", f"{files_scanned} arquivos analisados via AST")

        self._print_report()

        if all_violations:
            return 1
        return 0

    def _print_report(self):
        print("\n" + "=" * 80)
        total = self.passed + self.failed + self.warnings
        print(f"📊 RESULTADO FINAL DO GATE DE ARQUITETURA AIDD v5.1:")
        print(f"   - Testes Executados: {total}")
        print(f"   - Aprovados (PASS):  {self.passed}")
        print(f"   - Falhas (FAIL):     {self.failed}")
        print(f"   - Alertas (WARN):    {self.warnings}")
        print("=" * 80)

        if self.failed == 0:
            print("🏆 [CERTIFICAÇÃO CONCEDIDA]: Arquitetura de Bounded Context 100% conforme!")
        else:
            print("❌ [BLOQUEADO]: Violações de Bounded Context detectadas — módulos acoplados diretamente.")
            print("   Corrija os imports para usar core.* ou EventBus como intermediário.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="G_ARQUITETURA — Gate de Arquitetura Bounded Context")
    parser.add_argument("--dir", default=".", help="Diretório raiz do projeto")
    args = parser.parse_args()

    gate = ArchitectureGate(args.dir)
    sys.exit(gate.run_all_checks())
