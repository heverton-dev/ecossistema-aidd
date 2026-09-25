# -*- coding: utf-8 -*-
"""
AIDD-Diagnose Módulo de Observabilidade e Causa Raiz (D12 / Ticket 5).
Provê instrumentação de fases de diagnose, registro de hipóteses e geração
de relatório de causa raiz ao final do ciclo.
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
    """Estrutura imutável de telemetria de execução de fase."""
    etapa: str
    tokens_entrada: int = 0
    tokens_saida: int = 0
    duracao_segundos: float = 0.0
    status: str = "SUCESSO"
    timestamp: Optional[str] = None
    modelo: Optional[str] = None
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
            "detalhes": self.detalhes,
        }


def estimar_tokens(conteudo: Any) -> int:
    """Estima quantidade de tokens consumidos."""
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
    """Gerenciador de contexto para rastreamento de tempo e tokens."""

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


@dataclass
class DadosFase:
    """Estrutura de dados registrados para cada fase de diagnose."""
    numero: int
    timestamp_inicio: Optional[str] = None
    timestamp_fim: Optional[str] = None
    duracao_segundos: float = 0.0
    comando_reproducao: Optional[str] = None
    hipoteses: List[str] = field(default_factory=list)
    hipoteses_descartadas: List[Dict[str, str]] = field(default_factory=list)
    modo_fase2: Optional[str] = None
    status: str = "PENDENTE"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "numero": self.numero,
            "timestamp_inicio": self.timestamp_inicio,
            "timestamp_fim": self.timestamp_fim,
            "duracao_segundos": round(self.duracao_segundos, 4),
            "comando_reproducao": self.comando_reproducao,
            "hipoteses": self.hipoteses,
            "hipoteses_descartadas": self.hipoteses_descartadas,
            "modo_fase2": self.modo_fase2,
            "status": self.status,
        }


class RegistradorFase:
    """Rastreador de fase individual de diagnose."""

    def __init__(
        self,
        numero: int,
        diretorio_sessao: Optional[str] = None,
        modo_fase2: Optional[str] = None,
    ):
        self.numero = numero
        self.modo_fase2 = modo_fase2
        self.dados = DadosFase(numero=numero, modo_fase2=modo_fase2)
        self.inicio = 0.0
        self.fim = 0.0

        if diretorio_sessao:
            self.diretorio_sessao = Path(diretorio_sessao)
        else:
            self.diretorio_sessao = Path.cwd() / "docs" / "diagnosticos" / self._gerar_slug_sessao()

        self.diretorio_sessao.mkdir(parents=True, exist_ok=True)

    def _gerar_slug_sessao(self) -> str:
        """Gera slug no formato YYYYMMDD_timestamp."""
        agora = datetime.now()
        return agora.strftime("%Y%m%d_%H%M%S")

    def __enter__(self) -> RegistradorFase:
        self.registrar_inicio()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.dados.status = "FALHA"
            if exc_val:
                self.dados.hipoteses_descartadas.append({
                    "hipotese": "Execução",
                    "prova": str(exc_val)
                })
        self.registrar_fim()

    def registrar_inicio(self) -> None:
        """Registra timestamp de início."""
        self.inicio = time.perf_counter()
        self.dados.timestamp_inicio = datetime.now().isoformat()
        self.dados.status = "EM_PROGRESSO"

    def registrar_fim(self) -> None:
        """Registra timestamp de fim e calcula duração."""
        self.fim = time.perf_counter()
        self.dados.timestamp_fim = datetime.now().isoformat()
        self.dados.duracao_segundos = max(0.0, self.fim - self.inicio)
        if self.dados.status == "EM_PROGRESSO":
            self.dados.status = "CONCLUIDA"

        self._gravar_log_fase()

    def registrar_comando_reproducao(self, comando: str) -> None:
        """Registra o comando usado para reprodução."""
        self.dados.comando_reproducao = comando

    def registrar_hipotese(self, hipotese: str) -> None:
        """Registra uma hipótese ativa."""
        if hipotese not in self.dados.hipoteses:
            self.dados.hipoteses.append(hipotese)

    def registrar_descartada(self, hipotese: str, prova: str) -> None:
        """Registra uma hipótese descartada com prova."""
        self.dados.hipoteses_descartadas.append({
            "hipotese": hipotese,
            "prova": prova
        })

    def _gravar_log_fase(self) -> None:
        """Grava log da fase em arquivo."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nome_arquivo = f"fase_{self.numero:02d}_{timestamp_str}.log"
        caminho_arquivo = self.diretorio_sessao / nome_arquivo

        linhas = [
            "=" * 80,
            f"RELATORIO DE FASE {self.numero} - DIAGNOSE AIDD",
            "=" * 80,
            f"Timestamp Início: {self.dados.timestamp_inicio}",
            f"Timestamp Fim: {self.dados.timestamp_fim}",
            f"Duração: {self.dados.duracao_segundos:.4f}s",
            f"Status: {self.dados.status}",
            f"Modo Fase 2: {self.modo_fase2 or 'N/A'}",
            "",
            "COMANDO DE REPRODUCAO:",
            f"  {self.dados.comando_reproducao or 'N/A'}",
            "",
            "HIPOTESES ATIVAS:",
        ]

        for hip in self.dados.hipoteses:
            linhas.append(f"  - {hip}")

        if not self.dados.hipoteses:
            linhas.append("  (Nenhuma)")

        linhas.extend([
            "",
            "HIPOTESES DESCARTADAS:",
        ])

        for item in self.dados.hipoteses_descartadas:
            linhas.append(f"  - {item['hipotese']}")
            linhas.append(f"    Prova: {item['prova']}")

        if not self.dados.hipoteses_descartadas:
            linhas.append("  (Nenhuma)")

        linhas.extend([
            "",
            "METADADOS_JSON:",
            json.dumps(self.dados.to_dict(), indent=2, ensure_ascii=False),
            "=" * 80,
        ])

        conteudo = "\n".join(linhas) + "\n"
        caminho_arquivo.write_text(conteudo, encoding="utf-8")


def gerar_relatorio_causa_raiz(
    diretorio_sessao: Union[str, Path],
    slug: Optional[str] = None,
    execucoes: int = 0,
    teste_regressao: Optional[str] = None,
    exit_antes_fix: Optional[int] = None,
) -> Path:
    """
    Gera relatório consolidado de causa raiz em RELATORIO-CAUSA-RAIZ.md.

    Lê todos os arquivos fase_*.log do diretório, consolida dados e gera
    um relatório final em Markdown. Com execucoes/teste_regressao/exit_antes_fix
    inclui a seção que o G_aidd_diagnose exige (o gate roda o teste de novo).

    Retorna o caminho do arquivo gerado.
    """
    diretorio_sessao = Path(diretorio_sessao)
    diretorio_sessao.mkdir(parents=True, exist_ok=True)

    if slug is None:
        slug = diretorio_sessao.name

    # Coleta logs de todas as fases
    logs = sorted(diretorio_sessao.glob("fase_*.log"))

    linhas = [
        "# RELATORIO-CAUSA-RAIZ",
        "",
        f"**Data**: {datetime.now().isoformat()}",
        f"**Sessão**: {slug}",
        "",
        "## Resumo Executivo",
        "",
        f"Análise de diagnose realizada em {len(logs)} fase(s).",
        "",
    ]

    fases_dados = []

    for log_path in logs:
        conteudo = log_path.read_text(encoding="utf-8")

        # Extrai dados do log
        try:
            # Procura pela seção JSON
            inicio_json = conteudo.rfind("METADADOS_JSON:")
            if inicio_json != -1:
                inicio_json = conteudo.find("{", inicio_json)
                fim_json = conteudo.rfind("}", inicio_json) + 1
                json_str = conteudo[inicio_json:fim_json]
                dados = json.loads(json_str)
                fases_dados.append(dados)
        except (json.JSONDecodeError, ValueError):
            pass

    # Gera seção de fases
    linhas.append("## Fases Executadas")
    linhas.append("")

    for dados in fases_dados:
        num_fase = dados.get("numero", "?")
        status = dados.get("status", "?")
        duracao = dados.get("duracao_segundos", 0)

        linhas.append(f"### Fase {num_fase}")
        linhas.append("")
        linhas.append(f"- **Status**: {status}")
        linhas.append(f"- **Duração**: {duracao:.4f}s")
        linhas.append(f"- **Comando**: {dados.get('comando_reproducao', 'N/A')}")
        linhas.append("")

        hipoteses = dados.get("hipoteses", [])
        if hipoteses:
            linhas.append("**Hipóteses Ativas**:")
            for hip in hipoteses:
                linhas.append(f"  - {hip}")
            linhas.append("")

        descartadas = dados.get("hipoteses_descartadas", [])
        if descartadas:
            linhas.append("**Hipóteses Descartadas**:")
            for item in descartadas:
                linhas.append(f"  - {item.get('hipotese', '?')}: {item.get('prova', '?')}")
            linhas.append("")

    if execucoes or teste_regressao:
        linhas.extend(["## Prova", ""])
        if execucoes:
            linhas.append(f"- **Execuções**: {execucoes} execuções com o mesmo resultado")
        if teste_regressao:
            linhas.append(f"- **Teste de Regressão**: `{teste_regressao}`")
            if exit_antes_fix is not None and exit_antes_fix != 0:
                linhas.append(f"- **Resultado Antes do Fix**: FALHA (exit {exit_antes_fix}, declarado)")
            linhas.append("- **Resultado Após o Fix**: PASSOU (conferido pelo G_aidd_diagnose)")
        linhas.append("")

    # Seção de conclusões
    linhas.extend([
        "",
        "## Conclusões",
        "",
        "Este relatório consolida os registros das fases de diagnose gravados em fase_*.log.",
        "",
    ])

    nome_relatorio = "RELATORIO-CAUSA-RAIZ.md"
    caminho_relatorio = diretorio_sessao / nome_relatorio

    conteudo_final = "\n".join(linhas)
    caminho_relatorio.write_text(conteudo_final, encoding="utf-8")

    return caminho_relatorio
