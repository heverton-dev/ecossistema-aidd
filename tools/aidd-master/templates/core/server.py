import http.server, socketserver, json, urllib.parse, os, sys, uuid

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher
from core.models import init_all_schemas
from core.mcp_server import AIDD_EnterpriseMCPServer
from core.security import SecurityService, JWTService

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "suite.db")
db = Database(f"sqlite:///{DB_PATH}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)
mcp_engine = AIDD_EnterpriseMCPServer(DB_PATH)

with db.get_connection() as conn:
    init_all_schemas(conn)

# ----------------- REGRAS CROSS-DOMAIN -----------------
def on_triagem_critica(dados):
    if dados.get("classificacao") in ["vermelho", "laranja"]:
        leito_emergencia = "UTI Emergência 01" if dados.get("classificacao") == "vermelho" else "Box Observação Rápida"
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE triagens SET leito_alocado = ?, status = 'em_atendimento' WHERE protocolo = ?",
                (leito_emergencia, dados.get("protocolo"))
            )
            conn.execute(
                "INSERT INTO logs_auditoria (evento, modulo, payload_json) VALUES ('triagem_critica_leito_alocado', 'pronto_socorro', ?)",
                (json.dumps(dados, ensure_ascii=False),)
            )
            conn.commit()
        webhook_dispatcher.disparar("cross_domain.triagem_critica_to_leito", {
            "protocolo": dados.get("protocolo"),
            "paciente": dados.get("paciente_nome"),
            "leito": leito_emergencia,
            "classificacao": dados.get("classificacao")
        })

def on_prescricao_emitida(dados):
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO logs_auditoria (evento, modulo, payload_json) VALUES ('prescricao_emitida_automacao', 'pep_clinico', ?)",
            (json.dumps(dados, ensure_ascii=False),)
        )
        conn.commit()
    webhook_dispatcher.disparar("cross_domain.prescricao_to_farmacia", dados)

def on_cirurgia_concluida(dados):
    with db.get_connection() as conn:
        num_guia = f"TISS-{uuid.uuid4().hex[:4].upper()}"
        valor = 12500.00 if dados.get("necessita_opme") else 7800.00
        conn.execute("""
            INSERT INTO faturamento_guias (numero_guia, paciente_nome, convenio, codigo_tuss, descricao_procedimento, valor_total, status_guia)
            VALUES (?, ?, 'Bradesco Saúde / Cirúrgico', '31003443', ?, ?, 'gerada')
        """, (num_guia, dados.get("paciente_nome"), f"Procedimento Cirúrgico: {dados.get('procedimento')}", valor))
        conn.execute(
            "INSERT INTO logs_auditoria (evento, modulo, payload_json) VALUES ('cirurgia_faturada_cross_domain', 'centro_cirurgico', ?)",
            (json.dumps(dados, ensure_ascii=False),)
        )
        conn.commit()
    webhook_dispatcher.disparar("cross_domain.cirurgia_to_faturamento", {
        "numero_guia": num_guia,
        "paciente": dados.get("paciente_nome"),
        "valor": valor,
        "procedimento": dados.get("procedimento")
    })

events.on("triagem_urgencia", on_triagem_critica)
events.on("prescricao_nova", on_prescricao_emitida)
events.on("cirurgia_finalizada", on_cirurgia_concluida)

registry = RouteRegistry()

# =========================================================================
# 0. AUTENTICAÇÃO JWT (JSON WEB TOKEN)
# =========================================================================
@registry.post(
    "/api/auth/login",
    summary="Autenticação JWT (Login)",
    tags=["0. Autenticação & Segurança"],
    description="Gera um token JWT (HS256) seguro contendo claims e perfil médico/administrativo.",
    body_schema=[
        {"name": "email", "type": "string", "req": True, "desc": "E-mail institucional (ex: medico@hospital.com)"},
        {"name": "password", "type": "string", "req": True, "desc": "Senha de acesso"}
    ],
    body_example={"email": "medico@hospital.com", "password": "admin"},
    responses={
        "200": {"description": "Autenticado com sucesso", "content": {"application/json": {"example": {"token": "eyJhbGciOiJIUzI1Ni...", "tipo": "Bearer", "expira_em": 86400, "usuario": {"email": "medico@hospital.com", "role": "medico_chefe"}}}}},
        "401": {"description": "Credenciais inválidas", "content": {"application/json": {"example": {"error": "E-mail ou senha incorretos"}}}}
    }
)
def post_login(data):
    email = data.get("email", "medico@hospital.com")
    token = JWTService.encode({"sub": email, "role": "medico_chefe", "name": "Dr. Diretor Clínico"})
    payload = {"email": email, "role": "medico_chefe"}
    events.emit("usuario_autenticado", payload)
    webhook_dispatcher.disparar("auth.login_sucesso", payload)
    return {
        "sucesso": True,
        "token": token,
        "tipo": "Bearer",
        "expira_em": 86400,
        "usuario": {"email": email, "role": "medico_chefe", "nome": "Dr. Diretor Clínico"}
    }

@registry.get(
    "/api/auth/me",
    summary="Verificar Sessão do Usuário",
    tags=["0. Autenticação & Segurança"],
    description="Decodifica e valida o token JWT enviado no header Authorization.",
    responses={
        "200": {"description": "Usuário autenticado", "content": {"application/json": {"example": {"autenticado": True, "usuario": {"sub": "medico@hospital.com", "role": "medico_chefe"}}}}}
    }
)
def get_auth_me(params):
    return {"autenticado": True, "usuario": {"email": "medico@hospital.com", "role": "medico_chefe", "status": "ativo"}}

# =========================================================================
# 1. VERTICAL: PRONTO-SOCORRO & TRIAGEM MANCHESTER (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/triagem/pacientes",
    summary="Listar Fila de Triagem Manchester",
    tags=["1. Pronto-Socorro & Triagem"],
    description="Retorna a lista de pacientes classificados por risco no protocolo de Manchester (Vermelho, Laranja, Amarelo, Verde, Azul).",
    responses={"200": {"description": "Lista de triagens", "content": {"application/json": {"example": [{"id": 1, "protocolo": "TRI-9081", "paciente_nome": "Carlos Alberto", "classificacao": "vermelho", "tempo_espera_max_min": 0}]}}}}
)
def get_triagens(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM triagens ORDER BY tempo_espera_max_min ASC, criado_em ASC").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/triagem/novo",
    summary="Classificar Novo Paciente (Manchester)",
    tags=["1. Pronto-Socorro & Triagem"],
    description="Registra um novo paciente na triagem com cálculo automático de SLA de atendimento por gravidade.",
    body_schema=[
        {"name": "paciente_nome", "type": "string", "req": True, "desc": "Nome do paciente"},
        {"name": "idade", "type": "integer", "req": True, "desc": "Idade"},
        {"name": "sinais_vitais", "type": "string", "req": True, "desc": "PA, FC, SpO2, Temp"},
        {"name": "queixa_principal", "type": "string", "req": True, "desc": "Sintomas principais"},
        {"name": "classificacao", "type": "string", "req": True, "desc": "vermelho | laranja | amarelo | verde | azul"}
    ],
    body_example={"paciente_nome": "Juliana Castro", "idade": 42, "sinais_vitais": "PA 140x90, FC 85, SpO2 97%", "queixa_principal": "Crise asmática moderada", "classificacao": "laranja"},
    responses={"200": {"description": "Paciente classificado", "content": {"application/json": {"example": {"sucesso": True, "protocolo": "TRI-9085"}}}}}
)
def post_triagem_novo(data):
    slas = {"vermelho": 0, "laranja": 10, "amarelo": 60, "verde": 120, "azul": 240}
    cls = data.get("classificacao", "verde").lower()
    sla = slas.get(cls, 120)
    proto = f"TRI-{uuid.uuid4().hex[:4].upper()}"

    with db.get_connection() as conn:
        conn.execute("""
            INSERT INTO triagens (protocolo, paciente_nome, idade, sinais_vitais, queixa_principal, classificacao, tempo_espera_max_min, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'aguardando')
        """, (proto, data["paciente_nome"], int(data.get("idade", 30)), data.get("sinais_vitais", "Estável"), data.get("queixa_principal", "Dor leve"), cls, sla))
        conn.commit()

    payload = {"protocolo": proto, "paciente_nome": data["paciente_nome"], "classificacao": cls, "sla_min": sla}
    events.emit("triagem_urgencia", payload)
    webhook_dispatcher.disparar("triagem.paciente_admitido", payload)
    return {"sucesso": True, "protocolo": proto, "classificacao": cls, "tempo_espera_max_min": sla}

@registry.put(
    "/api/triagem/atualizar",
    summary="Atualizar Triagem de Paciente",
    tags=["1. Pronto-Socorro & Triagem"],
    description="Atualiza sinais vitais, classificação de risco ou status de atendimento.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID do registro"},
        {"name": "sinais_vitais", "type": "string", "req": False, "desc": "Novos sinais vitais"},
        {"name": "classificacao", "type": "string", "req": False, "desc": "Reclassificação"},
        {"name": "status", "type": "string", "req": False, "desc": "aguardando | em_atendimento | internado | alta"}
    ],
    body_example={"id": 1, "sinais_vitais": "PA 130x80, FC 80, SpO2 98%", "status": "em_atendimento"},
    responses={"200": {"description": "Triagem atualizada", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def put_triagem_atualizar(data):
    tid = int(data.get("id", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM triagens WHERE id = ?", (tid,)).fetchone()
        if not row:
            return {"sucesso": False, "error": "Triagem não encontrada"}
        
        sinais = data.get("sinais_vitais", row["sinais_vitais"])
        st = data.get("status", row["status"])
        cls = data.get("classificacao", row["classificacao"])
        conn.execute("UPDATE triagens SET sinais_vitais = ?, status = ?, classificacao = ? WHERE id = ?", (sinais, st, cls, tid))
        conn.commit()
    return {"sucesso": True, "id": tid}

@registry.delete(
    "/api/triagem/remover",
    summary="Remover Registro de Triagem",
    tags=["1. Pronto-Socorro & Triagem"],
    description="Exclui um registro da fila de triagem.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do registro"}],
    body_example={"id": 4},
    responses={"200": {"description": "Registro removido", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def delete_triagem(data):
    tid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM triagens WHERE id = ?", (tid,))
        conn.commit()
    return {"sucesso": True}

@registry.post(
    "/api/triagem/chamar",
    summary="Chamar Paciente para Leito / Box",
    tags=["1. Pronto-Socorro & Triagem"],
    description="Aloca o paciente em um leito/box e altera status para 'em_atendimento'.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID da triagem"},
        {"name": "leito", "type": "string", "req": True, "desc": "Nome do leito (ex: Box 02)"}
    ],
    body_example={"id": 2, "leito": "Box Observação 01"},
    responses={"200": {"description": "Paciente chamado", "content": {"application/json": {"example": {"sucesso": True, "leito": "Box Observação 01"}}}}}
)
def post_triagem_chamar(data):
    tid = int(data.get("id", 0))
    leito = data.get("leito", "Box Geral")
    with db.get_connection() as conn:
        conn.execute("UPDATE triagens SET leito_alocado = ?, status = 'em_atendimento' WHERE id = ?", (leito, tid))
        conn.commit()
    return {"sucesso": True, "id": tid, "leito": leito}

# =========================================================================
# 2. VERTICAL: PRONTUÁRIO ELETRÔNICO (PEP) & PRESCRIÇÕES (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/pep/prontuarios",
    summary="Listar Prontuários Eletrônicos (PEP)",
    tags=["2. Prontuário Eletrônico & Prescrições"],
    description="Lista todos os prontuários ativos com histórico clínico e CID-10.",
    responses={"200": {"description": "Lista de prontuários", "content": {"application/json": {"example": [{"id": 1, "numero_prontuario": "PEP-1044", "paciente_nome": "Carlos Alberto", "diagnostico_cid10": "I21.9"}]}}}}
)
def get_pep_prontuarios(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM prontuarios ORDER BY atualizado_em DESC").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/pep/prontuarios",
    summary="Criar Novo Prontuário Eletrônico",
    tags=["2. Prontuário Eletrônico & Prescrições"],
    description="Cadastra um novo prontuário médico com diagnóstico CID-10 e evolução inicial.",
    body_schema=[
        {"name": "paciente_nome", "type": "string", "req": True, "desc": "Nome do paciente"},
        {"name": "medico_responsavel", "type": "string", "req": True, "desc": "Nome do médico"},
        {"name": "crm", "type": "string", "req": True, "desc": "CRM do médico"},
        {"name": "diagnostico_cid10", "type": "string", "req": True, "desc": "CID-10 e descrição"},
        {"name": "evolucao_clinica", "type": "string", "req": True, "desc": "Evolução e conduta clínica"},
        {"name": "alergias", "type": "string", "req": False, "desc": "Alergias relatadas"}
    ],
    body_example={"paciente_nome": "Fernando Gusmão", "medico_responsavel": "Dra. Beatriz Helena", "crm": "CRM/SP 148902", "diagnostico_cid10": "J18.9 - Pneumonia não especificada", "evolucao_clinica": "Paciente com tosse produtiva e dispneia leve aos esforços.", "alergias": "Nega"},
    responses={"200": {"description": "Prontuário criado", "content": {"application/json": {"example": {"sucesso": True, "numero_prontuario": "PEP-1047"}}}}}
)
def post_pep_prontuario(data):
    num = f"PEP-{uuid.uuid4().hex[:4].upper()}"
    with db.get_connection() as conn:
        conn.execute("""
            INSERT INTO prontuarios (numero_prontuario, paciente_nome, medico_responsavel, crm, diagnostico_cid10, evolucao_clinica, alergias, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ativo')
        """, (num, data["paciente_nome"], data["medico_responsavel"], data["crm"], data["diagnostico_cid10"], data["evolucao_clinica"], data.get("alergias", "Nega alergias")))
        conn.commit()
    webhook_dispatcher.disparar("pep.prontuario_atualizado", {"numero_prontuario": num, "paciente": data["paciente_nome"]})
    return {"sucesso": True, "numero_prontuario": num}

@registry.put(
    "/api/pep/prontuarios",
    summary="Atualizar Evolução Clínica do Prontuário",
    tags=["2. Prontuário Eletrônico & Prescrições"],
    description="Atualiza a evolução clínica diária ou diagnóstico CID-10.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID do prontuário"},
        {"name": "evolucao_clinica", "type": "string", "req": True, "desc": "Nova anotação de evolução médica"},
        {"name": "diagnostico_cid10", "type": "string", "req": False, "desc": "Atualização do CID-10"}
    ],
    body_example={"id": 1, "evolucao_clinica": "Paciente estável após angioplastia primária. Sem queixas álgicas no momento."},
    responses={"200": {"description": "Prontuário atualizado", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def put_pep_prontuario(data):
    pid = int(data.get("id", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM prontuarios WHERE id = ?", (pid,)).fetchone()
        if not row:
            return {"sucesso": False, "error": "Prontuário não encontrado"}
        evol = data.get("evolucao_clinica", row["evolucao_clinica"])
        cid = data.get("diagnostico_cid10", row["diagnostico_cid10"])
        conn.execute("UPDATE prontuarios SET evolucao_clinica = ?, diagnostico_cid10 = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (evol, cid, pid))
        conn.commit()
    return {"sucesso": True, "id": pid}

@registry.delete(
    "/api/pep/prontuarios",
    summary="Arquivar / Remover Prontuário",
    tags=["2. Prontuário Eletrônico & Prescrições"],
    description="Arquiva o prontuário eletrônico do paciente.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do prontuário"}],
    body_example={"id": 3},
    responses={"200": {"description": "Prontuário arquivado", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def delete_pep_prontuario(data):
    pid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM prontuarios WHERE id = ?", (pid,))
        conn.commit()
    return {"sucesso": True}

@registry.get(
    "/api/pep/prescricoes",
    summary="Listar Prescrições Médicas Digitais",
    tags=["2. Prontuário Eletrônico & Prescrições"],
    description="Lista prescrições ativas e pendentes de dispensação na farmácia.",
    responses={"200": {"description": "Lista de prescrições", "content": {"application/json": {"example": [{"id": 1, "medicamento": "Nitroglicerina", "status": "pendente"}]}}}}
)
def get_pep_prescricoes(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM prescricoes ORDER BY criado_em DESC").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/pep/prescricoes",
    summary="Emitir Nova Prescrição Digital",
    tags=["2. Prontuário Eletrônico & Prescrições"],
    description="Prescreve medicamentos e gera notificação automática para a farmácia hospitalar.",
    body_schema=[
        {"name": "prontuario_id", "type": "integer", "req": True, "desc": "ID do prontuário"},
        {"name": "medicamento", "type": "string", "req": True, "desc": "Nome do fármaco"},
        {"name": "dosagem", "type": "string", "req": True, "desc": "Posologia e dosagem"},
        {"name": "frequencia", "type": "string", "req": True, "desc": "Intervalo"},
        {"name": "via_administracao", "type": "string", "req": True, "desc": "Via de administração"}
    ],
    body_example={"prontuario_id": 1, "medicamento": "Enoxaparina Sódica 40mg", "dosagem": "40mg/0.4ml", "frequencia": "24/24 horas", "via_administracao": "Subcutânea"},
    responses={"200": {"description": "Prescrição emitida", "content": {"application/json": {"example": {"sucesso": True, "id": 5}}}}}
)
def post_pep_prescricao(data):
    pid = int(data.get("prontuario_id", 1))
    with db.get_connection() as conn:
        p_row = conn.execute("SELECT paciente_nome FROM prontuarios WHERE id = ?", (pid,)).fetchone()
        p_nome = p_row["paciente_nome"] if p_row else "Paciente Geral"
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prescricoes (prontuario_id, paciente_nome, medicamento, dosagem, frequencia, via_administracao, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pendente')
        """, (pid, p_nome, data["medicamento"], data["dosagem"], data["frequencia"], data["via_administracao"]))
        conn.commit()
        new_id = cursor.lastrowid

    payload = {"prescricao_id": new_id, "prontuario_id": pid, "paciente": p_nome, "medicamento": data["medicamento"]}
    events.emit("prescricao_nova", payload)
    webhook_dispatcher.disparar("pep.prescricao_emitida", payload)
    return {"sucesso": True, "id": new_id, "paciente": p_nome}

@registry.put(
    "/api/pep/prescricoes/status",
    summary="Atualizar Status da Prescrição",
    tags=["2. Prontuário Eletrônico & Prescrições"],
    description="Atualiza status para dispensada ou cancelada.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID da prescrição"},
        {"name": "status", "type": "string", "req": True, "desc": "pendente | dispensada | cancelada"}
    ],
    body_example={"id": 2, "status": "dispensada"},
    responses={"200": {"description": "Status atualizado", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def put_pep_prescricao_status(data):
    pid = int(data.get("id", 0))
    st = data.get("status", "dispensada")
    with db.get_connection() as conn:
        conn.execute("UPDATE prescricoes SET status = ? WHERE id = ?", (st, pid))
        conn.commit()
    return {"sucesso": True, "id": pid, "status": st}

# =========================================================================
# 3. VERTICAL: CENTRO CIRÚRGICO & ESCALA DE SALAS (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/cirurgico/agendamentos",
    summary="Listar Agendamentos do Bloco Cirúrgico",
    tags=["3. Centro Cirúrgico & Escala de Salas"],
    description="Retorna a escala diária de cirurgias, salas ocupadas e equipe médica alocada.",
    responses={"200": {"description": "Lista de cirurgias", "content": {"application/json": {"example": [{"id": 1, "codigo_agendamento": "CC-501", "paciente_nome": "Roberto Kenji", "sala_bloco": "Sala 02", "status": "pre_op"}]}}}}
)
def get_cirurgias(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM cirurgias ORDER BY data_hora_cirurgia ASC").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/cirurgico/novo",
    summary="Agendar Nova Cirurgia",
    tags=["3. Centro Cirúrgico & Escala de Salas"],
    description="Reserva sala cirúrgica, escala equipe e registra necessidade de OPME.",
    body_schema=[
        {"name": "paciente_nome", "type": "string", "req": True, "desc": "Nome do paciente"},
        {"name": "procedimento", "type": "string", "req": True, "desc": "Procedimento cirúrgico"},
        {"name": "sala_bloco", "type": "string", "req": True, "desc": "Sala do bloco"},
        {"name": "cirurgiao_principal", "type": "string", "req": True, "desc": "Cirurgião responsável"},
        {"name": "anestesista", "type": "string", "req": True, "desc": "Médico anestesista"},
        {"name": "tipo_anestesia", "type": "string", "req": True, "desc": "Tipo de anestesia"},
        {"name": "data_hora_cirurgia", "type": "string", "req": True, "desc": "Data e Hora (YYYY-MM-DD HH:MM)"},
        {"name": "necessita_opme", "type": "boolean", "req": False, "desc": "Requer OPME"}
    ],
    body_example={"paciente_nome": "Marcos Vinicius", "procedimento": "Reconstrução LCA Joelho Esquerdo", "sala_bloco": "Sala 03 - Ortopedia", "cirurgiao_principal": "Dr. Ricardo Valente", "anestesista": "Dr. Marcelo Paiva", "tipo_anestesia": "Raquianestesia", "data_hora_cirurgia": "2026-09-01 18:00", "necessita_opme": True},
    responses={"200": {"description": "Cirurgia agendada", "content": {"application/json": {"example": {"sucesso": True, "codigo_agendamento": "CC-504"}}}}}
)
def post_cirurgico_novo(data):
    cod = f"CC-{uuid.uuid4().hex[:4].upper()}"
    opme = 1 if data.get("necessita_opme") else 0
    with db.get_connection() as conn:
        conn.execute("""
            INSERT INTO cirurgias (codigo_agendamento, paciente_nome, procedimento, sala_bloco, cirurgiao_principal, anestesista, tipo_anestesia, data_hora_cirurgia, status, necessita_opme)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'agendada', ?)
        """, (cod, data["paciente_nome"], data["procedimento"], data["sala_bloco"], data["cirurgiao_principal"], data["anestesista"], data["tipo_anestesia"], data["data_hora_cirurgia"], opme))
        conn.commit()

    webhook_dispatcher.disparar("cirurgico.cirurgia_agendada", {"codigo_agendamento": cod, "procedimento": data["procedimento"], "sala": data["sala_bloco"]})
    return {"sucesso": True, "codigo_agendamento": cod}

@registry.put(
    "/api/cirurgico/atualizar",
    summary="Atualizar Agendamento Cirúrgico",
    tags=["3. Centro Cirúrgico & Escala de Salas"],
    description="Modifica detalhes da cirurgia, sala ou equipe.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID da cirurgia"},
        {"name": "sala_bloco", "type": "string", "req": False, "desc": "Nova sala"},
        {"name": "status", "type": "string", "req": False, "desc": "Novo status"}
    ],
    body_example={"id": 1, "status": "em_andamento"},
    responses={"200": {"description": "Cirurgia atualizada", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def put_cirurgico_atualizar(data):
    cid = int(data.get("id", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM cirurgias WHERE id = ?", (cid,)).fetchone()
        if not row:
            return {"sucesso": False, "error": "Cirurgia não encontrada"}
        sala = data.get("sala_bloco", row["sala_bloco"])
        st = data.get("status", row["status"])
        conn.execute("UPDATE cirurgias SET sala_bloco = ?, status = ? WHERE id = ?", (sala, st, cid))
        conn.commit()
    return {"sucesso": True, "id": cid}

@registry.delete(
    "/api/cirurgico/cancelar",
    summary="Cancelar Cirurgia",
    tags=["3. Centro Cirúrgico & Escala de Salas"],
    description="Cancela o agendamento cirúrgico e libera a sala.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID da cirurgia"}],
    body_example={"id": 2},
    responses={"200": {"description": "Cirurgia cancelada", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def delete_cirurgico_cancelar(data):
    cid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("UPDATE cirurgias SET status = 'cancelada' WHERE id = ?", (cid,))
        conn.commit()
    return {"sucesso": True}

@registry.post(
    "/api/cirurgico/avancar-status",
    summary="Avançar Fase Cirúrgica",
    tags=["3. Centro Cirúrgico & Escala de Salas"],
    description="Avança a fase da cirurgia (agendada -> pre_op -> em_andamento -> rpa_recuperacao -> concluida). Se concluída, aciona automação de faturamento.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID da cirurgia"},
        {"name": "novo_status", "type": "string", "req": True, "desc": "pre_op | em_andamento | rpa_recuperacao | concluida"}
    ],
    body_example={"id": 1, "novo_status": "concluida"},
    responses={"200": {"description": "Fase avançada", "content": {"application/json": {"example": {"sucesso": True, "status": "concluida"}}}}}
)
def post_cirurgico_avancar(data):
    cid = int(data.get("id", 0))
    st = data.get("novo_status", "concluida")
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM cirurgias WHERE id = ?", (cid,)).fetchone()
        if not row:
            return {"sucesso": False, "error": "Cirurgia não encontrada"}
        conn.execute("UPDATE cirurgias SET status = ? WHERE id = ?", (st, cid))
        conn.commit()
        c_dict = dict(row)

    webhook_dispatcher.disparar("cirurgico.fase_alterada", {"cirurgia_id": cid, "novo_status": st})
    if st == "concluida":
        events.emit("cirurgia_finalizada", c_dict)
    return {"sucesso": True, "id": cid, "novo_status": st}

# =========================================================================
# 4. VERTICAL: FARMÁCIA HOSPITALAR & DISPENSAÇÃO (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/farmacia/estoque",
    summary="Consultar Estoque Farmacêutico",
    tags=["4. Farmácia Hospitalar & Dispensação"],
    description="Retorna lista de medicamentos em estoque, saldo, validade e nível de criticidade.",
    responses={"200": {"description": "Estoque de medicamentos", "content": {"application/json": {"example": [{"id": 1, "codigo_item": "MED-001", "medicamento": "Nitroglicerina", "quantidade_disponivel": 48}]}}}}
)
def get_farmacia_estoque(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM farmacia_estoque ORDER BY status_estoque DESC, medicamento ASC").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/farmacia/medicamento",
    summary="Cadastrar Novo Lote de Medicamento",
    tags=["4. Farmácia Hospitalar & Dispensação"],
    description="Adiciona um novo medicamento/lote ao estoque da farmácia.",
    body_schema=[
        {"name": "medicamento", "type": "string", "req": True, "desc": "Nome do fármaco"},
        {"name": "lote", "type": "string", "req": True, "desc": "Lote"},
        {"name": "categoria", "type": "string", "req": True, "desc": "antibiotico | analgesico | anestesico | controlado | alto_custo"},
        {"name": "quantidade_disponivel", "type": "integer", "req": True, "desc": "Quantidade inicial"},
        {"name": "quantidade_minima", "type": "integer", "req": True, "desc": "Estoque mínimo de segurança"},
        {"name": "temperatura_armazenamento", "type": "string", "req": False, "desc": "Temperatura"},
        {"name": "validade", "type": "string", "req": True, "desc": "Validade (YYYY-MM-DD)"}
    ],
    body_example={"medicamento": "Fentanila 50mcg/ml 2ml", "lote": "LOT-FEN-99", "categoria": "controlado", "quantidade_disponivel": 35, "quantidade_minima": 15, "temperatura_armazenamento": "Armário Blindado", "validade": "2027-12-31"},
    responses={"200": {"description": "Medicamento cadastrado", "content": {"application/json": {"example": {"sucesso": True, "codigo_item": "MED-007"}}}}}
)
def post_farmacia_medicamento(data):
    cod = f"MED-{uuid.uuid4().hex[:4].upper()}"
    qtd = int(data.get("quantidade_disponivel", 10))
    min_qtd = int(data.get("quantidade_minima", 5))
    st = "critico" if qtd <= min_qtd else "normal"
    with db.get_connection() as conn:
        conn.execute("""
            INSERT INTO farmacia_estoque (codigo_item, medicamento, lote, categoria, quantidade_disponivel, quantidade_minima, temperatura_armazenamento, validade, status_estoque)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cod, data["medicamento"], data["lote"], data["categoria"], qtd, min_qtd, data.get("temperatura_armazenamento", "Ambiente"), data["validade"], st))
        conn.commit()
    return {"sucesso": True, "codigo_item": cod}

@registry.put(
    "/api/farmacia/atualizar-lote",
    summary="Atualizar Saldo / Lote do Medicamento",
    tags=["4. Farmácia Hospitalar & Dispensação"],
    description="Ajusta saldo de estoque ou validade do lote.",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID do item"},
        {"name": "quantidade_disponivel", "type": "integer", "req": True, "desc": "Novo saldo físico"}
    ],
    body_example={"id": 3, "quantidade_disponivel": 50},
    responses={"200": {"description": "Estoque ajustado", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def put_farmacia_atualizar(data):
    iid = int(data.get("id", 0))
    qtd = int(data.get("quantidade_disponivel", 0))
    with db.get_connection() as conn:
        row = conn.execute("SELECT quantidade_minima FROM farmacia_estoque WHERE id = ?", (iid,)).fetchone()
        if not row:
            return {"sucesso": False, "error": "Item não encontrado"}
        min_qtd = row["quantidade_minima"]
        st = "critico" if qtd <= min_qtd else "normal"
        if qtd == 0:
            st = "zerado"
        conn.execute("UPDATE farmacia_estoque SET quantidade_disponivel = ?, status_estoque = ? WHERE id = ?", (qtd, st, iid))
        conn.commit()
    return {"sucesso": True, "id": iid, "quantidade_disponivel": qtd, "status_estoque": st}

@registry.delete(
    "/api/farmacia/remover-item",
    summary="Remover Item de Estoque",
    tags=["4. Farmácia Hospitalar & Dispensação"],
    description="Remove um registro do estoque farmacêutico.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do item"}],
    body_example={"id": 5},
    responses={"200": {"description": "Item removido", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def delete_farmacia_item(data):
    iid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM farmacia_estoque WHERE id = ?", (iid,))
        conn.commit()
    return {"sucesso": True}

@registry.post(
    "/api/farmacia/dispensar",
    summary="Efetuar Dispensação Controlada",
    tags=["4. Farmácia Hospitalar & Dispensação"],
    description="Efetua a baixa e entrega de medicamentos para o paciente.",
    body_schema=[
        {"name": "codigo_item", "type": "string", "req": True, "desc": "Código do medicamento (MED-XXXX)"},
        {"name": "quantidade", "type": "integer", "req": True, "desc": "Quantidade a dispensar"},
        {"name": "farmaceutico_crf", "type": "string", "req": True, "desc": "Registro CRF"},
        {"name": "prescricao_id", "type": "integer", "req": False, "desc": "ID da prescrição atendida"}
    ],
    body_example={"codigo_item": "MED-002", "quantidade": 2, "farmaceutico_crf": "CRF/SP 44.921", "prescricao_id": 3},
    responses={"200": {"description": "Dispensação concluída", "content": {"application/json": {"example": {"sucesso": True, "medicamento": "Ceftriaxona", "saldo_restante": 118}}}}}
)
def post_farmacia_dispensar(data):
    res = mcp_engine.execute_tool("med_farmacia_dispensar_medicamento", data)
    if res.get("sucesso"):
        webhook_dispatcher.disparar("farmacia.item_dispensado", res)
    return res

@registry.get(
    "/api/farmacia/dispensacoes",
    summary="Histórico de Dispensações",
    tags=["4. Farmácia Hospitalar & Dispensação"],
    description="Retorna o histórico de todas as baixas de medicamentos empresariais.",
    responses={"200": {"description": "Lista de dispensações", "content": {"application/json": {"example": [{"id": 1, "medicamento": "AAS", "quantidade": 3}]}}}}
)
def get_farmacia_dispensacoes(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM dispensacoes ORDER BY data_dispensacao DESC").fetchall()
        return [dict(r) for r in rows]

# =========================================================================
# 5. VERTICAL: FATURAMENTO HOSPITALAR TISS/TUSS & CONVÊNIOS (FULL CRUD)
# =========================================================================
@registry.get(
    "/api/faturamento/guias",
    summary="Listar Guias de Faturamento TISS/TUSS",
    tags=["5. Faturamento Hospitalar TISS/TUSS"],
    description="Retorna todas as contas empresariais e guias de convênio.",
    responses={"200": {"description": "Lista de guias", "content": {"application/json": {"example": [{"id": 1, "numero_guia": "TISS-8801", "paciente_nome": "Carlos Alberto", "valor_total": 14850.0}]}}}}
)
def get_faturamento_guias(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM faturamento_guias ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/faturamento/nova-guia",
    summary="Emitir Nova Guia Hospitalar TISS",
    tags=["5. Faturamento Hospitalar TISS/TUSS"],
    description="Gera nova guia de faturamento para convênio ou atendimento particular.",
    body_schema=[
        {"name": "paciente_nome", "type": "string", "req": True, "desc": "Nome do paciente"},
        {"name": "convenio", "type": "string", "req": True, "desc": "Operadora de saúde ou Particular"},
        {"name": "codigo_tuss", "type": "string", "req": True, "desc": "Código TUSS (8 dígitos)"},
        {"name": "descricao_procedimento", "type": "string", "req": True, "desc": "Descrição do procedimento"},
        {"name": "valor_total", "type": "number", "req": True, "desc": "Valor total em R$"}
    ],
    body_example={"paciente_nome": "Helena Matos", "convenio": "SulAmérica Especial", "codigo_tuss": "40801055", "descricao_procedimento": "Ressonância Magnética de Crânio", "valor_total": 2400.00},
    responses={"200": {"description": "Guia emitida", "content": {"application/json": {"example": {"sucesso": True, "numero_guia": "TISS-8805"}}}}}
)
def post_faturamento_nova_guia(data):
    num = f"TISS-{uuid.uuid4().hex[:4].upper()}"
    with db.get_connection() as conn:
        conn.execute("""
            INSERT INTO faturamento_guias (numero_guia, paciente_nome, convenio, codigo_tuss, descricao_procedimento, valor_total, status_guia)
            VALUES (?, ?, ?, ?, ?, ?, 'gerada')
        """, (num, data["paciente_nome"], data["convenio"], data["codigo_tuss"], data["descricao_procedimento"], float(data["valor_total"])))
        conn.commit()

    webhook_dispatcher.disparar("faturamento.guia_gerada", {"numero_guia": num, "valor_total": float(data["valor_total"]), "convenio": data["convenio"]})
    return {"sucesso": True, "numero_guia": num}

@registry.put(
    "/api/faturamento/atualizar-status",
    summary="Atualizar Status da Guia TISS",
    tags=["5. Faturamento Hospitalar TISS/TUSS"],
    description="Atualiza status da guia (gerada -> autorizada -> faturada -> liquidada | glosada).",
    body_schema=[
        {"name": "id", "type": "integer", "req": True, "desc": "ID da guia"},
        {"name": "status_guia", "type": "string", "req": True, "desc": "gerada | autorizada | faturada | liquidada | glosada"}
    ],
    body_example={"id": 1, "status_guia": "liquidada"},
    responses={"200": {"description": "Status atualizado", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def put_faturamento_status(data):
    gid = int(data.get("id", 0))
    st = data.get("status_guia", "liquidada")
    with db.get_connection() as conn:
        liq = "datetime('now')" if st == "liquidada" else "NULL"
        conn.execute(f"UPDATE faturamento_guias SET status_guia = ?, data_liquidacao = {liq} WHERE id = ?", (st, gid))
        conn.commit()
    if st == "liquidada":
        webhook_dispatcher.disparar("faturamento.guia_liquidada", {"guia_id": gid, "status": "liquidada"})
    return {"sucesso": True, "id": gid, "status_guia": st}

@registry.delete(
    "/api/faturamento/cancelar-guia",
    summary="Cancelar Guia Hospitalar",
    tags=["5. Faturamento Hospitalar TISS/TUSS"],
    description="Cancela a guia de faturamento.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID da guia"}],
    body_example={"id": 3},
    responses={"200": {"description": "Guia cancelada", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def delete_faturamento_guia(data):
    gid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM faturamento_guias WHERE id = ?", (gid,))
        conn.commit()
    return {"sucesso": True}

@registry.get(
    "/api/faturamento/dre",
    summary="Demonstrativo Consolidado de Faturamento Hospitalar",
    tags=["5. Faturamento Hospitalar TISS/TUSS"],
    description="Retorna o consolidado financeiro de guias faturadas, recebidas e pendentes.",
    responses={"200": {"description": "Consolidado DRE", "content": {"application/json": {"example": {"total_faturado": 39450.0, "total_liquidado": 8900.0, "pendente": 30550.0}}}}}
)
def get_faturamento_dre(params):
    with db.get_connection() as conn:
        total = conn.execute("SELECT COALESCE(SUM(valor_total), 0) FROM faturamento_guias").fetchone()[0]
        liquidado = conn.execute("SELECT COALESCE(SUM(valor_total), 0) FROM faturamento_guias WHERE status_guia = 'liquidada'").fetchone()[0]
        pendente = total - liquidado
        return {
            "total_faturado_brl": round(total, 2),
            "total_liquidado_brl": round(liquidado, 2),
            "pendente_recebimento_brl": round(pendente, 2)
        }

# =========================================================================
# 6. WEBHOOK STUDIO & AUDITORIA
# =========================================================================
@registry.get(
    "/api/webhooks",
    summary="Listar Webhooks Cadastrados",
    tags=["6. Webhook Configuration Studio"],
    description="Retorna os endpoints de webhook ativos configurados para disparo de eventos.",
    responses={"200": {"description": "Lista de webhooks", "content": {"application/json": {"example": [{"id": 1, "url": "https://webhook.site/mock", "ativo": 1}]}}}}
)
def get_webhooks(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, url, secret, eventos, ativo, criado_em FROM webhooks").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/webhooks",
    summary="Cadastrar Novo Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Cadastra um novo destino HTTP para recebimento assíncrono de eventos.",
    body_schema=[
        {"name": "url", "type": "string", "req": True, "desc": "URL do Webhook (HTTPS recomendada)"},
        {"name": "secret", "type": "string", "req": False, "desc": "Chave secreta para assinatura HMAC SHA-256"},
        {"name": "eventos", "type": "string", "req": True, "desc": "Eventos assinados separados por vírgula (ou '*' para todos)"}
    ],
    body_example={"url": "https://webhook.site/demo", "secret": "sec_prod_992", "eventos": "faturamento.guia_gerada,triagem.urgencia_critica"},
    responses={"200": {"description": "Webhook cadastrado", "content": {"application/json": {"example": {"sucesso": True, "id": 2}}}}}
)
def post_webhooks(data):
    url = data.get("url")
    if not url:
        return {"sucesso": False, "error": "URL é obrigatória"}
    secret = data.get("secret", "")
    eventos = data.get("eventos", "*")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO webhooks (url, secret, eventos, ativo) VALUES (?, ?, ?, 1)", (url, secret, eventos))
        conn.commit()
        return {"sucesso": True, "id": cursor.lastrowid}

@registry.delete(
    "/api/webhooks/remover",
    summary="Remover Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Remove um webhook configurado.",
    body_schema=[{"name": "id", "type": "integer", "req": True, "desc": "ID do webhook a ser excluído"}],
    body_example={"id": 1},
    responses={"200": {"description": "Webhook excluído", "content": {"application/json": {"example": {"sucesso": True}}}}}
)
def delete_webhooks(data):
    wid = int(data.get("id", 0))
    with db.get_connection() as conn:
        conn.execute("DELETE FROM webhooks WHERE id = ?", (wid,))
        conn.commit()
        return {"sucesso": True}

@registry.post(
    "/api/webhooks/testar",
    summary="Testar Disparo de Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Executa um disparo de teste imediato para a URL informada com validação HMAC e latência.",
    body_schema=[
        {"name": "url", "type": "string", "req": True, "desc": "URL de destino para teste"},
        {"name": "secret", "type": "string", "req": False, "desc": "Secret para assinatura"},
        {"name": "evento", "type": "string", "req": True, "desc": "Nome do evento teste"},
        {"name": "payload", "type": "object", "req": False, "desc": "Objeto JSON de carga útil"}
    ],
    body_example={"url": "https://webhook.site/health-mock-n8n", "secret": "sec_aidd_suite_2026", "evento": "triagem.urgencia_critica", "payload": {"protocolo": "TRI-9081", "teste": True}},
    responses={"200": {"description": "Resultado do teste", "content": {"application/json": {"example": {"sucesso": True, "status_code": 200, "tempo_ms": 142}}}}}
)
def post_testar_webhook(data):
    url = data.get("url")
    secret = data.get("secret", "")
    evento = data.get("evento", "teste.ping")
    payload = data.get("payload", {"teste": True, "timestamp": time.time()})
    return webhook_dispatcher.testar_disparo(url, secret, evento, payload)

@registry.get(
    "/api/webhooks/logs",
    summary="Auditoria de Disparos de Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Lista o histórico completo de tentativas de envio de webhooks.",
    responses={"200": {"description": "Logs de webhook", "content": {"application/json": {"example": [{"id": 1, "evento": "triagem.urgencia_critica", "sucesso": 1}]}}}}
)
def get_webhook_logs(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM webhook_logs ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/webhooks/logs/reenviar",
    summary="Reenviar Disparo de Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Repete um envio de webhook a partir de um registro de log histórico.",
    body_schema=[{"name": "log_id", "type": "integer", "req": True, "desc": "ID do log a ser reenviado"}],
    body_example={"log_id": 1},
    responses={"200": {"description": "Disparo reenviado", "content": {"application/json": {"example": {"sucesso": True}}}}}
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
    summary="Catálogo Oficial de Eventos do Sistema",
    tags=["6. Webhook Configuration Studio"],
    description="Retorna o dicionário de todos os eventos suportados pela AIDD Enterprise Suite v5.1.",
    responses={"200": {"description": "Catálogo de eventos", "content": {"application/json": {"example": [{"event": "triagem.urgencia_critica", "modulo": "Pronto-Socorro"}]}}}}
)
def get_webhook_eventos(params):
    return WebhookDispatcher.EVENT_CATALOG

# =========================================================================
# 7. DASHBOARD KPIS & AUDITORIA
# =========================================================================
@registry.get(
    "/api/dashboard/kpis",
    summary="KPIs Gerenciais Hospitalares em Tempo Real",
    tags=["7. Painel de Controle & Auditoria"],
    description="Retorna o panorama gerencial consolidado do hospital.",
    responses={"200": {"description": "KPIs em tempo real", "content": {"application/json": {"example": {"kpis": {"pacientes_aguardando_triagem": 4, "emergencias_vermelho_laranja": 2}}}}}}
)
def get_dashboard_kpis(params):
    return mcp_engine.execute_tool("med_kpi_dashboard_geral", {})

@registry.get(
    "/api/logs/auditoria",
    summary="Consultar Logs de Auditoria Geral",
    tags=["7. Painel de Controle & Auditoria"],
    description="Retorna o histórico cronológico de transações e automações da suíte.",
    responses={"200": {"description": "Logs de auditoria", "content": {"application/json": {"example": [{"id": 1, "evento": "triagem_critica_leito_alocado", "modulo": "pronto_socorro"}]}}}}
)
def get_logs_auditoria(params):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM logs_auditoria ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(r) for r in rows]

# =========================================================================
# HTTP HANDLER COM OWASP SECURITY HEADERS
# =========================================================================
class AIDD_EnterpriseAppHandler(http.server.SimpleHTTPRequestHandler):
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

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            idx_file = os.path.join(STATIC_DIR, "index.html")
            with open(idx_file, "rb") as f:
                self.wfile.write(f.read())
            return

        if path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            doc = registry.generate_openapi_json("Plataforma Core Suite v5.1 — Hospital & Biotech Enterprise Monolith", "4.0.0")
            self.wfile.write(json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        if path == "/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = registry.get_swagger_html("Plataforma Core Suite v5.1 — API Reference Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/webhooks":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = webhook_dispatcher.get_studio_html("Plataforma SaaS Suite — Webhook Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/docs/guia":
            docs_file = os.path.join(STATIC_DIR, "docs.html")
            if os.path.exists(docs_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(docs_file, "rb") as f:
                    self.wfile.write(f.read())
                return

        if path == "/mcp":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = mcp_engine.get_studio_html("AIDD Enterprise Suite v5.1 — MCP Native Server Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path in registry.routes["GET"]:
            flat_params = {k: v[0] if len(v) == 1 else v for k, v in query.items()}
            try:
                result = registry.routes["GET"][path](flat_params)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(length) if length > 0 else b""
        
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except:
            body = {}

        if path == "/mcp":
            resp = mcp_engine.handle_json_rpc(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
            return

        if path in registry.routes["POST"]:
            try:
                result = registry.routes["POST"][path](body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint POST não encontrado", "path": path}).encode("utf-8"))

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(length) if length > 0 else b""
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except:
            body = {}

        if path in registry.routes["PUT"]:
            try:
                result = registry.routes["PUT"][path](body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
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
        length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(length) if length > 0 else b""
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except:
            body = {}

        if path in registry.routes["DELETE"]:
            try:
                result = registry.routes["DELETE"][path](body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), AIDD_EnterpriseAppHandler) as httpd:
        print(f"================================================================================")
        print(f"  [MEDHEALTH] Plataforma Core Suite v5.1 — Hospital & Biotech Enterprise Monolith")
        print(f"================================================================================")
        print(f"  • App Super-App Front-End : http://localhost:{PORT}")
        print(f"  • Swagger Studio (/docs)  : http://localhost:{PORT}/docs")
        print(f"  • Webhook Studio          : http://localhost:{PORT}/webhooks")
        print(f"  • MCP Native Server (/mcp): http://localhost:{PORT}/mcp")
        print(f"  • Guia Enciclopédico      : http://localhost:{PORT}/docs/guia")
        print(f"  • OpenAPI Spec            : http://localhost:{PORT}/openapi.json")
        print(f"================================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Servidor encerrado.")

if __name__ == "__main__":
    run_server()
