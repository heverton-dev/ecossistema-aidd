#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTRATO: InjectorRequest — Validacao do payload de injecao de componentes
aidd-generator — Injetor Universal de Componentes

Valida requisicoes de injecao contra `schema_injector_request.json`
(JSON Schema Draft 2020-12) usando um validador manual leve — sem
dependencia externa (jsonschema nao esta em requirements.txt).

Cobre o subconjunto de regras usado pelo schema: type, required,
enum, pattern, minLength, maxLength, additionalProperties.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

TIPOS_VALIDOS = (
    "skill",
    "mcp",
    "rule",
    "spec",
    "config",
    "command",
    "hook",
    "sub-agent",
    "script",
)
PROJETOS_VALIDOS = (
    "aidd-generator",
    "aidd-master",
    "aidd-master-enterprise",
    "aidd-forge",
)

_SCHEMA_PATH = Path(__file__).resolve().parent / "schema_injector_request.json"
_NOME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass
class InjectorRequest:
    """Requisicao de injecao de componente, ja validada."""

    tipo: str
    nome: str
    descricao: str
    camada_alvo: Optional[str] = None
    conteudo: Dict[str, str] = field(default_factory=dict)
    alvo_projeto: str = "aidd-generator"


@dataclass
class ResultadoValidacao:
    """Resultado estruturado da validacao de um payload."""

    valido: bool
    erros: List[str] = field(default_factory=list)
    request: Optional[InjectorRequest] = None


def carregar_schema() -> Dict[str, Any]:
    """Carrega `schema_injector_request.json` do disco."""
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validar_request(payload: Dict[str, Any]) -> ResultadoValidacao:
    """
    Valida um payload de injecao contra o contrato universal.

    Args:
        payload: dicionario cru (ex.: vindo de CLI, IntentRouter ou JSON).

    Returns:
        ResultadoValidacao com `valido=False` e lista de `erros` estruturados
        quando o payload for incompleto ou incorreto; caso contrario
        `valido=True` com `request` populado.
    """
    erros: List[str] = []

    if not isinstance(payload, dict):
        return ResultadoValidacao(valido=False, erros=["payload deve ser um objeto JSON"])

    campos_permitidos = {"tipo", "nome", "descricao", "camada_alvo", "conteudo", "alvo_projeto"}
    extras = set(payload.keys()) - campos_permitidos
    if extras:
        erros.append(f"campos nao permitidos: {sorted(extras)}")

    for campo in ("tipo", "nome", "descricao"):
        if campo not in payload:
            erros.append(f"campo obrigatorio ausente: '{campo}'")

    tipo = payload.get("tipo")
    if tipo is not None:
        if not isinstance(tipo, str) or tipo not in TIPOS_VALIDOS:
            erros.append(f"'tipo' invalido: {tipo!r} — esperado um de {TIPOS_VALIDOS}")

    nome = payload.get("nome")
    if nome is not None:
        if not isinstance(nome, str):
            erros.append("'nome' deve ser string")
        elif not (3 <= len(nome) <= 80):
            erros.append("'nome' deve ter entre 3 e 80 caracteres")
        elif not _NOME_PATTERN.match(nome):
            erros.append(f"'nome' invalido: {nome!r} — use kebab-case (ex.: 'minha-skill')")

    descricao = payload.get("descricao")
    if descricao is not None:
        if not isinstance(descricao, str):
            erros.append("'descricao' deve ser string")
        elif not (8 <= len(descricao) <= 2000):
            erros.append("'descricao' deve ter entre 8 e 2000 caracteres")

    camada_alvo = payload.get("camada_alvo")
    if camada_alvo is not None and camada_alvo not in ("1", "2", "3", "4", "5"):
        erros.append(f"'camada_alvo' invalida: {camada_alvo!r} — esperado '1'..'5'")

    conteudo = payload.get("conteudo")
    if conteudo is not None:
        if not isinstance(conteudo, dict):
            erros.append("'conteudo' deve ser objeto")
        elif not all(isinstance(v, str) for v in conteudo.values()):
            erros.append("'conteudo' deve mapear string -> string")

    alvo_projeto = payload.get("alvo_projeto", "aidd-generator")
    if alvo_projeto not in PROJETOS_VALIDOS:
        erros.append(f"'alvo_projeto' invalido: {alvo_projeto!r} — esperado um de {PROJETOS_VALIDOS}")

    if erros:
        return ResultadoValidacao(valido=False, erros=erros)

    request = InjectorRequest(
        tipo=tipo,
        nome=nome,
        descricao=descricao,
        camada_alvo=camada_alvo,
        conteudo=dict(conteudo) if conteudo else {},
        alvo_projeto=alvo_projeto,
    )
    return ResultadoValidacao(valido=True, erros=[], request=request)
