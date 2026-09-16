"""Orquestrador do Injetor Universal de Componentes.

Compoe, na ordem: validacao de contrato -> deteccao de camada AIDD ->
materializacao transacional com rollback -> (se `skill`) sincronizacao
multi-harness. Erros de validacao ou de camada nunca tocam disco; erros de
materializacao ja vem com rollback aplicado pelo proprio `Materializador`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from aidd_forge.core.camada_detector import detectar_camada
from aidd_forge.core.harness_sync import HarnessSyncResult, sincronizar_command, sincronizar_skill
from aidd_forge.core.injection_schema import validate_request
from aidd_forge.core.injector_profiles import sincronizar_componente
from aidd_forge.core.materializador import (
    ConteudoStubError,
    DestinoExistenteError,
    InjectionRequest,
    MaterializacaoError,
    MaterializationResult,
    Materializador,
)

# Cada tipo aqui ganha espelhamento multi-harness dentro do PROJETO ALVO
# (distinto de `sincronizar_componente`, que sincroniza a copia canonica
# dentro do MONOREPO ecossistema-aidd). "command" foi adicionado em
# 2026-09-15: antes disso `forge inject command` so gravava um unico
# arquivo em `.agent/commands/`, invisivel pra qualquer harness real.
HARNESS_SYNCERS: dict[str, Callable[..., HarnessSyncResult]] = {
    "skill": sincronizar_skill,
    "command": sincronizar_command,
}
TIPOS_COM_HARNESS_SYNC: frozenset[str] = frozenset(HARNESS_SYNCERS)


@dataclass
class UniversalInjectionResult:
    """Resultado final de uma injecao universal (sucesso ou falha)."""

    errors: list[str] = field(default_factory=list)
    materialization: MaterializationResult | None = None
    harness_sync: HarnessSyncResult | None = None
    camada: int | None = None
    sync_warning: str | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


class UniversalInjector:
    """Ponto de entrada unico do fluxo de injecao universal de componentes."""

    def __init__(self, target_root: Path):
        self.target_root = Path(target_root)

    def injetar(self, payload: dict[str, Any], force: bool = False) -> UniversalInjectionResult:
        schema_result = validate_request(payload)
        if not schema_result.valid:
            return UniversalInjectionResult(errors=schema_result.errors)

        tipo = payload["tipo"]
        nome = payload["nome"]

        try:
            camada = detectar_camada(tipo, payload.get("camada_alvo"))
        except ValueError as exc:
            return UniversalInjectionResult(errors=[str(exc)])

        request = InjectionRequest(
            tipo=tipo, nome=nome, descricao=payload["descricao"], conteudo=payload["conteudo"]
        )

        try:
            materialization = Materializador(self.target_root).materializar(request, force=force)
        except (ConteudoStubError, DestinoExistenteError, MaterializacaoError) as exc:
            return UniversalInjectionResult(errors=[str(exc)], camada=camada)

        sync_code = sincronizar_componente(tipo, ferramenta="aidd-forge")
        sync_warning = materialization.sync_warning
        if sync_code != 0 and not sync_warning:
            sync_warning = f"sincronizacao multi-harness retornou codigo {sync_code}"

        harness_result = None
        syncer = HARNESS_SYNCERS.get(tipo)
        if syncer is not None:
            harness_result = syncer(nome, self.target_root, force=force)

        return UniversalInjectionResult(
            materialization=materialization,
            harness_sync=harness_result,
            camada=camada,
            sync_warning=sync_warning,
        )
