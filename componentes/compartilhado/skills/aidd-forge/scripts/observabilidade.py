# -*- coding: utf-8 -*-
"""
Observabilidade e telemetria frugal de aidd-forge (D12 / DoD 5).

Cada execucao instrumentada DEVE emitir metricas estruturadas (duracao e
artefatos injetados); nao emitir gera MetricaAusenteError. O log JSON estrito
e gravado em secoes/ (JSONL) ou no stdout.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

_ARQUIVO_TELEMETRIA = "FORGE-TELEMETRIA.jsonl"
_STATUS_VALIDOS = ("sucesso", "falha")
_CAMPOS_METRICA = ("operacao", "duracao_s", "artefatos", "status")

PathLike = Union[str, Path]


class MetricaAusenteError(RuntimeError):
    """Execucao concluida sem emitir metricas estruturadas de execucao."""


class MetricaInvalidaError(ValueError):
    """Metrica fora do schema estrito de telemetria frugal."""


def validar_metrica(metrica: Any) -> Dict[str, Any]:
    """Valida a metrica contra o schema estrito (campos exatos, tipos corretos)."""
    if not isinstance(metrica, dict):
        raise MetricaInvalidaError("metrica deve ser objeto JSON")
    if set(metrica.keys()) != set(_CAMPOS_METRICA):
        raise MetricaInvalidaError(
            f"campos da metrica devem ser exatamente {sorted(_CAMPOS_METRICA)}"
        )

    operacao = metrica["operacao"]
    if not isinstance(operacao, str) or not operacao.strip():
        raise MetricaInvalidaError("'operacao' deve ser string nao vazia")

    duracao = metrica["duracao_s"]
    if isinstance(duracao, bool) or not isinstance(duracao, (int, float)):
        raise MetricaInvalidaError("'duracao_s' deve ser numerica")
    if duracao < 0:
        raise MetricaInvalidaError("'duracao_s' deve ser >= 0")

    artefatos = metrica["artefatos"]
    if not isinstance(artefatos, list) or any(not isinstance(a, str) for a in artefatos):
        raise MetricaInvalidaError("'artefatos' deve ser lista de strings")

    status = metrica["status"]
    if status not in _STATUS_VALIDOS:
        raise MetricaInvalidaError(f"'status' deve ser um de {_STATUS_VALIDOS}")

    return {
        "operacao": operacao,
        "duracao_s": float(duracao),
        "artefatos": list(artefatos),
        "status": status,
    }


class Execucao:
    """Instrumentacao de uma execucao: artefatos, duracao e emissao da metrica."""

    def __init__(
        self,
        operacao: str,
        destino_secoes: Optional[PathLike] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.operacao = operacao
        self.destino_secoes = Path(destino_secoes) if destino_secoes is not None else None
        self._clock = clock
        self._inicio = clock()
        self._artefatos: List[str] = []
        self._emitido = False
        self.metrica: Optional[Dict[str, Any]] = None

    def registrar_artefato(self, caminho: str) -> None:
        if not isinstance(caminho, str) or not caminho.strip():
            raise MetricaInvalidaError("artefato deve ser string nao vazia")
        self._artefatos.append(caminho)

    def emitir(self, status: str = "sucesso") -> Dict[str, Any]:
        """Valida, persiste (secoes/ JSONL ou stdout) e marca a metrica como emitida."""
        metrica = validar_metrica(
            {
                "operacao": self.operacao,
                "duracao_s": max(0.0, self._clock() - self._inicio),
                "artefatos": list(self._artefatos),
                "status": status,
            }
        )
        linha = json.dumps(metrica, sort_keys=True, ensure_ascii=False)
        if self.destino_secoes is None:
            print(linha)
        else:
            self.destino_secoes.mkdir(parents=True, exist_ok=True)
            arquivo = self.destino_secoes / _ARQUIVO_TELEMETRIA
            with arquivo.open("a", encoding="utf-8") as fh:
                fh.write(linha + "\n")
        self.metrica = metrica
        self._emitido = True
        return metrica

    def __enter__(self) -> "Execucao":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            return False
        if not self._emitido:
            raise MetricaAusenteError(
                f"execucao '{self.operacao}' concluiu sem emitir metricas estruturadas"
            )
        return False


def execucao(
    operacao: str,
    destino_secoes: Optional[PathLike] = None,
    clock: Callable[[], float] = time.monotonic,
) -> Execucao:
    """Context manager de execucao observavel; exige emitir() antes do fim."""
    return Execucao(operacao, destino_secoes=destino_secoes, clock=clock)


if __name__ == "__main__":
    print(
        "Uso: importe o modulo e use `with execucao(<operacao>, destino_secoes=...): ...`",
        file=sys.stderr,
    )
    sys.exit(1)
