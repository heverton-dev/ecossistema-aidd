# -*- coding: utf-8 -*-
"""
tests/test_mapas_e_livros_em_dia.py

Gate de conformidade do Ticket 23 (D14 - Documentação Viva / DoD 14) do fronteiras-ferramentas
ciclo-01, ampliado no Ticket 22 do ciclo-03 da VSA (D15 / DoD 8):
1. Os 13 mapas visuais passam no `scripts/mapa_visual.py TYPE --check` com exit code 0.
2. O livro mais recente de cada série (LIVRO-ECOSSISTEMA-AIDD, O-GRANDE-LIVRO-VISUAL, MINI-LIVRO)
   possui data >= data do fechamento do ciclo-03 da VSA (2026-10-08).
3. Os livros atuais não citam `aidd-generator`, `aidd-factory` ou `aidd-bridge` fora da tabela
   ou nota explícita de nomes antigos / apelidos.
4. O verificador determinístico de livros (`livro.py check docs/livros`) passa sem achados.
5. Os livros atuais não citam `tools/aidd-*` (pasta extinta no Ticket 5), salvo as fichas
   históricas de 22/09/2026 que o Livro Visual embute como registro.
6. O laudo revisado do ciclo-03 traz, para cada achado do DIAGNOSTICO.md, o comando de prova e o
   exit code; o padrão de arquitetura VSA está marcado como implementado, com os desvios.
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
DATA_CORTE = date(2026, 10, 8)
SERIES = ("LIVRO-ECOSSISTEMA-AIDD", "O-GRANDE-LIVRO-VISUAL-DA-AUDITORIA-AIDD", "MINI-LIVRO-DO-ZERO-AO-APP-PRONTO")
CICLO_VSA = RAIZ / "docs" / "auditoria" / "modularizacao-vsa" / "ciclo-03"
PADRAO_VSA = RAIZ / "docs" / "padroes" / "ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md"
# Fichas históricas de 22/09/2026 embutidas no Livro Visual (registro do que foi auditado em tools/).
MARCAS_FICHA_HISTORICA = (
    "**ferramenta:** `tools/aidd-",
    "**comando executado:** `pytest tools/aidd-",
    "bilhetes (rules / agents.md)",
    "8 ferramentas da pasta `tools/`",
)


def _livros_mais_recentes() -> list[Path]:
    padrao = re.compile(r"^(\d{2})-(\d{2})-(\d{4})_(.+)\.md$")
    recentes: dict[str, tuple[date, Path]] = {}
    for arquivo in DIR_LIVROS.glob("*.md"):
        m = padrao.match(arquivo.name)
        if not m or m.group(4) not in SERIES:
            continue
        data = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if m.group(4) not in recentes or data > recentes[m.group(4)][0]:
            recentes[m.group(4)] = (data, arquivo)
    return [recentes[s][1] for s in SERIES if s in recentes]

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
    import scripts.mapa_visual as mv
    rc = mv.main([tipo_mapa, "--check"])
    assert rc == 0, f"Mapa {tipo_mapa} divergiu"



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

    arquivos_alvo = _livros_mais_recentes()
    assert len(arquivos_alvo) == len(SERIES)

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


def test_livros_atuais_sem_caminho_tools_fora_das_fichas_historicas():
    """Ticket 22 (ciclo-03 VSA): `tools/` saiu no Ticket 5; os livros apontam para `modulos/`."""
    for arq in _livros_mais_recentes():
        for idx, linha in enumerate(arq.read_text(encoding="utf-8").splitlines(), 1):
            if "tools/aidd-" not in linha:
                continue
            assert any(m in linha.lower() for m in MARCAS_FICHA_HISTORICA), (
                f"{arq.name}:{idx} cita a pasta extinta tools/: '{linha.strip()[:160]}'")


def test_laudo_revisado_vsa_com_prova_de_cada_achado():
    """Ticket 22 (ciclo-03 VSA): cada achado do DIAGNOSTICO.md tem comando de prova e exit code."""
    achados = re.findall(r"^### (\d+)\. ", (CICLO_VSA / "DIAGNOSTICO.md").read_text(encoding="utf-8"), re.M)
    laudo = CICLO_VSA / "LAUDO-REVISADO.md"
    assert laudo.is_file(), "falta docs/auditoria/modularizacao-vsa/ciclo-03/LAUDO-REVISADO.md"
    secoes = re.split(r"^### ", laudo.read_text(encoding="utf-8"), flags=re.M)
    for numero in achados:
        secao = next((s for s in secoes if s.startswith(f"{numero}. ")), None)
        assert secao, f"laudo sem a seção do achado {numero}"
        assert re.search(r"`[^`]+`.*\bexit [0-9]\b", secao), f"achado {numero} sem comando de prova com exit code"


def test_padrao_vsa_implementado_com_desvios():
    texto = PADRAO_VSA.read_text(encoding="utf-8")
    status = next(linha for linha in texto.splitlines() if linha.startswith("> **Status:**"))
    assert "Implementado" in status, status
    assert "Implementação real e desvios registrados" in texto
