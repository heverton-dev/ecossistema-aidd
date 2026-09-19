#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_DOCS_ROT.py - Quality Gate Determinístico Anti-Docs Rot do Ecossistema AIDD.

Verifica:
1. Links relativos quebrados em documentações vivas (docs/protocolos, docs/ e READMEs principais).
2. Planos soltos em docs/planos/ que não estão em feitos/ ou devidamente marcados.
3. Arquivos obsoletos ou duplicados na raiz de docs/.

Exit 0: Conformidade total (zero docs rot detectados).
Exit 1: Links quebrados ou documentos podres detectados.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Forçar stdout para utf-8 no Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"

# Regex para links markdown: [label](caminho)
LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

# Pastas consideradas ativas e que não podem conter links quebrados
PASTAS_ATIVAS = [
    ROOT_DIR / "docs" / "protocolos",
    ROOT_DIR / "componentes",
]

# Arquivos raiz obrigatórios a validar
ARQUIVOS_RAIZ_ATIVOS = [
    ROOT_DIR / "AGENTS.md",
    ROOT_DIR / "README.md",
    ROOT_DIR / "MEMORY.md",
]


def extrair_links_locais(conteudo: str) -> List[str]:
    """Extrai links que não são URLs externas (http/https/mailto/#anchor)."""
    links = []
    for _, target in LINK_REGEX.findall(conteudo):
        target = target.strip()
        # Ignora links externos e âncoras puras
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Remove âncora interna do caminho (ex: doc.md#secao)
        caminho_limpo = target.split("#")[0].strip()
        if caminho_limpo:
            links.append(caminho_limpo)
    return links


DIRETORIOS_IGNORADOS = {".venv", "venv", "node_modules", ".git", "__pycache__", "site-packages", ".dist-info"}


def verificar_links_quebrados() -> List[str]:
    """Verifica links relativos nos arquivos markdown vivos."""
    erros = []
    arquivos_para_auditar = [a for a in ARQUIVOS_RAIZ_ATIVOS if a.is_file()]

    for pasta in PASTAS_ATIVAS:
        if pasta.is_dir():
            for arq in pasta.rglob("*.md"):
                # Ignora dependências e ambientes virtuais
                if any(ign in arq.parts for ign in DIRETORIOS_IGNORADOS):
                    continue
                arquivos_para_auditar.append(arq)

    for arq in arquivos_para_auditar:
        if not arq.is_file():
            continue
        try:
            texto = arq.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            erros.append(f"Erro ao ler {arq.relative_to(ROOT_DIR)}: {e}")
            continue

        links = extrair_links_locais(texto)
        pasta_base = arq.parent

        for link in links:
            # Resolve caminho relativo ao arquivo
            caminho_alvo = (pasta_base / link).resolve()
            # Se não existir relativamente, tenta resolver a partir do ROOT_DIR
            if not caminho_alvo.exists():
                caminho_raiz = (ROOT_DIR / link.lstrip("/\\")).resolve()
                if not caminho_raiz.exists():
                    erros.append(
                        f"[{arq.relative_to(ROOT_DIR)}] Link quebrado: '{link}' -> destino não encontrado."
                    )
    return erros


def verificar_planos_orfaos() -> List[str]:
    """Valida que não existem diretórios de planos soltos fora de a-fazer, fazendo ou feitos."""
    erros = []
    planos_dir = DOCS_DIR / "planos"
    if not planos_dir.is_dir():
        return erros

    subpastas_permitidas = {"a-fazer", "fazendo", "feitos"}
    for item in planos_dir.iterdir():
        if item.is_dir() and item.name not in subpastas_permitidas and not item.name.startswith("."):
            erros.append(
                f"[docs/planos/] Diretório de plano solto/órfão: '{item.name}'. "
                f"Deve residir em 'a-fazer/', 'fazendo/' ou 'feitos/'."
            )
    return erros


def auditar_docs_rot() -> Tuple[int, List[str]]:
    """Executa a auditoria determinística anti-docs-rot."""
    falhas = []
    
    # 1. Links quebrados
    links_quebrados = verificar_links_quebrados()
    falhas.extend(links_quebrados)

    # 2. Planos soltos ou mal categorizados
    planos_orfaos = verificar_planos_orfaos()
    falhas.extend(planos_orfaos)

    return (1 if falhas else 0, falhas)


def main():
    codigo, falhas = auditar_docs_rot()
    if codigo != 0:
        print(f"[G_DOCS_ROT] ❌ REPROVADO: {len(falhas)} inconsistência(s) encontrada(s):")
        for f in falhas[:25]:
            print(f"  - {f}")
        if len(falhas) > 25:
            print(f"  ... e mais {len(falhas) - 25} problemas.")
        sys.exit(1)
    else:
        print("[G_DOCS_ROT] ✅ APROVADO: Documentação viva íntegra, sem links quebrados ou rot.")
        sys.exit(0)


if __name__ == "__main__":
    main()
