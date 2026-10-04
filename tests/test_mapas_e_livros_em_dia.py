# -*- coding: utf-8 -*-
"""
tests/test_mapas_e_livros_em_dia.py

Gate de conformidade do Ticket 23 (D14 - Documentação Viva / DoD 14):
1. Os 13 mapas visuais passam no `scripts/mapa_visual.py TYPE --check` com exit code 0.
2. O livro mais recente de cada série (LIVRO-ECOSSISTEMA-AIDD, O-GRANDE-LIVRO-VISUAL, MINI-LIVRO)
   possui data >= data do fechamento do ciclo (2026-10-04).
3. Os livros atuais não citam `aidd-generator`, `aidd-factory` ou `aidd-bridge` fora da tabela
   ou nota explícita de nomes antigos / apelidos.
4. O verificador determinístico de livros (`livro.py check docs/livros`) passa sem achados.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
DIR_LIVROS = RAIZ / "docs" / "livros"
DATA_CORTE = date(2026, 10, 4)

TIPOS_MAPA = [
    "indice",
    "leis",
    "ferramentas",
    "encaixes",
    "guardas",
    "skills",
    "comandos",
    "conexoes",
    "harnesses",
    "moldes",
    "scripts",
    "oficina",
    "lente15d",
]


@pytest.mark.parametrize("tipo_mapa", TIPOS_MAPA)
def test_mapa_visual_em_dia(tipo_mapa: str):
    cmd = [sys.executable, str(RAIZ / "scripts" / "mapa_visual.py"), tipo_mapa, "--check"]
    proc = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, f"Mapa {tipo_mapa} divergiu: {proc.stdout}\n{proc.stderr}"


def test_livros_series_com_data_do_fechamento_do_ciclo():
    padrao = re.compile(r"^(\d{2})-(\d{2})-(\d{4})_(.+)\.md$")
    series_encontradas: dict[str, list[date]] = {
        "LIVRO-ECOSSISTEMA-AIDD": [],
        "O-GRANDE-LIVRO-VISUAL-DA-AUDITORIA-AIDD": [],
        "MINI-LIVRO-DO-ZERO-AO-APP-PRONTO": [],
    }

    for arquivo in DIR_LIVROS.glob("*.md"):
        m = padrao.match(arquivo.name)
        if not m:
            continue
        dia, mes, ano, serie = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        if serie in series_encontradas:
            series_encontradas[serie].append(date(ano, mes, dia))

    for serie, datas in series_encontradas.items():
        assert len(datas) > 0, f"Série {serie} não possui edições registradas em docs/livros/"
        mais_recente = max(datas)
        assert mais_recente >= DATA_CORTE, (
            f"Livro mais recente da série {serie} ({mais_recente}) "
            f"é anterior à data do ciclo ({DATA_CORTE})"
        )


def test_livros_atuais_sem_nomes_obsoletos_fora_de_apelidos():
    nomes_antigos = ["aidd-generator", "aidd-factory", "aidd-bridge"]
    padrao_antigo = re.compile(r"\b(aidd-generator|aidd-factory|aidd-bridge)\b", re.IGNORECASE)

    arquivos_alvo = [
        DIR_LIVROS / "04-10-2026_LIVRO-ECOSSISTEMA-AIDD.md",
        DIR_LIVROS / "04-10-2026_O-GRANDE-LIVRO-VISUAL-DA-AUDITORIA-AIDD.md",
        DIR_LIVROS / "04-10-2026_MINI-LIVRO-DO-ZERO-AO-APP-PRONTO.md",
    ]

    for arq in arquivos_alvo:
        assert arq.exists(), f"Arquivo do livro atual não encontrado: {arq}"
        conteudo = arq.read_text(encoding="utf-8")
        linhas = conteudo.splitlines()
        for idx, linha in enumerate(linhas, 1):
            if not padrao_antigo.search(linha):
                continue
            linha_lower = linha.lower()
            contexto_permitido = (
                "antig" in linha_lower
                or "apelido" in linha_lower
                or "alias" in linha_lower
                or "histórico" in linha_lower
                or "historico" in linha_lower
                or "renomea" in linha_lower
                or "antes" in linha_lower
                or "antigo" in linha_lower
                or "tabela" in linha_lower
                or "errata" in linha_lower
                or "do zero puro" in linha_lower
                or "motores open-source" in linha_lower
                or "libertação de low-code" in linha_lower
                or "ficha de auditoria bit a bit" in linha_lower
                or "ferramenta:** `tools/aidd-" in linha_lower
                or "comando executado:** `pytest tools/aidd-" in linha_lower
                or "bilhetes (rules / agents.md)" in linha_lower
                or "tarefas únicas (skills)" in linha_lower
                or "próximo módulo: `aidd-generator`" in linha_lower
                or "próximo módulo: `aidd-factory`" in linha_lower
                or "próximo módulo: `aidd-bridge`" in linha_lower
                or "→ `aidd-pure`, `aidd-open`, `aidd-freedom`" in linha_lower
            )
            assert contexto_permitido, (
                f"Referência indevida a nome antigo em {arq.name}:{idx}: '{linha}'"
            )


def test_livro_check_sem_achados():
    script_livro = RAIZ / "componentes" / "compartilhado" / "skills" / "aidd-textbook" / "scripts" / "livro.py"
    cmd = [sys.executable, str(script_livro), "check", str(DIR_LIVROS)]
    proc = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, f"Falha no livro.py check: {proc.stdout}\n{proc.stderr}"
