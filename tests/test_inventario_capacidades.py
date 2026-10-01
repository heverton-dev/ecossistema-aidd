# -*- coding: utf-8 -*-
"""
Inventário de capacidades (fronteiras-ferramentas ciclo-01, Ticket 3).

Regras:
  - Órfão = existia na foto e não existe mais em lugar nenhum de tools/ e componentes/.
  - Remover a cópia que tinha uma função a mais reprova; remover cópia idêntica, mover ou
    renomear arquivo não reprova.
  - Nomes antigos da tabela de apelidos (Ticket 4) são traduzidos antes de comparar, em
    qualquer caixa; comando de CLI só depois de 'ecossistema.py '; prosa .md não conta linha.
  - INVENTARIO-ANTES.json não pode ter nada que o detect-secrets acuse (1.033 achados
    reprovaram o G_SEGREDOS em 01/10: sha256 e linhas de teste com chave falsa).
  - Só arquivos rastreados pelo git entram na foto.
"""

import gzip
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / "scripts" / "inventario_capacidades.py"
CICLO = "docs/auditoria/fronteiras-ferramentas/ciclo-01"
FOTO = f"{CICLO}/INVENTARIO-ANTES.json"


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _rodar(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--repo", str(repo)],
                          capture_output=True, text=True, encoding="utf-8")


def _escrever(repo, rel, texto):
    caminho = repo / rel
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    """Repo com duas cópias de um módulo; a de aidd-generator tem uma função a mais."""
    raiz = tmp_path / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.name", "teste")
    _git(raiz, "config", "user.email", "teste@teste")
    base = "def montar():\n    return 1\n"
    _escrever(raiz, "tools/aidd-generator/aidd_generator/gate.py",
              base + "\n\ndef validar_extra():\n    return 'so nesta copia'\n")
    _escrever(raiz, "componentes/compartilhado/gate.py", base)
    _escrever(raiz, "componentes/compartilhado/test_gate.py", "def test_montar():\n    assert True\n")
    _escrever(raiz, "tools/aidd-generator/cli.py",
              "print('[AIDD-Generator] pronto')\nUSO = 'python ecossistema.py generate <ideia>'\n")
    _escrever(raiz, "componentes/compartilhado/comandos/generate.md", "# Comando /generate\nGera um app.\n")
    _git(raiz, "add", ".")
    _git(raiz, "commit", "-q", "-m", "init")
    return raiz


def _fotografar(repo):
    res = _rodar(repo, "foto", "--cycle", CICLO)
    assert res.returncode == 0, res.stdout + res.stderr
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "foto")


def test_remover_copia_com_funcao_a_mais_sem_juntar_acusa_orfao(repo):
    _fotografar(repo)
    _git(repo, "rm", "-q", "tools/aidd-generator/aidd_generator/gate.py")

    res = _rodar(repo, "comparar", FOTO)
    assert res.returncode == 1, res.stdout
    assert "função validar_extra" in res.stdout


def test_remover_copia_identica_nao_acusa_orfao(repo):
    _escrever(repo, "tools/aidd-forge/gate.py", "def montar():\n    return 1\n")
    _git(repo, "add", ".")
    _fotografar(repo)
    _git(repo, "rm", "-q", "tools/aidd-forge/gate.py")

    res = _rodar(repo, "comparar", FOTO)
    assert res.returncode == 0, res.stdout


def test_mover_arquivo_nao_acusa_orfao(repo):
    _fotografar(repo)
    (repo / "componentes/almoxarifado").mkdir()
    _git(repo, "mv", "componentes/compartilhado/gate.py", "componentes/almoxarifado/gate.py")

    assert _rodar(repo, "comparar", FOTO).returncode == 0


def test_nomes_antigos_da_tabela_de_apelidos_nao_viram_orfao(repo):
    _fotografar(repo)
    _git(repo, "mv", "tools/aidd-generator", "tools/aidd-pure")
    _git(repo, "mv", "tools/aidd-pure/aidd_generator", "tools/aidd-pure/aidd_pure")
    gate = repo / "tools/aidd-pure/aidd_pure/gate.py"
    gate.write_text(gate.read_text(encoding="utf-8").replace("validar_extra", "validar_mais"), encoding="utf-8")
    # Nome antigo em outra caixa e comando de CLI renomeado; a prosa do .md é reescrita.
    _escrever(repo, "tools/aidd-pure/cli.py",
              "print('[AIDD-Pure] pronto')\nUSO = 'python ecossistema.py pure-motor <ideia>'\n")
    _escrever(repo, "componentes/compartilhado/comandos/generate.md", "# Comando /pure-motor\nGera um app.\n")

    assert _rodar(repo, "comparar", FOTO).returncode == 1  # sem tabela, a função renomeada some

    _escrever(repo, "componentes/compartilhado/specs/NOMES-ANTIGOS.json", json.dumps({
        "ferramentas": {"aidd-generator": "aidd-pure"},
        "pacotes_python": {"aidd_generator": "aidd_pure"},
        "funcoes_renomeadas": {"validar_extra": "validar_mais"},
        "comandos_cli": {"generate": "pure-motor"},
    }))
    res = _rodar(repo, "comparar", FOTO)
    assert res.returncode == 0, res.stdout


def test_linha_que_sumiu_de_todas_as_copias_acusa_orfao(repo):
    _fotografar(repo)
    gate = repo / "tools/aidd-generator/aidd_generator/gate.py"
    gate.write_text(gate.read_text(encoding="utf-8").replace("'so nesta copia'", "None"), encoding="utf-8")

    res = _rodar(repo, "comparar", FOTO)
    assert res.returncode == 1
    assert "so nesta copia" in res.stdout


def test_foto_ignora_arquivo_nao_rastreado_e_fora_de_tools_e_componentes(repo):
    _escrever(repo, "tools/aidd-generator/rascunho_local.py", "def lixo():\n    pass\n")
    _escrever(repo, ".claude/skills/espelho.py", "def espelho():\n    pass\n")
    _git(repo, "add", ".claude")
    _rodar(repo, "foto", "--cycle", CICLO)

    indice = json.loads((repo / FOTO).read_text(encoding="utf-8"))
    assert sorted(indice) == ["componentes/compartilhado/comandos/generate.md", "componentes/compartilhado/gate.py",
                              "componentes/compartilhado/test_gate.py", "tools/aidd-generator/aidd_generator/gate.py",
                              "tools/aidd-generator/cli.py"]
    assert indice["componentes/compartilhado/test_gate.py"]["testes"] == ["test_montar"]


def test_foto_nao_tem_nada_que_o_detect_secrets_acuse(repo):
    pytest.importorskip("detect_secrets")
    _escrever(repo, "tools/aidd-forge/test_segredos.py",
              "def test_chave_falsa():\n"
              "    aws = 'aws_key=AKIAIOSFODNN7EXAMPLE'  # pragma: allowlist secret\n"
              "    gh = 'ghp_1234567890abcdefghijklmnopqrstuvwxyz'  # pragma: allowlist secret\n")
    _git(repo, "add", ".")
    _rodar(repo, "foto", "--cycle", CICLO)

    with gzip.open(repo / f"{CICLO}/INVENTARIO-ANTES.linhas.json.gz", "rb") as gz:
        linhas = json.loads(gz.read().decode("utf-8"))
    assert len(linhas["tools/aidd-forge/test_segredos.py"]["sha256"]) == 64  # hash e linhas vão no .gz
    res = subprocess.run([sys.executable, "-m", "detect_secrets", "scan", FOTO,
                          f"{CICLO}/INVENTARIO-ANTES.linhas.json.gz"],
                         cwd=repo, capture_output=True, text=True, encoding="utf-8")
    assert json.loads(res.stdout)["results"] == {}, res.stdout


def test_foto_e_deterministica(repo):
    _rodar(repo, "foto", "--cycle", CICLO)
    primeira = [(repo / CICLO / n).read_bytes() for n in ("INVENTARIO-ANTES.json", "INVENTARIO-ANTES.linhas.json.gz")]
    _rodar(repo, "foto", "--cycle", CICLO)
    segunda = [(repo / CICLO / n).read_bytes() for n in ("INVENTARIO-ANTES.json", "INVENTARIO-ANTES.linhas.json.gz")]
    assert primeira == segunda
    assert b"\r\n" not in primeira[0]


def test_comparar_sem_foto_reprova(repo):
    assert _rodar(repo, "comparar", FOTO).returncode == 1
