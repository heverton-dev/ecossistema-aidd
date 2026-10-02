# -*- coding: utf-8 -*-
"""Ticket 11 (D2) — Planta baixa com tickets roteados para as 6 ferramentas.

O aidd-planner deixa de gerar "1 modulo generico so para o construtor": ele le o
contrato C1 do aidd-forge (`.aidd/HANDOFF_FORGE_PLANNER.json`), desenha camadas,
fases e tickets, e grava cada ticket endereçado ao dono real
(constru+master+enterprise+ops). O `perfil_app` do C2 e' calculado da propria
planta (modulos, persistencia, filas, integracoes e rotas do Quarteto) — nada vem
de lista fixa de nichos (o ops reprovava com `NICHO_NAO_RECONHECIDO`).

Regras do contrato (docs/auditoria/fronteiras-ferramentas/ciclo-01/ESPEC-CONTRATOS-E-GATE.md):
  - cada ticket tem `ferramenta_destino`, `entrada`, `saida_esperada`,
    `pecas_do_almoxarifado` e `criterio_de_aceite`;
  - toda `ferramenta_destino` existe no mapa de donos e toda peca citada existe
    no almoxarifado provado pelo C1 (evidencia, nao promessa);
  - `entrada_construtor` do fluxo 02 carrega o plano de motores da factory.
"""

import hashlib
import json
import os
import sys

import pytest

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ECOSSISTEMA_DIR = os.path.dirname(os.path.dirname(_PLANNER_DIR))

for _pasta in (_PLANNER_DIR,):
    if _pasta not in sys.path:
        sys.path.insert(0, _pasta)

from src.cli import main as cli_main  # noqa: E402

try:  # o motor da planta e' o que este ticket entrega (TDD Red: ainda nao existe)
    from src.core import planta as _modulo_planta
    _ERRO_IMPORT = ""
except ImportError as _erro:  # pragma: no cover - caminho do Red
    _modulo_planta = None
    _ERRO_IMPORT = str(_erro)


def _planta():
    """Import tardio: no Red cada teste FALHA (exit 1) em vez de quebrar a colecao."""
    assert _modulo_planta is not None, f"src.core.planta ausente: {_ERRO_IMPORT}"
    return _modulo_planta

SCHEMA_C1 = os.path.join(
    _ECOSSISTEMA_DIR, "componentes", "compartilhado", "specs",
    "handoff-forge-to-planner.schema.json",
)
SCHEMA_C2 = os.path.join(
    _ECOSSISTEMA_DIR, "componentes", "compartilhado", "specs",
    "handoff-planner-to-engine.schema.json",
)
MAPA_DONOS = os.path.join(
    _ECOSSISTEMA_DIR, "componentes", "compartilhado", "specs",
    "MAPA-DONOS-FERRAMENTAS.json",
)

CAMPOS_DO_TICKET = (
    "id",
    "ferramenta_destino",
    "entrada",
    "saida_esperada",
    "pecas_do_almoxarifado",
    "criterio_de_aceite",
)


# ---------------------------------------------------------------------------
# Fixtures / helpers deterministicos
# ---------------------------------------------------------------------------

def _sha256_de_arquivo(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _catalogo():
    with open(
        os.path.join(_ECOSSISTEMA_DIR, "componentes", "compartilhado", "CATALOGO.json"),
        encoding="utf-8",
    ) as f:
        return json.load(f)


def _handoff_c1_valido(pastas_criadas=None):
    """C1 conforme `handoff-forge-to-planner.schema.json`, com evidencia real."""
    catalogo = _catalogo()
    pecas = [p["nome"] for p in catalogo["pecas"]]
    handoff = {
        "versao_schema": "1.0.0",
        "projeto_dir": "/tmp/projeto-aidd",
        "git": {"inicializado": True, "commit_inicial": "a1b2c3d4e5f6"},
        "dependencias": [{"pacote": "click", "versao": "8.1.7"}],
        "leis_e_guardas": [{"gate": "gates/G_TESTES.py", "sha256": "a" * 64}],
        "harnesses": [".claude/skills"],
        "almoxarifado": {"catalogo_sha256": "b" * 64, "pecas_disponiveis": pecas},
        "capacidade_llm": "delegado_com_resposta",
        "estrutura_projeto": {
            "pastas_criadas": list(
                pastas_criadas
                if pastas_criadas is not None
                else ("gates", "skills", "pipeline_phases", "governance", ".aidd")
            )
        },
    }
    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_C1, encoding="utf-8") as f:
        jsonschema.validate(instance=handoff, schema=json.load(f))
    return handoff


def _gravar_c1(pasta, pastas_criadas=None):
    """Grava o C1 real em `<pasta>/.aidd/HANDOFF_FORGE_PLANNER.json` e devolve o dict."""
    handoff = _handoff_c1_valido(pastas_criadas=pastas_criadas)
    destino = os.path.join(pasta, ".aidd")
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(destino, "HANDOFF_FORGE_PLANNER.json"), "w", encoding="utf-8") as f:
        json.dump(handoff, f, indent=2, ensure_ascii=False)
    return handoff


def _init(tmp_path, fluxo=1, nome="Loja AIDD", slug="loja-aidd",
          dominio="comercio", dominios_extra=(), c1=True, pastas_criadas=None,
          escrever_c1=True, force=True):
    """Roda `planner init` de verdade e devolve (rc, pasta, PLANNER.json, C2.json)."""
    pasta = str(tmp_path)
    handoff_c1 = _gravar_c1(pasta, pastas_criadas=pastas_criadas) if c1 else None
    if not c1 and os.path.isdir(os.path.join(pasta, ".aidd")):
        os.remove(os.path.join(pasta, ".aidd", "HANDOFF_FORGE_PLANNER.json"))

    argv = [
        "init",
        "--fluxo", str(fluxo),
        "--nome", nome,
        "--slug", slug,
        "--descricao", "Planta baixa roteada para as seis ferramentas do ecossistema",
        "--dominio", dominio,
        "--pasta", pasta,
        "--dominio-modulo", "nucleo",
    ]
    if force:
        argv.append("--force")
    for modulo in dominios_extra:
        argv.extend(["--dominio-modulo", modulo])
    if not escrever_c1 and handoff_c1 is not None:
        os.remove(os.path.join(pasta, ".aidd", "HANDOFF_FORGE_PLANNER.json"))

    rc = cli_main(argv)
    with open(os.path.join(pasta, "PLANNER.json"), encoding="utf-8") as f:
        plano = json.load(f)
    with open(os.path.join(pasta, "HANDOFF_PLANNER_ENGINE.json"), encoding="utf-8") as f:
        handoff_c2 = json.load(f)
    return rc, pasta, plano, handoff_c2


def _plano_com_modulo(plano, modulo):
    """Devolve o plano com um bounded context novo (`modulo`) no lugar do 'nucleo'."""
    import copy

    alterado = copy.deepcopy(plano)
    alterado["ddd_bounded_contexts"][0]["modulo"] = modulo
    return alterado


# ---------------------------------------------------------------------------
# TDD Red: a planta roteada nao existe no planner atual
# ---------------------------------------------------------------------------

def test_planner_gera_ticket_para_construtor_master_enterprise_e_ops(tmp_path):
    rc, _pasta, _plano, c2 = _init(tmp_path, fluxo=1)
    assert rc == 0

    destinos = [t["ferramenta_destino"] for t in c2["tickets"]]
    assert _planta().MAPPED_CONSTRUTOR_POR_FLUXO[1] in destinos, "sem ticket do construtor do fluxo 01"
    for dono in ("aidd-master", "aidd-enterprise", "aidd-ops"):
        assert dono in destinos, f"sem ticket roteado para {dono}"


def test_tickets_do_fluxo_02_vao_para_o_construtor_do_fluxo_02(tmp_path):
    rc, _pasta, _plano, c2 = _init(tmp_path, fluxo=2, nome="Hub Mensagens", slug="hub-mensagens")
    assert rc == 0
    destinos = {t["ferramenta_destino"] for t in c2["tickets"]}
    assert "aidd-open" in destinos
    assert "aidd-pure" not in destinos


def test_tickets_do_fluxo_03_vao_para_o_construtor_do_fluxo_03(tmp_path):
    rc, _pasta, _plano, c2 = _init(tmp_path, fluxo=3, nome="App Low Code", slug="app-low-code")
    assert rc == 0
    destinos = {t["ferramenta_destino"] for t in c2["tickets"]}
    assert "aidd-freedom" in destinos


def test_cada_ticket_tem_os_cinco_campos_do_contrato(tmp_path):
    rc, _pasta, _plano, c2 = _init(tmp_path)
    assert rc == 0
    assert c2["tickets"], "a planta precisa de tickets roteados"

    for ticket in c2["tickets"]:
        for campo in CAMPOS_DO_TICKET:
            assert campo in ticket, f"ticket {ticket.get('id')} sem '{campo}'"
        assert ticket["id"].strip()
        assert isinstance(ticket["entrada"], dict) and ticket["entrada"], \
            f"ticket {ticket['id']} sem entrada de trabalho"
        assert ticket["saida_esperada"].strip()
        assert isinstance(ticket["pecas_do_almoxarifado"], list)
        assert ticket["criterio_de_aceite"].strip()


def test_ferramenta_destino_existe_no_mapa_de_donos(tmp_path):
    _rc, _pasta, _plano, c2 = _init(tmp_path)
    with open(MAPA_DONOS, encoding="utf-8") as f:
        mapa = json.load(f)
    destinos = {t["ferramenta_destino"] for t in c2["tickets"]}
    assert destinos, "nenhum destino roteado"
    assert destinos <= set(_planta().FERRAMENTAS_DA_PLANTA)
    for destino in destinos:
        assert destino in mapa, f"{destino} nao esta no MAPA-DONOS-FERRAMENTAS.json"


def test_pecas_citadas_existem_no_almoxarifado_do_c1(tmp_path):
    """Evidencia, nao promessa: toda peca citada veio do C1 (Lei/Regra 3 da ESPEC)."""
    _rc, _pasta, _plano, c2 = _init(tmp_path)
    c1 = _handoff_c1_valido()
    disponiveis = set(c1["almoxarifado"]["pecas_disponiveis"])

    citadas = []
    for ticket in c2["tickets"]:
        citadas.extend(ticket["pecas_do_almoxarifado"])
    assert citadas, "nenhuma peca do almoxarifado foi citada (prova de consumo sob demanda)"
    for peca in citadas:
        assert peca in disponiveis, f"peca '{peca}' nao existe no almoxarifado provado pelo C1"


def test_camadas_e_fases_seguem_a_estrutura_projeto_do_c1(tmp_path):
    _rc, _pasta, plano, c2 = _init(tmp_path, dominios_extra=("pedidos",))
    c1 = _handoff_c1_valido()

    assert c2["camadas"] == _planta().derivar_camadas(c1, ["nucleo", "pedidos"])
    assert c2["camadas"], "camadas vazias"
    for camada in c2["camadas"]:
        assert isinstance(camada, str) and camada.strip()

    assert c2["fases"] == _planta().derivar_fases(c2["tickets"])
    assert len(c2["fases"]) == len({t["ferramenta_destino"] for t in c2["tickets"]})


def test_camada_de_governanca_surge_do_c1_e_nasce_do_terreno(tmp_path):
    """A camada `governanca` so aparece quando o C1 prova que a pasta existe."""
    _rc, _pasta, _plano, com_governanca = _init(
        tmp_path, pastas_criadas=("gates", "skills", "governance", ".aidd")
    )
    assert "governanca" in com_governanca["camadas"]

    _rc2, _pasta2, _plano2, sem_governanca = _init(
        tmp_path, slug="outro-projeto", nome="Outro Projeto",
        pastas_criadas=("gates", "skills", ".aidd"),
    )
    assert "governanca" not in sem_governanca["camadas"]


# ---------------------------------------------------------------------------
# perfil_app: derivado da propria planta, nunca de lista fixa
# ---------------------------------------------------------------------------

def test_perfil_app_derivado_de_modulos_banco_filas_integracoes_e_rotas(tmp_path):
    rc, _pasta, plano, c2 = _init(tmp_path, fluxo=1, dominios_extra=("pedidos",))
    assert rc == 0
    perfil = c2["perfil_app"]

    modulos = [c["slug"] for c in c2["modulos_funcionais"]]
    assert perfil["modulos"] == modulos
    assert set(perfil["modulos"]) == {"nucleo", "pedidos"}

    # persistencia vem do desenho (infraestrutura_alvo), nao de um enum fixo
    assert perfil["banco"] == c2["arquitetura_alvo"]["persistencia"]
    assert perfil["banco"] in ("sqlite_wal", "postgresql")

    # filas e integracoes vem do que a planta desenhou, nao de nicho
    c1 = _handoff_c1_valido()
    modulos_funcionais = _planta().derivar_modulos_funcionais(plano)
    assert perfil["filas"] == _planta().calcular_perfil_app(plano, modulos_funcionais)["filas"]
    assert perfil["integracoes_externas"] == _planta().calcular_perfil_app(plano, modulos_funcionais)["integracoes_externas"]

    # rotas do Quarteto desenhadas no plano (Lei #10)
    assert "/api" in perfil["rotas_quarteto"]
    assert "/docs" in perfil["rotas_quarteto"]
    assert "/mcp" in perfil["rotas_quarteto"]
    assert any(r.startswith("/webhook") for r in perfil["rotas_quarteto"])

    # portas desenhadas no plano
    assert perfil["portas"] == sorted(
        {int(plano["infraestrutura_alvo"]["porta_api"])}
    )


def test_perfil_app_inclui_fila_e_integracao_declaradas_no_modulo(tmp_path):
    _rc, pasta, plano, c2 = _init(tmp_path, fluxo=1)
    modulos = _planta().derivar_modulos_funcionais(plano)
    modulos[0]["filas"] = ["pedidos-processamento"]
    modulos[0]["integracoes_externas"] = ["gateway-pagamentos"]

    perfil = _planta().calcular_perfil_app(plano, modulos)
    assert perfil["filas"] == ["pedidos-processamento"]
    assert "gateway-pagamentos" in perfil["integracoes_externas"]
    assert os.path.isdir(pasta)


def test_mudar_um_modulo_planejado_muda_o_perfil_app(tmp_path):
    rc, _pasta, plano, c2 = _init(tmp_path)
    assert rc == 0
    perfil_antes = c2["perfil_app"]

    alterado = _plano_com_modulo(plano, "financeiro")
    modulos = _planta().derivar_modulos_funcionais(alterado)
    perfil_depois = _planta().calcular_perfil_app(alterado, modulos)

    assert perfil_depois != perfil_antes, "mudar a planta tem que mudar o perfil"
    assert perfil_antes["modulos"] == ["nucleo"]
    assert perfil_depois["modulos"] == ["financeiro"]
    assert perfil_antes["entidades"] != perfil_depois["entidades"]


def test_adicionar_modulo_planejado_muda_o_perfil_app(tmp_path):
    _rc, _pasta, plano, c2 = _init(tmp_path)
    perfil_antes = c2["perfil_app"]

    # nova planta: Nucleo + Pedidos (via derivacao real das camadas da planta)
    plano2 = json.loads(json.dumps(plano))
    ctx = json.loads(json.dumps(plano["ddd_bounded_contexts"][0]))
    ctx["modulo"] = "pedidos"
    ctx["entidades"][0]["nome"] = "Pedido"
    plano2["ddd_bounded_contexts"].append(ctx)

    modulos = _planta().derivar_modulos_funcionais(plano2)
    perfil_depois = _planta().calcular_perfil_app(plano2, modulos)
    assert len(perfil_depois["modulos"]) == len(perfil_antes["modulos"]) + 1
    assert "pedidos" in perfil_depois["modulos"]
    assert perfil_depois != perfil_antes


# ---------------------------------------------------------------------------
# entrada_construtor: a factory do fluxo 02 recebe o plano de motores
# ---------------------------------------------------------------------------

def test_fluxo_02_entrega_o_plano_de_motores_da_factory(tmp_path):
    rc, _pasta, _plano, c2 = _init(tmp_path, fluxo=2, nome="Hub Mensagens", slug="hub-mensagens")
    assert rc == 0

    entrada = c2["entrada_construtor"]
    assert "plano_motores" in entrada, "fluxo 02 sem entrada da factory"
    plano_motores = entrada["plano_motores"]
    for fase in ("fase_1_intake", "fase_2_curadoria", "fase_3_sizing"):
        assert fase in plano_motores, f"plano de motores sem {fase}"
        assert not plano_motores[fase].get("erro"), f"{fase} com erro: {plano_motores[fase].get('erro')}"


def test_fluxo_02_passa_o_preflight_da_factory(tmp_path):
    """Verificacao Green do ticket: o fluxo 02 passa do pre-flight da factory.

    O pre-flight da factory e' a validacao do PLANO-INFRAESTRUTURA contra
    `plano-infraestrutura.schema.json` (aidd-ops = produtor do envelope). Se a
    entrada do fluxo 02 nao valida ali, o aidd-open reprova antes de comecar.
    """
    _rc, _pasta, _plano, c2 = _init(tmp_path, fluxo=2, nome="Hub Mensagens", slug="hub-mensagens")
    plano_motores = c2["entrada_construtor"]["plano_motores"]

    with open(
        os.path.join(_ECOSSISTEMA_DIR, "componentes", "compartilhado", "specs",
                     "plano-infraestrutura.schema.json"),
        encoding="utf-8",
    ) as f:
        schema = json.load(f)

    import jsonschema

    try:
        jsonschema.validate(instance=plano_motores, schema=schema)
    except jsonschema.ValidationError as erro:
        pytest.fail(f"entrada do fluxo 02 reprova no pre-flight da factory: {erro.message}")


def test_fluxo_01_entrega_ideia_e_capacidade_llm(tmp_path):
    _rc, _pasta, plano, c2 = _init(tmp_path, fluxo=1)
    entrada = c2["entrada_construtor"]
    assert entrada["ideia"].strip()
    assert entrada["capacidade_llm"] == "nenhuma" or entrada["capacidade_llm"] in (
        "delegado_com_resposta", "headless_com_chave", "nenhuma",
    )
    assert entrada["origem_export"]["hash"] == _sha256_de_arquivo(
        os.path.join(str(tmp_path), "PLANNER.json")
    ) or len(entrada["origem_export"]["hash"]) == 64


def test_fluxo_03_entrega_origem_export_com_caminho_e_hash(tmp_path):
    export = tmp_path / "export-lowcode"
    export.mkdir()
    (export / "index.html").write_text("<html></html>", encoding="utf-8")
    _rc, _pasta, _plano, c2 = _init(tmp_path, fluxo=3, nome="App Low Code", slug="app-low-code")
    entrada = c2["entrada_construtor"]
    assert "origem_export" in entrada
    assert entrada["origem_export"]["caminho"].strip()
    assert len(entrada["origem_export"]["hash"]) == 64


# ---------------------------------------------------------------------------
# Contrato C2 e leitura do C1
# ---------------------------------------------------------------------------

def test_handoff_c2_valida_contra_a_fonte_unica_de_schema(tmp_path):
    for fluxo in (1, 2, 3):
        sub = tmp_path / f"fluxo{fluxo}"
        sub.mkdir()
        rc, _pasta, _plano, c2 = _init(sub, fluxo=fluxo)
        assert rc == 0
        jsonschema = pytest.importorskip("jsonschema")
        with open(SCHEMA_C2, encoding="utf-8") as f:
            jsonschema.validate(instance=c2, schema=json.load(f))


def test_a_planta_tambem_vai_gravada_no_planner_json(tmp_path):
    rc, _pasta, plano, c2 = _init(tmp_path)
    assert rc == 0
    assert plano["planta"]["tickets"] == c2["tickets"]
    assert plano["planta"]["camadas"] == c2["camadas"]
    assert plano["planta"]["fases"] == c2["fases"]
    assert plano["planta"]["perfil_app"] == c2["perfil_app"]


def test_planner_le_o_c1_gravado_pelo_forge(tmp_path):
    pasta = str(tmp_path)
    handoff = _gravar_c1(pasta)
    lido = _planta().carregar_handoff_c1(pasta)
    assert lido["git"]["commit_inicial"] == handoff["git"]["commit_inicial"]
    assert lido["almoxarifado"]["pecas_disponiveis"] == handoff["almoxarifado"]["pecas_disponiveis"]
    assert lido["capacidade_llm"] == handoff["capacidade_llm"]


def test_sem_c1_o_planner_ainda_gera_a_planta_sem_citar_peca(tmp_path):
    """Degradacao honesta: sem o C1 nao ha evidencia de almoxarifado, entao
    nenhum ticket cita peca — e o handoff continua valendo contra o schema."""
    rc, _pasta, plano, c2 = _init(tmp_path, slug="sem-c1", nome="Sem C1", escrever_c1=False)
    assert rc == 0
    for ticket in c2["tickets"]:
        assert ticket["pecas_do_almoxarifado"] == []
    assert c2.get("avisos"), "degradação tem de ser declarada, não silenciosa"
    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_C2, encoding="utf-8") as f:
        jsonschema.validate(instance=c2, schema=json.load(f))


def test_rotear_tickets_e_deterministico(tmp_path):
    _rc, _pasta, plano, _c2 = _init(tmp_path, fluxo=1)
    c1 = _handoff_c1_valido()
    modulos = _planta().derivar_modulos_funcionais(plano)
    primeiro = _planta().rotear_tickets(plano, modulos, c1, fluxo_num=1)
    segundo = _planta().rotear_tickets(plano, modulos, c1, fluxo_num=1)
    assert primeiro == segundo


def test_montar_planta_carrega_tudo_do_c2(tmp_path):
    _rc, _pasta, plano, c2 = _init(tmp_path)
    planta = _planta().montar_planta(plano, _handoff_c1_valido(), fluxo_num=1)
    for chave in (
        "versao_schema", "fluxo_alvo", "metadados_projeto", "quarteto_sine_qua_non",
        "arquitetura_alvo", "modulos_funcionais", "camadas", "fases", "tickets",
        "entrada_construtor", "perfil_app",
    ):
        assert chave in planta, f"planta sem '{chave}'"
        assert planta[chave] == c2[chave], f"divergencia em '{chave}'"


def test_montar_handoff_engine_rejeita_handoff_c1_invalido(tmp_path):
    plano = _plano_minimo()
    with pytest.raises(Exception):
        _planta().carregar_handoff_c1(str(tmp_path))
    assert _planta().montar_handoff_engine(plano, fluxo_num=1)["tickets"]


def _plano_minimo():
    from src.core.planner_engine import gerar_template_plano

    return gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="App Direto",
        slug="app-direto",
        descricao="Planta minima para o contrato do planner",
        dominio="generico",
    )
