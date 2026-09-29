# -*- coding: utf-8 -*-
"""
Teste do rollback transacional de aidd-enterprise (Ticket 8 / D14).
Exige:
- Context manager transacional com snapshot pre-injecao: falha no meio da
  transacao reverte arquivos modificados, purga artefatos parciais e deixa o
  workspace limpo (zero orfaos) -> exit 1.
- Sucesso faz commit (exit 0) preservando o que foi escrito.
- Recuperacao pos-crash via journal; workspace sujo -> exit 1.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
ROLLBACK_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-enterprise" / "scripts" / "rollback.py"
JOURNAL = ".ENTERPRISE-ROLLBACK-JOURNAL.json"
SNAPSHOT_DIR = ".ENTERPRISE-SNAPSHOT"


def carregar_rollback():
    spec = importlib.util.spec_from_file_location("aidd_enterprise_rollback", str(ROLLBACK_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def raiz_limpa(raiz: Path, exceto=()) -> bool:
    proibidos = {JOURNAL, SNAPSHOT_DIR, "novo_componente.md"}
    proibidos.difference_update(exceto)
    encontrados = {p.name for p in raiz.iterdir()}
    return not (encontrados & proibidos)


def test_import_rollback():
    mod = carregar_rollback()
    assert hasattr(mod, "TransacaoEnterprise")
    assert hasattr(mod, "executar_com_rollback")
    assert hasattr(mod, "recuperar")
    assert hasattr(mod, "workspace_limpo")
    assert hasattr(mod, "main")


def test_falha_no_meio_da_transacao_deixa_zero_orfaos(tmp_path):
    """Injecao falha no meio -> exit 1, orfaos removidos, snapshot e journal purgados."""
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    (raiz / "pre_existente.txt").write_text("conteudo original\n", encoding="utf-8")

    def etapa_1(tx):
        tx.escriturar("novo_componente.md", "# novo\n")
        tx.escriturar("pre_existente.txt", "sobrescrito pela injecao\n")

    def etapa_2(tx):
        raise RuntimeError("falha abrupta na injecao")

    codigo = mod.executar_com_rollback(raiz, [etapa_1, etapa_2])
    assert codigo == 1, "falha no meio da transacao deve retornar exit 1"
    assert not (raiz / "novo_componente.md").exists(), "artefato parcial deve ser purgado"
    assert (raiz / "pre_existente.txt").read_text(encoding="utf-8") == "conteudo original\n", (
        "arquivo modificado deve ser revertido ao snapshot pre-injecao"
    )
    assert raiz_limpa(raiz), f"workspace deve ficar limpo apos rollback: {sorted(p.name for p in raiz.iterdir())}"
    assert mod.workspace_limpo(raiz)


def test_commit_mantem_arquivos_e_saida_0(tmp_path):
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()

    def etapa(tx):
        tx.escriturar("novo_componente.md", "# commitado\n")

    assert mod.executar_com_rollback(raiz, [etapa]) == 0
    assert (raiz / "novo_componente.md").read_text(encoding="utf-8") == "# commitado\n"
    assert raiz_limpa(raiz, exceto=("novo_componente.md",))
    assert mod.workspace_limpo(raiz)


def test_arquivo_pre_existente_restaurado_apos_falha(tmp_path):
    """Snapshot pre-injecao restaura bytes originais de arquivos modificados."""
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    original = "estado previo do componente\n"
    (raiz / "componente.md").write_text(original, encoding="utf-8")

    def etapa(tx):
        tx.escriturar("componente.md", "estado corrompido\n")
        raise ValueError("injecao abortada")

    with pytest.raises(ValueError):
        with mod.TransacaoEnterprise(raiz) as tx:
            etapa(tx)
    assert (raiz / "componente.md").read_text(encoding="utf-8") == original
    assert raiz_limpa(raiz)


def test_escritura_fora_da_raiz_e_bloqueada(tmp_path):
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    with pytest.raises(PermissionError):
        with mod.TransacaoEnterprise(raiz) as tx:
            tx.escriturar("../fuga.md", "nao pode")
    assert not (tmp_path / "fuga.md").exists()


def test_recuperacao_por_journal_apos_crash(tmp_path):
    """Crash abrupto deixa journal+snapshot; recuperar() reverte e limpa."""
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    (raiz / "alvo.txt").write_text("previo\n", encoding="utf-8")

    tx = mod.TransacaoEnterprise(raiz)
    tx.escriturar("alvo.txt", "sobrescrito\n")
    tx.escriturar("orfao.md", "parcial\n")
    # simula crash: nao chama concluir() nem desfazer() (journal e snapshot ficam)
    assert (raiz / JOURNAL).is_file()
    assert (raiz / SNAPSHOT_DIR).is_dir()

    removidos = mod.recuperar(raiz)
    assert removidos, "recuperacao deve remover/restaurar itens"
    assert (raiz / "alvo.txt").read_text(encoding="utf-8") == "previo\n"
    assert not (raiz / "orfao.md").exists()
    assert raiz_limpa(raiz)
    assert mod.workspace_limpo(raiz)


def test_main_sem_argumento_exit_1():
    mod = carregar_rollback()
    assert mod.main([]) == 1


def test_main_sem_journal_exit_0_idempotente(tmp_path):
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    assert mod.main([str(raiz)]) == 0


def test_main_recupera_e_confirma_limpeza(tmp_path):
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    tx = mod.TransacaoEnterprise(raiz)
    tx.escriturar("orfao.md", "lixo\n")
    assert mod.main([str(raiz)]) == 0
    assert raiz_limpa(raiz)


def test_main_journal_corrompido_exit_1(tmp_path):
    """Journal corrompido impede garantir limpeza -> exit 1."""
    mod = carregar_rollback()
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    (raiz / JOURNAL).write_text("{corrompido", encoding="utf-8")
    assert mod.main([str(raiz)]) == 1


def test_subprocesso_exit_1_e_diretorio_limpo(tmp_path):
    """End-to-end: injecao que falha termina com exit 1 e workspace limpo."""
    raiz = tmp_path / "alvo"
    raiz.mkdir()
    script = tmp_path / "injecao.py"
    script.write_text(
        (
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('rb', r'{ROLLBACK_PATH}')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "def ok(tx):\n"
            "    tx.escriturar('parcial.md', 'parcial')\n"
            "def quebra(tx):\n"
            "    raise RuntimeError('injecao falhou')\n"
            f"sys.exit(mod.executar_com_rollback(r'{raiz}', [ok, quebra]))\n"
        ),
        encoding="utf-8",
    )
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert res.returncode == 1, f"injecao falha deve terminar com exit 1 (obtido {res.returncode})"
    assert not (raiz / "parcial.md").exists()
    assert not (raiz / JOURNAL).exists()
    assert not (raiz / SNAPSHOT_DIR).exists()
