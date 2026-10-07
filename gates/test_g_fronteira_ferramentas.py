# -*- coding: utf-8 -*-
"""
Testes do Quality Gate G_FRONTEIRA_FERRAMENTAS — Ciclo 01, Ticket 6 (D1).

Lei #13 (o portão precisa provar que morde): cada teste planta violações reais
num repositório Git temporário e exige o exit code real capturado do subprocess:
  - modo aviso   (AIDD_FRONTEIRA_MODO=aviso)   → exit 0, relatório impresso;
  - modo bloqueio(AIDD_FRONTEIRA_MODO=bloqueio)→ exit 1 sob violação não perdoada;
  - allowlist_fronteira.json só pode diminuir (crescimento reprova o teste).
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GATE_SCRIPT = RAIZ / "gates" / "G_FRONTEIRA_FERRAMENTAS.py"
MAPA_REAL = RAIZ / "componentes" / "compartilhado" / "specs" / "MAPA-DONOS-FERRAMENTAS.json"
ALLOWLIST_REAL = RAIZ / "gates" / "allowlist_fronteira.json"

# Limite congelado da allowlist (número de entradas conhecidas com data).
# Só pode diminuir: se gates/allowlist_fronteira.json crescer, o teste reprova.
BASELINE_ALLOWLIST = 172

PIECA = "modulos/02-triade-motores/fluxo-02-open/core/aidd-open/templates/dominio/peca.py"
COPIA = "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/dominio/peca.py"
DOCKERFILE = "modulos/02-triade-motores/fluxo-02-open/core/aidd-open/Dockerfile"
ARQUIVO_LIMPO = "modulos/02-triade-motores/fluxo-02-open/core/aidd-open/scripts/limpo.py"
CONTEUDO_PECA = "peca canonica do almoxarifado — ticket 6 fronteira\n"


def _subprocesso(args, cwd, modo=None):
    env = os.environ.copy()
    env.pop("AIDD_FRONTEIRA_MODO", None)
    if modo is not None:
        env["AIDD_FRONTEIRA_MODO"] = modo
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _git(cwd, *args):
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, f"git {' '.join(args)} falhou: {r.stderr}"
    return r


def montar_repo(tmp_path, violacoes=True):
    """Monta repo Git temporário com o mapa de donos real, catálogo mínimo e o gate."""
    mapa_dir = tmp_path / "componentes" / "compartilhado" / "specs"
    mapa_dir.mkdir(parents=True)
    shutil.copy(MAPA_REAL, mapa_dir / "MAPA-DONOS-FERRAMENTAS.json")

    catalogo = {
        "versao": 1,
        "gerado_por": "test_g_fronteira_ferramentas",
        "ferramentas": [
            {
                "id": "aidd-open",
                "entrada_cli": "modulos/02-triade-motores/fluxo-02-open/core/aidd-open/scripts/pipeline_factory.py",
                "gates_proprios": [PIECA if violacoes else ARQUIVO_LIMPO],
            }
        ],
    }
    docs_dir = tmp_path / "docs" / "auditoria" / "mapa-pecas"
    docs_dir.mkdir(parents=True)
    (docs_dir / "catalogo-pecas.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    if violacoes:
        for caminho in (PIECA, COPIA):
            alvo = tmp_path / caminho
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(CONTEUDO_PECA, encoding="utf-8")
        docker = tmp_path / DOCKERFILE
        docker.parent.mkdir(parents=True, exist_ok=True)
        docker.write_text("FROM alpine:3.20\n", encoding="utf-8")
    else:
        limpo = tmp_path / ARQUIVO_LIMPO
        limpo.parent.mkdir(parents=True, exist_ok=True)
        limpo.write_text("x = 1\n", encoding="utf-8")

    gates_dir = tmp_path / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    (gates_dir / "allowlist_fronteira.json").write_text(
        json.dumps({"violacoes": []}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    shutil.copy(GATE_SCRIPT, gates_dir / "G_FRONTEIRA_FERRAMENTAS.py")

    _git(tmp_path, "init")
    _git(tmp_path, "add", "-A")
    return gates_dir / "G_FRONTEIRA_FERRAMENTAS.py"


def rodar(gate, cwd, modo=None):
    return _subprocesso([str(gate)], cwd, modo=modo)


def conferir_allowlist(caminho, baseline):
    """Só pode diminuir: reprova (AssertionError) se a allowlist crescer."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    total = len(dados.get("violacoes", []))
    assert total <= baseline, (
        f"allowlist_fronteira.json cresceu: {total} entradas > baseline {baseline}"
    )


def test_aviso_reporta_dockerfile_e_copia_com_dono_e_sai_zero(tmp_path):
    """Modo aviso imprime arquivo, ferramenta atual e dono certo para as 2 violações, exit 0."""
    gate = montar_repo(tmp_path, violacoes=True)
    res = rodar(gate, tmp_path, modo="aviso")
    assert res.returncode == 0, res.stdout + res.stderr

    linha_docker = [l for l in res.stdout.splitlines() if DOCKERFILE in l]
    assert linha_docker, f"violação {DOCKERFILE} não reportada:\n{res.stdout}"
    assert any("ferramenta_atual=aidd-open" in l for l in linha_docker)
    assert any("dono_certo=aidd-ops" in l for l in linha_docker), (
        f"dono certo de Dockerfile deveria ser aidd-ops:\n{res.stdout}"
    )

    linha_copia = [l for l in res.stdout.splitlines() if COPIA in l and "copia" in l]
    assert linha_copia, f"cópia de peça do catálogo não reportada:\n{res.stdout}"
    assert any("ferramenta_atual=aidd-master" in l for l in linha_copia)
    assert any("dono_certo=aidd-open" in l for l in linha_copia), (
        f"dono da peça {PIECA} deveria ser aidd-open:\n{res.stdout}"
    )


def test_aviso_passa_com_flag_ou_env_sai_zero(tmp_path):
    """Com --modo aviso ou AIDD_FRONTEIRA_MODO=aviso, o gate sai 0 mesmo com violações."""
    gate = montar_repo(tmp_path, violacoes=True)
    res = rodar(gate, tmp_path, modo="aviso")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "modo=aviso" in res.stdout


def test_padrao_sem_env_e_bloqueio_sai_um(tmp_path):
    """Sem AIDD_FRONTEIRA_MODO no ambiente (padrão a partir do Ticket 20), o padrão é bloqueio → exit 1 sob violação."""
    gate = montar_repo(tmp_path, violacoes=True)
    res = rodar(gate, tmp_path, modo=None)
    assert res.returncode == 1, res.stdout + res.stderr
    assert "modo=bloqueio" in res.stdout


def test_bloqueio_reprova_violacoes_com_exit_1(tmp_path):
    """Lei #13: modo bloqueio reprova (exit 1) sob violação real plantada."""
    gate = montar_repo(tmp_path, violacoes=True)
    res = rodar(gate, tmp_path, modo="bloqueio")
    assert res.returncode == 1, res.stdout + res.stderr
    assert DOCKERFILE in res.stdout
    assert COPIA in res.stdout


def test_bloqueio_repo_limpo_sai_zero(tmp_path):
    """Modo bloqueio aprova (exit 0) quando não há violação nenhuma."""
    gate = montar_repo(tmp_path, violacoes=False)
    res = rodar(gate, tmp_path, modo="bloqueio")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "restantes=0" in res.stdout


def test_allowlist_perdoa_violacoes_conhecidas(tmp_path):
    """Entrada datada na allowlist perdoa a violação: bloqueio sai 0 e conta perdoadas."""
    gate = montar_repo(tmp_path, violacoes=True)
    allowlist = {
        "violacoes": [
            {"arquivo": DOCKERFILE, "data": "2026-09-01", "motivo": "violação conhecida"},
            {"arquivo": COPIA, "data": "2026-09-01", "motivo": "violação conhecida"},
        ]
    }
    (tmp_path / "gates" / "allowlist_fronteira.json").write_text(
        json.dumps(allowlist, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    res = rodar(gate, tmp_path, modo="bloqueio")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "perdoadas=2" in res.stdout
    assert "restantes=0" in res.stdout


def test_morde_mapa_de_donos_ausente(tmp_path):
    """Lei #13: sem o mapa de donos o gate reprova sempre (exit 1), até em modo aviso."""
    gate = montar_repo(tmp_path, violacoes=True)
    (tmp_path / "componentes" / "compartilhado" / "specs" / "MAPA-DONOS-FERRAMENTAS.json").unlink()
    res = rodar(gate, tmp_path, modo="aviso")
    assert res.returncode == 1, res.stdout + res.stderr
    assert "MAPA-DONOS-FERRAMENTAS" in res.stdout


def test_morde_modo_invalido(tmp_path):
    """Modo desconhecido é erro de configuração → exit 1."""
    gate = montar_repo(tmp_path, violacoes=False)
    res = rodar(gate, tmp_path, modo="escavando")
    assert res.returncode == 1, res.stdout + res.stderr
    assert "AIDD_FRONTEIRA_MODO" in res.stdout


def test_allowlist_real_esta_no_baseline():
    """A allowlist real do repositório não pode crescer acima do baseline congelado."""
    assert ALLOWLIST_REAL.exists(), f"Allowlist não encontrada: {ALLOWLIST_REAL}"
    conferir_allowlist(ALLOWLIST_REAL, BASELINE_ALLOWLIST)


def test_morde_allowlist_crescida(tmp_path):
    """Prova que a checagem de crescimento da allowlist morde: baseline+1 → AssertionError."""
    cresceu = tmp_path / "allowlist_fronteira.json"
    entradas = [{"arquivo": f"modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/x{i}.py", "data": "2026-09-01"} for i in range(3)]
    cresceu.write_text(json.dumps({"violacoes": entradas}), encoding="utf-8")
    with pytest.raises(AssertionError):
        conferir_allowlist(cresceu, 2)


def test_repositorio_real_modo_aviso_sai_zero():
    """Estado real do repositório em modo aviso: exit 0 (relatório é só aviso)."""
    res = rodar(GATE_SCRIPT, RAIZ, modo="aviso")
    assert res.returncode == 0, res.stdout + res.stderr


def test_repositorio_real_modo_bloqueio_sai_zero():
    """Estado real em modo bloqueio: todas as violações conhecidas estão na allowlist → exit 0."""
    res = rodar(GATE_SCRIPT, RAIZ, modo="bloqueio")
    assert res.returncode == 0, res.stdout + res.stderr
