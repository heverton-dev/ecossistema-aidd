# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD — Catalogo Deterministico de Paletas de Design (Lei Inviolavel #11)
=============================================================================
Escolhe uma paleta de marca (cor primaria) para um projeto a partir do seu
nome/descricao/dominio de negocio — SEM LLM (Lei #1: Determinism First).

Por que determinístico em vez de LLM gerar a paleta: decisão explícita do
usuário na validação E2E do Fluxo 01 (18/09/2026) — cor de marca é escolha
entre boas opções, não raciocínio; um catálogo curado dá 0 custo de token,
0 dependência de rede/API e resultado 100% reprodutível. Esta sessão já
mostrou duas vezes que caminhos dependentes de LLM neste ecossistema falham
silenciosamente (protocolo delegado mockado — ver
docs/teste-end-to-end/17-09-2026_relatorio-testes-triade-fluxos-1-2-3.md).

Mecanismo: (1) casa palavras-chave do domínio/descrição contra o catálogo
"por nicho" — cada entrada tem uma cor pensada para aquele tipo de negócio;
(2) se nada bate, cai para um catálogo "genérico" indexado por hash SHA-256
do texto de identidade (nome/slug do projeto) — mesmo projeto sempre gera a
mesma paleta, projetos diferentes tendem a paletas diferentes.

O NEUTRO estrutural (cinza de fundo/texto/borda) fica FIXO em Tailwind
`slate` para todos os projetos — é a escolha real do padrão-ouro `proj_ctt`
(planos-ctt-app/frontend), e variar o neutro também multiplicaria a
complexidade de manutenção dos componentes sem ganho perceptível de
identidade visual (quem dá a identidade é a cor primária).
"""

from __future__ import annotations

import hashlib
import unicodedata
from typing import Any, Dict, List

# Cada entrada: nome de exibição, hex primário (saturado o bastante para
# texto branco em cima), hex do hover (mesmo tom ~12% mais escuro) e, para
# as "por nicho", as palavras-chave que a ativam.
_CATALOGO_POR_NICHO: List[Dict[str, Any]] = [
    {"nome": "Oceano Clínico", "primaria": "#0F766E", "primaria_hover": "#0B5D57",
     "keywords": ["saude", "clinica", "hospital", "medic", "odont", "consultorio", "bem-estar", "wellness", "terapia"]},
    {"nome": "Confiança Financeira", "primaria": "#1D4ED8", "primaria_hover": "#1E40AF",
     "keywords": ["financeiro", "banco", "fintech", "credito", "pagamento", "contabil", "investimento"]},
    {"nome": "Apetite Delivery", "primaria": "#EA580C", "primaria_hover": "#C2410C",
     "keywords": ["delivery", "lanchonete", "restaurante", "comida", "cardapio", "food", "gastronomia"]},
    {"nome": "Aço Industrial", "primaria": "#475569", "primaria_hover": "#334155",
     "keywords": ["industrial", "b2b", "fabrica", "manufatura", "logistica", "distribuicao", "atacado"]},
    {"nome": "Saber Educacional", "primaria": "#7C3AED", "primaria_hover": "#6D28D9",
     "keywords": ["educacao", "escola", "curso", "ensino", "universidade", "aluno", "aprendizagem"]},
    {"nome": "Raiz Sustentável", "primaria": "#15803D", "primaria_hover": "#166534",
     "keywords": ["energia", "solar", "sustentab", "ambiental", "reciclagem", "verde", "ecologic"]},
    {"nome": "Toque Estético", "primaria": "#DB2777", "primaria_hover": "#BE185D",
     "keywords": ["beleza", "estetica", "salao", "moda", "cosmetico", "spa"]},
    {"nome": "Alicerce Imobiliário", "primaria": "#B45309", "primaria_hover": "#92400E",
     "keywords": ["imobiliaria", "imovel", "construcao", "arquitetura", "engenharia civil"]},
    {"nome": "Rota Logística", "primaria": "#0369A1", "primaria_hover": "#075985",
     "keywords": ["frota", "transporte", "entrega", "roteirizacao", "encomenda", "correios"]},
    {"nome": "Pacto Jurídico", "primaria": "#1E3A8A", "primaria_hover": "#1E293B",
     "keywords": ["juridico", "advocacia", "advogado", "contrato", "legal", "compliance"]},
    {"nome": "Colheita Rural", "primaria": "#65A30D", "primaria_hover": "#4D7C0F",
     "keywords": ["agro", "agricultura", "fazenda", "rural", "pecuaria", "plantacao"]},
    {"nome": "Trilha de Viagem", "primaria": "#0891B2", "primaria_hover": "#0E7490",
     "keywords": ["turismo", "viagem", "hotel", "hospedagem", "reserva", "passeio"]},
]

_CATALOGO_GENERICO: List[Dict[str, str]] = [
    {"nome": "Índigo Padrão", "primaria": "#4F46E5", "primaria_hover": "#4338CA"},
    {"nome": "Esmeralda Padrão", "primaria": "#059669", "primaria_hover": "#047857"},
    {"nome": "Âmbar Padrão", "primaria": "#D97706", "primaria_hover": "#B45309"},
    {"nome": "Rosa Padrão", "primaria": "#E11D48", "primaria_hover": "#BE123C"},
    {"nome": "Ciano Padrão", "primaria": "#0891B2", "primaria_hover": "#0E7490"},
    {"nome": "Violeta Padrão", "primaria": "#7C3AED", "primaria_hover": "#6D28D9"},
    {"nome": "Azul Padrão", "primaria": "#2563EB", "primaria_hover": "#1D4ED8"},
    {"nome": "Teal Padrão", "primaria": "#0D9488", "primaria_hover": "#0F766E"},
    {"nome": "Laranja Padrão", "primaria": "#EA580C", "primaria_hover": "#C2410C"},
    {"nome": "Fúcsia Padrão", "primaria": "#C026D3", "primaria_hover": "#A21CAF"},
]

NEUTRO_PADRAO = "slate"


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return sem_acento.lower()


def escolher_paleta(texto_identidade: str, dominio: str = "") -> Dict[str, str]:
    """Escolhe deterministicamente uma paleta para o projeto.

    Args:
        texto_identidade: nome/slug/descricao do projeto (usado para o hash
            de fallback — mesmo texto sempre gera a mesma paleta).
        dominio: dominio de negocio livre (ex.: "saude", "delivery") — casado
            contra as palavras-chave do catalogo por nicho antes do fallback.

    Returns:
        dict com `nome`, `primaria` (hex), `primaria_hover` (hex), `neutro`
        (nome da familia de cinza Tailwind, sempre "slate" hoje).
    """
    texto_busca = _normalizar(f"{dominio} {texto_identidade}")
    for entrada in _CATALOGO_POR_NICHO:
        if any(kw in texto_busca for kw in entrada["keywords"]):
            return {
                "nome": entrada["nome"], "primaria": entrada["primaria"],
                "primaria_hover": entrada["primaria_hover"], "neutro": NEUTRO_PADRAO,
            }

    texto_hash = texto_identidade or dominio or "aidd-projeto"
    indice = int(hashlib.sha256(texto_hash.encode("utf-8")).hexdigest(), 16) % len(_CATALOGO_GENERICO)
    entrada = _CATALOGO_GENERICO[indice]
    return {
        "nome": entrada["nome"], "primaria": entrada["primaria"],
        "primaria_hover": entrada["primaria_hover"], "neutro": NEUTRO_PADRAO,
    }
