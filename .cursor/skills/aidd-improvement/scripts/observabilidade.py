# -*- coding: utf-8 -*-
"""
AIDD-Melhoria Módulo de Observabilidade e Frugalidade (D12 / Ticket 5).
Provê instrumentação de orçamentos de tokens (estimados/reais), medição de latência,
geração de logs padronizados em 'secoes/' e telemetria transparente via CLI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Optional, Union


def sanitizar_nome_arquivo(nome: str) -> str:
    """Remove caracteres ilegais para nomes de arquivo em Windows/POSIX."""
    return re.sub(r'[\\/*?:"<>| ]', '_', nome)


@dataclass
class MetricasExecucao:
    """
    Estrutura imutável de telemetria e consumo de recursos.
    """
    etapa: str
    tokens_entrada: int = 0
    tokens_saida: int = 0
    duracao_segundos: float = 0.0
    status: str = "SUCESSO"
    timestamp: Optional[str] = None
    modelo: Optional[str] = None
    custo_estimado: float = 0.0
    detalhes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.detalhes is None:
            self.detalhes = {}

    @property
    def tokens_total(self) -> int:
        """Soma total de tokens consumidos (entrada + saída)."""
        return self.tokens_entrada + self.tokens_saida

    def to_dict(self) -> Dict[str, Any]:
        """Converte métricas em dicionário serializável."""
        return {
            "timestamp": self.timestamp,
            "etapa": self.etapa,
            "status": self.status,
            "duracao_segundos": round(self.duracao_segundos, 4),
            "tokens_entrada": self.tokens_entrada,
            "tokens_saida": self.tokens_saida,
            "tokens_total": self.tokens_total,
            "modelo": self.modelo or "heuristica-local",
            "custo_estimado": round(self.custo_estimado, 6),
            "detalhes": self.detalhes,
        }

    def formatar_relatorio(self) -> str:
        """Gera formatação textual padronizada para registro em arquivo de log."""
        linhas = [
            "=" * 80,
            "RELATORIO DE OBSERVABILIDADE E FRUGALIDADE - AIDD",
            "=" * 80,
            f"timestamp: {self.timestamp}",
            f"etapa: {self.etapa}",
            f"status: {self.status}",
            f"duracao_segundos: {self.duracao_segundos:.4f}",
            f"tokens_entrada: {self.tokens_entrada}",
            f"tokens_saida: {self.tokens_saida}",
            f"tokens_total: {self.tokens_total}",
            f"modelo: {self.modelo or 'heuristica-local'}",
            f"custo_estimado: {self.custo_estimado:.6f}",
            "=" * 80,
            "METADADOS_JSON:",
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            "=" * 80,
        ]
        return "\n".join(linhas) + "\n"


def estimar_tokens(conteudo: Any) -> int:
    """
    Estima quantidade de tokens consumidos com base no volume de texto.
    Heurística determinística: ~4 caracteres por token em média (OpenAI/Anthropic/Gemini standard).
    """
    if conteudo is None:
        return 0

    if isinstance(conteudo, str):
        texto = conteudo.strip()
    elif isinstance(conteudo, (dict, list)):
        texto = json.dumps(conteudo, ensure_ascii=False)
    else:
        texto = str(conteudo).strip()

    if not texto:
        return 0

    return max(1, len(texto) // 4)


class RastreadorExecucao:
    """
    Gerenciador de contexto para rastreamento transparente de tempo e tokens.
    """
    def __init__(self, etapa: str, modelo: Optional[str] = None):
        self.etapa = etapa
        self.modelo = modelo
        self.tokens_entrada = 0
        self.tokens_saida = 0
        self.status = "SUCESSO"
        self.inicio = 0.0
        self.fim = 0.0
        self.detalhes: Dict[str, Any] = {}
        self.metricas: Optional[MetricasExecucao] = None

    def __enter__(self) -> RastreadorExecucao:
        self.inicio = time.perf_counter()
        return self

    def registrar_entrada(self, conteudo: Any) -> int:
        tokens = estimar_tokens(conteudo)
        self.tokens_entrada += tokens
        return tokens

    def registrar_saida(self, conteudo: Any) -> int:
        tokens = estimar_tokens(conteudo)
        self.tokens_saida += tokens
        return tokens

    def definir_status(self, status: str) -> None:
        self.status = status

    def finalizar(self, status: Optional[str] = None) -> MetricasExecucao:
        self.fim = time.perf_counter()
        if status:
            self.status = status
        duracao = max(0.0, self.fim - self.inicio)
        self.metricas = MetricasExecucao(
            etapa=self.etapa,
            tokens_entrada=self.tokens_entrada,
            tokens_saida=self.tokens_saida,
            duracao_segundos=duracao,
            status=self.status,
            modelo=self.modelo,
            detalhes=self.detalhes,
        )
        return self.metricas

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.status = "FALHA"
            self.detalhes["erro"] = str(exc_val)
        self.finalizar()


def registrar_observabilidade(
    metricas: MetricasExecucao,
    log_dir: Optional[Union[str, Path]] = None,
    prefixo: str = "observabilidade",
    exibir_console: bool = True,
) -> Path:
    """
    Grava o log padronizado de observabilidade e frugalidade no diretório de seções
    e opcionalmente expõe as métricas no console.

    Retorna o Path absoluto do arquivo gerado.
    """
    if log_dir is None:
        # Tenta localizar a pasta secoes do repositório
        raiz = Path(__file__).resolve().parents[4]
        destino_dir = raiz / "secoes"
    else:
        destino_dir = Path(log_dir).resolve()

    destino_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    etapa_sanitizada = sanitizar_nome_arquivo(metricas.etapa)
    nome_arquivo = f"{prefixo}_{etapa_sanitizada}_{timestamp_str}.log"
    caminho_arquivo = destino_dir / nome_arquivo

    conteudo = metricas.formatar_relatorio()
    caminho_arquivo.write_text(conteudo, encoding="utf-8")

    if exibir_console:
        print(
            f"[OBSERVABILIDADE] Etapa: {metricas.etapa} | Status: {metricas.status} | "
            f"Duração: {metricas.duracao_segundos:.2f}s | "
            f"Tokens: [In={metricas.tokens_entrada}, Out={metricas.tokens_saida}, Total={metricas.tokens_total}]"
        )

    return caminho_arquivo
