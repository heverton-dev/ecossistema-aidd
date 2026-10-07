# -*- coding: utf-8 -*-
"""
Teste de aderência dos templates do aidd-forge ao Padrão-Ouro TanStack
(TICKET-01 / D13 / Lei #11).

Exige que `modulos/01-governanca-e-qualidade/core/aidd-forge/aidd_forge/templates/`:
- não prescreva Next.js (endosso reprova; menção de abolição é permitida);
- declare TanStack Start / TanStack Router + React + TypeScript + Tailwind
  como stack mandatória (Lei #11, G_STACK_PADRAO_OURO).

Bidirecional: qualquer endosso a Next.js nos templates faz o teste falhar
(exit 1); templates aderentes aprovam (exit 0).
"""

import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge" / "aidd_forge" / "templates"

SUFIXOS_TEXTO = {".py", ".md", ".json", ".html"}

# Endosso de Next.js como stack (Lei #11: Next.js é formalmente abolido).
PADRAO_ENDOSSO_NEXT = re.compile(r"next\.js|nextjs", re.IGNORECASE)

# Contexto lícito: abolição / proibição / auditoria de drift do Next.js.
PADRAO_ABOLICAO = re.compile(
    r"aboli|viola[çc][ãa]o da lei #11|formalmente|proibid|banid|removid|drift",
    re.IGNORECASE,
)


def _arquivos_template() -> list[Path]:
    assert TEMPLATES_DIR.is_dir(), (
        f"diretório de templates inexistente: {TEMPLATES_DIR}"
    )
    return sorted(
        caminho
        for caminho in TEMPLATES_DIR.rglob("*")
        if caminho.is_file() and caminho.suffix in SUFIXOS_TEXTO
    )


def test_templates_nao_prescrevem_next_js():
    """Lei #11: nenhum template do forge pode endossar Next.js como stack."""
    violacoes: list[str] = []
    for caminho in _arquivos_template():
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        for numero, linha in enumerate(texto.splitlines(), start=1):
            if PADRAO_ENDOSSO_NEXT.search(linha) and not PADRAO_ABOLICAO.search(linha):
                relativo = caminho.relative_to(ROOT_DIR).as_posix()
                violacoes.append(f"{relativo}:{numero}: {linha.strip()}")
    assert not violacoes, (
        "templates do forge endossam Next.js (Lei #11 abole o framework):\n"
        + "\n".join(violacoes)
    )


def test_agents_md_template_declara_tanstack_como_padrao_ouro():
    """Governança injetada deve prescrever TanStack Start / Router na Lei #11."""
    agents = (TEMPLATES_DIR / "governance" / "AGENTS.md").read_text(
        encoding="utf-8", errors="replace"
    )
    linha_lei_11 = next(
        (linha for linha in agents.splitlines() if linha.startswith("11.")), ""
    )
    assert "TanStack" in linha_lei_11, (
        f"Lei #11 do template AGENTS.md não declara TanStack: {linha_lei_11!r}"
    )
    assert "Next" not in linha_lei_11 or PADRAO_ABOLICAO.search(linha_lei_11), (
        f"Lei #11 do template AGENTS.md prescreve Next.js: {linha_lei_11!r}"
    )


def test_gate_stack_template_valida_deps_tanstack():
    """G_STACK_PADRAO_OURO (template) deve exigir as deps canônicas TanStack."""
    gate = (TEMPLATES_DIR / "gates" / "G_STACK_PADRAO_OURO.py").read_text(
        encoding="utf-8", errors="replace"
    )
    for dependencia in (
        "@tanstack/react-router",
        "react",
        "typescript",
        "tailwindcss",
    ):
        assert f'"{dependencia}"' in gate, (
            f"template do gate não valida a dependência canônica: {dependencia}"
        )
    assert "abolido" in gate, (
        "template do gate não registra a abolição do Next.js (Lei #11)"
    )


def test_checklist_camadas_mercado_template_adere_tanstack():
    """Checklist de camadas do forge não pode oferecer Next.js como alternativa."""
    caminho = TEMPLATES_DIR / "governance" / "CHECKLIST-CAMADAS-MERCADO.json"
    texto = caminho.read_text(encoding="utf-8")
    dados = json.loads(texto)  # checklist precisa continuar JSON válido
    assert dados, "checklist do forge vazio"
    assert "TanStack" in texto, "checklist do forge não menciona TanStack"
    violacoes = [
        f"linha {numero}: {linha.strip()}"
        for numero, linha in enumerate(texto.splitlines(), start=1)
        if PADRAO_ENDOSSO_NEXT.search(linha) and not PADRAO_ABOLICAO.search(linha)
    ]
    assert not violacoes, (
        "CHECKLIST-CAMADAS-MERCADO.json endossa Next.js (Lei #11):\n"
        + "\n".join(violacoes)
    )
