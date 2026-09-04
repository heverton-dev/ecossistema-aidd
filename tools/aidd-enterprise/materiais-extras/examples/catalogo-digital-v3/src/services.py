import json, urllib.parse
from db import Database
from auth import hash_senha, verificar_senha

class LojaService:
    def __init__(self, db_path="loja.db"):
        self.db = Database(db_path)

    def obter_configuracoes(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT chave, valor FROM configuracoes").fetchall()
            config = {r["chave"]: r["valor"] for r in rows}
            if not config:
                config = {
                    "nome_loja": "Tech & Lifestyle Store",
                    "whatsapp": "5511999999999",
                    "banner_texto": "🔥 Frete Grátis acima de R$ 150 | Atendimento Rápido via WhatsApp",
                    "chave_pix": "pix@techlifestyle.com.br"
                }
                for k, v in config.items():
                    conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (k, v))
                conn.commit()
            return config

    def salvar_configuracoes(self, novas_configs: dict):
        with self.db.get_connection() as conn:
            for k, v in novas_configs.items():
                conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (k, str(v)))
            conn.commit()
            return {"sucesso": True, "config": self.obter_configuracoes()}

    def autenticar_admin(self, email: str, senha: str):
        email_limpo = email.strip().lower()
        with self.db.get_connection() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email_limpo,)).fetchone()
            if user and verificar_senha(senha, user["senha_hash"]):
                return {"sucesso": True, "usuario": {"id": user["id"], "nome": user["nome"], "email": user["email"]}}
            return {"sucesso": False, "erro": "Credenciais invalidas."}

    def cadastrar_admin(self, nome: str, email: str, senha: str):
        with self.db.get_connection() as conn:
            try:
                conn.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                             (nome, email.strip().lower(), hash_senha(senha)))
                conn.commit()
                return {"sucesso": True}
            except:
                return {"sucesso": False, "erro": "Usuario ja existente"}

    def listar_produtos(self, categoria: str = None, busca: str = None, apenas_ativos: bool = True):
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

    def salvar_produto(self, dados: dict):
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
            return {"sucesso": True, "id": pid}

    def deletar_produto(self, produto_id: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
            conn.commit()
            return {"sucesso": True}

    def gerar_link_whatsapp(self, itens: list, cliente_nome: str = "Cliente"):
        config = self.obter_configuracoes()
        numero = config.get("whatsapp", "5511999999999").replace("+", "").replace("-", "").replace(" ", "")
        
        total = sum(i["preco"] * i["qtd"] for i in itens)
        
        msg = f"🛒 *NOVO PEDIDO - {config.get('nome_loja', 'Loja')}*\n\n"
        msg += f"👤 *Cliente:* {cliente_nome}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        
        for item in itens:
            subtotal = item["preco"] * item["qtd"]
            msg += f"• {item['qtd']}x *{item['nome']}* — R$ {subtotal:.2f}\n"
            
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💰 *TOTAL DO PEDIDO:* R$ {total:.2f}\n\n"
        msg += "Olá! Gostaria de confirmar a disponibilidade e os dados para pagamento via Pix/Cartão."
        
        url_encoded = urllib.parse.quote(msg)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={numero}&text={url_encoded}"
        
        # Registrar pedido no banco
        with self.db.get_connection() as conn:
            conn.execute("INSERT INTO pedidos (cliente_nome, itens_json, valor_total) VALUES (?, ?, ?)",
                         (cliente_nome, json.dumps(itens), total))
            conn.commit()
            
        return {"sucesso": True, "whatsapp_url": whatsapp_url, "total": total}

    def seed_dados_iniciais(self):
        with self.db.get_connection() as conn:
            self.obter_configuracoes()
            # Admin padrão
            admin = conn.execute("SELECT * FROM usuarios WHERE email = 'admin@loja.com'").fetchone()
            if not admin:
                conn.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                             ("Gerente da Loja", "admin@loja.com", hash_senha("123456")))
            # Produtos iniciais
            count = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
            if count == 0:
                conn.execute("""
                    INSERT INTO produtos (nome, descricao, preco, preco_promo, categoria, thumbnail, destaque) VALUES
                    ('Teclado Mecânico Wireless 75%', 'Switches silenciosos, RGB customizável e conexão Bluetooth tri-mode.', 349.90, 299.90, 'Periféricos', 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500', 1),
                    ('Mouse Ergonômico Vertical Pro', 'Sensor óptico de alta precisão 4000 DPI com descanso de polegar.', 189.00, 159.90, 'Periféricos', 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500', 1),
                    ('Fone Noise Cancelling Studio', 'Cancelamento ativo de ruído ANC, bateria de 40h e áudio Hi-Res.', 499.00, 429.00, 'Áudio', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500', 1),
                    ('Desk Pad em Couro Premium 90x40', 'Superfície impermeável, toque macio e acabamento em costura reforçada.', 119.90, 89.90, 'Acessórios', 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500', 0),
                    ('Cafeteira Prensa Francesa 1L', 'Vidro borossilicato de alta resistência e êmbolo em inox duplo.', 149.90, 129.00, 'Lifestyle', 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500', 0)
                """)
                conn.commit()
