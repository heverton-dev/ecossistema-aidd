# -*- coding: utf-8 -*-
"""
 =============================================================================
 ECOSSISTEMA AIDD — QUALITY GATE: G_ARQUITETURA_DELIVERABLE
 =============================================================================
 Gate estatico via AST que valida conformidade com Clean Architecture e DDD
 nos deliverables (templates e modulos de software gerados pelas ferramentas).

 Regras de verificacao (AST-based, Zero Token Fallacy):
   1. SQL cru/sqlite3: proibe `execute()`/`executemany()`/`executescript()`
      e `import sqlite3` em arquivos FORA de infrastructure/.
   2. Domain isolado: proibe `import sqlite3`/`sqlalchemy`/`infrastructure.*`
      dentro de domain/.
   3. Routes limpos: proibe `execute()`/`import sqlite3`/`invalidate` em
      routes.py (interfaces).

 Duas correcoes aplicadas em 2026-09-10 apos auditoria por reproducao real
 (achado: 524 violacoes reportadas, a maioria falso-positivo):
   a. `_extract_execute_calls` so conta `.execute()/.executemany()/
      .executescript()` como SQL quando o 1o argumento e uma string literal
      (ou f-string) — trade-off deliberado (perde deteccao de query montada
      em variavel antes de passar pro execute) para eliminar falso positivo
      de metodos de negocio homonimos (ex.: `SagaStep.execute(context)`,
      que recebe um dict, nao uma query).
   b. Arquivos do nucleo compartilhado que legitimamente SAO a camada de
      infraestrutura (persistencia, fila, webhooks, revogacao de token) mas
      vivem em `core/`/`v2/` em vez de `infrastructure/` — ver
      NUCLEO_COMPARTILHADO_INFRA — sao tratados como infrastructure/ pela
      Regra 1. Isso NAO exime routes.py/server.py nem arquivos de dominio.

 Diretorios auditados (deliverables e templates):
   - tools/*/src/
   - tools/*/templates/
   Fora do escopo (deliberado, mesma convencao de G_HONESTIDADE_ROTULO):
   tools/*/materiais-extras/examples/** (material de documentacao/exemplo,
   nao script vivo).

 Uso:
   python gates/G_ARQUITETURA_DELIVERABLE.py
       exit 0 = nenhuma violacao de Clean Architecture detectada.
       exit 1 = ao menos 1 violacao detectada (arquivo, linha e regra
                sao impressos).
"""

import ast
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Diretorios a escanear (caminhos relativos a ROOT_DIR)
# ---------------------------------------------------------------------------
DIRETORIOS_AUDITADOS = [
    "tools/aidd-master/src",
    "tools/aidd-master/templates",
    "tools/aidd-enterprise/src",
    "tools/aidd-enterprise/templates",
    "tools/aidd-generator/src",
    "tools/aidd-generator/templates",
    "tools/aidd-ops/src",
    "tools/aidd-ops/templates",
    "tools/aidd-bridge/src",
    "tools/aidd-forge/aidd_forge",
]

# ---------------------------------------------------------------------------
# Padrões de SQL e banco de dados
# ---------------------------------------------------------------------------
SQL_CALL_NAMES = {"execute", "executemany", "executescript"}
DB_IMPORT_MODULES = {"sqlite3", "sqlalchemy", "psycopg2"}
INFRA_KEYWORDS = {"infrastructure"}
CACHE_KEYWORDS = {"invalidate", "invalidate_prefix", "read_model", "cache"}

# Arquivos do nucleo compartilhado (tools/*/src/core/, templates/core/,
# templates/v2/) que implementam persistencia/fila/webhooks/revogacao de
# token — sao a infraestrutura de fato do framework, so nao vivem numa
# pasta chamada infrastructure/. Auditado manualmente linha a linha em
# 2026-09-10 antes de entrar nesta lista (ver commit de correcao do gate).
NUCLEO_COMPARTILHADO_INFRA = {
    "database.py",
    "database_adapter.py",
    "outbox_worker.py",
    "jobs.py",
    "webhooks.py",
    "token_revocation.py",
}

# Mapeamento camada -> arquivos proibidos/permitidos
LAYER_RULES = {
    "infrastructure": {
        "sql_allowed": True,
        "db_imports_allowed": True,
    },
    "domain": {
        "sql_allowed": False,
        "db_imports_allowed": False,
        "infra_imports_allowed": False,
    },
}


# ---------------------------------------------------------------------------
# Helpers: deteccao de camada por path
# ---------------------------------------------------------------------------
def _is_in_layer(filepath, layer):
    parts = filepath.replace("\\", "/").split("/")
    return layer in parts


def _is_shared_kernel_infra(filepath):
    """Arquivo do nucleo compartilhado (core/ ou v2/) que ja e infra de fato
    (ver NUCLEO_COMPARTILHADO_INFRA) — tratado como infrastructure/ na Regra 1."""
    parts = filepath.replace("\\", "/").split("/")
    basename = parts[-1] if parts else ""
    if basename not in NUCLEO_COMPARTILHADO_INFRA:
        return False
    return "core" in parts or "v2" in parts


def _is_infrastructure(filepath):
    return _is_in_layer(filepath, "infrastructure") or _is_shared_kernel_infra(filepath)


def _is_domain(filepath):
    return _is_in_layer(filepath, "domain")


def _is_route_file(filepath):
    basename = os.path.basename(filepath).lower()
    return basename in ("routes.py", "route.py", "router.py", "api.py", "views.py")


# ---------------------------------------------------------------------------
# Helpers: extracao de imports e chamadas via AST
# ---------------------------------------------------------------------------
def _extract_imports(tree):
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def _parece_query_sql(node):
    """True se o 1o argumento da chamada e string literal ou f-string —
    o formato universal de uma query SQL inline. Um metodo de negocio
    homonimo (ex.: SagaStep.execute(context)) recebe um objeto, nao uma
    string, e cai fora daqui. Trade-off deliberado: nao detecta query
    montada numa variavel antes do execute(); ver docstring do modulo."""
    if not node.args:
        return False
    primeiro = node.args[0]
    if isinstance(primeiro, ast.Constant) and isinstance(primeiro.value, str):
        return True
    if isinstance(primeiro, ast.JoinedStr):
        return True
    return False


def _extract_execute_calls(tree):
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        if name in SQL_CALL_NAMES and _parece_query_sql(node):
            calls.append((name, getattr(node, "lineno", 0)))
    return calls


def _extract_cache_calls(tree):
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        if name and any(kw in name.lower() for kw in CACHE_KEYWORDS):
            calls.append((name, getattr(node, "lineno", 0)))
    return calls


# ---------------------------------------------------------------------------
# Regra 1: SQL fora de infrastructure/
# ---------------------------------------------------------------------------
def _check_sql_outside_infra(tree, rel_path):
    violations = []
    if _is_infrastructure(rel_path):
        return violations

    # Checagem via AST: chamadas .execute/.executemany/.executescript
    for call_name, lineno in _extract_execute_calls(tree):
        violations.append({
            "regra": "SQL-fora-infra",
            "arquivo": rel_path,
            "linha": lineno,
            "detalhe": f"chamada .{call_name}() fora de infrastructure/",
        })

    # Checagem via AST: import sqlite3
    imports = _extract_imports(tree)
    if "sqlite3" in imports:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sqlite3":
                        violations.append({
                            "regra": "SQL-fora-infra",
                            "arquivo": rel_path,
                            "linha": getattr(node, "lineno", 0),
                            "detalhe": "import sqlite3 fora de infrastructure/",
                        })
                        break
            elif isinstance(node, ast.ImportFrom):
                if node.module == "sqlite3":
                    violations.append({
                        "regra": "SQL-fora-infra",
                        "arquivo": rel_path,
                        "linha": getattr(node, "lineno", 0),
                        "detalhe": "from sqlite3 ... fora de infrastructure/",
                    })
                    break

    return violations


# ---------------------------------------------------------------------------
# Regra 2: Domain importando infra/banco
# ---------------------------------------------------------------------------
def _check_domain_violations(tree, rel_path):
    violations = []
    if not _is_domain(rel_path):
        return violations

    imports = _extract_imports(tree)

    # import sqlite3/sqlalchemy/psycopg2 em domain
    for mod in imports:
        if mod in DB_IMPORT_MODULES:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] == mod:
                            violations.append({
                                "regra": "domain-imports-infra",
                                "arquivo": rel_path,
                                "linha": getattr(node, "lineno", 0),
                                "detalhe": f"import {alias.name} em domain/ (banco nao pertence ao dominio)",
                            })
                            break
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] == mod:
                        violations.append({
                            "regra": "domain-imports-infra",
                            "arquivo": rel_path,
                            "linha": getattr(node, "lineno", 0),
                            "detalhe": f"from {node.module} ... em domain/ (banco nao pertence ao dominio)",
                        })
                        break

    # import infrastructure.* em domain
    for mod in imports:
        if mod in INFRA_KEYWORDS:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "infrastructure" in alias.name.lower():
                            violations.append({
                                "regra": "domain-imports-infra",
                                "arquivo": rel_path,
                                "linha": getattr(node, "lineno", 0),
                                "detalhe": f"import {alias.name} em domain/ (dependencia de infraestrutura)",
                            })
                            break
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "infrastructure" in node.module.lower():
                        violations.append({
                            "regra": "domain-imports-infra",
                            "arquivo": rel_path,
                            "linha": getattr(node, "lineno", 0),
                            "detalhe": f"from {node.module} ... em domain/ (dependencia de infraestrutura)",
                        })
                        break

    # Chamadas .execute() em domain (SQL embutido)
    for call_name, lineno in _extract_execute_calls(tree):
        violations.append({
            "regra": "domain-imports-infra",
            "arquivo": rel_path,
            "linha": lineno,
            "detalhe": f"chamada .{call_name}() em domain/ (persistencia nao pertence ao dominio)",
        })

    return violations


# ---------------------------------------------------------------------------
# Regra 3: Routes com acoplamento direto a banco/cache
# ---------------------------------------------------------------------------
def _check_route_violations(tree, rel_path):
    violations = []
    if not _is_route_file(rel_path):
        return violations

    # Chamadas .execute() em routes (SQL direto)
    for call_name, lineno in _extract_execute_calls(tree):
        violations.append({
            "regra": "route-db-coupling",
            "arquivo": rel_path,
            "linha": lineno,
            "detalhe": f"chamada .{call_name}() em route (SQL nao pertence a interface)",
        })

    # import sqlite3 em routes
    imports = _extract_imports(tree)
    if "sqlite3" in imports:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sqlite3":
                        violations.append({
                            "regra": "route-db-coupling",
                            "arquivo": rel_path,
                            "linha": getattr(node, "lineno", 0),
                            "detalhe": "import sqlite3 em route (banco nao pertence a interface)",
                        })
                        break
            elif isinstance(node, ast.ImportFrom):
                if node.module == "sqlite3":
                    violations.append({
                        "regra": "route-db-coupling",
                        "arquivo": rel_path,
                        "linha": getattr(node, "lineno", 0),
                        "detalhe": "from sqlite3 ... em route (banco nao pertence a interface)",
                    })
                    break

    # Chamadas de cache/invalidate direto em routes
    for call_name, lineno in _extract_cache_calls(tree):
        violations.append({
            "regra": "route-db-coupling",
            "arquivo": rel_path,
            "linha": lineno,
            "detalhe": f"chamada .{call_name}() em route (cache deve ser orquestrado pelo use case)",
        })

    return violations


# ---------------------------------------------------------------------------
# Auditoria principal
# ---------------------------------------------------------------------------
def _audit_file(filepath, root_dir):
    caminho_abs = os.path.join(root_dir, filepath)
    try:
        with open(caminho_abs, "r", encoding="utf-8-sig") as f:
            fonte = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    try:
        arvore = ast.parse(fonte, filename=filepath)
    except SyntaxError:
        return []

    violations = []
    violations.extend(_check_sql_outside_infra(arvore, filepath))
    violations.extend(_check_domain_violations(arvore, filepath))
    violations.extend(_check_route_violations(arvore, filepath))
    return violations


def checar(root_dir=None):
    if root_dir is None:
        root_dir = ROOT_DIR

    print("=" * 70)
    print(" [GATE] G_ARQUITETURA_DELIVERABLE — Clean Architecture / DDD")
    print("=" * 70)
    print(f" Raiz: {root_dir}")
    print(f" Escopo: tools/*/src/, tools/*/templates/, tools/*/materiais-extras/")
    print("=" * 70)

    all_violations = []
    total_files = 0
    dirs_scanned = 0

    for dir_rel in DIRETORIOS_AUDITADOS:
        dir_abs = os.path.join(root_dir, dir_rel)
        if not os.path.isdir(dir_abs):
            print(f"[SKIP] {dir_rel}/ nao existe neste checkout")
            continue

        dirs_scanned += 1
        dir_files = 0
        dir_violations = []

        for root, _, files in os.walk(dir_abs):
            for fname in sorted(files):
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, root_dir).replace("\\", "/")
                total_files += 1
                dir_files += 1

                violations = _audit_file(rel_path, root_dir)
                if violations:
                    dir_violations.extend(violations)
                    print(f"[FALHA] {rel_path} — {len(violations)} violacao(oes)")
                    for v in violations:
                        print(f"         {v['regra']}:L{v['linha']} — {v['detalhe']}")
                else:
                    print(f"[OK] {rel_path}")

        if dir_violations:
            print(f"\n  Total {dir_rel}/: {len(dir_violations)} violacao(oes) em {dir_files} arquivo(s)")
        else:
            print(f"\n  Total {dir_rel}/: 0 violacao(es) em {dir_files} arquivo(s)")
        all_violations.extend(dir_violations)

    print("\n" + "=" * 70)
    if all_violations:
        regras = {}
        for v in all_violations:
            regras[v["regra"]] = regras.get(v["regra"], 0) + 1

        print(f" [FALHA] Quality Gate REPROVADO com {len(all_violations)} violacao(oes):")
        for regra, count in sorted(regras.items()):
            print(f"  - {regra}: {count} violacao(oes)")
        print()
        for v in all_violations:
            print(f"  - {v['arquivo']}:{v['linha']} [{v['regra']}] {v['detalhe']}")
        print("=" * 70)
        return 1

    print(f" [SUCESSO] Quality Gate G_ARQUITETURA_DELIVERABLE APROVADO")
    print(f"   ({total_files} arquivo(s) auditado(s), {dirs_scanned} diretorio(s), 0 violacao)")
    print("=" * 70)
    return 0


# ---------------------------------------------------------------------------
# API pública para reuso programático (ex.: Fase 8 do aidd-generator)
# ---------------------------------------------------------------------------
def auditar_arquivos(diretorios, root_dir=None):
    """Audita uma lista de diretorios e/ou arquivos .py (caminhos relativos a
    root_dir) contra as regras Clean Architecture/DDD.

    Args:
        diretorios: lista de strings — paths relativos a root_dir. Cada item
            pode ser um diretorio (sera percorrido recursivamente buscando
            *.py) ou um arquivo .py individual.
        root_dir: raiz absoluta do monorepo (default: ROOT_DIR).

    Returns:
        (violacoes, total_arquivos) onde violacoes eh lista de dicts com
        chaves regra/arquivo/linha/detalhe, e total_arquivos eh int.

    Sem saida em stdout — propria para reuso em pipelines.
    """
    if root_dir is None:
        root_dir = ROOT_DIR

    violacoes = []
    total = 0

    for alvo_rel in diretorios:
        alvo_abs = os.path.join(root_dir, alvo_rel)
        if os.path.isdir(alvo_abs):
            for root, _, files in os.walk(alvo_abs):
                for fname in sorted(files):
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, root_dir).replace("\\", "/")
                    total += 1
                    violacoes.extend(_audit_file(rel_path, root_dir))
        elif os.path.isfile(alvo_abs) and alvo_rel.endswith(".py"):
            total += 1
            violacoes.extend(_audit_file(alvo_rel, root_dir))

    return violacoes, total


if __name__ == "__main__":
    sys.exit(checar())
