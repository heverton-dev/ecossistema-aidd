# -*- coding: utf-8 -*-
"""
Testes unitários do módulo VectorStore nativo (pgvector / SQLite fallback).
Valida similaridade de cosseno, isolamento multi-tenant e operações CRUD.
"""

import os
import sys
import pytest
from pathlib import Path

# Adiciona caminhos do src-core
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_CORE = ROOT_DIR / "componentes" / "compartilhado" / "src-core"
if str(SRC_CORE) not in sys.path:
    sys.path.insert(0, str(SRC_CORE))

from vector_store import VectorStore, _similaridade_cosseno


class MockSQLiteAdapter:
    def __init__(self, db_path: str):
        import sqlite3
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self.is_postgres = False
        self.tipo = "sqlite"

    def get_connection(self):
        return self._conn


def test_similaridade_cosseno_matematica():
    # Vetores idênticos devem ter score 1.0
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(_similaridade_cosseno(v1, v2), 0.0001) == 1.0

    # Vetores ortogonais devem ter score 0.0
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(_similaridade_cosseno(v1, v3), 0.0001) == 0.0

    # Vetores vazios ou de dimensões diferentes
    assert _similaridade_cosseno([], []) == 0.0
    assert _similaridade_cosseno([1.0], [1.0, 2.0]) == 0.0


def test_vector_store_sqlite_crud_e_busca(tmp_path):
    db_file = str(tmp_path / "test_vector.db")
    adapter = MockSQLiteAdapter(db_file)
    store = VectorStore(adapter, dimensao_padrao=3)

    # 1. Inicializar schema
    assert store.inicializar_schema() is True

    # 2. Inserir embeddings para dois tenants
    assert store.adicionar("item-1", "Texto clinico 1", [1.0, 0.0, 0.0], tenant_id="tenant-a", metadata={"cat": "cirurgia"}) is True
    assert store.adicionar("item-2", "Texto clinico 2", [0.8, 0.2, 0.0], tenant_id="tenant-a", metadata={"cat": "implante"}) is True
    assert store.adicionar("item-3", "Texto outro tenant", [1.0, 0.0, 0.0], tenant_id="tenant-b", metadata={"cat": "financeiro"}) is True

    # 3. Busca sem filtro de tenant
    res = store.buscar_similares([1.0, 0.0, 0.0], top_k=2)
    assert len(res) == 2
    assert res[0]["score"] == 1.0

    # 4. Busca com isolamento estrito de tenant (tenant-a)
    res_a = store.buscar_similares([1.0, 0.0, 0.0], top_k=5, tenant_id="tenant-a")
    assert len(res_a) == 2
    ids_a = [r["id"] for r in res_a]
    assert "item-1" in ids_a
    assert "item-2" in ids_a
    assert "item-3" not in ids_a  # Garantia Anti-IDOR

    # 5. Busca com limiar mínimo de score
    res_min = store.buscar_similares([1.0, 0.0, 0.0], top_k=5, tenant_id="tenant-a", min_score=0.99)
    assert len(res_min) == 1
    assert res_min[0]["id"] == "item-1"
