import urllib.request, urllib.error, json, threading, hmac, hashlib, time, uuid, os
from pathlib import Path

try:
    from core.database import DB_ERRORS
except ImportError:
    from database import DB_ERRORS

class WebhookDispatcher:
    BASE_CATALOG = [
        {
            "event": "*",
            "modulo": "Global",
            "descricao": "Assina todos os eventos gerados por todos os módulos da suíte.",
            "exemplo": {"event": "qualquer_evento", "data": {}}
        },
        {
            "event": "auth.login_sucesso",
            "modulo": "Segurança",
            "descricao": "Disparado após autenticação JWT bem-sucedida de um usuário ou operador.",
            "exemplo": {"email": "admin@empresa.com", "role": "admin"}
        }
    ]
    EVENT_CATALOG = [e.copy() for e in BASE_CATALOG]

    @classmethod
    def register_module_events(cls, slug: str, name: str):
        """Registra dinamicamente os eventos padrão do ciclo de vida de uma fatia vertical."""
        clean_slug = str(slug).lower().strip()
        events = [
            {
                "event": f"{clean_slug}.criado",
                "modulo": name,
                "descricao": f"Disparado na criação e persistência de um novo registro no módulo {name}.",
                "exemplo": {"id": 1, "modulo": clean_slug, "status": "ativo"}
            },
            {
                "event": f"{clean_slug}.atualizado",
                "modulo": name,
                "descricao": f"Disparado na alteração de dados de um registro no módulo {name}.",
                "exemplo": {"id": 1, "modulo": clean_slug, "status": "atualizado"}
            },
            {
                "event": f"{clean_slug}.deletado",
                "modulo": name,
                "descricao": f"Disparado na exclusão lógica ou física de um registro no módulo {name}.",
                "exemplo": {"id": 1, "modulo": clean_slug, "deletado": True}
            }
        ]
        existing = {e["event"] for e in cls.EVENT_CATALOG}
        for ev in events:
            if ev["event"] not in existing:
                cls.EVENT_CATALOG.append(ev)

    def __init__(self, db):
        self.db = db


    def calcular_assinatura(self, secret: str, payload_bytes: bytes) -> str:
        if not secret:
            return ""
        sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return f"sha256={sig}"

    def disparar(self, evento: str, payload: dict):
        def _exec():
            try:
                with self.db.get_connection() as conn:
                    rows = conn.execute("SELECT id, url, eventos, secret, ativo FROM webhooks WHERE ativo = 1").fetchall()
                    if not rows:
                        return
                    webhooks = [dict(r) for r in rows]

                body_dict = {
                    "event": evento,
                    "timestamp": int(time.time()),
                    "delivery_id": str(uuid.uuid4()),
                    "data": payload
                }
                body_bytes = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")

                for wh in webhooks:
                    eventos_sub = []
                    try:
                        eventos_sub = json.loads(wh["eventos"]) if wh["eventos"].startswith("[") else [e.strip() for e in wh["eventos"].split(",")]
                    except (json.JSONDecodeError, AttributeError):
                        eventos_sub = [wh["eventos"]]

                    # Match wildcard or topic
                    if "*" not in eventos_sub and evento not in eventos_sub:
                        continue

                    self._enviar_com_retry(wh, evento, body_bytes, body_dict)
            except Exception as e:
                print(f"[Webhook Dispatcher Error] {e}")

        threading.Thread(target=_exec, daemon=True).start()

    def _enviar_com_retry(self, wh: dict, evento: str, body_bytes: bytes, body_dict: dict):
        max_retries = 3
        url = wh["url"]
        secret = wh.get("secret", "")
        signature = self.calcular_assinatura(secret, body_bytes)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AIDD-Enterprise-Webhook-Studio/5.1",
            "X-Webhook-Event": evento,
            "X-Webhook-Delivery": body_dict.get("delivery_id", str(uuid.uuid4())),
            "X-Webhook-Timestamp": str(body_dict.get("timestamp", int(time.time())))
        }
        if signature:
            headers["X-Webhook-Signature"] = signature
            headers["X-Hub-Signature-256"] = signature

        for tentativa in range(1, max_retries + 1):
            t0 = time.time()
            status_code = None
            resp_body = ""
            status = "falha"
            try:
                req = urllib.request.Request(url, data=body_bytes, headers=headers)
                with urllib.request.urlopen(req, timeout=6) as response:
                    status_code = response.status
                    resp_body = response.read().decode("utf-8", errors="replace")[:1000]
                    status = "sucesso" if (200 <= status_code < 300) else "falha"
            except urllib.error.HTTPError as he:
                status_code = he.code
                resp_body = he.read().decode("utf-8", errors="replace")[:1000]
                status = "falha"
            except urllib.error.URLError as ue:
                resp_body = str(ue.reason)
                status = "timeout" if "timed out" in str(ue.reason).lower() else "falha"
            except Exception as ex:
                resp_body = str(ex)
                status = "falha"

            duracao_ms = round((time.time() - t0) * 1000, 2)

            try:
                with self.db.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO webhook_logs (webhook_id, evento, url, payload_json, status_code, resposta, sucesso)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (wh["id"], evento, url, json.dumps(body_dict, ensure_ascii=False), status_code, resp_body, 1 if status == "sucesso" else 0))
                    conn.commit()
            except DB_ERRORS as db_err:
                print(f"[Webhook Log DB Error] {db_err}")

            if status == "sucesso":
                break
            time.sleep(1)

    def testar_disparo(self, url: str, secret: str, evento: str, payload: dict) -> dict:
        body_dict = {
            "event": evento,
            "timestamp": int(time.time()),
            "delivery_id": str(uuid.uuid4()),
            "data": payload
        }
        body_bytes = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
        signature = self.calcular_assinatura(secret, body_bytes)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AIDD-Enterprise-Webhook-Studio/5.1",
            "X-Webhook-Event": evento,
            "X-Webhook-Delivery": body_dict["delivery_id"],
            "X-Webhook-Timestamp": str(body_dict["timestamp"])
        }
        if signature:
            headers["X-Webhook-Signature"] = signature
            headers["X-Hub-Signature-256"] = signature

        t0 = time.time()
        status_code = None
        resp_body = ""
        status = "falha"

        try:
            req = urllib.request.Request(url, data=body_bytes, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as response:
                status_code = response.status
                resp_body = response.read().decode("utf-8", errors="replace")
                status = "sucesso" if (200 <= status_code < 300) else "falha"
        except urllib.error.HTTPError as he:
            status_code = he.code
            resp_body = he.read().decode("utf-8", errors="replace")
            status = "falha"
        except urllib.error.URLError as ue:
            resp_body = f"Erro de Conexão: {ue.reason}"
            status = "timeout" if "timed out" in str(ue.reason).lower() else "falha"
        except Exception as ex:
            resp_body = f"Erro inesperado: {str(ex)}"
            status = "falha"

        duracao_ms = round((time.time() - t0) * 1000, 2)

        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO webhook_logs (webhook_id, evento, url, payload_json, status_code, resposta, sucesso)
                    VALUES (NULL, ?, ?, ?, ?, ?, ?)
                """, (evento, url, json.dumps(body_dict, ensure_ascii=False), status_code, resp_body[:1000], 1 if status == "sucesso" else 0))
                conn.commit()
        except DB_ERRORS:
            pass

        return {
            "sucesso": (status == "sucesso"),
            "status_code": status_code,
            "duracao_ms": duracao_ms,
            "status": status,
            "headers_enviados": headers,
            "payload_enviado": body_dict,
            "resposta_recebida": resp_body[:2000]
        }

    def get_studio_html(self, title: str = "Plataforma SaaS Suite — Webhook Studio") -> str:
        # Dynamic build of event options & templates
        event_options = "".join([
            f'<option value="{ev["event"]}">{ev["event"]} ({ev["modulo"]})</option>'
            for ev in self.EVENT_CATALOG if ev["event"] != "*"
        ])

        modal_checkboxes = "".join([
            f'<label style="display:flex; align-items:center; gap:0.4rem;"><input type="checkbox" name="wh-ev" value="{ev["event"]}"> {ev["event"]} <span style="color:#94a3b8; font-size:0.75rem;">({ev["modulo"]})</span></label>'
            for ev in self.EVENT_CATALOG
        ])

        catalog_rows = "".join([f'''<tr>
            <td><span class="badge badge-event">{ev["event"]}</span></td>
            <td><span class="code-pill">{ev["modulo"]}</span></td>
            <td>{ev["descricao"]}</td>
            <td><span class="code-pill">{json.dumps(ev["exemplo"], ensure_ascii=False)}</span></td>
        </tr>''' for ev in self.EVENT_CATALOG])

        event_templates_dict = {ev["event"]: ev["exemplo"] for ev in self.EVENT_CATALOG}
        event_templates_json = json.dumps(event_templates_dict, ensure_ascii=False)
        initial_event = self.EVENT_CATALOG[1]["event"] if len(self.EVENT_CATALOG) > 1 else "*"

        _html = (Path(__file__).parent / "webhook_studio.html").read_text(encoding="utf-8")
        _html = _html.replace("__TITLE__", str(title))
        _html = _html.replace("__EVENT_OPTIONS__", str(event_options))
        _html = _html.replace("__CATALOG_ROWS__", str(catalog_rows))
        _html = _html.replace("__MODAL_CHECKBOXES__", str(modal_checkboxes))
        _html = _html.replace("__EVENT_TEMPLATES_JSON__", str(event_templates_json))
        _html = _html.replace("__INITIAL_EVENT__", str(initial_event))
        return _html
