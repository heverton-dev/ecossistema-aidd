# -*- coding: utf-8 -*-
"""
Contrato Estrutural e Manifesto de Módulos (VSA).
Dimensão D1: Contratos e Regras.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any


MACRO_MODULOS_CANONICOS = (
    "01-governanca-e-qualidade",
    "02-triade-motores",
    "03-plataforma-e-entrega",
    "04-nucleo-compartilhado",
)


@dataclass
class ModuloDef:
    nome: str
    descricao: str
    submodulos: List[str] = field(default_factory=list)


@dataclass
class ManifestoModulos:
    versao: str
    macro_modulos: Dict[str, ModuloDef]


def validar_manifesto_modulos(dados: Dict[str, Any]) -> ManifestoModulos:
    if not isinstance(dados, dict):
        raise ValueError("Dados do manifesto devem ser um dicionário.")

    versao = dados.get("versao")
    if not versao or not isinstance(versao, str):
        raise ValueError("Campo 'versao' obrigatório e deve ser string.")

    macro_raw = dados.get("macro_modulos")
    if not isinstance(macro_raw, dict):
        raise ValueError("Campo 'macro_modulos' obrigatório e deve ser dicionário.")

    presentes = set(macro_raw.keys())
    canonicos = set(MACRO_MODULOS_CANONICOS)

    faltantes = canonicos - presentes
    if faltantes:
        raise ValueError(f"Macro-módulos canônicos ausentes: {sorted(list(faltantes))}")

    extras = presentes - canonicos
    if extras:
        raise ValueError(f"Macro-módulos não canônicos detectados: {sorted(list(extras))}")

    modulos_validados: Dict[str, ModuloDef] = {}
    for nome, info in macro_raw.items():
        if not isinstance(info, dict):
            raise ValueError(f"Macro-módulo '{nome}' deve ser um dicionário.")
        desc = info.get("descricao", "")
        subs = info.get("submodulos", [])
        if not isinstance(subs, list):
            raise ValueError(f"Submódulos de '{nome}' devem ser uma lista.")
        modulos_validados[nome] = ModuloDef(nome=nome, descricao=desc, submodulos=subs)

    return ManifestoModulos(versao=versao, macro_modulos=modulos_validados)
