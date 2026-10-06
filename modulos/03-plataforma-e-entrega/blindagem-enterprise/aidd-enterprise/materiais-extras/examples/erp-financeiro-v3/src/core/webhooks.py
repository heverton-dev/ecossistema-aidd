import threading, urllib.request, json

class WebhookDispatcher:
    def __init__(self, db=None):
        self.db = db

    def _obter_webhook_url(self):
        if not self.db:
            return None
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT valor FROM configuracoes WHERE chave = 'webhook_url'").fetchone()
            return row["valor"] if row and row["valor"] else None

    def disparar(self, evento: str, dados: dict):
        url = self._obter_webhook_url()
        if not url or not url.startswith("http"):
            return

        payload = json.dumps({
            "event": evento,
            "timestamp": dados.get("data_hora") or "agora",
            "data": dados
        }, ensure_ascii=False).encode("utf-8")

        def _send():
            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "AIDD-Webhook-Dispatcher/2.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as res:
                    print(f"[WEBHOOK] Evento '{evento}' entregue com sucesso: status {res.status}")
            except Exception as e:
                print(f"[WEBHOOK_WARN] Falha ao disparar webhook para {url}: {e}")

        # Dispara em thread separada para não travar a resposta do usuário
        t = threading.Thread(target=_send, daemon=True)
        t.start()
