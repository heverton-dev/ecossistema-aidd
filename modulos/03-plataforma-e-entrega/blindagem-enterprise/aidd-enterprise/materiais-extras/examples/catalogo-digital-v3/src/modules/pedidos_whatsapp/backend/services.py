import urllib.parse, json

class PedidosService:
    def __init__(self, db, config_service=None, events=None):
        self.db = db
        self.config_service = config_service
        self.events = events

    def checkout_whatsapp(self, itens: list, cliente_nome: str = "Cliente"):
        config = self.config_service.obter() if self.config_service else {}
        numero = config.get("whatsapp", "5511999999999").replace("+", "").replace("-", "").replace(" ", "")
        total = sum(i["preco"] * i["qtd"] for i in itens)

        msg = f"NOVO PEDIDO - {config.get('nome_loja', 'Loja')}\n\n"
        msg += f"Cliente: {cliente_nome}\n"
        msg += "--------------------\n"
        for item in itens:
            msg += f"- {item['qtd']}x {item['nome']} (R$ {item['preco'] * item['qtd']:.2f})\n"
        msg += "--------------------\n"
        msg += f"TOTAL: R$ {total:.2f}\n"

        url = f"https://api.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(msg)}"

        with self.db.get_connection() as conn:
            conn.execute("INSERT INTO pedidos (cliente_nome, itens_json, valor_total) VALUES (?, ?, ?)",
                         (cliente_nome, json.dumps(itens), total))
            conn.commit()

        if self.events:
            self.events.emit("pedido_criado", {"cliente": cliente_nome, "total": total, "itens": itens})

        return {"sucesso": True, "whatsapp_url": url, "total": total}
