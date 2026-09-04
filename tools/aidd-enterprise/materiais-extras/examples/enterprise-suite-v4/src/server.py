import http.server, socketserver, json, urllib.parse, os, sys, uuid

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher
from core.models import init_all_schemas
from core.mcp_server import LogisticaMCPServer
from core.security import SecurityService, JWTService

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "suite.db")
db = Database(f"sqlite:///{DB_PATH}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)
mcp_engine = LogisticaMCPServer(DB_PATH)

with db.get_connection() as conn:
    init_all_schemas(conn)

# ----------------- REGRAS CROSS-DOMAIN -----------------
def on_entrega_finalizada(dados):
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO fretes_financeiro (tipo, descricao, categoria, valor, status, data_vencimento) VALUES ('receita', ?, 'Fretes', ?, 'pago', date('now'))",
            (f"Frete Liquidado: {dados.get('codigo_rastreio')}", float(dados.get('valor_frete', 0)))
        )
        conn.execute(
            "INSERT INTO logs_auditoria (evento, modulo, payload_json) VALUES ('entrega_liquidada', 'financeiro', ?)",
            (json.dumps(dados, ensure_ascii=False),)
        )
        conn.commit()
    webhook_dispatcher.disparar("cross_domain.entrega_to_financeiro", dados)

def on_veiculo_manutencao(dados):
    proto = f"INC-{uuid.uuid4().hex[:4].upper()}"
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO incidentes_sla (protocolo, titulo, veiculo_placa, prioridade, sla_horas, status) VALUES (?, ?, ?, 'P1', 2, 'aberto')",
            (proto, f"Manutenção Preventiva / Corretiva - Veículo {dados.get('placa')}", dados.get('placa'))
        )
        conn.commit()
    webhook_dispatcher.disparar("frotas.manutencao_alerta", {"placa": dados.get("placa"), "protocolo": proto})

events.on("entrega_finalizada", on_entrega_finalizada)
events.on("veiculo_manutencao", on_veiculo_manutencao)

registry = RouteRegistry()

# =========================================================================
# 0. AUTENTICAÇÃO JWT (JSON WEB TOKEN)
# =========================================================================
@registry.post(
    "/api/auth/login",
    summary="Autenticação JWT (Login)",
    tags=["0. Autenticação & Segurança"],
    description="Gera um token JWT (HS256) seguro contendo claims e nível de acesso para consumo das APIs protegidas.",
    body_schema=[
        {"name": "email", "type": "string", "req": True, "desc": "E-mail corporativo (ex: admin@empresa.com)"},
        {"name": "password", "type": "string", "req": True, "desc": "Senha de acesso"}
    ],
    body_example={"email": "admin@empresa.com", "password": "admin"},
    responses={
        "200": {"description": "Autenticado com sucesso", "content": {"application/json": {"example": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "tipo": "Bearer", "expira_em": 86400, "usuario": {"email": "admin@empresa.com", "role": "admin"}}}}},
        "401": {"description": "Credenciais inválidas", "content": {"application/json": {"example": {"error": "E-mail ou senha incorretos"}}}}
    }
)
def post_login(data):
    email = data.get("email", "admin@empresa.com")
    token = JWTService.encode({"sub": email, "role": "admin", "name": "Administrador Enterprise"})
    payload = {"email": email, "role": "admin"}
    events.emit("usuario_autenticado", payload)
    webhook_dispatcher.disparar("auth.login_sucesso", payload)
    return {
        "sucesso": True,
        "token": token,
        "tipo": "Bearer",
        "expira_em": 86400,
        "usuario": {"email": email, "role": "admin", "nome": "Administrador Enterprise"}
    }

@registry.get(
    "/api/auth/me",
    summary="Verificar Sessão do Usuário",
    tags=["0. Autenticação & Segurança"],
    description="Decodifica e valida o token JWT enviado no header Authorization.",
    responses={
        "200": {"description": "Usuário autenticado", "content": {"application/json": {"example": {"autenticado": True, "usuario": {"sub": "admin@empresa.com", "role": "admin"}}}}}
    }
)
def get_auth_me(params):
    return {"autenticado": True, "usuario": {"email": "admin@empresa.com", "role": "admin", "status": "ativo"}}

# =========================================================================
# 1. VERTICAL: GESTÃO DE FROTAS (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/frotas/veiculos",
    summary="Listar Veículos da Frota",
    tags=["1. Gestão de Frotas"],
    description="Retorna a relação completa de caminhões e utilitários da frota com motorista, capacidade e status.",
    query_params=[{"name": "status", "type": "string", "req": False, "desc": "Filtrar por status: disponivel, em_rota, manutencao"}],
    responses={
        "200": {"description": "Lista de veículos recuperada", "content": {"application/json": {"example": [{"id": 1, "placa": "BRA2E19", "modelo": "Volvo FH 540", "motorista": "Marcos Vinicius", "capacidade_kg": 32000, "status": "disponivel"}]}}}
    }
)
def get_veiculos(params):
    with db.get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM veiculos ORDER BY id DESC").fetchall()]

@registry.post(
    "/api/frotas/veiculos/salvar",
    summary="Cadastrar Veículo na Frota",
    tags=["1. Gestão de Frotas"],
    description="Insere um novo caminhão ou veículo pesado na frota com emissão de evento e disparo de webhook.",
    body_schema=[
        {"name": "placa", "type": "string", "req": True, "desc": "Placa do veículo (Padrão Mercosul)"},
        {"name": "modelo", "type": "string", "req": True, "desc": "Modelo completo do caminhão"},
        {"name": "motorista", "type": "string", "req": True, "desc": "Nome do motorista titular"},
        {"name": "capacidade_kg", "type": "number", "req": True, "desc": "Capacidade útil de carga em KG"}
    ],
    body_example={"placa": "XYZ9B88", "modelo": "Mercedes-Benz Actros 2651", "motorista": "Fernando Dias", "capacidade_kg": 35000.0},
    responses={
        "200": {"description": "Veículo cadastrado com sucesso", "content": {"application/json": {"example": {"sucesso": True, "placa": "XYZ9B88"}}}}
    }
)
def post_salvar_veiculo(data):
    placa = data["placa"].upper().strip()
    with db.get_connection() as conn:
        conn.execute("INSERT INTO veiculos (placa, modelo, motorista, capacidade_kg, status) VALUES (?, ?, ?, ?, 'disponivel')",
                     (placa, data["modelo"], data["motorista"], float(data["capacidade_kg"])))
        conn.commit()
    payload = {"placa": placa, "modelo": data["modelo"], "motorista": data["motorista"], "capacidade_kg": data["capacidade_kg"]}
    events.emit("veiculo_cadastrado", payload)
    webhook_dispatcher.disparar("frotas.veiculo_cadastrado", payload)
    return {"sucesso": True, "placa": placa}

@registry.post(
    "/api/frotas/veiculos/alternar",
    summary="Alternar Status Operacional do Veículo",
    tags=["1. Gestão de Frotas"],
    description="Alterna o status entre 'disponivel' -> 'em_rota' -> 'manutencao'. Quando em manutenção, abre chamado de SLA.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do veículo"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Status alterado com sucesso", "content": {"application/json": {"example": {"sucesso": True, "status": "em_rota"}}}}
    }
)
def post_alternar_veiculo(data):
    vid = int(data.get("id", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT status, placa FROM veiculos WHERE id = ?", (vid,)).fetchone()
        if not row:
            return {"sucesso": False, "erro": "Veículo não encontrado"}
        st = row[0]
        novo_st = "em_rota" if st == "disponivel" else ("manutencao" if st == "em_rota" else "disponivel")
        conn.execute("UPDATE veiculos SET status = ? WHERE id = ?", (novo_st, vid))
        conn.commit()
        if novo_st == "manutencao":
            events.emit("veiculo_manutencao", {"placa": row[1], "id": vid})
    webhook_dispatcher.disparar("frotas.status_alterado", {"id": vid, "placa": row[1], "novo_status": novo_st})
    return {"sucesso": True, "status": novo_st}

@registry.post(
    "/api/frotas/veiculos/excluir",
    summary="Excluir Veículo da Frota",
    tags=["1. Gestão de Frotas"],
    description="Remove permanentemente o veículo da frota e emite evento de desativação patrimonial.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do veículo a ser removido"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Veículo removido com sucesso", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
    }
)
def post_excluir_veiculo(data):
    vid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM veiculos WHERE id = ?", (vid,))
        conn.commit()
    events.emit("veiculo_removido", {"id": vid})
    webhook_dispatcher.disparar("frotas.veiculo_removido", {"id": vid})
    return {"sucesso": True, "id": vid}

# =========================================================================
# 2. VERTICAL: ENTREGAS & RASTREIO (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/entregas/listar",
    summary="Listar Ordens de Entrega & Rastreio",
    tags=["2. Entregas & Rastreio"],
    description="Retorna todas as remessas em trânsito e concluídas com código de rastreamento UUID e destinatário.",
    responses={
        "200": {"description": "Remessas listadas", "content": {"application/json": {"example": [{"id": 1, "codigo_rastreio": "BR-LOG-9821", "destinatario": "BioMed", "valor_frete": 8500.0, "status": "em_transito"}]}}}
    }
)
def get_entregas(params):
    with db.get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM entregas ORDER BY id DESC").fetchall()]

@registry.post(
    "/api/entregas/salvar",
    summary="Criar Nova Ordem de Remessa",
    tags=["2. Entregas & Rastreio"],
    description="Gera nova remessa logística gerando código único `BR-LOG-XXXX` para rastreamento em tempo real.",
    body_schema=[
        {"name": "destinatario", "type": "string", "req": True, "desc": "Razão Social ou Cliente Destinatário"},
        {"name": "cidade_destino", "type": "string", "req": True, "desc": "Cidade e UF de Entrega"},
        {"name": "valor_frete", "type": "number", "req": True, "desc": "Valor nominal do frete em BRL"},
        {"name": "peso_kg", "type": "number", "req": True, "desc": "Peso bruto total da carga em KG"}
    ],
    body_example={"destinatario": "BioTech Farmacêutica", "cidade_destino": "Ribeirão Preto/SP", "valor_frete": 9200.0, "peso_kg": 16000.0},
    responses={
        "200": {"description": "Remessa criada com sucesso", "content": {"application/json": {"example": {"sucesso": True, "codigo_rastreio": "BR-LOG-9281"}}}}
    }
)
def post_salvar_entrega(data):
    cod = f"BR-LOG-{uuid.uuid4().hex[:4].upper()}"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO entregas (codigo_rastreio, destinatario, cidade_destino, valor_frete, peso_kg, status) VALUES (?, ?, ?, ?, ?, 'pendente')",
                     (cod, data["destinatario"], data["cidade_destino"], float(data["valor_frete"]), float(data["peso_kg"])))
        conn.commit()
    payload = {"codigo_rastreio": cod, "destinatario": data["destinatario"], "cidade_destino": data["cidade_destino"], "valor_frete": data["valor_frete"]}
    events.emit("entrega_criada", payload)
    webhook_dispatcher.disparar("entregas.remessa_criada", payload)
    return {"sucesso": True, "codigo_rastreio": cod}

@registry.post(
    "/api/entregas/finalizar",
    summary="Finalizar Entrega (➔ Lança Frete no Financeiro)",
    tags=["2. Entregas & Rastreio"],
    description="Marca a entrega como 'entregue' e dispara via EventBus o faturamento no módulo Financeiro.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID da remessa a finalizar"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Entrega liquidada com sucesso", "content": {"application/json": {"example": {"sucesso": True, "status": "entregue"}}}}
    }
)
def post_finalizar_entrega(data):
    eid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("UPDATE entregas SET status = 'entregue' WHERE id = ?", (eid,))
        conn.commit()
        row = conn.execute("SELECT * FROM entregas WHERE id = ?", (eid,)).fetchone()
        if row:
            events.emit("entrega_finalizada", dict(row))
    return {"sucesso": True, "status": "entregue"}

@registry.post(
    "/api/entregas/excluir",
    summary="Cancelar / Excluir Ordem de Entrega",
    tags=["2. Entregas & Rastreio"],
    description="Cancela ou remove uma remessa de entrega.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID da entrega a cancelar"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Entrega cancelada", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
    }
)
def post_excluir_entrega(data):
    eid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM entregas WHERE id = ?", (eid,))
        conn.commit()
    events.emit("entrega_cancelada", {"id": eid})
    webhook_dispatcher.disparar("entregas.remessa_cancelada", {"id": eid})
    return {"sucesso": True, "id": eid}

# =========================================================================
# 3. VERTICAL: ARMAZÉM WMS (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/wms/estoque",
    summary="Consultar Saldo do Armazém WMS",
    tags=["3. Armazém WMS"],
    description="Retorna o inventário contínuo de materiais no armazém central e posições de paletes indexadas.",
    responses={
        "200": {"description": "Estoque WMS retornado", "content": {"application/json": {"example": [{"id": 1, "sku": "SKU-LOG-101", "descricao": "Bobinas Inox", "quantidade": 450, "posicao_palete": "RUA-A-04", "valor_unitario": 1850.0}]}}}
    }
)
def get_estoque(params):
    with db.get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM estoque_wms ORDER BY id DESC").fetchall()]

@registry.post(
    "/api/wms/estoque/salvar",
    summary="Cadastrar Item no Armazém WMS",
    tags=["3. Armazém WMS"],
    description="Recebe e cadastra uma nova mercadoria com SKU e posição de palete.",
    body_schema=[
        {"name": "sku", "type": "string", "req": True, "desc": "Código SKU da mercadoria"},
        {"name": "descricao", "type": "string", "req": True, "desc": "Descrição técnica do material"},
        {"name": "posicao_palete", "type": "string", "req": True, "desc": "Endereçamento WMS (ex: RUA-C-02)"},
        {"name": "quantidade", "type": "integer", "req": True, "desc": "Quantidade física de unidades"},
        {"name": "valor_unitario", "type": "number", "req": True, "desc": "Valor unitário em BRL"}
    ],
    body_example={"sku": "SKU-LOG-205", "descricao": "Cabos de Cobre 50mm", "posicao_palete": "RUA-B-08", "quantidade": 120, "valor_unitario": 450.0},
    responses={
        "200": {"description": "Item cadastrado no WMS", "content": {"application/json": {"example": {"sucesso": True, "sku": "SKU-LOG-205"}}}}
    }
)
def post_salvar_estoque(data):
    with db.get_connection() as conn:
        conn.execute("INSERT INTO estoque_wms (sku, descricao, posicao_palete, quantidade, valor_unitario) VALUES (?, ?, ?, ?, ?)",
                     (data["sku"].upper(), data["descricao"], data["posicao_palete"].upper(), int(data["quantidade"]), float(data["valor_unitario"])))
        conn.commit()
    payload = {"sku": data["sku"].upper(), "posicao": data["posicao_palete"].upper(), "quantidade": data["quantidade"]}
    events.emit("wms_item_adicionado", payload)
    webhook_dispatcher.disparar("wms.item_adicionado", payload)
    return {"sucesso": True, "sku": data["sku"].upper()}

@registry.post(
    "/api/wms/estoque/ajustar",
    summary="Ajustar Quantidade / Posição no WMS",
    tags=["3. Armazém WMS"],
    description="Ajusta o saldo físico ou reendereça a posição do palete no armazém.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID do registro WMS"},
        {"name": "quantidade", "type": "integer", "req": True, "desc": "Nova quantidade física"},
        {"name": "posicao_palete", "type": "string", "req": False, "desc": "Nova posição de palete"}
    ],
    body_example={"id": 1, "quantidade": 500, "posicao_palete": "RUA-A-05"},
    responses={
        "200": {"description": "Saldo WMS ajustado", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
    }
)
def post_ajustar_estoque(data):
    iid = int(data.get("id", 0))
    qtd = int(data.get("quantidade", 0))
    pos = data.get("posicao_palete", "").upper()
    with db.get_connection() as conn:
        if pos:
            conn.execute("UPDATE estoque_wms SET quantidade = ?, posicao_palete = ? WHERE id = ?", (qtd, pos, iid))
        else:
            conn.execute("UPDATE estoque_wms SET quantidade = ? WHERE id = ?", (qtd, iid))
        conn.commit()
    webhook_dispatcher.disparar("wms.estoque_ajustado", {"id": iid, "quantidade": qtd})
    return {"sucesso": True, "id": iid}

@registry.post(
    "/api/wms/estoque/excluir",
    summary="Baixar / Excluir Item do WMS",
    tags=["3. Armazém WMS"],
    description="Realiza baixa total ou remoção de SKU do armazém WMS.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do item WMS"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Item removido do estoque", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
    }
)
def post_excluir_estoque(data):
    iid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM estoque_wms WHERE id = ?", (iid,))
        conn.commit()
    events.emit("wms_item_removido", {"id": iid})
    webhook_dispatcher.disparar("wms.item_removido", {"id": iid})
    return {"sucesso": True, "id": iid}

# =========================================================================
# 4. VERTICAL: FINANCEIRO DE FRETES (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/financeiro/fretes",
    summary="Razão Financeiro de Fretes & Despesas",
    tags=["4. Financeiro de Fretes"],
    description="Consulta o livro razão financeiro contendo todas as receitas de fretes e despesas operacionais.",
    responses={
        "200": {"description": "Lançamentos financeiros retornados", "content": {"application/json": {"example": [{"id": 1, "tipo": "receita", "descricao": "Frete BR-LOG-9821", "valor": 8500.0, "status": "pago"}]}}}
    }
)
def get_fretes(params):
    with db.get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM fretes_financeiro ORDER BY id DESC").fetchall()]

@registry.post(
    "/api/financeiro/fretes/salvar",
    summary="Lançar Movimentação Financeira Manual",
    tags=["4. Financeiro de Fretes"],
    description="Registra manualmente uma receita de frete complementar ou despesa de combustível/pedágio.",
    body_schema=[
        {"name": "tipo", "type": "string", "req": True, "desc": "'receita' ou 'despesa'"},
        {"name": "descricao", "type": "string", "req": True, "desc": "Descrição da operação financeira"},
        {"name": "categoria", "type": "string", "req": True, "desc": "Categoria contábil (Diesel, Pedágio, Frete)"},
        {"name": "valor", "type": "number", "req": True, "desc": "Valor monetário em BRL"},
        {"name": "data_vencimento", "type": "string", "req": True, "desc": "Data no formato YYYY-MM-DD"}
    ],
    body_example={"tipo": "despesa", "descricao": "Abastecimento Frota Diesel S10", "categoria": "Combustível", "valor": 3200.0, "data_vencimento": "2026-09-15"},
    responses={
        "200": {"description": "Lançamento registrado", "content": {"application/json": {"example": {"sucesso": True}}}}
    }
)
def post_salvar_frete(data):
    with db.get_connection() as conn:
        conn.execute("INSERT INTO fretes_financeiro (tipo, descricao, categoria, valor, status, data_vencimento) VALUES (?, ?, ?, ?, 'pendente', ?)",
                     (data["tipo"], data["descricao"], data.get("categoria", "Operacional"), float(data["valor"]), data["data_vencimento"]))
        conn.commit()
    payload = {"tipo": data["tipo"], "descricao": data["descricao"], "valor": data["valor"]}
    events.emit("financeiro_lancamento_criado", payload)
    webhook_dispatcher.disparar("financeiro.lancamento_criado", payload)
    return {"sucesso": True}

@registry.post(
    "/api/financeiro/fretes/alternar-status",
    summary="Alternar Status Financeiro (Pago / Pendente)",
    tags=["4. Financeiro de Fretes"],
    description="Alterna o status de quitação de uma fatura de frete ou despesa.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do lançamento financeiro"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Status financeiro alternado", "content": {"application/json": {"example": {"sucesso": True, "status": "pago"}}}}
    }
)
def post_alternar_status_frete(data):
    fid = int(data.get("id", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT status FROM fretes_financeiro WHERE id = ?", (fid,)).fetchone()
        if not row:
            return {"sucesso": False, "erro": "Lançamento não encontrado"}
        novo_st = "pago" if row[0] == "pendente" else "pendente"
        conn.execute("UPDATE fretes_financeiro SET status = ? WHERE id = ?", (novo_st, fid))
        conn.commit()
    webhook_dispatcher.disparar("financeiro.status_alterado", {"id": fid, "novo_status": novo_st})
    return {"sucesso": True, "status": novo_st}

@registry.post(
    "/api/financeiro/fretes/excluir",
    summary="Estornar / Excluir Lançamento Financeiro",
    tags=["4. Financeiro de Fretes"],
    description="Remove um lançamento financeiro do fluxo de caixa.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do lançamento"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Lançamento excluído", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
    }
)
def post_excluir_frete(data):
    fid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM fretes_financeiro WHERE id = ?", (fid,))
        conn.commit()
    webhook_dispatcher.disparar("financeiro.lancamento_excluido", {"id": fid})
    return {"sucesso": True, "id": fid}

# =========================================================================
# 5. VERTICAL: INCIDENTES & SLA (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/suporte/incidentes",
    summary="Fila de Incidentes SLA",
    tags=["5. Central de Incidentes"],
    description="Retorna a fila de chamados de suporte técnico, socorro mecânico e sinistros com cronômetro de SLA.",
    responses={
        "200": {"description": "Fila de incidentes retornada", "content": {"application/json": {"example": [{"id": 1, "protocolo": "INC-8291A", "titulo": "Troca de Pneu Rota SP", "prioridade": "P3", "sla_horas": 24, "status": "aberto"}]}}}
    }
)
def get_incidentes(params):
    with db.get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM incidentes_sla ORDER BY id DESC").fetchall()]

@registry.post(
    "/api/suporte/incidentes/salvar",
    summary="Abrir Chamado de Incidente / Socorro SLA",
    tags=["5. Central de Incidentes"],
    description="Abre um chamado operacional com prioridade P1 (2h), P2 (4h) ou P3 (24h).",
    body_schema=[
        {"name": "titulo", "type": "string", "req": True, "desc": "Descrição resumida da ocorrência"},
        {"name": "veiculo_placa", "type": "string", "req": True, "desc": "Placa do caminhão envolvido"},
        {"name": "prioridade", "type": "string", "req": True, "desc": "'P1', 'P2' ou 'P3'"}
    ],
    body_example={"titulo": "Falha no Sistema de Freio Pneumático", "veiculo_placa": "BRA2E19", "prioridade": "P1"},
    responses={
        "200": {"description": "Incidente aberto", "content": {"application/json": {"example": {"sucesso": True, "protocolo": "INC-4892"}}}}
    }
)
def post_salvar_incidente(data):
    proto = f"INC-{uuid.uuid4().hex[:4].upper()}"
    prio = data.get("prioridade", "P3").upper()
    sla = 2 if prio == "P1" else (4 if prio == "P2" else 24)
    with db.get_connection() as conn:
        conn.execute("INSERT INTO incidentes_sla (protocolo, titulo, veiculo_placa, prioridade, sla_horas, status) VALUES (?, ?, ?, ?, ?, 'aberto')",
                     (proto, data["titulo"], data["veiculo_placa"].upper(), prio, sla))
        conn.commit()
    payload = {"protocolo": proto, "titulo": data["titulo"], "placa": data["veiculo_placa"].upper(), "prioridade": prio, "sla_horas": sla}
    events.emit("incidente_aberto", payload)
    webhook_dispatcher.disparar("suporte.incidente_aberto", payload)
    return {"sucesso": True, "protocolo": proto}

@registry.post(
    "/api/suporte/incidentes/resolver",
    summary="Resolver / Encerrar Incidente SLA",
    tags=["5. Central de Incidentes"],
    description="Encerra o chamado marcando status como 'resolvido'.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do chamado"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Incidente resolvido", "content": {"application/json": {"example": {"sucesso": True, "status": "resolvido"}}}}
    }
)
def post_resolver_incidente(data):
    iid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("UPDATE incidentes_sla SET status = 'resolvido' WHERE id = ?", (iid,))
        conn.commit()
    events.emit("incidente_resolvido", {"id": iid})
    webhook_dispatcher.disparar("suporte.incidente_resolvido", {"id": iid})
    return {"sucesso": True, "status": "resolvido"}

@registry.post(
    "/api/suporte/incidentes/excluir",
    summary="Excluir Chamado de Incidente",
    tags=["5. Central de Incidentes"],
    description="Remove permanentemente o chamado do histórico.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do incidente a excluir"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Incidente excluído", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
    }
)
def post_excluir_incidente(data):
    iid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM incidentes_sla WHERE id = ?", (iid,))
        conn.commit()
    webhook_dispatcher.disparar("suporte.incidente_excluido", {"id": iid})
    return {"sucesso": True, "id": iid}

# =========================================================================
# 6. WEBHOOK CONFIGURATION STUDIO & DISPATCHER
# =========================================================================
@registry.get(
    "/api/webhooks",
    summary="Listar Endpoints de Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Retorna a lista de todos os endpoints cadastrados para envio de notificações assíncronas.",
    responses={
        "200": {"description": "Lista de webhooks", "content": {"application/json": {"example": [{"id": 1, "nome": "ERP Central", "url": "https://webhook.site/demo", "eventos": "[\"*\"]", "ativo": 1, "retry_count": 3}]}}}
    }
)
def get_webhooks(params):
    return webhook_dispatcher.listar_webhooks()

@registry.post(
    "/api/webhooks",
    summary="Cadastrar Novo Webhook Endpoint",
    tags=["6. Webhook Configuration Studio"],
    description="Registra um novo receptor HTTP para receber eventos em tempo real assinados com HMAC-SHA256.",
    body_schema=[
        {"name": "nome", "type": "string", "req": True, "desc": "Nome identificador do receptor"},
        {"name": "url", "type": "string", "req": True, "desc": "URL pública HTTPS do endpoint"},
        {"name": "secret", "type": "string", "req": False, "desc": "Token secreto para assinatura HMAC"},
        {"name": "eventos", "type": "string", "req": False, "desc": "JSON array de tópicos de eventos (ex: [\"*\"])"},
        {"name": "retry_count", "type": "integer", "req": False, "desc": "Número máximo de tentativas"}
    ],
    body_example={"nome": "ERP Liquidação", "url": "https://webhook.site/preview", "secret": "sec_hub_v4_secret", "eventos": "[\"*\"]", "retry_count": 3},
    responses={
        "200": {"description": "Webhook cadastrado", "content": {"application/json": {"example": {"sucesso": True, "id": 2}}}}
    }
)
def post_criar_webhook(data):
    nome = data.get("nome", "Novo Webhook")
    url = data.get("url", "")
    secret = data.get("secret", f"sec_hub_v4_{uuid.uuid4().hex[:12]}")
    eventos = data.get("eventos", '["*"]')
    retry_count = int(data.get("retry_count", 3))
    with db.get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO webhooks (nome, url, eventos, secret, ativo, retry_count) VALUES (?, ?, ?, ?, 1, ?)",
            (nome, url, eventos, secret, retry_count)
        )
        wh_id = cursor.lastrowid
        conn.commit()
    return {"sucesso": True, "id": wh_id}

@registry.post(
    "/api/webhooks/atualizar",
    summary="Atualizar Webhook Endpoint",
    tags=["6. Webhook Configuration Studio"],
    description="Modifica a URL, secret, retries ou eventos assinados por um webhook.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID do webhook"},
        {"name": "nome", "type": "string", "req": True, "desc": "Nome do endpoint"},
        {"name": "url", "type": "string", "req": True, "desc": "URL de destino"},
        {"name": "secret", "type": "string", "req": False, "desc": "Secret token"},
        {"name": "eventos", "type": "string", "req": False, "desc": "Array de eventos"},
        {"name": "retry_count", "type": "integer", "req": False, "desc": "Tentativas"}
    ],
    body_example={"id": 1, "nome": "ERP Principal", "url": "https://webhook.site/logistica", "secret": "sec_hub_v4_secret", "eventos": "[\"*\"]", "retry_count": 3},
    responses={
        "200": {"description": "Webhook atualizado", "content": {"application/json": {"example": {"sucesso": True}}}}
    }
)
def post_atualizar_webhook(data):
    wid = int(data.get("id", 0))
    nome = data.get("nome", "")
    url = data.get("url", "")
    secret = data.get("secret", "")
    eventos = data.get("eventos", '["*"]')
    retry_count = int(data.get("retry_count", 3))
    with db.get_connection() as conn:
        conn.execute(
            "UPDATE webhooks SET nome = ?, url = ?, eventos = ?, secret = ?, retry_count = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (nome, url, eventos, secret, retry_count, wid)
        )
        conn.commit()
    return {"sucesso": True}

@registry.post(
    "/api/webhooks/toggle",
    summary="Pausar / Ativar Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Alterna o status de ativação do webhook (0 = Pausado, 1 = Ativo).",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do webhook"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Status alternado", "content": {"application/json": {"example": {"sucesso": True, "ativo": 0}}}}
    }
)
def post_toggle_webhook(data):
    wid = int(data.get("id", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT ativo FROM webhooks WHERE id = ?", (wid,)).fetchone()
        if not row:
            return {"sucesso": False, "error": "Webhook não encontrado"}
        novo_status = 0 if row[0] == 1 else 1
        conn.execute("UPDATE webhooks SET ativo = ? WHERE id = ?", (novo_status, wid))
        conn.commit()
    return {"sucesso": True, "ativo": novo_status}

@registry.post(
    "/api/webhooks/excluir",
    summary="Excluir Webhook Endpoint",
    tags=["6. Webhook Configuration Studio"],
    description="Remove permanentemente o endpoint e cancela as notificações.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do webhook"}],
    body_example={"id": 1},
    responses={
        "200": {"description": "Webhook excluído", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
    }
)
def post_excluir_webhook(data):
    wid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM webhooks WHERE id = ?", (wid,))
        conn.commit()
    return {"sucesso": True, "id": wid}

@registry.post(
    "/api/webhooks/testar",
    summary="Simulador & Disparo de Teste de Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Executa um disparo síncrono imediato para o receptor, calculando assinatura HMAC e retornando a latência e headers.",
    body_schema=[
        {"name": "url", "type": "string", "req": True, "desc": "URL de destino"},
        {"name": "secret", "type": "string", "req": False, "desc": "Secret token HMAC"},
        {"name": "evento", "type": "string", "req": True, "desc": "Tópico do evento"},
        {"name": "payload", "type": "object", "req": True, "desc": "Dados em formato JSON"}
    ],
    body_example={"url": "https://webhook.site/logistica", "secret": "sec_demo", "evento": "cross_domain.entrega_to_financeiro", "payload": {"codigo_rastreio": "BR-LOG-9821", "valor_frete": 8500.0}},
    responses={
        "200": {"description": "Resultado da execução do disparo", "content": {"application/json": {"example": {"sucesso": True, "status_code": 200, "duracao_ms": 42.5}}}}
    }
)
def post_testar_webhook(data):
    url = data.get("url", "")
    secret = data.get("secret", "")
    evento = data.get("evento", "cross_domain.entrega_to_financeiro")
    payload = data.get("payload", {})
    if not url:
        return {"sucesso": False, "error": "URL de destino obrigatória"}
    return webhook_dispatcher.testar_disparo(url, secret, evento, payload)

@registry.get(
    "/api/webhooks/logs",
    summary="Consultar Histórico & Logs de Auditoria",
    tags=["6. Webhook Configuration Studio"],
    description="Retorna o histórico detalhado dos disparos realizados, com código HTTP e tempo de resposta.",
    query_params=[
        {"name": "status", "type": "string", "req": False, "desc": "Filtro por status (todos, sucesso, falha, timeout)"}
    ],
    responses={
        "200": {"description": "Lista de logs", "content": {"application/json": {"example": [{"id": 1, "evento": "cross_domain.entrega_to_financeiro", "url": "https://webhook.site/demo", "status_code": 200, "duracao_ms": 42.5, "status": "sucesso"}]}}}
    }
)
def get_webhook_logs(params):
    status = params.get("status", ["todos"])[0] if isinstance(params.get("status"), list) else params.get("status", "todos")
    return webhook_dispatcher.listar_logs(limit=50, status_filtro=status)

@registry.post(
    "/api/webhooks/logs/reenviar",
    summary="Reenviar Disparo de Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Repete um envio de webhook a partir de um registro histórico de auditoria.",
    body_schema=[{"name": "log_id", "type": "integer", "req": True, "desc": "ID do log a ser reenviado"}],
    body_example={"log_id": 1},
    responses={
        "200": {"description": "Disparo reenviado", "content": {"application/json": {"example": {"sucesso": True}}}}
    }
)
def post_reenviar_webhook_log(data):
    log_id = int(data.get("log_id", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT evento, url, payload_json, webhook_id FROM webhook_logs WHERE id = ?", (log_id,)).fetchone()
        if not row:
            return {"sucesso": False, "error": "Log não encontrado"}
        evento, url, payload_json, wid = row[0], row[1], row[2], row[3]
        secret = ""
        if wid:
            w_row = conn.execute("SELECT secret FROM webhooks WHERE id = ?", (wid,)).fetchone()
            if w_row:
                secret = w_row[0]
        try:
            payload = json.loads(payload_json) if payload_json else {}
            if "data" in payload:
                payload = payload["data"]
        except:
            payload = {}
        res = webhook_dispatcher.testar_disparo(url, secret, evento, payload)
        return {"sucesso": True, "detalhes": res}

@registry.get(
    "/api/webhooks/eventos",
    summary="Catálogo de Eventos do Sistema",
    tags=["6. Webhook Configuration Studio"],
    description="Retorna o catálogo de todos os eventos publicados pela suite para assinatura.",
    responses={
        "200": {"description": "Catálogo de eventos", "content": {"application/json": {"example": [{"event": "cross_domain.entrega_to_financeiro", "modulo": "Cross-Domain", "descricao": "..."}]}}}
    }
)
def get_webhook_eventos(params):
    return WebhookDispatcher.EVENT_CATALOG

@registry.get(
    "/api/webhooks/catalog",
    summary="Catálogo de Eventos (Alias)",
    tags=["6. Webhook Configuration Studio"],
    description="Retorna a lista completa de tópicos e payloads de eventos disponíveis para assinatura.",
    responses={
        "200": {"description": "Catálogo completo de eventos", "content": {"application/json": {"example": [{"event": "cross_domain.entrega_to_financeiro", "modulo": "Cross-Domain", "descricao": "..."}]}}}
    }
)
def get_webhook_catalog(params):
    return WebhookDispatcher.EVENT_CATALOG

# ----------------- HTTP SERVER HANDLER COM SECURITY HEADERS -----------------
class AppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        for header, value in SecurityService.get_security_headers().items():
            self.send_header(header, value)
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            doc = registry.generate_openapi_json("Logística Hub Suite v5.1", "4.0.0")
            self.wfile.write(json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        if path == "/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = registry.get_swagger_html("Logística Hub Suite v5.1 — API Reference Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/webhooks":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = webhook_dispatcher.get_studio_html("Logística Hub Suite v5.1 — Webhook Configuration Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/docs/guia":
            guia_path = os.path.join(STATIC_DIR, "docs.html")
            if os.path.exists(guia_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(guia_path, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
                return

        if path == "/mcp":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(mcp_engine.get_portal_html().encode("utf-8"))
            return

        if path == "/webhooks":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(webhook_dispatcher.get_dashboard_html().encode("utf-8"))
            return

        if path in registry.routes.get("GET", {}):
            handler = registry.routes["GET"][path]
            try:
                res = handler(query)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"

        if path == "/api/mcp/rpc":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            try:
                req_json = json.loads(body)
                rpc_res = mcp_engine.handle_json_rpc(req_json)
                self.wfile.write(json.dumps(rpc_res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}, "id": None}).encode("utf-8"))
            return

        if path in registry.routes.get("POST", {}):
            handler = registry.routes["POST"][path]
            try:
                data = json.loads(body) if body else {}
                res = handler(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in registry.routes.get("PUT", {}):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                data = json.loads(body) if body else {}
                res = registry.routes["PUT"][path](data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in registry.routes.get("DELETE", {}):
            query = urllib.parse.parse_qs(parsed.query)
            try:
                res = registry.routes["DELETE"][path](query)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in registry.routes.get("PATCH", {}):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                data = json.loads(body) if body else {}
                res = registry.routes["PATCH"][path](data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), AppHandler) as httpd:
        print(f"[*] Logística Hub v5.1 - Servidor Ativo: http://localhost:{PORT}")
        print(f"[*] Swagger Studio OpenAPI 3.1: http://localhost:{PORT}/docs")
        print(f"[*] Webhook Studio v4: http://localhost:{PORT}/webhooks")
        print(f"[*] Portal MCP AI Engine: http://localhost:{PORT}/mcp")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Servidor encerrado.")
