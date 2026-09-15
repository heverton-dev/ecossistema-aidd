"""
AIDD v6.1 — FastAPI Server (Structured Logging + OpenTelemetry)
================================================================
Migra server.py de http.server para FastAPI. Todas as dependencias
(FastAPI, uvicorn, Pydantic) ja estao em requirements.txt.

Beneficios vs. http.server:
  - OpenAPI 3.1 nativo (elimina RouteRegistry para docs)
  - Validacao Pydantic automatica no body/params
  - Async nativo com uvicorn
  - OWASP headers via middleware (elimina handler manual)
  - Error handling estruturado
  - Structured logging via structlog (JSON em prod, pretty em dev)
  - Distributed tracing via OpenTelemetry + OTLP exporter
  - 500+ linhas de NIH eliminadas

Uso:
  python src/server_fastapi.py
  # ou
  uvicorn src.server_fastapi:app --host 0.0.0.0 --port 3000
"""

import os, sys, json, uuid, time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Structured Logging + OpenTelemetry (must init before app creation)
# ---------------------------------------------------------------------------
from logging_config import setup_logging, setup_otel

setup_logging()
tracer = setup_otel(service_name="aidd-enterprise")

import structlog
logger = structlog.stdlib.get_logger("aidd.server")

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Any
import uvicorn

from core.database import Database
from core.events import EventBus
from core.webhooks import WebhookDispatcher
from core.models import init_all_schemas
from core.mcp_server import AIDD_EnterpriseMCPServer
from core.security import SecurityService, JWTService
from core.repositories import (
    TriagemRepository, PepRepository, CirurgicoRepository,
    FarmaciaRepository, FaturamentoRepository, AuditoriaRepository,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PORT = int(os.environ.get("PORT", 3000))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "suite.db")

# ---------------------------------------------------------------------------
# Bootstrap — identico ao server.py original
# ---------------------------------------------------------------------------
db = Database(f"sqlite:///{DB_PATH}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)
mcp_engine = AIDD_EnterpriseMCPServer(DB_PATH)
triagem_repo = TriagemRepository(db)
pep_repo = PepRepository(db)
cirurgico_repo = CirurgicoRepository(db)
farmacia_repo = FarmaciaRepository(db)
faturamento_repo = FaturamentoRepository(db)
auditoria_repo = AuditoriaRepository(db)

with db.get_connection() as conn:
    init_all_schemas(conn)

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AIDD Enterprise Suite v5.1",
    description="Hospital & Biotech Enterprise Monolith — Clean Architecture Cross-Domain",
    version="5.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# OpenTelemetry FastAPI Instrumentation (auto-traces every request)
# ---------------------------------------------------------------------------
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
    logger.info("opentelemetry_fastapi_instrumented")
except Exception as exc:
    logger.warning("opentelemetry_instrumentation_skipped", error=str(exc))

# OWASP Security Headers via Middleware (substitui handler manual de 200 linhas)
@app.middleware("http")
async def owasp_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    for header, value in SecurityService.get_security_headers().items():
        response.headers[header] = value
    return response

# CORS — restrito em producao, aberto em dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic Models (validacao automatica — elimina body_schema manual)
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str = Field(..., examples=["medico@hospital.com"])
    password: str = Field(..., examples=["admin"])

class TriagemRequest(BaseModel):
    paciente_nome: str
    idade: int = 30
    sinais_vitais: str = "Estavel"
    queixa_principal: str = "Dor leve"
    classificacao: str = "verde"

class TriagemUpdateRequest(BaseModel):
    id: int
    sinais_vitais: Optional[str] = None
    classificacao: Optional[str] = None
    status: Optional[str] = None

class TriagemChamarRequest(BaseModel):
    id: int
    leito: str = "Box Geral"

class PEPRequest(BaseModel):
    paciente_nome: str
    medico_responsavel: str
    crm: str
    diagnostico_cid10: str
    evolucao_clinica: str
    alergias: str = "Nega alergias"

class PEPUpdateRequest(BaseModel):
    id: int
    evolucao_clinica: str
    diagnostico_cid10: Optional[str] = None

class PrescricaoRequest(BaseModel):
    prontuario_id: int
    medicamento: str
    dosagem: str
    frequencia: str
    via_administracao: str

class PrescricaoStatusRequest(BaseModel):
    id: int
    status: str

class CirurgiaRequest(BaseModel):
    paciente_nome: str
    procedimento: str
    sala_bloco: str
    cirurgiao_principal: str
    anestesista: str
    tipo_anestesia: str
    data_hora_cirurgia: str
    necessita_opme: bool = False

class CirurgiaUpdateRequest(BaseModel):
    id: int
    sala_bloco: Optional[str] = None
    status: Optional[str] = None

class CirurgiaAvancarRequest(BaseModel):
    id: int
    novo_status: str

class MedicamentoRequest(BaseModel):
    medicamento: str
    lote: str
    categoria: str
    quantidade_disponivel: int
    quantidade_minima: int
    temperatura_armazenamento: str = "Ambiente"
    validade: str

class MedicamentoUpdateRequest(BaseModel):
    id: int
    quantidade_disponivel: int

class GuiaRequest(BaseModel):
    paciente_nome: str
    convenio: str
    codigo_tuss: str
    descricao_procedimento: str
    valor_total: float

class GuiaStatusRequest(BaseModel):
    id: int
    status_guia: str

class WebhookRequest(BaseModel):
    url: str
    secret: str = ""
    eventos: str = "*"

class WebhookTestRequest(BaseModel):
    url: str
    secret: str = ""
    evento: str = "teste.ping"
    payload: dict = {}

# ---------------------------------------------------------------------------
# Cross-Domain Event Handlers (identicos ao original)
# ---------------------------------------------------------------------------
def on_triagem_critica(dados):
    if dados.get("classificacao") in ["vermelho", "laranja"]:
        leito = "UTI Emergencia 01" if dados["classificacao"] == "vermelho" else "Box Observacao Rapida"
        triagem_repo.alocar_leito_por_protocolo(dados.get("protocolo"), leito)
        auditoria_repo.registrar("triagem_critica_leito_alocado", "pronto_socorro", json.dumps(dados, ensure_ascii=False))
        webhook_dispatcher.disparar("cross_domain.triagem_critica_to_leito", {
            "protocolo": dados.get("protocolo"), "paciente": dados.get("paciente_nome"),
            "leito": leito, "classificacao": dados["classificacao"],
        })

def on_prescricao_emitida(dados):
    auditoria_repo.registrar("prescricao_emitida_automacao", "pep_clinico", json.dumps(dados, ensure_ascii=False))
    webhook_dispatcher.disparar("cross_domain.prescricao_to_farmacia", dados)

def on_cirurgia_concluida(dados):
    num_guia = f"TISS-{uuid.uuid4().hex[:4].upper()}"
    valor = 12500.00 if dados.get("necessita_opme") else 7800.00
    faturamento_repo.criar_guia_cirurgia(num_guia, dados.get("paciente_nome"), f"Procedimento Cirurgico: {dados.get('procedimento')}", valor)
    auditoria_repo.registrar("cirurgia_faturada_cross_domain", "centro_cirurgico", json.dumps(dados, ensure_ascii=False))
    webhook_dispatcher.disparar("cross_domain.cirurgia_to_faturamento", {
        "numero_guia": num_guia, "paciente": dados.get("paciente_nome"),
        "valor": valor, "procedimento": dados.get("procedimento"),
    })

events.on("triagem_urgencia", on_triagem_critica)
events.on("prescricao_nova", on_prescricao_emitida)
events.on("cirurgia_finalizada", on_cirurgia_concluida)

# ---------------------------------------------------------------------------
# 0. AUTENTICACAO JWT
# ---------------------------------------------------------------------------
@app.post("/api/auth/login", tags=["0. Autenticacao & Seguranca"], summary="Autenticacao JWT (Login)")
def post_login(data: LoginRequest):
    token = JWTService.encode({"sub": data.email, "role": "medico_chefe", "name": "Dr. Diretor Clinico"})
    payload = {"email": data.email, "role": "medico_chefe"}
    events.emit("usuario_autenticado", payload)
    webhook_dispatcher.disparar("auth.login_sucesso", payload)
    return {"sucesso": True, "token": token, "tipo": "Bearer", "expira_em": 86400,
            "usuario": {"email": data.email, "role": "medico_chefe", "nome": "Dr. Diretor Clinico"}}

@app.get("/api/auth/me", tags=["0. Autenticacao & Seguranca"], summary="Verificar Sessao do Usuario")
def get_auth_me():
    return {"autenticado": True, "usuario": {"email": "medico@hospital.com", "role": "medico_chefe", "status": "ativo"}}

# ---------------------------------------------------------------------------
# 1. PRONTO-SOCORRO & TRIAGEM MANCHESTER
# ---------------------------------------------------------------------------
@app.get("/api/triagem/pacientes", tags=["1. Pronto-Socorro & Triagem"], summary="Listar Fila de Triagem Manchester")
def get_triagens():
    return triagem_repo.listar()

@app.post("/api/triagem/novo", tags=["1. Pronto-Socorro & Triagem"], summary="Classificar Novo Paciente (Manchester)")
def post_triagem_novo(data: TriagemRequest):
    slas = {"vermelho": 0, "laranja": 10, "amarelo": 60, "verde": 120, "azul": 240}
    cls = data.classificacao.lower()
    sla = slas.get(cls, 120)
    proto = f"TRI-{uuid.uuid4().hex[:4].upper()}"
    triagem_repo.criar(proto, data.paciente_nome, data.idade, data.sinais_vitais, data.queixa_principal, cls, sla)
    payload = {"protocolo": proto, "paciente_nome": data.paciente_nome, "classificacao": cls, "sla_min": sla}
    events.emit("triagem_urgencia", payload)
    webhook_dispatcher.disparar("triagem.paciente_admitido", payload)
    return {"sucesso": True, "protocolo": proto, "classificacao": cls, "tempo_espera_max_min": sla}

@app.put("/api/triagem/atualizar", tags=["1. Pronto-Socorro & Triagem"], summary="Atualizar Triagem de Paciente")
def put_triagem_atualizar(data: TriagemUpdateRequest):
    row = triagem_repo.obter(data.id)
    if not row:
        raise HTTPException(404, "Triagem nao encontrada")
    triagem_repo.atualizar(data.id, data.sinais_vitais or row["sinais_vitais"], data.status or row["status"], data.classificacao or row["classificacao"])
    return {"sucesso": True, "id": data.id}

@app.delete("/api/triagem/remover", tags=["1. Pronto-Socorro & Triagem"], summary="Remover Registro de Triagem")
def delete_triagem(id: int):
    triagem_repo.remover(id)
    return {"sucesso": True}

@app.post("/api/triagem/chamar", tags=["1. Pronto-Socorro & Triagem"], summary="Chamar Paciente para Leito / Box")
def post_triagem_chamar(data: TriagemChamarRequest):
    triagem_repo.alocar_leito(data.id, data.leito)
    return {"sucesso": True, "id": data.id, "leito": data.leito}

# ---------------------------------------------------------------------------
# 2. PRONTUARIO ELETRONICO (PEP) & PRESCRICOES
# ---------------------------------------------------------------------------
@app.get("/api/pep/prontuarios", tags=["2. PEP & Prescricoes"], summary="Listar Prontuarios Eletronicos")
def get_pep_prontuarios():
    return pep_repo.listar_prontuarios()

@app.post("/api/pep/prontuarios", tags=["2. PEP & Prescricoes"], summary="Criar Novo Prontuario Eletronico")
def post_pep_prontuario(data: PEPRequest):
    num = f"PEP-{uuid.uuid4().hex[:4].upper()}"
    pep_repo.criar_prontuario(num, data.paciente_nome, data.medico_responsavel, data.crm, data.diagnostico_cid10, data.evolucao_clinica, data.alergias)
    webhook_dispatcher.disparar("pep.prontuario_atualizado", {"numero_prontuario": num, "paciente": data.paciente_nome})
    return {"sucesso": True, "numero_prontuario": num}

@app.put("/api/pep/prontuarios", tags=["2. PEP & Prescricoes"], summary="Atualizar Evolucao Clinica")
def put_pep_prontuario(data: PEPUpdateRequest):
    row = pep_repo.obter_prontuario(data.id)
    if not row:
        raise HTTPException(404, "Prontuario nao encontrado")
    pep_repo.atualizar_prontuario(data.id, data.evolucao_clinica, data.diagnostico_cid10 or row["diagnostico_cid10"])
    return {"sucesso": True, "id": data.id}

@app.delete("/api/pep/prontuarios", tags=["2. PEP & Prescricoes"], summary="Arquivar / Remover Prontuario")
def delete_pep_prontuario(id: int):
    pep_repo.remover_prontuario(id)
    return {"sucesso": True}

@app.get("/api/pep/prescricoes", tags=["2. PEP & Prescricoes"], summary="Listar Prescricoes Medicas Digitais")
def get_pep_prescricoes():
    return pep_repo.listar_prescricoes()

@app.post("/api/pep/prescricoes", tags=["2. PEP & Prescricoes"], summary="Emitir Nova Prescricao Digital")
def post_pep_prescricao(data: PrescricaoRequest):
    p_nome = pep_repo.obter_paciente_nome(data.prontuario_id) or "Paciente Geral"
    new_id = pep_repo.criar_prescricao(data.prontuario_id, p_nome, data.medicamento, data.dosagem, data.frequencia, data.via_administracao)
    payload = {"prescricao_id": new_id, "prontuario_id": data.prontuario_id, "paciente": p_nome, "medicamento": data.medicamento}
    events.emit("prescricao_nova", payload)
    webhook_dispatcher.disparar("pep.prescricao_emitida", payload)
    return {"sucesso": True, "id": new_id, "paciente": p_nome}

@app.put("/api/pep/prescricoes/status", tags=["2. PEP & Prescricoes"], summary="Atualizar Status da Prescricao")
def put_pep_prescricao_status(data: PrescricaoStatusRequest):
    pep_repo.atualizar_status_prescricao(data.id, data.status)
    return {"sucesso": True, "id": data.id, "status": data.status}

# ---------------------------------------------------------------------------
# 3. CENTRO CIRURGICO & ESCALA DE SALAS
# ---------------------------------------------------------------------------
@app.get("/api/cirurgico/agendamentos", tags=["3. Centro Cirurgico"], summary="Listar Agendamentos do Bloco Cirurgico")
def get_cirurgias():
    return cirurgico_repo.listar()

@app.post("/api/cirurgico/novo", tags=["3. Centro Cirurgico"], summary="Agendar Nova Cirurgia")
def post_cirurgico_novo(data: CirurgiaRequest):
    cod = f"CC-{uuid.uuid4().hex[:4].upper()}"
    opme = 1 if data.necessita_opme else 0
    cirurgico_repo.criar(cod, data.paciente_nome, data.procedimento, data.sala_bloco, data.cirurgiao_principal, data.anestesista, data.tipo_anestesia, data.data_hora_cirurgia, opme)
    webhook_dispatcher.disparar("cirurgico.cirurgia_agendada", {"codigo_agendamento": cod, "procedimento": data.procedimento, "sala": data.sala_bloco})
    return {"sucesso": True, "codigo_agendamento": cod}

@app.put("/api/cirurgico/atualizar", tags=["3. Centro Cirurgico"], summary="Atualizar Agendamento Cirurgico")
def put_cirurgico_atualizar(data: CirurgiaUpdateRequest):
    row = cirurgico_repo.obter(data.id)
    if not row:
        raise HTTPException(404, "Cirurgia nao encontrada")
    cirurgico_repo.atualizar(data.id, data.sala_bloco or row["sala_bloco"], data.status or row["status"])
    return {"sucesso": True, "id": data.id}

@app.delete("/api/cirurgico/cancelar", tags=["3. Centro Cirurgico"], summary="Cancelar Cirurgia")
def delete_cirurgico_cancelar(id: int):
    cirurgico_repo.cancelar(id)
    return {"sucesso": True}

@app.post("/api/cirurgico/avancar-status", tags=["3. Centro Cirurgico"], summary="Avancar Fase Cirurgica")
def post_cirurgico_avancar(data: CirurgiaAvancarRequest):
    row = cirurgico_repo.obter(data.id)
    if not row:
        raise HTTPException(404, "Cirurgia nao encontrada")
    cirurgico_repo.atualizar_status(data.id, data.novo_status)
    webhook_dispatcher.disparar("cirurgico.fase_alterada", {"cirurgia_id": data.id, "novo_status": data.novo_status})
    if data.novo_status == "concluida":
        events.emit("cirurgia_finalizada", row)
    return {"sucesso": True, "id": data.id, "novo_status": data.novo_status}

# ---------------------------------------------------------------------------
# 4. FARMACIA HOSPITALAR & DISPENSACAO
# ---------------------------------------------------------------------------
@app.get("/api/farmacia/estoque", tags=["4. Farmacia Hospitalar"], summary="Consultar Estoque Farmaceutico")
def get_farmacia_estoque():
    return farmacia_repo.listar_estoque()

@app.post("/api/farmacia/medicamento", tags=["4. Farmacia Hospitalar"], summary="Cadastrar Novo Lote de Medicamento")
def post_farmacia_medicamento(data: MedicamentoRequest):
    cod = f"MED-{uuid.uuid4().hex[:4].upper()}"
    st = "critico" if data.quantidade_disponivel <= data.quantidade_minima else "normal"
    farmacia_repo.criar_item(cod, data.medicamento, data.lote, data.categoria, data.quantidade_disponivel, data.quantidade_minima, data.temperatura_armazenamento, data.validade, st)
    return {"sucesso": True, "codigo_item": cod}

@app.put("/api/farmacia/atualizar-lote", tags=["4. Farmacia Hospitalar"], summary="Atualizar Saldo / Lote")
def put_farmacia_atualizar(data: MedicamentoUpdateRequest):
    min_qtd = farmacia_repo.obter_quantidade_minima(data.id)
    if min_qtd is None:
        raise HTTPException(404, "Item nao encontrado")
    st = "zerado" if data.quantidade_disponivel == 0 else ("critico" if data.quantidade_disponivel <= min_qtd else "normal")
    farmacia_repo.atualizar_saldo(data.id, data.quantidade_disponivel, st)
    return {"sucesso": True, "id": data.id, "quantidade_disponivel": data.quantidade_disponivel, "status_estoque": st}

@app.delete("/api/farmacia/remover-item", tags=["4. Farmacia Hospitalar"], summary="Remover Item de Estoque")
def delete_farmacia_item(id: int):
    farmacia_repo.remover_item(id)
    return {"sucesso": True}

@app.post("/api/farmacia/dispensar", tags=["4. Farmacia Hospitalar"], summary="Efetuar Dispensacao Controlada")
def post_farmacia_dispensar(data: dict):
    res = mcp_engine.execute_tool("med_farmacia_dispensar_medicamento", data)
    if res.get("sucesso"):
        webhook_dispatcher.disparar("farmacia.item_dispensado", res)
    return res

@app.get("/api/farmacia/dispensacoes", tags=["4. Farmacia Hospitalar"], summary="Historico de Dispensacoes")
def get_farmacia_dispensacoes():
    return farmacia_repo.listar_dispensacoes()

# ---------------------------------------------------------------------------
# 5. FATURAMENTO HOSPITALAR TISS/TUSS
# ---------------------------------------------------------------------------
@app.get("/api/faturamento/guias", tags=["5. Faturamento TISS/TUSS"], summary="Listar Guias de Faturamento")
def get_faturamento_guias():
    return faturamento_repo.listar_guias()

@app.post("/api/faturamento/nova-guia", tags=["5. Faturamento TISS/TUSS"], summary="Emitir Nova Guia Hospitalar TISS")
def post_faturamento_nova_guia(data: GuiaRequest):
    num = f"TISS-{uuid.uuid4().hex[:4].upper()}"
    faturamento_repo.criar_guia(num, data.paciente_nome, data.convenio, data.codigo_tuss, data.descricao_procedimento, data.valor_total)
    webhook_dispatcher.disparar("faturamento.guia_gerada", {"numero_guia": num, "valor_total": data.valor_total, "convenio": data.convenio})
    return {"sucesso": True, "numero_guia": num}

@app.put("/api/faturamento/atualizar-status", tags=["5. Faturamento TISS/TUSS"], summary="Atualizar Status da Guia TISS")
def put_faturamento_status(data: GuiaStatusRequest):
    faturamento_repo.atualizar_status(data.id, data.status_guia)
    if data.status_guia == "liquidada":
        webhook_dispatcher.disparar("faturamento.guia_liquidada", {"guia_id": data.id, "status": "liquidada"})
    return {"sucesso": True, "id": data.id, "status_guia": data.status_guia}

@app.delete("/api/faturamento/cancelar-guia", tags=["5. Faturamento TISS/TUSS"], summary="Cancelar Guia Hospitalar")
def delete_faturamento_guia(id: int):
    faturamento_repo.remover_guia(id)
    return {"sucesso": True}

@app.get("/api/faturamento/dre", tags=["5. Faturamento TISS/TUSS"], summary="Demonstrativo Consolidado DRE")
def get_faturamento_dre():
    total, liquidado = faturamento_repo.dre()
    pendente = total - liquidado
    return {"total_faturado_brl": round(total, 2), "total_liquidado_brl": round(liquidado, 2), "pendente_recebimento_brl": round(pendente, 2)}

# ---------------------------------------------------------------------------
# 6. WEBHOOK STUDIO & AUDITORIA
# ---------------------------------------------------------------------------
@app.get("/api/webhooks", tags=["6. Webhook Studio"], summary="Listar Webhooks Cadastrados")
def get_webhooks():
    return webhook_dispatcher.listar_webhooks()

@app.post("/api/webhooks", tags=["6. Webhook Studio"], summary="Cadastrar Novo Webhook")
def post_webhooks(data: WebhookRequest):
    new_id = webhook_dispatcher.cadastrar_webhook(data.url, data.secret, data.eventos)
    return {"sucesso": True, "id": new_id}

@app.delete("/api/webhooks/remover", tags=["6. Webhook Studio"], summary="Remover Webhook")
def delete_webhooks(id: int):
    webhook_dispatcher.remover_webhook(id)
    return {"sucesso": True}

@app.post("/api/webhooks/testar", tags=["6. Webhook Studio"], summary="Testar Disparo de Webhook")
def post_testar_webhook(data: WebhookTestRequest):
    return webhook_dispatcher.testar_disparo(data.url, data.secret, data.evento, data.payload)

@app.get("/api/webhooks/logs", tags=["6. Webhook Studio"], summary="Auditoria de Disparos de Webhook")
def get_webhook_logs():
    return webhook_dispatcher.listar_logs(limite=50)

@app.post("/api/webhooks/logs/reenviar", tags=["6. Webhook Studio"], summary="Reenviar Disparo de Webhook")
def post_reenviar_webhook_log(log_id: int):
    row = webhook_dispatcher.obter_log(log_id)
    if not row:
        raise HTTPException(404, "Log nao encontrado")
    evento, payload_json, wid = row[0], row[1], row[3]
    secret = webhook_dispatcher.obter_secret_webhook(wid) or ""
    try:
        payload = json.loads(payload_json) if payload_json else {}
        if "data" in payload:
            payload = payload["data"]
    except json.JSONDecodeError:
        payload = {}
    res = webhook_dispatcher.testar_disparo(row[1], secret, evento, payload)
    return {"sucesso": True, "detalhes": res}

@app.get("/api/webhooks/eventos", tags=["6. Webhook Studio"], summary="Catalogo de Eventos do Sistema")
def get_webhook_eventos():
    return WebhookDispatcher.EVENT_CATALOG

# ---------------------------------------------------------------------------
# 7. DASHBOARD KPIS & AUDITORIA
# ---------------------------------------------------------------------------
@app.get("/api/dashboard/kpis", tags=["7. Dashboard & Auditoria"], summary="KPIs Gerenciais Hospitalares")
def get_dashboard_kpis():
    return mcp_engine.execute_tool("med_kpi_dashboard_geral", {})

@app.get("/api/logs/auditoria", tags=["7. Dashboard & Auditoria"], summary="Consultar Logs de Auditoria Geral")
def get_logs_auditoria():
    return auditoria_repo.listar(limite=50)

# ---------------------------------------------------------------------------
# 8. PLATAFORMA ENDPOINTS (HTML Studios)
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return HTMLResponse(open(index_file, "rb").read())
    return HTMLResponse("<h1>AIDD Enterprise Suite v5.1</h1>")

@app.get("/webhooks", include_in_schema=False)
async def serve_webhook_studio():
    return HTMLResponse(webhook_dispatcher.get_studio_html("AIDD Enterprise Suite — Webhook Studio"))

@app.get("/mcp", include_in_schema=False)
async def serve_mcp_studio():
    return HTMLResponse(mcp_engine.get_studio_html("AIDD Enterprise Suite — MCP Native Server Studio"))

@app.post("/mcp", include_in_schema=False)
async def handle_mcp(request: Request):
    body = await request.json()
    return JSONResponse(mcp_engine.handle_json_rpc(body))

# ---------------------------------------------------------------------------
# Startup banner
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_banner():
    print("=" * 80)
    print("  [AIDD] Plataforma Core Suite v5.1 — FastAPI Server")
    print("=" * 80)
    print(f"  App Super-App Front-End  : http://localhost:{PORT}")
    print(f"  Swagger UI (/docs)       : http://localhost:{PORT}/docs")
    print(f"  ReDoc (/redoc)           : http://localhost:{PORT}/redoc")
    print(f"  Webhook Studio           : http://localhost:{PORT}/webhooks")
    print(f"  MCP Native Server (/mcp) : http://localhost:{PORT}/mcp")
    print(f"  OpenAPI Spec             : http://localhost:{PORT}/openapi.json")
    print("=" * 80)
    logger.info("server_started", port=PORT, env=os.environ.get("AIDD_ENV", "development"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
