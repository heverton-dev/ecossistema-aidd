"""Testes para atualizar_index_planos.py — classificacao de status e
movimentacao fisica de pastas, com foco na distincao real entre RASCUNHO
(⏳, nunca movido) e AGUARDANDO (🔒, aprovado, move para a-fazer/)."""

import tempfile
from pathlib import Path

from atualizar_index_planos import (
    status_de_pasta,
    status_de_arquivo_unico,
    mover_se_necessario,
    RASCUNHO,
    AGUARDANDO,
    EM_EXECUCAO,
    CONCLUIDO,
    INDETERMINADO,
)


def _escrever_00(pasta: Path, linhas_status: list[str]) -> None:
    linhas_tabela = "\n".join(f"| {i+1} | Item {i+1} | {s} | doc.md |" for i, s in enumerate(linhas_status))
    conteudo = f"""# PROCESSO E DECISOES

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
{linhas_tabela}
"""
    (pasta / "00-PROCESSO-E-DECISOES.md").write_text(conteudo, encoding="utf-8")


class TestStatusDePasta:
    def test_todos_rascunho_e_rascunho(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _escrever_00(pasta, ["⏳ Rascunho gerado, aguardando aprovacao"] * 2)
            assert status_de_pasta(pasta / "00-PROCESSO-E-DECISOES.md") == RASCUNHO

    def test_todos_aguardando_e_aguardando(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _escrever_00(pasta, ["🔒 Aprovado, aguardando execucao"] * 2)
            assert status_de_pasta(pasta / "00-PROCESSO-E-DECISOES.md") == AGUARDANDO

    def test_mistura_rascunho_e_aguardando_fica_rascunho(self):
        """Aprovacao parcial (nunca deveria acontecer via cmd_aprovar, que
        aprova tudo de uma vez, mas pode ocorrer por edicao manual) nunca
        deve mover a pasta - fica onde esta ate aprovacao completa."""
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _escrever_00(pasta, ["🔒 Aprovado, aguardando execucao", "⏳ Rascunho gerado, aguardando aprovacao"])
            assert status_de_pasta(pasta / "00-PROCESSO-E-DECISOES.md") == RASCUNHO

    def test_algum_em_execucao_e_em_execucao(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _escrever_00(pasta, ["✅ Concluido", "🔶 Em execucao"])
            assert status_de_pasta(pasta / "00-PROCESSO-E-DECISOES.md") == EM_EXECUCAO

    def test_todos_concluido_e_concluido(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _escrever_00(pasta, ["✅ Concluido"] * 3)
            assert status_de_pasta(pasta / "00-PROCESSO-E-DECISOES.md") == CONCLUIDO

    def test_marcador_desconhecido_e_indeterminado(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _escrever_00(pasta, ["texto sem marcador nenhum"])
            assert status_de_pasta(pasta / "00-PROCESSO-E-DECISOES.md") == INDETERMINADO


class TestStatusDeArquivoUnico:
    def test_rascunho_no_texto_livre(self, tmp_path):
        arq = tmp_path / "PLANO-X.md"
        arq.write_text("> **Status:** [RASCUNHO - aguardando aprovacao]\n", encoding="utf-8")
        assert status_de_arquivo_unico(arq) == RASCUNHO

    def test_concluido_no_texto_livre(self, tmp_path):
        arq = tmp_path / "PLANO-X.md"
        arq.write_text("> **Status:** CONCLUIDO\n", encoding="utf-8")
        assert status_de_arquivo_unico(arq) == CONCLUIDO


class TestMoverSeNecessario:
    def test_rascunho_nunca_e_movido(self, tmp_path):
        planos_dir = tmp_path / "docs" / "planos"
        pasta_item = planos_dir / "plano-x"
        pasta_item.mkdir(parents=True)
        iniciativa = {"status": RASCUNHO, "item": pasta_item}

        import atualizar_index_planos as mod
        original = mod.PLANOS_DIR
        mod.PLANOS_DIR = planos_dir
        try:
            mover_se_necessario(iniciativa, dry_run=False)
        finally:
            mod.PLANOS_DIR = original

        assert pasta_item.exists()
        assert iniciativa["item"] == pasta_item

    def test_aguardando_move_para_a_fazer(self, tmp_path):
        planos_dir = tmp_path / "docs" / "planos"
        pasta_item = planos_dir / "plano-y"
        pasta_item.mkdir(parents=True)
        iniciativa = {"status": AGUARDANDO, "item": pasta_item}

        import atualizar_index_planos as mod
        original = mod.PLANOS_DIR
        mod.PLANOS_DIR = planos_dir
        try:
            mover_se_necessario(iniciativa, dry_run=False)
        finally:
            mod.PLANOS_DIR = original

        assert not pasta_item.exists()
        assert (planos_dir / "a-fazer" / "plano-y").exists()
