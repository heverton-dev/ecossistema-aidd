import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tempfile
from scripts.gerenciador_planos import cmd_init, verificar_cercas_arquivo, cmd_check_fences


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