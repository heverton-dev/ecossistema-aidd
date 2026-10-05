import os
import pytest
from pathlib import Path

def test_vsa_worktree_context_isolates_and_restricts():
    from scripts.isolamento_vsa import VSAWorktreeContext

    with VSAWorktreeContext(nome="teste-vsa") as ctx:
        assert ctx.worktree_path.exists()
        # Escrita dentro do worktree deve ser permitida
        arquivo_isolado = ctx.worktree_path / "arquivo_teste.txt"
        ctx.escrever_arquivo(arquivo_isolado, "conteudo isolado")
        assert arquivo_isolado.read_text(encoding="utf-8") == "conteudo isolado"

        # Tentativa de escrita fora da pasta de isolamento deve falhar com PermissionError
        arquivo_externo = Path(os.getcwd()) / "arquivo_proibido_externo.txt"
        with pytest.raises(PermissionError, match="Mutação proibida fora do worktree"):
            ctx.escrever_arquivo(arquivo_externo, "falha")

    # Apos saida do contexto, limpeza efemera executada
    assert not ctx.worktree_path.exists()
