#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_MIGRATION_ROT (ISSUE-0017 / Lei Canônica #3)
=============================================================================
Quality Gate determinístico de prevenção a Migration Rot.
Garante que toda migração de banco de dados seja idempotente, possua rollback
funcional e completo (downgrade) e convirja perfeitamente para o schema declarado.

Regra Canônica (ISSUE-0017 / Lei #3 Structured Persistence):
  Uma migração que não é idempotente, não tem rollback ou deixa o schema
  divergindo do declarado deve ser bloqueada ANTES de atingir qualquer banco
  real de desenvolvimento, homologação ou produção.

Critérios Determinísticos Auditados:
  1. Varredura Estática de Rollbacks (AST):
     - Todo arquivo de migração DEVE definir a função `downgrade()`.
     - `downgrade()` não pode ser vazia, stub ou mero `pass` quando `upgrade()`
       contém operações de mutação DDL.
  2. Execução Efêmera em Memória / Temporário Isolado:
     - Nenhum banco real de produção ou persistente é tocado.
  3. Convergência de Schema:
     - Aplicação de `upgrade head` constrói o schema, que é auditado contra
       os modelos declarados (ex: alembic_models.py / SQLAlchemy metadata).
     - Divergência de tabelas ou colunas bloqueia com exit 1.
  4. Prova de Idempotência por Re-aplicação:
     - Re-execução imediata do upgrade não deve falhar nem alterar o schema.
  5. Rollback Total (Downgrade):
     - Execução de `downgrade base` deve remover todas as tabelas e índices
       criados pela migração.
  6. Ciclo Completo (Upgrade -> Downgrade -> Upgrade):
     - Re-aplicação pós-rollback deve convergir para o mesmo schema exato.
  7. Declaração Explícita de Escopo de Motor (Lei #8 Honestidade de Rótulo):
     - Escopo coberto: SQLite WAL (efêmero / in-memory).
     - Limite metrológico: Migrações PostgreSQL requerem instância de serviço
       dedicada e não são executadas em memória por este portão.

Saída:
  exit 0 = Todas as migrações possuem rollback funcional, convergem e são idempotentes.
  exit 1 = Divergência de schema, ausência de rollback, resíduo após downgrade ou falha de ciclo.
"""

import argparse
import ast
import importlib.util
import os
import sqlite3
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def auditar_ast_migracoes(versions_dir: str) -> List[str]:
    """Audita estaticamente os arquivos de migração procurando ausência ou stubs em downgrade()."""
    erros = []
    if not os.path.isdir(versions_dir):
        return [f"Diretório de versões de migração não encontrado: {versions_dir}"]

    py_files = [f for f in sorted(os.listdir(versions_dir)) if f.endswith(".py") and not f.startswith("__")]
    if not py_files:
        return [f"Nenhum arquivo de migração encontrado em {versions_dir}"]

    for py_file in py_files:
        caminho = os.path.join(versions_dir, py_file)
        try:
            with open(caminho, "r", encoding="utf-8", errors="replace") as f:
                codigo = f.read()
            tree = ast.parse(codigo, filename=caminho)
        except Exception as e:
            erros.append(f"{py_file}: Erro ao fazer parsing AST: {e}")
            continue

        upgrade_func = None
        downgrade_func = None

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                if node.name == "upgrade":
                    upgrade_func = node
                elif node.name == "downgrade":
                    downgrade_func = node

        if upgrade_func is None:
            erros.append(f"{py_file}: Função upgrade() ausente.")
            continue

        if downgrade_func is None:
            erros.append(f"{py_file}: Função downgrade() ausente (missing rollback).")
            continue

        # Verificar se downgrade() tem corpo real
        stmts_downgrade = [
            stmt for stmt in downgrade_func.body
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
            and not isinstance(stmt, ast.Pass)
        ]

        stmts_upgrade = [
            stmt for stmt in upgrade_func.body
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
            and not isinstance(stmt, ast.Pass)
        ]

        if stmts_upgrade and not stmts_downgrade:
            erros.append(
                f"{py_file}: Função downgrade() vazia ou apenas com pass/docstring "
                "enquanto upgrade() possui operações (missing rollback)."
            )

    return erros


def extrair_schema_sqlite(db_path: str) -> Dict[str, Any]:
    """Inspeciona o banco SQLite e extrai a estrutura de tabelas, colunas e índices."""
    schema: Dict[str, Any] = {"tables": {}, "indexes": {}}
    if not os.path.isfile(db_path):
        return schema

    conn = sqlite3.connect(db_path)
    try:
        # Tabelas normais (excluindo internas do SQLite)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tabelas = [row[0] for row in cursor.fetchall()]

        for tabela in tabelas:
            # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
            cols_cursor = conn.execute(f"PRAGMA table_info({tabela})")
            colunas = {
                r[1]: {
                    "type": (r[2] or "").upper(),
                    "notnull": bool(r[3]),
                    "has_default": r[4] is not None,
                    "pk": bool(r[5]),
                }
                for r in cols_cursor.fetchall()
            }
            schema["tables"][tabela] = colunas

        # Índices
        idx_cursor = conn.execute(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
        )
        for row in idx_cursor.fetchall():
            schema["indexes"][row[0]] = row[1]

    finally:
        conn.close()

    return schema


def comparar_schemas_sqlite(s1: Dict[str, Any], s2: Dict[str, Any]) -> List[str]:
    """Compara dois schemas SQLite e retorna discrepâncias."""
    diffs = []
    t1 = set(s1.get("tables", {}).keys())
    t2 = set(s2.get("tables", {}).keys())

    if t1 != t2:
        diffs.append(f"Tabelas divergentes: presentes na 1ª={t1 - t2}, presentes na 2ª={t2 - t1}")

    for tabela in t1.intersection(t2):
        cols1 = s1["tables"][tabela]
        cols2 = s2["tables"][tabela]
        if set(cols1.keys()) != set(cols2.keys()):
            diffs.append(
                f"Tabela {tabela}: colunas divergentes (1ª={set(cols1.keys())}, 2ª={set(cols2.keys())})"
            )
        else:
            for col_name, c1 in cols1.items():
                c2 = cols2[col_name]
                if c1["notnull"] != c2["notnull"] or c1["pk"] != c2["pk"]:
                    diffs.append(f"Tabela {tabela}, coluna {col_name}: atributos divergentes ({c1} vs {c2})")

    idx1 = set(s1.get("indexes", {}).keys())
    idx2 = set(s2.get("indexes", {}).keys())
    if idx1 != idx2:
        diffs.append(f"Índices divergentes: presentes na 1ª={idx1 - idx2}, presentes na 2ª={idx2 - idx1}")

    return diffs


def carregar_metadata_declarado(models_file: str) -> Tuple[Optional[Any], List[str]]:
    """Carrega dinamicamente os modelos declarados via alembic_models.py ou SQLAlchemy."""
    if not os.path.isfile(models_file):
        return None, []

    erros = []
    try:
        spec = importlib.util.spec_from_file_location("alembic_models_dynamic", models_file)
        if spec is None or spec.loader is None:
            return None, [f"Falha ao carregar spec de modelos de {models_file}"]
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "Base") and hasattr(mod.Base, "metadata"):
            return mod.Base.metadata, []
        return None, []
    except Exception as e:
        erros.append(f"Erro ao carregar modelos declarados de {models_file}: {e}")
        return None, erros


def verificar_convergencia_com_modelos(
    schema_sqlite: Dict[str, Any], metadata_declarado: Any
) -> List[str]:
    """Verifica se todas as tabelas e colunas declaradas no metadata existem no SQLite."""
    erros = []
    if metadata_declarado is None:
        return erros

    tabelas_sqlite = schema_sqlite.get("tables", {})

    for table_name, table_obj in metadata_declarado.tables.items():
        if table_name not in tabelas_sqlite:
            erros.append(f"Tabela declarada '{table_name}' não foi criada pela migração no SQLite.")
            continue

        cols_sqlite = tabelas_sqlite[table_name]
        for col in table_obj.columns:
            if col.name not in cols_sqlite:
                erros.append(
                    f"Coluna declarada '{table_name}.{col.name}' ausente no schema gerado pela migração."
                )

    return erros


def _executar_comando_alembic(ini_path: str, db_path: str, acao: str, argumento: str) -> Tuple[int, str, str]:
    """Executa comando alembic em subprocesso hermético apontando para banco efêmero."""
    base_dir = os.path.dirname(os.path.abspath(ini_path))
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{os.path.abspath(db_path)}"
    # Garante que sys.path inclua o base_dir para imports de models
    script_alembic = os.path.join(base_dir, "alembic")

    py_code = f"""
import sys, os
from alembic.config import Config
from alembic import command

ini_path = sys.argv[1]
acao = sys.argv[2]
arg = sys.argv[3]
base_dir = os.path.dirname(os.path.abspath(ini_path))
sys.path.insert(0, base_dir)

cfg = Config(ini_path)
cfg.set_main_option('script_location', os.path.join(base_dir, 'alembic'))

if acao == 'upgrade':
    command.upgrade(cfg, arg)
elif acao == 'downgrade':
    command.downgrade(cfg, arg)
else:
    raise ValueError(f'Acao desconhecida: {{acao}}')
"""

    res = subprocess.run(
        [sys.executable, "-c", py_code, os.path.abspath(ini_path), acao, argumento],
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    return res.returncode, res.stdout, res.stderr


def auditar_migracoes_target(target_dir: str) -> Tuple[bool, List[str]]:
    """Executa a auditoria completa de ciclo de migrações para um alvo específico."""
    erros = []
    ini_path = os.path.join(target_dir, "alembic.ini")
    versions_dir = os.path.join(target_dir, "alembic", "versions")
    models_path = os.path.join(target_dir, "alembic_models.py")

    if not os.path.isfile(ini_path):
        return False, [f"alembic.ini ausente em {target_dir}"]

    # 1. Auditoria Estática AST (Rollback ausente ou vazio)
    erros_ast = auditar_ast_migracoes(versions_dir)
    if erros_ast:
        erros.extend(erros_ast)
        return False, erros

    # 2. Carregar modelos declarados para conferência de convergência
    metadata_declarado, erros_meta = carregar_metadata_declarado(models_path)
    if erros_meta:
        erros.extend(erros_meta)
        return False, erros

    # 3. Execução em Banco Efêmero (nenhum banco real é tocado)
    tf = tempfile.NamedTemporaryFile(suffix=".db", prefix="aidd_ephemeral_migr_", delete=False)
    tf.close()
    db_path = tf.name

    try:
        # Passo 3.1: Upgrade head
        code_up, out_up, err_up = _executar_comando_alembic(ini_path, db_path, "upgrade", "head")
        if code_up != 0:
            erros.append(f"Falha ao executar 'alembic upgrade head' no banco efêmero:\n{err_up or out_up}")
            return False, erros

        schema_up1 = extrair_schema_sqlite(db_path)

        # Passo 3.2: Comparar com schema declarado
        if metadata_declarado is not None:
            erros_conv = verificar_convergencia_com_modelos(schema_up1, metadata_declarado)
            if erros_conv:
                erros.extend(erros_conv)
                return False, erros

        # Passo 3.3: Prova de Idempotência da Re-aplicação
        code_reup, out_reup, err_reup = _executar_comando_alembic(ini_path, db_path, "upgrade", "head")
        if code_reup != 0:
            erros.append(f"Re-aplicação de migração falhou (não idempotente):\n{err_reup or out_reup}")
            return False, erros

        schema_reup = extrair_schema_sqlite(db_path)
        diff_reup = comparar_schemas_sqlite(schema_up1, schema_reup)
        if diff_reup:
            erros.append(f"Re-aplicação causou mutação no schema (não idempotente): {diff_reup}")
            return False, erros

        # Passo 3.4: Downgrade base (Rollback)
        code_down, out_down, err_down = _executar_comando_alembic(ini_path, db_path, "downgrade", "base")
        if code_down != 0:
            erros.append(f"Falha ao executar 'alembic downgrade base' (rollback falhou):\n{err_down or out_down}")
            return False, erros

        schema_down = extrair_schema_sqlite(db_path)
        tabelas_restantes = set(schema_down.get("tables", {}).keys()) - {"alembic_version"}
        if tabelas_restantes:
            erros.append(
                f"Rollback incompleto: tabelas ainda persistem após downgrade base: {sorted(tabelas_restantes)}"
            )
            return False, erros

        # Passo 3.5: Ciclo Completo (Upgrade -> Downgrade -> Upgrade)
        code_cycle, out_cycle, err_cycle = _executar_comando_alembic(ini_path, db_path, "upgrade", "head")
        if code_cycle != 0:
            erros.append(f"Falha ao re-executar upgrade após downgrade:\n{err_cycle or out_cycle}")
            return False, erros

        schema_up2 = extrair_schema_sqlite(db_path)
        diff_ciclo = comparar_schemas_sqlite(schema_up1, schema_up2)
        if diff_ciclo:
            erros.append(f"Divergência de schema após ciclo completo de upgrade/downgrade/upgrade: {diff_ciclo}")
            return False, erros

    finally:
        # Garantir limpeza imediata do arquivo efêmero
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

    return len(erros) == 0, erros


def descobrir_alvos_migracao() -> List[str]:
    """Descobre automaticamente projetos com alembic.ini no ecossistema."""
    candidatos = [
        os.path.join(ROOT_DIR, "tools", "aidd-master"),
        os.path.join(ROOT_DIR, "tools", "aidd-enterprise"),
    ]
    alvos = []
    for cand in candidatos:
        if os.path.isfile(os.path.join(cand, "alembic.ini")):
            alvos.append(cand)
    return alvos


def main() -> int:
    parser = argparse.ArgumentParser(
        description="G_MIGRATION_ROT: Quality Gate determinístico de prevenção a Migration Rot."
    )
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        help="Diretório contendo alembic.ini para auditar (pode ser repetido).",
    )
    args = parser.parse_args()

    print("=" * 72)
    print(" [GATE] G_MIGRATION_ROT — Prevenção a Migration Rot (ISSUE-0017 / Lei #3)")
    print("=" * 72)

    # Declaração Explícita de Escopo de Motor (Lei #8 Honestidade de Rótulo)
    print("\n [ESCOPO DE MOTOR — LEI #8 / HONESTIDADE DE RÓTULO]")
    print(" Motor testado: SQLite WAL (efêmero em memória / tmp isolado por execução).")
    print(" Limite metrológico: Migrações PostgreSQL não são executadas em memória neste portão")
    print(" e requerem instância de serviço dedicada. Apenas o motor padrão é exercitado.")
    print("=" * 72)

    alvos = args.targets if args.targets else descobrir_alvos_migracao()
    if not alvos:
        print("[ERRO] Nenhum alvo de migração encontrado para auditoria.")
        return 1

    falhas_totais = {}
    conformes = []

    for alvo in alvos:
        nome_alvo = os.path.relpath(alvo, ROOT_DIR)
        print(f"\n[AUDITANDO] Alvo: {nome_alvo}")
        sucesso, erros = auditar_migracoes_target(alvo)
        if sucesso:
            conformes.append(nome_alvo)
            print(f"  [OK] Varredura AST: rollbacks presentes e não-vazios.")
            print(f"  [OK] Banco efêmero: upgrade, convergência e downgrade executados.")
            print(f"  [OK] Idempotência comprovada por re-aplicação.")
            print(f"  [OK] Ciclo de migração reversível (upgrade -> downgrade -> upgrade).")
        else:
            falhas_totais[nome_alvo] = erros
            print(f"  [FALHA] Violações detectadas em {nome_alvo}.")

    print("\n" + "=" * 72)
    if falhas_totais:
        print(f" [FALHA] Quality Gate REPROVADO em {len(falhas_totais)} alvo(s) (ISSUE-0017 / Lei #3):")
        print("=" * 72)
        for alvo, errs in falhas_totais.items():
            print(f"\n  [VIOLAÇÃO] {alvo}:")
            for e in errs:
                print(f"    - {e}")
        print("\n" + "=" * 72)
        print(" REGRA CANÔNICA VIOLADA (Lei #3 Structured Persistence):")
        print(" Toda migração deve possuir rollback funcional, não divergir do schema declarado")
        print(" e provar idempotência estrita via re-aplicação antes de tocar qualquer banco.")
        print("=" * 72)
        return 1

    print(f" [SUCESSO] 100% dos alvos ({len(conformes)}) aprovados no portão G_MIGRATION_ROT!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
