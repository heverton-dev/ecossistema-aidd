# -*- coding: utf-8 -*-
"""
Consumo do almoxarifado único pelo aidd-enterprise (D1 / D3 — Ticket 18).

O enterprise é o dono do conteúdo da peça "injetor", mas não guarda cópia dela:
a peça vive em `componentes/compartilhado/injetor/` e é resolvida por
`aidd_forge.core.almoxarifado.caminho_peca`. Antes de executar qualquer peça, o
selo SHA-256 do CATALOGO.json é conferido (blindagem: peça adulterada não roda).

Peças carregadas, nesta ordem (folhas antes de quem as importa):
  - injetor/profiles_registry.py  -> sys.modules['profiles_registry']
  - injetor/detector_camada.py    -> sys.modules['detector_camada']
  - injetor/inject.py             -> o Use Case `inject` (cmd_inject, run_inject, ...)

A peça `inject.py` calcula a raiz da ferramenta a partir de `__file__` (três
níveis acima: `application_enterprise/commands/inject.py` -> raiz do enterprise) para
achar `src/core` e o perfil do projeto. Por isso o módulo da peça recebe como
`__file__` a posição canônica do Use Case no enterprise (a âncora); o código
executado continua sendo o da peça (`__spec__.origin` e `co_filename` apontam
para o almoxarifado). As cópias antigas (application_enterprise/commands/inject.py,
src/core/detector_camada.py, src/core/profiles_registry.py) ficam no disco até
a remoção com o usuário (Ticket 19), sem ser importadas.
"""

import hashlib
import importlib.util
import sys
import types
from pathlib import Path

def _achar_raiz_repo(inicio: Path) -> Path:
    curr = inicio
    while curr and curr.parent != curr:
        if (curr / "ecossistema.py").is_file():
            return curr
        curr = curr.parent
    return inicio.parents[3]


_RAIZ = _achar_raiz_repo(Path(__file__).resolve().parent)
ENTERPRISE_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = ENTERPRISE_DIR / "src" / "core"

_VSA_FORGE = _RAIZ / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge"
FORGE_DIR = _VSA_FORGE if _VSA_FORGE.is_dir() else (ENTERPRISE_DIR.parent / "aidd-forge")

ANCORA_INJECT = ENTERPRISE_DIR / "application_enterprise" / "commands" / "inject.py"

PECA_INJECT = "injetor/inject.py"
PECAS_NUCLEO_INJETOR = (
    ("profiles_registry", "injetor/profiles_registry.py"),
    ("detector_camada", "injetor/detector_camada.py"),
)
PECA_SCHEMA = "injetor/schema_injector_request.json"
NOME_MODULO_INJETOR = "aidd_enterprise_injetor"

for _p in (str(ENTERPRISE_DIR), str(CORE_DIR), str(FORGE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aidd_forge.core.almoxarifado import caminho_peca, carregar_catalogo  # noqa: E402


class ErroSeloPeca(RuntimeError):
    """Peça do almoxarifado cujo sha256 não bate com o selo do CATALOGO.json."""


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def verificar_selo(nome: str, raiz=None) -> Path:
    """Resolve a peça `nome` e confere o sha256 contra o catálogo. Devolve o caminho."""
    catalogo = carregar_catalogo(raiz)
    entrada = next((p for p in catalogo.get("pecas", []) if p.get("nome") == nome), None)
    if entrada is None:
        raise ErroSeloPeca(f"peça '{nome}' ausente do CATALOGO.json")
    esperado = str(entrada.get("sha256", "")).split("sha256-", 1)[-1]
    caminho = caminho_peca(nome, raiz=raiz)
    obtido = _sha256(caminho)
    if not esperado or obtido != esperado:
        raise ErroSeloPeca(
            f"selo SHA-256 da peça '{nome}' não confere: catálogo={esperado or '(vazio)'} "
            f"disco={obtido} ({caminho})"
        )
    return caminho


def _executar(caminho: Path, nome_modulo: str, ancora: Path = None) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(nome_modulo, caminho)
    if spec is None or spec.loader is None:
        raise ImportError(f"peça ilegível: {caminho}")
    modulo = importlib.util.module_from_spec(spec)
    if ancora is not None:
        modulo.__file__ = str(ancora)
    anterior = sys.modules.get(nome_modulo)
    sys.modules[nome_modulo] = modulo
    try:
        spec.loader.exec_module(modulo)
    except BaseException:
        if anterior is not None:
            sys.modules[nome_modulo] = anterior
        else:
            sys.modules.pop(nome_modulo, None)
        raise
    return modulo


def _ja_carregado(nome_modulo: str, caminho: Path) -> bool:
    modulo = sys.modules.get(nome_modulo)
    origem = getattr(getattr(modulo, "__spec__", None), "origin", None)
    return bool(origem) and Path(origem).resolve() == caminho.resolve()


def carregar_injetor(raiz=None) -> types.ModuleType:
    """Carrega (idempotente) o injetor a partir das peças seladas do almoxarifado."""
    verificar_selo(PECA_SCHEMA, raiz=raiz)
    for nome_modulo, peca in PECAS_NUCLEO_INJETOR:
        caminho = verificar_selo(peca, raiz=raiz)
        if not _ja_carregado(nome_modulo, caminho):
            _executar(caminho, nome_modulo)
    caminho_inject = verificar_selo(PECA_INJECT, raiz=raiz)
    if _ja_carregado(NOME_MODULO_INJETOR, caminho_inject):
        return sys.modules[NOME_MODULO_INJETOR]
    return _executar(caminho_inject, NOME_MODULO_INJETOR, ancora=ANCORA_INJECT)
