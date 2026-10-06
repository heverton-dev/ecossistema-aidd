# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — Suite de Testes
=============================================================================
Testes reais com subprocess do CLI pipeline_ops.py cobrindo:
  - 5 nichos reais rodando pipeline completa ponta a ponta
  - 1 caso de texto ambíguo
  - 1 caso de texto não reconhecido
  - Gate G_OPS_MVP isolado (2 modos)
"""

import json
import os
import subprocess
import sys

import pytest

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_SCRIPT = os.path.join(TOOL_ROOT, "scripts", "pipeline_ops.py")
GATE_SCRIPT = os.path.join(TOOL_ROOT, "gates", "G_OPS_MVP.py")


def _run_pipeline(texto: str, pasta: str, nicho: str = None) -> subprocess.CompletedProcess:
    """Executa pipeline_ops.py via subprocess real."""
    cmd = [sys.executable, PIPELINE_SCRIPT]
    if nicho:
        cmd.extend(["--nicho", nicho])
    else:
        cmd.append(texto)
    cmd.extend(["--pasta", pasta])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=TOOL_ROOT,
    )


def _carregar_plano(pasta: str) -> dict:
    caminho = os.path.join(pasta, "PLANO-INFRAESTRUTURA.json")
    assert os.path.isfile(caminho), f"PLANO-INFRAESTRUTURA.json nao encontrado em {pasta}"
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Testes dos 5 nichos reais ──

NICHOS_REAIS = [
    ("clinicas", "Clinica odontologica com agendamento de pacientes e WhatsApp"),
    ("delivery", "Lanchonete de delivery com cardapio e pedidos pelo WhatsApp"),
    ("farmacias", "Farmacia de manipulacao com receitas medicas e reposicao de remedios"),
    ("b2b_industrial", "Industria B2B com orcamentos tecnicos, contratos e assinatura digital"),
    ("energia_solar", "Empresa de energia solar com simulador fotovoltaico e visitas tecnicas"),
]


@pytest.mark.parametrize("slug,texto", NICHOS_REAIS, ids=[n[0] for n in NICHOS_REAIS])
def test_nicho_completo(slug, texto, tmp_path):
    """Cada nicho real deve gerar exit 0 e PLANO-INFRAESTRUTURA.json válido."""
    pasta = str(tmp_path / f"saida_{slug}")
    os.makedirs(pasta, exist_ok=True)

    resultado = _run_pipeline(texto, pasta)

    # Exit code deve ser 0
    assert resultado.returncode == 0, (
        f"Nicho '{slug}' retornou exit {resultado.returncode}.\n"
        f"STDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"
    )

    # Deve ter impresso sucesso
    assert "Fase" in resultado.stdout or "OK" in resultado.stdout

    # PLANO-INFRAESTRUTURA.json deve existir e ser válido
    plano = _carregar_plano(pasta)
    assert plano["versao"] == "1.0.0"
    assert "fase_1_intake" in plano
    assert "fase_2_curadoria" in plano
    assert "fase_3_sizing" in plano

    # Fase 1: nicho correto
    f1 = plano["fase_1_intake"]["saida"]
    assert f1["nicho_slug"] == slug
    assert f1["nicho_nome_exibicao"]

    # Fase 2: tem ferramentas
    f2 = plano["fase_2_curadoria"]["saida"]
    assert len(f2["ferramentas"]) > 0

    # Fase 3: tem vps e bancos_logicos
    f3 = plano["fase_3_sizing"]["saida"]
    assert f3["vps"]["vcpu"] >= 2
    assert f3["vps"]["ram_gb"] >= 4
    assert f3["vps"]["disco_gb"] >= 40
    assert isinstance(f3["bancos_logicos"], list)
    assert isinstance(f3["fontes_consultadas"], list)
    assert len(f3["fontes_consultadas"]) > 0


# ── Testes do tipo de origem "monólito customizado" (Fluxo 01, aidd-master) ──

def _criar_monolito_fake(base_dir: str, nome_projeto: str, slugs_modulos: list) -> str:
    """Cria um diretório com os 3 artefatos reais que `aidd-master init`
    sempre gera (estrutura mínima, mas real o suficiente para exercitar o
    caminho de detecção de arquivo por arquivo, sem depender de rodar o
    aidd-master de verdade dentro deste teste)."""
    projeto_dir = os.path.join(base_dir, f"proj_{nome_projeto}")
    os.makedirs(projeto_dir, exist_ok=True)
    with open(os.path.join(projeto_dir, "PLANO-EXECUCAO-ESTRUTURADO.json"), "w", encoding="utf-8") as f:
        json.dump({
            "projeto": {"nome": nome_projeto},
            "fases": [],
            "modulos": [{"nome": s.title(), "slug": s} for s in slugs_modulos],
        }, f)
    with open(os.path.join(projeto_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
        f.write("services:\n  app:\n    build: .\n")
    with open(os.path.join(projeto_dir, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write("FROM python:3.12-slim\n")
    return projeto_dir


def _run_pipeline_dir_projeto(dir_projeto: str, pasta: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, PIPELINE_SCRIPT, "plan", "--dir-projeto", dir_projeto, "--pasta", pasta]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=TOOL_ROOT)


def test_monolito_customizado_ponta_a_ponta(tmp_path):
    """Achado real corrigido: aidd-ops só cobria o Fluxo 02 (OSS por nicho) —
    um monólito do aidd-master (Fluxo 01) sempre batia NICHO_NAO_RECONHECIDO.
    Reprodução real via CLI: `ops plan --dir-projeto <monólito>` deve
    reconhecer a origem, dimensionar pela contagem de módulos (não por
    catálogo OSS) e gravar um PLANO-INFRAESTRUTURA.json 100% válido contra
    o mesmo schema canônico — sem nenhuma mudança de schema."""
    dir_projeto = _criar_monolito_fake(str(tmp_path), "app-teste", ["tarefas", "usuarios"])
    pasta = str(tmp_path / "saida_monolito")
    os.makedirs(pasta, exist_ok=True)

    resultado = _run_pipeline_dir_projeto(dir_projeto, pasta)
    assert resultado.returncode == 0, (
        f"Exit {resultado.returncode}.\nSTDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"
    )

    plano = _carregar_plano(pasta)
    f1 = plano["fase_1_intake"]["saida"]
    assert f1["nicho_slug"] == "monolito_customizado"
    assert "app-teste" in f1["nicho_nome_exibicao"]

    f2 = plano["fase_2_curadoria"]["saida"]
    nomes = sorted(f["nome"] for f in f2["ferramentas"])
    assert nomes == ["tarefas", "usuarios"]

    f3 = plano["fase_3_sizing"]["saida"]
    # 2 módulos: baseline 1.0 vcpu + 0.25*2=0.5 = 1.5*1.2=1.8 -> ceil 2 (mínimo já cobre)
    assert f3["vps"]["vcpu"] >= 2
    assert f3["bancos_logicos"] == []
    assert sorted(f3["ferramentas_sem_banco"]) == ["tarefas", "usuarios"]


def test_monolito_dimensiona_mais_para_mais_modulos(tmp_path):
    """A heurística de sizing por módulo precisa realmente escalar com a
    complexidade do monólito — mais módulos, mais vCPU/RAM — provando que
    não caiu de volta no mínimo fixo independente da entrada."""
    dir_pequeno = _criar_monolito_fake(str(tmp_path), "pequeno", ["principal"])
    dir_grande = _criar_monolito_fake(
        str(tmp_path), "grande",
        [f"modulo{i}" for i in range(20)],
    )
    pasta_pequeno = str(tmp_path / "saida_pequeno")
    pasta_grande = str(tmp_path / "saida_grande")
    os.makedirs(pasta_pequeno, exist_ok=True)
    os.makedirs(pasta_grande, exist_ok=True)

    r_pequeno = _run_pipeline_dir_projeto(dir_pequeno, pasta_pequeno)
    r_grande = _run_pipeline_dir_projeto(dir_grande, pasta_grande)
    assert r_pequeno.returncode == 0
    assert r_grande.returncode == 0

    vps_pequeno = _carregar_plano(pasta_pequeno)["fase_3_sizing"]["saida"]["vps"]
    vps_grande = _carregar_plano(pasta_grande)["fase_3_sizing"]["saida"]["vps"]
    assert vps_grande["vcpu"] > vps_pequeno["vcpu"]
    assert vps_grande["ram_gb"] > vps_pequeno["ram_gb"]


def test_monolito_invalido_sem_docker_compose(tmp_path):
    """Pasta sem os artefatos reais de `aidd-master init` deve reprovar
    explicitamente (MONOLITO_INVALIDO), nunca cair silenciosamente em
    NICHO_NAO_RECONHECIDO (que sugeriria, erradamente, tentar nichos OSS)."""
    dir_projeto = str(tmp_path / "pasta_qualquer")
    os.makedirs(dir_projeto, exist_ok=True)
    pasta = str(tmp_path / "saida_invalido")
    os.makedirs(pasta, exist_ok=True)

    resultado = _run_pipeline_dir_projeto(dir_projeto, pasta)
    assert resultado.returncode == 1
    assert "MONOLITO_INVALIDO" in resultado.stdout


# ── Teste via --nicho (bypass) ──

def test_nicho_explicito(tmp_path):
    """--nicho clinicas deve funcionar igual a texto com 'clinica'."""
    pasta = str(tmp_path / "saida_explicito")
    os.makedirs(pasta, exist_ok=True)

    resultado = _run_pipeline("", pasta, nicho="clinicas")
    assert resultado.returncode == 0, (
        f"Exit {resultado.returncode}.\nSTDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"
    )

    plano = _carregar_plano(pasta)
    assert plano["fase_1_intake"]["saida"]["nicho_slug"] == "clinicas"


# ── Texto ambíguo ──

def test_texto_ambiguo(tmp_path):
    """Texto que casa com mais de 1 nicho → NICHO_AMBIGUO, exit 1, nenhum arquivo."""
    pasta = str(tmp_path / "saida_ambiguo")
    os.makedirs(pasta, exist_ok=True)

    # 'clinica de delivery de farmacia' casa com clinicas, delivery E farmacias
    texto = "clinica de delivery de farmacia"
    resultado = _run_pipeline(texto, pasta)

    assert resultado.returncode == 1, (
        f"Texto ambíguo deveria retornar exit 1, retornou {resultado.returncode}.\n"
        f"STDOUT: {resultado.stdout}"
    )

    assert "NICHO_AMBIGUO" in resultado.stdout or "NICHO_AMBIGUO" in resultado.stderr

    # Nenhum PLANO-INFRAESTRUTURA.json deve ser escrito (ou se escrito, deve ter erro na fase 1)
    caminho_plano = os.path.join(pasta, "PLANO-INFRAESTRUTURA.json")
    if os.path.isfile(caminho_plano):
        plano = _carregar_plano(pasta)
        f1 = plano.get("fase_1_intake", {})
        assert f1.get("erro") is not None, "Fase 1 deveria ter erro registrado"


# ── Texto não reconhecido ──

def test_texto_nao_reconhecido(tmp_path):
    """Texto que não casa com nenhum nicho → NICHO_NAO_RECONHECIDO, exit 1."""
    pasta = str(tmp_path / "saida_nao_reconhecido")
    os.makedirs(pasta, exist_ok=True)

    texto = "quero vender courses online no mercado americano"
    resultado = _run_pipeline(texto, pasta)

    assert resultado.returncode == 1, (
        f"Texto não reconhecido deveria retornar exit 1, retornou {resultado.returncode}.\n"
        f"STDOUT: {resultado.stdout}"
    )

    assert "NICHO_NAO_RECONHECIDO" in resultado.stdout or "NICHO_NAO_RECONHECIDO" in resultado.stderr


# ── Gate G_OPS_MVP: modo sem --dir ──

def test_gate_estrutura():
    """G_OPS_MVP sem --dir deve validar a própria estrutura e retornar exit 0."""
    resultado = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=TOOL_ROOT,
    )

    assert resultado.returncode == 0, (
        f"Gate estrutura retornou exit {resultado.returncode}.\n"
        f"STDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"
    )

    assert "APROVADO" in resultado.stdout or "PASS" in resultado.stdout


# ── Gate G_OPS_MVP: modo com --dir de saída válida ──

def test_gate_saida_valida(tmp_path):
    """G_OPS_MVP com --dir de saída válida deve retornar exit 0."""
    # Primeiro gerar uma saída válida
    pasta = str(tmp_path / "saida_gate")
    os.makedirs(pasta, exist_ok=True)
    resultado_pipeline = _run_pipeline("Clinica odontologica", pasta)
    assert resultado_pipeline.returncode == 0

    # Agora rodar o gate
    resultado_gate = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--dir", pasta],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=TOOL_ROOT,
    )

    assert resultado_gate.returncode == 0, (
        f"Gate saida válida retornou exit {resultado_gate.returncode}.\n"
        f"STDOUT: {resultado_gate.stdout}\nSTDERR: {resultado_gate.stderr}"
    )


# ── Gate G_OPS_MVP: modo com --dir corrompido ──

def test_gate_saida_corrompida(tmp_path):
    """G_OPS_MVP com --dir com PLANO corrompido (campo obrigatório removido) deve retornar exit 1."""
    pasta = str(tmp_path / "saida_corrompida")
    os.makedirs(pasta, exist_ok=True)

    # Criar PLANO-INFRAESTRUTURA.json com campo obrigatório removido
    plano_corrompido = {
        "versao": "1.0.0",
        "gerado_em": "2026-01-01T00:00:00Z",
        "pipeline": "aidd-ops-mvp-fases-1-3",
        "fase_1_intake": {
            "entrada": {"texto": "test"},
            "saida": None,  # Saida ausente = corrompido
            "erro": {"sucesso": False, "codigo": "TESTE", "erro": "corrompido"},
        },
        "fase_2_curadoria": {
            "entrada": {"nicho_slug": "test"},
            "saida": None,
            "erro": {"sucesso": False, "codigo": "TESTE", "erro": "corrompido"},
        },
        "fase_3_sizing": {
            "entrada": {"ferramentas": []},
            "saida": None,
            "erro": {"sucesso": False, "codigo": "TESTE", "erro": "corrompido"},
        },
    }

    caminho_plano = os.path.join(pasta, "PLANO-INFRAESTRUTURA.json")
    with open(caminho_plano, "w", encoding="utf-8") as f:
        json.dump(plano_corrompido, f, indent=2)

    resultado_gate = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--dir", pasta],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=TOOL_ROOT,
    )

    assert resultado_gate.returncode == 1, (
        f"Gate corrompido deveria retornar exit 1, retornou {resultado_gate.returncode}.\n"
        f"STDOUT: {resultado_gate.stdout}"
    )


# ── Gate G_OPS_MVP: --dir inexistente ──

def test_gate_dir_inexistente(tmp_path):
    """G_OPS_MVP com --dir inexistente deve retornar exit 1."""
    pasta_inexistente = str(tmp_path / "nao_existe")

    resultado_gate = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--dir", pasta_inexistente],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=TOOL_ROOT,
    )

    assert resultado_gate.returncode == 1


# ── Validação de schemas ──

def test_schemas_sao_validos():
    """Todos os 3 schemas devem ser JSON Schema Draft 2020-12 válidos."""
    schemas_dir = os.path.join(TOOL_ROOT, "schemas")
    for nome in ["schema_intake_request.json", "schema_stack_selecionada.json", "schema_sizing_output.json"]:
        caminho = os.path.join(schemas_dir, nome)
        assert os.path.isfile(caminho), f"Schema {nome} ausente"
        with open(caminho, "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert schema.get("$schema", "").endswith("2020-12/schema"), f"{nome}: $schema invalido"
        assert schema.get("additionalProperties") is False, f"{nome}: additionalProperties deve ser false"
        assert len(schema.get("required", [])) > 0, f"{nome}: deve ter required"


# ── Exatidão de sizing: fixtures de ouro (aritmética exata, mata mutantes
#    de math.ceil, margem 1.2, mínimos e entrada trocada) ──

# Fixture de ouro: derivada deterministicamente dos dados canônicos
# (catalogo_nichos.json x requisitos_recursos.json) com a mesma fórmula da
# fase 3 (soma por nicho, margem 1.2, math.ceil, mínimos 2/4/40).
# Se alguém mudar requisitos_recursos.json ou a fórmula sem querer, este
# teste quebra e força atualização consciente da fixture.
FIXTURES_OURO_SIZING = {
    "clinicas":      {"vcpu": 9, "ram_gb": 9,  "disco_gb": 96,  "bancos": 4},
    "delivery":      {"vcpu": 6, "ram_gb": 8,  "disco_gb": 96,  "bancos": 3},
    "farmacias":     {"vcpu": 4, "ram_gb": 4,  "disco_gb": 48,  "bancos": 2},
    "b2b_industrial": {"vcpu": 6, "ram_gb": 11, "disco_gb": 108, "bancos": 4},
    "energia_solar": {"vcpu": 6, "ram_gb": 6,  "disco_gb": 72,  "bancos": 4},
}


@pytest.mark.parametrize("slug,texto", NICHOS_REAIS, ids=[n[0] for n in NICHOS_REAIS])
def test_sizing_valores_exatos_por_nicho(slug, texto, tmp_path):
    """Sizing de cada nicho deve bater a fixture de ouro com igualdade
    estrita (==), não apenas pisos (>=)."""
    pasta = str(tmp_path / f"saida_gold_{slug}")
    os.makedirs(pasta, exist_ok=True)

    resultado = _run_pipeline(texto, pasta)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr

    plano = _carregar_plano(pasta)
    f3 = plano["fase_3_sizing"]["saida"]
    ouro = FIXTURES_OURO_SIZING[slug]

    assert f3["vps"]["vcpu"] == ouro["vcpu"], (
        f"{slug}: vcpu esperado {ouro['vcpu']}, obtido {f3['vps']['vcpu']}"
    )
    assert f3["vps"]["ram_gb"] == ouro["ram_gb"], (
        f"{slug}: ram_gb esperado {ouro['ram_gb']}, obtido {f3['vps']['ram_gb']}"
    )
    assert f3["vps"]["disco_gb"] == ouro["disco_gb"], (
        f"{slug}: disco_gb esperado {ouro['disco_gb']}, obtido {f3['vps']['disco_gb']}"
    )
    assert len(f3["bancos_logicos"]) == ouro["bancos"], (
        f"{slug}: bancos esperados {ouro['bancos']}, obtidos {len(f3['bancos_logicos'])}"
    )


def test_dimensionar_unidade_aritmetica_exata(tmp_path):
    """Teste de unidade direto de dimensionar(): soma conhecida + margem 1.2
    + ceil + mínimos, sem subprocess — determinismo aritmético puro."""
    sys.path.insert(0, os.path.join(TOOL_ROOT, "scripts", "phases"))
    from importlib import import_module
    sizing = import_module("03_sizing")

    # Caso 1: mínimo prático domina (2 vCPU / 4 GB / 40 GB)
    r1 = sizing.dimensionar([])  # vazio falha
    assert r1.sucesso is False  # contrato: lista vazia é erro

    r2 = sizing.dimensionar([{"nome": "Typebot"}])  # 1 vcpu, 1 ram, 20 disco
    assert r2.sucesso is True
    # 1*1.2=1.2 -> ceil 2 (mínimo 2); 1*1.2=1.2 -> ceil 2 < 4 (mínimo 4);
    # 20*1.2=24 -> ceil 24 < 40 (mínimo 40)
    assert r2.valor["vps"]["vcpu"] == 2
    assert r2.valor["vps"]["ram_gb"] == 4
    assert r2.valor["vps"]["disco_gb"] == 40

    # Caso 2: soma exata com arredondamento para cima
    # Typebot+Chatwoot: vcpu 3*1.2=3.6->4; ram 3*1.2=3.6->4; disco 40*1.2=48
    r3 = sizing.dimensionar([{"nome": "Typebot"}, {"nome": "Chatwoot"}])
    assert r3.valor["vps"]["vcpu"] == 4
    assert r3.valor["vps"]["ram_gb"] == 4
    assert r3.valor["vps"]["disco_gb"] == 48

    # Caso 3: arredondamento com 0.5 ram (Listmonk 0.5)
    # Listmonk: vcpu 1*1.2=1.2->2(mín); ram 0.5*1.2=0.6->1(mín 4); disco 10*1.2=12(mín 40)
    r4 = sizing.dimensionar([{"nome": "Listmonk"}])
    assert r4.valor["vps"]["vcpu"] == 2
    assert r4.valor["vps"]["ram_gb"] == 4
    assert r4.valor["vps"]["disco_gb"] == 40

    # Caso 4: ferramenta desconhecida não soma nada e é reportada
    r5 = sizing.dimensionar([{"nome": "FerramentaInexistente"}])
    assert r5.sucesso is True
    assert r5.valor["vps"]["vcpu"] == 2  # mínimo
    assert "FerramentaInexistente" in r5.valor["ferramentas_sem_banco"]
    assert any(
        f["ferramenta"] == "FerramentaInexistente" and not f["requisitos_encontrados"]
        for f in r5.valor["fontes_consultadas"]
    )


# ── Testes do tipo de origem "nicho dinâmico" (Fluxo 02, fora dos 5 nichos fixos) ──

def _criar_ferramentas_json(base_dir: str, ferramentas: list) -> str:
    caminho = os.path.join(base_dir, "ferramentas.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(ferramentas, f)
    return caminho


def _run_pipeline_ferramentas_json(texto: str, ferramentas_json: str, pasta: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, PIPELINE_SCRIPT, "plan", texto, "--ferramentas-json", ferramentas_json, "--pasta", pasta]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=TOOL_ROOT)


def test_nicho_dinamico_ponta_a_ponta(tmp_path):
    """Achado real (18/09/2026): um domínio de negócio fora dos 5 nichos
    fixos do catálogo (ex.: "gestão de tarefas") sempre batia
    NICHO_NAO_RECONHECIDO, mesmo quando a stack de ferramentas OSS já
    tinha sido decidida em outra etapa (PRÉ-PLANO do aidd-planner).
    Reprodução real via CLI: `ops plan "<texto>" --ferramentas-json
    <arquivo> --pasta <dest>` deve reconhecer a origem como nicho
    dinâmico, pular o casamento por palavra-chave e gravar um
    PLANO-INFRAESTRUTURA.json 100% válido contra o mesmo schema
    canônico — sem nenhuma mudança de schema."""
    ferramentas_path = _criar_ferramentas_json(str(tmp_path), [{"nome": "Evolution API"}])
    pasta = str(tmp_path / "saida_dinamico")
    os.makedirs(pasta, exist_ok=True)

    resultado = _run_pipeline_ferramentas_json("gestao de tarefas", ferramentas_path, pasta)
    assert resultado.returncode == 0, (
        f"Exit {resultado.returncode}.\nSTDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"
    )

    plano = _carregar_plano(pasta)
    f1 = plano["fase_1_intake"]["saida"]
    assert f1["nicho_slug"].startswith("dinamico_")
    assert "gestao de tarefas" in f1["nicho_nome_exibicao"].lower() or "gestao_de_tarefas" in f1["nicho_slug"]

    f2 = plano["fase_2_curadoria"]["saida"]
    assert [f["nome"] for f in f2["ferramentas"]] == ["Evolution API"]

    f3 = plano["fase_3_sizing"]["saida"]
    assert f3["bancos_logicos"] == []  # Evolution API nao exige banco relacional


def test_nicho_dinamico_sem_ferramentas_falha(tmp_path):
    """Nicho dinâmico exige ao menos 1 ferramenta planejada — lista vazia
    deve reprovar explicitamente (FERRAMENTAS_VAZIAS), nunca gerar um
    plano "vazio" silenciosamente."""
    ferramentas_path = _criar_ferramentas_json(str(tmp_path), [])
    pasta = str(tmp_path / "saida_dinamico_vazio")
    os.makedirs(pasta, exist_ok=True)

    resultado = _run_pipeline_ferramentas_json("gestao de tarefas", ferramentas_path, pasta)
    assert resultado.returncode == 1
    assert "FERRAMENTAS_VAZIAS" in resultado.stdout
