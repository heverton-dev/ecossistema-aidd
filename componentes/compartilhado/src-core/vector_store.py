# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — VECTOR STORE NATIVO (pgvector + SQLite Fallback)
=============================================================================
Fornece persistência e busca vetorial de alta performance para RAG sem
necessidade de banco vetorial externo proprietário (Pinecone/Qdrant/Chroma).
Regido pelas 9 Camadas de Mercado de CONSTRAINTS.md (Camada 4 — RevNault):
  - Em PostgreSQL 16: utiliza extensão nativa `pgvector` com índice HNSW
    e operador de distância por cosseno (<=>).
  - Em SQLite WAL: armazena vetor serializado em JSON com cálculo vetorial
    determinístico em memória (produto escalar sobre normas L2).
  - Isolamento Multi-Tenant estrito via `tenant_id`.
=============================================================================
"""

import json
import math
from typing import Any, Dict, List, Optional, Tuple


def _similaridade_cosseno(v1: List[float], v2: List[float]) -> float:
    """Calcula a similaridade de cosseno entre dois vetores de ponto flutuante."""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class VectorStore:
    """Gerenciador unificado de embeddings e busca semântica multi-tenant."""

    def __init__(self, db_adapter: Any, dimensao_padrao: int = 1536):
        self.db = db_adapter
        self.dimensao = dimensao_padrao

    def inicializar_schema(self) -> bool:
        """Cria tabelas e extensões necessárias para o armazenamento vetorial."""
        is_postgres = getattr(self.db, "is_postgres", False) or "postgres" in getattr(self.db, "tipo", "").lower()
        conn = self.db.get_connection()
        try:
            with conn:
                cur = conn.cursor()
                if is_postgres:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS semantic_embeddings (
                            id VARCHAR(255) PRIMARY KEY,
                            tenant_id VARCHAR(255) NOT NULL,
                            texto TEXT NOT NULL,
                            metadata JSONB DEFAULT '{{}}'::jsonb,
                            embedding VECTOR({self.dimensao})
                        );
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_semantic_embeddings_hnsw
                        ON semantic_embeddings USING hnsw (embedding vector_cosine_ops);
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_semantic_embeddings_tenant ON semantic_embeddings(tenant_id);")
                else:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS semantic_embeddings (
                            id TEXT PRIMARY KEY,
                            tenant_id TEXT NOT NULL,
                            texto TEXT NOT NULL,
                            metadata TEXT DEFAULT '{}',
                            embedding TEXT NOT NULL
                        );
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_semantic_embeddings_tenant ON semantic_embeddings(tenant_id);")
            return True
        except Exception:
            return False

    def adicionar(
        self,
        item_id: str,
        texto: str,
        vetor: List[float],
        tenant_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Insere ou atualiza um embedding associado a um tenant."""
        if not item_id or not vetor:
            return False
        meta_dict = metadata or {}
        is_postgres = getattr(self.db, "is_postgres", False) or "postgres" in getattr(self.db, "tipo", "").lower()

        conn = self.db.get_connection()
        try:
            with conn:
                cur = conn.cursor()
                if is_postgres:
                    cur.execute(
                        """
                        INSERT INTO semantic_embeddings (id, tenant_id, texto, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            tenant_id = EXCLUDED.tenant_id,
                            texto = EXCLUDED.texto,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding;
                        """,
                        (item_id, tenant_id, texto, json.dumps(meta_dict), vetor)
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO semantic_embeddings (id, tenant_id, texto, metadata, embedding)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT (id) DO UPDATE SET
                            tenant_id = excluded.tenant_id,
                            texto = excluded.texto,
                            metadata = excluded.metadata,
                            embedding = excluded.embedding;
                        """,
                        (item_id, tenant_id, texto, json.dumps(meta_dict), json.dumps(vetor))
                    )
            return True
        except Exception:
            return False

    def buscar_similares(
        self,
        vetor_consulta: List[float],
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Busca os itens mais próximos semanticamente por distância de cosseno."""
        if not vetor_consulta or top_k <= 0:
            return []

        is_postgres = getattr(self.db, "is_postgres", False) or "postgres" in getattr(self.db, "tipo", "").lower()
        conn = self.db.get_connection()
        resultados = []

        try:
            cur = conn.cursor()
            if is_postgres:
                # 1 - (embedding <=> vetor_consulta) converte distância de cosseno em score de similaridade (1.0 = idêntico)
                query = """
                    SELECT id, tenant_id, texto, metadata, (1 - (embedding <=> %s)) AS score
                    FROM semantic_embeddings
                """
                params: List[Any] = [vetor_consulta]
                if tenant_id:
                    query += " WHERE tenant_id = %s"
                    params.append(tenant_id)
                query += " ORDER BY embedding <=> %s LIMIT %s;"
                params.extend([vetor_consulta, top_k])

                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    score = float(row[4])
                    if score >= min_score:
                        meta = row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}")
                        resultados.append({
                            "id": row[0],
                            "tenant_id": row[1],
                            "texto": row[2],
                            "metadata": meta,
                            "score": round(score, 4)
                        })
            else:
                # Fallback SQLite: recupera registros filtrados por tenant e computa similaridade em memória
                query = "SELECT id, tenant_id, texto, metadata, embedding FROM semantic_embeddings"
                params = []
                if tenant_id:
                    query += " WHERE tenant_id = ?"
                    params.append(tenant_id)

                cur.execute(query, tuple(params))
                candidatos = []
                for row in cur.fetchall():
                    try:
                        emb = json.loads(row[4])
                        score = _similaridade_cosseno(vetor_consulta, emb)
                        if score >= min_score:
                            meta = json.loads(row[3]) if isinstance(row[3], str) else (row[3] or {})
                            candidatos.append({
                                "id": row[0],
                                "tenant_id": row[1],
                                "texto": row[2],
                                "metadata": meta,
                                "score": round(score, 4)
                            })
                    except Exception:
                        continue

                candidatos.sort(key=lambda x: x["score"], reverse=True)
                resultados = candidatos[:top_k]

            return resultados
        except Exception:
            return []
