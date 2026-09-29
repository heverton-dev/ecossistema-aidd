# -*- coding: utf-8 -*-
"""
Observabilidade e telemetria de auditoria de aidd-enterprise (D12).

Cada execucao instrumentada DEVE emitir metricas estruturadas (inicio, fim,
duracao, contagem de componentes, bytes transferidos e hashes SHA-256
verificados); nao emitir gera MetricaAusenteError (exit 1). O log JSONL estrito
e persistido em secoes/ (Lei #3: persistencia em arquivo).
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

_ARQUIVO_TELEMETRIA = "ENTERPRISE-TELEMETRIA.jsonl"
_STATUS_VALIDOS = ("sucesso", "falha")
_CAMPOS_METRICA = (
    "operacao",
    "inicio_s",
    "fim_s",
    "duracao_s",
    "componentes",
    "bytes_transferidos",
    "hashes_verificados",
    "status",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PathLike = Union[str, Path]


class MetricaAusenteError(RuntimeError):
    """Execucao concluida sem emitir metricas estruturadas de execucao."""


class MetricaInvalidaError(ValueError):
    """Metrica fora do schema estrito de telemetria de auditoria."""


def encontrar_raiz_repositorio() -> Optional[Path]:
    """Localiza a raiz do repositorio procurando por ecossistema.py."""
    atual = Path(__file__).resolve()
    for candidato in [atual, *atual.parents]:
        if (candidato / "ecossistema.py").is_file():
            return candidato
    return None


def destino_padrao_secoes() -> Path:
    """Diretorio secoes/ do repositorio (destino canonico do log de auditoria)."""
    raiz = encontrar_raiz_repositorio()
    if raiz is None:
        raise FileNotFoundError("raiz do repositorio nao encontrada (ecossistema.py ausente)")
    return raiz / "secoes"


def _numerico_nao_negativo(valor: Any, campo: str, inteiro: bool = False) -> None:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise MetricaInvalidaError(f"'{campo}' deve ser numerica")
    if valor < 0:
        raise MetricaInvalidaError(f"'{campo}' deve ser >= 0")
    if inteiro and not isinstance(valor, int):
        raise MetricaInvalidaError(f"'{campo}' deve ser inteiro")


def validar_metrica(metrica: Any) -> Dict[str, Any]:
    """Valida a metrica contra o schema estrito (campos exatos, tipos corretos)."""
    if not isinstance(metrica, dict):
        raise MetricaInvalidaError("metrica deve ser objeto JSON")
    if set(metrica.keys()) != set(_CAMPOS_METRICA):
        raise MetricaInvalidaError(f"campos da metrica devem ser exatamente {sorted(_CAMPOS_METRICA)}")

    operacao = metrica["operacao"]
    if not isinstance(operacao, str) or not operacao.strip():
        raise MetricaInvalidaError("'operacao' deve ser string nao vazia")

    _numerico_nao_negativo(metrica["inicio_s"], "inicio_s")
    _numerico_nao_negativo(metrica["fim_s"], "fim_s")
    _numerico_nao_negativo(metrica["duracao_s"], "duracao_s")
    _numerico_nao_negativo(metrica["componentes"], "componentes", inteiro=True)
    _numerico_nao_negativo(metrica["bytes_transferidos"], "bytes_transferidos", inteiro=True)

    hashes = metrica["hashes_verificados"]
    if not isinstance(hashes, list):
        raise MetricaInvalidaError("'hashes_verificados' deve ser lista de SHA-256 hex")
    for item in hashes:
        if not isinstance(item, str) or not _SHA256_RE.match(item):
            raise MetricaInvalidaError(f"hash invalido (esperado SHA-256 hex): {item!r}")

    status = metrica["status"]
    if status not in _STATUS_VALIDOS:
        raise MetricaInvalidaError(f"status deve ser um de {_STATUS_VALIDOS}")

    return {
        "operacao": operacao,
        "inicio_s": float(metrica["inicio_s"]),
        "fim_s": float(metrica["fim_s"]),
        "duracao_s": float(metrica["duracao_s"]),
        "componentes": int(metrica["componentes"]),
        "bytes_transferidos": int(metrica["bytes_transferidos"]),
        "hashes_verificados": list(hashes),
        "status": status,
    }


class Execucao:
    """Instrumentacao de uma execucao: metricas de injecao e emissao auditavel."""

    def __init__(
        self,
        operacao: str,
        destino_secoes: Optional[PathLike] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.operacao = operacao
        self.destino_secoes = Path(destino_secoes) if destino_secoes is not None else destino_padrao_secoes()
        self._clock = clock
        self._inicio = clock()
        self._componentes: List[str] = []
        self._bytes = 0
        self._hashes: List[str] = []
        self._emitido = False
        self.metrica: Optional[Dict[str, Any]] = None

    def registrar_componente(self, nome: str) -> None:
        if not isinstance(nome, str) or not nome.strip():
            raise MetricaInvalidaError("componente deve ser string nao vazia")
        self._componentes.append(nome)

    def registrar_bytes(self, total: int) -> None:
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise MetricaInvalidaError("bytes_transferidos deve ser inteiro >= 0")
        self._bytes += total

    def registrar_hash(self, sha256: str) -> None:
        if not isinstance(sha256, str) or not _SHA256_RE.match(sha256):
            raise MetricaInvalidaError(f"hash invalido (esperado SHA-256 hex): {sha256!r}")
        self._hashes.append(sha256)

    def emitir(self, status: str = "sucesso") -> Dict[str, Any]:
        """Valida, persiste (secoes/ JSONL) e marca a metrica como emitida."""
        fim = self._clock()
        metrica = validar_metrica(
            {
                "operacao": self.operacao,
                "inicio_s": self._inicio,
                "fim_s": fim,
                "duracao_s": max(0.0, fim - self._inicio),
                "componentes": len(self._componentes),
                "bytes_transferidos": self._bytes,
                "hashes_verificados": list(self._hashes),
                "status": status,
            }
        )
        linha = json.dumps(metrica, sort_keys=True, ensure_ascii=False)
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
                f"execucao '{self.operacao}' concluiu sem log de telemetria estruturado"
            )
        return False


def execucao(
    operacao: str,
    destino_secoes: Optional[PathLike] = None,
    clock: Callable[[], float] = time.time,
) -> Execucao:
    """Context manager de execucao observavel; exige emitir() antes do fim."""
    return Execucao(operacao, destino_secoes=destino_secoes, clock=clock)


if __name__ == "__main__":
    print(
        "Uso: importe o modulo e use `with execucao(<operacao>, destino_secoes=...): ...`",
        file=sys.stderr,
    )
    sys.exit(1)
