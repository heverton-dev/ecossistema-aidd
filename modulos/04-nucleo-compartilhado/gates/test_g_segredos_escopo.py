# -*- coding: utf-8 -*-
"""
modulos/04-nucleo-compartilhado/gates/test_g_segredos_escopo.py — Escopo de varredura do G_SEGREDOS (Ticket 3, D3).

Regras sob prova em modulos/04-nucleo-compartilhado/gates/G_SEGREDOS.py:
  * modo 'rapido' (padrao) varre APENAS os arquivos staged do commit em curso,
    resolvidos por gates/_escopo_commit.arquivos_staged() e filtrados pelos que
    existem em disco;
  * arquivo rastreado por git mas NAO staged nao entra na varredura rapida;
  * modo 'completo' (AIDD_GATES_MODO=completo) mantem a varredura de todos os
    arquivos rastreados (git ls-files), incluindo os que nao estao staged;
  * stage vazio em modo 'rapido' aprova sem varrer nada;
  * o baseline gerado de verdade (detect-secrets scan) continua autorizando o
    segredo ja catalogado do arquivo staged, inclusive quando o baseline foi
    gravado com barras invertidas (gerado no Windows).

Cada cenário monta um repositorio git sintetico em tmp_path com o gate real
(G_SEGREDOS.py) e o resolvedor de escopo (_escopo_commit.py) copiados para
dentro dele, e roda o gate de verdade via subprocess: o codigo de saida
verificado em cada assert e o exit code real do processo.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from _gate_test_utils import rodar_gate

GATES_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATES_DIR, "G_SEGREDOS.py")
ESCOPO_PATH = os.path.join(GATES_DIR, "_escopo_commit.py")

# Chave AWS ficticia usada pelos detectores do detect-secrets (mesma fixture do
# test_g_segredos.py: o detector de AWS Access Key a classifica como segredo).
# Montada em runtime: o literal inteiro no arquivo seria um achado real do G_SEGREDOS
# em modo completo (o gate_final de 30/09/2026 reprovou exatamente por isso).
SEGREDO_AWS = "AKIA" + "IOSFODNN7EXAMPLE"

# Dentro do pre-commit o git exporta estas variaveis; se elas vazarem para o
# `git diff --cached` executado pelo gate, o escopo seria lido do indice do
# repositorio real em vez do repositorio sintetico do teste.
VARIAVEIS_DE_REPOSITORIO_DO_HOOK = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)


@pytest.fixture
def modo_do_gate(monkeypatch):
    """Fixa AIDD_GATES_MODO no ambiente herdado pelo subprocesso do gate."""

    def _usar(modo):
        for chave in VARIAVEIS_DE_REPOSITORIO_DO_HOOK:
            monkeypatch.delenv(chave, raising=False)
        monkeypatch.setenv("AIDD_GATES_MODO", modo)

    return _usar


def _git(raiz, *args):
    return subprocess.run(
        ["git", *args],
        cwd=str(raiz),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _escrever(raiz, caminho, texto):
    alvo = Path(raiz) / caminho
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(texto, encoding="utf-8")
    return alvo


def _comitar(raiz, msg="commit de teste"):
    subprocess.run(
        [
            "git",
            "-c", "user.email=test@example.com",
            "-c", "user.name=Test Runner",
            "-c", "commit.gpgsign=false",
            "commit",
            "-q",
            "-m", msg,
        ],
        cwd=str(raiz),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _rodar(raiz):
    return rodar_gate(Path(raiz) / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_SEGREDOS.py", raiz)


def _repo_limpo(tmp_path):
    """git init + gate e resolvedor de escopo copiados + README limpo, tudo commitado."""
    raiz = tmp_path / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "test@example.com")
    _git(raiz, "config", "user.name", "Test Runner")

    (raiz / "modulos" / "04-nucleo-compartilhado" / "gates").mkdir(parents=True)
    shutil.copyfile(GATE_PATH, raiz / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_SEGREDOS.py")
    shutil.copyfile(ESCOPO_PATH, raiz / "modulos" / "04-nucleo-compartilhado" / "gates" / "_escopo_commit.py")
    _escrever(raiz, "README.md", "# Repositorio Limpo\nNenhum segredo aqui.\n")

    _git(raiz, "add", "-A")
    _comitar(raiz, "base limpa")
    return raiz


def _repo_com_segredo_rastreado_fora_do_stage(tmp_path):
    """Arquivo versionado e limpo no HEAD, com segredo apenas em disco (nao staged)."""
    raiz = _repo_limpo(tmp_path)
    _escrever(raiz, "config/app.py", "AWS_ACCESS_KEY_ID = ''\n")
    _git(raiz, "add", "config/app.py")
    _comitar(raiz, "arquivo rastreado e limpo")
    _escrever(raiz, "config/app.py", f"AWS_ACCESS_KEY_ID = '{SEGREDO_AWS}'\n")
    return raiz


def _gerar_baseline_real(raiz):
    """Roda o detect-secrets de verdade e grava o baseline no repositorio sintetico."""
    resultado = subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan"],
        cwd=str(raiz),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (Path(raiz) / ".secrets.baseline").write_text(resultado.stdout, encoding="utf-8")


def _converter_baseline_para_barras_invertidas(raiz):
    """Regrava as chaves de results no formato Windows (barras invertidas)."""
    caminho = Path(raiz) / ".secrets.baseline"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["results"] = {
        chave.replace("/", "\\"): valor
        for chave, valor in dados.get("results", {}).items()
    }
    caminho.write_text(json.dumps(dados, indent=2) + "\n", encoding="utf-8")


def test_segredo_novo_em_arquivo_staged_reprova_no_modo_rapido(tmp_path, modo_do_gate):
    """O que estao no stage do commit emcurso e obrigatoriamente varrido."""
    raiz = _repo_limpo(tmp_path)
    _escrever(raiz, "config/app.py", f"AWS_ACCESS_KEY_ID = '{SEGREDO_AWS}'\n")
    _git(raiz, "add", "config/app.py")
    modo_do_gate("rapido")

    res = _rodar(raiz)

    assert res.returncode == 1, f"Falhou unexpectedly:\n{res.stdout}\n{res.stderr}"
    assert "[INFO] Escopo rapido: 1 arquivo(s)" in res.stdout
    assert "Quality Gate REPROVADO" in res.stdout
    assert "AWS Access Key" in res.stdout


def test_modo_rapido_nao_varre_arquivo_rastreado_e_nao_staged(tmp_path, modo_do_gate):
    """Rastreado no HEAD, alterado so em disco: fora do escopo do commit emcurso."""
    raiz = _repo_com_segredo_rastreado_fora_do_stage(tmp_path)
    modo_do_gate("rapido")

    res = _rodar(raiz)

    assert res.returncode == 0, f"Falhou unexpectedly:\n{res.stdout}\n{res.stderr}"
    assert "[INFO] Escopo rapido: 0 arquivo(s)" in res.stdout
    assert "AWS Access Key" not in res.stdout
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout


def test_modo_completo_varre_todos_os_arquivos_rastreados(tmp_path, modo_do_gate):
    """No modo completo o mesmo arquivo nao staged volta a ser varrido (git ls-files)."""
    raiz = _repo_com_segredo_rastreado_fora_do_stage(tmp_path)
    modo_do_gate("completo")

    res = _rodar(raiz)

    assert res.returncode == 1, f"Falhou unexpectedly:\n{res.stdout}\n{res.stderr}"
    assert "[INFO] Escopo completo:" in res.stdout
    assert "AWS Access Key" in res.stdout
    assert "Quality Gate REPROVADO" in res.stdout


def test_modo_rapido_ignora_arquivo_untracked(tmp_path, modo_do_gate):
    """Arquivo nunca versionado nao faz parte do commit emcurso."""
    raiz = _repo_limpo(tmp_path)
    _escrever(raiz, "rascunho.txt", f"AWS_ACCESS_KEY_ID = '{SEGREDO_AWS}'\n")
    modo_do_gate("rapido")

    res = _rodar(raiz)

    assert res.returncode == 0, f"Falhou unexpectedly:\n{res.stdout}\n{res.stderr}"
    assert "[INFO] Escopo rapido: 0 arquivo(s)" in res.stdout
    assert "AWS Access Key" not in res.stdout


def test_modo_rapido_com_stage_vazio_aprova(tmp_path, modo_do_gate):
    """Nada staged, nada a varrer: o gate rapido aprova sem reprovar por escopo vazio."""
    raiz = _repo_limpo(tmp_path)
    modo_do_gate("rapido")

    res = _rodar(raiz)

    assert res.returncode == 0, f"Falhou unexpectedly:\n{res.stdout}\n{res.stderr}"
    assert "[INFO] Escopo rapido: 0 arquivo(s)" in res.stdout
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout


def test_modo_rapido_respeita_baseline_do_arquivo_staged(tmp_path, modo_do_gate):
    """Baseline real continua autorizando o segredo ja catalogado do arquivo staged."""
    raiz = _repo_limpo(tmp_path)
    _escrever(raiz, "config/app.py", f"AWS_ACCESS_KEY_ID = '{SEGREDO_AWS}'\n")
    _git(raiz, "add", "-A")
    _comitar(raiz, "arquivo com segredo")
    _gerar_baseline_real(raiz)
    _git(raiz, "add", "-A")
    _comitar(raiz, "baseline")

    # Alteracao no arquivo catalogado: o segredo continua sendo o mesmo do baseline.
    _escrever(
        raiz,
        "config/app.py",
        f"AWS_ACCESS_KEY_ID = '{SEGREDO_AWS}'\n# ajuste de comentario\n",
    )
    _git(raiz, "add", "config/app.py")
    modo_do_gate("rapido")

    res = _rodar(raiz)

    assert res.returncode == 0, f"Falhou unexpectedly:\n{res.stdout}\n{res.stderr}"
    assert "[INFO] Escopo rapido: 1 arquivo(s)" in res.stdout
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout


@pytest.mark.skipif(
    os.name != "nt",
    reason="a normalizacao para barras invertidas so ocorre no Windows",
)
def test_modo_rapido_com_baseline_em_barras_invertidas_aprova(tmp_path, modo_do_gate):
    """Baseline gravado no Windows (chaves com barra invertida) casa com o caminho staged."""
    raiz = _repo_limpo(tmp_path)
    _escrever(raiz, "config/app.py", f"AWS_ACCESS_KEY_ID = '{SEGREDO_AWS}'\n")
    _git(raiz, "add", "-A")
    _comitar(raiz, "arquivo com segredo")
    _gerar_baseline_real(raiz)
    _converter_baseline_para_barras_invertidas(raiz)
    _git(raiz, "add", "-A")
    _comitar(raiz, "baseline em barras invertidas")

    _escrever(
        raiz,
        "config/app.py",
        f"AWS_ACCESS_KEY_ID = '{SEGREDO_AWS}'\n# ajuste de comentario\n",
    )
    _git(raiz, "add", "config/app.py")
    modo_do_gate("rapido")

    res = _rodar(raiz)

    assert res.returncode == 0, f"Falhou unexpectedly:\n{res.stdout}\n{res.stderr}"
    assert "[INFO] Escopo rapido: 1 arquivo(s)" in res.stdout
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout