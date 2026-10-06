import urllib.request, urllib.error, json, threading, hmac, hashlib, time


class WebhookDispatcher:
    EVENT_CATALOG = [
        {"event": "cross_domain.entrega_to_financeiro", "modulo": "Cross-Domain", "descricao": "Disparado quando uma entrega é finalizada e o frete é liquidado no Financeiro."},
        {"event": "frotas.manutencao_alerta", "modulo": "Frotas", "descricao": "Disparado quando um veículo entra em manutenção e um incidente de SLA é aberto automaticamente."},
        {"event": "auth.login_sucesso", "modulo": "Autenticação", "descricao": "Disparado a cada autenticação bem-sucedida na API."},
        {"event": "frotas.veiculo_cadastrado", "modulo": "Frotas", "descricao": "Disparado ao cadastrar um novo veículo na frota."},
        {"event": "frotas.status_alterado", "modulo": "Frotas", "descricao": "Disparado ao alternar o status operacional de um veículo."},
        {"event": "frotas.veiculo_removido", "modulo": "Frotas", "descricao": "Disparado ao excluir um veículo da frota."},
        {"event": "entregas.remessa_criada", "modulo": "Entregas", "descricao": "Disparado ao criar uma nova ordem de remessa."},
        {"event": "entregas.remessa_cancelada", "modulo": "Entregas", "descricao": "Disparado ao cancelar ou excluir uma remessa."},
        {"event": "wms.item_adicionado", "modulo": "Armazém WMS", "descricao": "Disparado ao cadastrar um item no armazém."},
        {"event": "wms.estoque_ajustado", "modulo": "Armazém WMS", "descricao": "Disparado ao ajustar a quantidade ou posição de um item no WMS."},
        {"event": "wms.item_removido", "modulo": "Armazém WMS", "descricao": "Disparado ao dar baixa de um item no WMS."},
        {"event": "financeiro.lancamento_criado", "modulo": "Financeiro de Fretes", "descricao": "Disparado ao lançar manualmente uma movimentação financeira."},
        {"event": "financeiro.status_alterado", "modulo": "Financeiro de Fretes", "descricao": "Disparado ao alternar o status de pagamento de um lançamento."},
        {"event": "financeiro.lancamento_excluido", "modulo": "Financeiro de Fretes", "descricao": "Disparado ao excluir um lançamento financeiro."},
        {"event": "suporte.incidente_aberto", "modulo": "Central de Incidentes", "descricao": "Disparado ao abrir um novo chamado de incidente ou socorro mecânico."},
        {"event": "suporte.incidente_resolvido", "modulo": "Central de Incidentes", "descricao": "Disparado ao resolver um chamado de incidente."},
        {"event": "suporte.incidente_excluido", "modulo": "Central de Incidentes", "descricao": "Disparado ao excluir um chamado de incidente do histórico."},
    ]

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

    # ----------------- WEBHOOK CONFIGURATION STUDIO -----------------
    def listar_webhooks(self):
        with self.db.get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM webhooks ORDER BY id DESC").fetchall()]

    def _assinar_payload(self, secret: str, body_bytes: bytes) -> str:
        if not secret:
            return ""
        return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    def testar_disparo(self, url: str, secret: str, evento: str, payload: dict) -> dict:
        body_json = {"event": evento, "data": payload}
        body_bytes = json.dumps(body_json, ensure_ascii=False).encode("utf-8")
        assinatura = self._assinar_payload(secret, body_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": evento,
            "X-Webhook-Signature": assinatura
        }

        status_code = None
        status = "falha"
        erro = None
        inicio = time.time()
        try:
            req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as res:
                status_code = res.status
                status = "sucesso" if 200 <= status_code < 300 else "falha"
        except urllib.error.HTTPError as e:
            status_code = e.code
            status = "falha"
            erro = str(e)
        except Exception as e:
            status = "timeout" if "timed out" in str(e).lower() else "falha"
            erro = str(e)
        duracao_ms = round((time.time() - inicio) * 1000, 2)

        webhook_id = None
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT id FROM webhooks WHERE url = ?", (url,)).fetchone()
            if row:
                webhook_id = row[0]
            conn.execute(
                "INSERT INTO webhook_logs (webhook_id, evento, url, payload_json, status_code, duracao_ms, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (webhook_id, evento, url, json.dumps(body_json, ensure_ascii=False), status_code, duracao_ms, status)
            )
            conn.commit()

        return {
            "sucesso": status == "sucesso",
            "status": status,
            "status_code": status_code,
            "duracao_ms": duracao_ms,
            "signature": assinatura,
            "error": erro
        }

    def listar_logs(self, limit: int = 50, status_filtro: str = "todos"):
        with self.db.get_connection() as conn:
            if status_filtro and status_filtro != "todos":
                rows = conn.execute(
                    "SELECT * FROM webhook_logs WHERE status = ? ORDER BY id DESC LIMIT ?",
                    (status_filtro, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM webhook_logs ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_studio_html(self, title: str) -> str:
        webhooks = self.listar_webhooks()
        cards = "".join(
            f"<div class='wh-card'><b>{w['nome']}</b><br>{w['url']}<br>Ativo: {w['ativo']}</div>"
            for w in webhooks
        ) or "<p>Nenhum webhook cadastrado.</p>"
        return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>{title}</title></head>
<body>
<h1>{title}</h1>
<div id="webhooks-list">{cards}</div>
</body></html>"""

    def get_dashboard_html(self) -> str:
        logs = self.listar_logs(limit=50)
        rows = "".join(
            f"<tr><td>{l['evento']}</td><td>{l['url']}</td><td>{l['status_code']}</td><td>{l['status']}</td></tr>"
            for l in logs
        ) or "<tr><td colspan='4'>Nenhum log registrado.</td></tr>"
        return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>Dashboard de Webhooks</title></head>
<body>
<h1>Dashboard de Webhooks</h1>
<table><thead><tr><th>Evento</th><th>URL</th><th>Status HTTP</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>"""
