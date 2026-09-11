import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tempfile
from scripts.gerenciador_melhorias import cmd_init, NOTA_NAO_AUDITADA, _parsear_itens_avaliados
from scripts.gerenciador_planos import cmd_init as plano_cmd_init


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

        dados_json = dest / "11-09-2026_melhoria-performance-build.json"
        conteudo = json.loads(dados_json.read_text(encoding="utf-8"))
        assert conteudo["nota_atual"] == NOTA_NAO_AUDITADA


def test_cmd_init_rejeita_pedido_vazio():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        ret = cmd_init("", destino_base=dest)
        assert ret == 1


def test_parsear_itens_avaliados_ok_e_invalido():
    ok = _parsear_itens_avaliados(["01::feito::rodei o teste X"])
    assert ok == [{"item": "01", "status": "feito", "justificativa": "rodei o teste X"}]

    with pytest.raises(ValueError):
        _parsear_itens_avaliados(["01::status-invalido::algo"])

    with pytest.raises(ValueError):
        _parsear_itens_avaliados(["formato-sem-separador"])


def test_cmd_init_reanalise_plano_existente_sem_nota_anterior():
    with tempfile.TemporaryDirectory() as tmp_planos, tempfile.TemporaryDirectory() as tmp_melhorias:
        dest_planos = Path(tmp_planos)
        dest_melhorias = Path(tmp_melhorias)

        plano_cmd_init("plano-antigo-reanalise", ["Item Um"], destino_base=dest_planos)
        pasta_plano = dest_planos / "plano-antigo-reanalise"
        # Remove o bloco de nota para simular um plano de formato antigo.
        caminho_00 = pasta_plano / "00-PROCESSO-E-DECISOES.md"
        conteudo = caminho_00.read_text(encoding="utf-8")
        conteudo = conteudo.split("### Metrica da Iniciativa")[0] + "## 2. Processo Adotado\ntexto\n"
        caminho_00.write_text(conteudo, encoding="utf-8")

        ret = cmd_init(
            "Reanalisar plano-antigo-reanalise",
            nome="reanalise teste",
            nota_atual="6",
            evidencia="evidencia-nova",
            plano_existente=str(pasta_plano),
            itens_avaliados=["01::parcial::metade do item ja esta no codigo"],
            destino_base=dest_melhorias,
            hoje=date(2026, 9, 11),
        )
        assert ret == 0

        dados_json = json.loads((dest_melhorias / "11-09-2026_melhoria-reanalise-teste.json").read_text(encoding="utf-8"))
        assert dados_json["nota_anterior"] == NOTA_NAO_AUDITADA
        assert dados_json["nota_atual"] == "6"
        assert dados_json["itens_avaliados"][0]["status"] == "parcial"

        html = (dest_melhorias / "11-09-2026_melhoria-reanalise-teste.html").read_text(encoding="utf-8")
        assert "Previsto no plano vs. implementado hoje" in html
        assert "🟡 Parcial" in html


def test_cmd_init_reanalise_com_nota_anterior_ja_registrada():
    with tempfile.TemporaryDirectory() as tmp_planos, tempfile.TemporaryDirectory() as tmp_melhorias:
        dest_planos = Path(tmp_planos)
        dest_melhorias = Path(tmp_melhorias)

        plano_cmd_init(
            "plano-com-nota",
            ["Item Um"],
            destino_base=dest_planos,
            nota_atual_geral="5",
            evidencia_geral="relatorio-antigo.html",
        )
        pasta_plano = dest_planos / "plano-com-nota"

        ret = cmd_init(
            "Reanalisar plano-com-nota",
            nome="segunda reanalise",
            nota_atual="8",
            evidencia="evidencia-nova",
            plano_existente=str(pasta_plano),
            destino_base=dest_melhorias,
            hoje=date(2026, 9, 11),
        )
        assert ret == 0
        dados_json = json.loads((dest_melhorias / "11-09-2026_melhoria-segunda-reanalise.json").read_text(encoding="utf-8"))
        assert dados_json["nota_anterior"] == "5"
        assert dados_json["evidencia_anterior"] == "relatorio-antigo.html"
        assert dados_json["nota_atual"] == "8"
