# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Injetor Universal: Detector Híbrido de Camada
=============================================================================
Converte um pedido em linguagem natural PT-BR ("crie uma skill de
cibersegurança") ou argumentos explícitos de CLI em um InjectorRequest
completo: infere 'tipo' e 'nome' quando não fornecidos explicitamente,
resolve 'camada_alvo' via a matriz de perfis, e preenche 'descricao'.

Estratégia "híbrida" desta implementação: heurística determinística por
palavra-chave primeiro; se a heurística não conseguir identificar o 'tipo'
com confiança, o fallback é DELEGADO ao chamador (Result.fail com
codigo='TIPO_AMBIGUO' e a lista de candidatos) — nunca um palpite mudo.
Isso é deliberado: o motor é 100% determinístico (ver AGENTS.md, Regra
G_QUALIDADE) e não invoca um LLM para "adivinhar" o tipo silenciosamente.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

try:
    from result import Result
except ImportError:
    from core.result import Result

try:
    from profiles_registry import TIPOS_VALIDOS, obter_camada_alvo
except ImportError:
    from core.profiles_registry import TIPOS_VALIDOS, obter_camada_alvo


_PROJETO_PADRAO = "aidd-master"

# Palavras-chave PT-BR/EN que identificam cada 'tipo' de componente.
_PALAVRAS_CHAVE: Dict[str, Tuple[str, ...]] = {
    "skill": ("skill", "habilidade", "habilidades"),
    "mcp": ("mcp", "model context protocol", "ferramenta mcp", "ferramentas mcp"),
    "rule": ("regra", "regras", "rule", "rules"),
    "spec": ("spec", "especificacao", "especificação", "especificações"),
    "config": ("config", "configuracao", "configuração", "configuracoes"),
    "agent": ("agente", "agentes", "agent", "agents"),
}

_VERBOS_INJECAO = (
    "adicione", "adicionar", "crie", "criar", "cria",
    "nova", "novo", "gere", "gerar", "instale", "instalar",
)


def _normalizar(texto: str) -> str:
    """Remove acentos e baixa a caixa, preservando espaços e hífens."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.lower().strip()


def _slugificar(texto: str) -> str:
    """Converte texto livre em slug kebab-case válido para 'nome'."""
    norm = _normalizar(texto)
    norm = re.sub(r"[^a-z0-9\s-]", "", norm)
    norm = re.sub(r"[\s_]+", "-", norm).strip("-")
    norm = re.sub(r"-{2,}", "-", norm)
    return norm


def parece_pedido_de_injecao(texto: str) -> bool:
    """Reconhecimento amplo: o texto tem forma de pedido de injeção de componente?"""
    norm = _normalizar(texto)
    tem_verbo = any(v in norm for v in _VERBOS_INJECAO)
    tem_tipo = any(any(p in norm for p in palavras) for palavras in _PALAVRAS_CHAVE.values())
    return tem_verbo and tem_tipo


def detectar_tipo(texto: str) -> Optional[str]:
    """Heurística determinística por palavra-chave. Retorna None se ambíguo/não encontrado."""
    norm = _normalizar(texto)
    candidatos = [tipo for tipo, palavras in _PALAVRAS_CHAVE.items() if any(p in norm for p in palavras)]
    if len(candidatos) == 1:
        return candidatos[0]
    return None


def _extrair_nome_e_descricao(texto: str, tipo: str) -> Tuple[str, str]:
    """Extrai o slug de 'nome' e a 'descricao' a partir do texto livre.

    Remove verbo de injeção + palavra-chave do tipo + preposição "de", e usa
    o restante tanto para o slug ('nome') quanto para a 'descricao' completa.
    """
    norm = _normalizar(texto)
    for verbo in sorted(_VERBOS_INJECAO, key=len, reverse=True):
        norm = re.sub(rf"\b{re.escape(verbo)}\b", " ", norm)
    for palavra in sorted(_PALAVRAS_CHAVE[tipo], key=len, reverse=True):
        norm = re.sub(rf"\b{re.escape(palavra)}\b", " ", norm)
    norm = re.sub(r"^\s*(um|uma|de|do|da|para)\s+", " ", norm)
    norm = re.sub(r"\bde\b", " ", norm, count=1)
    resto = norm.strip()
    resto = re.sub(r"\s{2,}", " ", resto)

    nome = _slugificar(resto) or "componente-sem-nome"
    descricao = texto.strip()
    return nome, descricao


def detectar_de_texto(texto: str, alvo_projeto: str = _PROJETO_PADRAO) -> Result:
    """Constrói um InjectorRequest completo a partir de uma frase em PT-BR."""
    tipo = detectar_tipo(texto)
    if tipo is None:
        candidatos = [
            t for t, palavras in _PALAVRAS_CHAVE.items() if any(p in _normalizar(texto) for p in palavras)
        ]
        return Result.fail(
            "Não foi possível inferir o 'tipo' do componente com confiança a partir do texto.",
            codigo="TIPO_AMBIGUO",
            detalhes={"texto": texto, "candidatos": candidatos, "tipos_validos": list(TIPOS_VALIDOS)},
        )

    nome, descricao = _extrair_nome_e_descricao(texto, tipo)
    return construir_request(tipo=tipo, nome=nome, descricao=descricao, alvo_projeto=alvo_projeto)


def construir_request(
    tipo: str,
    nome: str,
    descricao: str,
    alvo_projeto: str = _PROJETO_PADRAO,
    conteudo: Optional[str] = None,
) -> Result:
    """Constrói e enriquece (com 'camada_alvo') um InjectorRequest a partir de campos explícitos."""
    if tipo not in TIPOS_VALIDOS:
        return Result.fail(
            f"'tipo' inválido: {tipo!r}. Valores aceitos: {', '.join(TIPOS_VALIDOS)}",
            codigo="TIPO_INVALIDO",
        )

    nome_slug = _slugificar(nome) or nome
    camada_alvo = obter_camada_alvo(alvo_projeto, tipo)

    payload: Dict[str, Any] = {
        "tipo": tipo,
        "nome": nome_slug,
        "descricao": descricao,
        "alvo_projeto": alvo_projeto,
        "camada_alvo": camada_alvo,
    }
    if conteudo:
        payload["conteudo"] = conteudo

    return Result.ok(payload)
