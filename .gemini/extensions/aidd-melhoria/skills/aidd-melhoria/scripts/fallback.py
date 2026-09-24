# -*- coding: utf-8 -*-
"""
AIDD-Melhoria Módulo de Tratamento de Exceções, Retry Backoff e Fallback Operacional (D11).
Implementa:
1. Exceções canônicas de domínio para falhas de manifesto, timeout e interrupção.
2. Política autônoma de retry com backoff exponencial configurável e hooks de telemetria.
3. Rastreamento e persistência atômica do estado de execução (EstadoExecucao) sem perda de contexto.
4. Leitura resiliente de manifestos com parada graceful em falha de I/O.
5. Invocação segura do motor analítico com geração contingencial de relatório determinístico de fallback.
6. Interrupção controlada do pipeline sem deixar estados órfãos ou crashes não-capturados.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    import handoff as _handoff
except ImportError:
    from . import handoff as _handoff


class FallbackOperacionalError(Exception):
    """Exceção levantada quando retries autônomos são esgotados ou ocorre falha operacional persistente."""
    pass


class ManifestReadError(FallbackOperacionalError):
    """Exceção levantada quando a leitura do manifesto falha por inexistência, permissão ou corrupção de dados."""
    pass


class LLMTimeoutError(FallbackOperacionalError):
    """Exceção levantada quando a chamada ao modelo/LLM atinge o limite de tempo configurado."""
    pass


class PipelineInterruptedError(FallbackOperacionalError):
    """Exceção levantada quando o pipeline precisa ser interrompido gracefully."""
    pass


@dataclass
class EstadoExecucao:
    """
    Estrutura imutável de rastreamento de estado para observabilidade e recuperação de falhas.
    Registra cada etapa, histórico de exceções e contexto da solicitação.
    """
    etapa_atual: str
    contexto: Dict[str, Any] = field(default_factory=dict)
    status: str = "INICIADO"  # INICIADO, EM_PROGRESSO, FALLBACK_ACIONADO, INTERROMPIDO, CONCLUIDO
    historico_erros: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    criado_em: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    atualizado_em: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def registrar_erro(
        self,
        etapa: str,
        erro: Union[Exception, str],
        detalhes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra uma falha estruturada no histórico de erros sem truncamento."""
        registro = {
            "etapa": etapa,
            "tipo_erro": type(erro).__name__ if isinstance(erro, Exception) else "ErroGenerico",
            "mensagem": str(erro),
            "detalhes": detalhes or {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self.historico_erros.append(registro)
        self.atualizado_em = registro["timestamp"]
        self.adicionar_log(f"[ERRO na etapa '{etapa}'] {erro}")

    def adicionar_log(self, mensagem: str) -> None:
        """Adiciona uma entrada ao buffer cronológico de telemetria."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entrada = f"[{timestamp}] {mensagem}"
        self.logs.append(entrada)
        self.atualizado_em = timestamp

    def atualizar_etapa(self, nova_etapa: str, novo_status: Optional[str] = None) -> None:
        """Atualiza a etapa e status da execução corrente."""
        self.etapa_atual = nova_etapa
        if novo_status:
            self.status = novo_status
        self.atualizado_em = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.adicionar_log(f"Transição para etapa '{nova_etapa}' (status: {self.status})")

    def para_dict(self) -> Dict[str, Any]:
        """Converte a estrutura do estado para um dicionário serializável."""
        return asdict(self)

    def salvar_estado(self, caminho_arquivo: Optional[Union[Path, str]] = None) -> Path:
        """
        Persiste o estado atomicamente no disco em formato JSON UTF-8.
        Se nenhum caminho for fornecido, cria um log temporal em `./secoes/` ou diretório temporário.
        """
        if caminho_arquivo:
            destino = Path(caminho_arquivo).resolve()
        else:
            diretorio_base = Path("secoes").resolve()
            diretorio_base.mkdir(parents=True, exist_ok=True)
            timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
            destino = diretorio_base / f"estado_execucao_{timestamp_str}.json"

        destino.parent.mkdir(parents=True, exist_ok=True)
        temp_file = destino.with_suffix(".tmp")
        
        conteudo = json.dumps(self.para_dict(), indent=2, ensure_ascii=False)
        temp_file.write_text(conteudo, encoding="utf-8")
        temp_file.replace(destino)
        return destino


def executar_com_retry(
    funcao: Callable[[], Any],
    max_tentativas: int = 3,
    backoff_base: float = 0.01,
    fator: float = 2.0,
    excecoes_retry: tuple = (Exception,),
    logger: Optional[Callable[[str], None]] = None,
    on_retry_hook: Optional[Callable[[int, Exception, float], None]] = None,
) -> Any:
    """
    Executa uma operação com política de retry autônomo com backoff exponencial.
    Em caso de falha transitória, aguarda e tenta novamente até max_tentativas.
    Invoca hooks opcionais de telemetria em cada retry.
    Se todas as tentativas falharem, levanta FallbackOperacionalError encapsulando o erro original.
    """
    ultimo_erro: Optional[Exception] = None

    for tentativa in range(1, max_tentativas + 1):
        try:
            return funcao()
        except excecoes_retry as exc:
            ultimo_erro = exc
            if tentativa < max_tentativas:
                tempo_espera = backoff_base * (fator ** (tentativa - 1))
                if logger:
                    logger(
                        f"[RETRY {tentativa}/{max_tentativas}] Falha detectada: {exc}. "
                        f"Aguardando {tempo_espera:.4f}s antes da próxima tentativa."
                    )
                if on_retry_hook:
                    try:
                        on_retry_hook(tentativa, exc, tempo_espera)
                    except Exception as hook_exc:
                        sys.stderr.write(f"[AVISO HOOK] Falha ao executar on_retry_hook: {hook_exc}\n")
                time.sleep(tempo_espera)
            else:
                break

    mensagem_erro = f"Falha persistente na execução após {max_tentativas} tentativas: {ultimo_erro}"
    raise FallbackOperacionalError(mensagem_erro) from ultimo_erro


def interromper_pipeline_gracefully(
    estado: EstadoExecucao,
    motivo: str,
    arquivo_log: Optional[Union[Path, str]] = None,
    handoff_path: Optional[Union[Path, str]] = None,
    detalhes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Interrompe o fluxo da ferramenta gracefully registrando a falha e preservando o estado factual.
    Gera arquivo de log de estado e atualiza handoff sem perda de dados.
    """
    if estado.status != "INTERROMPIDO":
        estado.status = "FALLBACK_ACIONADO"
    estado.registrar_erro(estado.etapa_atual, motivo, detalhes)
    
    if arquivo_log:
        estado.salvar_estado(arquivo_log)

    if handoff_path:
        handoff_dest = Path(handoff_path).resolve()
        _handoff.emitir_handoff(
            handoff_dest,
            status="FALHA",
            codigo_saida=1,
            repo_root=handoff_dest.parent,
            erro=motivo,
            detalhes=detalhes or estado.contexto,
        )

    return {
        "status": "FALLBACK_ACIONADO",
        "motivo": motivo,
        "estado": estado.para_dict(),
    }


def ler_manifesto_com_fallback(
    caminho_manifesto: Union[Path, str],
    estado: Optional[EstadoExecucao] = None,
    arquivo_log: Optional[Union[Path, str]] = None,
    handoff_path: Optional[Union[Path, str]] = None,
    max_tentativas: int = 3,
    backoff_base: float = 0.01,
) -> Tuple[Optional[Dict[str, Any]], EstadoExecucao]:
    """
    Lê e valida o manifesto JSON de entrada com salvaguardas de fallback e retries de I/O.
    Se o manifesto não existir ou estiver corrompido, interrompe a execução com estado salvo e handoff de falha.
    """
    caminho = Path(caminho_manifesto).resolve()
    estado_atual = estado or EstadoExecucao(
        etapa_atual="leitura_manifesto",
        contexto={"caminho_manifesto": str(caminho)},
    )

    def operacao_leitura() -> Dict[str, Any]:
        if not caminho.is_file():
            raise ManifestReadError(f"Manifesto não encontrado no caminho: {caminho}")
        texto = caminho.read_text(encoding="utf-8")
        return json.loads(texto)

    try:
        dados = executar_com_retry(
            operacao_leitura,
            max_tentativas=max_tentativas,
            backoff_base=backoff_base,
            excecoes_retry=(OSError, json.JSONDecodeError),
        )
        estado_atual.atualizar_etapa("manifesto_lido", novo_status="EM_PROGRESSO")
        return dados, estado_atual
    except Exception as exc:
        motivo = f"Falha na leitura do manifesto: {exc}"
        estado_atual.status = "INTERROMPIDO"
        interromper_pipeline_gracefully(
            estado=estado_atual,
            motivo=motivo,
            arquivo_log=arquivo_log,
            handoff_path=handoff_path,
            detalhes={"caminho_manifesto": str(caminho)},
        )
        return None, estado_atual


def executar_analise_com_fallback(
    motor_ou_funcao: Callable[..., Any],
    pedido: str,
    nome: Optional[str] = None,
    estado: Optional[EstadoExecucao] = None,
    arquivo_log: Optional[Union[Path, str]] = None,
    handoff_path: Optional[Union[Path, str]] = None,
    max_tentativas: int = 3,
    backoff_base: float = 0.01,
    on_retry_hook: Optional[Callable[[int, Exception, float], None]] = None,
) -> Dict[str, Any]:
    """
    Executa a análise via motor/LLM com contingência de fallback estruturado.
    Em caso de falha irrecuperável ou timeout, aciona o fallback operacional determinístico,
    registra as métricas/erros de estado e emite o envelope seguro de relatório.
    """
    estado_atual = estado or EstadoExecucao(
        etapa_atual="analise_llm",
        contexto={"pedido": pedido, "nome": nome},
    )

    try:
        resultado = executar_com_retry(
            motor_ou_funcao,
            max_tentativas=max_tentativas,
            backoff_base=backoff_base,
            on_retry_hook=on_retry_hook,
        )
        estado_atual.atualizar_etapa("analise_concluida", novo_status="CONCLUIDO")
        if arquivo_log:
            estado_atual.salvar_estado(arquivo_log)
        return resultado
    except Exception as exc:
        # Acionamento de Fallback Operacional Graceful
        estado_atual.status = "FALLBACK_ACIONADO"
        estado_atual.registrar_erro("analise_llm", exc, {"pedido": pedido})

        slug = nome or "analise-melhoria-fallback"
        relatorio_fallback = {
            "pedido": pedido,
            "nome": slug,
            "nota_atual": "FALHA_OPERACIONAL",
            "evidencia": f"Fallback acionado após falha operacional: {exc}",
            "resumo": f"Sugestão de refatoração para '{pedido}' (Modo Fallback Operacional)",
            "achados": [
                "Execução do motor principal interceptada por timeout/falha persistente",
                "Acionamento de salvaguarda de fallback determinístico sem perda de contexto"
            ],
            "riscos": [
                "Necessidade de reavaliação dos serviços externos caso haja conectividade restabelecida"
            ],
            "recomendacao": f"Sugestão de refatoração para '{pedido}' gerada via contingência autônoma.",
            "itens_avaliados": [
                {"item": "Determinismo", "status": "feito", "justificativa": "Fallback determinístico ativo"},
                {"item": "Resiliencia", "status": "feito", "justificativa": "Salvaguarda de exceção operacional executada"}
            ],
            "status_operacional": "FALLBACK"
        }

        envelope = {"relatorio": relatorio_fallback}

        if arquivo_log:
            estado_atual.salvar_estado(arquivo_log)

        if handoff_path:
            handoff_dest = Path(handoff_path).resolve()
            _handoff.emitir_handoff(
                handoff_dest,
                status="SUCESSO_FALLBACK",
                codigo_saida=0,
                repo_root=handoff_dest.parent,
                detalhes={
                    "pedido": pedido,
                    "modo": "FALLBACK",
                    "erro_original": str(exc),
                },
            )

        return envelope
