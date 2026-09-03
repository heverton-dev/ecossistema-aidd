#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INJETOR — Orquestrador do Injetor Universal de Componentes
aidd-generator — Fases 1-4 do plano mestre ORCA 3 (contrato, profiles,
deteccao/materializacao, sincronizacao), aplicadas a este projeto.

Encadeia: validacao de contrato -> deteccao de tipo (se omitido) ->
resolucao de rota -> geracao de scaffold -> materializacao transacional
-> sincronizacao de anchors globais.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR.parent.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent.parent))  # repo root, para `python -m` e imports relativos

from scripts.core.injector.contrato import validar_request
from scripts.core.injector.detector_camada import detectar_tipo
from scripts.core.injector.profiles_registry import (
    ProjetoNaoSuportadoError,
    TipoNaoSuportadoError,
    resolver_rota,
)
from scripts.core.injector.materializador import materializar
from scripts.core.injector.sincronizador_harness import sincronizar
from scripts.core.injector import scaffolds

_GERADORES = {
    "skill": scaffolds.gerar_skill,
    "rule": scaffolds.gerar_rule,
    "spec": scaffolds.gerar_spec,
    "config": scaffolds.gerar_config,
    "mcp": scaffolds.gerar_mcp,
}


@dataclass
class ResultadoInjecao:
    """Resultado consolidado de uma injecao de componente."""

    sucesso: bool
    tipo: Optional[str] = None
    nome: Optional[str] = None
    dest: Optional[str] = None
    arquivos_publicados: List[str] = field(default_factory=list)
    anchors_atualizados: List[str] = field(default_factory=list)
    erro: Optional[str] = None
    erros: List[str] = field(default_factory=list)


def injetar(
    nome: str,
    descricao: str,
    tipo: Optional[str] = None,
    alvo_projeto: str = "aidd-generator",
    conteudo: Optional[Dict[str, str]] = None,
    root: Optional[Path] = None,
    force: bool = False,
) -> ResultadoInjecao:
    """
    Executa o fluxo completo de injecao de um componente.

    Args:
        nome: slug do componente (kebab-case).
        descricao: descricao em linguagem natural.
        tipo: 'skill'|'mcp'|'rule'|'spec'|'config'. Se None, e detectado
            automaticamente a partir de `descricao` (heuristica + fallback LLM).
        alvo_projeto: projeto AIDD de destino (default 'aidd-generator').
        conteudo: overrides opcionais de conteudo (chave 'principal' sobrescreve
            o arquivo `dest`; demais chaves sao ignoradas por este projeto).
        root: raiz do projeto onde materializar (default: cwd).
        force: permite sobrescrever destinos ja existentes.

    Returns:
        ResultadoInjecao com `sucesso` e detalhes; em falha, `erro`/`erros`
        descrevem a causa e nenhum arquivo permanece no disco (rollback).
    """
    root = Path(root) if root is not None else Path.cwd()
    conteudo = conteudo or {}

    if tipo is None:
        deteccao = detectar_tipo(descricao)
        if not deteccao.tipo:
            return ResultadoInjecao(
                sucesso=False,
                erro="nao foi possivel detectar 'tipo' automaticamente — informe explicitamente",
            )
        tipo = deteccao.tipo

    payload = {
        "tipo": tipo,
        "nome": nome,
        "descricao": descricao,
        "alvo_projeto": alvo_projeto,
    }
    validacao = validar_request(payload)
    if not validacao.valido:
        return ResultadoInjecao(sucesso=False, erros=validacao.erros)

    try:
        rota = resolver_rota(alvo_projeto, tipo, nome)
    except (ProjetoNaoSuportadoError, TipoNaoSuportadoError) as exc:
        return ResultadoInjecao(sucesso=False, erro=str(exc))

    gerador = _GERADORES[tipo]
    conteudo_principal = conteudo.get("principal") or gerador(nome, descricao)

    arquivos = {rota.dest: conteudo_principal}
    for mirror in rota.mirrors:
        arquivos[mirror] = conteudo_principal

    resultado_materializacao = materializar(root, arquivos, force=force)
    if not resultado_materializacao.sucesso:
        return ResultadoInjecao(
            sucesso=False,
            tipo=tipo,
            nome=nome,
            erro=resultado_materializacao.erro,
        )

    resultado_sync = sincronizar(root, tipo, nome, descricao, rota.dest, rota.anchors)

    return ResultadoInjecao(
        sucesso=True,
        tipo=tipo,
        nome=nome,
        dest=rota.dest,
        arquivos_publicados=resultado_materializacao.arquivos_publicados,
        anchors_atualizados=resultado_sync.anchors_atualizados,
    )
