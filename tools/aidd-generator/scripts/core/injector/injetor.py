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

import subprocess

_GERADORES = {
    "skill": scaffolds.gerar_skill,
    "rule": scaffolds.gerar_rule,
    "spec": scaffolds.gerar_spec,
    "config": scaffolds.gerar_config,
    "mcp": scaffolds.gerar_mcp,
}

CANONICAL_TEMPLATES: Dict[str, str] = {
    "skill": "componentes/aidd-generator/skills/{nome}/SKILL.md",
    "mcp": "componentes/aidd-generator/mcps/{nome}/server.py",
    "rule": "rules/{nome}.md",
    "spec": "componentes/aidd-generator/specs/{nome}.md",
    "config": "componentes/aidd-generator/config/{nome}.json",
    "command": "componentes/aidd-generator/comandos/{nome}.md",
    "hook": "componentes/aidd-generator/hooks/{nome}/hook.sh",
    "sub-agent": "componentes/aidd-generator/subagentes/{nome}.md",
    "script": "componentes/aidd-generator/scripts/{nome}.py",
}


def _default_ecossistema_root() -> Path:
    """Raiz real do monorepo ecossistema-aidd.

    Isolada numa funcao propria (em vez de inline em cada chamador) para que
    testes possam monkeypatchar este ponto unico e evitar gravar na arvore
    real do repositorio durante `pytest` (ver `conftest.py`).
    """
    return Path(__file__).resolve().parents[5]


def sincronizar_componente(
    tipo: str,
    ferramenta: str = "aidd-generator",
    ecossistema_root: Optional[Path] = None,
) -> int:
    """Invoca o sincronizador multi-harness do ecossistema AIDD."""
    if ecossistema_root is None:
        ecossistema_root = _default_ecossistema_root()

    script_ecossistema = ecossistema_root / "ecossistema.py"
    if script_ecossistema.exists():
        cmd = [
            sys.executable,
            str(script_ecossistema),
            "components",
            "sync",
            "--tipo",
            tipo,
            "--ferramenta",
            ferramenta,
        ]
        try:
            res = subprocess.run(cmd, cwd=str(ecossistema_root), capture_output=True, text=True)
            return res.returncode
        except Exception:
            pass

    try:
        scripts_dir = str(ecossistema_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import gestor_componentes
        gestor_componentes.sync(tipo=tipo, ferramenta=ferramenta)
        return 0
    except Exception:
        return 1



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
    sync_warning: Optional[str] = None


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

    gerador = _GERADORES.get(tipo)
    if gerador is not None:
        conteudo_padrao = gerador(nome, descricao)
    else:
        conteudo_padrao = f"# {nome}\n\n{descricao}\n"
    conteudo_principal = conteudo.get("principal") or conteudo_padrao

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

    # Grava na fonte canonica de componentes e dispara sync multi-harness
    if tipo in CANONICAL_TEMPLATES:
        ecossistema_root = _default_ecossistema_root()
        dest_canonico = ecossistema_root / CANONICAL_TEMPLATES[tipo].format(nome=nome)
        try:
            dest_canonico.parent.mkdir(parents=True, exist_ok=True)
            dest_canonico.write_text(conteudo_principal, encoding="utf-8")
        except Exception:
            pass

        if (root / "componentes").is_dir():
            dest_root_canonico = root / CANONICAL_TEMPLATES[tipo].format(nome=nome)
            try:
                dest_root_canonico.parent.mkdir(parents=True, exist_ok=True)
                dest_root_canonico.write_text(conteudo_principal, encoding="utf-8")
            except Exception:
                pass

    sync_code = sincronizar_componente(tipo, ferramenta="aidd-generator")
    sync_warning = (
        f"sincronizacao multi-harness retornou codigo {sync_code}"
        if sync_code != 0
        else None
    )

    resultado_sync = sincronizar(root, tipo, nome, descricao, rota.dest, rota.anchors)

    return ResultadoInjecao(
        sucesso=True,
        tipo=tipo,
        nome=nome,
        dest=rota.dest,
        arquivos_publicados=resultado_materializacao.arquivos_publicados,
        anchors_atualizados=resultado_sync.anchors_atualizados,
        sync_warning=sync_warning,
    )
