# -*- coding: utf-8 -*-
"""
Teste de rollback transacional de aidd-forge (Ticket 8 / D14 / DoD 7).
Exige:
- Falha injetada no meio do bootstrap -> nenhum arquivo órfão sobrevive;
  diretório alvo restaurado ao estado limpo original.
- Journal transacional permite recuperação de falha abrupta (crash).
- Escrita fora da raiz do alvo bloqueada (confinamento).
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
RB_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "rollback.py"
JOURNAL = ".FORGE-ROLLBACK-JOURNAL.json"


def carregar_rollback():
    spec = importlib.util.spec_from_file_location("aidd_forge_rollback", str(RB_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_rollback():
    rb = carregar_rollback()
    assert hasattr(rb, "TransacaoForge")
    assert hasattr(rb, "executar_com_rollback")
    assert hasattr(rb, "recuperar")
    assert hasattr(rb, "main")


def test_falha_no_meio_do_bootstrap_deixa_zero_orfaos(tmp_path):
    rb = carregar_rollback()
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    original = {"manter.txt"}
    (alvo / "manter.txt").write_text("pre-existente\n", encoding="utf-8")

    def etapa_1(tx):
        tx.escriturar("arquivo_a.txt", "conteudo a\n")
        tx.escriturar("sub/b.txt", "conteudo b\n")

    def etapa_2(tx):
        tx.escriturar("arquivo_c.txt", "conteudo c\n")
        raise RuntimeError("falha injetada no meio do bootstrap")

    codigo = rb.executar_com_rollback(alvo, [etapa_1, etapa_2])
    assert codigo == 1

    restantes = {p.name for p in alvo.iterdir()}
    assert restantes == original, f"arquivos órfãos sobraram: {restantes}"
    assert not (alvo / "sub").exists(), "diretório criado pela transação deve ser removido"
    assert not (alvo / JOURNAL).exists(), "journal não pode sobreviver ao rollback"


def test_commit_mantem_arquivos_e_saida_0(tmp_path):
    rb = carregar_rollback()
    alvo = tmp_path / "alvo"
    alvo.mkdir()

    def etapa_1(tx):
        tx.escriturar("ok.txt", "ok\n")

    assert rb.executar_com_rollback(alvo, [etapa_1]) == 0
    assert (alvo / "ok.txt").read_text(encoding="utf-8") == "ok\n"
    assert not (alvo / JOURNAL).exists()


def test_arquivo_pre_existente_nao_e_revertido(tmp_path):
    """Rollback só remove o que a própria transação criou."""
    rb = carregar_rollback()
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    (alvo / "pre_existente.txt").write_text("nao mexer\n", encoding="utf-8")

    def etapa(tx):
        tx.escriturar("novo.txt", "novo\n")
        raise RuntimeError("aborta")

    assert rb.executar_com_rollback(alvo, [etapa]) == 1
    assert (alvo / "pre_existente.txt").read_text(encoding="utf-8") == "nao mexer\n"
    assert not (alvo / "novo.txt").exists()


def test_escritura_fora_da_raiz_e_bloqueada(tmp_path):
    rb = carregar_rollback()
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    tx = rb.TransacaoForge(alvo)
    with pytest.raises(Exception):
        tx.escriturar("../fuga.py", "fuga\n")
    assert not (tmp_path / "fuga.py").exists()


def test_recuperacao_por_journal_apos_crash(tmp_path):
    """Crash abrupto: journal presente -> main() remove órfãos com exit 0."""
    rb = carregar_rollback()
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    orfao = alvo / "orfao.txt"
    orfao.write_text("sobrou\n", encoding="utf-8")
    sub = alvo / "sub"
    sub.mkdir()
    (sub / "intern.txt").write_text("sobrou\n", encoding="utf-8")
    (alvo / JOURNAL).write_text(
        json.dumps({"versao": 1, "arquivos": ["orfao.txt", "sub/intern.txt"], "dirs": ["sub"]}),
        encoding="utf-8",
    )

    assert rb.main([str(alvo)]) == 0
    assert not orfao.exists()
    assert not sub.exists()
    assert not (alvo / JOURNAL).exists()


def test_main_sem_argumento_exit_1():
    rb = carregar_rollback()
    assert rb.main([]) == 1


def test_main_sem_journal_exit_0_idempotente(tmp_path):
    rb = carregar_rollback()
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    assert rb.main([str(alvo)]) == 0


def test_subprocesso_exit_1_e_diretorio_limpo(tmp_path):
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    (alvo / "base.txt").write_text("base\n", encoding="utf-8")
    script = tmp_path / "falha_bootstrap.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('rb', r'{RB_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            f"alvo = r'{alvo}'\n"
            "def etapa1(tx):\n"
            "    tx.escriturar('etapa1.txt', 'x')\n"
            "def etapa2(tx):\n"
            "    tx.escriturar('pasta/etapa2.txt', 'y')\n"
            "    raise RuntimeError('boom')\n"
            "sys.exit(mod.executar_com_rollback(alvo, [etapa1, etapa2]))\n"
        ),
        encoding="utf-8",
    )
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=120)
    assert res.returncode == 1, f"esperava exit 1 (obtido {res.returncode})"
    restantes = sorted(p.name for p in alvo.iterdir())
    assert restantes == ["base.txt"], f"órfãos sobraram: {restantes}"
