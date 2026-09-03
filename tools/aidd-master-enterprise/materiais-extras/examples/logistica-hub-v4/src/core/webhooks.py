import urllib.request, json, threading

class WebhookDispatcher:
    def __init__(self, db):
        self.db = db

    def disparar(self, evento: str, payload: dict):
        def _send():
            try:
                with self.db.get_connection() as conn:
                    row = conn.execute("SELECT valor FROM configuracoes WHERE chave = 'webhook_url'").fetchone()
                    if not row or not row[0]:
                        return
                    url = row[0]
                
                body = json.dumps({"event": evento, "data": payload}).encode("utf-8")
                req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                print(f"[Webhook Dispatch Error] {e}")

        threading.Thread(target=_send, daemon=True).start()
