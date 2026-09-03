#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLASH GEN — Mapeador de Comandos Slash para o Pipeline AIDD
aidd-project-generator v2.2

Mapeia comandos de IDE (/generate, /aidd-gen) para execução do pipeline,
integrando o IntentRouter para detecção de linguagem natural.

Uso:
    from scripts.commands.slash_gen import SlashCommandHandler

    handler = SlashCommandHandler()
    resultado = handler.processar("/generate rastreador de hábitos via CLI")
    # resultado = {'acao': 'gerar_projeto', 'ideia': 'rastreador de hábitos via CLI', ...}

Comandos suportados:
    /generate <ideia>   — Gera projeto (confiança 1.0)
    /aidd-gen <ideia>   — Gera projeto (confiança 1.0)
    /aidd <ideia>       — Gera projeto (confiança 0.95)
    /continue           — Continua pipeline interrompido
    /status             — Mostra status do pipeline
    /help               — Mostra ajuda dos comandos

Linguagem natural (via IntentRouter):
    "crie um sistema de [X]"  → gerar_projeto
    "quero um app para [X]"   → gerar_projeto
    "build a [X]"             → gerar_projeto
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Adicionar diretório de phases ao path para importar IntentRouter
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_PHASES_DIR = _SCRIPTS_DIR / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))

from utils_intent_router import IntentRouter, IntentResultado, extrair_argumentos


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ComandoSlash:
    """Representa um comando slash parseado."""
    comando: str          # '/generate', '/aidd-gen', etc.
    argumento: str = ''   # Texto após o comando
    raw: str = ''         # Texto original completo


@dataclass
class ResultadoSlash:
    """Resultado do processamento de um comando slash."""
    acao: str                                    # 'gerar_projeto', 'continuar_pipeline', 'ver_status', 'ajuda', 'desconhecido'
    ideia: Optional[str] = None                  # Ideia extraída (para gerar_projeto)
    confianca: float = 0.0                       # 0.0 a 1.0
    pasta_sugerida: Optional[str] = None         # Pasta sugerida para o projeto
    argumentos: Dict[str, Any] = field(default_factory=dict)
    comando_original: str = ''                   # Texto original
    padrao_matcheado: str = ''                   # Regex que fez match
    sucesso: bool = True                         # Se o parse foi bem-sucedido
    mensagem: str = ''                           # Mensagem para o usuário


# =============================================================================
# REGISTRY DE COMANDOS SLASH
# =============================================================================

# Mapeamento: comando → (regex_completo, acao, grupo_ideia, confianca)
COMANDOS_SLASH: List[tuple] = [
    # /generate <ideia>
    (r'^/generate\s+(.+)$', 'gerar_projeto', 1, 1.0),
    # /aidd-gen <ideia>
    (r'^/aidd-gen\s+(.+)$', 'gerar_projeto', 1, 1.0),
    # /aidd <ideia>
    (r'^/aidd\s+(.+)$', 'gerar_projeto', 1, 0.95),
    # /gen <ideia> (alias curto)
    (r'^/gen\s+(.+)$', 'gerar_projeto', 1, 0.95),
    # /continue
    (r'^/continue$', 'continuar_pipeline', None, 1.0),
    # /resume
    (r'^/resume$', 'continuar_pipeline', None, 1.0),
    # /status
    (r'^/status$', 'ver_status', None, 1.0),
    # /aidd-status
    (r'^/aidd-status$', 'ver_status', None, 1.0),
    # /help
    (r'^/help$', 'ajuda', None, 1.0),
    # /aidd-help
    (r'^/aidd-help$', 'ajuda', None, 1.0),
]


# =============================================================================
# TEXTO DE AJUDA
# =============================================================================

AJUDA_TEXTO = """
╔══════════════════════════════════════════════════════════════╗
║          AIDD PROJECT GENERATOR — COMANDOS SLASH            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  COMANDOS DIRETOS:                                           ║
║    /generate <ideia>    Gera projeto a partir da ideia       ║
║    /aidd-gen <ideia>    Alias para /generate                 ║
║    /aidd <ideia>        Alias para /generate                 ║
║    /gen <ideia>         Alias curto para /generate           ║
║    /continue            Continua pipeline interrompido       ║
║    /resume              Alias para /continue                 ║
║    /status              Mostra status do pipeline            ║
║    /help                Mostra esta ajuda                    ║
║                                                              ║
║  ARGUMENTOS OPCIONAIS:                                       ║
║    --pasta <caminho>    Define pasta de destino              ║
║    --implementar-codigo Gera código funcional (Fase 8)       ║
║    --interativo         Modo interativo na Fase 4            ║
║    --nao-interativo     Modo automático (padrão)             ║
║                                                              ║
║  LINGUAGEM NATURAL (Intent Router):                          ║
║    "crie um sistema de gerenciamento de tarefas"             ║
║    "quero um app para controlar finanças"                    ║
║    "build a REST API for managing books"                     ║
║    "preciso de um bot para Discord"                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


# =============================================================================
# SLASH COMMAND HANDLER
# =============================================================================

class SlashCommandHandler:
    """
    Handler principal para comandos slash do aidd-generator.

    Processa comandos como /generate, /aidd-gen e linguagem natural,
    convertendo-os em ações estruturadas para o pipeline.

    Integra com IntentRouter para fallback em linguagem natural.
    """

    def __init__(self):
        self._intent_router = IntentRouter()

    def parsear_comando(self, texto: str) -> Optional[ComandoSlash]:
        """
        Extrai o comando e argumento de um texto slash.

        Args:
            texto: Texto bruto do usuário

        Returns:
            ComandoSlash se for um comando direto, None caso contrário
        """
        if not texto or not isinstance(texto, str):
            return None

        texto_limpo = texto.strip()

        for padrao_regex, acao, grupo_ideia, confianca in COMANDOS_SLASH:
            match = re.search(padrao_regex, texto_limpo, re.IGNORECASE)
            if match:
                argumento = ''
                if grupo_ideia is not None:
                    try:
                        argumento = match.group(grupo_ideia).strip()
                    except IndexError:
                        pass

                # Extrair o comando literal (primeira palavra)
                comando = texto_limpo.split()[0] if texto_limpo.split() else texto_limpo

                return ComandoSlash(
                    comando=comando,
                    argumento=argumento,
                    raw=texto_limpo,
                )

        return None

    def processar(self, texto: str) -> ResultadoSlash:
        """
        Processa um texto do usuário e retorna a ação a executar.

        Fluxo:
        1. Tenta parsear como comando slash direto (/generate, /aidd-gen, etc.)
        2. Se não for comando direto, usa IntentRouter para linguagem natural
        3. Se nada detectar, retorna 'desconhecido'

        Args:
            texto: Texto do usuário (comando slash ou linguagem natural)

        Returns:
            ResultadoSlash com a ação, ideia e argumentos extraídos
        """
        if not texto or not isinstance(texto, str):
            return ResultadoSlash(
                acao='desconhecido',
                sucesso=False,
                mensagem='Texto vazio ou inválido',
                comando_original=str(texto),
            )

        texto_limpo = texto.strip()

        # 1. Tentar comando slash direto
        comando = self.parsear_comando(texto_limpo)
        if comando is not None:
            return self._processar_comando_direto(comando)

        # 2. Fallback: IntentRouter (linguagem natural)
        return self._processar_linguagem_natural(texto_limpo)

    def _processar_comando_direto(self, comando: ComandoSlash) -> ResultadoSlash:
        """Processa um comando slash já parseado."""
        for padrao_regex, acao, grupo_ideia, confianca in COMANDOS_SLASH:
            match = re.search(padrao_regex, comando.raw, re.IGNORECASE)
            if match:
                if acao == 'ajuda':
                    return ResultadoSlash(
                        acao='ajuda',
                        confianca=1.0,
                        comando_original=comando.raw,
                        padrao_matcheado=padrao_regex,
                        mensagem=AJUDA_TEXTO,
                    )

                ideia = None
                if grupo_ideia is not None:
                    try:
                        ideia = match.group(grupo_ideia).strip()
                        # Strip --arguments from ideia
                        ideia = re.sub(r'\s+--\S+.*$', '', ideia).strip()
                    except IndexError:
                        pass

                # Extrair argumentos opcionais
                args = extrair_argumentos(comando.raw)

                # Gerar pasta sugerida
                pasta = args.get('pasta')
                if not pasta and ideia:
                    nome_slug = re.sub(r'[^a-z0-9]+', '-', ideia.lower())[:50].strip('-')
                    pasta = f'../{nome_slug}'

                return ResultadoSlash(
                    acao=acao,
                    ideia=ideia,
                    confianca=confianca,
                    pasta_sugerida=pasta,
                    argumentos=args,
                    comando_original=comando.raw,
                    padrao_matcheado=padrao_regex,
                )

        # Não deveria chegar aqui, mas safety net
        return ResultadoSlash(
            acao='desconhecido',
            sucesso=False,
            mensagem=f'Comando não reconhecido: {comando.comando}',
            comando_original=comando.raw,
        )

    def _processar_linguagem_natural(self, texto: str) -> ResultadoSlash:
        """Processa texto em linguagem natural via IntentRouter."""
        resultado = self._intent_router.detectar_ou_fallback(texto)

        if not resultado.detectado:
            return ResultadoSlash(
                acao='desconhecido',
                sucesso=False,
                mensagem='Intenção não detectada. Use /help para ver comandos disponíveis.',
                comando_original=texto,
            )

        # Extrair argumentos
        args = extrair_argumentos(texto)

        # Gerar pasta sugerida
        pasta = args.get('pasta')
        if not pasta and resultado.ideia_extraida:
            nome_slug = re.sub(r'[^a-z0-9]+', '-', resultado.ideia_extraida.lower())[:50].strip('-')
            pasta = f'../{nome_slug}'

        return ResultadoSlash(
            acao=resultado.intencao,
            ideia=resultado.ideia_extraida,
            confianca=resultado.confianca,
            pasta_sugerida=pasta,
            argumentos=args,
            comando_original=texto,
            padrao_matcheado=resultado.padrao_matcheado,
        )

    def listar_comandos(self) -> List[str]:
        """Retorna lista de comandos slash disponíveis."""
        return [
            '/generate <ideia>',
            '/aidd-gen <ideia>',
            '/aidd <ideia>',
            '/gen <ideia>',
            '/continue',
            '/resume',
            '/status',
            '/help',
        ]


# =============================================================================
# HELPERS — Conversão para argumentos do pipeline
# =============================================================================

def slash_para_pipeline_args(texto: str) -> Dict[str, Any]:
    """
    Converte um comando slash (ou linguagem natural) em argumentos
    prontos para executar_pipeline().

    Args:
        texto: Comando do usuário

    Returns:
        Dict com 'ideia', 'pasta', 'implementar_codigo', 'interativo'
        ou vazio se não detectou intenção de gerar projeto.

    Exemplo:
        >>> args = slash_para_pipeline_args("/generate rastreador de hábitos --pasta ../habitos")
        >>> args['ideia']
        'rastreador de hábitos'
        >>> args['pasta']
        '../habitos'
    """
    handler = SlashCommandHandler()
    resultado = handler.processar(texto)

    if not resultado.sucesso or resultado.acao != 'gerar_projeto':
        return {}

    args = dict(resultado.argumentos)
    args['ideia'] = resultado.ideia

    if resultado.pasta_sugerida and 'pasta' not in args:
        args['pasta'] = resultado.pasta_sugerida

    return args


def formatar_resultado(resultado: ResultadoSlash) -> str:
    """
    Formata um ResultadoSlash para exibição ao usuário.

    Args:
        resultado: Resultado do processamento

    Returns:
        String formatada para output
    """
    if not resultado.sucesso:
        return f"❌ {resultado.mensagem}"

    if resultado.acao == 'ajuda':
        return resultado.mensagem

    if resultado.acao == 'gerar_projeto':
        linhas = [f"✅ Projeto detectado!"]
        linhas.append(f"   Ideia: {resultado.ideia}")
        linhas.append(f"   Confiança: {resultado.confianca:.0%}")
        if resultado.pasta_sugerida:
            linhas.append(f"   Pasta: {resultado.pasta_sugerida}")
        if resultado.argumentos.get('implementar_codigo'):
            linhas.append(f"   Modo: com implementação de código (Fase 8)")
        return '\n'.join(linhas)

    if resultado.acao == 'continuar_pipeline':
        return "✅ Continuando pipeline..."

    if resultado.acao == 'ver_status':
        return "📊 Status do pipeline: (implementar consulta ao PLANO-EXECUCAO-ESTRUTURADO.json)"

    return f"⚠️ Ação: {resultado.acao}"


# =============================================================================
# TESTE RÁPIDO
# =============================================================================

if __name__ == '__main__':
    print("=== Slash Command Handler — Teste Rápido ===\n")

    handler = SlashCommandHandler()

    testes = [
        # Comandos diretos
        "/generate rastreador de hábitos via CLI",
        "/aidd-gen sistema de gerenciamento de tarefas",
        "/aidd API REST para catálogo de livros",
        "/gen bot para Discord",
        "/generate app de finanças --pasta ../financas --implementar-codigo",
        "/continue",
        "/status",
        "/help",

        # Linguagem natural
        "crie um sistema de gerenciamento de tarefas com Python",
        "quero um app para controlar finanças pessoais",
        "build a habit tracker CLI with Python and SQLite",

        # Não detectável
        "oi",
    ]

    for texto in testes:
        resultado = handler.processar(texto)
        status = "✓" if resultado.sucesso else "✗"
        print(f"{status} '{texto[:60]}'")
        print(f"  → ação: {resultado.acao}, confiança: {resultado.confianca}")
        if resultado.ideia:
            print(f"  → ideia: {resultado.ideia[:60]}")
        print()

    # Teste de conversão para pipeline
    print("--- Conversão para Pipeline ---")
    args = slash_para_pipeline_args("/generate rastreador de hábitos --pasta ../habitos")
    print(f"  Args: {args}")

    print("\n✓ Slash Command Handler OK")
