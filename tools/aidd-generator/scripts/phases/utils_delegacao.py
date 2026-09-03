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
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any


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


def extrair_json_resposta(texto: str) -> Any:
    """
    Extrai e decodifica JSON de uma resposta de LLM, mesmo se contiver
    markdown code fences (```json ... ```), texto explicativo antes ou depois,
    ou quebras de linha não escapadas dentro de strings.
    """
    if not texto or not isinstance(texto, str):
        raise ValueError("Texto vazio ou inválido para extração de JSON")

    texto_limpo = texto.strip()

    def _tentar_parse_sanitizado(s: str):
        # Substitui barras invertidas que não sejam escapes válidos de JSON por barra dupla
        s_sanitizado = re.sub(r'\\(?!["\\/bfnrtuU0-9])', r'\\\\', s)
        try:
            return json.loads(s_sanitizado, strict=False)
        except Exception:
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


# =============================================================================
# CONSTANTES
# =============================================================================

CACHE_DIR = Path(__file__).parent.parent / '.aidd' / 'cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT_DELEGACAO = 30  # segundos, aguardando resposta da ADE
INTERVALO_POLLING = 0.5  # segundos entre verificações


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
        """Escreve requisição em arquivo JSON no cache."""
        caminho = CACHE_DIR / f"_llm_request_{self.id}.json"
        dados = {
            "id": self.id,
            "fase": self.fase,
            "timestamp": self.timestamp_criado,
            "modelo_sugerido": self.modelo_sugerido,
            "contexto": self.contexto,
            "prompt": self.prompt,
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return caminho

    @staticmethod
    def aguardar_resposta(id_requisicao: str, timeout: int = TIMEOUT_DELEGACAO) -> Optional[Dict[str, Any]]:
        """Aguarda e lê resposta da ADE no arquivo JSON correspondente."""
        caminho_resposta = CACHE_DIR / f"_llm_response_{id_requisicao}.json"
        inicio = time.time()

        while time.time() - inicio < timeout:
            if caminho_resposta.exists():
                try:
                    with open(caminho_resposta, 'r', encoding='utf-8') as f:
                        dados = json.load(f)

                    # Validação básica
                    if "conteudo" in dados and "tokens_consumidos" in dados:
                        return dados

                except (json.JSONDecodeError, IOError):
                    # Arquivo não está pronto ainda, aguardar mais
                    pass

            time.sleep(INTERVALO_POLLING)

        # Timeout
        return None


# =============================================================================
# MODO DELEGADO (default)
# =============================================================================

def solicitar_llm_modo_delegado(
    prompt: str,
    contexto: str,
    fase: str,
    timeout: int = TIMEOUT_DELEGACAO,
    modelo: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Modo Delegado (default, universal):
    1. Escreve requisição em arquivo
    2. Aguarda resposta da ADE (Claude Code, Codex, Gemini CLI, etc.)
    3. Retorna resposta estruturada

    Não requer nenhuma credencial nova — usa a ADE já ativa.
    Se ADE não responder em tempo:
    - Se headless estiver configurado (LLM_MODEL no env), faz fallback automático.
    - Se headless não estiver configurado, retorna None (timeout com falha honesta).

    Returns:
        {
            "id": "abc12345",
            "conteudo": "resposta LLM",
            "tokens_consumidos": 1234,
            "modelo_usado": "claude-opus-5",
            "timestamp_resposta": "2026-08-30T10:30:00Z"
        }
        ou None se timeout sem headless configurado
    """
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
    print(f"  Aguardando resposta da ADE... (timeout {timeout}s)")

    # Aguardar resposta
    resposta = RequisicaoLLMDelegada.aguardar_resposta(req.id, timeout=timeout)

    if resposta is None:
        print(f"✗ Timeout ao aguardar resposta delegada (ID: {req.id})")
        if modelo or os.environ.get('LLM_MODEL'):
            print("⚠️  Fallback automático: caindo para Modo Headless após timeout do modo delegado...")
            return solicitar_llm_modo_headless(prompt, contexto, fase, modelo=modelo)
        return None

    print(f"✓ Resposta recebida:")
    print(f"  Modelo: {resposta.get('modelo_usado', 'desconhecido')}")
    print(f"  Tokens: {resposta.get('tokens_consumidos', '?')}")

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
            "modelo_usado": "claude-opus-5",
            "timestamp_resposta": "2026-08-30T10:30:00Z"
        }
        ou None se erro
    """
    try:
        import litellm
    except ImportError:
        print("✗ litellm não instalado. Use: python -m pip install litellm")
        return None

    modelo = modelo or os.environ.get('LLM_MODEL', 'claude-opus-5')

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

            resultado = {
                "conteudo": conteudo,
                "tokens_consumidos": tokens,
                "modelo_usado": modelo,
                "timestamp_resposta": datetime.now(timezone.utc).isoformat(),
            }

            print(f"✓ Resposta obtida via {modelo}")
            if tokens:
                print(f"  Tokens consumidos: {tokens}")

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

    # Força explícita via argumento
    if '--modo' in sys.argv:
        idx = sys.argv.index('--modo')
        if idx + 1 < len(sys.argv):
            modo = sys.argv[idx + 1]
            if modo in ['delegado', 'headless']:
                return modo

    # Detectar ADE ativa
    ade_detectado = False

    # Claude Code
    if os.environ.get('CLAUDECODE') == '1':
        print("🔍 Detectado: Claude Code (CLAUDECODE=1)")
        ade_detectado = True

    # Outros harnesses (extensível)
    # Adicione conforme suporte for adicionado para Codex, Gemini CLI, etc.

    if ade_detectado:
        return 'delegado'
    else:
        print("⚠️  Nenhuma ADE detectada — usando Modo Headless")
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
    timeout_delegacao: int = TIMEOUT_DELEGACAO
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
        Dict com keys: conteudo, tokens_consumidos, modelo_usado, timestamp_resposta
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
