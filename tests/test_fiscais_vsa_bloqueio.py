# -*- coding: utf-8 -*-
"""Ticket 20 (ciclo-03 VSA, D13 / DoD 8): fiscais da VSA em bloqueio e allowlists enxutas.

1. G_COPIA_UNICA_VSA e G_MODULO_FRONTEIRA rodam em bloqueio sem --modo e sem variável, e a
   árvore real passa nos dois; o pre-commit (que o audit também roda) não força --modo aviso.
2. allowlist_fronteira.json (G_FRONTEIRA_FERRAMENTAS) e allowlist_modulo_fronteira.json
   (G_MODULO_FRONTEIRA): toda entrada aponta para arquivo que existe e ainda é violação real
   (sem entrada morta); o teto da segunda é o número de entradas.
3. Toda entrada fora do esqueleto enterprise × master tem a data da revisão do Ticket 20 e um
   motivo atual (não o texto genérico da semeadura ou do inventário). As entradas de
   aidd-enterprise/ e aidd-master/ ficam com o Ticket 23 (Bloco 9), que reorganiza as duas.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GATES = RAIZ / "modulos" / "04-nucleo-compartilhado" / "gates"
CONTRATOS = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts"
FISCAIS = {
    "G_COPIA_UNICA_VSA": ("g-copia-unica-vsa", "AIDD_COPIA_UNICA_MODO"),
    "G_MODULO_FRONTEIRA": ("g-modulo-fronteira", "AIDD_MODULO_FRONTEIRA_MODO"),
}
REVISAO = "2026-10-08"
MOTIVOS_GENERICOS = ("conhecida no inventario inicial", "acoplamento existente na semeadura")
ESQUELETO_T23 = (
    "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/",
    "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/",
)
VARIAVEIS_DO_HOOK = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_PREFIX")


def _rodar(gate: str, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in VARIAVEIS_DO_HOOK and k not in ("AIDD_FRONTEIRA_MODO",) + tuple(v[1] for v in FISCAIS.values())}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(GATES / f"{gate}.py"), *args], cwd=str(RAIZ),
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)


def _allowlist(nome: str) -> dict:
    return json.loads((CONTRATOS / nome).read_text(encoding="utf-8"))


def _entradas() -> list[tuple[str, dict]]:
    return ([("allowlist_fronteira.json", e) for e in _allowlist("allowlist_fronteira.json")["violacoes"]]
            + [("allowlist_modulo_fronteira.json", e)
               for e in _allowlist("allowlist_modulo_fronteira.json")["entradas"]])


@pytest.mark.parametrize("gate", sorted(FISCAIS))
def test_fiscal_sem_modo_roda_em_bloqueio_e_aprova_a_arvore(gate):
    proc = _rodar(gate)
    assert "modo bloqueio" in proc.stdout, proc.stdout + proc.stderr
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("gate", sorted(FISCAIS))
def test_pre_commit_nao_forca_aviso_no_fiscal(gate):
    hook_id, variavel = FISCAIS[gate]
    texto = (RAIZ / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    bloco = next(b for b in re.split(r"\n\s*- id: ", texto) if b.split("\n", 1)[0].strip() == hook_id)
    entrada = re.search(r"entry:\s*(.+)", bloco).group(1)
    assert f"{gate}.py" in entrada
    assert "aviso" not in entrada and variavel not in entrada, entrada


def test_allowlist_fronteira_sem_entrada_morta():
    proc = _rodar("G_FRONTEIRA_FERRAMENTAS", "--modo", "aviso")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    perdoadas = set(re.findall(r"\[PERDOADA\] arquivo=(\S+)", proc.stdout))
    for e in _allowlist("allowlist_fronteira.json")["violacoes"]:
        assert (RAIZ / e["arquivo"]).is_file(), f"arquivo não existe: {e['arquivo']}"
        assert e["arquivo"] in perdoadas, f"entrada morta (não é mais violação): {e['arquivo']}"


def test_allowlist_modulo_fronteira_teto_igual_ao_numero_de_entradas():
    dados = _allowlist("allowlist_modulo_fronteira.json")
    assert dados["teto"] == len(dados["entradas"])
    for e in dados["entradas"]:
        assert (RAIZ / e["arquivo"]).is_file(), f"arquivo não existe: {e['arquivo']}"


@pytest.mark.parametrize("nome,entrada", [(n, e) for n, e in _entradas()
                                          if not e["arquivo"].startswith(ESQUELETO_T23)],
                         ids=lambda v: v if isinstance(v, str) else f"{v['arquivo']}:{v.get('tipo', '')}:{v.get('alvo', '')}")
def test_entrada_revisada_tem_data_e_motivo_atual(nome, entrada):
    assert entrada["data"] >= REVISAO, f"{nome}: {entrada['arquivo']} sem revisão do Ticket 20"
    motivo = entrada["motivo"]
    assert not motivo.startswith(MOTIVOS_GENERICOS), f"{nome}: motivo genérico em {entrada['arquivo']}"
    assert len(motivo) >= 40, f"{nome}: motivo curto demais em {entrada['arquivo']}"
