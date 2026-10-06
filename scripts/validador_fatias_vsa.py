# -*- coding: utf-8 -*-
"""
Validador Determinístico de Fatias Verticais VSA e Autocontenção Fractal.
Verifica se os módulos em modulos/ contêm a estrutura canônica necessária conforme
docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md.
"""

import sys
from pathlib import Path
from typing import List, Tuple

try:
    from scripts.validador_fractalidade_vsa import validar_fractalidade_slice
except ImportError:
    from validador_fractalidade_vsa import validar_fractalidade_slice

RAIZ_REPO = Path(__file__).resolve().parent.parent
MODULOS_DIR = RAIZ_REPO / "modulos"

# Fatias autossuficientes canônicas com trinca viva (core, skills, gates, tests, README.md)
SLICES_FRACTAIS = [
    MODULOS_DIR / "01-governanca-e-qualidade",
    MODULOS_DIR / "02-triade-motores" / "fluxo-01-pure",
    MODULOS_DIR / "02-triade-motores" / "fluxo-02-open",
    MODULOS_DIR / "02-triade-motores" / "fluxo-03-freedom",
]

# Macro-módulos agregadores que possuem subfatias ou estrutura própria
MACRO_MODULOS_COMPOSITOS = [
    MODULOS_DIR / "03-plataforma-e-entrega",
    MODULOS_DIR / "04-nucleo-compartilhado",
]


def validar_macro_composto(caminho: Path, elementos: List[str]) -> List[str]:
    erros = []
    for elem in elementos:
        alvo = caminho / elem
        if not alvo.exists():
            erros.append(f"[{caminho.name}] Elemento obrigatório ausente: {elem}")
    readme = caminho / "README.md"
    if not readme.exists():
        erros.append(f"[{caminho.name}] README.md ausente.")
    return erros


def validar_todas_fatias() -> Tuple[bool, List[str]]:
    erros_totais: List[str] = []

    for fatia in SLICES_FRACTAIS:
        if not fatia.exists():
            erros_totais.append(f"Fatia obrigatória não existe: {fatia.relative_to(RAIZ_REPO)}")
            continue
        valido, errs = validar_fractalidade_slice(fatia)
        if not valido:
            for e in errs:
                erros_totais.append(f"[{fatia.name}] {e}")

    # Validação estrutural dos módulos compostos conforme arquitetura
    # 03-plataforma-e-entrega agrega fatiamento-master, blindagem-enterprise, operacoes-ops, skills, gates, tests
    erros_totais.extend(validar_macro_composto(
        MODULOS_DIR / "03-plataforma-e-entrega",
        ["fatiamento-master", "blindagem-enterprise", "operacoes-ops", "skills", "gates", "tests"]
    ))

    # 04-nucleo-compartilhado possui cli, contracts, scripts, gates, tests, sync
    erros_totais.extend(validar_macro_composto(
        MODULOS_DIR / "04-nucleo-compartilhado",
        ["cli", "contracts", "scripts", "gates", "tests", "sync"]
    ))

    return len(erros_totais) == 0, erros_totais


def main() -> int:
    valido, erros = validar_todas_fatias()
    if valido:
        print("[validador_fatias_vsa] SUCESSO: Todas as fatias verticais VSA estão íntegras e em conformidade.")
        return 0
    else:
        print(f"[validador_fatias_vsa] ERRO: {len(erros)} inconformidades detectadas:")
        for err in erros:
            print(f"  - {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
