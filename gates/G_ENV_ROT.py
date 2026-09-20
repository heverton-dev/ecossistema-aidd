#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_ENV_ROT (ISSUE-0015 / Lei Canônica #9)
=============================================================================
Quality Gate determinístico de prevenção a Config & Environment Rot.
Audita via AST (Abstract Syntax Tree) todas as chamadas de variáveis de
ambiente no código-fonte (Python: os.getenv, os.environ; JS/TS: process.env)
e exige que toda chave encontrada esteja formalmente documentada em .env.example.

Regra Canônica (ISSUE-0015 / Lei #9 Tool Testing Discipline & Clean Execution):
  Qualquer variável de ambiente que o código lê mas que não consta em
  .env.example impede a execução reprodutível em máquinas virgens/limpas.
  Este portão bloqueia commits (exit 1) na ocorrência de qualquer variável
  não documentada, apontando nome da chave, arquivo e linha.
  Adicionalmente, identifica e relata chaves órfãs presentes em .env.example
  que nenhum código consome, bem como acessos dinâmicos indecidíveis.

Critérios Determinísticos:
  1. Varredura via AST (Python ast e Tree-Sitter JS/TS) — zero regex.
  2. Acessos dinâmicos (f-strings, variáveis como chave) detectados e
     explicitamente reportados como indecidíveis.
  3. Exit 1 em qualquer chave lida pelo código ausente do .env.example.
  4. Relatório explícito de chaves órfãs documentadas sem uso no código.

Saída:
  exit 0 = 100% das variáveis de ambiente lidas pelo código estão em .env.example.
  exit 1 = Ao menos uma variável exigida pelo código não está documentada.
"""

import argparse
import ast
import os
import re
import sys
from typing import Dict, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Diretórios que devem ser ignorados na varredura de código
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".next",
    "dist",
    "build",
    ".gemini",
    ".cursor",
    ".vscode",
    "secoes",
    ".system_generated",
    ".pytest_cache",
    ".turbo",
    ".temp",
    "target_project",
}

# Variáveis providas nativamente pelo kernel/shell do Sistema Operacional.
# Não devem constar em .env.example para não poluir ou quebrar a inicialização do host.
OS_BUILTIN_ENV_VARS = {
    "PATH",
    "SYSTEMROOT",
    "LOCALAPPDATA",
    "APPDATA",
    "TEMP",
    "TMP",
    "HOME",
    "USERPROFILE",
    "WINDIR",
    "PWD",
    "SHELL",
    "TERM",
}

# Inicialização de parsers Tree-Sitter para JS/TS se disponíveis
_TREE_SITTER_AVAILABLE = False
_JS_PARSER = None
_TS_PARSER = None
_TSX_PARSER = None

try:
    import tree_sitter
    import tree_sitter_javascript
    import tree_sitter_typescript

    _JS_LANG = tree_sitter.Language(tree_sitter_javascript.language())
    _TS_LANG = tree_sitter.Language(tree_sitter_typescript.language_typescript())
    _TSX_LANG = tree_sitter.Language(tree_sitter_typescript.language_tsx())

    _JS_PARSER = tree_sitter.Parser(_JS_LANG)
    _TS_PARSER = tree_sitter.Parser(_TS_LANG)
    _TSX_PARSER = tree_sitter.Parser(_TSX_LANG)
    _TREE_SITTER_AVAILABLE = True
except Exception:
    _TREE_SITTER_AVAILABLE = False


def carregar_chaves_env_example(env_path: str) -> Set[str]:
    """Extrai o conjunto de nomes de variáveis declaradas em um arquivo .env ou .env.example."""
    chaves = set()
    if not os.path.isfile(env_path):
        return chaves

    try:
        with open(env_path, "r", encoding="utf-8", errors="replace") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                if linha.startswith("export "):
                    linha = linha[7:].strip()
                if "=" in linha:
                    chave = linha.split("=", 1)[0].strip()
                    if chave:
                        chaves.add(chave)
    except Exception as e:
        print(f"[AVISO] Erro ao ler arquivo de variáveis {env_path}: {e}")

    return chaves


class PythonEnvASTVisitor(ast.NodeVisitor):
    """Varre AST Python procurando leituras de variáveis de ambiente."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.chaves_estaticas: List[Tuple[str, int]] = []
        self.chaves_dinamicas: List[Tuple[str, int, str]] = []

    def _extrair_string_constante(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        ast_str_type = getattr(ast, "Str", None)
        if ast_str_type and isinstance(node, ast_str_type):
            return node.s
        return None

    def visit_Call(self, node: ast.Call):
        # os.getenv(...) ou getenv(...)
        is_getenv = False
        is_environ_get = False

        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name == "getenv":
                is_getenv = True
            elif attr_name in ("get", "setdefault"):
                # Verifica se o objeto base é environ ou os.environ
                val = node.func.value
                if isinstance(val, ast.Attribute) and val.attr == "environ":
                    is_environ_get = True
                elif isinstance(val, ast.Name) and val.id == "environ":
                    is_environ_get = True
        elif isinstance(node.func, ast.Name):
            if node.func.id == "getenv":
                is_getenv = True

        if (is_getenv or is_environ_get) and node.args:
            arg0 = node.args[0]
            val = self._extrair_string_constante(arg0)
            lineno = getattr(node, "lineno", 0)
            if val is not None:
                self.chaves_estaticas.append((val, lineno))
            else:
                expr_str = ast.unparse(arg0) if hasattr(ast, "unparse") else "<dynamic_expr>"
                self.chaves_dinamicas.append((self.filepath, lineno, expr_str))

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        # os.environ[...] ou environ[...]
        is_environ = False
        if isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
            is_environ = True
        elif isinstance(node.value, ast.Name) and node.value.id == "environ":
            is_environ = True

        if is_environ:
            slice_node = node.slice
            if isinstance(slice_node, ast.Index):  # Compatibilidade Python < 3.9
                slice_node = slice_node.value

            val = self._extrair_string_constante(slice_node)
            lineno = getattr(node, "lineno", 0)
            if val is not None:
                self.chaves_estaticas.append((val, lineno))
            else:
                expr_str = ast.unparse(slice_node) if hasattr(ast, "unparse") else "<dynamic_expr>"
                self.chaves_dinamicas.append((self.filepath, lineno, expr_str))

        self.generic_visit(node)


def scan_python_file(filepath: str) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int, str]]]:
    """Realiza o AST scan de um arquivo Python individual."""
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()
        tree = ast.parse(content, filename=filepath)
        visitor = PythonEnvASTVisitor(filepath)
        visitor.visit(tree)
        return visitor.chaves_estaticas, visitor.chaves_dinamicas
    except SyntaxError as e:
        print(f"[AVISO] Erro de sintaxe em {filepath}:{e.lineno}: {e.msg}")
        return [], []
    except Exception as e:
        print(f"[AVISO] Erro ao analisar {filepath}: {e}")
        return [], []


def scan_js_ts_file(filepath: str) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int, str]]]:
    """Realiza o AST scan de um arquivo JavaScript/TypeScript via Tree-Sitter."""
    if not _TREE_SITTER_AVAILABLE:
        return [], []

    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".js", ".mjs", ".cjs"):
        parser = _JS_PARSER
    elif ext == ".ts":
        parser = _TS_PARSER
    elif ext in (".tsx", ".jsx"):
        parser = _TSX_PARSER
    else:
        return [], []

    try:
        with open(filepath, "rb") as f:
            code_bytes = f.read()
        tree = parser.parse(code_bytes)
    except Exception as e:
        print(f"[AVISO] Erro ao parsear JS/TS {filepath}: {e}")
        return [], []

    chaves_estaticas = []
    chaves_dinamicas = []

    def walk_tree_sitter(node):
        # 1. Member expression: process.env.KEY ou Subscript: process.env['KEY'] / process.env[dynamic]
        if node.type in ("member_expression", "subscript_expression"):
            obj = node.child_by_field_name("object")
            prop = node.child_by_field_name("property")
            if obj:
                obj_text = code_bytes[obj.start_byte:obj.end_byte].decode("utf-8", errors="ignore")
                if obj_text == "process.env":
                    lineno = node.start_point[0] + 1
                    if prop:
                        if prop.type == "property_identifier":
                            prop_text = code_bytes[prop.start_byte:prop.end_byte].decode("utf-8", errors="ignore")
                            chaves_estaticas.append((prop_text, lineno))
                        elif prop.type == "string":
                            prop_text = code_bytes[prop.start_byte:prop.end_byte].decode("utf-8", errors="ignore")
                            val = prop_text.strip("'\"`")
                            chaves_estaticas.append((val, lineno))
                        else:
                            dyn_expr = code_bytes[prop.start_byte:prop.end_byte].decode("utf-8", errors="ignore")
                            chaves_dinamicas.append((filepath, lineno, dyn_expr))

        # 2. Destructuring: const { FOO, BAR: alias } = process.env
        if node.type == "variable_declarator":
            val_node = node.child_by_field_name("value")
            name_node = node.child_by_field_name("name")
            if val_node and name_node and name_node.type == "object_pattern":
                val_text = code_bytes[val_node.start_byte:val_node.end_byte].decode("utf-8", errors="ignore")
                if val_text == "process.env":
                    lineno = node.start_point[0] + 1
                    for child in name_node.children:
                        if child.type == "shorthand_property_identifier_pattern":
                            chave_id = code_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="ignore")
                            chaves_estaticas.append((chave_id, lineno))
                        elif child.type == "pair_pattern":
                            key_child = child.child_by_field_name("key")
                            if key_child:
                                if key_child.type == "property_identifier":
                                    chave_id = code_bytes[key_child.start_byte:key_child.end_byte].decode("utf-8", errors="ignore")
                                    chaves_estaticas.append((chave_id, lineno))
                                elif key_child.type == "string":
                                    chave_id = code_bytes[key_child.start_byte:key_child.end_byte].decode("utf-8", errors="ignore").strip("'\"`")
                                    chaves_estaticas.append((chave_id, lineno))
                                else:
                                    dyn = code_bytes[key_child.start_byte:key_child.end_byte].decode("utf-8", errors="ignore")
                                    chaves_dinamicas.append((filepath, lineno, dyn))

        for child in node.children:
            walk_tree_sitter(child)

    walk_tree_sitter(tree.root_node)
    return chaves_estaticas, chaves_dinamicas


def executar_auditoria_env_rot(root_dir: str = ROOT_DIR, env_file: str = None) -> int:
    """Audita todas as leituras de variáveis de ambiente contra o .env.example."""
    print("=" * 72)
    print(" [GATE] G_ENV_ROT — Prevenção de Environment & Config Rot (Lei #9 / ISSUE-0015)")
    print("=" * 72)

    if not env_file:
        env_file = os.path.join(root_dir, ".env.example")

    if not os.path.isfile(env_file):
        print(f"[FALHA CRÍTICA] Arquivo de variáveis {env_file} não encontrado!")
        print(" O ecossistema exige a presença canônica de .env.example para reprodutibilidade.")
        return 1

    chaves_declaradas = carregar_chaves_env_example(env_file)
    print(f"[INFO] .env.example analisado: {len(chaves_declaradas)} chaves documentadas.")

    chaves_por_codigo: Dict[str, List[Tuple[str, int]]] = {}
    todas_chaves_dinamicas: List[Tuple[str, int, str]] = []
    arquivos_escaneados = 0

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            filepath = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()

            if ext == ".py":
                arquivos_escaneados += 1
                estaticas, dinamicas = scan_python_file(filepath)
            elif ext in (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"):
                arquivos_escaneados += 1
                estaticas, dinamicas = scan_js_ts_file(filepath)
            else:
                continue

            for chave, lineno in estaticas:
                if chave in OS_BUILTIN_ENV_VARS:
                    continue
                chaves_por_codigo.setdefault(chave, []).append((filepath, lineno))

            todas_chaves_dinamicas.extend(dinamicas)

    print(f"[INFO] Total de arquivos de código escaneados via AST: {arquivos_escaneados}")
    print(f"[INFO] Total de chaves de ambiente distintas lidas no código: {len(chaves_por_codigo)}")

    # 1. Chaves que o código lê mas não estão em .env.example
    chaves_faltantes: Dict[str, List[Tuple[str, int]]] = {}
    for chave, ocorrencias in chaves_por_codigo.items():
        if chave not in chaves_declaradas:
            chaves_faltantes[chave] = ocorrencias

    # 2. Chaves que estão em .env.example mas nenhum código lê
    chaves_orfas = chaves_declaradas - set(chaves_por_codigo.keys())

    # Relatório de Acessos Dinâmicos (Indecidíveis)
    if todas_chaves_dinamicas:
        print("\n" + "-" * 72)
        print(f" [AVISO / INDECIDÍVEL] {len(todas_chaves_dinamicas)} acesso(s) a env dinâmico(s) detectado(s):")
        print("-" * 72)
        for fp, lineno, expr in todas_chaves_dinamicas:
            rel = os.path.relpath(fp, root_dir)
            print(f"  [DINÂMICO] {rel}:{lineno} -> {expr}")

    # Relatório de Chaves Órfãs
    if chaves_orfas:
        print("\n" + "-" * 72)
        print(f" [INFORMATIVO] {len(chaves_orfas)} chave(s) presente(s) em .env.example não lida(s) diretamente:")
        print("-" * 72)
        for k in sorted(chaves_orfas):
            print(f"  [ÓRFÃ] {k}")

    # Relatório de Chaves Faltantes (Bloqueio - Exit 1)
    if chaves_faltantes:
        print("\n" + "=" * 72)
        print(f" [FALHA] {len(chaves_faltantes)} variável(is) de ambiente exigida(s) pelo código AUSENTE(S) em .env.example:")
        print("=" * 72)
        for k, ocorrencias in sorted(chaves_faltantes.items()):
            print(f"\n  [CHAVE FALTANTE] {k}")
            for fp, lineno in ocorrencias:
                rel = os.path.relpath(fp, root_dir)
                print(f"    -> Em {rel}:{lineno}")

        print("\n" + "=" * 72)
        print(" REGRA CANÔNICA VIOLADA (Lei #9 / ISSUE-0015):")
        print(" Toda variável de ambiente lida pelo código (os.getenv, os.environ, process.env)")
        print(" DEVE constar documentada no arquivo .env.example da raiz.")
        print(" Chaves ausentes quebram a execução em máquinas limpas e são estritamente bloqueadas.")
        print("=" * 72)
        return 1

    print("\n" + "=" * 72)
    print(" [SUCESSO] 100% das variáveis de ambiente lidas pelo código estão em .env.example!")
    print("=" * 72)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="G_ENV_ROT: Quality Gate de Prevenção a Environment Rot (ISSUE-0015).")
    parser.add_argument("--root-dir", default=ROOT_DIR, help="Diretório raiz para varredura de código.")
    parser.add_argument("--env-file", default=None, help="Caminho para arquivo .env.example alternativo.")
    args = parser.parse_args()

    return executar_auditoria_env_rot(root_dir=args.root_dir, env_file=args.env_file)


if __name__ == "__main__":
    sys.exit(main())
