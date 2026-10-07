# -*- coding: utf-8 -*-
"""
Consumo do almoxarifado unico (D1 / Ticket 15 — falhas V3 e V11).

O aidd-pure nao guarda copia de peca do almoxarifado. O injetor, a CLI
`aidd_inject` e o gate `G_INJECT` sao PECA de `aidd-enterprise` e vivem em
`componentes/compartilhado/injetor/variantes/aidd-pure/`. Este modulo resolve o
caminho delas via `aidd_forge.core.almoxarifado.caminho_peca` e as importa nos
nomes canonicos que o codigo e as suites ja usam.

A peca e relocavel: as ancoras de caminho calculadas a partir de `__file__`
(`_ROOT`, `_PHASES_DIR`, `_default_ecossistema_root`) apontam para a posicao da
peca no almoxarifado, que nao e a posicao do consumidor. Por isso
`reancorar_modulo` devolve para o aidd-pure — a semantica original e preservada
(rh para `<raiz do ecossistema>`, `scripts/phases` para as fases), apenas
resolvida a partir de quem consome, nao de onde a peca esta guardada.
"""

import sys
import types
from pathlib import Path

# =============================================================================
# RAIZES
# =============================================================================

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PURE_DIR = SCRIPTS_DIR.parent
PHASES_DIR = SCRIPTS_DIR / 'phases'


def _descobrir_raiz_ecossistema(inicio: Path) -> Path:
    """Sobe a arvore ate achar o marcador `ecossistema.py` (raiz do monorepo)."""
    for candidato in (inicio, *inicio.parents):
        if (candidato / 'ecossistema.py').is_file():
            return candidato
    raise RuntimeError(
        f"raiz do ecossistema nao encontrada a partir de {inicio}: "
        "esperado um ancestral com ecossistema.py"
    )


RAIZ_ECOSSISTEMA = _descobrir_raiz_ecossistema(SCRIPTS_DIR)
FORGE_VSA = RAIZ_ECOSSISTEMA / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge"
FORGE_DIR = FORGE_VSA if FORGE_VSA.is_dir() else (RAIZ_ECOSSISTEMA / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge")

for _p in (str(SCRIPTS_DIR), str(PHASES_DIR), str(FORGE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aidd_forge.core.almoxarifado import caminho_peca  # noqa: E402

# =============================================================================
# PECAS DO INJETOR
# =============================================================================

PECA_INJETOR = 'injetor/variantes/aidd-pure'
PKG_INJETOR = 'scripts.core.injector'

# Ordem importa: as folhas entram antes dos modulos que as importam, porque a
# peca usa imports absolutos `from scripts.core.injector.<modulo> import ...`.
MODULOS_INJETOR = (
    'contrato',
    'detector_camada',
    'materializador',
    'profiles_registry',
    'scaffolds',
    'sincronizador_harness',
    'injetor',
)


def caminho_peca_do_injetor(nome: str) -> Path:
    """Resolve `injetor/variantes/aidd-pure/<nome>` no almoxarifado."""
    return caminho_peca(f'{PECA_INJETOR}/{nome}', raiz=RAIZ_ECOSSISTEMA)


def caminho_modulo_injetor(modulo: str) -> Path:
    """Caminho da peca `core/injector/<modulo>.py`."""
    return caminho_peca_do_injetor(f'core/injector/{modulo}.py')


def caminho_cli_injetor() -> Path:
    """Caminho da peca da CLI `aidd_inject`."""
    return caminho_peca_do_injetor('aidd_inject.py')


# Gates de projeto que o aidd-pure roda e que são peça do almoxarifado (Bloco 4: as
# cópias em scripts/gates/ saíram). G_HARNESS_COMPAT tem variante própria do aidd-pure.
PECA_POR_GATE = {
    'G_BLOQUEAR_SEGREDOS': 'gates/G_BLOQUEAR_SEGREDOS.py',
    'G_CYBERSECURITY_OWASP': 'gates/G_CYBERSECURITY_OWASP.py',
    'G_HARNESS_COMPAT': 'gates/variantes/aidd-pure/G_HARNESS_COMPAT.py',
}


def caminho_gate_catalogo(nome: str) -> Path:
    """Caminho de um gate de projeto no almoxarifado (`PECA_POR_GATE`)."""
    return caminho_peca(PECA_POR_GATE[nome], raiz=RAIZ_ECOSSISTEMA)


def caminho_gate_injetor() -> Path:
    """Caminho da peca do gate `G_INJECT`."""
    return caminho_peca_do_injetor('G_INJECT.py')


# =============================================================================
# CARREGAMENTO
# =============================================================================

def _executar(caminho: Path, nome_modulo: str) -> types.ModuleType:
    """Executa a peca como modulo e a registra em `sys.modules[nome_modulo]`."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(nome_modulo, caminho)
    if spec is None or spec.loader is None:
        raise ImportError(f'peça ilegível: {caminho}')
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome_modulo] = modulo
    try:
        spec.loader.exec_module(modulo)
    except BaseException:
        sys.modules.pop(nome_modulo, None)
        raise
    return modulo


def reancorar_modulo(modulo: types.ModuleType) -> None:
    """Devolve as ancoras `__file__` da peca para o consumidor (aidd-pure)."""
    if hasattr(modulo, '_default_ecossistema_root'):
        modulo._default_ecossistema_root = lambda: RAIZ_ECOSSISTEMA
    if hasattr(modulo, '_PHASES_DIR'):
        modulo._PHASES_DIR = PHASES_DIR
    if hasattr(modulo, '_ROOT'):
        modulo._ROOT = PURE_DIR


def registrar_injetor() -> types.ModuleType:
    """Registra `scripts.core.injector.*` a partir da peca do almoxarifado.

    Idempotente. Retorna o modulo de pacote do injetor.
    """
    import scripts.core as core

    caminho_init = caminho_modulo_injetor('__init__')
    if caminho_init.parent.name != 'injector':
        raise RuntimeError(f'peça fora do almoxarifado: {caminho_init}')

    pacote = sys.modules.get(PKG_INJETOR)
    if pacote is None or Path(getattr(pacote, '__file__', '')).resolve() != caminho_init.resolve():
        pacote = types.ModuleType(PKG_INJETOR)
        pacote.__file__ = str(caminho_init)
        pacote.__path__ = [str(caminho_init.parent)]
        pacote.__package__ = PKG_INJETOR
        sys.modules[PKG_INJETOR] = pacote
        setattr(core, 'injector', pacote)

    for nome in MODULOS_INJETOR:
        caminho = caminho_modulo_injetor(nome)
        nome_modulo = f'{PKG_INJETOR}.{nome}'
        modulo = sys.modules.get(nome_modulo)
        if modulo is None or Path(getattr(modulo, '__file__', '')).resolve() != caminho.resolve():
            modulo = _executar(caminho, nome_modulo)
            reancorar_modulo(modulo)
        setattr(pacote, nome, modulo)

    codigo = compile(
        caminho_init.read_text(encoding='utf-8'), str(caminho_init), 'exec'
    )
    exec(codigo, pacote.__dict__)
    return pacote


def registrar_cli_injetor() -> types.ModuleType:
    """Registra a CLI da peca como `aidd_inject` (idempotente)."""
    caminho = caminho_cli_injetor()
    modulo = sys.modules.get('aidd_inject')
    if modulo is None or Path(getattr(modulo, '__file__', '')).resolve() != caminho.resolve():
        modulo = _executar(caminho, 'aidd_inject')
        reancorar_modulo(modulo)
    return modulo


def registrar_gate_injetor() -> types.ModuleType:
    """Registra o gate da peca como `G_INJECT` (idempotente)."""
    caminho = caminho_gate_injetor()
    modulo = sys.modules.get('G_INJECT')
    if modulo is None or Path(getattr(modulo, '__file__', '')).resolve() != caminho.resolve():
        modulo = _executar(caminho, 'G_INJECT')
        reancorar_modulo(modulo)
    return modulo


def modulos_do_injetor() -> dict:
    """Mapa nome canonico -> modulo, para inspecao/diagnostico."""
    registrar_injetor()
    return {
        nome: sys.modules[f'{PKG_INJETOR}.{nome}']
        for nome in MODULOS_INJETOR
        if f'{PKG_INJETOR}.{nome}' in sys.modules
    }