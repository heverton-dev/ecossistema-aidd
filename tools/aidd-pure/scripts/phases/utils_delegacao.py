#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTILS: Delegação LLM Agnóstica
aidd-project-generator v2.1

Protocolo universal para comunicação com orquestrador:
- Modo Delegado (default): escreve arquivo, ADE responde, fase continua
- Modo Headless (fallback): usa litellm direto se nenhuma ADE ativa

Nenhuma credencial nova necessária em Modo Delegado.
"""

import sys
import os
import re
import json
import uuid
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any, Type

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    _WATCHDOG_DISPONIVEL = True
except ImportError:
    _WATCHDOG_DISPONIVEL = False

# Escritor atômico: staging → fsync → os.replace
try:
    from escritor_atomico import escrever_json_atomico
except ImportError:
    import importlib.util
    _comp_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "componentes", "compartilhado", "src-core"
    )
    if os.path.isdir(_comp_dir) and _comp_dir not in sys.path:
        sys.path.insert(0, _comp_dir)
    from escritor_atomico import escrever_json_atomico

if _WATCHDOG_DISPONIVEL:
    class _ArquivoRespostaHandler(FileSystemEventHandler):
        """Handler leve para acordar o loop de espera assim que o arquivo é modificado/criado."""
        def __init__(self, nome_alvo: str, evento_sinal: threading.Event):
            super().__init__()
            self.nome_alvo = nome_alvo
            self.evento_sinal = evento_sinal

        def on_created(self, event):
            if not event.is_directory and Path(event.src_path).name == self.nome_alvo:
                self.evento_sinal.set()

        def on_modified(self, event):
            if not event.is_directory and Path(event.src_path).name == self.nome_alvo:
                self.evento_sinal.set()

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None

try:
    import instructor
except ImportError:
    instructor = None

try:
    from schemas.registry import (
        validar_request as _validar_request,
        validar_response as _validar_response,
        SchemaValidationError,
    )
except ImportError:
    _validar_request = None
    _validar_response = None
    SchemaValidationError = None


# =============================================================================
# EXCEÇÕES CUSTOMIZADAS
# =============================================================================

class LLMNaoConfiguradoException(Exception):
    """Erro de configuração do provedor LLM — mensagem amigável para o usuário final."""

    def __init__(self, mensagem_usuario: str, detalhes_tecnicos: str):
        super().__init__(mensagem_usuario)
        self.mensagem_usuario = mensagem_usuario
        self.detalhes_tecnicos = detalhes_tecnicos

    def __str__(self) -> str:
        return self.mensagem_usuario

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carrega .env da raiz do repositório da ferramenta (independente do cwd de
# onde a pipeline for invocada — inclusive quando roda dentro de um projeto
# gerado, que é uma pasta irmã, não filha, deste repo).
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parent.parent.parent / '.env'
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH)
except ImportError:
    pass


def _remover_fence_envolvente(texto: str) -> str:
    """Remove um code fence markdown (```lang\\n...\\n```) que envolva TODO o
    valor de uma string — caso em que o LLM cola o bloco de código completo
    (fences inclusos) como valor literal de um campo JSON como 'codigo'/'teste'."""
    if not isinstance(texto, str):
        return texto
    m = re.match(r'^```[a-zA-Z0-9_+-]*\s*\n([\s\S]*?)\n?```\s*$', texto.strip())
    return m.group(1) if m else texto


def _sanitizar_campos_codigo(resultado: Any) -> Any:
    """Aplica _remover_fence_envolvente aos campos 'codigo'/'teste', se existirem."""
    if isinstance(resultado, dict):
        for campo in ('codigo', 'teste'):
            if campo in resultado:
                resultado[campo] = _remover_fence_envolvente(resultado[campo])
    return resultado


def extrair_json_resposta(texto: str, response_model=None) -> Any:
    """
    Extrai e decodifica JSON de uma resposta de LLM, mesmo se contiver
    markdown code fences (```json ... ```), texto explicativo antes ou depois,
    ou quebras de linha não escapadas dentro de strings.

    Se response_model for fornecido e instructor estiver disponível, usa
    instructor para parsing robusto com retry automático.
    """
    if not texto or not isinstance(texto, str):
        raise ValueError("Texto vazio ou inválido para extração de JSON")

    texto_limpo = texto.strip()

    # Tenta usar instructor se response_model for fornecido
    if response_model is not None and BaseModel is not None and instructor is not None:
        try:
            return _parsear_com_instructor(texto_limpo, response_model)
        except Exception:
            # Fallback para parsing manual se instructor falhar
            pass

    # Parsing manual (legado) para compatibilidade
    return _extrair_json_manual(texto_limpo)


def _extrair_json_manual(texto_limpo: str) -> Any:
    """Parsing manual de JSON (legado, mantido para compatibilidade)."""

    def _tentar_parse_sanitizado(s: str):
        # Substitui barras invertidas que não sejam escapes válidos de JSON por barra dupla
        s_sanitizado = re.sub(r'\\(?!["\\/bfnrtuU0-9])', r'\\\\', s)
        try:
            return json.loads(s_sanitizado, strict=False)
        except json.JSONDecodeError:
            return None

    # 1. Tentar decodificar direto
    try:
        return _sanitizar_campos_codigo(json.loads(texto_limpo, strict=False))
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Se envelopado em markdown code fence
    if '```' in texto_limpo:
        for pattern in [r'```(?:json)?\s*([\s\S]*)\s*```', r'```(?:json)?\s*([\s\S]*?)\s*```']:
            match = re.search(pattern, texto_limpo)
            if match:
                bloco = match.group(1).strip()
                try:
                    return _sanitizar_campos_codigo(json.loads(bloco, strict=False))
                except json.JSONDecodeError:
                    pass
                res = _tentar_parse_sanitizado(bloco)
                if res is not None:
                    return _sanitizar_campos_codigo(res)

    # 4. Fallback estruturado para respostas de codegen (codigo + teste)
    def _extrair_campos_codegen(s: str):
        if '"codigo"' not in s:
            return None
        res = {}
        m_cod = re.search(r'"codigo"\s*:\s*"""([\s\S]*?)"""', s)
        if not m_cod:
            m_cod = re.search(r'"codigo"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"(?:teste|caminho)|\s*"\s*\}\s*$)', s)
        if not m_cod:
            m_cod = re.search(r'"codigo"\s*:\s*([\s\S]*?)(?:,\s*"teste"|\}\s*$)', s)
        if m_cod:
            c = m_cod.group(1).strip()
            if c.startswith('"') and c.endswith('"') and len(c) >= 2:
                c = c[1:-1]
            c = c.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
            res['codigo'] = c

        m_tst = re.search(r'"teste"\s*:\s*"""([\s\S]*?)"""', s)
        if not m_tst:
            m_tst = re.search(r'"teste"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"caminho|\s*"\s*\}\s*$)', s)
        if not m_tst:
            m_tst = re.search(r'"teste"\s*:\s*([\s\S]*?)(?:,\s*"caminho"|\}\s*$)', s)
        if m_tst:
            t = m_tst.group(1).strip()
            if t.startswith('"') and t.endswith('"') and len(t) >= 2:
                t = t[1:-1]
            t = t.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
            res['teste'] = t

        m_cam = re.search(r'"caminho_relativo"\s*:\s*"([^"]+)"', s)
        if m_cam:
            res['caminho_relativo'] = m_cam.group(1)

        m_tcam = re.search(r'"caminho_teste"\s*:\s*"([^"]+)"', s)
        if m_tcam:
            res['caminho_teste'] = m_tcam.group(1)

        if 'codigo' in res and 'teste' in res:
            return res
        return None

    res_cod = _extrair_campos_codegen(texto_limpo)
    if res_cod is not None:
        return _sanitizar_campos_codigo(res_cod)

    # 5. Se nada funcionou, repassa para json.loads para gerar exceção informativa
    return _sanitizar_campos_codigo(json.loads(texto_limpo, strict=False))


def _parsear_com_instructor(texto: str, response_model: Any) -> Any:
    """
    Parseia JSON usando o mecanismo de validação com retry automático do
    ecossistema instructor/pydantic (Retry + model_validate).

    Args:
        texto: String JSON (ou dict) para parsear
        response_model: Modelo Pydantic alvo

    Returns:
        Instância do response_model validada

    Raises:
        ValidationError: Se o JSON não corresponder ao modelo
        ImportError: Se pydantic/instructor não estiver disponível
    """
    if BaseModel is None:
        raise ImportError("pydantic é necessário para usar parsing estruturado (instructor)")
    if instructor is None:
        raise ImportError("instructor é necessário para usar parsing estruturado")
    return _validar_pydantic_com_retry(texto, response_model)


# =============================================================================
# ITEM 3 [TK-2]: ESCADA DE REPARO JSON DETERMINÍSTICA — ZERO LLM
# =============================================================================
# Reparo mecânico (regex/AST) das quebras de formatação mais comuns em
# respostas de LLM, ANTES de qualquer retry caro de LLM. Cada degrau é
# determinístico e auditável; a escada inteira roda sem rede e sem modelo.


def _reparo_remover_virgulas_trailing(s: str) -> str:
    """Degrau 1: remove vírgulas sobrando antes de } ou ] (regex determinístico)."""
    return re.sub(r',\s*(?=[}\]])', '', s)


def _reparo_fechar_estrutura(s: str) -> str:
    """Degrau 2: fecha chaves/colchetes abertos (balanceamento por pilha,
    respeitando strings). Nunca inventa conteúdo — só fecha o que ficou aberto."""
    pilha = []
    em_string = False
    escape = False
    for ch in s:
        if em_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                em_string = False
            continue
        if ch == '"':
            em_string = True
        elif ch in '{[':
            pilha.append(ch)
        elif ch in '}]':
            if pilha and ((ch == '}' and pilha[-1] == '{') or (ch == ']' and pilha[-1] == '[')):
                pilha.pop()
    if not pilha and not em_string:
        return s
    fechamento = ''.join('}' if c == '{' else ']' for c in reversed(pilha))
    if em_string:
        fechamento = '"' + fechamento
    return s + fechamento


def _reparo_aspas_soltas_fim(s: str) -> str:
    """Degrau 3: fecha string aberta no fim do payload (trailing quote)."""
    pilha = []
    em_string = False
    escape = False
    for ch in s:
        if em_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                em_string = False
            continue
        if ch == '"':
            em_string = True
        elif ch in '{[':
            pilha.append(ch)
        elif ch in '}]':
            if pilha and ((ch == '}' and pilha[-1] == '{') or (ch == ']' and pilha[-1] == '[')):
                pilha.pop()
    return s + '"' if em_string else s


def _reparo_quebras_em_strings(s: str) -> str:
    """Degrau 4: sanitiza quebras de linha/tabs literais dentro de strings
    (JSON estrito não aceita \n cru dentro de aspas)."""
    def _sub(m):
        corpo = m.group(1)
        corpo = corpo.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
        corpo = corpo.replace('\t', '\\t')
        return '"' + corpo + '"'
    return re.sub(r'"((?:[^"\\]|\\.)*)"', _sub, s, flags=re.S)


def _reparo_chaves_sem_aspas(s: str) -> str:
    """Degrau 5: envolve chaves JS-style sem aspas ({codigo: "x"}) em aspas."""
    return re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)',
                  lambda m: m.group(1) + '"' + m.group(2) + '"' + m.group(3), s)


ESCADA_REPARO_JSON = (
    _reparo_remover_virgulas_trailing,
    _reparo_fechar_estrutura,
    _reparo_aspas_soltas_fim,
    _reparo_quebras_em_strings,
    _reparo_chaves_sem_aspas,
)


def reparar_json_deterministico(texto: str, max_degraus: int = 6) -> Optional[Any]:
    """[TK-2] Item 3: escada determinística de reparo de JSON quebrado.

    Aplica degraus cumulativos (cada degrau soma o reparo anterior) e tenta
    json.loads(strict=False) a cada passo. Zero LLM, zero rede, zero aleatório.

    Returns:
        Objeto Python desserializado, ou None se nenhum degrau recuperou.
    """
    if not isinstance(texto, str) or not texto.strip():
        return None

    s = texto.strip()
    # Extração manual de fences markdown e substrings {..} / [..] primeiro
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', s)
    if m:
        s = m.group(1).strip()
    else:
        m_obj = re.search(r'[\s\S]*?(\{[\s\S]*\}|\[[\s\S]*\])', s)
        if m_obj:
            s = m_obj.group(1)

    try:
        return json.loads(s, strict=False)
    except json.JSONDecodeError:
        pass

    reparo_acumulado = s
    aplicados: list = []
    for degrau in ESCADA_REPARO_JSON:
        if len(aplicados) >= max_degraus:
            break
        novo = degrau(reparo_acumulado)
        aplicados.append(degrau.__name__)
        if novo == reparo_acumulado:
            continue
        reparo_acumulado = novo
        try:
            return json.loads(reparo_acumulado, strict=False)
        except json.JSONDecodeError:
            continue

    # Combinação final: todos os degraus aplicados de uma vez (ordem da escada)
    combinado = s
    for degrau in ESCADA_REPARO_JSON:
        combinado = degrau(combinado)
    try:
        return json.loads(combinado, strict=False)
    except json.JSONDecodeError:
        return None


def _validar_pydantic_com_retry_com_loads(
    texto: str,
    response_model: Any,
    max_retries: int = 3,
    _loads: Optional[Callable[[str], Any]] = None,
) -> Any:
    """
    Valida JSON contra modelo Pydantic com retry automático via instructor.
    (Renomeado no Item 3 [TK-2]: versão SEM escada determinística — usada
    como mecanismo puro de validação; o wrapper público aplica a escada antes.)

    Args:
        texto: String JSON para validar
        response_model: Modelo Pydantic alvo
        max_retries: Número máximo de tentativas

    Returns:
        Instância validada do response_model
    """
    if BaseModel is None:
        raise ImportError("pydantic é necessário")

    import json as json_mod
    ultimo_erro: Optional[Exception] = None

    for tentativa in range(max_retries):
        try:
            # Tenta parsear o JSON primeiro
            if _loads is None:
                _loads = lambda s, strict=False: json_mod.loads(s, strict=False)
            dados = _loads(texto) if isinstance(texto, str) else texto

            # Se o dado já é uma instância do modelo, retorna
            if isinstance(dados, response_model):
                return dados

            # Valida e cria instância do modelo
            return response_model.model_validate(dados)

        except ValueError as e:
            ultimo_erro = e
            # Se instructor estiver disponível, usa retry automático
            if instructor is not None and tentativa < max_retries - 1:
                time.sleep(0.5 * (tentativa + 1))  # Backoff linear

    # Se todas as tentativas falharam, levanta o último erro
    if ultimo_erro is not None:
        raise ultimo_erro
    raise ValueError("Falha desconhecida na validação Pydantic")


def _validar_pydantic_com_retry(
    texto: str,
    response_model: Any,
    max_retries: int = 1,
    _loads: Optional[Callable[[str], Any]] = None,
) -> Any:
    """[TK-2] Item 3: wrapper público com escada determinística ANTES do retry.

    Ordem de resolução (economia de tokens, Zero Token Fallacy):
    1. Parse/validação direta (caminho feliz).
    2. Escada determinística de reparo (reparar_json_deterministico) — zero LLM.
    3. No MÁXIMO 1 tentativa adicional via _validar_pydantic_com_retry_com_loads
       (mecanismo instructor), só se a escada não recuperou.

    Args:
        texto: String JSON (ou dict) para validar
        response_model: Modelo Pydantic alvo
        max_retries: Tentativas adicionais pós-escada (default 1 — antes eram 3)

    Returns:
        Instância validada do response_model
    """
    if BaseModel is None:
        raise ImportError("pydantic é necessário")

    # Caminho feliz: dict direto ou string parseável
    if isinstance(texto, response_model):
        return texto

    dados_escada: Any = None
    if isinstance(texto, str):
        try:
            dados_direto = ( _loads(texto) if _loads is not None
                            else json.loads(texto, strict=False) )
            return response_model.model_validate(dados_direto)
        except (ValueError, TypeError):
            pass

        # Degrau determinístico — nunca chama LLM
        dados_escada = reparar_json_deterministico(texto)
        if dados_escada is not None:
            try:
                return response_model.model_validate(dados_escada)
            except Exception:
                dados_escada = None  # escada recuperou JSON, mas não validou

    # Último recurso: no máximo 1 tentativa pelo mecanismo instructor
    return _validar_pydantic_com_retry_com_loads(
        texto, response_model, max_retries=max(1, max_retries), _loads=_loads
    )


# =============================================================================
# CONSTANTES E CONFIGURAÇÃO DE TIMEOUTS POR FASE
# =============================================================================

CACHE_DIR = Path(__file__).parent.parent / '.aidd' / 'cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT_DELEGACAO = 30  # segundos legado / fallback geral
TIMEOUT_PADRAO_DELEGACAO = 30
INTERVALO_POLLING = 0.1  # compatibilidade legado: agora 100ms
INTERVALO_POLLING_INICIAL = 0.1  # 100ms inicial
INTERVALO_POLLING_MAX = 1.0      # teto de 1s para reduzir I/O de disco
FATOR_BACKOFF_POLLING = 1.5      # escalonamento progressivo

TIMEOUTS_POR_FASE = {
    # Fases de análise, design e especificação
    "phase_01": 30,
    "phase_02": 45,
    "phase_03": 45,
    "phase_04": 60,
    "phase_05": 60,
    "phase_06": 60,
    # Fases de testes e implementação pesada de código
    "phase_07": 120,
    "phase_08": 180,
    "01_analisador_ideia": 30,
    "02_analisador": 45,
    "03_designer": 45,
    "04_especificador": 60,
    "05_arquiteto": 60,
    "06_planejador": 60,
    "07_gerador_testes": 120,
    "08_implementador": 180,
}


def obter_timeout_por_fase(fase: Optional[str] = None, timeout_custom: Optional[int] = None) -> int:
    """Retorna timeout em segundos configurável por fase, suportando env vars e overrides."""
    if timeout_custom is not None:
        return timeout_custom

    env_global = os.environ.get("AIDD_TIMEOUT_DELEGACAO")
    if env_global:
        try:
            return int(env_global)
        except ValueError:
            pass

    if fase:
        env_fase_key = f"AIDD_TIMEOUT_{fase.upper().replace('-', '_')}"
        env_fase = os.environ.get(env_fase_key)
        if env_fase:
            try:
                return int(env_fase)
            except ValueError:
                pass
        fase_norm = fase.lower().strip()
        if fase_norm in TIMEOUTS_POR_FASE:
            return TIMEOUTS_POR_FASE[fase_norm]

    return TIMEOUT_PADRAO_DELEGACAO


# =============================================================================
# ITEM 4 [TK-6]: HERMETICIDADE DE SESSÕES — ROTULAGEM DE TELEMETRIA
# =============================================================================
# Regra de honestidade de rótulo (#9): a telemetria de tokens informa
# explicitamente se a medição ocorreu em sessão isolada (headless efêmero,
# sem persistência de contexto) ou em sessão compartilhada delegada (ADE
# ativa, contexto acumulado da conversa pode contaminar a medição).

SESSAO_ISOLADA = 'sessao_isolada'
SESSAO_COMPARTILHADA_DELEGADA = 'sessao_compartilhada_delegada'


def rotular_tipo_sessao(modo: str) -> str:
    """Retorna o rótulo canônico do tipo de sessão para a telemetria.

    - 'headless'  -> SESSAO_ISOLADA (processo efêmero, sem persistência)
    - 'delegado'  -> SESSAO_COMPARTILHADA_DELEGADA (ADE ativa na conversa)
    """
    if modo == 'headless':
        return SESSAO_ISOLADA
    return SESSAO_COMPARTILHADA_DELEGADA


# Flags de hermeticidade obrigatórias por harness em comandos headless CLI.
# Qualquer executor headless que monte comando de CLI externa DEVE incluir
# flag de sessão efêmera do harness alvo (ver gates/G_SESSAO_HERMETICA.py).
FLAGS_SESSAO_EFEMERA_POR_HARNESS = {
    'claude': ['--no-session-persistence'],
    'claude-code': ['--no-session-persistence'],
    'codex': ['--ephemeral'],
    'agy': ['--ephemeral-session'],
    'opencode': ['--no-persist'],
    'mimo': ['--no-persist'],
    'gemini': ['--ephemeral'],
    'hermes': ['--ephemeral'],
}


def validar_sessao_hermetica(comando: list, harness: Optional[str] = None) -> Dict[str, Any]:
    """Valida (determinístico, zero token) que um comando headless CLI contém
    flag de sessão efêmera/isolada.

    Args:
        comando: lista argv do processo a disparar
        harness: nome do harness (opcional; inferido do argv[0] se ausente)

    Returns:
        {'hermetico': bool, 'harness': str, 'flag_exigida': str|None,
         'flags_presentes': list}
    """
    if not comando:
        return {'hermetico': False, 'harness': None, 'flag_exigida': None, 'flags_presentes': []}
    nome_bin = Path(str(comando[0])).name.lower()
    harness_norm = (harness or nome_bin).lower()
    for chave, flags in FLAGS_SESSAO_EFEMERA_POR_HARNESS.items():
        if harness_norm.startswith(chave):
            presentes = [f for f in comando if f in flags]
            return {
                'hermetico': len(presentes) > 0,
                'harness': chave,
                'flag_exigida': flags[0],
                'flags_presentes': presentes,
            }
    # Harness sem flag conhecida: exigência não aplicável — hermético por
    # omissão documentada (nenhuma CLI externa disparada).
    return {'hermetico': True, 'harness': harness_norm, 'flag_exigida': None, 'flags_presentes': []}


def forcar_sessao_hermetica(comando: list, harness: Optional[str] = None) -> list:
    """Garante que o comando receba a flag de sessão efêmera do harness
    (idempotente: não duplica flag já presente)."""
    relatorio = validar_sessao_hermetica(comando, harness)
    if relatorio['hermetico'] or relatorio['flag_exigida'] is None:
        return list(comando)
    return [comando[0], relatorio['flag_exigida']] + list(comando[1:])


# =============================================================================
# PROTOCOLO DELEGADO
# =============================================================================

class RequisicaoLLMDelegada:
    """Encapsula uma solicitação de LLM delegada à ADE"""

    def __init__(self, prompt: str, contexto: str, fase: str, modelo_sugerido: Optional[str] = None):
        self.id = str(uuid.uuid4())[:8]
        self.prompt = prompt
        self.contexto = contexto
        self.fase = fase
        self.modelo_sugerido = modelo_sugerido or "claude-opus-5"
        self.timestamp_criado = datetime.now(timezone.utc).isoformat()

    def escrever_arquivo(self) -> Path:
        """Escreve requisição em arquivo JSON no cache.

        Valida o payload contra schemas/llm_request_v1.json antes de escrever
        (quando schemas disponíveis).
        """
        caminho = CACHE_DIR / f"_llm_request_{self.id}.json"
        dados = {
            "id": self.id,
            "fase": self.fase,
            "timestamp": self.timestamp_criado,
            "modelo_sugerido": self.modelo_sugerido,
            "contexto": self.contexto,
            "prompt": self.prompt,
        }
        if _validar_request is not None:
            _validar_request(dados)
        escrever_json_atomico(caminho, dados)
        return caminho

    @staticmethod
    def aguardar_resposta(
        id_requisicao: str,
        timeout: Optional[int] = None,
        fase: Optional[str] = None,
        intervalo_inicial: float = INTERVALO_POLLING_INICIAL,
        intervalo_max: float = INTERVALO_POLLING_MAX,
        fator_backoff: float = FATOR_BACKOFF_POLLING,
    ) -> Optional[Dict[str, Any]]:
        """Aguarda e lê resposta da ADE com polling adaptativo event-driven.

        - Inicia em 100ms (0.1s) e escala progressivamente via backoff até intervalo_max.
        - Se watchdog estiver disponível, usa file watcher event-driven para reação imediata.
        - Valida o payload contra schemas/llm_response_v1.json quando disponível.
        """
        timeout_efetivo = timeout if timeout is not None else obter_timeout_por_fase(fase)
        caminho_resposta = CACHE_DIR / f"_llm_response_{id_requisicao}.json"
        nome_alvo = caminho_resposta.name

        evento_sinal = threading.Event()
        observer = None

        if _WATCHDOG_DISPONIVEL:
            try:
                observer = Observer()
                handler = _ArquivoRespostaHandler(nome_alvo, evento_sinal)
                observer.schedule(handler, str(CACHE_DIR), recursive=False)
                observer.start()
            except OSError:
                observer = None

        inicio = time.time()
        intervalo = intervalo_inicial

        try:
            while time.time() - inicio < timeout_efetivo:
                if caminho_resposta.exists():
                    try:
                        with open(caminho_resposta, 'r', encoding='utf-8') as f:
                            dados = json.load(f)

                        # Validação básica (legado)
                        if "conteudo" not in dados or "tokens_consumidos" not in dados:
                            pass
                        else:
                            # Validação JSON Schema (quando disponível)
                            if _validar_response is not None:
                                try:
                                    _validar_response(dados)
                                except SchemaValidationError:
                                    pass
                            return dados

                    except (json.JSONDecodeError, IOError):
                        # Arquivo ainda sendo gravado ou com lock temporário
                        pass

                tempo_restante = timeout_efetivo - (time.time() - inicio)
                if tempo_restante <= 0:
                    break

                tempo_espera = min(intervalo, tempo_restante)

                if observer is not None:
                    # Event-driven: acorda instantaneamente se arquivo for criado/modificado
                    evento_sinal.wait(timeout=tempo_espera)
                    evento_sinal.clear()
                else:
                    time.sleep(tempo_espera)

                intervalo = min(intervalo * fator_backoff, intervalo_max)

            # Timeout
            return None

        finally:
            if observer is not None:
                try:
                    observer.stop()
                    observer.join(timeout=0.2)
                except OSError:
                    pass


# =============================================================================
# TELEMETRIA AUXILIAR DE TOKENS (tiktoken, offline)
# =============================================================================

_TOKENIZADOR_TIKTOKEN = None


def _obter_tokenizador_tiktoken():
    """Carrega o tokenizador cl100k_base do tiktoken com cache (offline).

    A telemetria é auxiliar: nunca pode derrubar a pipeline, então qualquer
    falha de import/encoding vira retorno None permanente (flag False).
    """
    global _TOKENIZADOR_TIKTOKEN
    if _TOKENIZADOR_TIKTOKEN is None:
        try:
            import tiktoken
            _TOKENIZADOR_TIKTOKEN = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _TOKENIZADOR_TIKTOKEN = False
    return _TOKENIZADOR_TIKTOKEN or None


def estimar_tokens_tiktoken(prompt: str, contexto: str, conteudo: Optional[str]) -> Optional[Dict[str, Any]]:
    """Estima tokens de entrada (contexto+prompt) e saída (conteudo) via tiktoken.

    Telemetria auxiliar, determinística e 100% offline. NÃO é medição de billing:
    o rótulo canônico de origem de medição continua sendo o campo
    `origem_medicao` (autodeclarado no modo delegado; medido_api/indisponivel
    no headless conforme o provider reporte).

    Returns:
        {
            "entrada": int,
            "saida": int,
            "total": int,
            "tokenizer": "cl100k_base",
            "metodo": "tiktoken"
        }
        ou None se tiktoken indisponível.
    """
    tokenizador = _obter_tokenizador_tiktoken()
    if tokenizador is None:
        return None
    entrada = f"{contexto} {prompt}".strip() if contexto else (prompt or "")
    tokens_entrada = len(tokenizador.encode(entrada)) if entrada else 0
    tokens_saida = len(tokenizador.encode(conteudo)) if conteudo else 0
    return {
        "entrada": tokens_entrada,
        "saida": tokens_saida,
        "total": tokens_entrada + tokens_saida,
        "tokenizer": "cl100k_base",
        "metodo": "tiktoken",
    }


# =============================================================================
# MODO DELEGADO (default)
# =============================================================================

def solicitar_llm_modo_delegado(
    prompt: str,
    contexto: str,
    fase: str,
    timeout: Optional[int] = None,
    modelo: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Modo Delegado (default, universal):
    1. Escreve requisição em arquivo
    2. Aguarda resposta da ADE (Claude Code, Codex, Gemini CLI, etc.) com polling adaptativo
    3. Retorna resposta estruturada

    Não requer nenhuma credencial nova — usa a ADE já ativa.
    Se ADE não responder em tempo:
    - Se headless estiver configurado (LLM_MODEL no env ou modelo explícito), faz fallback automático.
    - Se headless não estiver configurado ou falhar, retorna None (timeout com falha honesta).

    Returns:
        {
            "id": "abc12345",
            "conteudo": "resposta LLM",
            "tokens_consumidos": 1234,
            "origem_medicao": "autodeclarado",
            "modelo_usado": "claude-opus-5",
            "timestamp_resposta": "2026-08-30T10:30:00Z",
            "tokens_estimativa_local": {
                "entrada": 100, "saida": 50, "total": 150,
                "tokenizer": "cl100k_base", "metodo": "tiktoken"
            }
        }
        ou None se timeout sem headless configurado.
    """
    timeout_efetivo = obter_timeout_por_fase(fase, timeout)
    req = RequisicaoLLMDelegada(
        prompt=prompt,
        contexto=contexto,
        fase=fase,
        modelo_sugerido=modelo
    )

    # Escrever requisição
    caminho_req = req.escrever_arquivo()
    print(f"✓ Requisição delegada criada: {caminho_req.name}")
    print(f"  ID: {req.id}")
    print(f"  Aguardando resposta da ADE... (timeout {timeout_efetivo}s)")

    # Aguardar resposta
    resposta = RequisicaoLLMDelegada.aguardar_resposta(req.id, timeout=timeout_efetivo, fase=fase)

    if resposta is None:
        print(f"✗ Timeout ao aguardar resposta delegada (ID: {req.id})")
        if modelo or os.environ.get('LLM_MODEL'):
            print("⚠️  Fallback automático: caindo para Modo Headless após timeout do modo delegado...")
            try:
                return solicitar_llm_modo_headless(prompt, contexto, fase, modelo=modelo)
            except LLMNaoConfiguradoException as e:
                print(f"⚠️  Modo Headless não configurado para fallback: {e}")
                return None
            except Exception as e:
                print(f"⚠️  Falha no Modo Headless durante fallback: {e}")
                return None
        return None

    # Garantir que modo delegado sempre rotule como autodeclarado,
    # sobrescrevendo qualquer valor que o ADE externo tenha escrito
    resposta['origem_medicao'] = 'autodeclarado'

    # Item 4 [TK-6]: rótulo honesto de tipo de sessão — no modo delegado o
    # modelo roda DENTRO da sessão da ADE ativa; contexto acumulado da
    # conversa pode contaminar a medição declarada.
    resposta['tipo_sessao'] = rotular_tipo_sessao('delegado')

    # Telemetria auxiliar offline (tiktoken): estimativa local de entrada/saída.
    # Não substitui tokens_consumidos nem origem_medicao — é apenas referência
    # local para o usuário estimar custo antes/depois, sem depender do ADE.
    resposta['tokens_estimativa_local'] = estimar_tokens_tiktoken(
        prompt, contexto, resposta.get('conteudo')
    )

    print(f"✓ Resposta recebida:")
    print(f"  Modelo: {resposta.get('modelo_usado', 'desconhecido')}")
    print(f"  Tokens: {resposta.get('tokens_consumidos', '?')} (origem: {resposta['origem_medicao']})")
    est_local = resposta.get('tokens_estimativa_local')
    if est_local:
        print(f"  Estimativa local: {est_local['entrada']} entrada + {est_local['saida']} saída = {est_local['total']} tokens (tiktoken, offline)")
    else:
        print(f"  Estimativa local: indisponível (tiktoken não instalado)")

    return resposta


# =============================================================================
# MODO HEADLESS (fallback)
# =============================================================================

def solicitar_llm_modo_headless(
    prompt: str,
    contexto: str,
    fase: str,
    modelo: Optional[str] = None,
    temperatura: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Modo Headless (fallback, para CI/CD, scripts standalone, etc.):
    Chama LLM diretamente via litellm (requer credencial configurada).

    Item 4 [TK-6]: sessão hermética por construção — litellm roda em
    processo efêmero sem persistência de contexto (sem flags de sessão
    persistente); telemetria rotulada como sessao_isolada.

    Args:
        prompt: Texto do prompt
        contexto: Contexto adicional (ex: "Phase 2, analisando...")
        fase: Nome da fase (para logs)
        modelo: Modelo a usar (default: env var LLM_MODEL ou claude-opus-5)
        temperatura: Parâmetro de temperature da API

    Returns:
        {
            "conteudo": "resposta LLM",
            "tokens_consumidos": 1234,
            "origem_medicao": "medido_api",
            "modelo_usado": "claude-opus-5",
            "timestamp_resposta": "2026-08-30T10:30:00Z",
            "tokens_estimativa_local": {
                "entrada": 100, "saida": 50, "total": 150,
                "tokenizer": "cl100k_base", "metodo": "tiktoken"
            }
        }
        ou None se erro.
        tokens_estimativa_local é telemetria auxiliar offline (tiktoken);
        não substitui tokens_consumidos nem origem_medicao (medido_api/indisponivel).
    """
    try:
        import litellm
    except ImportError:
        print("✗ litellm não instalado. Use: python -m pip install litellm")
        return None

    if not modelo or modelo == 'desconhecido':
        modelo = os.environ.get('LLM_MODEL')

    if not modelo or modelo == 'desconhecido':
        try:
            from .utils_modelo import detectar_modelo_harness
            h_model = detectar_modelo_harness()
            if h_model and h_model != 'desconhecido':
                modelo = h_model
        except ImportError:
            pass

    if not modelo or modelo == 'desconhecido':
        raise LLMNaoConfiguradoException(
            mensagem_usuario=(
                "Nenhum modelo LLM configurado para o Modo Headless. "
                "Configure LLM_MODEL e a chave do provedor no arquivo .env (veja .env.example)."
            ),
            detalhes_tecnicos="Modelo não especificado ou 'desconhecido' no modo headless."
        )

    print(f"✓ Modo Headless: chamando {modelo} diretamente")
    print(f"  Contexto: {contexto}")

    timeout_segundos = int(os.environ.get('LLM_TIMEOUT_SEGUNDOS', '180'))
    max_tentativas = int(os.environ.get('LLM_MAX_TENTATIVAS', '3'))

    for tentativa in range(1, max_tentativas + 1):
        try:
            resposta = litellm.completion(
                model=modelo,
                messages=[
                    {"role": "system", "content": f"Contexto: {contexto}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperatura,
                max_tokens=8192,
                timeout=timeout_segundos,
            )

            conteudo = resposta.choices[0].message.content
            tokens = resposta.usage.total_tokens if hasattr(resposta.usage, 'total_tokens') else None
            origem_medicao = "medido_api" if tokens is not None else "indisponivel"

            resultado = {
                "conteudo": conteudo,
                "tokens_consumidos": tokens,
                "origem_medicao": origem_medicao,
                "modelo_usado": modelo,
                "timestamp_resposta": datetime.now(timezone.utc).isoformat(),
                "tokens_estimativa_local": estimar_tokens_tiktoken(prompt, contexto, conteudo),
                # Item 4 [TK-6]: headless litellm é processo isolado, sem
                # persistência de sessão — medição sem contaminação de contexto.
                "tipo_sessao": rotular_tipo_sessao('headless'),
            }

            print(f"✓ Resposta obtida via {modelo}")
            if tokens is not None:
                print(f"  Tokens consumidos: {tokens} (origem: {origem_medicao})")
            else:
                print(f"  Tokens: não disponível (origem: {origem_medicao})")
            est_local = resultado.get('tokens_estimativa_local')
            if est_local:
                print(f"  Estimativa local: {est_local['entrada']} entrada + {est_local['saida']} saída = {est_local['total']} tokens (tiktoken, offline)")
            else:
                print(f"  Estimativa local: indisponível (tiktoken não instalado)")

            return resultado

        except Exception as e:
            _traduzir_erro_litellm(e, modelo)
            print(f"✗ Erro ao chamar LLM ({modelo}) [tentativa {tentativa}/{max_tentativas}]: {type(e).__name__}: {e}")
            if tentativa < max_tentativas:
                time.sleep(3 * tentativa)
            else:
                return None


def _traduzir_erro_litellm(erro: Exception, modelo: str) -> None:
    """Traduz erros crus do litellm em LLMNaoConfiguradoException amigável.

    Captura os cenários reais que o usuário final encontra:
    - BadRequestError: modelo/provedor não configurado ou inválido
    - AuthenticationError: chave de API ausente ou inválida
    - ConnectionError/timeout: problemas de rede
    """
    nome_erro = type(erro).__name__
    texto_erro = str(erro)

    # BadRequestError — modelo/provedor mal configurado (o erro mais comum e feio)
    if nome_erro == 'BadRequestError':
        raise LLMNaoConfiguradoException(
            mensagem_usuario=(
                f"Provedor de IA não configurado corretamente para o modelo '{modelo}'. "
                "Configure LLM_MODEL e a chave do provedor no arquivo .env (veja .env.example)."
            ),
            detalhes_tecnicos=f"{nome_erro}: {texto_erro}"
        ) from erro

    # AuthenticationError — chave inválida ou ausente
    if nome_erro == 'AuthenticationError':
        raise LLMNaoConfiguradoException(
            mensagem_usuario=(
                "Chave de API do provedor de IA inválida ou ausente. "
                "Verifique a variável correspondente no arquivo .env (veja .env.example)."
            ),
            detalhes_tecnicos=f"{nome_erro}: {texto_erro}"
        ) from erro

    # Erros de rede / timeout
    if nome_erro in ('ConnectionError', 'Timeout', 'APIConnectionError'):
        raise LLMNaoConfiguradoException(
            mensagem_usuario=(
                "Não foi possível conectar ao provedor de IA. "
                "Verifique sua conexão com a internet e as credenciais no arquivo .env."
            ),
            detalhes_tecnicos=f"{nome_erro}: {texto_erro}"
        ) from erro


# =============================================================================
# AUTO-SELEÇÃO DE MODO
# =============================================================================

def detectar_modo_execucao() -> str:
    """
    Detecta qual modo deve ser usado:
    - 'delegado' se detecta uma ADE ativa (env vars de harness)
    - 'headless' se rodar standalone (CI/CD, script local, etc.)

    Critérios:
    1. Se --modo headless passado em sys.argv, força headless
    2. Se CLAUDECODE=1 (Claude Code) ou equivalente de outras ADEs, usa delegado
    3. Se variáveis de ADE não detectadas, headless (mas relata aviso)
    """

    # 1. Força explícita via argumento
    if '--modo' in sys.argv:
        idx = sys.argv.index('--modo')
        if idx + 1 < len(sys.argv):
            modo = sys.argv[idx + 1]
            if modo in ['delegado', 'headless']:
                return modo

    # 2. Força explícita via variável de ambiente
    modo_env = os.environ.get('AIDD_MODO')
    if modo_env in ['delegado', 'headless']:
        return modo_env

    # 3. Detectar ADE / Harness ativo na sessão
    ade_detectados = []

    # Claude Code
    if os.environ.get('CLAUDECODE') == '1':
        ade_detectados.append('Claude Code')

    # OpenCode
    if os.environ.get('OPENCODE') or os.environ.get('OPENCODE_SESSION') or os.environ.get('OPENCODE_CONFIG_DIR'):
        ade_detectados.append('OpenCode')

    # Antigravity
    if os.environ.get('ANTIGRAVITY_CLI') or os.environ.get('AGY_SESSION') or os.environ.get('ANTIGRAVITY_AGENT'):
        ade_detectados.append('Antigravity')

    # MimoCode
    if os.environ.get('MIMOCODE') or os.environ.get('MIMO_SESSION') or os.environ.get('MIMO_WORKSPACE'):
        ade_detectados.append('MimoCode')

    # Gemini CLI
    if os.environ.get('GEMINI_SESSION') or os.environ.get('GEMINI_CLI'):
        ade_detectados.append('Gemini CLI')

    # Checagem complementar de ambiente
    try:
        from .utils_fleet_discovery import detectar_via_ambiente
        outros = detectar_via_ambiente()
        for o in outros:
            nome_cap = o.capitalize()
            if nome_cap not in ade_detectados:
                ade_detectados.append(nome_cap)
    except ImportError:
        pass

    if ade_detectados:
        print(f"🔍 Detectado harness ativo na sessão: {', '.join(ade_detectados)}")
        return 'delegado'

    print("⚠️  Nenhuma ADE detectada via sessão ativa — usando Modo Headless")
    print("   (Configure LLM_MODEL e credencial para usar este modo)")
    return 'headless'


# =============================================================================
# INTERFACE UNIFICADA
# =============================================================================

def solicitar_llm(
    prompt: str,
    contexto: str,
    fase: str,
    modo: Optional[str] = None,
    modelo: Optional[str] = None,
    timeout_delegacao: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Interface unificada — escolhe automaticamente entre Delegado e Headless.

    Args:
        prompt: Texto do prompt (ex: "Analise este projeto...")
        contexto: Contexto executivo (ex: "Phase 2: Analisador de Ideia")
        fase: ID da fase (ex: "phase_02")
        modo: Força modo ('delegado', 'headless'). Se None, detecta automaticamente.
        modelo: Modelo a usar em headless (default: LLM_MODEL env var)
        timeout_delegacao: Timeout para modo delegado (segundos)

    Returns:
        Dict com keys: conteudo, tokens_consumidos, origem_medicao, modelo_usado, timestamp_resposta
        ou None se erro/timeout
    """

    modo = modo or detectar_modo_execucao()

    print(f"\n{'='*70}")
    print(f"Solicitação LLM — Modo: {modo.upper()}")
    print(f"Fase: {fase}")
    print(f"{'='*70}")

    if modo == 'delegado':
        return solicitar_llm_modo_delegado(prompt, contexto, fase, timeout=timeout_delegacao, modelo=modelo)
    else:
        return solicitar_llm_modo_headless(prompt, contexto, fase, modelo=modelo)


# =============================================================================
# TESTE RÁPIDO
# =============================================================================

if __name__ == '__main__':
    # Teste: tentar modo delegado com timeout curto
    resposta = solicitar_llm(
        prompt="Olá, você consegue me responder?",
        contexto="Teste do protocolo delegado",
        fase="phase_test",
        timeout_delegacao=2
    )

    if resposta:
        print(f"\n✓ Resposta: {resposta['conteudo'][:100]}...")
    else:
        print("\n✗ Nenhuma resposta recebida (esperado em teste sem ADE ativa)")
