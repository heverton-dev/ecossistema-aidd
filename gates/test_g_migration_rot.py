#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TESTES DE QUALIDADE: G_MIGRATION_ROT (ISSUE-0017 & Lei Canônica #13)
=============================================================================
Testa o portão determinístico G_MIGRATION_ROT:
1. Caminho feliz: alvos canônicos executam ciclo completo e convergem (exit 0).
2. Prova que morde (Lei #13): remoção deliberada do rollback (downgrade ausente
   ou transformado em pass/stub) faz o portão executar e asserir exit 1.
3. Prova que morde (Lei #13): divergência de schema (model declara tabela/coluna
   não gerada pela migração) faz o portão executar e asserir exit 1.
4. Prova que morde (Lei #13): re-aplicação não idempotente faz o portão falhar
   e asserir exit 1.
=============================================================================
"""

import os
import shutil
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gates.G_MIGRATION_ROT import (
    auditar_ast_migracoes,
    auditar_migracoes_target,
    extrair_schema_sqlite,
    comparar_schemas_sqlite,
)

GATE_SCRIPT = os.path.join(ROOT_DIR, "gates", "G_MIGRATION_ROT.py")
SOURCE_TARGET = os.path.join(ROOT_DIR, "tools", "aidd-master")


def _copiar_ambiente_migracao(dest_dir: str):
    """Copia a estrutura canônica de alembic para um diretório temporário isolado."""
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(os.path.join(SOURCE_TARGET, "alembic.ini"), dest_dir)
    shutil.copy(os.path.join(SOURCE_TARGET, "alembic_models.py"), dest_dir)
    shutil.copytree(os.path.join(SOURCE_TARGET, "alembic"), os.path.join(dest_dir, "alembic"))


def test_caminho_feliz_migracoes_canonicas():
    """Valida que os alvos canônicos passam com exit 0 no portão G_MIGRATION_ROT."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, GATE_SCRIPT]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, env=env)
    assert res.returncode == 0, f"Portão falhou no caminho feliz:\n{res.stderr or res.stdout}"
    assert "SQLite WAL" in res.stdout
    assert "PostgreSQL" in res.stdout
    assert "100% dos alvos" in res.stdout


def test_reprova_quando_falta_rollback_exit_1(tmp_path):
    """Lei #13: Prova que morde quando o rollback é deliberadamente removido."""
    alvo_teste = str(tmp_path / "app_sem_rollback")
    _copiar_ambiente_migracao(alvo_teste)

    # Localizar arquivo de migração e transformar downgrade() em 'pass'
    versions_dir = os.path.join(alvo_teste, "alembic", "versions")
    migr_file = os.path.join(versions_dir, os.listdir(versions_dir)[0])

    with open(migr_file, "r", encoding="utf-8") as f:
        conteudo = f.read()

    idx = conteudo.find("def downgrade")
    assert idx != -1, "Função downgrade deve existir no arquivo original"
    conteudo_sem_rollback = conteudo[:idx] + "def downgrade() -> None:\n    pass\n"

    with open(migr_file, "w", encoding="utf-8") as f:
        f.write(conteudo_sem_rollback)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, GATE_SCRIPT, "--target", alvo_teste]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, env=env)

    # Asserção estrita de reprovação com exit 1
    assert res.returncode == 1, "Portão deveria reprovar com exit 1 quando rollback está ausente ou vazio."
    assert "missing rollback" in res.stdout.lower() or "downgrade" in res.stdout.lower()


def test_reprova_quando_funcao_downgrade_ausente_exit_1(tmp_path):
    """Lei #13: Prova que morde quando a função downgrade() é completamente excluída."""
    alvo_teste = str(tmp_path / "app_downgrade_deletado")
    _copiar_ambiente_migracao(alvo_teste)

    versions_dir = os.path.join(alvo_teste, "alembic", "versions")
    migr_file = os.path.join(versions_dir, os.listdir(versions_dir)[0])

    with open(migr_file, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    # Remove o bloco da função downgrade inteira
    linhas_sem_downgrade = []
    ignorar = False
    for l in linhas:
        if l.strip().startswith("def downgrade"):
            ignorar = True
            continue
        if not ignorar:
            linhas_sem_downgrade.append(l)

    with open(migr_file, "w", encoding="utf-8") as f:
        f.writelines(linhas_sem_downgrade)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, GATE_SCRIPT, "--target", alvo_teste]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, env=env)

    assert res.returncode == 1, "Portão deveria reprovar com exit 1 quando função downgrade() é omitida."
    assert "downgrade() ausente" in res.stdout.lower() or "missing rollback" in res.stdout.lower()


def test_reprova_quando_diverge_schema_exit_1(tmp_path):
    """Lei #13: Prova que morde quando o modelo declara tabela não criada na migração."""
    alvo_teste = str(tmp_path / "app_schema_divergente")
    _copiar_ambiente_migracao(alvo_teste)

    # Injetar uma tabela não existente em alembic_models.py
    models_path = os.path.join(alvo_teste, "alembic_models.py")
    with open(models_path, "a", encoding="utf-8") as f:
        f.write("\n\nclass TabelaFantasma(Base):\n    __tablename__ = 'tabela_fantasma'\n    id = Column(Integer, primary_key=True)\n")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, GATE_SCRIPT, "--target", alvo_teste]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, env=env)

    assert res.returncode == 1, "Portão deveria reprovar com exit 1 por divergência de schema."
    assert "tabela_fantasma" in res.stdout.lower()


def test_reprova_quando_reaplicacao_nao_idempotente_exit_1(tmp_path):
    """Lei #13: Prova que morde quando a migração falha ao ser re-aplicada."""
    alvo_teste = str(tmp_path / "app_nao_idempotente")
    _copiar_ambiente_migracao(alvo_teste)

    versions_dir = os.path.join(alvo_teste, "alembic", "versions")
    migr_file = os.path.join(versions_dir, os.listdir(versions_dir)[0])

    with open(migr_file, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Adiciona um comando DDL sem IF NOT EXISTS diretamente via op.execute
    conteudo_nao_idempotente = conteudo.replace(
        "def upgrade() -> None:\n",
        "def upgrade() -> None:\n    op.execute('CREATE TABLE temp_quebra (id INT)')\n",
    )
    with open(migr_file, "w", encoding="utf-8") as f:
        f.write(conteudo_nao_idempotente)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, GATE_SCRIPT, "--target", alvo_teste]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, env=env)

    assert res.returncode == 1, "Portão deveria reprovar com exit 1 por não-idempotência."
    assert "idempotente" in res.stdout.lower() or "temp_quebra" in res.stdout.lower()
