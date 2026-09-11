import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tempfile
from scripts.gerenciador_melhorias import cmd_init, NOTA_NAO_AUDITADA


def test_cmd_init_cria_par_html_json_com_evidencia():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        ret = cmd_init(
            "Melhorar a busca de skills no ecossistema",
            nome="busca de skills",
            nota_atual="6",
            evidencia="docs/relatorios/exemplo.html",
            resumo="Resumo de teste.",
            achados=["achado 1", "achado 2"],
            riscos=["risco 1"],
            recomendacao="Seguir para /plan",
            destino_base=dest,
            hoje=date(2026, 9, 11),
        )
        assert ret == 0

        html = dest / "11-09-2026_melhoria-busca-de-skills.html"
        dados_json = dest / "11-09-2026_melhoria-busca-de-skills.json"
        assert html.exists()
        assert dados_json.exists()

        conteudo_html = html.read_text(encoding="utf-8")
        assert "Nota Atual" in conteudo_html
        assert "6" in conteudo_html
        assert "achado 1" in conteudo_html

        import json
        conteudo_json = json.loads(dados_json.read_text(encoding="utf-8"))
        assert conteudo_json["nota_atual"] == "6"
        assert conteudo_json["evidencia"] == "docs/relatorios/exemplo.html"


def test_cmd_init_sem_evidencia_forca_nao_auditado():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        ret = cmd_init(
            "Investigar performance do build",
            nome="performance build",
            nota_atual="8",
            evidencia=None,
            destino_base=dest,
            hoje=date(2026, 9, 11),
        )
        assert ret == 0

        import json
        dados_json = dest / "11-09-2026_melhoria-performance-build.json"
        conteudo = json.loads(dados_json.read_text(encoding="utf-8"))
        assert conteudo["nota_atual"] == NOTA_NAO_AUDITADA


def test_cmd_init_rejeita_pedido_vazio():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        ret = cmd_init("", destino_base=dest)
        assert ret == 1
