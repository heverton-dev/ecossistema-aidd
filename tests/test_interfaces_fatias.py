# -*- coding: utf-8 -*-
"""Ticket 10 (ciclo-03 VSA, D1 / DoD 4): interface publica por fatia e nomes de pacote unicos.

1. Cada uma das 7 fatias de MAPA-FATIAS.json tem `interface.py` com `__all__`
   nao vazio, e cada nome do `__all__` existe de verdade ao carregar o arquivo.
2. Nenhum pacote importavel se repete entre fatias diferentes. Raizes de import
   de cada ferramenta: a propria pasta, `src/` e `scripts/`. As caixas de layout
   (`src`, `scripts`, `tests`) nao contam: cada ferramenta roda com a propria raiz.
   Excecao so pela allowlist datada, que so pode diminuir.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CONTRATOS = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts"
MAPA = json.loads((CONTRATOS / "MAPA-FATIAS.json").read_text(encoding="utf-8"))
ALLOWLIST = CONTRATOS / "allowlist_pacotes_repetidos.json"
FATIAS = MAPA["fatias"]


def _nomes_definidos(arvore: ast.Module) -> set[str]:
    nomes: set[str] = set()
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nomes.add(no.name)
        elif isinstance(no, ast.Assign):
            nomes.update(a.id for a in no.targets if isinstance(a, ast.Name))
        elif isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
            nomes.add(no.target.id)
        elif isinstance(no, (ast.Import, ast.ImportFrom)):
            nomes.update((a.asname or a.name).split(".")[0] for a in no.names)
    return nomes


def _all_declarado(arvore: ast.Module) -> list[str] | None:
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(isinstance(a, ast.Name) and a.id == "__all__" for a in no.targets):
            if isinstance(no.value, (ast.List, ast.Tuple)):
                return [e.value for e in no.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return None


@pytest.mark.parametrize("fatia", sorted(FATIAS))
def test_fatia_tem_interface_com_all(fatia: str) -> None:
    interface = RAIZ / FATIAS[fatia]["caminho"] / "interface.py"
    assert interface.is_file(), f"{fatia}: falta {interface.relative_to(RAIZ).as_posix()}"
    arvore = ast.parse(interface.read_text(encoding="utf-8"))
    exportados = _all_declarado(arvore)
    assert exportados, f"{fatia}: interface.py sem __all__ (lista literal nao vazia)"
    faltando = sorted(set(exportados) - _nomes_definidos(arvore))
    assert not faltando, f"{fatia}: __all__ cita nomes nao definidos: {faltando}"


@pytest.mark.parametrize("fatia", sorted(FATIAS))
def test_interface_carrega_e_entrega_cada_nome(fatia: str) -> None:
    """Carrega a interface num processo limpo, com nome de modulo unico, e confere
    que cada nome exportado existe; caminhos exportados precisam existir no disco."""
    interface = RAIZ / FATIAS[fatia]["caminho"] / "interface.py"
    codigo = (
        "import importlib.util, sys, pathlib\n"
        f"spec = importlib.util.spec_from_file_location('interface_{fatia.replace('-', '_')}', r'{interface}')\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "for n in m.__all__:\n"
        "    v = getattr(m, n)\n"
        "    if isinstance(v, pathlib.Path) and not v.exists():\n"
        "        sys.exit(f'{n} aponta para caminho inexistente: {v}')\n"
    )
    r = subprocess.run([sys.executable, "-c", codigo], cwd=str(RAIZ), capture_output=True, text=True)
    assert r.returncode == 0, f"{fatia}: interface nao carrega\n{r.stdout}\n{r.stderr}"


def pacotes_por_nome() -> dict[str, set[str]]:
    """nome de pacote -> fatias que o expoem numa raiz de import."""
    por_nome: dict[str, set[str]] = defaultdict(set)
    caixas = set(MAPA["caixas_de_layout"])
    for fatia, dados in FATIAS.items():
        for ferramenta in dados["ferramentas"]:
            base = RAIZ / dados["caminho"] / ferramenta
            for sub in MAPA["raizes_import"]:
                raiz_import = base / sub if sub else base
                if not raiz_import.is_dir():
                    continue
                for pasta in raiz_import.iterdir():
                    if pasta.name in caixas or not (pasta / "__init__.py").is_file():
                        continue
                    por_nome[pasta.name].add(fatia)
    return por_nome


def _allowlist() -> dict[str, set[str]]:
    dados = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    return {e["pacote"]: set(e["fatias"]) for e in dados["entradas"]}


def test_sem_pacote_repetido_entre_fatias() -> None:
    perdoados = _allowlist()
    repetidos = {
        nome: sorted(fatias)
        for nome, fatias in pacotes_por_nome().items()
        if len(fatias) > 1 and fatias != perdoados.get(nome)
    }
    assert not repetidos, f"pacotes com o mesmo nome em fatias diferentes: {repetidos}"


def test_allowlist_datada_e_so_com_colisao_real() -> None:
    dados = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    reais = pacotes_por_nome()
    for e in dados["entradas"]:
        assert e.get("data") and e.get("motivo"), f"entrada sem data/motivo: {e}"
        assert set(e["fatias"]) == reais.get(e["pacote"], set()), (
            f"entrada morta ou desatualizada na allowlist (so pode diminuir): {e['pacote']}"
        )
