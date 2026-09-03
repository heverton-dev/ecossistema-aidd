#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executor de Pipeline em Subprocesso com Captura de Erros e Logs
web/pipeline_runner.py — aidd-project-generator
"""

import os
import sys
import time
import queue
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque

from web.status_parser import analisar_status_pasta_projeto

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = ROOT_DIR / 'scripts' / 'pipeline_completo.py'


class PipelineRunner:
    """
    Gerencia a execução assíncrona do CLI pipeline_completo.py,
    rastreando logs, status das fases e tratando erros para exibição amigável.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.processo: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None

        # Estado da execução
        self.em_execucao: bool = False
        self.sucesso: Optional[bool] = None
        self.ideia: str = ""
        self.pasta_projeto: str = ""
        self.implementar_codigo: bool = False
        self.t_inicio: float = 0.0
        self.t_fim: Optional[float] = None

        # Logs e erros
        self.logs: deque = deque(maxlen=300)
        self.erro_amigavel: Optional[str] = None
        self.erro_tecnico: Optional[str] = None
        self.precisa_configuracao: bool = False
        self.fase_que_falhou: Optional[str] = None

    def iniciar_pipeline(
        self,
        ideia: str,
        pasta_projeto: str,
        implementar_codigo: bool = False
    ) -> Dict[str, Any]:
        """Inicia o pipeline em uma thread separada executando o script CLI oficial."""
        with self._lock:
            if self.em_execucao:
                return {
                    'sucesso': False,
                    'mensagem': 'Já existe um pipeline em execução. Aguarde a conclusão ou cancele.'
                }

            ideia_limpa = ideia.strip()
            if not ideia_limpa:
                return {
                    'sucesso': False,
                    'mensagem': 'Por favor, informe a ideia do projeto que deseja construir.'
                }

            pasta_destino = Path(pasta_projeto.strip()).resolve()

            self.em_execucao = True
            self.sucesso = None
            self.ideia = ideia_limpa
            self.pasta_projeto = str(pasta_destino)
            self.implementar_codigo = implementar_codigo
            self.t_inicio = time.time()
            self.t_fim = None
            self.logs.clear()
            self.erro_amigavel = None
            self.erro_tecnico = None
            self.precisa_configuracao = False
            self.fase_que_falhou = None

            self.thread = threading.Thread(
                target=self._executar_worker,
                args=(ideia_limpa, pasta_destino, implementar_codigo),
                daemon=True
            )
            self.thread.start()

            return {
                'sucesso': True,
                'mensagem': 'Pipeline iniciado com sucesso!',
                'pasta_projeto': str(pasta_destino),
                'implementar_codigo': implementar_codigo
            }

    def _executar_worker(self, ideia: str, pasta_destino: Path, implementar_codigo: bool):
        """Worker que roda em background monitorando o subprocesso."""
        cmd = [
            sys.executable,
            str(PIPELINE_SCRIPT),
            ideia,
            '--pasta',
            str(pasta_destino)
        ]

        if implementar_codigo:
            cmd.append('--implementar-codigo')

        # Garantir UTF-8 no Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'

        self._adicionar_log(f"🚀 Iniciando pipeline AIDD...")
        self._adicionar_log(f"📁 Pasta de destino: {pasta_destino}")
        self._adicionar_log(f"💡 Ideia: {ideia}")
        if implementar_codigo:
            self._adicionar_log("⚡ Modo funcional ativado (Fase 8 - implementação de código real)")

        try:
            # Garante que a pasta pai existe
            pasta_destino.parent.mkdir(parents=True, exist_ok=True)

            self.processo = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(ROOT_DIR),
                env=env,
                bufsize=1
            )

            # Leitura de logs em tempo real
            if self.processo.stdout:
                for linha in iter(self.processo.stdout.readline, ''):
                    if not linha:
                        break
                    linha_formatada = linha.rstrip()
                    if linha_formatada:
                        self._adicionar_log(linha_formatada)

            self.processo.wait()
            codigo_saida = self.processo.returncode
            self.t_fim = time.time()

            with self._lock:
                self.em_execucao = False
                if codigo_saida == 0:
                    self.sucesso = True
                    self._adicionar_log(f"🎉 Pipeline concluído com sucesso em {self.t_fim - self.t_inicio:.1f}s!")
                else:
                    self.sucesso = False
                    self._processar_falha()

        except Exception as e:
            self.t_fim = time.time()
            with self._lock:
                self.em_execucao = False
                self.sucesso = False
                self.erro_amigavel = f"Erro ao iniciar o processo do pipeline: {e}"
                self.erro_tecnico = str(e)
                self._adicionar_log(f"❌ Erro de inicialização: {e}")

    def _adicionar_log(self, mensagem: str):
        """Adiciona log ao buffer thread-safe."""
        timestamp = time.strftime('%H:%M:%S')
        with self._lock:
            self.logs.append(f"[{timestamp}] {mensagem}")

    def _processar_falha(self):
        """Analisa os logs brutos para identificar a causa da falha e gerar mensagem amigável."""
        todos_logs = "\n".join(self.logs)

        # 1. Detecção de erro de Chave de IA / LiteLLM
        indicadores_falha_llm = [
            'badrequesterror',
            'provider list',
            'authenticationerror',
            'invalid api key',
            'llm_model não está configurado',
            'llm_model nao esta configurado',
            'chave de api',
            '401 unauthorized',
            '401 client error',
            'apiconnectionerror',
            'ratelimiterror',
            'litellm.exceptions',
            'nenhuma chave configurada'
        ]

        logs_lower = todos_logs.lower()
        if any(ind in logs_lower for ind in indicadores_falha_llm):
            self.precisa_configuracao = True
            self.erro_amigavel = (
                "Você ainda não configurou uma chave de IA ou a chave configurada é inválida/expirada. "
                "Vá em Configurações para definir uma chave válida e tentar novamente."
            )
        elif 'permissionerror' in logs_lower or 'acesso negado' in logs_lower:
            self.erro_amigavel = (
                "Permissão negada ao acessar a pasta de destino. Escolha outra pasta ou execute como administrador."
            )
        elif 'timeout' in logs_lower:
            self.erro_amigavel = (
                "Tempo limite de resposta do modelo de IA excedido. O provedor pode estar instável. "
                "Tente novamente ou alterne o provedor em Configurações."
            )
        else:
            self.erro_amigavel = (
                "O pipeline falhou durante a execução. Verifique os detalhes técnicos abaixo para mais informações."
            )

        self.erro_tecnico = todos_logs

    def cancelar_pipeline(self) -> Dict[str, Any]:
        """Cancela a execução em andamento do subprocesso."""
        with self._lock:
            if not self.em_execucao or not self.processo:
                return {'sucesso': False, 'mensagem': 'Nenhum pipeline em execução para cancelar.'}

            try:
                self.processo.terminate()
                # No Windows, force kill se necessário
                time.sleep(0.5)
                if self.processo.poll() is None:
                    self.processo.kill()

                self.em_execucao = False
                self.sucesso = False
                self.t_fim = time.time()
                self.erro_amigavel = "Pipeline cancelado pelo usuário."
                self._adicionar_log("⚠️ Pipeline cancelado pelo usuário.")
                return {'sucesso': True, 'mensagem': 'Pipeline cancelado com sucesso.'}
            except Exception as e:
                return {'sucesso': False, 'mensagem': f"Erro ao cancelar processo: {e}"}

    def obter_status(self) -> Dict[str, Any]:
        """Retorna o estado consolidado do runner e os dados reais de status_parser."""
        with self._lock:
            em_exec = self.em_execucao
            sucesso = self.sucesso
            ideia = self.ideia
            pasta = self.pasta_projeto
            implementar = self.implementar_codigo
            t_inicio = self.t_inicio
            t_fim = self.t_fim
            logs_lista = list(self.logs)
            erro_amigavel = self.erro_amigavel
            erro_tecnico = self.erro_tecnico
            precisa_config = self.precisa_configuracao

        duracao_decorrida = (t_fim or time.time()) - t_inicio if t_inicio > 0 else 0.0

        # Analisar arquivos de cache reais do disco
        dados_fases: Dict[str, Any] = {}
        if pasta:
            dados_fases = analisar_status_pasta_projeto(
                pasta_projeto=Path(pasta),
                implementar_codigo=implementar,
                subprocess_rodando=em_exec
            )

        return {
            'em_execucao': em_exec,
            'sucesso': sucesso,
            'ideia': ideia,
            'pasta_projeto': pasta,
            'implementar_codigo': implementar,
            'duracao_segundos': round(duracao_decorrida, 1),
            'logs': logs_lista,
            'erro_amigavel': erro_amigavel,
            'erro_tecnico': erro_tecnico,
            'precisa_configuracao': precisa_config,
            'fases_dados': dados_fases
        }


# Instância singleton para ser usada pela aplicação Flask
runner_global = PipelineRunner()
