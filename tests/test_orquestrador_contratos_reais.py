# -*- coding: utf-8 -*-
"""Ticket 12 (D2 / DoD 6): o orquestrador so passa o bastao, nao escreve contrato.

Regras provadas aqui:
1. O orquestrador nunca grava `PLANO-INFRAESTRUTURA.json` nem nenhum
   `HANDOFF_*.json`: quem produz o contrato e' a ferramenta dona da etapa.
   Sem contrato gravado pela ferramenta, o bastao nao passa (etapa reprova).
2. Os contratos gravados pelas ferramentas chegam ao fim do fluxo byte a byte
   (o orquestrador so le).
3. Cada ferramenta recebe os tickets que a planta (C2) roteou para ela.
4. O `dispatch` das fatias VSA roda no comeco da etapa do master, nao na do
   construtor.
5. A etapa 7 audita o projeto gerado (`ecossistema.py forge audit <projeto>`),
   nao o monorepo (`ecossistema.py audit`).

As ferramentas pesadas (forge, construtores, master, enterprise, ops) sao
substituidas por um executor que registra o comando e grava o contrato como a
ferramenta gravaria; o planner roda de verdade (subprocess real), entao o C2 e
o VSA_DISPATCH.json lidos pelo orquestrador sao os do proprio planner.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.orquestrador_sincrono import OrquestradorSincrono  # noqa: E402

SPECS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "specs"
HEX64 = "a" * 64
CONSTRUTOR_POR_FLUXO = {1: "aidd-pure", 2: "aidd-open", 3: "aidd-freedom"}
NOMES_CONTRATO = {
    "C1": Path(".aidd") / "HANDOFF_FORGE_PLANNER.json",
    "C2": Path("HANDOFF_PLANNER_ENGINE.json"),
    "C3": Path("HANDOFF_ENGINE_MASTER.json"),
    "C4": Path("HANDOFF_MASTER_ENTERPRISE.json"),
    "C5": Path("HANDOFF_ENTERPRISE_OPS.json"),
}
SCHEMA_POR_CONTRATO = {
    "C1": "handoff-forge-to-planner.schema.json",
    "C3": "handoff-engine-to-master.schema.json",
    "C4": "handoff-master-to-enterprise.schema.json",
    "C5": "handoff-enterprise-to-ops.schema.json",
}


# ---------------------------------------------------------------------------
# Contratos como cada ferramenta dona os grava
# ---------------------------------------------------------------------------

def _c1(pasta: Path) -> Dict[str, Any]:
    return {
        "versao_schema": "1.0.0",
        "projeto_dir": str(pasta),
        "git": {"inicializado": True, "commit_inicial": "abc1234"},
        "dependencias": [{"pacote": "jsonschema", "versao": "4.0.0"}],
        "leis_e_guardas": [{"gate": "G_INJECT.py", "sha256": HEX64}],
        "harnesses": ["claude"],
        "almoxarifado": {"catalogo_sha256": HEX64, "pecas_disponiveis": []},
        "capacidade_llm": "delegado_com_resposta",
        "estrutura_projeto": {"pastas_criadas": ["gates"]},
    }


def _c3(fluxo: int, slug: str) -> Dict[str, Any]:
    return {
        "versao_schema": "1.0.0",
        "origem_engine": CONSTRUTOR_POR_FLUXO[fluxo],
        "projeto_slug": slug,
        "slices_geradas": [{
            "slice_nome": slug,
            "caminho_src": f"src/modules/{slug}",
            "sha256_arvore": HEX64,
            "endpoints": [{"rota": f"/api/{slug}", "metodo": "GET", "funcao": "listar"}],
            "tabelas_sql": [slug.replace("-", "_")],
        }],
        "artefatos_frontend": {
            "tecnologia": "tanstack_router",
            "paginas_geradas": ["/dashboard"],
            "origem_design": "custom_tdd",
        },
        "testes_executados": {
            "total": 2, "passaram": 2, "falharam": 0, "zero_stubs": True,
            "relatorio_pytest": {"caminho": "reports/pytest.xml", "exit_code": 0},
        },
        "arquivos_fora_da_zona": [],
    }


def _c4(pasta: Path, slug: str) -> Dict[str, Any]:
    return {
        "versao_schema": "1.0.0",
        "diretorio_projeto": str(pasta),
        "servidor_sobe": {"log_subida": "log_subida.txt", "porta": 8000},
        "quarteto": [
            {"rota": rota, "status_http_medido": 200}
            for rota in ("/openapi.json", "/webhooks", "/mcp", "/docs")
        ],
        "componentes_para_blindagem": [
            {"tipo": "slice", "caminho_relativo": f"src/modules/{slug}", "sha256": HEX64},
        ],
    }


def _c5(pasta: Path) -> Dict[str, Any]:
    return {
        "versao_schema": "1.0.0",
        "diretorio_projeto": str(pasta),
        "registry": {"caminho": "COMPONENT-REGISTRY.json", "sha256": HEX64},
        "selo_sha256": HEX64,
        "drift": {"verificado": True, "exit_code": 0},
        "perfil_app": {
            "tipo_runtime": "monolito_modular_docker",
            "portas_expostas": [8000],
            "banco": "sqlite",
        },
    }


def _gravar_json(caminho: Path, dados: Dict[str, Any]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def _sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _subcomando(cmd: List[str]) -> List[str]:
    """Argumentos depois de `ecossistema.py` (vazio se nao for a CLI raiz)."""
    textos = [str(c) for c in cmd]
    for indice, valor in enumerate(textos):
        if Path(valor).name == "ecossistema.py":
            return textos[indice + 1:]
    return []


class FerramentasDeTeste:
    """Executor no lugar de `_executar_comando`: registra cada chamada.

    `gravar_contratos=True` faz cada ferramenta gravar o proprio contrato,
    como a ferramenta dona gravaria. O planner sempre roda de verdade.
    """

    def __init__(self, orq: OrquestradorSincrono, gravar_contratos: bool):
        self.orq = orq
        self.gravar_contratos = gravar_contratos
        self.chamadas: List[Dict[str, Any]] = []

    def __call__(self, cmd: List[str], cwd: Optional[Path] = None,
                 env_extra: Optional[Dict[str, str]] = None) -> int:
        sub = _subcomando(cmd)
        self.chamadas.append({"sub": sub, "env": dict(env_extra or {})})
        pasta = self.orq.pasta
        if sub[:1] == ["planner"]:
            proc = subprocess.run(
                [sys.executable, str(ROOT_DIR / "ecossistema.py")] + sub,
                cwd=str(ROOT_DIR), capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            return proc.returncode
        if not self.gravar_contratos:
            return 0
        if sub[:2] == ["forge", "init"]:
            _gravar_json(pasta / NOMES_CONTRATO["C1"], _c1(pasta))
        elif sub[:1] in (["pure-motor"], ["open-motor"], ["freedom-motor"]):
            _gravar_json(pasta / NOMES_CONTRATO["C3"], _c3(self.orq.fluxo, self.orq.slug))
        elif sub[:2] == ["master", "add-module"]:
            _gravar_json(pasta / NOMES_CONTRATO["C4"], _c4(pasta, self.orq.slug))
        elif sub[:2] == ["enterprise", "verificar-drift"]:
            _gravar_json(pasta / NOMES_CONTRATO["C5"], _c5(pasta))
        elif sub[:2] == ["ops", "plan"]:
            (pasta / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")
            (pasta / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
        return 0

    def subs(self) -> List[List[str]]:
        return [c["sub"] for c in self.chamadas]

    def indice(self, prefixo: List[str]) -> int:
        for posicao, sub in enumerate(self.subs()):
            if sub[:len(prefixo)] == prefixo:
                return posicao
        return -1


def _orquestrador(tmp_path: Path, fluxo: int) -> OrquestradorSincrono:
    pasta = tmp_path / f"projeto-fluxo-{fluxo}"
    origem = tmp_path / "export-lowcode"
    origem.mkdir(exist_ok=True)
    (origem / "package.json").write_text('{"name": "app"}\n', encoding="utf-8")
    return OrquestradorSincrono(
        fluxo=fluxo,
        nome="Gestao Clinicas",
        slug="gestao-clinicas",
        dominio="clinicas",
        pasta=str(pasta),
        origem_export=str(origem) if fluxo == 3 else None,
    )


def _sem_entrega(orq: OrquestradorSincrono) -> None:
    # O card de entrega (git init + guia) nao faz parte do contrato testado.
    orq._fechar_entrega = lambda: None


# ---------------------------------------------------------------------------
# Sanidade: os contratos de teste sao os que os schemas exigem
# ---------------------------------------------------------------------------

def test_contratos_de_teste_aderem_aos_schemas(tmp_path):
    payloads = {
        "C1": _c1(tmp_path),
        "C3": _c3(1, "gestao-clinicas"),
        "C4": _c4(tmp_path, "gestao-clinicas"),
        "C5": _c5(tmp_path),
    }
    for chave, payload in payloads.items():
        schema = json.loads((SPECS_DIR / SCHEMA_POR_CONTRATO[chave]).read_text(encoding="utf-8"))
        jsonschema.validate(instance=payload, schema=schema)


# ---------------------------------------------------------------------------
# 1. Nunca grava PLANO-INFRAESTRUTURA.json nem HANDOFF_*.json
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fluxo", [1, 2, 3])
def test_orquestrador_nao_grava_plano_infra_nem_handoff(tmp_path, fluxo):
    orq = _orquestrador(tmp_path, fluxo)
    _sem_entrega(orq)
    ferramentas = FerramentasDeTeste(orq, gravar_contratos=False)
    orq._executar_comando = ferramentas

    sucesso = orq.executar_fluxo_completo()

    assert sucesso is False, "sem contrato gravado pelas ferramentas o bastao nao pode passar"
    assert not list(orq.pasta.rglob("PLANO-INFRAESTRUTURA.json"))
    escritos = {p.name for p in orq.pasta.rglob("HANDOFF_*.json")}
    # O unico handoff presente e' o C2, gravado pelo planner real.
    assert escritos <= {"HANDOFF_PLANNER_ENGINE.json"}, escritos
    assert ferramentas.indice(["forge", "init"]) == 0
    # C1 ausente => para na etapa 1, sem chamar o planner.
    assert ferramentas.indice(["planner", "init"]) == -1


def test_construtor_sem_contrato_c3_trava_o_bastao(tmp_path, capsys):
    orq = _orquestrador(tmp_path, 1)
    _sem_entrega(orq)
    ferramentas = FerramentasDeTeste(orq, gravar_contratos=True)
    orq._executar_comando = ferramentas
    assert orq.etapa_01_forge() is True
    assert orq.etapa_02_planner() is True

    # O construtor roda, mas nao grava o C3.
    def construtor_mudo(cmd, cwd=None, env_extra=None):
        ferramentas.chamadas.append({"sub": _subcomando(cmd), "env": dict(env_extra or {})})
        return 0

    orq._executar_comando = construtor_mudo
    assert orq.etapa_03_engine() is False
    assert not (orq.pasta / "HANDOFF_ENGINE_MASTER.json").exists()
    assert "HANDOFF_ENGINE_MASTER.json" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 2. Contratos das ferramentas chegam intactos; tickets roteados entregues
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fluxo", [1, 2, 3])
def test_fluxo_completo_le_contratos_das_ferramentas_sem_alterar(tmp_path, fluxo):
    orq = _orquestrador(tmp_path, fluxo)
    _sem_entrega(orq)
    ferramentas = FerramentasDeTeste(orq, gravar_contratos=True)
    orq._executar_comando = ferramentas

    hashes: Dict[str, str] = {}
    etapas = [
        (orq.etapa_01_forge, ["C1"]),
        (orq.etapa_02_planner, ["C2"]),
        (orq.etapa_03_engine, ["C3"]),
        (orq.etapa_04_master, ["C4"]),
        (orq.etapa_05_enterprise, ["C5"]),
        (orq.etapa_06_ops, []),
        (orq.etapa_07_auditoria, []),
    ]
    for etapa, contratos in etapas:
        assert etapa() is True, etapa.__name__
        for chave in contratos:
            hashes[chave] = _sha(orq.pasta / NOMES_CONTRATO[chave])

    for chave, sha in hashes.items():
        assert _sha(orq.pasta / NOMES_CONTRATO[chave]) == sha, f"{chave} foi reescrito pelo orquestrador"
    assert not list(orq.pasta.rglob("PLANO-INFRAESTRUTURA.json"))

    # O manifesto final registra os contratos realmente lidos (com hash).
    manifesto = json.loads((orq.pasta / "ORQUESTRACAO_EXECUCAO.json").read_text(encoding="utf-8"))
    lidos = {item["arquivo"]: item["sha256"] for item in manifesto["contratos_lidos"]}
    for chave, sha in hashes.items():
        assert lidos[NOMES_CONTRATO[chave].as_posix()] == sha


@pytest.mark.parametrize("fluxo", [1, 2, 3])
def test_cada_ferramenta_recebe_os_tickets_dela(tmp_path, fluxo):
    orq = _orquestrador(tmp_path, fluxo)
    _sem_entrega(orq)
    ferramentas = FerramentasDeTeste(orq, gravar_contratos=True)
    orq._executar_comando = ferramentas
    assert orq.executar_fluxo_completo() is True

    c2_path = orq.pasta / "HANDOFF_PLANNER_ENGINE.json"
    c2 = json.loads(c2_path.read_text(encoding="utf-8"))
    esperado: Dict[str, List[str]] = {}
    for ticket in c2["tickets"]:
        esperado.setdefault(ticket["ferramenta_destino"], []).append(ticket["id"])

    construtor = CONSTRUTOR_POR_FLUXO[fluxo]
    motor = {1: "pure-motor", 2: "open-motor", 3: "freedom-motor"}[fluxo]
    por_comando = {
        construtor: [motor],
        "aidd-master": ["master", "add-module"],
        "aidd-enterprise": ["enterprise", "inject"],
        "aidd-ops": ["ops", "plan"],
    }
    for ferramenta, prefixo in por_comando.items():
        chamada = ferramentas.chamadas[ferramentas.indice(prefixo)]
        tickets = json.loads(chamada["env"]["AIDD_TICKETS"])
        assert [t["id"] for t in tickets] == esperado[ferramenta], ferramenta
        assert all(t["ferramenta_destino"] == ferramenta for t in tickets)
        assert Path(chamada["env"]["AIDD_HANDOFF_PLANNER"]) == c2_path

    if fluxo == 2:
        # A factory recebe a planta (C2) do planner, nunca um plano inventado.
        sub = ferramentas.chamadas[ferramentas.indice(["open-motor"])]["sub"]
        assert Path(sub[sub.index("--plano") + 1]) == c2_path


# ---------------------------------------------------------------------------
# 3. dispatch na etapa do master
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fluxo", [1, 2, 3])
def test_dispatch_roda_no_comeco_da_etapa_master(tmp_path, fluxo):
    orq = _orquestrador(tmp_path, fluxo)
    _sem_entrega(orq)
    ferramentas = FerramentasDeTeste(orq, gravar_contratos=True)
    orq._executar_comando = ferramentas
    assert orq.etapa_01_forge() and orq.etapa_02_planner()
    assert (orq.pasta / "VSA_DISPATCH.json").is_file(), "o planner grava o manifesto VSA"

    inicio_engine = len(ferramentas.chamadas)
    assert orq.etapa_03_engine() is True
    assert all(sub[:1] != ["dispatch"] for sub in ferramentas.subs()[inicio_engine:])

    inicio_master = len(ferramentas.chamadas)
    assert orq.etapa_04_master() is True
    subs_master = ferramentas.subs()[inicio_master:]
    assert subs_master[0][:1] == ["dispatch"]
    assert Path(subs_master[0][subs_master[0].index("--target-dir") + 1]) == orq.pasta
    assert Path(subs_master[0][subs_master[0].index("--dispatch") + 1]) == orq.pasta / "VSA_DISPATCH.json"
    assert subs_master[1][:2] == ["master", "init"]


# ---------------------------------------------------------------------------
# 4. Etapa 7 audita o projeto, nao o monorepo
# ---------------------------------------------------------------------------

def test_etapa_7_roda_forge_audit_no_projeto(tmp_path):
    orq = _orquestrador(tmp_path, 1)
    ferramentas = FerramentasDeTeste(orq, gravar_contratos=True)
    orq._executar_comando = ferramentas
    orq.pasta.mkdir(parents=True, exist_ok=True)

    assert orq.etapa_07_auditoria() is True
    subs = ferramentas.subs()
    assert ["audit"] not in subs, "a etapa 7 nao audita o monorepo"
    auditoria = [sub for sub in subs if sub[:2] == ["forge", "audit"]]
    assert len(auditoria) == 1
    assert Path(auditoria[0][2]) == orq.pasta


def test_etapa_7_reprova_quando_forge_audit_reprova(tmp_path):
    orq = _orquestrador(tmp_path, 1)
    orq.pasta.mkdir(parents=True, exist_ok=True)
    orq._executar_comando = lambda cmd, cwd=None, env_extra=None: 1
    assert orq.etapa_07_auditoria() is False
    assert not (orq.pasta / "ORQUESTRACAO_EXECUCAO.json").exists()


# ---------------------------------------------------------------------------
# 5. A factory aceita a planta real (C2) como entrada
# ---------------------------------------------------------------------------

def test_factory_aceita_c2_real_do_planner(tmp_path):
    pasta = tmp_path / "planta-fluxo-2"
    proc = subprocess.run(
        [sys.executable, str(ROOT_DIR / "ecossistema.py"), "planner", "init",
         "--fluxo", "2", "--nome", "Hub Clinicas", "--slug", "hub-clinicas",
         "--dominio", "clinicas", "--pasta", str(pasta)],
        cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    # Processo proprio: o pacote `core` da factory colide com o `core` da raiz.
    factory_dir = ROOT_DIR / "modulos" / "02-triade-motores" / "fluxo-02-open" / "core" / "aidd-open"
    sonda = (
        "import json, sys\n"
        "import pipeline_factory\n"
        "r = pipeline_factory._carregar_plano(sys.argv[1])\n"
        "print(json.dumps({'sucesso': r.sucesso, 'erro': r.erro,"
        " 'tem_sizing': bool(r.sucesso and r.valor['fase_3_sizing'].get('saida') is not None)}))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", sonda, str(pasta / "HANDOFF_PLANNER_ENGINE.json")],
        cwd=str(factory_dir / "scripts"), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env={**__import__("os").environ, "PYTHONPATH": str(factory_dir)},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    resultado = json.loads(proc.stdout.strip().splitlines()[-1])
    assert resultado["sucesso"] is True, resultado
    assert resultado["tem_sizing"] is True
