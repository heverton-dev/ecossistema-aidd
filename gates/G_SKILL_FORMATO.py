#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_SKILL_FORMATO
=============================================================================
Confere o formato de cada skill da fonte unica contra
docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md (secoes 5.1, 5.2 e 5.3).

Escopo: componentes/*/skills/<pasta>/SKILL.md

Violacoes (codigo impresso no relatorio):
  SEM_FRONTMATTER          SKILL.md sem bloco --- com name e description
  FRONTMATTER_YAML_INVALIDO bloco --- que nao e YAML valido (ex.: "Slash: /x" sem aspas)
  NOME_DIFERENTE_DA_PASTA  name do frontmatter diferente do nome da pasta
  NOME_FORA_DO_PADRAO      name fora de ^[a-z0-9]+(-[a-z0-9]+)*$ ou acima de 64 caracteres
  SUFIXO_RUNNER            name termina em -runner (o nome diz o que faz, nao como roda)
  SEM_USE_WHEN             description sem "Use when" (o gatilho de quando usar)
  CORPO_ACIMA_DE_450       corpo (depois do frontmatter) com mais de 450 linhas
  SEM_PREFIXO_AIDD         skill nossa sem o prefixo aidd- (terceiro = declarado em
                           gates/dependencias_externas.json)

Deteccao 100% deterministica (leitura de arquivo e regex), zero LLM.

Uso:
  python gates/G_SKILL_FORMATO.py [--raiz <repo>] [--aviso]
      exit 0 = nenhuma violacao (ou --aviso: violacoes so impressas)
      exit 1 = ao menos 1 violacao
"""

import argparse
import glob
import os
import re
import sys
from typing import List, Optional, Tuple

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
import gestor_dependencias  # noqa: E402

PADRAO_NOME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NOME = 64
MAX_LINHAS_CORPO = 450
PREFIXO_NOSSO = "aidd-"


def ler_frontmatter(conteudo: str) -> Tuple[Optional[dict], str, Optional[str]]:
    """Retorna (frontmatter, corpo, erro_yaml). frontmatter e None se ausente ou invalido."""
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*(?:\n|$)", conteudo, flags=re.DOTALL)
    if not m:
        return None, conteudo, None
    try:
        dados = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        return None, conteudo[m.end():], str(exc).splitlines()[0]
    return (dados if isinstance(dados, dict) else None), conteudo[m.end():], None


def auditar_skill(skill_md: str, terceiros: set) -> List[str]:
    """Lista de violacoes 'CODIGO: detalhe' de um SKILL.md."""
    pasta = os.path.basename(os.path.dirname(skill_md))
    with open(skill_md, "r", encoding="utf-8") as f:
        fm, corpo, erro_yaml = ler_frontmatter(f.read())
    if erro_yaml:
        return [f"FRONTMATTER_YAML_INVALIDO: {erro_yaml}"]
    if not fm or not fm.get("name") or not fm.get("description"):
        return ["SEM_FRONTMATTER: faltam name e/ou description"]

    nome = str(fm["name"])
    descricao = str(fm["description"])
    violacoes = []
    if nome != pasta:
        violacoes.append(f"NOME_DIFERENTE_DA_PASTA: name '{nome}' != pasta '{pasta}'")
    if not PADRAO_NOME.match(nome) or len(nome) > MAX_NOME:
        violacoes.append(f"NOME_FORA_DO_PADRAO: '{nome}'")
    if nome.endswith("-runner"):
        violacoes.append(f"SUFIXO_RUNNER: '{nome}'")
    if "use when" not in descricao.lower():
        violacoes.append("SEM_USE_WHEN: a description nao diz quando usar")
    linhas = len(corpo.splitlines())
    if linhas > MAX_LINHAS_CORPO:
        violacoes.append(f"CORPO_ACIMA_DE_450: {linhas} linhas")
    if nome not in terceiros and pasta not in terceiros and not nome.startswith(PREFIXO_NOSSO):
        violacoes.append(f"SEM_PREFIXO_AIDD: '{nome}'")
    return violacoes


def auditar(raiz: str) -> List[Tuple[str, List[str]]]:
    terceiros = gestor_dependencias.skills_de_terceiros(
        os.path.join(raiz, "gates", "dependencias_externas.json")
    )
    padrao = os.path.join(raiz, "componentes", "*", "skills", "*", "SKILL.md")
    resultado = []
    for skill_md in sorted(glob.glob(padrao)):
        violacoes = auditar_skill(skill_md, terceiros)
        if violacoes:
            resultado.append((os.path.relpath(skill_md, raiz).replace("\\", "/"), violacoes))
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description="G_SKILL_FORMATO: formato e nome das skills (CONVENCAO-AUTORIA-SKILLS 5.1-5.3)")
    parser.add_argument("--raiz", default=ROOT_DIR, help="Raiz do repositorio a auditar")
    parser.add_argument("--aviso", action="store_true", help="Modo aviso: imprime as violacoes e sai com exit 0")
    args = parser.parse_args()

    total_skills = len(glob.glob(os.path.join(args.raiz, "componentes", "*", "skills", "*", "SKILL.md")))
    print(f"[G_SKILL_FORMATO] Auditando {total_skills} skill(s) em componentes/*/skills/ ...")
    achados = auditar(args.raiz)

    if not achados:
        print(f"[OK] G_SKILL_FORMATO: {total_skills} skill(s) no formato das secoes 5.1-5.3.")
        return 0

    total = sum(len(v) for _, v in achados)
    rotulo = "AVISO" if args.aviso else "FALHA"
    print(f"\n[{rotulo}] {total} violacao(oes) em {len(achados)} skill(s):")
    for caminho, violacoes in achados:
        print(f"  - {caminho}")
        for v in violacoes:
            print(f"      {v}")
    print("\nRegra: docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md (secoes 5.1, 5.2 e 5.3).")
    if args.aviso:
        print("[AVISO] Modo aviso ativo: nao reprova (exit 0).")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
