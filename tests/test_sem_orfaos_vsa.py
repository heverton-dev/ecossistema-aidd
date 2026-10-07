# -*- coding: utf-8 -*-
"""
Teste de Handoff do Ticket 14 (D8 / DoD 5).
Garante que nenhum script *_vsa.py em scripts/ ou contrato em docs/padroes/contratos/
fique órfão (sem consumidor no código de produção do ecossistema fora de testes).
"""

import ast
import os
import re
from pathlib import Path
import pytest

RAIZ = Path(__file__).resolve().parents[1]


def listar_arquivos_producao():
    arquivos = []
    pastas_busca = [RAIZ / "scripts", RAIZ / "modulos", RAIZ / "componentes"]
    for pasta in pastas_busca:
        if pasta.exists():
            for p in pasta.rglob("*.py"):
                # Excluir pastas de testes ou caches
                partes = p.parts
                if "tests" in partes or "test" in partes or "__pycache__" in partes:
                    continue
                arquivos.append(p)
    # Incluir ecossistema.py raiz
    if (RAIZ / "ecossistema.py").exists():
        arquivos.append(RAIZ / "ecossistema.py")
    return arquivos


def obter_scripts_alvo():
    alvos = list((RAIZ / "scripts").glob("*_vsa.py"))
    manifesto = RAIZ / "docs" / "padroes" / "contratos" / "manifesto_modulos.py"
    if manifesto.exists():
        alvos.append(manifesto)
    return alvos


def test_nenhum_script_vsa_esta_orfao():
    alvos = obter_scripts_alvo()
    arquivos_prod = listar_arquivos_producao()

    orfaos = []
    for alvo in alvos:
        nome_modulo = alvo.stem
        # Procurar se algum arquivo de produção importa ou referencia esse módulo
        consumidores = []
        for prod in arquivos_prod:
            if prod.resolve() == alvo.resolve():
                continue
            texto = prod.read_text(encoding="utf-8", errors="replace")
            # Procura referências como `import nome_modulo`, `from ... import nome_modulo`, `nome_modulo.py`
            padrao = rf"\b{re.escape(nome_modulo)}\b"
            if re.search(padrao, texto):
                consumidores.append(prod)

        if not consumidores:
            orfaos.append(alvo.name)

    assert not orfaos, f"Scripts VSA órfãos detectados sem consumidores em produção: {orfaos}"
