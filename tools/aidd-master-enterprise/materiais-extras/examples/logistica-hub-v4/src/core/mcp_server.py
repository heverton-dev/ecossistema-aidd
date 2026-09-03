import sys, json, os, sqlite3, uuid

class LogisticaMCPServer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.tools = {
            # 1. FROTAS
            "frotas_listar_veiculos": {
                "description": "Lista todos os veículos da frota, motoristas, capacidade em KG e status operacional.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            "frotas_cadastrar_veiculo": {
                "description": "Cadastra um novo caminhão ou utilitário na frota com placa e capacidade.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "placa": {"type": "string", "description": "Placa do veículo (ex: BRA2E19)"},
                        "modelo": {"type": "string", "description": "Modelo do caminhão"},
                        "motorista": {"type": "string", "description": "Nome do motorista responsável"},
                        "capacidade_kg": {"type": "number", "description": "Capacidade de carga em KG"}
                    },
                    "required": ["placa", "modelo", "motorista", "capacidade_kg"]
                }
            },
            "frotas_alternar_status": {
                "description": "Alterna ciclicamente o status do caminhão (disponivel, em_rota, manutencao).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do veículo"}
                    },
                    "required": ["id"]
                }
            },
            "frotas_excluir_veiculo": {
                "description": "Remove um veículo da frota de transporte.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do veículo a ser excluído"}
                    },
                    "required": ["id"]
                }
            },

            # 2. ENTREGAS
            "entregas_listar": {
                "description": "Lista todas as ordens de transporte e remessas em tempo real.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            "entregas_criar_remessa": {
                "description": "Cria uma nova remessa de entrega com código de rastreamento e valor de frete.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "destinatario": {"type": "string", "description": "Nome do cliente destinatário"},
                        "cidade_destino": {"type": "string", "description": "Cidade e UF de destino"},
                        "valor_frete": {"type": "number", "description": "Valor monetário do frete em BRL"},
                        "peso_kg": {"type": "number", "description": "Peso total da carga em KG"}
                    },
                    "required": ["destinatario", "cidade_destino", "valor_frete", "peso_kg"]
                }
            },
            "entregas_atualizar_status": {
                "description": "Atualiza o status da entrega (pendente, em_transito, entregue). Dispara faturamento se 'entregue'.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entrega_id": {"type": "integer", "description": "ID da entrega"},
                        "novo_status": {"type": "string", "description": "pendente, em_transito, entregue"}
                    },
                    "required": ["entrega_id", "novo_status"]
                }
            },
            "entregas_excluir_remessa": {
                "description": "Cancela ou remove uma remessa de entrega.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID da entrega a ser cancelada"}
                    },
                    "required": ["id"]
                }
            },

            # 3. WMS
            "wms_consultar_estoque": {
                "description": "Consulta os itens e saldo de estoque no armazém WMS com posições de palete.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            "wms_adicionar_item": {
                "description": "Cadastra uma nova mercadoria no estoque WMS com SKU e posição de palete.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sku": {"type": "string", "description": "Código SKU único"},
                        "descricao": {"type": "string", "description": "Descrição do material"},
                        "posicao_palete": {"type": "string", "description": "Endereçamento WMS (ex: RUA-A-04)"},
                        "quantidade": {"type": "integer", "description": "Quantidade física de unidades"},
                        "valor_unitario": {"type": "number", "description": "Valor unitário em BRL"}
                    },
                    "required": ["sku", "descricao", "posicao_palete", "quantidade", "valor_unitario"]
                }
            },
            "wms_ajustar_estoque": {
                "description": "Ajusta o saldo físico ou a posição de palete de um item no WMS.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do item WMS"},
                        "quantidade": {"type": "integer", "description": "Nova quantidade física"},
                        "posicao_palete": {"type": "string", "description": "Nova posição (opcional)"}
                    },
                    "required": ["id", "quantidade"]
                }
            },
            "wms_excluir_item": {
                "description": "Dá baixa total ou remove um item do armazém WMS.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do item no WMS"}
                    },
                    "required": ["id"]
                }
            },

            # 4. FINANCEIRO
            "financeiro_listar_fretes": {
                "description": "Lista todas as faturas de fretes recebidos e despesas operacionais.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            "financeiro_lancar_movimentacao": {
                "description": "Registra uma receita de frete ou despesa operacional (Diesel, Pedágio, Manutenção).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tipo": {"type": "string", "description": "'receita' ou 'despesa'"},
                        "descricao": {"type": "string", "description": "Descrição da operação"},
                        "categoria": {"type": "string", "description": "Categoria contábil"},
                        "valor": {"type": "number", "description": "Valor em BRL"},
                        "data_vencimento": {"type": "string", "description": "Data YYYY-MM-DD"}
                    },
                    "required": ["tipo", "descricao", "valor", "data_vencimento"]
                }
            },
            "financeiro_alternar_status": {
                "description": "Alterna o status de quitação financeiro entre 'pago' e 'pendente'.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do lançamento financeiro"}
                    },
                    "required": ["id"]
                }
            },
            "financeiro_excluir_lancamento": {
                "description": "Exclui um lançamento do razão financeiro.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do lançamento"}
                    },
                    "required": ["id"]
                }
            },

            # 5. SUPORTE SLA
            "suporte_listar_incidentes": {
                "description": "Lista todos os chamados de socorro mecânico e incidentes de transporte com SLA.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            "suporte_abrir_incidente": {
                "description": "Abre um chamado de suporte operacional / pane mecânica com prioridade P1/P2/P3 e SLA.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string", "description": "Título do incidente"},
                        "veiculo_placa": {"type": "string", "description": "Placa do caminhão envolvido"},
                        "prioridade": {"type": "string", "description": "P1 (2h), P2 (4h) ou P3 (24h)"}
                    },
                    "required": ["titulo", "prioridade"]
                }
            },
            "suporte_resolver_incidente": {
                "description": "Encerra e marca o chamado de suporte como 'resolvido'.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do incidente"}
                    },
                    "required": ["id"]
                }
            },
            "suporte_excluir_incidente": {
                "description": "Remove um chamado de incidente do histórico.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "ID do incidente"}
                    },
                    "required": ["id"]
                }
            }
        }

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def handle_call_tool(self, name: str, args: dict) -> dict:
        with self._get_conn() as conn:
            # 1. FROTAS
            if name == "frotas_listar_veiculos":
                veics = [dict(r) for r in conn.execute("SELECT * FROM veiculos ORDER BY id DESC").fetchall()]
                return {"content": [{"type": "text", "text": json.dumps(veics, ensure_ascii=False, indent=2)}]}

            elif name == "frotas_cadastrar_veiculo":
                conn.execute("INSERT INTO veiculos (placa, modelo, motorista, capacidade_kg, status) VALUES (?, ?, ?, ?, 'disponivel')",
                             (args["placa"].upper(), args["modelo"], args["motorista"], float(args["capacidade_kg"])))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Veículo {args['placa'].upper()} cadastrado com sucesso!"}]}

            elif name == "frotas_alternar_status":
                vid = int(args["id"])
                row = conn.execute("SELECT status, placa FROM veiculos WHERE id = ?", (vid,)).fetchone()
                if not row:
                    return {"isError": True, "content": [{"type": "text", "text": "Veículo não encontrado"}]}
                novo_st = "em_rota" if row[0] == "disponivel" else ("manutencao" if row[0] == "em_rota" else "disponivel")
                conn.execute("UPDATE veiculos SET status = ? WHERE id = ?", (novo_st, vid))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Status do veículo {row[1]} atualizado para {novo_st.upper()}!"}]}

            elif name == "frotas_excluir_veiculo":
                conn.execute("DELETE FROM veiculos WHERE id = ?", (int(args["id"]),))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Veículo #{args['id']} excluído da frota!"}]}

            # 2. ENTREGAS
            elif name == "entregas_listar":
                entregas = [dict(r) for r in conn.execute("SELECT * FROM entregas ORDER BY id DESC").fetchall()]
                return {"content": [{"type": "text", "text": json.dumps(entregas, ensure_ascii=False, indent=2)}]}

            elif name == "entregas_criar_remessa":
                cod = f"BR-LOG-{uuid.uuid4().hex[:4].upper()}"
                conn.execute("INSERT INTO entregas (codigo_rastreio, destinatario, cidade_destino, valor_frete, peso_kg, status) VALUES (?, ?, ?, ?, ?, 'pendente')",
                             (cod, args["destinatario"], args["cidade_destino"], float(args["valor_frete"]), float(args["peso_kg"])))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Remessa criada! Código de Rastreamento: {cod}"}]}

            elif name == "entregas_atualizar_status":
                conn.execute("UPDATE entregas SET status = ? WHERE id = ?", (args["novo_status"], int(args["entrega_id"])))
                conn.commit()
                if args["novo_status"] == "entregue":
                    row = conn.execute("SELECT * FROM entregas WHERE id = ?", (int(args["entrega_id"]),)).fetchone()
                    if row:
                        conn.execute("INSERT INTO fretes_financeiro (tipo, descricao, valor, status, data_vencimento) VALUES ('receita', ?, ?, 'pago', date('now'))",
                                     (f"Faturamento Frete {row['codigo_rastreio']}", float(row['valor_frete'])))
                        conn.commit()
                return {"content": [{"type": "text", "text": f"Entrega #{args['entrega_id']} atualizada para {args['novo_status'].upper()}!"}]}

            elif name == "entregas_excluir_remessa":
                conn.execute("DELETE FROM entregas WHERE id = ?", (int(args["id"]),))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Remessa #{args['id']} cancelada e excluída!"}]}

            # 3. WMS
            elif name == "wms_consultar_estoque":
                itens = [dict(r) for r in conn.execute("SELECT * FROM estoque_wms ORDER BY id DESC").fetchall()]
                return {"content": [{"type": "text", "text": json.dumps(itens, ensure_ascii=False, indent=2)}]}

            elif name == "wms_adicionar_item":
                conn.execute("INSERT INTO estoque_wms (sku, descricao, posicao_palete, quantidade, valor_unitario) VALUES (?, ?, ?, ?, ?)",
                             (args["sku"].upper(), args["descricao"], args["posicao_palete"].upper(), int(args["quantidade"]), float(args["valor_unitario"])))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Item SKU {args['sku'].upper()} adicionado no WMS!"}]}

            elif name == "wms_ajustar_estoque":
                iid = int(args["id"])
                qtd = int(args["quantidade"])
                pos = args.get("posicao_palete")
                if pos:
                    conn.execute("UPDATE estoque_wms SET quantidade = ?, posicao_palete = ? WHERE id = ?", (qtd, pos.upper(), iid))
                else:
                    conn.execute("UPDATE estoque_wms SET quantidade = ? WHERE id = ?", (qtd, iid))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Estoque WMS #{iid} ajustado para {qtd} unidades!"}]}

            elif name == "wms_excluir_item":
                conn.execute("DELETE FROM estoque_wms WHERE id = ?", (int(args["id"]),))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Item #{args['id']} baixado do estoque WMS!"}]}

            # 4. FINANCEIRO
            elif name == "financeiro_listar_fretes":
                fretes = [dict(r) for r in conn.execute("SELECT * FROM fretes_financeiro ORDER BY id DESC").fetchall()]
                return {"content": [{"type": "text", "text": json.dumps(fretes, ensure_ascii=False, indent=2)}]}

            elif name == "financeiro_lancar_movimentacao":
                conn.execute("INSERT INTO fretes_financeiro (tipo, descricao, categoria, valor, status, data_vencimento) VALUES (?, ?, ?, ?, 'pendente', ?)",
                             (args["tipo"], args["descricao"], args.get("categoria", "Geral"), float(args["valor"]), args["data_vencimento"]))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Lançamento financeiro de {args['tipo'].upper()} registrado com sucesso!"}]}

            elif name == "financeiro_alternar_status":
                fid = int(args["id"])
                row = conn.execute("SELECT status FROM fretes_financeiro WHERE id = ?", (fid,)).fetchone()
                if not row:
                    return {"isError": True, "content": [{"type": "text", "text": "Lançamento não encontrado"}]}
                novo_st = "pago" if row[0] == "pendente" else "pendente"
                conn.execute("UPDATE fretes_financeiro SET status = ? WHERE id = ?", (novo_st, fid))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Status financeiro #{fid} alterado para {novo_st.upper()}!"}]}

            elif name == "financeiro_excluir_lancamento":
                conn.execute("DELETE FROM fretes_financeiro WHERE id = ?", (int(args["id"]),))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Lançamento #{args['id']} excluído!"}]}

            # 5. SUPORTE SLA
            elif name == "suporte_listar_incidentes":
                incs = [dict(r) for r in conn.execute("SELECT * FROM incidentes_sla ORDER BY id DESC").fetchall()]
                return {"content": [{"type": "text", "text": json.dumps(incs, ensure_ascii=False, indent=2)}]}

            elif name == "suporte_abrir_incidente":
                proto = f"INC-{uuid.uuid4().hex[:6].upper()}"
                prio = args.get("prioridade", "P3").upper()
                sla = 2 if prio == "P1" else (4 if prio == "P2" else 24)
                conn.execute("INSERT INTO incidentes_sla (protocolo, titulo, veiculo_placa, prioridade, status, sla_horas) VALUES (?, ?, ?, ?, 'aberto', ?)",
                             (proto, args["titulo"], args.get("veiculo_placa", "N/A"), prio, sla))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Incidente aberto! Protocolo: {proto} (SLA: {sla}h)"}]}

            elif name == "suporte_resolver_incidente":
                conn.execute("UPDATE incidentes_sla SET status = 'resolvido' WHERE id = ?", (int(args["id"]),))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Incidente #{args['id']} marcado como RESOLVIDO!"}]}

            elif name == "suporte_excluir_incidente":
                conn.execute("DELETE FROM incidentes_sla WHERE id = ?", (int(args["id"]),))
                conn.commit()
                return {"content": [{"type": "text", "text": f"Incidente #{args['id']} excluído do histórico!"}]}

            else:
                return {"isError": True, "content": [{"type": "text", "text": f"Ferramenta desconhecida: {name}"}]}

    def process_rpc(self, request: dict) -> dict:
        method = request.get("method")
        msg_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "logistica-hub-mcp", "version": "4.0.0"}
                }
            }

        elif method == "tools/list":
            tools_list = []
            for name, meta in self.tools.items():
                tools_list.append({
                    "name": name,
                    "description": meta["description"],
                    "inputSchema": meta["inputSchema"]
                })
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": tools_list}
            }

        elif method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            res = self.handle_call_tool(name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": res
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Método desconhecido: {method}"}
            }

    def handle_json_rpc(self, req: dict) -> dict:
        return self.process_rpc(req)

    def get_portal_html(self) -> str:
        tools_cards = ""
        for name, meta in self.tools.items():
            schema_pretty = json.dumps(meta["inputSchema"], indent=2, ensure_ascii=False)
            tools_cards += f"""
            <div class="mcp-card">
                <div class="mcp-tool-header">
                    <span class="mcp-tool-badge">TOOL</span>
                    <span class="mcp-tool-name">{name}</span>
                </div>
                <p class="mcp-tool-desc">{meta['description']}</p>
                <div class="mcp-schema-box">
                    <pre>{schema_pretty}</pre>
                </div>
                <button class="btn btn-primary" style="margin-top: 1rem; width: 100%; justify-content: center;" onclick="prepararTesteTool('{name}')">Testar no Playground MCP</button>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal MCP Universal — Logística Hub v5.1</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #020617;
            --surface: #050b18;
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.16);
            --primary: #3b82f6;
            --primary-light: #60a5fa;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --code-bg: #010409;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}

        /* SCROLLBAR 4PX */
        * {{ scrollbar-width: thin; scrollbar-color: rgba(59, 130, 246, 0.4) transparent; }}
        ::-webkit-scrollbar {{ width: 4px !important; height: 4px !important; }}
        ::-webkit-scrollbar-track {{ background: transparent !important; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(59, 130, 246, 0.35) !important; border-radius: 9999px !important; }}

        /* BOTÃO LINHA ÚNICA */
        button, .btn, .btn-primary {{
            white-space: nowrap !important;
            text-overflow: ellipsis;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            line-height: 1.2 !important;
        }}

        body {{ background: var(--bg); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; }}

        header {{
            min-height: 60px;
            height: 60px;
            background: rgba(3, 7, 18, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1.5rem;
            position: sticky;
            top: 0;
            z-index: 50;
            gap: 1rem;
            white-space: nowrap;
            overflow-x: auto;
            scrollbar-width: none;
        }}
        header::-webkit-scrollbar {{ display: none; }}

        .brand {{ font-weight: 800; font-size: 1.05rem; display: flex; align-items: center; gap: 0.6rem; color: #fff; flex-shrink: 0; }}
        .btn {{ padding: 0.45rem 0.9rem; border-radius: 8px; font-size: 0.82rem; font-weight: 700; border: 1px solid var(--border); background: rgba(255, 255, 255, 0.04); color: #fff; text-decoration: none; cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem; transition: all 0.15s; }}
        .btn:hover {{ background: rgba(255, 255, 255, 0.08); border-color: var(--border-hover); }}
        .btn-primary {{ background: var(--primary); border-color: var(--primary); }}

        main {{ max-width: 1300px; width: 100%; margin: 0 auto; padding: 2.5rem 1.5rem; flex: 1; }}
        .banner {{ background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 14px; padding: 1.5rem; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; }}
        .tools-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }}
        .mcp-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; display: flex; flex-direction: column; justify-content: space-between; }}
        .mcp-tool-header {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.6rem; }}
        .mcp-tool-badge {{ background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; font-size: 0.68rem; font-weight: 800; padding: 0.15rem 0.4rem; border-radius: 4px; font-family: 'JetBrains Mono', monospace; }}
        .mcp-tool-name {{ font-weight: 800; font-size: 1.05rem; color: #fff; font-family: 'JetBrains Mono', monospace; }}
        .mcp-tool-desc {{ font-size: 0.86rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 1rem; }}
        .mcp-schema-box {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; padding: 0.8rem; max-height: 140px; overflow-y: auto; }}
        .mcp-schema-box pre {{ font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #93c5fd; }}

        .playground-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.8rem; margin-top: 2rem; }}
        .playground-title {{ font-size: 1.25rem; font-weight: 800; color: #fff; margin-bottom: 1rem; }}
        .rpc-editor {{ width: 100%; height: 160px; background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #60a5fa; outline: none; margin-bottom: 1rem; }}
        .rpc-response {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #34d399; min-height: 120px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            <span>Model Context Protocol (MCP) Portal</span>
        </div>
        <div style="display: flex; gap: 0.8rem;">
            <a href="/" class="btn">Aplicação Web</a>
            <a href="/docs/guia" class="btn">Guia Oficial</a>
            <a href="/docs" class="btn btn-primary">Swagger Studio</a>
        </div>
    </header>

    <main>
        <div class="banner">
            <div>
                <h2 style="font-size: 1.4rem; font-weight: 800; margin-bottom: 0.4rem;">Servidor Nativo Universal MCP 4.0</h2>
                <p style="font-size: 0.9rem; color: var(--text-muted);">Compatibilidade direta com Claude Desktop, Cursor e Antigravity via JSON-RPC 2.0.</p>
            </div>
            <button class="btn btn-primary" onclick="testarListTools()">Listar Ferramentas (tools/list)</button>
        </div>

        <h3 style="font-size: 1.15rem; font-weight: 800; margin-bottom: 1.2rem;">Ferramentas de CRUD & Operações Logísticas Disponíveis</h3>
        <div class="tools-grid">
            {tools_cards}
        </div>

        <div class="playground-box">
            <div class="playground-title">Interactive MCP JSON-RPC 2.0 Playground</div>
            <textarea class="rpc-editor" id="rpc-input">{{
  "jsonrpc": "2.0",
  "id": "test-1",
  "method": "tools/call",
  "params": {{
    "name": "frotas_listar_veiculos",
    "arguments": {{}}
  }}
}}</textarea>
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <button class="btn btn-primary" onclick="executarRpc()">Executar Chamada JSON-RPC</button>
            </div>
            <div class="rpc-response" id="rpc-output">// O payload de resposta JSON-RPC do servidor MCP aparecerá aqui</div>
        </div>
    </main>

    <script>
        async function executarRpc() {{
            const input = document.getElementById('rpc-input').value;
            const output = document.getElementById('rpc-output');
            output.textContent = 'Enviando chamada RPC...';
            try {{
                const res = await fetch('/api/mcp/rpc', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: input
                }});
                const data = await res.json();
                output.textContent = JSON.stringify(data, null, 2);
            }} catch (err) {{
                output.textContent = 'Erro ao processar chamada RPC: ' + err.message;
            }}
        }}

        function prepararTesteTool(name) {{
            document.getElementById('rpc-input').value = JSON.stringify({{
                "jsonrpc": "2.0",
                "id": "call-" + Date.now(),
                "method": "tools/call",
                "params": {{
                    "name": name,
                    "arguments": {{}}
                }}
            }}, null, 2);
            window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
        }}

        function testarListTools() {{
            document.getElementById('rpc-input').value = JSON.stringify({{
                "jsonrpc": "2.0",
                "id": "list-1",
                "method": "tools/list"
            }}, null, 2);
            executarRpc();
        }}
    </script>
</body>
</html>
"""
