# -*- coding: utf-8 -*-
"""
Testes de provision_project.py — cobertura que nao existia antes de
17/09/2026 (achado real na validacao E2E do Fluxo 01/Etapa 4).

Contexto: provision_project.py e a implementacao real por tras de
`aidd-master init`, o comando OFICIAL de entrada para provisionar um novo
projeto modular (documentado como tal em `aidd.py init --help`). Ate
17/09/2026 nenhum teste chamava `provision()` e verificava os arquivos
gerados. Isso permitiu 2 bugs reais sobreviverem sem ninguem notar:

1. Todo projeto criado com `aidd-master init` nascia sem `src/server.py`,
   porque `add_module.criar_modulo()` so RE-liga (regenera) o server.py
   quando ele ja existe (comentario explicito no proprio codigo dizendo
   que a composicao inicial e responsabilidade de quem chama
   `criar_modulo()` pela primeira vez) — e `provision()` nunca gerava esse
   arquivo na primeira vez. G_ESTRUTURA reprova isso ("Servidor ausente ou
   vazio").
2. `src/static/index.html` era copiado estaticamente de
   `templates/core/index.html`, uma versao desatualizada sem as variaveis
   CSS (`--bg-base`) e a estrutura modal (`modal-overlay`/`modal-generic`)
   que G_CONTRACTS exige — enquanto `compose_suite()` (usado por outro
   fluxo) ja gerava esse mesmo arquivo dinamicamente via
   `generate_superapp_index_html()`, sempre em dia.

Juntos, os dois bugs faziam o comando oficial de inicio do Fluxo 01/Etapa 4
nunca produzir um projeto que passasse na propria auditoria do produto.
"""

import os
import sys

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_provision_gera_server_py_no_primeiro_modulo(tmp_path):
    """Achado real: `provision()` criava o modulo 'principal' mas nunca
    escrevia src/server.py na primeira composicao do projeto."""
    from provision_project import provision

    provision("Projeto Teste Provision", base_dir=str(tmp_path))

    projetos = list(tmp_path.glob("proj_*"))
    assert len(projetos) == 1, f"esperava 1 diretorio proj_*, achei: {projetos}"
    projeto_dir = projetos[0]

    server_path = projeto_dir / "src" / "server.py"
    assert server_path.exists(), "src/server.py nao foi gerado por provision()"
    assert server_path.stat().st_size > 0, "src/server.py foi gerado vazio"


def test_provision_gera_index_html_com_css_e_modal_atuais(tmp_path):
    """Achado real: templates/core/index.html (copiado estaticamente) nunca
    tinha --bg-base nem modal-overlay/modal-generic, exigidos por
    G_CONTRACTS. provision() deve gerar via generate_superapp_index_html(),
    igual a compose_suite()."""
    from provision_project import provision

    provision("Projeto Teste Index", base_dir=str(tmp_path))
    projeto_dir = next(tmp_path.glob("proj_*"))

    index_path = projeto_dir / "src" / "static" / "index.html"
    conteudo = index_path.read_text(encoding="utf-8")
    assert "<style>" in conteudo and "--bg-base" in conteudo
    assert "modal-overlay" in conteudo or "modal-generic" in conteudo


def test_provision_passa_no_gate_g_estrutura(tmp_path):
    """Nao basta o arquivo existir — precisa satisfazer de verdade o mesmo
    gate que `aidd-master audit` roda contra qualquer projeto provisionado
    (reproducao real, sem leitura cruzada de codigo)."""
    from provision_project import provision

    provision("Projeto Teste Estrutura", base_dir=str(tmp_path))
    projeto_dir = next(tmp_path.glob("proj_*"))

    gate_path = os.path.join(SCRIPTS_DIR, "gates", "G_ESTRUTURA.py")
    import subprocess

    resultado = subprocess.run(
        [sys.executable, gate_path, "--dir", str(projeto_dir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_provision_passa_no_gate_g_contracts(tmp_path):
    """Mesma logica do teste acima, para o gate que pegava o index.html
    desatualizado (G_CONTRACTS)."""
    from provision_project import provision

    provision("Projeto Teste Contracts", base_dir=str(tmp_path))
    projeto_dir = next(tmp_path.glob("proj_*"))

    gate_path = os.path.join(SCRIPTS_DIR, "gates", "G_CONTRACTS.py")
    import subprocess

    resultado = subprocess.run(
        [sys.executable, gate_path, "--dir", str(projeto_dir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
