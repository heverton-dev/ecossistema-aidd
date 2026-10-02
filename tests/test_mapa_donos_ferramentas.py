"""
Testes determinísticos para MAPA-DONOS-FERRAMENTAS.json e os 5 schemas de handoff.
Ciclo 01 - Ticket 5 (Fase 5 - Dimensão D1 / D2).
"""
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "componentes" / "compartilhado" / "specs"
MAPA_PATH = SPECS_DIR / "MAPA-DONOS-FERRAMENTAS.json"

FERRAMENTAS_CANONICAS = [
    "aidd-forge",
    "aidd-planner",
    "aidd-pure",
    "aidd-open",
    "aidd-freedom",
    "aidd-master",
    "aidd-enterprise",
    "aidd-ops",
]

CINCO_SCHEMAS_HANDOFF = [
    "handoff-forge-to-planner.schema.json",
    "handoff-planner-to-engine.schema.json",
    "handoff-engine-to-master.schema.json",
    "handoff-master-to-enterprise.schema.json",
    "handoff-enterprise-to-ops.schema.json",
]


def test_mapa_donos_arquivo_e_8_ferramentas():
    """Assert all 8 tools present in MAPA-DONOS-FERRAMENTAS.json."""
    assert MAPA_PATH.exists(), f"Arquivo não encontrado: {MAPA_PATH}"
    
    with open(MAPA_PATH, "r", encoding="utf-8") as f:
        mapa = json.load(f)
        
    for tool in FERRAMENTAS_CANONICAS:
        assert tool in mapa, f"Ferramenta '{tool}' ausente em {MAPA_PATH.name}"
        dados = mapa[tool]
        assert isinstance(dados, dict), f"Entrada da ferramenta '{tool}' deve ser um objeto JSON"
        for key in ["responsabilidades", "dono_do_conteudo_de", "pode_conter", "nunca_conter", "zona_escrita_no_projeto"]:
            assert key in dados, f"Chave obrigatória '{key}' ausente em '{tool}'"
            assert isinstance(dados[key], list), f"Chave '{key}' em '{tool}' deve ser uma lista"


def test_responsabilidades_possuem_dono_unico():
    """Assert every responsibility has exactly one owner."""
    assert MAPA_PATH.exists(), f"Arquivo não encontrado: {MAPA_PATH}"
    
    with open(MAPA_PATH, "r", encoding="utf-8") as f:
        mapa = json.load(f)
        
    todas_responsabilidades = []
    donos_por_resp = {}
    
    for tool in FERRAMENTAS_CANONICAS:
        resps = mapa.get(tool, {}).get("responsabilidades", [])
        assert len(resps) > 0, f"Ferramenta '{tool}' deve ter pelo menos uma responsabilidade declarada"
        for r in resps:
            todas_responsabilidades.append(r)
            if r not in donos_por_resp:
                donos_por_resp[r] = []
            donos_por_resp[r].append(tool)
            
    duplicadas = {r: donos for r, donos in donos_por_resp.items() if len(donos) > 1}
    assert not duplicadas, f"Responsabilidades com mais de um dono detectadas: {duplicadas}"


def test_apenas_forge_pode_guardar_pecas():
    """Assert only aidd-forge has pode_guardar_pecas true."""
    assert MAPA_PATH.exists(), f"Arquivo não encontrado: {MAPA_PATH}"
    
    with open(MAPA_PATH, "r", encoding="utf-8") as f:
        mapa = json.load(f)
        
    assert mapa.get("aidd-forge", {}).get("pode_guardar_pecas") is True, (
        "aidd-forge deve ter pode_guardar_pecas: true"
    )
    
    for tool in FERRAMENTAS_CANONICAS:
        if tool != "aidd-forge":
            pode = mapa.get(tool, {}).get("pode_guardar_pecas", False)
            assert pode is False, f"Ferramenta '{tool}' não pode ter pode_guardar_pecas: true (apenas aidd-forge)"


def test_cinco_handoff_schemas_existem_e_sao_validos():
    """Assert 5 handoff schemas exist in componentes/compartilhado/specs/."""
    for schema_name in CINCO_SCHEMAS_HANDOFF:
        schema_file = SPECS_DIR / schema_name
        assert schema_file.exists(), f"Schema de handoff ausente: {schema_name}"
        with open(schema_file, "r", encoding="utf-8") as f:
            conteudo = json.load(f)
        assert isinstance(conteudo, dict), f"Conteúdo de {schema_name} deve ser objeto JSON"
        assert "$schema" in conteudo, f"$schema ausente em {schema_name}"
        assert "properties" in conteudo, f"properties ausente em {schema_name}"


def test_schemas_contenham_campos_de_evidencia_especificados():
    """Valida campos de evidência nos 5 contratos da ESPEC-CONTRATOS-E-GATE.md."""
    # C1: handoff-forge-to-planner
    c1_path = SPECS_DIR / "handoff-forge-to-planner.schema.json"
    assert c1_path.exists()
    with open(c1_path, "r", encoding="utf-8") as f:
        c1 = json.load(f)
    c1_props = c1.get("properties", {})
    for campo in ["versao_schema", "projeto_dir", "git", "dependencias", "leis_e_guardas", "harnesses", "almoxarifado", "capacidade_llm", "estrutura_projeto"]:
        assert campo in c1_props, f"Campo C1 '{campo}' ausente em handoff-forge-to-planner"

    # C2: handoff-planner-to-engine
    c2_path = SPECS_DIR / "handoff-planner-to-engine.schema.json"
    assert c2_path.exists()
    with open(c2_path, "r", encoding="utf-8") as f:
        c2 = json.load(f)
    c2_props = c2.get("properties", {})
    for campo in ["camadas", "fases", "tickets", "entrada_construtor", "perfil_app"]:
        assert campo in c2_props, f"Campo C2 de evidência '{campo}' ausente em handoff-planner-to-engine"

    # C3: handoff-engine-to-master
    c3_path = SPECS_DIR / "handoff-engine-to-master.schema.json"
    assert c3_path.exists()
    with open(c3_path, "r", encoding="utf-8") as f:
        c3 = json.load(f)
    c3_props = c3.get("properties", {})
    for campo in ["origem_engine", "slices_geradas", "testes_executados", "arquivos_fora_da_zona"]:
        assert campo in c3_props, f"Campo C3 de evidência '{campo}' ausente em handoff-engine-to-master"

    # C4: handoff-master-to-enterprise
    c4_path = SPECS_DIR / "handoff-master-to-enterprise.schema.json"
    assert c4_path.exists()
    with open(c4_path, "r", encoding="utf-8") as f:
        c4 = json.load(f)
    c4_props = c4.get("properties", {})
    for campo in ["quarteto", "servidor_sobe", "componentes_para_blindagem"]:
        assert campo in c4_props, f"Campo C4 de evidência '{campo}' ausente em handoff-master-to-enterprise"

    # C5: handoff-enterprise-to-ops
    c5_path = SPECS_DIR / "handoff-enterprise-to-ops.schema.json"
    assert c5_path.exists()
    with open(c5_path, "r", encoding="utf-8") as f:
        c5 = json.load(f)
    c5_props = c5.get("properties", {})
    for campo in ["registry", "selo_sha256", "drift", "perfil_app"]:
        assert campo in c5_props, f"Campo C5 de evidência '{campo}' ausente em handoff-enterprise-to-ops"
