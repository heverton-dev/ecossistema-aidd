import urllib.request, urllib.error, json, threading, hmac, hashlib, time, uuid, os

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
                    except:
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
            except Exception as db_err:
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
        except Exception:
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

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #060913;
            --bg-surface: #0c1222;
            --bg-elevated: #131d36;
            --bg-hover: #1b284a;
            --border: #1e293b;
            --border-light: rgba(255, 255, 255, 0.08);
            --border-focus: #38bdf8;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --text-subtle: #64748b;
            --primary: #0284c7;
            --primary-hover: #0369a1;
            --violet: #0ea5e9;
            --green: #10b981;
            --green-bg: rgba(16, 185, 129, 0.12);
            --red: #ef4444;
            --red-bg: rgba(239, 68, 68, 0.12);
            --amber: #f59e0b;
            --amber-bg: rgba(245, 158, 11, 0.12);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-base); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
        
        header {{
            background: rgba(12, 18, 34, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 0 1.5rem;
            min-height: 56px;
            height: 56px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 50;
            gap: 1rem;
            width: 100%;
            white-space: nowrap;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-weight: 700;
            font-size: 0.95rem;
            text-decoration: none;
            color: var(--text-main);
            flex-shrink: 0;
        }}
        .badge-ver {{
            background: rgba(14, 165, 233, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(14, 165, 233, 0.4);
            font-size: 0.68rem;
            font-weight: 700;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            text-transform: uppercase;
            flex-shrink: 0;
        }}
        .nav-tabs {{
            display: flex;
            gap: 0.35rem;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.25rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            flex-shrink: 0;
        }}
        .nav-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            font-weight: 600;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.15s ease;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        .nav-btn:hover {{ color: var(--text-main); background: rgba(255, 255, 255, 0.04); }}
        .nav-btn.active {{ color: #ffffff; background: var(--primary); }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 0.48rem 0.95rem;
            border-radius: var(--radius-sm);
            cursor: pointer;
            text-decoration: none;
            border: 1px solid var(--border);
            background: var(--bg-surface);
            color: var(--text-main);
        }}
        .btn-primary {{ background: var(--primary); border-color: var(--primary); color: #fff; }}
        .btn-primary:hover {{ background: var(--primary-hover); }}

        main {{ flex: 1; padding: 2rem; max-width: 1350px; width: 100%; margin: 0 auto; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }}
        .stat-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
        }}
        .stat-title {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }}
        .stat-val {{ font-size: 1.8rem; font-weight: 800; color: var(--text-main); margin-top: 0.25rem; }}

        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .panel {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            overflow: hidden;
            margin-bottom: 1.5rem;
        }}
        .panel-header {{
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .panel-title {{ font-size: 1rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; }}
        .panel-desc {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; }}

        table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
        th {{ background: var(--bg-elevated); padding: 0.75rem 1.25rem; text-align: left; color: var(--text-muted); font-weight: 700; border-bottom: 1px solid var(--border); }}
        td {{ padding: 0.85rem 1.25rem; border-bottom: 1px solid var(--border-light); }}
        tr:hover td {{ background: var(--bg-hover); }}

        .badge {{
            display: inline-flex;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .badge-event {{ background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); }}
        .badge-success {{ background: var(--green-bg); color: #34d399; }}
        .badge-danger {{ background: var(--red-bg); color: #f87171; }}
        .code-pill {{ font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; background: rgba(0,0,0,0.4); padding: 0.2rem 0.4rem; border-radius: 4px; }}

        .playground-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
        .form-group {{ margin-bottom: 1rem; }}
        .form-label {{ display: block; font-size: 0.78rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.35rem; }}
        .form-control {{
            width: 100%;
            background: var(--bg-base);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 0.6rem 0.85rem;
            border-radius: var(--radius-sm);
            font-size: 0.82rem;
            outline: none;
        }}
        .form-control:focus {{ border-color: var(--border-focus); }}
        .console-box {{
            background: #020617;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.85rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: #94a3b8;
            overflow-x: auto;
            white-space: pre-wrap;
        }}

        /* MODAL */
        .modal-overlay {{
            position: fixed; inset: 0; background: rgba(2, 6, 23, 0.8); backdrop-filter: blur(4px);
            display: none; align-items: center; justify-content: center; z-index: 100; p: 1rem;
        }}
        .modal-overlay.active {{ display: flex; }}
        .modal-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); width: 100%; max-width: 580px; overflow: hidden; }}
        .modal-header {{ padding: 1.2rem 1.5rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }}
        .modal-body {{ padding: 1.5rem; }}
        .modal-footer {{ padding: 1rem 1.5rem; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 0.6rem; }}

        #toast {{
            position: fixed; bottom: 2rem; right: 2rem; background: var(--green); color: #fff;
            padding: 0.75rem 1.25rem; border-radius: var(--radius-sm); font-size: 0.82rem; font-weight: 600;
            display: none; align-items: center; gap: 0.5rem; z-index: 200; box-shadow: var(--shadow-lg);
        }}
    </style>
</head>
<body>
    <header>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <a href="/webhooks" class="brand">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                AIDD Webhook Studio
            </a>
            <span class="badge-ver">v5.1 Event Engine</span>
        </div>

        <nav class="nav-tabs">
            <button class="nav-btn active" onclick="switchTab('endpoints', event)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                Endpoints
            </button>
            <button class="nav-btn" onclick="switchTab('playground', event)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Simulador & Testes
            </button>
            <button class="nav-btn" onclick="switchTab('logs', event)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                Auditoria & Logs
            </button>
            <button class="nav-btn" onclick="switchTab('catalog', event)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                Catálogo de Eventos
            </button>
        </nav>

        <!-- BUSCA RÁPIDA / Ctrl + K -->
        <div style="position: relative; display: flex; align-items: center; min-width: 260px;">
            <svg style="position: absolute; left: 0.65rem; color: var(--text-muted); pointer-events: none;" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" id="wh-global-search" placeholder="Filtrar eventos e logs (Ctrl + K)..." oninput="filtrarWebhookStudio(this.value)" class="form-control" style="padding-left: 2rem; padding-right: 3.5rem; font-size: 0.75rem; height: 32px;">
            <kbd style="position: absolute; right: 0.5rem; font-size: 0.65rem; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 4px; padding: 0.1rem 0.35rem; color: var(--text-muted); font-family: monospace; pointer-events: none;">Ctrl K</kbd>
        </div>

        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <a href="/" class="btn">Super-App</a>
            <a href="/docs" class="btn">Swagger Studio</a>
            <a href="/mcp" class="btn">MCP Native</a>
        </div>
    </header>

    <main>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-title">Endpoints Cadastrados</span>
                <span class="stat-val" id="stat-endpoints">0</span>
            </div>
            <div class="stat-card">
                <span class="stat-title">Disparos de Webhook</span>
                <span class="stat-val" id="stat-total-logs" style="color: var(--violet);">0</span>
            </div>
            <div class="stat-card">
                <span class="stat-title">Taxa de Entrega (2xx)</span>
                <span class="stat-val" id="stat-success-rate" style="color: var(--green);">100%</span>
            </div>
            <div class="stat-card">
                <span class="stat-title">Assinatura HMAC</span>
                <span class="stat-val" style="color: #38bdf8; font-size: 1.2rem; margin-top: 0.3rem;">SHA-256</span>
            </div>
        </div>

        <!-- ABA 1: ENDPOINTS -->
        <div id="tab-endpoints" class="tab-content active">
            <div class="panel">
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Destinos & Webhooks Configurados</div>
                        <div class="panel-desc">Endpoints cadastrados para recepção de eventos transacionais em tempo real da suíte.</div>
                    </div>
                    <button class="btn btn-primary" onclick="abrirModalCriar()">+ Novo Endpoint</button>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>URL de Destino</th>
                                <th>Eventos Assinados</th>
                                <th>Secret HMAC</th>
                                <th>Status</th>
                                <th style="text-align: right;">Ações</th>
                            </tr>
                        </thead>
                        <tbody id="lista-endpoints">
                            <tr><td colspan="5" style="text-align: center; color: var(--text-subtle);">Carregando endpoints...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ABA 2: SIMULADOR DE TESTES -->
        <div id="tab-playground" class="tab-content">
            <div class="playground-grid">
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">Emissor de Disparo Simulado</div>
                    </div>
                    <div style="padding: 1.5rem;">
                        <div class="form-group">
                            <label class="form-label">Carregar de Endpoint Cadastrado</label>
                            <select id="play-select-wh" class="form-control" onchange="preencherPlayground(this.value)">
                                <option value="">-- Selecione ou digite manualmente --</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">URL de Destino (POST)</label>
                            <input type="url" id="play-url" class="form-control" placeholder="https://webhook.site/..." required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Secret Token (Assinatura HMAC)</label>
                            <input type="text" id="play-secret" class="form-control" placeholder="sec_aidd_suite_2026">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Tópico do Evento da Plataforma</label>
                            <select id="play-evento" class="form-control" onchange="trocarTemplateEvento(this.value)">
                                {event_options}
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Payload JSON (data)</label>
                            <textarea id="play-payload" class="form-control" rows="6"></textarea>
                        </div>
                        <button class="btn btn-primary" style="width: 100%; justify-content: center;" onclick="executarTesteDisparo()">
                            Disparar Webhook Agora
                        </button>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">Resposta & Headers do Envio</div>
                        <span id="play-badge-status" class="badge" style="background: rgba(255,255,255,0.08);">Aguardando Disparo</span>
                    </div>
                    <div style="padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
                        <div>
                            <label class="form-label">Headers HTTP Calculados</label>
                            <div id="play-headers" class="console-box" style="height: 110px;">// Execute um disparo para visualizar headers</div>
                        </div>
                        <div>
                            <label class="form-label">Corpo de Resposta do Receptor</label>
                            <div id="play-response" class="console-box" style="height: 180px;">// O payload de resposta aparecerá aqui</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ABA 3: AUDITORIA E LOGS -->
        <div id="tab-logs" class="tab-content">
            <div class="panel">
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Auditoria de Disparos de Webhook</div>
                        <div class="panel-desc">Histórico cronológico de requisições, status HTTP e latência em milissegundos.</div>
                    </div>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Data / Hora</th>
                                <th>Evento</th>
                                <th>Destino (URL)</th>
                                <th>Status HTTP</th>
                                <th>Latência</th>
                                <th style="text-align: right;">Ações</th>
                            </tr>
                        </thead>
                        <tbody id="lista-logs">
                            <tr><td colspan="6" style="text-align: center; color: var(--text-subtle);">Carregando logs...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ABA 4: CATÁLOGO DE EVENTOS -->
        <div id="tab-catalog" class="tab-content">
            <div class="panel">
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Catálogo Oficial de Eventos da Suíte Enterprise</div>
                        <div class="panel-desc">Tópicos canônicos de eventos emitidos pelas fatias verticais e pelo EventBus.</div>
                    </div>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Tópico do Evento</th>
                                <th>Módulo</th>
                                <th>Descrição da Ação</th>
                                <th>Payload Canônico</th>
                            </tr>
                        </thead>
                        <tbody>
                            {catalog_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </main>

    <!-- MODAL NOVO ENDPOINT -->
    <div id="modal-endpoint" class="modal-overlay">
        <div class="modal-card">
            <div class="modal-header">
                <div class="panel-title">Novo Webhook Endpoint</div>
                <button class="btn" onclick="fecharModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">URL de Destino (HTTPS)</label>
                    <input type="url" id="wh-url" class="form-control" placeholder="https://webhook.site/demo" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Secret Token HMAC</label>
                    <input type="text" id="wh-secret" class="form-control" placeholder="sec_aidd_suite_2026">
                </div>
                <div class="form-group">
                    <label class="form-label">Eventos Assinados da Plataforma</label>
                    <div style="display: grid; grid-template-columns: 1fr; gap: 0.4rem; font-size: 0.8rem; background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: var(--radius-sm); max-height: 180px; overflow-y: auto;">
                        {modal_checkboxes}
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn" onclick="fecharModal()">Cancelar</button>
                <button class="btn btn-primary" onclick="salvarEndpoint()">Salvar Endpoint</button>
            </div>
        </div>
    </div>

    <!-- TOAST -->
    <div id="toast">
        <span id="toast-msg">Sucesso</span>
    </div>

    <script>
        let endpointsData = [];
        let logsData = [];
        const EVENT_TEMPLATES = {event_templates_json};

        function switchTab(tabId, ev) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            if (ev) ev.currentTarget.classList.add('active');

            if (tabId === 'endpoints') carregarEndpoints();
            if (tabId === 'logs') carregarLogs();
        }}

        function showToast(msg) {{
            const t = document.getElementById('toast');
            document.getElementById('toast-msg').textContent = msg;
            t.style.display = 'flex';
            setTimeout(() => {{ t.style.display = 'none'; }}, 3000);
        }}

        function abrirModalCriar() {{
            document.getElementById('wh-url').value = '';
            document.getElementById('wh-secret').value = 'sec_aidd_' + Math.random().toString(36).substring(2, 10);
            document.querySelectorAll('input[name="wh-ev"]').forEach(cb => cb.checked = false);
            document.getElementById('modal-endpoint').classList.add('active');
        }}

        function fecharModal() {{
            document.getElementById('modal-endpoint').classList.remove('active');
        }}

        async function carregarEndpoints() {{
            try {{
                const res = await fetch('/api/webhooks');
                endpointsData = await res.json();
                document.getElementById('stat-endpoints').textContent = endpointsData.length;
                const selectWh = document.getElementById('play-select-wh');
                selectWh.innerHTML = '<option value="">-- Selecione ou digite manualmente --</option>';

                const tbody = document.getElementById('lista-endpoints');
                if (endpointsData.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-subtle);">Nenhum webhook cadastrado.</td></tr>';
                    return;
                }}

                let html = '';
                endpointsData.forEach(wh => {{
                    selectWh.innerHTML += `<option value="${{wh.id}}">${{wh.url}}</option>`;
                    html += `<tr>
                        <td style="font-family: monospace; font-size: 0.8rem; font-weight: bold; color: #38bdf8;">${{wh.url}}</td>
                        <td><span class="badge badge-event">${{wh.eventos}}</span></td>
                        <td><span class="code-pill">${{wh.secret ? '••••••••' : 'Sem Secret'}}</span></td>
                        <td><span class="badge badge-success">Ativo</span></td>
                        <td style="text-align: right;">
                            <button class="btn" style="color: var(--red); border-color: rgba(239,68,68,0.3);" onclick="excluirEndpoint(${{wh.id}})">Excluir</button>
                        </td>
                    </tr>`;
                }});
                tbody.innerHTML = html;
            }} catch (err) {{
                console.error(err);
            }}
        }}

        async function salvarEndpoint() {{
            const url = document.getElementById('wh-url').value.trim();
            const secret = document.getElementById('wh-secret').value.trim();
            const checkboxes = document.querySelectorAll('input[name="wh-ev"]:checked');
            const eventos = Array.from(checkboxes).map(cb => cb.value);

            if (!url) {{
                alert('Informe a URL do Webhook.');
                return;
            }}

            const payload = {{
                url,
                secret,
                eventos: eventos.length > 0 ? eventos.join(',') : '*'
            }};

            const res = await fetch('/api/webhooks', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(payload)
            }});

            const data = await res.json();
            if (data.sucesso) {{
                fecharModal();
                showToast('Webhook cadastrado com sucesso!');
                carregarEndpoints();
            }} else {{
                alert('Erro: ' + (data.error || 'Falha ao salvar'));
            }}
        }}

        async function excluirEndpoint(id) {{
            if (!confirm('Deseja realmente remover este webhook?')) return;
            const res = await fetch('/api/webhooks/remover', {{
                method: 'DELETE',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ id }})
            }});
            const data = await res.json();
            if (data.sucesso) {{
                showToast('Webhook removido.');
                carregarEndpoints();
            }}
        }}

        function preencherPlayground(whId) {{
            if (!whId) return;
            const wh = endpointsData.find(w => w.id == whId);
            if (!wh) return;
            document.getElementById('play-url').value = wh.url;
            document.getElementById('play-secret').value = wh.secret;
        }}

        function trocarTemplateEvento(ev) {{
            const tmpl = EVENT_TEMPLATES[ev] || {{ "mensagem": "Disparo de Teste", "evento": ev }};
            document.getElementById('play-payload').value = JSON.stringify(tmpl, null, 2);
        }}

        async function executarTesteDisparo() {{
            const url = document.getElementById('play-url').value.trim();
            const secret = document.getElementById('play-secret').value.trim();
            const evento = document.getElementById('play-evento').value;
            let payload = {{}};

            try {{
                payload = JSON.parse(document.getElementById('play-payload').value);
            }} catch(e) {{
                alert('JSON inválido no payload.');
                return;
            }}

            const badgeStatus = document.getElementById('play-badge-status');
            badgeStatus.textContent = 'Enviando...';

            try {{
                const res = await fetch('/api/webhooks/testar', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ url, secret, evento, payload }})
                }});
                const data = await res.json();

                if (data.sucesso) {{
                    badgeStatus.className = 'badge badge-success';
                    badgeStatus.textContent = `200 OK (${{data.duracao_ms}}ms)`;
                    showToast('Disparo de teste entregue!');
                }} else {{
                    badgeStatus.className = 'badge badge-danger';
                    badgeStatus.textContent = `Falha: ${{data.status_code || 'Erro'}} (${{data.duracao_ms}}ms)`;
                }}

                document.getElementById('play-headers').textContent = JSON.stringify(data.headers_enviados, null, 2);
                document.getElementById('play-response').textContent = data.resposta_recebida || '(Sem resposta do servidor)';
                carregarLogs();
            }} catch (err) {{
                badgeStatus.className = 'badge badge-danger';
                badgeStatus.textContent = 'Erro de Rede';
                document.getElementById('play-response').textContent = String(err);
            }}
        }}

        async function carregarLogs() {{
            try {{
                const res = await fetch('/api/webhooks/logs');
                logsData = await res.json();
                document.getElementById('stat-total-logs').textContent = logsData.length;

                if (logsData.length > 0) {{
                    const sucs = logsData.filter(l => l.sucesso == 1).length;
                    const rate = Math.round((sucs / logsData.length) * 100);
                    document.getElementById('stat-success-rate').textContent = rate + '%';
                }}

                const tbody = document.getElementById('lista-logs');
                if (logsData.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-subtle);">Nenhum log gravado ainda.</td></tr>';
                    return;
                }}

                let html = '';
                logsData.forEach(log => {{
                    const badge = log.sucesso == 1 
                        ? `<span class="badge badge-success">${{log.status_code || 200}} OK</span>`
                        : `<span class="badge badge-danger">${{log.status_code || 'Erro'}}</span>`;

                    html += `<tr>
                        <td style="font-size: 0.78rem; color: var(--text-muted);">${{log.criado_em}}</td>
                        <td><span class="badge badge-event">${{log.evento}}</span></td>
                        <td style="font-family: monospace; font-size: 0.78rem;">${{log.url}}</td>
                        <td>${{badge}}</td>
                        <td><span class="code-pill">${{log.status_code ? '200ms' : '-'}}</span></td>
                        <td style="text-align: right;">
                            <button class="btn" onclick="reenviarLog(${{log.id}})">Reenviar</button>
                        </td>
                    </tr>`;
                }});
                tbody.innerHTML = html;
            }} catch(err) {{
                console.error(err);
            }}
        }}

        async function reenviarLog(logId) {{
            const res = await fetch('/api/webhooks/logs/reenviar', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ log_id: logId }})
            }});
            const data = await res.json();
            if (data.sucesso) {{
                showToast('Webhook reenviado!');
                carregarLogs();
            }} else {{
                alert('Erro ao reenviar: ' + (data.error || 'Falha'));
            }}
        }}

        // SPOTLIGHT COMMAND PALETTE PARA WEBHOOK STUDIO (ZERO EMOJIS)
        let spotlightSelectedIndex = 0;
        let spotlightFilteredCommands = [];

        function getWebhookIconSvg(type) {{
            const icons = {{
                app: '<svg width="16" height="16" fill="none" stroke="#38bdf8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
                docs: '<svg width="16" height="16" fill="none" stroke="#38bdf8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
                webhooks: '<svg width="16" height="16" fill="none" stroke="#f59e0b" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
                mcp: '<svg width="16" height="16" fill="none" stroke="#a855f7" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>',
                guia: '<svg width="16" height="16" fill="none" stroke="#10b981" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>',
                plus: '<svg width="16" height="16" fill="none" stroke="#38bdf8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>',
                rocket: '<svg width="16" height="16" fill="none" stroke="#f59e0b" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
                logs: '<svg width="16" height="16" fill="none" stroke="#a855f7" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
                catalog: '<svg width="16" height="16" fill="none" stroke="#10b981" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>'
            }};
            return icons[type] || '<svg width="16" height="16" fill="none" stroke="#94a3b8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>';
        }}

        function getSpotlightCommands() {{
            return [
                {{ id: 'nav-app', cat: 'Navegação', title: 'Super-App Clínico (Home)', desc: 'Dashboard e painéis do Super-App', iconType: 'app', action: () => {{ window.location.href = '/'; }} }},
                {{ id: 'nav-docs', cat: 'Navegação', title: 'Swagger Studio (OpenAPI)', desc: 'Documentação interativa REST e live playground', iconType: 'docs', action: () => {{ window.location.href = '/docs'; }} }},
                {{ id: 'nav-wh', cat: 'Navegação', title: 'Webhook Studio', desc: 'Simulador de eventos e logs de webhook', iconType: 'webhooks', action: () => {{ window.location.href = '/webhooks'; }} }},
                {{ id: 'nav-mcp', cat: 'Navegação', title: 'MCP Native Server Portal', desc: '16 Ferramentas JSON-RPC para Claude Desktop e LLMs', iconType: 'mcp', action: () => {{ window.location.href = '/mcp'; }} }},
                {{ id: 'nav-guia', cat: 'Navegação', title: 'Manual Enciclopédico & Design System', desc: '11 Capítulos de arquitetura, segurança e UI', iconType: 'guia', action: () => {{ window.location.href = '/docs/guia'; }} }},
                {{ id: 'act-new-ep', cat: 'Ações Webhook', title: 'Cadastrar Novo Endpoint Webhook', desc: 'Registrar URL de destino com secret HMAC', iconType: 'plus', action: () => {{ openModal(); }} }},
                {{ id: 'act-tab-sim', cat: 'Ações Webhook', title: 'Abrir Simulador de Disparos', desc: 'Testar emissão de eventos empresariais', iconType: 'rocket', action: () => {{ switchTab('playground'); }} }},
                {{ id: 'act-tab-logs', cat: 'Ações Webhook', title: 'Ver Auditoria e Histórico de Logs', desc: 'Inspecionar status HTTP e payloads', iconType: 'logs', action: () => {{ switchTab('logs'); }} }},
                {{ id: 'act-tab-cat', cat: 'Ações Webhook', title: 'Ver Catálogo Oficial de Eventos', desc: 'Catálogo de eventos transacionais das fatias verticais', iconType: 'catalog', action: () => {{ switchTab('catalog'); }} }}
            ];
        }}

        function abrirSpotlight() {{
            let modal = document.getElementById('spotlight-modal');
            if (!modal) {{
                criarSpotlightDOM();
                modal = document.getElementById('spotlight-modal');
            }}
            modal.style.display = 'flex';
            const inp = document.getElementById('spotlight-input');
            inp.value = '';
            filtrarSpotlight('');
            setTimeout(() => inp.focus(), 50);
        }}

        function fecharSpotlight() {{
            const modal = document.getElementById('spotlight-modal');
            if (modal) modal.style.display = 'none';
        }}

        function criarSpotlightDOM() {{
            const div = document.createElement('div');
            div.id = 'spotlight-modal';
            div.style.cssText = 'position:fixed;inset:0;background:rgba(2,6,23,0.85);backdrop-filter:blur(8px);z-index:9999;display:none;align-items:flex-start;justify-content:center;padding-top:5rem;';
            div.onclick = (e) => {{ if (e.target === div) fecharSpotlight(); }};
            div.innerHTML = `
                <div style="background:#0f172a;border:1px solid rgba(255,255,255,0.15);border-radius:16px;width:100%;max-width:640px;box-shadow:0 25px 50px -12px rgba(0,0,0,0.7);overflow:hidden;display:flex;flex-direction:column;max-height:80vh;" onclick="event.stopPropagation()">
                    <div style="padding:1rem;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;gap:0.75rem;background:rgba(255,255,255,0.02);">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                        <input type="text" id="spotlight-input" placeholder="Buscar ações do webhook ou navegação (Ctrl + K)..." 
                               oninput="filtrarSpotlight(this.value)" onkeydown="navegarSpotlightTeclado(event)"
                               style="width:100%;background:transparent;border:none;color:#fff;font-size:0.9rem;font-weight:600;outline:none;">
                        <kbd style="font-size:0.7rem;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);padding:0.2rem 0.5rem;border-radius:4px;color:#94a3b8;cursor:pointer;" onclick="fecharSpotlight()">ESC</kbd>
                    </div>
                    <div id="spotlight-results" style="overflow-y:auto;padding:0.5rem;max-height:55vh;display:flex;flex-direction:column;gap:0.25rem;"></div>
                    <div style="padding:0.6rem 1rem;background:#020617;border-top:1px solid rgba(255,255,255,0.1);display:flex;justify-content:space-between;align-items:center;font-size:0.72rem;color:#94a3b8;">
                        <div><kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">↑</kbd> <kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">↓</kbd> Navegar • <kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">↵</kbd> Executar • <kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">ESC</kbd> Fechar</div>
                        <span style="color:#f59e0b;font-weight:bold;font-family:monospace;">Spotlight Command Palette</span>
                    </div>
                </div>`;
            document.body.appendChild(div);
        }}

        function filtrarSpotlight(q) {{
            const query = (q || '').toLowerCase().trim();
            const allCommands = getSpotlightCommands();
            spotlightFilteredCommands = allCommands.filter(cmd => 
                !query || 
                cmd.title.toLowerCase().includes(query) || 
                cmd.desc.toLowerCase().includes(query) || 
                cmd.cat.toLowerCase().includes(query)
            );
            spotlightSelectedIndex = 0;
            renderizarSpotlightResultados();
        }}

        function renderizarSpotlightResultados() {{
            const container = document.getElementById('spotlight-results');
            if (!container) return;
            if (spotlightFilteredCommands.length === 0) {{
                container.innerHTML = `<div style="padding:2rem;text-align:center;color:#64748b;font-size:0.85rem;">Nenhum comando encontrado</div>`;
                return;
            }}
            let html = '';
            let currentCat = '';
            spotlightFilteredCommands.forEach((cmd, idx) => {{
                if (cmd.cat !== currentCat) {{
                    currentCat = cmd.cat;
                    html += `<div style="font-size:0.68rem;font-weight:800;text-transform:uppercase;color:#64748b;padding:0.5rem 0.75rem 0.2rem 0.75rem;letter-spacing:0.05em;">${{currentCat}}</div>`;
                }}
                const isSelected = idx === spotlightSelectedIndex;
                const iconSvg = getWebhookIconSvg(cmd.iconType);
                html += `
                <div onclick="executarSpotlightComando(${{idx}})" 
                     style="display:flex;align-items:center;justify-content:space-between;padding:0.6rem 0.8rem;border-radius:8px;cursor:pointer;background:${{isSelected ? 'rgba(245,158,11,0.15)' : 'transparent'}};border:1px solid ${{isSelected ? 'rgba(245,158,11,0.3)' : 'transparent'}};transition:all 0.15s;">
                    <div style="display:flex;align-items:center;gap:0.6rem;min-width:0;">
                        <div style="width:28px;height:28px;border-radius:6px;background:rgba(255,255,255,0.05);display:flex;align-items:center;justify-content:center;flex-shrink:0;">${{iconSvg}}</div>
                        <div style="min-width:0;">
                            <div style="font-weight:700;font-size:0.82rem;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${{cmd.title}}</div>
                            <div style="font-size:0.72rem;color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${{cmd.desc}}</div>
                        </div>
                    </div>
                    <span style="font-size:0.68rem;color:#94a3b8;background:rgba(255,255,255,0.05);padding:0.15rem 0.4rem;border-radius:4px;flex-shrink:0;">${{cmd.cat}}</span>
                </div>`;
            }});
            container.innerHTML = html;
        }}

        function executarSpotlightComando(idx) {{
            const cmd = spotlightFilteredCommands[idx];
            if (cmd && cmd.action) {{
                fecharSpotlight();
                cmd.action();
            }}
        }}

        function navegarSpotlightTeclado(e) {{
            if (e.key === 'ArrowDown') {{
                e.preventDefault();
                if (spotlightSelectedIndex < spotlightFilteredCommands.length - 1) {{
                    spotlightSelectedIndex++;
                    renderizarSpotlightResultados();
                }}
            }} else if (e.key === 'ArrowUp') {{
                e.preventDefault();
                if (spotlightSelectedIndex > 0) {{
                    spotlightSelectedIndex--;
                    renderizarSpotlightResultados();
                }}
            }} else if (e.key === 'Enter') {{
                e.preventDefault();
                executarSpotlightComando(spotlightSelectedIndex);
            }} else if (e.key === 'Escape') {{
                e.preventDefault();
                fecharSpotlight();
            }}
        }}

        document.addEventListener('keydown', (e) => {{
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {{
                e.preventDefault();
                abrirSpotlight();
            }} else if (e.key === 'Escape') {{
                fecharSpotlight();
            }}
        }});

        function filtrarWebhookStudio(q) {{
            const query = (q || '').toLowerCase().trim();
            document.querySelectorAll('table tbody tr').forEach(tr => {{
                const text = tr.innerText.toLowerCase();
                tr.style.display = (!query || text.includes(query)) ? '' : 'none';
            }});
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            trocarTemplateEvento('{initial_event}');
            carregarEndpoints();
            carregarLogs();
        }});
    </script>
</body>
</html>"""
