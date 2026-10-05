import pytest
from pathlib import Path

def test_transacao_vsa_commit_sucesso(tmp_path):
    from scripts.rollback_vsa import TransacaoModularVSA

    arquivo_final = tmp_path / "resultado.txt"

    with TransacaoModularVSA(tmp_path) as tx:
        artefato_temp = tx.criar_artefato_temporario("temp.txt", "dados temporarios")
        assert artefato_temp.exists()
        arquivo_final.write_text("consolidado", encoding="utf-8")
        tx.marcar_sucesso()

    # Em caso de sucesso, artefatos temporarios sao limpos e final persiste
    assert not (tmp_path / "temp.txt").exists()
    assert arquivo_final.exists()
    assert arquivo_final.read_text(encoding="utf-8") == "consolidado"

def test_transacao_vsa_rollback_em_falha(tmp_path):
    from scripts.rollback_vsa import TransacaoModularVSA

    with pytest.raises(RuntimeError, match="Erro durante processamento"):
        with TransacaoModularVSA(tmp_path) as tx:
            tx.criar_artefato_temporario("parcial.txt", "dados sujos")
            assert (tmp_path / "parcial.txt").exists()
            raise RuntimeError("Erro durante processamento")

    # Em falha ou excecao, artefato parcial deve ser removido
    assert not (tmp_path / "parcial.txt").exists()
