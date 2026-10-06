# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_DRIFT_ANALYZER
=============================================================================
Detecta redundâncias estruturais e duplicidade de assinaturas de funções
entre fatias verticais VSA (features).

Regras de conformidade:
  1. Funções ou métodos de domínio em fatias diferentes (src/features/*)
     com a mesma assinatura e corpo funcional similar geram aviso ou bloqueio
     se excederem o limite de tolerância (sugestão de extração para src/core/).
  2. Fornece relatório determinístico de redundância inter-fatias via AST.
  3. Suporta modo de verificação estrita (--strict) para pipelines CI/CD.

Uso:
  python gates/G_DRIFT_ANALYZER.py [--target PATH] [--strict]
      exit 0 = Nenhuma duplicação indevida encontrada
      exit 1 = Duplicação inter-fatias detectada (modo estrito)
"""

import ast
import hashlib
import os
import sys
from typing import Dict, List, Set, Tuple


class FunctionSignatureVisitor(ast.NodeVisitor):
    def __init__(self, slice_name: str, file_path: str):
        self.slice_name = slice_name
        self.file_path = file_path
        self.functions: List[Dict[str, any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_func(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_func(node)
        self.generic_visit(node)

    def _analyze_func(self, node):
        # Ignora métodos mágicos ou handlers padrão
        if node.name.startswith("__") and node.name.endswith("__"):
            return

        arg_names = [a.arg for a in node.args.args]
        
        # Gera hash estrutural normalizado do corpo (desconsiderando docstrings)
        body_stmts = [
            s for s in node.body 
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))
        ]
        
        body_dump = "".join(ast.dump(s) for s in body_stmts)
        body_hash = hashlib.sha256(body_dump.encode("utf-8")).hexdigest()

        self.functions.append({
            "name": node.name,
            "args": arg_names,
            "line": node.lineno,
            "slice": self.slice_name,
            "file": self.file_path,
            "body_hash": body_hash,
            "stmts_count": len(body_stmts),
        })


def analyze_slice_drift(base_dir: str) -> List[Dict[str, any]]:
    """
    Analisa todas as fatias em base_dir/src/features ou base_dir/features
    e detecta funções com assinatura e lógica duplicadas entre fatias distintas.
    """
    features_dir = os.path.join(base_dir, "src", "features")
    if not os.path.isdir(features_dir):
        features_dir = os.path.join(base_dir, "features")
    
    if not os.path.isdir(features_dir):
        return []

    all_funcs: List[Dict[str, any]] = []

    for entry in os.listdir(features_dir):
        slice_path = os.path.join(features_dir, entry)
        if not os.path.isdir(slice_path) or entry.startswith("_"):
            continue

        for root, _, files in os.walk(slice_path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8-sig") as f:
                            tree = ast.parse(f.read(), filename=full_path)
                        visitor = FunctionSignatureVisitor(slice_name=entry, file_path=full_path)
                        visitor.visit(tree)
                        all_funcs.extend(visitor.functions)
                    except Exception:
                        continue

    # Agrupa por hash de corpo e assinatura para detectar redundância cruzada
    duplicates: List[Dict[str, any]] = []
    seen_hashes: Dict[str, Dict[str, any]] = {}

    for fn in all_funcs:
        # Só considera funções com complexidade mínima (> 1 statement)
        if fn["stmts_count"] <= 1:
            continue

        sig_key = f"{fn['name']}::{fn['body_hash']}"
        if sig_key in seen_hashes:
            prev = seen_hashes[sig_key]
            if prev["slice"] != fn["slice"]:
                duplicates.append({
                    "function": fn["name"],
                    "args": fn["args"],
                    "slice_a": prev["slice"],
                    "file_a": prev["file"],
                    "line_a": prev["line"],
                    "slice_b": fn["slice"],
                    "file_b": fn["file"],
                    "line_b": fn["line"],
                })
        else:
            seen_hashes[sig_key] = fn

    return duplicates


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Verificador de Drift e Redundância Inter-Fatias VSA")
    parser.add_argument("--target", default=".", help="Diretório raiz a ser analisado")
    parser.add_argument("--strict", action="store_true", help="Falha com Exit 1 se houver duplicações")
    args = parser.parse_args()

    duplicates = analyze_slice_drift(args.target)
    
    if duplicates:
        print(f"[AVISO] G_DRIFT_ANALYZER: Detectadas {len(duplicates)} duplicidade(s) estrutural(is) inter-fatias:")
        for dup in duplicates:
            print(f"  - Função '{dup['function']}' duplicada entre:")
            print(f"      Fatia [{dup['slice_a']}]: {dup['file_a']}:{dup['line_a']}")
            print(f"      Fatia [{dup['slice_b']}]: {dup['file_b']}:{dup['line_b']}")
            print(f"      -> Sugestão canônica: extrair função para src/core/")
        
        if args.strict:
            return 1
    else:
        print("[OK] G_DRIFT_ANALYZER: Nenhuma redundância funcional inter-fatias detectada.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
