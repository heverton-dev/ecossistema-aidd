class ProdutosService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar(self, categoria: str = None, busca: str = None, apenas_ativos: bool = True):
        with self.db.get_connection() as conn:
            query = "SELECT * FROM produtos WHERE 1=1"
            params = []
            if apenas_ativos:
                query += " AND ativo = 1"
            if categoria and categoria.lower() != 'todos':
                query += " AND LOWER(categoria) = LOWER(?)"
                params.append(categoria)
            if busca:
                query += " AND (LOWER(nome) LIKE LOWER(?) OR LOWER(descricao) LIKE LOWER(?))"
                params.extend([f"%{busca}%", f"%{busca}%"])
            query += " ORDER BY destaque DESC, id DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def salvar(self, dados: dict):
        with self.db.get_connection() as conn:
            pid = dados.get("id")
            if pid:
                conn.execute("""
                    UPDATE produtos SET nome=?, descricao=?, preco=?, preco_promo=?, categoria=?, thumbnail=?, estoque=?, destaque=?, ativo=?
                    WHERE id=?
                """, (
                    dados["nome"], dados["descricao"], float(dados["preco"]),
                    float(dados["preco_promo"]) if dados.get("preco_promo") else None,
                    dados["categoria"], dados["thumbnail"], int(dados.get("estoque", 50)),
                    int(dados.get("destaque", 0)), int(dados.get("ativo", 1)), pid
                ))
            else:
                cur = conn.execute("""
                    INSERT INTO produtos (nome, descricao, preco, preco_promo, categoria, thumbnail, estoque, destaque, ativo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dados["nome"], dados["descricao"], float(dados["preco"]),
                    float(dados["preco_promo"]) if dados.get("preco_promo") else None,
                    dados["categoria"], dados["thumbnail"], int(dados.get("estoque", 50)),
                    int(dados.get("destaque", 0)), int(dados.get("ativo", 1))
                ))
                pid = cur.lastrowid
            conn.commit()
            if self.events:
                self.events.emit("produto_salvo", {"id": pid, "nome": dados["nome"]})
            return {"sucesso": True, "id": pid}

    def deletar(self, produto_id: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
            conn.commit()
            if self.events:
                self.events.emit("produto_deletado", {"id": produto_id})
            return {"sucesso": True}
