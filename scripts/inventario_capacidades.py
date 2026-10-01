#!/usr/bin/env python3
import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_test_names(path: Path) -> List[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("test_"):
                names.append(node.name)
    return names


def _get_ast_defs(path: Path) -> Dict[str, List[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return {"functions": [], "classes": []}

    funcs = []
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {"functions": funcs, "classes": classes}


def _unique_lines(path: Path) -> List[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    seen = set()
    out = []
    for l in lines:
        k = l.strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _is_python(path: Path) -> bool:
    return path.suffix == ".py" and path.is_file()


def _find_py_files(root: Path) -> List[Path]:
    files = []
    for p in root.rglob("*.py"):
        try:
            rel = p.relative_to(root)
        except ValueError:
            rel = p
        s = str(rel).replace("\\", "/")
        if s.startswith(".git/") or "__pycache__" in s:
            continue
        files.append(p)
    return files


def foto(repo: Path, cycle_rel: str) -> int:
    root = Path(repo).resolve()
    cycle = root / cycle_rel
    cycle.mkdir(parents=True, exist_ok=True)

    files = _find_py_files(root)
    data: Dict[str, Dict[str, object]] = {}

    for f in files:
        try:
            rel = f.relative_to(root).as_posix()
        except Exception:
            rel = f.name
        data[rel] = {
            "sha256": sha256_file(f),
            "ast": _get_ast_defs(f),
            "test_names": _get_test_names(f),
            "unique_lines": _unique_lines(f),
        }

    out = cycle / "INVENTARIO-ANTES.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def comparar(repo: Path, cycle_rel: str) -> int:
    root = Path(repo).resolve()
    cycle = root / cycle_rel
    antes_path = cycle / "INVENTARIO-ANTES.json"
    if not antes_path.exists():
        return 1

    try:
        antes = json.loads(antes_path.read_text(encoding="utf-8"))
    except Exception:
        return 1

    files = _find_py_files(root)
    agora: Dict[str, Dict[str, object]] = {}
    for f in files:
        try:
            rel = f.relative_to(root).as_posix()
        except Exception:
            rel = f.name
        agora[rel] = {
            "sha256": sha256_file(f),
            "ast": _get_ast_defs(f),
            "test_names": _get_test_names(f),
            "unique_lines": _unique_lines(f),
        }

    orphans = []
    for rel, meta in antes.items():
        if rel not in agora:
            orphans.append(rel)
            continue
        a_lines_list = meta.get("unique_lines", []) or []
        b_lines_list = agora[rel].get("unique_lines", []) or []
        a_lines = set(a_lines_list) if isinstance(a_lines_list, list) else set()
        b_lines = set(b_lines_list) if isinstance(b_lines_list, list) else set()
        extra = a_lines - b_lines
        if extra:
            orphans.append(rel)

    if orphans:
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("foto")
    f.add_argument("--repo", required=True)
    f.add_argument("--cycle", required=True)
    c = sub.add_parser("comparar")
    c.add_argument("--repo", required=True)
    c.add_argument("--cycle", required=True)
    args = p.parse_args()

    if args.cmd == "foto":
        return foto(Path(args.repo), args.cycle)
    if args.cmd == "comparar":
        return comparar(Path(args.repo), args.cycle)
    return 2


if __name__ == "__main__":
    sys.exit(main())
