import urllib.request, json, threading

class WebhookDispatcher:
    def __init__(self, db):
        self.db = db

    def disparar(self, evento: str, payload: dict):
        def _send():
            with self.db.get_connection() as conn:
                r = conn.execute("SELECT valor FROM configuracoes WHERE chave = 'webhook_url'").fetchone()
                if r and r[0]:
                    url = r[0]
                    body = json.dumps({"event": evento, "payload": payload}).encode("utf-8")
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "AIDD-v4-Dispatcher"})
                    try:
                        urllib.request.urlopen(req, timeout=3)
                    except Exception:
                        pass
        threading.Thread(target=_send, daemon=True).start()
