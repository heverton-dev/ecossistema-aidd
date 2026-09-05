"""Fixtures compartilhadas da suite de testes do aidd-forge.

Ver achado do Prompt Corretivo 3 (Pacote 7): `resolve_canonical_destination()`/
`sincronizar_componente()` (em `aidd_forge.core.injector_profiles`) resolvem a
raiz do monorepo ecossistema-aidd via `_default_ecossistema_root()` quando
nenhum `ecossistema_root` explicito e passado. Sem isolamento, qualquer teste
que exercite `Materializador`/`UniversalInjector` (mesmo usando `tmp_path`
para o "projeto alvo") grava de verdade em `componentes/aidd-forge/...` deste
repositorio, poluindo a arvore real a cada execucao da suite.
"""

import pytest

from aidd_forge.core import injector_profiles


@pytest.fixture(autouse=True)
def isola_raiz_canonica_do_ecossistema(request, tmp_path, monkeypatch):
    """Isola por padrao a raiz canonica resolvida para dentro de `tmp_path`.

    Testes que precisam verificar a resolucao REAL da raiz (prova de que o
    calculo de `.parents[]` aponta para o monorepo de verdade) devem marcar
    `@pytest.mark.raiz_real` para pular este isolamento.
    """
    if request.node.get_closest_marker("raiz_real"):
        return

    raiz_fake = tmp_path / "_ecossistema_fake_root"
    monkeypatch.setattr(injector_profiles, "_default_ecossistema_root", lambda: raiz_fake)
