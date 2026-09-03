#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de Configuração de LLM e .env
web/config_manager.py — aidd-project-generator
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH_PADRAO = ROOT_DIR / '.env'

# Provedores suportados rigorosamente documentados em .env.example
PROVEDORES_SUPORTADOS = [
    {
        'id': 'groq',
        'nome': 'Groq (Llama 3.3 70B - Rápido / Camada Gratuita)',
        'modelo_padrao': 'groq/llama-3.3-70b-versatile',
        'env_key': 'GROQ_API_KEY',
        'requer_base_url': False,
        'placeholder_chave': 'gsk_...',
        'descricao': 'Opção recomendada para inicialização rápida com alta velocidade.'
    },
    {
        'id': 'nvidia_nim',
        'nome': 'NVIDIA NIM (Llama 3.3 70B Instruct - Gratuito)',
        'modelo_padrao': 'nvidia_nim/meta/llama-3.3-70b-instruct',
        'env_key': 'NVIDIA_NIM_API_KEY',
        'requer_base_url': False,
        'placeholder_chave': 'nvapi-...',
        'descricao': 'Excelente qualidade para design de arquitetura e análise crítica.'
    },
    {
        'id': 'openrouter',
        'nome': 'OpenRouter (Llama 3.3 70B Instruct Free)',
        'modelo_padrao': 'openrouter/meta-llama/llama-3.3-70b-instruct:free',
        'env_key': 'OPENROUTER_API_KEY',
        'requer_base_url': False,
        'placeholder_chave': 'sk-or-v1-...',
        'descricao': 'Roteador universal com acesso a modelos gratuitos e pagos.'
    },
    {
        'id': 'together_ai',
        'nome': 'TogetherAI (Llama 3.3 70B Turbo)',
        'modelo_padrao': 'together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo',
        'env_key': 'TOGETHERAI_API_KEY',
        'requer_base_url': False,
        'placeholder_chave': 'tok_... ou similar',
        'descricao': 'Alta taxa de throughput e estabilidade para geração.'
    },
    {
        'id': 'openai_compativel',
        'nome': 'OpenAI-compatível (Endpoint customizado)',
        'modelo_padrao': 'openai/gpt-4o-mini',
        'env_key': 'OPENAI_API_KEY',
        'requer_base_url': True,
        'placeholder_chave': 'sk-...',
        'descricao': 'Para usar OpenAI direto ou qualquer servidor local/remoto compatível (vLLM, Ollama, LM Studio).'
    }
]


def mascarar_chave(chave: Optional[str]) -> str:
    """Mascara a chave para exibição segura na interface (nunca expõe texto puro)."""
    if not chave:
        return ""
    chave_limpa = chave.strip()
    if len(chave_limpa) <= 8:
        return "••••••••"
    return f"{chave_limpa[:4]}••••••••{chave_limpa[-4:]}"


def ler_env_dict(caminho_env: Path) -> Dict[str, str]:
    """Lê um arquivo .env simples retornando dicionário de chave-valor."""
    vars_env: Dict[str, str] = {}
    if not caminho_env.exists():
        return vars_env

    try:
        conteudo = caminho_env.read_text(encoding='utf-8')
        for linha in conteudo.splitlines():
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue
            if '=' in linha:
                k, v = linha.split('=', 1)
                k = k.strip()
                v = v.strip()
                # Remove aspas se houver
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                vars_env[k] = v
    except Exception:
        pass
    return vars_env


def identificar_provedor_por_modelo(modelo: Optional[str]) -> Optional[Dict[str, Any]]:
    """Identifica qual provedor suportado corresponde ao prefixo do modelo."""
    if not modelo:
        return None
    modelo_lower = modelo.lower().strip()
    if modelo_lower.startswith('groq/'):
        return next((p for p in PROVEDORES_SUPORTADOS if p['id'] == 'groq'), None)
    if modelo_lower.startswith('nvidia_nim/') or 'nvidia' in modelo_lower:
        return next((p for p in PROVEDORES_SUPORTADOS if p['id'] == 'nvidia_nim'), None)
    if modelo_lower.startswith('openrouter/') or 'openrouter' in modelo_lower:
        return next((p for p in PROVEDORES_SUPORTADOS if p['id'] == 'openrouter'), None)
    if modelo_lower.startswith('together_ai/') or 'together' in modelo_lower:
        return next((p for p in PROVEDORES_SUPORTADOS if p['id'] == 'together_ai'), None)
    if modelo_lower.startswith('openai/'):
        return next((p for p in PROVEDORES_SUPORTADOS if p['id'] == 'openai_compativel'), None)
    return None


def obter_configuracao(caminho_env: Optional[Path] = None) -> Dict[str, Any]:
    """
    Retorna o estado de configuração atual do projeto.
    Carrega do arquivo .env e/ou variáveis de ambiente.
    """
    env_file = caminho_env or ENV_PATH_PADRAO
    vars_env = ler_env_dict(env_file)

    # Prioridade: valor do arquivo .env, fallback para os.environ
    llm_model = vars_env.get('LLM_MODEL') or os.environ.get('LLM_MODEL', '')
    claudecode = os.environ.get('CLAUDECODE') == '1'

    provedor = identificar_provedor_por_modelo(llm_model)
    provedor_id = provedor['id'] if provedor else 'groq'
    modelo_ativo = llm_model or (provedor['modelo_padrao'] if provedor else 'groq/llama-3.3-70b-versatile')

    # Identificar a chave associada
    env_key_name = provedor['env_key'] if provedor else 'GROQ_API_KEY'
    chave_valor = vars_env.get(env_key_name) or os.environ.get(env_key_name, '')
    base_url = vars_env.get('OPENAI_API_BASE') or os.environ.get('OPENAI_API_BASE', '')
    timeout = int(vars_env.get('LLM_TIMEOUT_SEGUNDOS') or os.environ.get('LLM_TIMEOUT_SEGUNDOS', '120'))

    # Está pronto se: CLAUDECODE=1 ativo OU (.env existe e tem LLM_MODEL + chave correspondente preenchida)
    tem_chave_preenchida = bool(chave_valor and len(chave_valor.strip()) > 3)
    tem_modelo_valido = bool(llm_model and len(llm_model.strip()) > 2)
    esta_configurado = claudecode or (tem_modelo_valido and tem_chave_preenchida)

    return {
        'esta_configurado': esta_configurado,
        'modo_delegado_ativo': claudecode,
        'provedor_ativo': provedor_id,
        'modelo_ativo': modelo_ativo,
        'tem_chave': tem_chave_preenchida,
        'chave_mascarada': mascarar_chave(chave_valor),
        'base_url': base_url,
        'timeout_segundos': timeout,
        'env_existe': env_file.exists(),
        'provedores_disponiveis': PROVEDORES_SUPORTADOS
    }


def salvar_configuracao(
    provedor_id: str,
    chave: str,
    modelo: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout_segundos: int = 120,
    caminho_env: Optional[Path] = None
) -> Tuple[bool, str]:
    """
    Grava ou atualiza o arquivo .env na raiz do projeto com o provedor escolhido.
    Também atualiza as variáveis no os.environ da sessão corrente.
    """
    env_file = caminho_env or ENV_PATH_PADRAO
    provedor = next((p for p in PROVEDORES_SUPORTADOS if p['id'] == provedor_id), None)
    if not provedor:
        return False, f"Provedor '{provedor_id}' não é suportado."

    modelo_final = (modelo or provedor['modelo_padrao']).strip()
    chave_limpa = chave.strip()

    # Se a chave veio vazia, tentar manter a chave já existente no arquivo .env
    if not chave_limpa:
        vars_atuais = ler_env_dict(env_file)
        chave_limpa = vars_atuais.get(provedor['env_key'], '')

    if not chave_limpa:
        return False, f"A chave de API para o provedor {provedor['nome']} é obrigatória."

    # Gerar conteúdo formatado compatível com .env.example
    linhas = [
        "# Gerado automaticamente pela Interface Web aidd-generator",
        "# NUNCA commite este arquivo no git.",
        "",
        "# --- Provedor Ativo ---",
        f"LLM_MODEL={modelo_final}",
        f"{provedor['env_key']}={chave_limpa}",
        "",
    ]

    if provedor['requer_base_url'] and base_url:
        linhas.append(f"OPENAI_API_BASE={base_url.strip()}")
        linhas.append("")

    linhas.extend([
        "# Timeout por chamada LLM headless (segundos)",
        f"LLM_TIMEOUT_SEGUNDOS={timeout_segundos}",
        ""
    ])

    conteudo = "\n".join(linhas)

    try:
        env_file.write_text(conteudo, encoding='utf-8')
    except Exception as e:
        return False, f"Erro ao escrever arquivo .env: {e}"

    # Atualizar variáveis de ambiente no processo atual
    os.environ['LLM_MODEL'] = modelo_final
    os.environ[provedor['env_key']] = chave_limpa
    if provedor['requer_base_url'] and base_url:
        os.environ['OPENAI_API_BASE'] = base_url.strip()
    os.environ['LLM_TIMEOUT_SEGUNDOS'] = str(timeout_segundos)

    # Carregar dotenv se disponível
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file, override=True)
    except Exception:
        pass

    return True, f"Configuração salva com sucesso para o provedor {provedor['nome']}!"


def testar_chave_llm(
    provedor_id: str,
    chave: str,
    modelo: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout_segundos: int = 15
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executa uma chamada mínima real de teste via litellm.
    Prompt mínimo: 'Diga apenas OK' (max_tokens=5).
    Retorna (sucesso, mensagem_amigavel, detalhes).
    """
    provedor = next((p for p in PROVEDORES_SUPORTADOS if p['id'] == provedor_id), None)
    if not provedor:
        return False, f"Provedor desconhecido: {provedor_id}", {}

    chave_limpa = chave.strip()
    if not chave_limpa:
        return False, "Chave de API não pode ser vazia.", {}

    modelo_final = (modelo or provedor['modelo_padrao']).strip()

    try:
        import litellm
    except ImportError:
        return False, "A biblioteca litellm não está instalada no ambiente Python.", {}

    # Configurar parâmetros da chamada
    kwargs: Dict[str, Any] = {
        'model': modelo_final,
        'messages': [{'role': 'user', 'content': 'Diga apenas: OK'}],
        'max_tokens': 10,
        'temperature': 0.1,
        'timeout': timeout_segundos,
        'api_key': chave_limpa
    }

    if provedor['requer_base_url'] and base_url:
        kwargs['api_base'] = base_url.strip()

    # Variável de ambiente temporária para provedores específicos
    env_backup = os.environ.get(provedor['env_key'])
    os.environ[provedor['env_key']] = chave_limpa

    try:
        resposta = litellm.completion(**kwargs)
        conteudo = resposta.choices[0].message.content.strip()
        tokens = resposta.usage.total_tokens if hasattr(resposta.usage, 'total_tokens') else 0

        return True, f"Chave validada com sucesso! Resposta do modelo: '{conteudo}'", {
            'resposta': conteudo,
            'tokens': tokens,
            'modelo': modelo_final,
            'provedor': provedor['nome']
        }
    except Exception as e:
        erro_str = str(e)
        tipo_erro = type(e).__name__

        # Tradução amigável dos erros comuns
        if 'AuthenticationError' in tipo_erro or '401' in erro_str or 'Invalid API Key' in erro_str:
            msg = f"Chave de API recusada pelo provedor ({provedor['nome']}). Verifique se a chave foi copiada corretamente."
        elif 'BadRequestError' in tipo_erro or 'Provider List' in erro_str:
            msg = f"Erro de requisição com o modelo '{modelo_final}'. Verifique se o nome do modelo é suportado por sua conta no provedor."
        elif 'RateLimitError' in tipo_erro or '429' in erro_str:
            msg = f"Limite de requisições ou créditos esgotados no provedor ({provedor['nome']})."
        elif 'Timeout' in tipo_erro or 'timed out' in erro_str.lower():
            msg = f"Tempo de resposta esgotado ({timeout_segundos}s). O serviço do provedor pode estar lento ou inacessível no momento."
        elif 'APIConnectionError' in tipo_erro or 'Connection' in tipo_erro:
            msg = "Não foi possível conectar ao servidor do provedor. Verifique sua conexão com a internet."
        else:
            msg = f"Falha ao validar chave com {provedor['nome']}: {erro_str}"

        return False, msg, {
            'tipo_erro': tipo_erro,
            'erro_bruto': erro_str,
            'modelo': modelo_final,
            'provedor': provedor['nome']
        }
    finally:
        # Restaurar estado da env var se necessário
        if env_backup is not None:
            os.environ[provedor['env_key']] = env_backup
        elif provedor['env_key'] in os.environ and not chave:
            del os.environ[provedor['env_key']]
