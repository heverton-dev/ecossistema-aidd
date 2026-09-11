import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tempfile
from unittest.mock import patch

from scripts.gerenciador_planos import (
    cmd_init,
    verificar_cercas_arquivo,
    cmd_check_fences,
    cmd_atualizar_nota,
    cmd_aprovar,
    cmd_iniciar_execucao,
    ler_nota_geral,
    ler_nota_item,
    NOTA_NAO_AUDITADA,
)


def test_cmd_init_cria_estrutura_completa():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        itens = ["Planejamento e Analise", "Execucao e Entrega"]
        ret = cmd_init("auditoria-modulo-x", itens, destino_base=dest)
        assert ret == 0

        pasta = dest / "auditoria-modulo-x"
        assert pasta.is_dir()
        
        proc_md = pasta / "00-PROCESSO-E-DECISOES.md"
        assert proc_md.exists()
        conteudo_proc = proc_md.read_text(encoding="utf-8")
        assert "PROCESSO E DECISOES — auditoria-modulo-x" in conteudo_proc
        assert "Planejamento e Analise" in conteudo_proc
        assert "Execucao e Entrega" in conteudo_proc
        assert "⏳ Rascunho gerado, aguardando aprovacao" in conteudo_proc

        item1 = pasta / "01-planejamento-e-analise.md"
        assert item1.exists()
        conteudo_item1 = item1.read_text(encoding="utf-8")
        assert "Definicao de Pronto" in conteudo_item1
        assert "Prompt de Execucao (PT-BR)" in conteudo_item1
        assert "Prompt de Execucao — English version" in conteudo_item1

        item2 = pasta / "02-execucao-e-entrega.md"
        assert item2.exists()


def test_verificar_cercas_arquivo():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        
        ok_file = dest / "ok.md"
        ok_file.write_text("texto\n```bash\necho ok\n```\nfim\n", encoding="utf-8")
        valido, _ = verificar_cercas_arquivo(ok_file)
        assert valido is True

        quebrado_file = dest / "quebrado.md"
        quebrado_file.write_text("texto\n```bash\necho ok\nsem fechar\n", encoding="utf-8")
        invalido, msg = verificar_cercas_arquivo(quebrado_file)
        assert invalido is False
        assert "nao foi fechada" in msg


def test_cmd_check_fences_sucesso():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        cmd_init("iniciativa-teste", ["Item Unico"], destino_base=dest)
        pasta = dest / "iniciativa-teste"
        ret = cmd_check_fences(str(pasta))
        assert ret == 0


def test_ler_nota_plano_antigo_sem_bloco_retorna_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "plano-antigo"
        pasta.mkdir()
        (pasta / "00-PROCESSO-E-DECISOES.md").write_text("# PROCESSO E DECISOES — plano-antigo\nsem nota aqui\n", encoding="utf-8")
        (pasta / "01-item-x.md").write_text("# Item 1 — Item X\n> **Status:** [RASCUNHO]\n", encoding="utf-8")

        assert ler_nota_geral(pasta) is None
        assert ler_nota_item(pasta, "1") is None


def test_atualizar_nota_geral_insere_bloco_em_plano_antigo_e_depois_substitui():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        cmd_init("plano-para-atualizar", ["Item Unico"], destino_base=dest)
        pasta = dest / "plano-para-atualizar"

        # Remove o bloco gerado (simula plano antigo, anterior a metrica).
        caminho_00 = pasta / "00-PROCESSO-E-DECISOES.md"
        conteudo_sem_nota = caminho_00.read_text(encoding="utf-8")
        conteudo_sem_nota = conteudo_sem_nota.split("### Metrica da Iniciativa")[0] + "## 2. Processo Adotado\ntexto\n"
        caminho_00.write_text(conteudo_sem_nota, encoding="utf-8")
        assert ler_nota_geral(pasta) is None

        ret = cmd_atualizar_nota(str(pasta), None, "5", "docs/melhorias/exemplo.html")
        assert ret == 0
        info = ler_nota_geral(pasta)
        assert info == {"nota_atual": "5", "evidencia": "docs/melhorias/exemplo.html"}

        ret2 = cmd_atualizar_nota(str(pasta), None, "8", "novo-relatorio.html")
        assert ret2 == 0
        info2 = ler_nota_geral(pasta)
        assert info2 == {"nota_atual": "8", "evidencia": "novo-relatorio.html"}


def test_atualizar_nota_item_exige_evidencia():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        cmd_init("plano-item-nota", ["Item Unico"], destino_base=dest)
        pasta = dest / "plano-item-nota"

        ret = cmd_atualizar_nota(str(pasta), "1", "9", None)
        assert ret == 1
        info_intacto = ler_nota_item(pasta, "1")
        assert info_intacto["nota_atual"] == NOTA_NAO_AUDITADA

        ret2 = cmd_atualizar_nota(str(pasta), "1", "9", "teste-real.html")
        assert ret2 == 0
        info = ler_nota_item(pasta, "1")
        assert info == {"nota_atual": "9", "evidencia": "teste-real.html"}


@patch("scripts.gerenciador_planos._rodar_atualizador_index")
def test_cmd_aprovar_reescreve_status_de_todos_os_itens(mock_atualizador):
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        cmd_init("plano-aprovar", ["Item Um", "Item Dois"], destino_base=dest)
        pasta = dest / "plano-aprovar"

        ret = cmd_aprovar(str(pasta))
        assert ret == 0
        mock_atualizador.assert_called_once()

        for nome_arquivo in ("01-item-um.md", "02-item-dois.md"):
            conteudo = (pasta / nome_arquivo).read_text(encoding="utf-8")
            assert "[APROVADO — Aguardando Execucao]" in conteudo
            assert "[RASCUNHO" not in conteudo

        conteudo_00 = (pasta / "00-PROCESSO-E-DECISOES.md").read_text(encoding="utf-8")
        assert "🔒 Aprovado, aguardando execucao" in conteudo_00
        assert "⏳ Rascunho gerado, aguardando aprovacao" not in conteudo_00


@patch("scripts.gerenciador_planos._rodar_atualizador_index")
def test_cmd_aprovar_e_idempotente_nao_reaplica_em_item_ja_aprovado(mock_atualizador):
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        cmd_init("plano-aprovar-2x", ["Item Unico"], destino_base=dest)
        pasta = dest / "plano-aprovar-2x"

        cmd_aprovar(str(pasta))
        conteudo_apos_1a = (pasta / "01-item-unico.md").read_text(encoding="utf-8")

        cmd_aprovar(str(pasta))
        conteudo_apos_2a = (pasta / "01-item-unico.md").read_text(encoding="utf-8")

        assert conteudo_apos_1a == conteudo_apos_2a
        assert mock_atualizador.call_count == 2


@patch("scripts.gerenciador_planos._rodar_atualizador_index")
def test_cmd_iniciar_execucao_reescreve_status_para_em_execucao(mock_atualizador):
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        cmd_init("plano-execucao", ["Item Unico"], destino_base=dest)
        pasta = dest / "plano-execucao"
        cmd_aprovar(str(pasta))

        ret = cmd_iniciar_execucao(str(pasta))
        assert ret == 0
        assert mock_atualizador.call_count == 2  # uma vez em aprovar, outra em iniciar-execucao

        conteudo_item = (pasta / "01-item-unico.md").read_text(encoding="utf-8")
        assert "[EM EXECUCAO]" in conteudo_item

        conteudo_00 = (pasta / "00-PROCESSO-E-DECISOES.md").read_text(encoding="utf-8")
        assert "🔶 Em execucao" in conteudo_00


@patch("scripts.gerenciador_planos._rodar_atualizador_index")
def test_cmd_iniciar_execucao_funciona_direto_de_rascunho(mock_atualizador):
    """Pular a aprovacao explicita e ir direto pra execucao nao deve travar -
    so implica que a aprovacao foi implicita."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        cmd_init("plano-direto", ["Item Unico"], destino_base=dest)
        pasta = dest / "plano-direto"

        ret = cmd_iniciar_execucao(str(pasta))
        assert ret == 0
        conteudo_item = (pasta / "01-item-unico.md").read_text(encoding="utf-8")
        assert "[EM EXECUCAO]" in conteudo_item


def test_cmd_aprovar_rejeita_pasta_inexistente():
    ret = cmd_aprovar("/caminho/que/nao/existe/de/verdade")
    assert ret == 1