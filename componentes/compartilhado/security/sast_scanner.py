# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — COMPONENTE COMPARTILHADO: SAST SCANNER DETERMINÍSTICO
=============================================================================
PLAN-0031 fase 03: Scanner SAST com regras customizadas e motor AST para
garantir Ultra Blindagem do código gerado por IA (Zero Stubs).

Detecta de forma determinística:
  1. SQLi: Concatenação / f-strings em cursor.execute(...) ou queries.
  2. Command Injection: Chamadas com shell=True ou os.system(...).
  3. Insecure Deserialization: pickle.load(s) ou yaml.load sem safe_load.
  4. Weak Cryptography / Hashes: hashlib.md5 ou hashlib.sha1 sem propósito seguro.
"""

import ast
import json
import os
import subprocess
import sys
from typing import Dict, List, NamedTuple, Optional


class SastViolation(NamedTuple):
    rule_id: str
    severity: str
    file_path: str
    line_number: int
    message: str


class AstSecurityVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations: List[SastViolation] = []

    def visit_Call(self, node: ast.Call):
        # 1. Checagem de Command Injection: shell=True ou os.system
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            # os.system(...)
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and func_name == "system":
                self.violations.append(
                    SastViolation(
                        rule_id="aidd-command-injection-shell-true",
                        severity="ERROR",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        message="Uso perigoso de os.system(). Use subprocess.run com lista de argumentos.",
                    )
                )

            # subprocess.*(..., shell=True)
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.violations.append(
                        SastViolation(
                            rule_id="aidd-command-injection-shell-true",
                            severity="ERROR",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            message="Execução de comando no SO com shell=True detectada.",
                        )
                    )

            # 2. Checagem de SQL Injection: .execute(f"...") ou .execute("..." + ...)
            if func_name in ("execute", "raw_query"):
                if node.args:
                    arg0 = node.args[0]
                    # f-string como primeiro argumento de execute
                    if isinstance(arg0, ast.JoinedStr):
                        self.violations.append(
                            SastViolation(
                                rule_id="aidd-sqli-fstring",
                                severity="ERROR",
                                file_path=self.file_path,
                                line_number=node.lineno,
                                message="Possível injeção de SQL via f-string em método execute().",
                            )
                        )
                    # Concatenação de string com BinOp (+)
                    elif isinstance(arg0, ast.BinOp) and isinstance(arg0.op, ast.Add):
                        self.violations.append(
                            SastViolation(
                                rule_id="aidd-sqli-fstring",
                                severity="ERROR",
                                file_path=self.file_path,
                                line_number=node.lineno,
                                message="Possível injeção de SQL via concatenação (+) em método execute().",
                            )
                        )

            # 3. Insecure Deserialization: pickle.loads / pickle.load
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                if module_name == "pickle" and func_name in ("load", "loads"):
                    self.violations.append(
                        SastViolation(
                            rule_id="aidd-insecure-deserialization",
                            severity="ERROR",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            message="Desserialização insegura com pickle detectada.",
                        )
                    )
                if module_name == "yaml" and func_name == "load":
                    # verificar se não está usando SafeLoader
                    safe = False
                    for kw in node.keywords:
                        if kw.arg == "Loader" and getattr(kw.value, "attr", "") in ("SafeLoader", "CSafeLoader"):
                            safe = True
                    if not safe:
                        self.violations.append(
                            SastViolation(
                                rule_id="aidd-insecure-deserialization",
                                severity="ERROR",
                                file_path=self.file_path,
                                line_number=node.lineno,
                                message="yaml.load() sem SafeLoader detectado. Use yaml.safe_load().",
                            )
                        )

                # 4. Weak Hashing: hashlib.md5 / hashlib.sha1
                if module_name == "hashlib" and func_name in ("md5", "sha1"):
                    self.violations.append(
                        SastViolation(
                            rule_id="aidd-weak-hashing",
                            severity="WARNING",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            message=f"Função de hash fraca hashlib.{func_name}() detectada.",
                        )
                    )

        self.generic_visit(node)


class SastScanner:
    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = rules_file or os.path.join(os.path.dirname(__file__), "semgrep_rules.yml")

    def scan_file_ast(self, file_path: str) -> List[SastViolation]:
        """Varredura estática de segurança baseada em AST determinística."""
        if not file_path.endswith(".py") or not os.path.isfile(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            tree = ast.parse(code, filename=file_path)
            visitor = AstSecurityVisitor(file_path)
            visitor.visit(tree)
            return visitor.violations
        except SyntaxError:
            return []

    def scan_directory(self, target_dir: str, use_semgrep_if_available: bool = True) -> List[SastViolation]:
        """Varre um diretório completo recursivamente."""
        violations: List[SastViolation] = []

        # Tentar Semgrep primeiro se solicitado e disponível
        if use_semgrep_if_available and os.path.isfile(self.rules_file):
            try:
                cmd = ["semgrep", "--config", self.rules_file, "--json", target_dir]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if proc.returncode in (0, 1) and proc.stdout:
                    data = json.loads(proc.stdout)
                    for r in data.get("results", []):
                        violations.append(
                            SastViolation(
                                rule_id=r.get("check_id", "semgrep-rule"),
                                severity=r.get("extra", {}).get("severity", "ERROR"),
                                file_path=r.get("path", ""),
                                line_number=r.get("start", {}).get("line", 0),
                                message=r.get("extra", {}).get("message", ""),
                            )
                        )
                    return violations
            except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
                # Fallback transparente para o motor AST nativo
                pass

        # Motor AST nativo
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    violations.extend(self.scan_file_ast(full_path))

        return violations
