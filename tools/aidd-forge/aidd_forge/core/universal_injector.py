"""Orquestrador do Injetor Universal de Componentes.

Compoe, na ordem: validacao de contrato -> deteccao de camada AIDD ->
materializacao transacional com rollback -> (se `skill`) sincronizacao
multi-harness. Erros de validacao ou de camada nunca tocam disco; erros de
materializacao ja vem com rollback aplicado pelo proprio `Materializador`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aidd_forge.core.camada_detector import detectar_camada
from aidd_forge.core.harness_sync import HarnessSyncResult, sincronizar_skill
from aidd_forge.core.injection_schema import validate_request
from aidd_forge.core.materializador import InjectionRequest, MaterializationResult, Materializador

TIPOS_COM_HARNESS_SYNC: frozenset[str] = frozenset({"skill"})


@dataclass
class UniversalInjectionResult:
    """Resultado final de uma injecao universal (sucesso ou falha)."""

    errors: list[str] = field(default_factory=list)
    materialization: MaterializationResult | None = None
    harness_sync: HarnessSyncResult | None = None
    camada: int | None = None

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
        except Exception as exc:
            return UniversalInjectionResult(errors=[str(exc)], camada=camada)

        harness_result = None
        if tipo in TIPOS_COM_HARNESS_SYNC:
            harness_result = sincronizar_skill(nome, self.target_root, force=force)

        return UniversalInjectionResult(
            materialization=materialization, harness_sync=harness_result, camada=camada
        )
