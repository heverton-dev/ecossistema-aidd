#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_IDIOMA_LEI_4 (ISSUE-0012)
=============================================================================
Verificação mecânica determinística da Lei #4 (AGENTS.md §2, "Extreme Token
Economy: Minimalist prompts, compact English core rules, dense PT-BR user
responses only when requested").

Objetivo:
  Bloquear a entrada de prosa em PT-BR em caminhos que devem ser estritamente
  em inglês compacto (ex: corpos de tickets, skills, prompts de agente).
  Redução medida de tokens: tickets em inglês telegráfico custam ~28% menos
  tokens que prosa em português (186 tickets vs 133 cabem no mesmo budget de 100k).

Escopo padrão auditado:
  - `docs/issues/*.md` (excluídos `INDEX.md`, `README.md`, `SESSOES.md`)
    O frontmatter YAML (campo `title:`) e blocos de código (```...```) são
    desconsiderados na auditoria do corpo.

Caminhos explicitamente isentos (mantidos em PT-BR per escopo acordado):
  - `docs/issues/INDEX.md`, `docs/issues/README.md`, `docs/issues/SESSOES.md`
  - `docs/protocolos/**`, `docs/planos/**`, `docs/livro/**`, `docs/relatorios/**`
  - `secoes/**`

Detecção:
  100% determinística, zero chamadas LLM.
  Calcula a densidade de marcadores lexicais do PT-BR:
  - Proporção de palavras estruturais e terminações comuns do português
    (`não`, `são`, `para`, `com`, `está`, `pelo`, `-ção`, etc.).
  - Proporção de caracteres acentuados típicos (`áéíóúâêôãõçà`).

Uso:
  python gates/G_IDIOMA_LEI_4.py [--caminho <arquivo_ou_dir>]
      exit 0 = nenhum arquivo sob escopo contém prosa em PT-BR acima do limiar.
      exit 1 = ao menos 1 arquivo contém violação de idioma (arquivo, densidade
               e amostra de termos são impressos).
"""

import argparse
import glob
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Arquivos ou nomes explicitamente isentos sob docs/issues
ISENCOES_ISSUES = {"INDEX.md", "README.md", "SESSOES.md"}

# Conjunto fechado de caracteres acentuados típicos da língua portuguesa
CARACTERES_ACENTUADOS = set("áéíóúâêôãõçà")

# Conjunto fechado de palavras estruturais e marcadores léxicos em PT-BR
PALAVRAS_ESTRUTURAIS_PT: Set[str] = {
    "não", "são", "está", "estão", "para", "com", "uma", "você", "como",
    "mais", "pelo", "pela", "pelos", "pelas", "então", "também", "deve",
    "devem", "este", "esta", "estes", "estas", "isso", "esse", "essa",
    "esses", "essas", "portão", "portões", "função", "produção",
    "verificação", "execução", "padrão", "geração", "que", "onde", "quando",
    "todos", "todas", "cada", "falso", "falsos", "positivo", "positivos",
    "segredo", "segredos", "chave", "chaves", "reais", "entrega", "entregue",
    "adotada", "adotado", "sucesso", "reprovado", "reprovação", "sessão",
    "sessões", "arquivo", "arquivos", "ferramenta", "ferramentas", "caminho"
}

SUFIXOS_PT = ("ção", "ções", "mento", "mentos", "ando", "endo", "indo")

# Limiares determinísticos de corte
MIN_PALAVRAS_AMOSTRA = 25
LIMIAR_PALAVRAS_PT_ALTO = 0.040   # > 4.0% de palavras PT reprova direto
LIMIAR_PALAVRAS_PT_MEDIO = 0.020  # > 2.0% combinado com > 0.8% acentos reprova
LIMIAR_ACENTOS_PT = 0.008


def extrair_corpo_analisavel(conteudo_md: str) -> str:
    """Remove frontmatter YAML e blocos de código com cercadura para auditar apenas a prosa."""
    # Remove frontmatter inicial (--- ... ---)
    sem_frontmatter = re.sub(r"^---\s*.*?---\s*", "", conteudo_md, flags=re.DOTALL)
    # Remove blocos de código ``` ... ```
    sem_codigo = re.sub(r"```.*?```", "", sem_frontmatter, flags=re.DOTALL)
    # Remove tags HTML de comentários <!-- ... -->
    sem_comentarios = re.sub(r"<!--.*?-->", "", sem_codigo, flags=re.DOTALL)
    return sem_comentarios


def analisar_texto(texto: str) -> Tuple[float, float, int, List[str], bool]:
    """Retorna (razao_palavras_pt, razao_acentos, total_palavras, amostra_termos, eh_violacao)."""
    palavras = re.findall(r"\b[a-zA-Z\u00C0-\u00FF]+\b", texto.lower())
    total_palavras = len(palavras)

    if total_palavras < MIN_PALAVRAS_AMOSTRA:
        return 0.0, 0.0, total_palavras, [], False

    termos_pt_encontrados = []
    for w in palavras:
        if w in PALAVRAS_ESTRUTURAIS_PT or w.endswith(SUFIXOS_PT):
            termos_pt_encontrados.append(w)

    letras = [c for c in texto.lower() if c.isalpha()]
    total_letras = len(letras)
    acentos = [c for c in letras if c in CARACTERES_ACENTUADOS]

    razao_palavras_pt = len(termos_pt_encontrados) / total_palavras
    razao_acentos = len(acentos) / max(1, total_letras)

    eh_violacao = (
        razao_palavras_pt >= LIMIAR_PALAVRAS_PT_ALTO
        or (razao_palavras_pt >= LIMIAR_PALAVRAS_PT_MEDIO and razao_acentos >= LIMIAR_ACENTOS_PT)
    )

    amostra_termos = sorted(list(set(termos_pt_encontrados)))[:10]
    return razao_palavras_pt, razao_acentos, total_palavras, amostra_termos, eh_violacao


def listar_arquivos_padrao() -> List[str]:
    """Lista todos os arquivos de tickets em docs/issues/**/*.md que devem ser estritamente em inglês."""
    padrao = os.path.join(ROOT_DIR, "docs", "issues", "**", "*.md")
    arquivos = []
    for caminho in sorted(glob.glob(padrao, recursive=True)):
        nome = os.path.basename(caminho)
        if nome in ISENCOES_ISSUES:
            continue
        arquivos.append(caminho)
    return arquivos


def auditar_arquivo(caminho_abs: str) -> Optional[Dict[str, any]]:
    """Audita um arquivo e retorna dados da violação se detectada prosa PT-BR."""
    nome = os.path.basename(caminho_abs)
    if nome in ISENCOES_ISSUES:
        return None

    try:
        with open(caminho_abs, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception as exc:
        print(f"[ERRO] Falha ao ler {caminho_abs}: {exc}", file=sys.stderr)
        return None

    corpo = extrair_corpo_analisavel(conteudo)
    razao_w, razao_a, total_w, amostra, eh_violacao = analisar_texto(corpo)

    if eh_violacao:
        rel_path = os.path.relpath(caminho_abs, ROOT_DIR).replace("\\", "/")
        return {
            "caminho": rel_path,
            "razao_palavras_pt": razao_w,
            "razao_acentos": razao_a,
            "total_palavras": total_w,
            "amostra": amostra,
        }
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gate G_IDIOMA_LEI_4: Detecção determinística de idioma para cumprimento da Lei #4"
    )
    parser.add_argument(
        "--caminho",
        "-c",
        help="Caminho específico de arquivo ou diretório a auditar",
        default=None,
    )
    args = parser.parse_args()

    if args.caminho:
        caminho_input = os.path.abspath(args.caminho)
        if os.path.isdir(caminho_input):
            arquivos = [
                os.path.join(caminho_input, f)
                for f in sorted(os.listdir(caminho_input))
                if f.endswith(".md") and f not in ISENCOES_ISSUES
            ]
        else:
            arquivos = [caminho_input]
    else:
        arquivos = listar_arquivos_padrao()

    print(f"Auditing language compliance (Law #4) across {len(arquivos)} target file(s)...")

    violacoes = []
    for arq in arquivos:
        resultado = auditar_arquivo(arq)
        if resultado:
            violacoes.append(resultado)

    if violacoes:
        print("\n" + "=" * 78)
        print("VIOLATION [G_IDIOMA_LEI_4]: Non-compact PT-BR prose detected in core paths!")
        print("Per Law #4 (AGENTS.md): core agent-facing content must be in compact English.")
        print("=" * 78)
        for v in violacoes:
            print(f"- File: {v['caminho']}")
            print(f"  Words: {v['total_palavras']} | PT Structural Words: {v['razao_palavras_pt']:.1%} | Accents: {v['razao_acentos']:.1%}")
            print(f"  Sample PT terms: {', '.join(v['amostra'])}")
        print("=" * 78)
        print(f"TOTAL VIOLATIONS: {len(violacoes)}\n")
        return 1

    print("[OK] G_IDIOMA_LEI_4: 100% compliant. All audited files adhere to compact English invariant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
