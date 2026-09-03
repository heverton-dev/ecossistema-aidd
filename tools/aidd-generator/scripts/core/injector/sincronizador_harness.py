#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZADOR DE HARNESS — Atualizacao de anchors globais pos-materializacao
aidd-generator — Injetor Universal de Componentes

Depois que `materializador.py` publica os arquivos fisicos de um componente,
este modulo atualiza os "anchors" definidos no profile (`profiles_registry`):
sempre a tabela em `AGENTS.md`; adicionalmente `HARNESS-COMPAT.json` para
MCPs e `PLANO-EXECUCAO-ESTRUTURADO.json` para specs. Todas as escritas sao
aditivas — nenhuma estrutura pre-existente e removida ou sobrescrita.
"""

import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

_MARCADOR_INICIO = "<!-- INJECTOR:TABELA:INICIO -->"
_MARCADOR_FIM = "<!-- INJECTOR:TABELA:FIM -->"


@dataclass
class ResultadoSincronizacao:
    """Resultado da sincronizacao de anchors para um componente injetado."""

    anchors_atualizados: List[str] = field(default_factory=list)


def sincronizar(root: Path, tipo: str, nome: str, descricao: str, dest: str, anchors: List[str]) -> ResultadoSincronizacao:
    """
    Atualiza os anchors globais listados para refletir um componente
    ja materializado com sucesso.

    Args:
        root: diretorio raiz do projeto.
        tipo: tipo do componente injetado.
        nome: slug do componente.
        descricao: descricao do componente.
        dest: caminho relativo do arquivo principal materializado.
        anchors: lista de anchors a atualizar (subconjunto de
            'AGENTS.md', 'HARNESS-COMPAT.json', 'PLANO-EXECUCAO-ESTRUTURADO.json').

    Returns:
        ResultadoSincronizacao com os anchors efetivamente atualizados.
    """
    root = Path(root)
    atualizados: List[str] = []

    if "AGENTS.md" in anchors:
        if _atualizar_agents_md(root, tipo, nome, descricao, dest):
            atualizados.append("AGENTS.md")

    if "HARNESS-COMPAT.json" in anchors:
        if _atualizar_harness_compat(root, tipo, nome, descricao, dest):
            atualizados.append("HARNESS-COMPAT.json")

    if "PLANO-EXECUCAO-ESTRUTURADO.json" in anchors:
        if _atualizar_plano_execucao(root, tipo, nome, descricao, dest):
            atualizados.append("PLANO-EXECUCAO-ESTRUTURADO.json")

    return ResultadoSincronizacao(anchors_atualizados=atualizados)


def _atualizar_agents_md(root: Path, tipo: str, nome: str, descricao: str, dest: str) -> bool:
    """Insere uma linha na tabela de 'Registro de Componentes Injetados'."""
    caminho = root / "AGENTS.md"
    if not caminho.exists():
        return False

    texto = caminho.read_text(encoding="utf-8")
    if _MARCADOR_INICIO not in texto or _MARCADOR_FIM not in texto:
        return False

    data = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    descricao_curta = descricao.strip().replace("\n", " ")
    if len(descricao_curta) > 100:
        descricao_curta = descricao_curta[:97] + "..."
    linha = f"| {tipo} | `{nome}` | `{dest}` | {data} | {descricao_curta} |"

    inicio = texto.index(_MARCADOR_INICIO) + len(_MARCADOR_INICIO)
    fim = texto.index(_MARCADOR_FIM)
    bloco_atual = texto[inicio:fim]

    novo_bloco = bloco_atual.rstrip("\n") + "\n" + linha + "\n"
    novo_texto = texto[:inicio] + novo_bloco + texto[fim:]
    caminho.write_text(novo_texto, encoding="utf-8")
    return True


def _atualizar_harness_compat(root: Path, tipo: str, nome: str, descricao: str, dest: str) -> bool:
    """Registra o componente em `componentes_injetados` (chave aditiva)."""
    caminho = root / "HARNESS-COMPAT.json"
    if not caminho.exists():
        return False

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    componentes = dados.setdefault("componentes_injetados", [])
    componentes.append({
        "id": uuid.uuid4().hex[:12],
        "tipo": tipo,
        "nome": nome,
        "descricao": descricao,
        "dest": dest,
        "data_injecao": datetime.now(timezone.utc).isoformat(),
    })

    dados.setdefault("metadata", {})["ultima_atualizacao"] = datetime.now(timezone.utc).isoformat()

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return True


def _atualizar_plano_execucao(root: Path, tipo: str, nome: str, descricao: str, dest: str) -> bool:
    """Acrescenta uma etapa concluida em `etapas` — nao mexe em `proxima_acao`."""
    caminho = root / "PLANO-EXECUCAO-ESTRUTURADO.json"
    if not caminho.exists():
        return False

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    etapas = dados.setdefault("etapas", [])
    etapa_id = f"injecao-{tipo}-{nome}"
    if any(e.get("id") == etapa_id for e in etapas if isinstance(e, dict)):
        return True  # idempotente — ja registrada, mas o anchor esta consistente

    etapas.append({
        "id": etapa_id,
        "nome": f"Injecao de componente: {tipo} '{nome}'",
        "descricao": descricao,
        "arquivos_afetados": [dest],
        "decisoes": ["Materializado via Injetor Universal de Componentes (scripts/core/injector/)"],
        "criterios_sucesso": ["Arquivo materializado", "Anchors sincronizados", "G_INJECT.py verde"],
        "status": "✅ COMPLETO",
        "data_conclusao": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "commit": None,
        "proxima_etapa": None,
    })

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return True
