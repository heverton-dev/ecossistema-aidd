# -*- coding: utf-8 -*-
"""
Testes do gate G_DEPENDENCIAS_PIN_HASH — valida deteccao de pin solto,
lockfile sem hash e CI sem --require-hashes, executando o gate real
(copiado) contra uma arvore sintetica isolada em tmp_path (nunca contra o
repositorio de producao — mesma tecnica de isolamento de
test_g_honestidade_rotulo.py).
"""

import os
import shutil

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_DEPENDENCIAS_PIN_HASH.py")

WORKFLOW_OK = """\
name: Auditoria
on: [push]
jobs:
  gates-raiz:
    steps:
      - name: Instalar dependências da raiz
        run: |
          python -m pip install --upgrade pip
          pip install --require-hashes -r requirements-dev.lock
"""

WORKFLOW_SEM_HASH = """\
name: Auditoria
on: [push]
jobs:
  gates-raiz:
    steps:
      - name: Instalar dependências da raiz
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
"""


def _preparar_gate_sintetico(root_dir):
    gdir = os.path.join(root_dir, "gates")
    os.makedirs(gdir, exist_ok=True)
    shutil.copyfile(GATE_PATH, os.path.join(gdir, "G_DEPENDENCIAS_PIN_HASH.py"))
    return gdir


def _escrever(caminho, conteudo):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def _montar_arvore_valida(root_dir):
    _preparar_gate_sintetico(root_dir)
    _escrever(
        os.path.join(root_dir, "requirements.txt"),
        "# comentario\nrequests==2.34.2\nclick==8.5.0\n",
    )
    _escrever(
        os.path.join(root_dir, "requirements.lock"),
        "requests==2.34.2 \\\n"
        "    --hash=sha256:aaaa\n"
        "    # via requirements.txt\n"
        "click==8.5.0 \\\n"
        "    --hash=sha256:bbbb\n",
    )
    _escrever(
        os.path.join(root_dir, "requirements-dev.txt"),
        "-r requirements.txt\npytest==9.1.1\n",
    )
    _escrever(
        os.path.join(root_dir, "requirements-dev.lock"),
        "requests==2.34.2 \\\n"
        "    --hash=sha256:aaaa\n"
        "click==8.5.0 \\\n"
        "    --hash=sha256:bbbb\n"
        "pytest==9.1.1 \\\n"
        "    --hash=sha256:cccc\n",
    )
    _escrever(
        os.path.join(root_dir, ".github/workflows/audit.yml"), WORKFLOW_OK
    )


def test_arvore_valida_aprova(tmp_path):
    _montar_arvore_valida(tmp_path)
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_DEPENDENCIAS_PIN_HASH APROVADO" in res.stdout


def test_especificador_solto_e_detectado(tmp_path):
    _montar_arvore_valida(tmp_path)
    _escrever(
        os.path.join(tmp_path, "requirements.txt"),
        "requests>=2.34.2\nclick==8.5.0\n",
    )
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 1
    assert "Quality Gate REPROVADO" in res.stdout
    assert "requirements.txt:1" in res.stdout
    assert "nao e pin exato" in res.stdout


def test_pacote_sem_versao_e_detectado(tmp_path):
    _montar_arvore_valida(tmp_path)
    _escrever(
        os.path.join(tmp_path, "requirements.txt"),
        "requests\nclick==8.5.0\n",
    )
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 1
    assert "requirements.txt:1" in res.stdout


def test_instalacao_editable_url_e_detectada(tmp_path):
    _montar_arvore_valida(tmp_path)
    _escrever(
        os.path.join(tmp_path, "requirements.txt"),
        "-e git+https://github.com/exemplo/repo.git#egg=exemplo\nclick==8.5.0\n",
    )
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 1
    assert "editable/VCS/URL" in res.stdout


def test_lockfile_ausente_e_detectado(tmp_path):
    _montar_arvore_valida(tmp_path)
    os.remove(os.path.join(tmp_path, "requirements.lock"))
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 1
    assert "requirements.lock — lockfile nao encontrado" in res.stdout


def test_pacote_do_lock_sem_hash_e_detectado(tmp_path):
    _montar_arvore_valida(tmp_path)
    _escrever(
        os.path.join(tmp_path, "requirements.lock"),
        "requests==2.34.2\n"  # sem --hash= associado
        "click==8.5.0 \\\n"
        "    --hash=sha256:bbbb\n",
    )
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 1
    assert "requests" in res.stdout
    assert "sem nenhum --hash=sha256" in res.stdout


def test_ci_sem_require_hashes_e_detectado(tmp_path):
    _montar_arvore_valida(tmp_path)
    _escrever(os.path.join(tmp_path, ".github/workflows/audit.yml"), WORKFLOW_SEM_HASH)
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 1
    assert "nenhuma instalacao usa '--require-hashes'" in res.stdout


def test_linha_de_include_e_comentario_nao_sao_falso_positivo(tmp_path):
    _montar_arvore_valida(tmp_path)
    _escrever(
        os.path.join(tmp_path, "requirements-dev.txt"),
        "# comentario com >= dentro, nunca deve ser lido como pin\n"
        "-r requirements.txt\n"
        "\n"
        "pytest==9.1.1  # comentario inline\n",
    )
    res = rodar_gate(os.path.join(tmp_path, "gates", "G_DEPENDENCIAS_PIN_HASH.py"), tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_DEPENDENCIAS_PIN_HASH APROVADO" in res.stdout
