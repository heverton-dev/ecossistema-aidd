#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de Escopo Preguiçoso e Poda de Contexto em Skills Locais VSA (Ticket 7).

Proporciona resolução, indexação seletiva sob demanda e poda de contexto
(token pruning) para skills locais de fatias verticais, aderindo às diretrizes
de aidd-agent-writing e aos limites de G_SKILL_FORMATO.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from scripts.exit_codes import ExitCode
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.exit_codes import ExitCode


@dataclass
class SkillMeta:
    """Metadados extraídos de forma preguiçosa de uma skill."""
    nome: str
    caminho: Path
    fatia: str
    descricao: str
    use_when: str
    linhas_totais: int
    requer_carregamento_profundo: bool = False


class GestorSkillsVSA:
    """Gestor de indexação preguiçosa e poda dinâmica de contexto para fatias VSA."""

    def __init__(self, raiz_repo: Optional[Path | str] = None):
        self.raiz_repo = Path(raiz_repo or os.getcwd()).resolve()
        self._indice_fatias: Dict[str, List[Path]] = {}
        self._cache_meta: Dict[str, SkillMeta] = {}

    def mapear_fatias_locais(self) -> Dict[str, List[Path]]:
        """Mapeia caminhos de skills pertencentes às fatias verticais."""
        self._indice_fatias.clear()
        padrao = self.raiz_repo / "modulos"
        if not padrao.exists():
            return {}

        for skill_md in padrao.glob("**/skills/**/SKILL.md"):
            partes = skill_md.relative_to(self.raiz_repo).parts
            fatia = partes[1] if len(partes) > 1 else "global"
            self._indice_fatias.setdefault(fatia, []).append(skill_md)

        # Adicionar catálogo de componentes compartilhados como fallback preguiçoso
        comp_skills = self.raiz_repo / "componentes" / "compartilhado" / "skills"
        if comp_skills.exists():
            for skill_md in comp_skills.glob("*/SKILL.md"):
                self._indice_fatias.setdefault("04-compartilhado", []).append(skill_md)

        return self._indice_fatias

    def resolver_meta_preguicoso(self, skill_path: Path) -> SkillMeta:
        """Lê estritamente o frontmatter sem carregar o corpo completo na memória."""
        chave = str(skill_path.resolve())
        if chave in self._cache_meta:
            return self._cache_meta[chave]

        nome = skill_path.parent.name
        descricao = ""
        use_when = ""
        linhas_totais = 0

        with open(skill_path, "r", encoding="utf-8", errors="replace") as f:
            linhas = f.readlines()
            linhas_totais = len(linhas)

            em_frontmatter = False
            fm_linhas = []
            for linha in linhas:
                if linha.strip() == "---":
                    if not em_frontmatter:
                        em_frontmatter = True
                        continue
                    else:
                        break
                if em_frontmatter:
                    fm_linhas.append(linha)

            fm_texto = "".join(fm_linhas)
            m_desc = re.search(r"description:\s*(.+)", fm_texto, re.IGNORECASE)
            if m_desc:
                descricao = m_desc.group(1).strip().strip('"').strip("'")
                m_uw = re.search(r"use when\s+(.+)", descricao, re.IGNORECASE)
                if m_uw:
                    use_when = m_uw.group(1).strip()

        partes = skill_path.relative_to(self.raiz_repo).parts
        fatia = partes[1] if len(partes) > 1 else "global"

        meta = SkillMeta(
            nome=nome,
            caminho=skill_path,
            fatia=fatia,
            descricao=descricao,
            use_when=use_when,
            linhas_totais=linhas_totais,
            requer_carregamento_profundo=linhas_totais > 150,
        )
        self._cache_meta[chave] = meta
        return meta

    def podar_contexto_skill(self, skill_path: Path, max_linhas: int = 150) -> str:
        """Aplica poda cirúrgica de contexto mantendo frontmatter, resumo e guardrails."""
        with open(skill_path, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()

        linhas = conteudo.splitlines()
        if len(linhas) <= max_linhas:
            return conteudo

        # Separar frontmatter e corpo
        m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*(?:\n|$)", conteudo, flags=re.DOTALL)
        if not m:
            return "\n".join(linhas[:max_linhas]) + "\n\n<!-- [CONTEXT PRUNED] Resto sob demanda -->"

        fm_bloco = m.group(0)
        corpo = conteudo[len(fm_bloco):]

        # Extrair seções críticas: Negative Guardrails, Failure Modes, Stopping Checklist
        secoes_preservar = ["## Negative Guardrails", "## Failure Modes", "## Stopping Checklist"]
        blocos_preservados: List[str] = []

        for sec in secoes_preservar:
            pos = corpo.find(sec)
            if pos != -1:
                proximo_h2 = corpo.find("\n## ", pos + len(sec))
                fim = proximo_h2 if proximo_h2 != -1 else len(corpo)
                blocos_preservados.append(corpo[pos:fim].strip())

        # Cabeçalho essencial do corpo (primeiros parágrafos até ~40 linhas)
        corpo_linhas = corpo.strip().splitlines()
        cabecalho_corpo = "\n".join(corpo_linhas[:40])

        corpo_podado = (
            cabecalho_corpo +
            "\n\n<!-- [CONTEXT-PRUNING ACTIVE: Referencias extensas omitidas. Consulte arquivos de scripts/ e docs/] -->\n\n" +
            "\n\n".join(blocos_preservados)
        )

        return fm_bloco + "\n" + corpo_podado


def obter_resumo_skills_fatia(fatia: str, raiz_repo: Optional[Path | str] = None) -> List[Dict[str, str]]:
    """Gera índice ultra-compacto de ponteiros de contexto para um subagente da fatia."""
    gestor = GestorSkillsVSA(raiz_repo)
    gestor.mapear_fatias_locais()

    caminhos = gestor._indice_fatias.get(fatia, [])
    ponteiros = []
    for p in caminhos:
        meta = gestor.resolver_meta_preguicoso(p)
        ponteiros.append({
            "skill": meta.nome,
            "use_when": meta.use_when or meta.descricao,
            "caminho": str(meta.caminho.relative_to(gestor.raiz_repo)).replace("\\", "/"),
            "linhas": str(meta.linhas_totais),
        })
    return ponteiros


MAPA_FATIAS_REL = Path("modulos/04-nucleo-compartilhado/contracts/MAPA-FATIAS.json")


def pastas_das_ferramentas(raiz_repo: Path | str) -> Dict[str, Path]:
    """Nome da ferramenta -> pasta, lido do MAPA-FATIAS (fonte única das fatias). Usado pelo components sync."""
    raiz = Path(raiz_repo)
    mapa = raiz / MAPA_FATIAS_REL
    if not mapa.is_file():
        return {}
    pastas: Dict[str, Path] = {}
    for info in json.loads(mapa.read_text(encoding="utf-8")).get("fatias", {}).values():
        base = raiz / info["caminho"]
        for ferramenta in info.get("ferramentas", []):
            pastas[Path(ferramenta).name] = base / ferramenta
    return pastas


def skills_da_ferramenta(pasta_ferramenta: Path | str) -> List[Path]:
    """Skills declaradas pela ferramenta: cada pasta com SKILL.md em <ferramenta>/skills/ (a fonte; as cópias de harness são destino)."""
    fonte = Path(pasta_ferramenta) / "skills"
    if not fonte.is_dir():
        return []
    return sorted(d for d in fonte.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
