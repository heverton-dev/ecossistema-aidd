# -*- coding: utf-8 -*-
"""
Teste de Fronteira e Almoxarifado do AIDD-Pure / Generator (Ticket 15, D1 / DoD 7).

Regras de conformidade:
1. V3 — o injetor e a CLI `aidd_inject` sao PEÇAS DO ALMOXARIFADO. O aidd-pure
   consome `componentes/compartilhado/injetor/variantes/aidd-pure/**` via
   `aidd_forge.core.almoxarifado.caminho_peca`: todo modulo ligado em
   `scripts.core.injector.*` tem de resolver `__file__` para a peça do
   almoxarifado. As copias legacy em `tools/aidd-pure/` PERMANECEM no lugar
   neste ticket (PLANO-EVOLUCAO item 6 / Ticket 8 "keep old copies in place";
   a remocao definitiva é o Bloco 4 / Ticket 19) — elas nao podem ser a
   origem do que o gerador executa.
2. V11 — o cache do protocolo delegado vive no PROJETO (`.aidd/cache`), nunca
   dentro da ferramenta. `import` nao pode criar diretorio dentro de
   `tools/aidd-pure/`, e a requisicao delegada tem de ser gravada no projeto.
"""
import fnmatch
import importlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
PURE_DIR = ROOT_DIR / "tools" / "aidd-pure"
FORGE_DIR = ROOT_DIR / "tools" / "aidd-forge"
CATALOGO = ROOT_DIR / "componentes" / "compartilhado"
PECA_INJETOR = "injetor/variantes/aidd-pure"

for _p in (
    str(ROOT_DIR),
    str(PURE_DIR / "scripts"),
    str(PURE_DIR / "scripts" / "phases"),
    str(PURE_DIR),
    str(FORGE_DIR),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aidd_forge.core.almoxarifado import caminho_peca  # noqa: E402


def _importar(nome: str, caminho_raiz: Path):
    """Importa modulo do aidd-pure via caminho, sem depender do cwd."""
    if nome in sys.modules:
        return sys.modules[nome]
    raiz = str(caminho_raiz)
    if raiz not in sys.path:
        sys.path.insert(0, raiz)
    return importlib.import_module(nome)


def _copias_locais_do_injetor() -> list:
    """Caminhos relativos dentro de tools/aidd-pure que casam `**/*inject*`."""
    encontrados = []
    for arquivo in PURE_DIR.rglob("*"):
        if not arquivo.is_file():
            continue
        rel = arquivo.relative_to(PURE_DIR).as_posix()
        if fnmatch.fnmatchcase(rel, "**/*inject*"):
            encontrados.append(rel)
    return sorted(encontrados)


def _dentro(caminho: Path, base: Path) -> bool:
    try:
        caminho.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


# =============================================================================
# V3 — almoxarifado unico: o injetor usado pelo gerador vem da peca canonica
# =============================================================================

def test_copias_legacy_permanecem_mas_nao_sao_a_origem_do_generador():
    """As copias legacy continuam no lugar (Ticket 8) e o gerador nao as usa.

    Este teste morde mesmo com as copias presentes: sem o carregador do
    almoxarifado, `scripts.core.injector.*` resolveria para a copia local de
    `tools/aidd-pure/` e falharia.
    """
    copias = _copias_locais_do_injetor()
    pecas = _importar("scripts.core.pecas_catalogo", PURE_DIR / "scripts")
    raiz_canonica = ROOT_DIR / "componentes" / "compartilhado" / PECA_INJETOR

    for modulo in ("contrato", "detector_camada", "injetor", "materializador"):
        origem = Path(sys.modules[f"scripts.core.injector.{modulo}"].__file__).resolve()
        assert _dentro(origem, raiz_canonica), (
            f"scripts.core.injector.{modulo} veio de {origem}, fora da peca "
            f"canonica {raiz_canonica}. As copias legacy em tools/aidd-pure/ "
            f"({len(copias)} arquivo(s) casando '**/*inject*') nao podem ser a "
            "origem do que o gerador executa."
        )
    assert pecas.PECA_INJETOR == PECA_INJETOR


def test_pecas_do_injetor_existem_no_almoxarifado():
    """As peças que o gerador precisa estão no almoxarifado e são resolvíveis."""
    esperadas = [
        f"{PECA_INJETOR}/aidd_inject.py",
        f"{PECA_INJETOR}/G_INJECT.py",
        f"{PECA_INJETOR}/core/injector/__init__.py",
        f"{PECA_INJETOR}/core/injector/contrato.py",
        f"{PECA_INJETOR}/core/injector/detector_camada.py",
        f"{PECA_INJETOR}/core/injector/injetor.py",
        f"{PECA_INJETOR}/core/injector/materializador.py",
        f"{PECA_INJETOR}/core/injector/profiles_registry.py",
        f"{PECA_INJETOR}/core/injector/scaffolds.py",
        f"{PECA_INJETOR}/core/injector/sincronizador_harness.py",
        f"{PECA_INJETOR}/core/injector/schema_injector_request.json",
    ]
    for nome in esperadas:
        caminho = caminho_peca(nome, raiz=ROOT_DIR)
        assert caminho.is_file(), f"peça ausente no almoxarifado: {nome}"


def test_catalogo_declarou_o_injetor_do_pure_como_peca_do_almoxarifado():
    """CATALOGO.json registra a peça com dono enterprise e consumidor aidd-pure."""
    catalogo = json.loads((CATALOGO / "CATALOGO.json").read_text(encoding="utf-8"))
    por_nome = {p["nome"]: p for p in catalogo["pecas"]}
    peca = por_nome[f"{PECA_INJETOR}/core/injector/injetor.py"]
    assert peca["dono_do_conteudo"] == "aidd-enterprise", peca
    assert peca["consumidores"] == ["aidd-pure"], peca


def test_modulos_do_injetor_sao_carregados_da_peca_do_almoxarifado():
    """O carregador do aidd-pure importa o injetor do almoxarifado, não de cópia."""
    pecas = _importar("scripts.core.pecas_catalogo", PURE_DIR / "scripts")
    assert hasattr(pecas, "caminho_peca"), (
        "scripts.core.pecas_catalogo deve expor caminho_peca do almoxarifado"
    )
    assert hasattr(pecas, "registrar_injetor"), (
        "scripts.core.pecas_catalogo deve expor registrar_injetor()"
    )

    chamadas: list = []
    caminho_peca_real = pecas.caminho_peca

    def espiao(nome, raiz=None):
        chamadas.append(nome)
        return caminho_peca_real(nome, raiz=raiz)

    pecas.caminho_peca = espiao
    try:
        pecas.registrar_injetor()
    finally:
        pecas.caminho_peca = caminho_peca_real

    assert chamadas, "o carregador do injetor não consultou o almoxarifado"
    assert all(n.startswith(PECA_INJETOR) for n in chamadas), chamadas

    modulos = {
        "scripts.core.injector": f"{PECA_INJETOR}/core/injector/__init__.py",
        "scripts.core.injector.contrato": f"{PECA_INJETOR}/core/injector/contrato.py",
        "scripts.core.injector.detector_camada": f"{PECA_INJETOR}/core/injector/detector_camada.py",
        "scripts.core.injector.injetor": f"{PECA_INJETOR}/core/injector/injetor.py",
        "scripts.core.injector.materializador": f"{PECA_INJETOR}/core/injector/materializador.py",
        "scripts.core.injector.profiles_registry": f"{PECA_INJETOR}/core/injector/profiles_registry.py",
        "scripts.core.injector.scaffolds": f"{PECA_INJETOR}/core/injector/scaffolds.py",
        "scripts.core.injector.sincronizador_harness": f"{PECA_INJETOR}/core/injector/sincronizador_harness.py",
    }
    for nome_modulo, nome_peca in modulos.items():
        modulo = sys.modules.get(nome_modulo)
        assert modulo is not None, f"módulo {nome_modulo} não foi registrado"
        origem = Path(modulo.__file__).resolve()
        esperado = caminho_peca(nome_peca, raiz=ROOT_DIR).resolve()
        assert origem == esperado, (
            f"{nome_modulo} veio de {origem}, não da peça {esperado}"
        )


def test_ancoras_de_caminho_da_peca_apontam_para_o_consumidor():
    """Peça relocável: âncoras `__file__` são reancoradas no consumidor."""
    pecas = _importar("scripts.core.pecas_catalogo", PURE_DIR / "scripts")
    pecas.registrar_injetor()

    detector = sys.modules["scripts.core.injector.detector_camada"]
    assert Path(detector._PHASES_DIR).resolve() == (PURE_DIR / "scripts" / "phases").resolve(), (
        "detector_camada._PHASES_DIR deve apontar para tools/aidd-pure/scripts/phases"
    )

    injetor = sys.modules["scripts.core.injector.injetor"]
    assert Path(injetor._default_ecossistema_root()).resolve() == ROOT_DIR.resolve(), (
        "_default_ecossistema_root() deve devolver a raiz do ecossistema"
    )

    contrato = sys.modules["scripts.core.injector.contrato"]
    assert contrato.carregar_schema()["type"] == "object", (
        "o schema do injetor deve carregar a partir da peça do almoxarifado"
    )


# =============================================================================
# V11 — cache do protocolo delegado vive no projeto
# =============================================================================

def test_cache_delegado_resolve_dentro_do_projeto(tmp_path: Path):
    """`<projeto>/.aidd/cache` e nunca a raiz da ferramenta."""
    utils = _importar("utils_delegacao", PURE_DIR / "scripts" / "phases")
    assert hasattr(utils, "resolver_cache_dir"), (
        "utils_delegacao deve expor resolver_cache_dir(projeto_dir)"
    )
    assert utils.resolver_cache_dir(tmp_path) == tmp_path / ".aidd" / "cache"
    assert not _dentro(utils.resolver_cache_dir(tmp_path), PURE_DIR)
    assert not _dentro(Path(utils.CACHE_DIR), PURE_DIR), (
        f"CACHE_DIR={utils.CACHE_DIR} está dentro da ferramenta"
    )


def test_import_de_utils_delegacao_nao_cria_diretorio_na_ferramenta():
    """Importar o módulo não pode materializar `.aidd/` dentro de tools/aidd-pure."""
    antes = sorted(p.as_posix() for p in PURE_DIR.rglob(".aidd"))
    caminho_modulo = PURE_DIR / "scripts" / "phases" / "utils_delegacao.py"
    spec = importlib.util.spec_from_file_location("utils_delegacao_isolado", caminho_modulo)
    if spec is None or spec.loader is None:
        raise AssertionError(f"módulo ilegível: {caminho_modulo}")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    depois = sorted(p.as_posix() for p in PURE_DIR.rglob(".aidd"))
    assert antes == depois, f"import criou estrutura na ferramenta: {set(depois) - set(antes)}"
    assert not (PURE_DIR / "scripts" / ".aidd").exists(), (
        "tools/aidd-pure/scripts/.aidd não pode existir (V11)"
    )


def test_requisicao_delegada_e_gravada_no_projeto(tmp_path: Path, monkeypatch):
    """A requisição delegada é escrita em `<projeto>/.aidd/cache`."""
    utils = _importar("utils_delegacao", PURE_DIR / "scripts" / "phases")
    monkeypatch.setattr(utils, "CACHE_DIR", utils.resolver_cache_dir(tmp_path))
    utils.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    requisicao = utils.RequisicaoLLMDelegada(
        prompt="p", contexto="c", fase="phase_01", modelo_sugerido="m"
    )
    caminho = requisicao.escrever_arquivo()

    assert caminho == tmp_path / ".aidd" / "cache" / f"_llm_request_{requisicao.id}.json"
    assert caminho.is_file()
    assert not _dentro(caminho, PURE_DIR)
    assert json.loads(caminho.read_text(encoding="utf-8"))["id"] == requisicao.id

def test_cache_com_cwd_dentro_da_ferramenta_cai_fora_de_tools(monkeypatch):
    """Rodar o aidd-pure de dentro de tools/aidd-pure não pode pôr o cache na ferramenta."""
    utils = _importar("utils_delegacao", PURE_DIR / "scripts" / "phases")
    monkeypatch.delenv("AIDD_PROJECT_DIR", raising=False)
    monkeypatch.chdir(PURE_DIR)
    cache = utils.resolver_cache_dir()
    assert not _dentro(cache, PURE_DIR.parent), f"cache dentro de tools/: {cache}"
    assert cache == PURE_DIR.parent.parent.resolve() / ".aidd" / "cache"


def test_cache_segue_o_projeto_do_handoff_do_planner(tmp_path, monkeypatch):
    """No fluxo 01 o orquestrador só informa AIDD_HANDOFF_PLANNER; o cache vai para o projeto dele."""
    utils = _importar("utils_delegacao", PURE_DIR / "scripts" / "phases")
    monkeypatch.delenv("AIDD_PROJECT_DIR", raising=False)
    monkeypatch.setenv("AIDD_HANDOFF_PLANNER", str(tmp_path / "HANDOFF_PLANNER_ENGINE.json"))
    monkeypatch.chdir(PURE_DIR.parent.parent)
    assert utils.resolver_cache_dir() == tmp_path.resolve() / ".aidd" / "cache"
