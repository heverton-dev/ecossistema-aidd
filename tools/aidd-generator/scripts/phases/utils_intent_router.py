#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTILS: Intent Router — Detecção de Intenção para Zero Fricção
aidd-project-generator v2.1

Detecta automaticamente quando o usuário quer gerar um projeto,
eliminando a necessidade de decorar comandos específicos.

Uso:
    from utils_intent_router import IntentRouter

    router = IntentRouter()
    resultado = router.detectar("crie um sistema de gerenciamento de tarefas")
    if resultado.detectado:
        print(f"Intenção: {resultado.intencao}")  # 'gerar_projeto'
        print(f"Ideia: {resultado.ideia_extraida}")  # "sistema de gerenciamento de tarefas"
"""

import re
import sys
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class IntentResultado:
    """Resultado da detecção de intenção."""
    detectado: bool = False
    intencao: Optional[str] = None  # 'gerar_projeto', 'continuar_pipeline', 'ver_status'
    ideia_extraida: Optional[str] = None
    confianca: float = 0.0  # 0.0 a 1.0
    padrao_matcheado: str = ""
    argumentos_extras: Dict[str, Any] = None

    def __post_init__(self):
        if self.argumentos_extras is None:
            self.argumentos_extras = {}


# =============================================================================
# PADRÕES DE INTENÇÃO — Português e Inglês
# =============================================================================

# Cada padrão: (regex, intenção, grupo_captura_da_ideia, confiança)
PADROES_GERAR_PROJETO = [
    # Padrões diretos (alta confiança)
    (r'^/generate\s+(.+)$', 'gerar_projeto', 1, 1.0),
    (r'^/aidd-gen\s+(.+)$', 'gerar_projeto', 1, 1.0),
    (r'^/aidd\s+(.+)$', 'gerar_projeto', 1, 0.95),

    # Português — verbos de criação
    (r'(?:crie|criar|construa|construir|gere|gerar|faça|fazer|monte|montar)\s+(?:um|uma|o|a)?\s*(?:sistema|projeto|aplicação|app|ferramenta|api|site|plataforma|bot|cli|serviço)\s+(?:de|para|que|com)\s+(.+)', 'gerar_projeto', 1, 0.9),
    (r'(?:quero|preciso|necessito)\s+(?:de\s+)?(?:um|uma)?\s*(?:sistema|projeto|aplicação|app|ferramenta|api|site|plataforma|bot|cli|serviço)\s+(?:de|para|que|com)\s+(.+)', 'gerar_projeto', 1, 0.85),
    (r'(?:me\s+)?(?:crie|gere|construa|faça|monte)\s+(.+)', 'gerar_projeto', 1, 0.75),

    # Inglês — verbos de criação
    (r'(?:create|build|generate|make|develop)\s+(?:a|an|the)?\s*(?:system|project|application|app|tool|api|website|platform|bot|cli|service)\s+(?:for|that|with|to)\s+(.+)', 'gerar_projeto', 1, 0.9),
    (r'(?:i\s+)?(?:want|need)\s+(?:a|an)?\s*(?:system|project|application|app|tool|api|website|platform|bot|cli|service)\s+(?:for|that|with|to)\s+(.+)', 'gerar_projeto', 1, 0.85),
    (r'(?:i\s+)?(?:want|need)\s+(?:a|an)?\s+(.+)', 'gerar_projeto', 1, 0.7),
    (r'(?:build|create|make)\s+(?:me\s+)?(.+)', 'gerar_projeto', 1, 0.7),
]

PADROES_CONTINUAR = [
    (r'^/continue$', 'continuar_pipeline', None, 1.0),
    (r'^/resume$', 'continuar_pipeline', None, 1.0),
    (r'(?:continue|continuar|retomar|seguir)\s+(?:o\s+)?(?:pipeline|processo|geração)', 'continuar_pipeline', None, 0.8),
    (r'(?:próxima\s+fase|next\s+phase)', 'continuar_pipeline', None, 0.85),
]

PADROES_STATUS = [
    (r'^/status$', 'ver_status', None, 1.0),
    (r'^/aidd-status$', 'ver_status', None, 1.0),
    (r'(?:status|progresso|como\s+vai|onde\s+estamos)\s+(?:do\s+)?(?:pipeline|projeto|processo)', 'ver_status', None, 0.7),
]

# Padrões de injeção de componentes (Injetor Universal — skills/MCPs/rules/specs/configs)
# grupo 1 = palavra do tipo, grupo 2 = descrição/ideia do componente
PADROES_INJETAR = [
    (r'^/inject\s+(skill|habilidade|mcp|regra|rule|spec|especifica[cç][aã]o|config|configura[cç][aã]o)\s+(.+)', 1.0),
    (r'(?:crie|criar|adicione|adicionar|gere|gerar|monte|montar|nova|novo|quero|preciso)\s+(?:um|uma|de\s+um[a]?|o|a)?\s*'
     r'(skill|habilidade|mcp|regra|rule|spec|especifica[cç][aã]o|config|configura[cç][aã]o)\s+(?:de|para|sobre)\s+(.+)', 0.85),
]

_TIPO_PALAVRA_PARA_CANONICO: Dict[str, str] = {
    'skill': 'skill', 'habilidade': 'skill',
    'mcp': 'mcp',
    'regra': 'rule', 'rule': 'rule',
    'spec': 'spec', 'especificacao': 'spec', 'especificação': 'spec',
    'config': 'config', 'configuracao': 'config', 'configuração': 'config',
}


# =============================================================================
# INTENT ROUTER
# =============================================================================

class IntentRouter:
    """
    Router de intenção que detecta automaticamente quando o usuário
    quer gerar um projeto, continuar um pipeline, ou ver status.

    Elimina a necessidade de decorar comandos — linguagem natural funciona.
    """

    def __init__(self):
        self._padroes = (
            [(p, 'gerar_projeto') for p in PADROES_GERAR_PROJETO] +
            [(p, 'continuar_pipeline') for p in PADROES_CONTINUAR] +
            [(p, 'ver_status') for p in PADROES_STATUS]
        )

    def detectar(self, texto: str) -> IntentResultado:
        """
        Detecta a intenção do usuário a partir do texto.

        Args:
            texto: Texto do usuário (pode ser comando /generate ou linguagem natural)

        Returns:
            IntentResultado com intenção detectada, ideia extraída e confiança
        """
        if not texto or not isinstance(texto, str):
            return IntentResultado(detectado=False)

        texto_limpo = texto.strip()

        # Testar cada padrão
        for (padrao_regex, intencao, grupo_ideia, confianca), intencao_cat in self._padroes:
            match = re.search(padrao_regex, texto_limpo, re.IGNORECASE)
            if match:
                ideia = None
                if grupo_ideia is not None:
                    try:
                        ideia = match.group(grupo_ideia).strip()
                        # Strip --arguments from ideia (e.g. "/generate X --pasta Y")
                        ideia = re.sub(r'\s+--\S+.*$', '', ideia).strip()
                    except IndexError:
                        pass

                return IntentResultado(
                    detectado=True,
                    intencao=intencao_cat,
                    ideia_extraida=ideia,
                    confianca=confianca,
                    padrao_matcheado=padrao_regex,
                )

        return IntentResultado(detectado=False)

    def detectar_ou_fallback(self, texto: str) -> IntentResultado:
        """
        Detecta intenção; se não detectar, assume que o texto inteiro é a ideia
        (útil quando o usuário simplesmente descreve o que quer).
        """
        resultado = self.detectar(texto)
        if resultado.detectado:
            return resultado

        # Fallback: texto longo o suficiente para ser uma ideia de projeto
        texto_limpo = texto.strip()
        if len(texto_limpo) >= 20:
            return IntentResultado(
                detectado=True,
                intencao='gerar_projeto',
                ideia_extraida=texto_limpo,
                confianca=0.5,
                padrao_matcheado='(fallback: texto longo assumido como ideia)',
            )

        return IntentResultado(detectado=False)

    def detectar_injecao(self, texto: str) -> IntentResultado:
        """
        Detecta intenção de injetar um componente (skill/mcp/rule/spec/config)
        a partir de linguagem natural em PT-BR — usado pelo Injetor Universal
        de Componentes (`scripts/aidd_inject.py`).
        """
        return detectar_injecao(texto)


# =============================================================================
# INJEÇÃO DE COMPONENTES — Injetor Universal (skills/MCPs/rules/specs/configs)
# =============================================================================

def detectar_injecao(texto: str) -> IntentResultado:
    """
    Detecta intenção de injetar um componente a partir de linguagem natural.

    Exemplos:
        "crie uma skill de auditoria de dependências" → tipo='skill'
        "adicione um mcp de verificação de CVEs"       → tipo='mcp'
        "nova regra de não commitar segredos"          → tipo='rule'

    Returns:
        IntentResultado com intencao='injetar_componente' e
        argumentos_extras={'tipo': <tipo_canonico>} quando detectado.
    """
    if not texto or not isinstance(texto, str):
        return IntentResultado(detectado=False)

    texto_limpo = texto.strip()

    for padrao_regex, confianca in PADROES_INJETAR:
        match = re.search(padrao_regex, texto_limpo, re.IGNORECASE)
        if not match:
            continue

        tipo_palavra = match.group(1).lower()
        tipo = _TIPO_PALAVRA_PARA_CANONICO.get(tipo_palavra)
        if not tipo:
            continue

        ideia = match.group(2).strip()
        ideia = re.sub(r'\s+--\S+.*$', '', ideia).strip()

        return IntentResultado(
            detectado=True,
            intencao='injetar_componente',
            ideia_extraida=ideia,
            confianca=confianca,
            padrao_matcheado=padrao_regex,
            argumentos_extras={'tipo': tipo},
        )

    return IntentResultado(detectado=False)


def slug_a_partir_da_ideia(ideia: str, tamanho_max: int = 50) -> str:
    """Converte uma descrição livre em um slug kebab-case (para usar como 'nome')."""
    slug = re.sub(r'[^a-z0-9]+', '-', ideia.lower())[:tamanho_max].strip('-')
    return slug or 'componente'


# =============================================================================
# HELPERS — Extração de argumentos do texto
# =============================================================================

def extrair_argumentos(texto: str) -> Dict[str, Any]:
    """
    Extrai argumentos opcionais do texto do usuário.

    Exemplos:
        "crie um sistema X --pasta ../meu-projeto --implementar-codigo"
        → {'pasta': '../meu-projeto', 'implementar_codigo': True}
    """
    args = {}

    # --pasta <path>
    m = re.search(r'--pasta\s+(\S+)', texto)
    if m:
        args['pasta'] = m.group(1)

    # --implementar-codigo / --com-codigo
    if re.search(r'--(?:implementar-codigo|com-codigo|completo)', texto, re.IGNORECASE):
        args['implementar_codigo'] = True

    # --interativo
    if re.search(r'--interativo', texto, re.IGNORECASE):
        args['interativo'] = True

    # --nao-interativo / --auto
    if re.search(r'--(?:nao-interativo|auto)', texto, re.IGNORECASE):
        args['nao_interativo'] = True

    return args


def texto_para_pipeline_args(texto: str) -> Dict[str, Any]:
    """
    Converte texto do usuário em argumentos prontos para executar_pipeline().

    Returns:
        Dict com 'ideia', 'pasta', 'implementar_codigo', 'interativo'
        ou vazio se não detectou intenção de gerar projeto.
    """
    router = IntentRouter()
    resultado = router.detectar_ou_fallback(texto)

    if not resultado.detectado or resultado.intencao != 'gerar_projeto':
        return {}

    args = extrair_argumentos(texto)
    args['ideia'] = resultado.ideia_extraida

    # Pasta default: nome derivado da ideia
    if 'pasta' not in args:
        nome_slug = re.sub(r'[^a-z0-9]+', '-', resultado.ideia_extraida.lower())[:50].strip('-')
        args['pasta'] = f'../{nome_slug}'

    return args


# =============================================================================
# TESTE RÁPIDO
# =============================================================================

if __name__ == '__main__':
    print("=== Intent Router — Teste Rápido ===\n")

    router = IntentRouter()

    testes = [
        # Comandos diretos
        "/generate rastreador de hábitos via CLI",
        "/aidd-gen sistema de gerenciamento de tarefas",
        "/aidd API REST para catálogo de livros",
        "/continue",
        "/status",

        # Português natural
        "crie um sistema de gerenciamento de tarefas com Python",
        "quero um app para controlar finanças pessoais",
        "construa uma API REST para cadastro de clientes",
        "preciso de um bot para Discord que gerencie tarefas",
        "gere um projeto de e-commerce com Flask",

        # Inglês natural
        "build a habit tracker CLI with Python and SQLite",
        "I need a REST API for managing a book catalog",
        "create a task management system with FastAPI",

        # Não detectável (curto demais para fallback)
        "oi",
        "hello",
        "ajuda",
    ]

    for texto in testes:
        resultado = router.detectar(texto)
        if resultado.detectado:
            print(f"✓ '{texto[:60]}...'")
            print(f"  → {resultado.intencao} (confiança: {resultado.confianca})")
            if resultado.ideia_extraida:
                print(f"  → Ideia: {resultado.ideia_extraida[:80]}")
        else:
            print(f"✗ '{texto[:60]}' — não detectado")

    # Teste de extração de argumentos
    print("\n--- Extração de Argumentos ---")
    texto_com_args = "crie um sistema de tarefas --pasta ../meu-projeto --implementar-codigo"
    args = texto_para_pipeline_args(texto_com_args)
    print(f"  Input: {texto_com_args}")
    print(f"  Args: {args}")

    print("\n✓ Intent Router OK")
